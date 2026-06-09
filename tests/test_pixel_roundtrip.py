"""Tests para pdf2md.pixel_roundtrip (T070 promovido em v0.6.0).

Foco em unidades puras (normalize, WER, alignment) + smoke do pipeline
end-to-end com PDFs sintéticos gerados via PyMuPDF.
"""
from pathlib import Path

import fitz
import pytest

# pixel_roundtrip puxa numpy/scipy/scikit-image (extra [rtpixel]). Sem o extra (base
# install), pula o módulo inteiro em vez de erro de coleta.
pytest.importorskip("scipy", reason="pixel-roundtrip requer o extra [rtpixel]")
pytest.importorskip("skimage", reason="pixel-roundtrip requer o extra [rtpixel]")

import numpy as np  # noqa: E402

from pdf2md.pixel_roundtrip import (  # noqa: E402
    PageMetrics,
    PixelRoundtripResult,
    align_dtw,
    align_hungarian,
    is_monotonic,
    normalize_text,
    page_wer,
    run_pixel_roundtrip,
)


# ----------------------------------------------------------------------------
# Helpers — PDFs sintéticos
# ----------------------------------------------------------------------------

def _make_pdf(path: Path, pages: list[str]) -> Path:
    """Cria PDF com 1 página por string em `pages`."""
    doc = fitz.open()
    for text in pages:
        page = doc.new_page(width=595, height=842)  # A4
        page.insert_text((72, 100), text, fontsize=11)
    doc.save(path)
    doc.close()
    return path


# ----------------------------------------------------------------------------
# Normalização
# ----------------------------------------------------------------------------

def test_normalize_lowercase_and_strip_escapes():
    assert normalize_text(r"FOO \_bar\_") == "foo _bar_"


def test_normalize_collapse_whitespace():
    assert normalize_text("a   b\n\nc\t  d") == "a b c d"


def test_normalize_nfc():
    # 'á' como letra única vs 'a' + diacrítico combinante
    composed = "á"
    decomposed = "á"
    assert normalize_text(composed) == normalize_text(decomposed)


# ----------------------------------------------------------------------------
# WER
# ----------------------------------------------------------------------------

def test_wer_identical_zero():
    assert page_wer("hello world", "hello world") == 0.0


def test_wer_disjoint_max():
    # Sem palavras em comum: WER alta (próxima de 1)
    assert page_wer("alpha beta gamma", "x y z") > 0.8


def test_wer_empty_handling():
    assert page_wer("", "") == 0.0
    assert page_wer("a b c", "") == 1.0
    assert page_wer("", "a b c") == 1.0


def test_wer_ignores_md_escapes():
    """Escapes markdown não devem afetar WER após normalização."""
    assert page_wer(r"foo \_bar\_", "foo _bar_") == 0.0


# ----------------------------------------------------------------------------
# Alinhamento — Hungarian
# ----------------------------------------------------------------------------

def test_align_hungarian_identity():
    """PDFs idênticos → pareamento i==i."""
    texts = ["page one alpha", "page two beta", "page three gamma"]
    pairs = align_hungarian(texts, texts)
    assert pairs == [(0, 0), (1, 1), (2, 2)]


def test_align_hungarian_shifted_render():
    """Render tem página extra no início → orig shifts para j+1."""
    orig = ["alpha unique", "beta unique", "gamma unique"]
    render = ["preface extra", "alpha unique", "beta unique", "gamma unique"]
    pairs = align_hungarian(orig, render)
    assert len(pairs) == 3
    # Cada orig pareou com seu render correto (offset +1)
    paired_dict = dict(pairs)
    assert paired_dict[0] == 1
    assert paired_dict[1] == 2
    assert paired_dict[2] == 3


def test_align_hungarian_empty():
    assert align_hungarian([], []) == []
    assert align_hungarian(["a"], []) == []
    assert align_hungarian([], ["a"]) == []


# ----------------------------------------------------------------------------
# Alinhamento — DTW
# ----------------------------------------------------------------------------

def test_align_dtw_identity():
    texts = ["alpha", "beta", "gamma"]
    pairs = align_dtw(texts, texts)
    # DTW também produz path diagonal para entradas iguais
    assert pairs[0] == (0, 0)
    assert pairs[-1] == (2, 2)


