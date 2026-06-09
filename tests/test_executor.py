"""Tests para pdf2md.executor — executa o Pipeline do route().

CPU paths (pdftotext) testadas de verdade nos exemplos in-repo. Marker injetado
(fake runner) p/ não exigir GPU. Refiners (pix2tex/gemma3) devem PULAR com nota.
"""
from pathlib import Path

import pytest

from pdf2md.executor import run_pipeline
from pdf2md.routing import (
    AUTO, INDEXACAO, QUALIDADE, RAPIDO, DocInfo, HostInfo, Pipeline, Step, route,
)
from pdf2md._profiles import OPTIMIZER, PRIMARY, REFINER

EXAMPLES = Path(__file__).resolve().parents[1] / "corpus" / "examples"
ARXIV = EXAMPLES / "arxiv_1706_03762_excerpt.pdf"
ARXIV_MATH = EXAMPLES / "arxiv_1706_03762_math_excerpt.pdf"
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


@pytest.mark.skipif(not ARXIV_MATH.exists(), reason="exemplo math ausente")
def test_indexacao_marks_pass2_on_math_doc(tmp_path):
    # --indexacao: pass1 (pdftotext) indexa; o gatilho marca pass2 no doc math-heavy.
    pipe = route(INDEXACAO, _host_gpu(), DocInfo.probe(ARXIV_MATH))
    res = run_pipeline(pipe, ARXIV_MATH, tmp_path)
    assert res.primary == "pdftotext"
    assert res.output_md and res.output_md.exists()        # pass1 indexou
    assert res.needs_pass2 is True
    assert any("ENFILEIRADO" in r for r in res.rationale)


@pytest.mark.skipif(not ARXIV.exists(), reason="exemplo arxiv ausente")
def test_indexacao_skips_pass2_on_prose_doc(tmp_path):
    # intro do MESMO paper = prosa (densidade sã, math ínfimo) → pass1 cobre, pass2 dispensado.
    pipe = route(INDEXACAO, _host_gpu(), DocInfo.probe(ARXIV))
    res = run_pipeline(pipe, ARXIV, tmp_path)
    assert res.primary == "pdftotext"
    assert res.needs_pass2 is False
    assert any("dispensado" in r for r in res.rationale)


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


def test_refiners_skip_honestly_when_unavailable(tmp_path):
    # pix2tex: cropper falha em pdf inexistente; gemma3: T180. Ambos pulam com nota honesta.
    pipe = Pipeline(intent=QUALIDADE, steps=[
        Step("marker", PRIMARY, ""),
        Step("pix2tex", REFINER, ""),
        Step("gemma3-4b-small-image", REFINER, ""),
    ])
    res = run_pipeline(pipe, "dummy.pdf", tmp_path,
                       marker_runner=lambda p, o: _touch(tmp_path / "m.md"))
    skipped = {a: why for a, why in res.skipped}
    assert "pix2tex" in skipped and "cropper" in skipped["pix2tex"]
    assert "gemma3-4b-small-image" in skipped and "T180" in skipped["gemma3-4b-small-image"]


@pytest.mark.skipif(not ARXIV.exists(), reason="exemplo arxiv ausente")
def test_pix2tex_orphan_regions_fall_to_end(tmp_path, monkeypatch):
    # regiões SEM block_indices (não casam bloco no extrator) → rede de segurança: seção-ao-fim.
    from pdf2md.formula_cropper import FormulaRegion
    import pdf2md.executor as ex

    def fake_crop(pdf, out_dir, **kw):
        d = Path(out_dir); d.mkdir(parents=True, exist_ok=True)
        (d / "pg00_5-12.png").write_bytes(b"x")
        (d / "pg00_5-32.png").write_bytes(b"x")
        return [
            FormulaRegion(0, (0, 0, 1, 1), "5.12", False, {}, d / "pg00_5-12.png"),     # block_indices=()
            FormulaRegion(0, (0, 0, 1, 1), "5.32", True, {}, d / "pg00_5-32.png"),      # matriz
        ]
    monkeypatch.setattr(ex, "crop_formulas", fake_crop)
    runner = lambda crop_dir: {"pg00_5-12.png": "a=b", "pg00_5-32.png": "M=I"}

    pipe = Pipeline(intent=QUALIDADE, steps=[
        Step("pdftotext", PRIMARY, ""), Step("pix2tex", REFINER, ""),
    ])
    res = run_pipeline(pipe, ARXIV, tmp_path, pix2tex_runner=runner)
    assert "pix2tex" in res.ran
    md = res.output_md.read_text(encoding="utf-8")
    assert "Fórmulas extraídas" in md and "a=b" in md and "M=I" in md   # órfãs ao fim
    assert "baixa confiança" in md and "PDF2MD:FORMULA" not in md       # 5.32 flagada; sem token vazado


def test_inline_formulas_substitutes_in_position(monkeypatch, tmp_path):
    # unit hermético: token no corpo → $$latex$$ na posição; complexo→comentário; vazio→raw; órfã→fim.
    from pdf2md.formula_cropper import FormulaRegion, formula_token
    from pdf2md.extractors import ExtractResult
    import pdf2md.executor as ex

    r1 = FormulaRegion(0, (0, 0, 1, 1), "5.12", False, {}, tmp_path / "pg00_5-12.png", (7,))
    r2 = FormulaRegion(0, (0, 0, 1, 1), "5.32", True, {}, tmp_path / "pg00_5-32.png", (9,))   # matriz
    t1, t2 = formula_token(r1), formula_token(r2)
    fake_md = f"before\n\n{t1}\n\nmiddle\n\n{t2}\n\nafter\n"
    fake = ExtractResult(markdown=fake_md, n_pages=1, backend="pdftotext",
                         placeholders={t1: "GARB1", t2: "GARB2"})
    monkeypatch.setattr(ex, "extract_pdftotext", lambda *a, **k: fake)

    md, n = ex._inline_formulas("x.pdf", [r1, r2], {"pg00_5-12.png": "a=b", "pg00_5-32.png": "M=I"})
    assert n == 2
    assert "$$ a=b \\tag{5.12} $$" in md and "$$ M=I \\tag{5.32} $$" in md
    assert "baixa confiança" in md                                  # r2 complexa
    assert "PDF2MD:FORMULA" not in md                               # nenhum token vaza
    assert md.index("a=b") < md.index("middle") < md.index("M=I")   # posição preservada
    assert "Fórmulas extraídas" not in md                           # tudo inline, sem órfã


