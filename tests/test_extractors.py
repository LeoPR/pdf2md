"""Tests para pdf2md.extractors — pdftotext (CPU estruturado) + tesseract (OCR).

Hermetic: usa os PDFs livres in-repo (corpus/examples/). Tesseract pula se o
binário não estiver instalado.
"""
from pathlib import Path

import pytest

from pdf2md.extractors import (
    ExtractResult, extract_pdftotext, extract_tesseract, join_hyphenation,
    normalize_chars, tesseract_cmd,
)

EXAMPLES = Path(__file__).resolve().parents[1] / "corpus" / "examples"
ARXIV = EXAMPLES / "arxiv_1706_03762_excerpt.pdf"     # text-layer (paper)
CDC = EXAMPLES / "cdc_mmwr_73_35_a1.pdf"              # printed gov


def test_normalize_chars_ligatures_and_quotes():
    assert normalize_chars("ﬁnal ﬂow diﬀer “x”") == 'final flow differ "x"'

def test_join_hyphenation():
    assert join_hyphenation("com-\nputation") == "computation"
    assert join_hyphenation("oper- ations") == "operations"


@pytest.mark.skipif(not ARXIV.exists(), reason="exemplo arxiv ausente")
def test_pdftotext_extracts_text_layer():
    r = extract_pdftotext(ARXIV)
    assert isinstance(r, ExtractResult)
    assert r.backend == "pdftotext"
    assert r.n_pages >= 1
    assert len(r.markdown) > 300
    assert "attention" in r.markdown.lower()      # título do paper
    # determinístico: 2ª extração idêntica
    assert extract_pdftotext(ARXIV).markdown == r.markdown

@pytest.mark.skipif(not ARXIV.exists(), reason="exemplo arxiv ausente")
def test_pdftotext_page_range():
    one = extract_pdftotext(ARXIV, page_range=(0, 0))
    full = extract_pdftotext(ARXIV)
    assert len(one.markdown) <= len(full.markdown)

@pytest.mark.skipif(not ARXIV.exists(), reason="exemplo arxiv ausente")
def test_pdftotext_out_of_range_raises():
    # page_range fora do doc → ValueError (não IndexError/leak)
    with pytest.raises(ValueError):
        extract_pdftotext(ARXIV, page_range=(50, 60))

def test_pdftotext_empty_pdf_raises(monkeypatch):
    # fitz não salva PDF 0-página; fingimos um doc vazio p/ exercer a guarda n==0
    class FakeDoc:
        def __len__(self): return 0
        def close(self): pass
    monkeypatch.setattr("pdf2md.extractors.fitz.open", lambda *a, **k: FakeDoc())
    with pytest.raises(ValueError):
        extract_pdftotext("whatever.pdf")


@pytest.mark.skipif(tesseract_cmd() is None, reason="tesseract não instalado")
@pytest.mark.skipif(not CDC.exists(), reason="exemplo cdc ausente")
def test_tesseract_ocrs_printed_page():
    r = extract_tesseract(CDC, page_range=(0, 0))
    assert r.backend == "tesseract"
    assert len(r.markdown.split()) > 20          # OCR de página impressa produz texto


# --- formula-aware (posição inline): placeholders por block_index -----------
PRESKILL = Path("Z:/caches/corpus/pdf2md/preskill_ph219_ch5.pdf")


@pytest.mark.skipif(not ARXIV.exists(), reason="exemplo arxiv ausente")
def test_pdftotext_no_regions_is_unchanged():
    # formula_regions=None → byte-idêntico + placeholders vazio (zero regressão no --rapido)
    a = extract_pdftotext(ARXIV)
    b = extract_pdftotext(ARXIV, formula_regions=None)
    assert a.markdown == b.markdown
    assert a.placeholders == {} and b.placeholders == {}


@pytest.mark.skipif(not PRESKILL.exists(), reason="Preskill zcache ausente (Z: não montado)")
def test_pdftotext_emits_placeholder_for_region(tmp_path):
    from pdf2md.formula_cropper import crop_formulas, formula_token
    regions = crop_formulas(PRESKILL, tmp_path, page_range=(4, 4))   # pg05 = índice 4, eq 5.12
    res = extract_pdftotext(PRESKILL, page_range=(4, 4), formula_regions=regions)
    tok = formula_token(regions[0])
    assert tok in res.markdown                         # placeholder na posição do math
    assert "Ncircuit" not in res.markdown              # math display cru foi substituído
    assert "circuit" in res.placeholders[tok].lower()  # raw original capturado p/ fallback
