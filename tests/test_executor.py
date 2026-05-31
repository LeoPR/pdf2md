"""Tests para pdf2md.executor — executa o Pipeline do route().

CPU paths (pdftotext) testadas de verdade nos exemplos in-repo. Marker injetado
(fake runner) p/ não exigir GPU. Refiners (pix2tex/gemma3) devem PULAR com nota.
"""
from pathlib import Path

import pytest

from pdf2md.executor import run_pipeline
from pdf2md.routing import (
    AUTO, QUALIDADE, RAPIDO, DocInfo, HostInfo, Pipeline, Step, route,
)
from pdf2md._profiles import OPTIMIZER, PRIMARY, REFINER

EXAMPLES = Path(__file__).resolve().parents[1] / "corpus" / "examples"
ARXIV = EXAMPLES / "arxiv_1706_03762_excerpt.pdf"
WILSON = EXAMPLES / "wilson_mathematics_excerpt.pdf"


def _host_cpu():
    return HostInfo(cpu_cores=4, ram_gb=8, gpu_vram_mb=0, has_marker=False, has_tesseract=True)

def _host_gpu():
    return HostInfo(cpu_cores=8, ram_gb=32, gpu_vram_mb=12000,
                    has_ollama=True, has_marker=True, has_tesseract=True)


@pytest.mark.skipif(not ARXIV.exists(), reason="exemplo arxiv ausente")
def test_rapido_executes_pdftotext(tmp_path):
    doc = DocInfo.probe(ARXIV)
    pipe = route(RAPIDO, _host_cpu(), doc)
    res = run_pipeline(pipe, ARXIV, tmp_path)
    assert res.primary == "pdftotext"
    assert res.output_md and res.output_md.exists()
    assert len(res.output_md.read_text(encoding="utf-8")) > 300
    assert "pdftotext" in res.ran
    # rapido: sem optimizer no pipeline → não consta em ran nem skipped de optimize
    assert "pdf2md-optimize" not in res.ran


@pytest.mark.skipif(not ARXIV.exists(), reason="exemplo arxiv ausente")
def test_optimizer_noop_on_text_extractor(tmp_path):
    # --balanceado inclui optimize, mas pdftotext não gera imagens → pula com nota
    doc = DocInfo.probe(ARXIV)
    pipe = route("balanceado", _host_cpu(), doc)
    res = run_pipeline(pipe, ARXIV, tmp_path)
    assert any(a == "pdf2md-optimize" for a, _ in res.skipped)
    assert any("sem imagens" in why for a, why in res.skipped if a == "pdf2md-optimize")


def test_marker_runner_injected(tmp_path):
    # PRIMARY marker executado via runner injetado (sem GPU real)
    fake_md = tmp_path / "fake.md"
    calls = []

    def fake_runner(pdf, out):
        calls.append((pdf, out))
        fake_md.write_text("# marker output\n", encoding="utf-8")
        return fake_md

    pipe = Pipeline(intent=QUALIDADE, steps=[Step("marker", PRIMARY, "test")])
    res = run_pipeline(pipe, "dummy.pdf", tmp_path, marker_runner=fake_runner)
    assert calls and res.primary == "marker"
    assert res.output_md == fake_md
    assert "marker" in res.ran


def test_refiners_skip_with_honest_reason(tmp_path):
    # pipeline com pix2tex + gemma3 → pulam com nota (BURACO #3 / T180)
    pipe = Pipeline(intent=QUALIDADE, steps=[
        Step("marker", PRIMARY, ""),
        Step("pix2tex", REFINER, ""),
        Step("gemma3-4b-small-image", REFINER, ""),
    ])
    res = run_pipeline(pipe, "dummy.pdf", tmp_path,
                       marker_runner=lambda p, o: _touch(tmp_path / "m.md"))
    skipped_algos = {a for a, _ in res.skipped}
    assert "pix2tex" in skipped_algos and "gemma3-4b-small-image" in skipped_algos
    assert any("BURACO #3" in why for a, why in res.skipped if a == "pix2tex")


