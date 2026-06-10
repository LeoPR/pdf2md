"""Tests do formula_cropper (cropper estrutural CPU, src/pdf2md).

- Unit HERMÉTICOS das funções puras (_overlap, merge_regions, _is_complex): não
  precisam de PDF.
- Integração HERMÉTICA nos fixtures sintéticos commitados (T065:
  corpus/examples/sintetico/pdf/, renders KaTeX e Computer Modern com GT
  conhecido) — rodam em qualquer clone, sem zcache nem pandoc/chrome.
- Integração no Preskill (zcache) com skipif: caso real born-digital CM
  (licença read-only impede fixture in-repo).
"""
from pathlib import Path

import pytest

import re

from pdf2md.formula_cropper import (
    FORMULA_TOKEN_RE, FormulaRegion, _is_complex, _overlap, crop_formulas,
    detect_formula_regions, formula_token, merge_regions,
)

PRESKILL = Path("Z:/caches/corpus/pdf2md/preskill_ph219_ch5.pdf")
SINTETICO_PDF = Path(__file__).parent.parent / "corpus" / "examples" / "sintetico" / "pdf"


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


def test_merge_unions_block_indices():
    regs = [
        {"bbox": [0, 0, 10, 10], "label": None, "block_indices": [7],
         "signals": {"cmex": True, "density": 1.0, "n_lines": 1}},
        {"bbox": [5, 2, 15, 12], "label": "5.1", "block_indices": [8],
         "signals": {"cmex": False, "density": 0.5, "n_lines": 1}},
    ]
    merged = merge_regions(regs)
    assert len(merged) == 1
    assert merged[0]["block_indices"] == [7, 8]


def test_formula_token_survives_processing():
    from pdf2md.extractors import join_hyphenation, normalize_chars
    r = FormulaRegion(4, (0, 0, 1, 1), "5.12", False, {}, Path("d/pg04_5-12.png"), (7,))
    t = formula_token(r)
    assert normalize_chars(t) == t                 # ligaduras/aspas/NFC não tocam ⟦⟧
    assert join_hyphenation(t) == t                # sem hífen-com-espaço/quebra
    assert re.sub(r"\n{3,}", "\n\n", f"a\n\n{t}\n\nb") == f"a\n\n{t}\n\nb"   # imune ao colapso
    assert FORMULA_TOKEN_RE.search(t).group(1) == "pg04_5-12"   # chave = stem do crop
    assert not t.startswith("#") and not t[0].isdigit()         # nunca vira heading


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
def test_no_duplicate_regions_on_fragmented_page(tmp_path):
    # pg idx5: eqs 5.13/5.14 que o PyMuPDF quebra em âncoras DISJUNTAS não podem duplicar
    # (revisão adversarial e21-inline: merge antes do absorb gerava 3x a mesma região).
    regions = crop_formulas(PRESKILL, tmp_path, page_range=(5, 5))
    keys = [r.block_indices for r in regions]
    assert len(keys) == len(set(keys)), f"block_indices duplicados: {keys}"
    labels = [r.label for r in regions]
    assert labels.count("5.13") <= 1 and labels.count("5.14") <= 1


@pytest.mark.skipif(not PRESKILL.exists(), reason="Preskill zcache ausente (Z: não montado)")
def test_region_block_indices_populated(tmp_path):
    # block_indices (chave de alinhamento com o extrator) deve vir preenchido
    regions = crop_formulas(PRESKILL, tmp_path, page_range=(4, 4))
    r = next(r for r in regions if r.label == "5.12")
    assert r.block_indices and all(isinstance(i, int) for i in r.block_indices)


@pytest.mark.skipif(not PRESKILL.exists(), reason="Preskill zcache ausente (Z: não montado)")
def test_crop_preskill_matrix_is_flagged_complex(tmp_path):
    regions = crop_formulas(PRESKILL, tmp_path, page_range=(15, 15))  # matrizes
    matrices = [r for r in regions if r.is_complex]
    assert matrices, "deveria sinalizar ao menos 1 região matriz/multi-linha como complexa"