def test_align_dtw_is_monotonic():
    """DTW por construção produz path monotônico."""
    orig = ["alpha", "beta", "gamma", "delta"]
    render = ["alpha", "alpha extra", "beta", "gamma", "delta"]
    pairs = align_dtw(orig, render)
    assert is_monotonic(pairs)


def test_is_monotonic_function():
    assert is_monotonic([(0, 0), (1, 1), (2, 2)]) is True
    assert is_monotonic([(0, 0), (1, 2), (2, 4)]) is True  # gaps OK
    assert is_monotonic([(0, 1), (1, 0), (2, 2)]) is False  # inversão


# ----------------------------------------------------------------------------
# Pipeline end-to-end (smoke + diff)
# ----------------------------------------------------------------------------

def test_run_pixel_roundtrip_identical_pdfs(tmp_path: Path):
    """PDFs idênticos: WER ~0, SSIM ~1, alinhamento i==i."""
    pdf_a = _make_pdf(tmp_path / "a.pdf", ["alpha quick fox", "beta slow turtle"])
    pdf_b = _make_pdf(tmp_path / "b.pdf", ["alpha quick fox", "beta slow turtle"])

    result = run_pixel_roundtrip(pdf_a, pdf_b)
    assert result.n_orig_pages == 2
    assert result.n_render_pages == 2
    assert result.alignment == "hungarian"
    assert result.monotonic is True
    assert len(result.pages) == 2
    for p in result.pages:
        assert p.wer < 0.05
        assert p.ssim_macro is not None and p.ssim_macro > 0.99


def test_run_pixel_roundtrip_skip_ssim(tmp_path: Path):
    """skip_ssim=True deixa ssim_macro=None mas mantém WER."""
    pdf_a = _make_pdf(tmp_path / "a.pdf", ["alpha"])
    pdf_b = _make_pdf(tmp_path / "b.pdf", ["alpha"])

    result = run_pixel_roundtrip(pdf_a, pdf_b, skip_ssim=True)
    assert result.skipped_ssim is True
    assert all(p.ssim_macro is None for p in result.pages)
    assert "ssim_median" not in result.agg


def test_run_pixel_roundtrip_dtw_option(tmp_path: Path):
    pdf_a = _make_pdf(tmp_path / "a.pdf", ["alpha", "beta"])
    pdf_b = _make_pdf(tmp_path / "b.pdf", ["alpha", "alpha extra", "beta"])
    result = run_pixel_roundtrip(pdf_a, pdf_b, align_method="dtw", skip_ssim=True)
    assert result.alignment == "dtw"
    assert result.monotonic is True


def test_run_pixel_roundtrip_invalid_align_raises(tmp_path: Path):
    pdf_a = _make_pdf(tmp_path / "a.pdf", ["alpha"])
    pdf_b = _make_pdf(tmp_path / "b.pdf", ["alpha"])
    with pytest.raises(ValueError, match="align_method"):
        run_pixel_roundtrip(pdf_a, pdf_b, align_method="invalid")


def test_result_save_json(tmp_path: Path):
    """Result.save_json grava arquivo válido."""
    pdf_a = _make_pdf(tmp_path / "a.pdf", ["alpha"])
    pdf_b = _make_pdf(tmp_path / "b.pdf", ["alpha"])
    result = run_pixel_roundtrip(pdf_a, pdf_b, skip_ssim=True)

    out = tmp_path / "result.json"
    result.save_json(out)
    assert out.exists()

    import json
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["alignment"] == "hungarian"
    assert data["n_orig_pages"] == 1
    assert len(data["pages"]) == 1


def test_result_render_text_contains_summary(tmp_path: Path):
    pdf_a = _make_pdf(tmp_path / "a.pdf", ["alpha"])
    pdf_b = _make_pdf(tmp_path / "b.pdf", ["alpha"])
    result = run_pixel_roundtrip(pdf_a, pdf_b, skip_ssim=True)
    txt = result.render_text()
    assert "Pixel-roundtrip" in txt
    assert "hungarian" in txt
    assert "Pares alinhados" in txt


def test_flag_high_wer_appears(tmp_path: Path):
    """Páginas com WER alto devem ter flag."""
    pdf_a = _make_pdf(tmp_path / "a.pdf", ["totally different one"])
    pdf_b = _make_pdf(tmp_path / "b.pdf", ["something else entirely"])
    result = run_pixel_roundtrip(pdf_a, pdf_b, skip_ssim=True)
    p = result.pages[0]
    assert "high_wer" in p.flags or "medium_wer" in p.flags
