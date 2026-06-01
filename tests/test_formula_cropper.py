"""Tests do formula_cropper (cropper estrutural CPU, src/pdf2md).

- Unit HERMÉTICOS das funções puras (_overlap, merge_regions, _is_complex): não
  precisam de PDF.
- Integração no Preskill (zcache) com skipif: born-digital Computer Modern é o
  único caso validado; não há fixture in-repo (licença read-only do Preskill +
  examples in-repo não têm display math). Mesmo padrão skipif dos outros testes.
"""
from pathlib import Path

import pytest

from pdf2md.formula_cropper import (
    FormulaRegion, _is_complex, _overlap, crop_formulas,
    detect_formula_regions, merge_regions,
)

PRESKILL = Path("Z:/caches/corpus/pdf2md/preskill_ph219_ch5.pdf")


# --- unit herméticos -------------------------------------------------------

def test_overlap_true_false():
    assert _overlap([0, 0, 10, 10], [5, 5, 15, 15])
    assert not _overlap([0, 0, 10, 10], [20, 20, 30, 30])
    assert _overlap([0, 0, 10, 10], [10.5, 0, 20, 10], eps=1.0)   # quase tocando, eps une
    assert not _overlap([0, 0, 10, 10], [12, 0, 20, 10], eps=1.0)


def test_merge_overlapping_into_one():
    regs = [
        {"bbox": [0, 0, 10, 10], "label": None, "signals": {"cmex": True, "density": 1.0, "n_lines": 1}},
        {"bbox": [5, 2, 15, 12], "label": "5.1", "signals": {"cmex": False, "density": 0.5, "n_lines": 1}},
    ]
    merged = merge_regions(regs)
    assert len(merged) == 1
    assert merged[0]["label"] == "5.1"                  # herda o label não-None
    assert merged[0]["bbox"] == [0, 0, 15, 12]          # união
    assert merged[0]["signals"]["merged_from"] == 2
    assert merged[0]["signals"]["cmex"] is True         # OR dos cmex


def test_merge_disjoint_stay_separate():
    regs = [
        {"bbox": [0, 0, 10, 10], "label": "5.1", "signals": {"cmex": False, "density": 1.0, "n_lines": 1}},
        {"bbox": [0, 50, 10, 60], "label": "5.2", "signals": {"cmex": False, "density": 1.0, "n_lines": 1}},
    ]
    assert len(merge_regions(regs)) == 2


def test_is_complex_matrix_vs_single_line():
    assert _is_complex({"merged_from": 3, "cmex": True, "n_lines": 6})       # matriz merged
    assert _is_complex({"merged_from": 1, "cmex": True, "n_lines": 7})       # tall cmex (cases)
    assert not _is_complex({"merged_from": 1, "cmex": True, "n_lines": 4})   # display linha-única (5.12)
    assert not _is_complex({"merged_from": 1, "cmex": False, "n_lines": 2})  # 5.17


# --- integração (Preskill zcache; pula sem Z:) -----------------------------

@pytest.mark.skipif(not PRESKILL.exists(), reason="Preskill zcache ausente (Z: não montado)")
def test_crop_preskill_finds_eq512(tmp_path):
    regions = crop_formulas(PRESKILL, tmp_path, page_range=(4, 4))   # pg05 = índice 4
    labels = {r.label for r in regions}
    assert "5.12" in labels
    r = next(r for r in regions if r.label == "5.12")
    assert r.crop_path and r.crop_path.exists()
    assert not r.is_complex                                   # 5.12 é linha-única


@pytest.mark.skipif(not PRESKILL.exists(), reason="Preskill zcache ausente (Z: não montado)")
def test_crop_preskill_pg07_three_eqs(tmp_path):
    regions = crop_formulas(PRESKILL, tmp_path, page_range=(6, 6))   # pg07 = índice 6
    labels = {r.label for r in regions}
    assert {"5.16", "5.17", "5.18"} <= labels                # recall das 3 display


@pytest.mark.skipif(not PRESKILL.exists(), reason="Preskill zcache ausente (Z: não montado)")
def test_crop_preskill_matrix_is_flagged_complex(tmp_path):
    regions = crop_formulas(PRESKILL, tmp_path, page_range=(15, 15))  # matrizes
    matrices = [r for r in regions if r.is_complex]
    assert matrices, "deveria sinalizar ao menos 1 região matriz/multi-linha como complexa"


def test_crop_empty_pdf_raises(tmp_path, monkeypatch):
    class FakeDoc:
        def __len__(self): return 0
        def close(self): pass
    monkeypatch.setattr("pdf2md.formula_cropper.fitz.open", lambda *a, **k: FakeDoc())
    with pytest.raises(ValueError):
        crop_formulas("whatever.pdf", tmp_path)