@pytest.mark.skipif(not PRESKILL.exists(), reason="Preskill zcache ausente (Z: não montado)")
def test_crop_inverted_page_range_raises(tmp_path):
    # page_range fora de faixa (lo>hi após clamp) → ValueError, não [] silencioso
    with pytest.raises(ValueError):
        crop_formulas(PRESKILL, tmp_path, page_range=(900, 999))


def test_crop_empty_pdf_raises(tmp_path, monkeypatch):
    class FakeDoc:
        def __len__(self): return 0
        def close(self): pass
    monkeypatch.setattr("pdf2md.formula_cropper.fitz.open", lambda *a, **k: FakeDoc())
    with pytest.raises(ValueError):
        crop_formulas("whatever.pdf", tmp_path)


# --- T065/T192: fixtures sintéticos in-repo (herméticos, 2 tipografias) -----

@pytest.mark.parametrize("rel", [
    "katex/formula_display/bayes.pdf",     # T192 H1: era 0 regiões em KaTeX
    "katex/formula_matriz/hadamard.pdf",
    "cm/formula_display/bayes.pdf",        # T192 H2: era crop com prosa engolida
    "cm/formula_matriz/hadamard.pdf",
])
def test_detecta_formula_fixture_sintetico(tmp_path, rel):
    """Render commitado (GT-por-construção) tem exatamente 1 fórmula display
    cercada de prosa: o cropper deve achá-la e o crop não pode conter prosa
    (os 2 modos de falha medidos no e24 ondas 2-3)."""
    regs = crop_formulas(SINTETICO_PDF / rel, tmp_path)
    assert regs, f"0 regiões em {rel}"
    assert all(r.crop_path.exists() for r in regs)
    import fitz
    d = fitz.open(SINTETICO_PDF / rel)
    try:
        clipped = " ".join(d[0].get_text(clip=fitz.Rect(*r.bbox)) for r in regs)
    finally:
        d.close()
    # prosa sintética: toda frase termina em "sob condições de contorno regulares"
    assert "contorno" not in clipped and "regulares" not in clipped, \
        f"crop de {rel} engoliu prosa: {clipped[:120]!r}"


# --- T192: detector multi-tipografia (KaTeX) --------------------------------

def _md2pdf_tools() -> bool:
    from pdf2md.discovery import available, find_chrome, find_pandoc
    return available(find_pandoc()) and available(find_chrome())


@pytest.mark.skipif(not _md2pdf_tools(), reason="pandoc/chrome ausentes")
def test_detecta_formula_em_pdf_katex(tmp_path):
    """e24 ondas 2-4: o detector era CEGO a fontes KaTeX (0 regiões em PDF do
    próprio md_to_pdf). Regressão: display math em render KaTeX é detectada e
    o crop não engole a prosa vizinha (segmento de linhas math)."""
    from pdf2md.pdfs import md_to_pdf
    md = tmp_path / "f.md"
    md.write_text(
        "# Doc\n\nUm parágrafo de prosa antes da fórmula, longo o suficiente "
        "para ser bloco de texto corrido de verdade.\n\n"
        "$$ H = \\frac{1}{\\sqrt{2}} \\begin{pmatrix} 1 & 1 \\\\ 1 & -1 \\end{pmatrix} $$\n\n"
        "E mais prosa depois da fórmula, também razoavelmente comprida.\n",
        encoding="utf-8",
    )
    pdf = md_to_pdf(md, tmp_path / "f.pdf")
    regs = crop_formulas(pdf, tmp_path / "crops")
    assert len(regs) >= 1                      # era 0 antes do T192
    assert regs[0].crop_path.exists()
    # crop puro: a prosa não entra no bbox (modo de falha da onda 3)
    import fitz
    d = fitz.open(pdf)
    txt = d[0].get_text(clip=fitz.Rect(*regs[0].bbox))
    d.close()
    assert "parágrafo" not in txt and "prosa" not in txt
