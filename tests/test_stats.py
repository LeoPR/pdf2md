"""Tests para pdf2md.stats — fmt_bytes, categorize_divergence, md_metrics, compute_stats."""
import json
from pathlib import Path

from pdf2md.stats import (
    categorize_divergence,
    compute_stats,
    detect_tools,
    fmt_bytes,
    folder_metrics,
    image_breakdown,
    md_metrics,
    roundtrip_metrics,
)


def test_fmt_bytes_units():
    assert fmt_bytes(0) == "0 B"
    assert fmt_bytes(512) == "512 B"
    assert fmt_bytes(1024) == "1.0 KB"
    assert fmt_bytes(1024 * 1024) == "1.0 MB"


def test_categorize_divergence_url_is_other():
    """URL não deve virar 'math' mesmo com escape backslash (regressão e02 CDC)."""
    assert categorize_divergence("<sup>\\*</sup>", "https://cdc.gov/foo") == "other"


def test_categorize_divergence_math_dollar():
    assert categorize_divergence("$x = 1$", "") == "math"


def test_categorize_divergence_math_latex_cmd():
    assert categorize_divergence("\\frac{a}{b}", "") == "math"


def test_categorize_divergence_heading():
    assert categorize_divergence("\n## Title", "") == "heading"


def test_categorize_divergence_emphasis():
    assert categorize_divergence("**bold**", "") == "emphasis"


def test_categorize_divergence_image_ref():
    assert categorize_divergence("![alt](foo.png)", "") == "image_ref"


def test_categorize_divergence_whitespace():
    assert categorize_divergence("", "  ") == "whitespace"


def test_detect_tools_with_overrides():
    """Kwargs explícitos têm precedência sobre env vars e auto-detect."""
    info = detect_tools(
        marker_version="1.10.2",
        torch_version="2.11",
        cuda_device="RTX 3060",
        cuda_memory_gb=12.0,
        pandoc_version="3.9",
    )
    assert info["marker"] == "1.10.2"
    assert info["torch"] == "2.11"
    assert info["cuda_available"] is True
    assert info["cuda_device"] == "RTX 3060"
    assert info["cuda_memory_gb"] == 12.0
    assert info["pandoc"] == "3.9"
    assert "python" in info


def test_md_metrics_basic(tmp_path: Path):
    md = tmp_path / "foo.md"
    md.write_text(
        "# Título\n\nLorem ipsum dolor sit amet. Mais texto aqui.\n\n"
        "$$E = mc^2$$\n\nInline $x$ e mais. ![img](a.png)\n",
        encoding="utf-8",
    )
    m = md_metrics(md)
    assert m["tokens"] > 0
    assert m["words"] >= 5
    assert m["headers"]["h1"] == 1
    assert m["math"]["display"] == 1
    assert m["math"]["inline_markers"] >= 1
    assert m["images_referenced"] == 1


def test_image_breakdown_counts(tmp_path: Path):
    (tmp_path / "a.png").write_bytes(b"x" * 100)
    (tmp_path / "b.jpeg").write_bytes(b"y" * 200)
    (tmp_path / "c.svg").write_bytes(b"<svg/>")
    out = image_breakdown(tmp_path)
    assert out["count"] == 3
    assert out["total_bytes"] >= 306
    assert set(out["by_format"].keys()) == {"png", "jpeg", "svg"}


def test_folder_metrics_book_layout(tmp_path: Path):
    """Layout livro: subpastas com .md de mesmo nome."""
    (tmp_path / "01_intro").mkdir()
    (tmp_path / "01_intro" / "01_intro.md").write_text(
        "# Intro\n\nTexto.\n", encoding="utf-8"
    )
    (tmp_path / "02_cap2").mkdir()
    (tmp_path / "02_cap2" / "02_cap2.md").write_text(
        "# Cap 2\n\nMais texto. $x=1$\n", encoding="utf-8"
    )
    m = folder_metrics(tmp_path)
    assert m["totals"]["chapter_count"] == 2
    assert m["totals"]["tokens"] > 0
    assert m["totals"]["math_inline"] >= 1


def test_folder_metrics_paper_layout(tmp_path: Path):
    """Layout paper: .md direto na pasta (não em subpasta)."""
    (tmp_path / "paper.md").write_text(
        "# Abstract\n\nTexto do paper.\n", encoding="utf-8"
    )
    m = folder_metrics(tmp_path)
    assert m["totals"]["chapter_count"] == 1
    assert "paper" in m["chapters"]


def test_roundtrip_metrics_identical(tmp_path: Path):
    md1 = tmp_path / "a.md"
    md2 = tmp_path / "b.md"
    text = "# Cap\n\nTexto idêntico em ambos.\n"
    md1.write_text(text, encoding="utf-8")
    md2.write_text(text, encoding="utf-8")
    rt = roundtrip_metrics(md1, md2)
    assert rt["similarity"] == 1.0
    assert rt["bloat_ratio"] == 1.0
    assert rt["divergence_categories"] == {}


def test_roundtrip_metrics_diverges(tmp_path: Path):
    md1 = tmp_path / "a.md"
    md2 = tmp_path / "b.md"
    md1.write_text("# Cap\n\nTexto original.\n", encoding="utf-8")
    md2.write_text("# Cap\n\nTexto modificado completamente.\n", encoding="utf-8")
    rt = roundtrip_metrics(md1, md2)
    assert 0.0 < rt["similarity"] < 1.0
    assert rt["divergence_categories"]


def test_compute_stats_writes_files(tmp_path: Path):
    """Pipeline end-to-end: cria _stats.json e _stats.md."""
    folder = tmp_path / "extract"
    folder.mkdir()
    (folder / "ch1").mkdir()
    (folder / "ch1" / "ch1.md").write_text(
        "# Cap 1\n\nLorem ipsum. $$E=mc^2$$\n", encoding="utf-8"
    )

    json_path, md_path = compute_stats(
        folder,
        tool_overrides={"marker_version": "1.10.2", "pandoc_version": "3.9"},
    )
    assert json_path.exists() and json_path.name == "_stats.json"
    assert md_path.exists() and md_path.name == "_stats.md"

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["tools"]["marker"] == "1.10.2"
    assert data["tools"]["pandoc"] == "3.9"
    assert data["output"]["totals"]["chapter_count"] == 1
    assert "generated_at" in data


def test_compute_stats_with_roundtrip(tmp_path: Path):
    folder = tmp_path / "extract"
    folder.mkdir()
    (folder / "p.md").write_text("# X\n\nTexto.\n", encoding="utf-8")

    md1 = tmp_path / "md1.md"
    md2 = tmp_path / "md2.md"
    md1.write_text("# X\n\nTexto.\n", encoding="utf-8")
    md2.write_text("# X\n\nTexto.\n", encoding="utf-8")

    json_path, _ = compute_stats(
        folder, roundtrip_md1=md1, roundtrip_md2=md2,
        tool_overrides={"marker_version": "1.10.2"},
    )
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["roundtrip"]["similarity"] == 1.0
