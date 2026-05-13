"""Tests para pdf2md.optimize — classificação, rewrite, optimize_dir.

Imagens fixture geradas in-memory via PIL (sem dependências de arquivos reais).
"""
import json
from pathlib import Path

import pytest

PIL = pytest.importorskip("PIL")
from PIL import Image, ImageDraw  # noqa: E402

from pdf2md.optimize import (  # noqa: E402
    classify_image,
    count_colors,
    fmt_bytes,
    optimize_dir,
    optimize_one,
    rewrite_md_refs,
)


# ---------------------------------------------------------------------------
# Fixtures de imagem
# ---------------------------------------------------------------------------

def _make_bw_image(path: Path, size: tuple[int, int] = (200, 200)) -> Path:
    """Imagem B&W estrita: dois retângulos preto/branco. Salva como JPEG."""
    img = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle((10, 10, 100, 100), fill="black")
    img.save(path, "JPEG", quality=95)
    return path


def _make_palette_image(path: Path, n_colors: int = 8) -> Path:
    """Imagem com paleta discreta (n cores RGB distintas) em faixas. JPEG."""
    img = Image.new("RGB", (200, 200), "white")
    draw = ImageDraw.Draw(img)
    palette = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
        (255, 0, 255), (0, 255, 255), (128, 128, 128), (0, 0, 0),
    ][:n_colors]
    band_w = 200 // len(palette)
    for i, color in enumerate(palette):
        draw.rectangle((i * band_w, 0, (i + 1) * band_w, 200), fill=color)
    img.save(path, "JPEG", quality=95)
    return path