def test_inline_formulas_empty_latex_restores_raw(monkeypatch, tmp_path):
    from pdf2md.formula_cropper import FormulaRegion, formula_token
    from pdf2md.extractors import ExtractResult
    import pdf2md.executor as ex
    r1 = FormulaRegion(0, (0, 0, 1, 1), "5.12", False, {}, tmp_path / "pg00_5-12.png", (7,))
    t1 = formula_token(r1)
    fake = ExtractResult(markdown=f"a\n\n{t1}\n\nb\n", n_pages=1, backend="pdftotext",
                         placeholders={t1: "RAWGARBLE"})
    monkeypatch.setattr(ex, "extract_pdftotext", lambda *a, **k: fake)
    md, n = ex._inline_formulas("x.pdf", [r1], {})       # pix2tex devolveu vazio
    assert n == 0 and "RAWGARBLE" in md and "PDF2MD:FORMULA" not in md   # baseline restaurado, sem token


def test_inline_formulas_orphan_appended(monkeypatch, tmp_path):
    from pdf2md.formula_cropper import FormulaRegion
    from pdf2md.extractors import ExtractResult
    import pdf2md.executor as ex
    r1 = FormulaRegion(0, (0, 0, 1, 1), "9.9", False, {}, tmp_path / "pg00_9-9.png", (3,))
    fake = ExtractResult(markdown="prose sem token\n", n_pages=1, backend="pdftotext", placeholders={})
    monkeypatch.setattr(ex, "extract_pdftotext", lambda *a, **k: fake)
    md, n = ex._inline_formulas("x.pdf", [r1], {"pg00_9-9.png": "x=1"})
    assert n == 1 and "Fórmulas extraídas" in md and "x=1" in md   # sem placeholder → rede ao fim


@pytest.mark.skipif(not (Path("Z:/caches/corpus/pdf2md/preskill_ph219_ch5.pdf")).exists(),
                    reason="Preskill zcache ausente")
def test_inline_real_preskill_position(tmp_path):
    # integração: crop real + extract real + latex fake → $$ na POSIÇÃO, prosa intacta, sem token.
    from pdf2md.formula_cropper import crop_formulas
    import pdf2md.executor as ex
    PRESKILL = Path("Z:/caches/corpus/pdf2md/preskill_ph219_ch5.pdf")
    regions = crop_formulas(PRESKILL, tmp_path, page_range=(4, 4))   # eq 5.12
    fake_latex = {r.crop_path.name: "X=Y" for r in regions}
    md, n = ex._inline_formulas(PRESKILL, regions, fake_latex)
    assert n == len(regions)
    assert "$$ X=Y \\tag{5.12} $$" in md
    assert "PDF2MD:FORMULA" not in md
    assert "bounded as" in md and md.index("bounded as") < md.index("X=Y")   # posição original


def test_pix2tex_skips_when_no_runtime(tmp_path, monkeypatch):
    # cropou fórmulas mas sem runner injetado e sem runtime descoberto → pula honesto
    from pdf2md.formula_cropper import FormulaRegion
    import pdf2md.executor as ex
    monkeypatch.setattr(ex, "crop_formulas",
                        lambda pdf, out_dir, **kw: [FormulaRegion(0, (0, 0, 1, 1), "1", False, {}, None)])
    monkeypatch.setattr(ex, "_discover_pix2tex_python", lambda: None)
    monkeypatch.setattr(ex.shutil, "which", lambda *a, **k: None)
    pipe = Pipeline(intent=QUALIDADE, steps=[Step("pdftotext", PRIMARY, "")])
    # injeta um step pix2tex à mão p/ exercer o caminho sem runtime
    pipe.steps.append(Step("pix2tex", REFINER, ""))
    if ARXIV.exists():
        res = run_pipeline(pipe, ARXIV, tmp_path)
        assert any(a == "pix2tex" and "runtime pix2tex ausente" in why for a, why in res.skipped)


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
    # pass2 não é executado agora, mas o VEREDITO do gatilho DEVE aparecer na rationale
    # (não dropar em silêncio) — seja ENFILEIRADO (warranted) ou dispensado (pass1 cobre).
    pipe = route("indexacao", _host_gpu(), DocInfo.probe(ARXIV))
    assert pipe.pass2 is not None      # host com marker → pass2 construído
    res = run_pipeline(pipe, ARXIV, tmp_path)  # pass1 = pdftotext (real)
    assert res.primary == "pdftotext"
    assert res.needs_pass2 is not None                        # gatilho foi avaliado
    assert any("pass2" in r.lower() for r in res.rationale)   # surfaçado, não dropado

def test_tesseract_dispatch_through_executor(tmp_path):
    import importlib.util

    from pdf2md.extractors import tesseract_cmd
    if (tesseract_cmd() is None or importlib.util.find_spec("pytesseract") is None
            or not WILSON.exists()):
        pytest.skip("tesseract bin / wrapper pytesseract / exemplo wilson ausente")
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