@pytest.mark.skipif(not ARXIV.exists(), reason="exemplo arxiv ausente")
def test_degraded_flag_propagates(tmp_path):
    # qualidade sem GPU degrada; executor propaga o flag
    doc = DocInfo.probe(ARXIV)
    pipe = route(QUALIDADE, _host_cpu(), doc)
    res = run_pipeline(pipe, ARXIV, tmp_path)
    assert res.degraded is True
    assert res.primary == "pdftotext"


def _touch(p: Path) -> Path:
    p.write_text("# x\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Correções da revisão adversarial do executor (exec-review)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not ARXIV.exists(), reason="exemplo arxiv ausente")
def test_indexacao_pass2_surfaced_not_dropped(tmp_path):
    # pass2 não é executado agora, mas DEVE aparecer na rationale (não dropar em silêncio)
    pipe = route("indexacao", _host_gpu(), DocInfo.probe(ARXIV))
    assert pipe.pass2 is not None      # host com marker → pass2 construído
    res = run_pipeline(pipe, ARXIV, tmp_path)  # pass1 = pdftotext (real)
    assert res.primary == "pdftotext"
    assert any("pass2 enfileir" in r for r in res.rationale)

def test_tesseract_dispatch_through_executor(tmp_path):
    from pdf2md.extractors import tesseract_cmd
    if tesseract_cmd() is None or not WILSON.exists():
        pytest.skip("tesseract ou exemplo wilson ausente")
    pipe = Pipeline(intent="rapido", steps=[Step("tesseract", PRIMARY, "scan")])
    res = run_pipeline(pipe, WILSON, tmp_path)
    assert res.primary == "tesseract"
    assert res.output_md and res.output_md.exists()

def test_unknown_primary_skips_with_note(tmp_path):
    pipe = Pipeline(intent="rapido", steps=[Step("mystery-algo", PRIMARY, "")])
    res = run_pipeline(pipe, "dummy.pdf", tmp_path)
    assert any(a == "mystery-algo" for a, _ in res.skipped)
    assert res.output_md is None

def test_optimize_runs_with_marker_images(tmp_path):
    from PIL import Image
    def runner(pdf, out):
        # marker "emite" md + uma imagem
        Image.new("RGB", (32, 32), (10, 20, 30)).save(out / "fig1.png")
        return _touch(out / "doc.md")
    pipe = Pipeline(intent="qualidade", steps=[
        Step("marker", PRIMARY, ""), Step("pdf2md-optimize", OPTIMIZER, ""),
    ])
    res = run_pipeline(pipe, "dummy.pdf", tmp_path, marker_runner=runner)
    assert "pdf2md-optimize" in res.ran    # rodou (havia imagem do marker)

def test_optimize_skips_for_text_primary(tmp_path):
    # mesmo com OPTIMIZER no pipeline, primary texto-puro → optimize pula
    pipe = Pipeline(intent="balanceado", steps=[
        Step("pdftotext", PRIMARY, ""), Step("pdf2md-optimize", OPTIMIZER, ""),
    ])
    # pdftotext precisa de um pdf real → usa arxiv se existir, senão fake primary path
    if ARXIV.exists():
        res = run_pipeline(pipe, ARXIV, tmp_path)
        assert any(a == "pdf2md-optimize" for a, _ in res.skipped)

def test_marker_md_selection_ignores_underscore_reports(tmp_path, monkeypatch):
    # _default_marker_runner deve casar pelo stem e ignorar relatórios '_*.md'
    import pdf2md.executor as ex
    (tmp_path / "_image_optimization.md").write_text("report\n", encoding="utf-8")
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper" / "paper.md").write_text("# real\n", encoding="utf-8")
    monkeypatch.setattr(ex.subprocess, "run", lambda *a, **k: None)
    monkeypatch.setattr(ex, "_discover_marker", lambda: "fake-marker")
    got = ex._default_marker_runner(Path("paper.pdf"), tmp_path)
    assert got.name == "paper.md"