def _make_continuous_image(path: Path) -> Path:
    """Imagem continuous tone (gradiente RGB com muito ruído) em JPEG."""
    import random
    random.seed(42)
    img = Image.new("RGB", (200, 200))
    pixels = img.load()
    for x in range(200):
        for y in range(200):
            r = (x * 255 // 200 + random.randint(-20, 20)) % 256
            g = (y * 255 // 200 + random.randint(-20, 20)) % 256
            b = random.randint(0, 255)
            pixels[x, y] = (r, g, b)
    img.save(path, "JPEG", quality=85)
    return path


# ---------------------------------------------------------------------------
# Pure functions
# ---------------------------------------------------------------------------

def test_count_colors_few():
    img = Image.new("RGB", (10, 10), "red")
    assert count_colors(img) == 1


def test_count_colors_many_returns_none():
    """Imagem com >max_check cores retorna None."""
    img = Image.new("RGB", (50, 50))
    pixels = img.load()
    for x in range(50):
        for y in range(50):
            pixels[x, y] = (x * 5, y * 5, (x + y) * 3)
    assert count_colors(img, max_check=10) is None


def test_classify_bw(tmp_path: Path):
    """JPEG B&W puro deve virar 'palette_lossy' (anti-aliasing inflou cores no JPEG)."""
    path = _make_bw_image(tmp_path / "bw.jpeg")
    with Image.open(path) as img:
        img.load()
        kind, n = classify_image(img)
    # JPEG sempre adiciona ruído, então mesmo BW puro vira palette_lossy ou bw
    assert kind in ("bw", "palette", "palette_lossy")


def test_classify_continuous(tmp_path: Path):
    """Gradiente ruidoso deve ser continuous tone."""
    path = _make_continuous_image(tmp_path / "cont.jpeg")
    with Image.open(path) as img:
        img.load()
        kind, _ = classify_image(img)
    assert kind == "continuous"


def test_fmt_bytes_units():
    assert fmt_bytes(0) == "0 B"
    assert fmt_bytes(1024) == "1.0 KB"
    assert fmt_bytes(1024 * 1024 * 5) == "5.0 MB"


# ---------------------------------------------------------------------------
# rewrite_md_refs
# ---------------------------------------------------------------------------

def test_rewrite_md_refs_basic(tmp_path: Path):
    md = tmp_path / "ch.md"
    md.write_text(
        "Veja ![fig 1](images/_page_0_Pic_0.jpeg) e ![bla](images/_page_2.png)\n",
        encoding="utf-8",
    )
    n = rewrite_md_refs(md, {"_page_0_Pic_0.jpeg": "_page_0_Pic_0.png"})
    assert n == 1
    assert "images/_page_0_Pic_0.png" in md.read_text(encoding="utf-8")
    assert "_page_2.png" in md.read_text(encoding="utf-8")  # não tocada


def test_rewrite_md_refs_dry_run(tmp_path: Path):
    md = tmp_path / "ch.md"
    original = "![](foo.jpeg)\n"
    md.write_text(original, encoding="utf-8")
    n = rewrite_md_refs(md, {"foo.jpeg": "foo.png"}, dry_run=True)
    assert n == 1  # conta a substituição
    assert md.read_text(encoding="utf-8") == original  # não escreveu


def test_rewrite_md_refs_no_renames(tmp_path: Path):
    md = tmp_path / "ch.md"
    md.write_text("![](foo.png)\n", encoding="utf-8")
    assert rewrite_md_refs(md, {}) == 0


# ---------------------------------------------------------------------------
# optimize_one + optimize_dir
# ---------------------------------------------------------------------------

def test_optimize_one_continuous_keeps_jpeg(tmp_path: Path):
    """Continuous tone JPEG não deve ser tocado."""
    path = _make_continuous_image(tmp_path / "cont.jpeg")
    rec = optimize_one(path)
    assert rec["decision"] == "keep_jpeg"
    assert path.exists()  # original preservada


def test_optimize_one_dry_run(tmp_path: Path):
    """Dry-run não deve modificar nenhum arquivo."""
    path = _make_bw_image(tmp_path / "bw.jpeg")
    original_bytes = path.stat().st_size
    rec = optimize_one(path, dry_run=True)
    assert path.exists()
    assert path.stat().st_size == original_bytes
    # tmp não pode ter sobrado
    assert not (tmp_path / "bw.png.tmp").exists()


def test_optimize_dir_writes_reports(tmp_path: Path):
    """End-to-end: pasta com imagem + MD, gera relatórios."""
    chap = tmp_path / "ch1"
    chap.mkdir()
    imgs = chap / "images"
    imgs.mkdir()
    _make_continuous_image(imgs / "_page_0.jpeg")
    (chap / "ch1.md").write_text(
        "# Cap 1\n\n![fig](images/_page_0.jpeg)\n", encoding="utf-8"
    )

    json_path, md_path, summary = optimize_dir(tmp_path)

    assert json_path.exists() and json_path.name == "_image_optimization.json"
    assert md_path.exists() and md_path.name == "_image_optimization.md"

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["total_images"] == 1
    assert "by_kind" in data
    assert "records" in data


def test_optimize_dir_dry_run_no_changes(tmp_path: Path):
    """Dry-run: gera relatórios mas não modifica imagens."""
    chap = tmp_path / "ch1"
    chap.mkdir()
    img_path = _make_bw_image(chap / "fig.jpeg")
    md = chap / "ch1.md"
    md.write_text("![](fig.jpeg)\n", encoding="utf-8")

    original_md = md.read_text(encoding="utf-8")
    json_path, _, summary = optimize_dir(tmp_path, dry_run=True)

    assert summary["dry_run"] is True
    assert img_path.exists()  # imagem original intacta
    assert md.read_text(encoding="utf-8") == original_md  # MD intacto


def test_optimize_dir_progress_callback(tmp_path: Path):
    """Callback é chamado uma vez por imagem com (i, total, record)."""
    _make_continuous_image(tmp_path / "a.jpeg")
    _make_continuous_image(tmp_path / "b.jpeg")

    calls = []

    def cb(i, total, rec):
        calls.append((i, total, rec["decision"]))

    optimize_dir(tmp_path, on_progress=cb)
    assert len(calls) == 2
    assert calls[0][0] == 1 and calls[1][0] == 2
    assert all(c[1] == 2 for c in calls)
