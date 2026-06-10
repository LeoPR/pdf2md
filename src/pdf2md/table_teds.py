"""TEDS de tabela — nota estrutural por algoritmo (T075).

Cadeia: markdown → HTML (pandoc, gfm) → primeira <table> → normalização de
transporte → TEDS/TEDS-struct (table-recognition-metric, implementação
canônica do PubTabNet, arXiv:1911.10683). É o análogo de tabela do
page_wer/page_ssim (pixel_roundtrip): TEDS(GT md, md extraído de pdf₂) é a
nota de round-trip da camada tabela.

Normalização de transporte (princípio delta-E, adapter): `<thead>/<tbody>/
<tfoot>/<colgroup>` são artefato do CAMINHO (pipe→pandoc envelopa; HTML cru
não) — a estrutura canônica comparada é tr/th/td + row/colspan + texto.

Calibrado e medido em lab/e25 (T075, 2026-06-10): identidade 1.0 em 15/15;
perturbações monotônicas; marker atinge EXATAMENTE o teto do formato pipe em
tabelas com spans (TEDS marker == TEDS best-pipe por item) — a perda em
row/colspan é do markdown-transporte (T440), não do extractor. Escopo: medido
em render born-digital (Chrome) de templates próprios; LaTeX/scan pendentes.

Uso típico:

    from pdf2md.table_teds import table_roundtrip

    r = table_roundtrip(gt_md_text, extracted_md_text)
    print(r.teds, r.teds_struct, r.no_table)
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass

# table-recognition-metric (apted/lxml, pure-pip) vive no extra [tables] — medidor
# OPCIONAL, não infla o core de quem só quer pdf->md. Guard com erro CLARO.
try:
    from lxml import etree
    from lxml import html as _lxml_html
    from table_recognition_metric import TEDS
except ModuleNotFoundError as _e:  # pragma: no cover
    raise ModuleNotFoundError(
        f"table-teds (medidor TEDS de tabelas, T075) requer o extra [tables]: "
        f"pip install 'pdf2md-tool[tables]' (faltou: {_e.name})"
    ) from _e

_TEDS_CACHE: dict[bool, TEDS] = {}


# ============================================================================
# md/html → documento-tabela normalizado
# ============================================================================

def _normalize_table(t) -> None:
    """Remove camadas de transporte: thead/tbody/tfoot viram filhos diretos
    de <table>; colgroup sai. th/td, spans e texto permanecem intactos."""
    for sec in t.xpath("./thead|./tbody|./tfoot"):
        for child in list(sec):
            sec.addprevious(child)
        t.remove(sec)
    for cg in t.xpath("./colgroup"):
        t.remove(cg)


def first_table(html_text: str):
    """Primeira <table> de um fragmento/página HTML (ou None)."""
    try:
        tree = _lxml_html.fromstring(html_text)
    except Exception:
        return None
    if getattr(tree, "tag", None) == "table":   # raiz JÁ é a tabela (.// só vê descendentes)
        return tree
    return tree.find(".//table")


def table_doc_from_html(html_text: str) -> str | None:
    """Documento `<html><body><table>…` normalizado, pronto para teds_score."""
    t = first_table(html_text)
    if t is None:
        return None
    _normalize_table(t)
    return f"<html><body>{etree.tostring(t, encoding='unicode')}</body></html>"


def table_doc_from_md(md_text: str) -> str | None:
    """md (gfm) → primeira tabela como documento normalizado. Requer pandoc
    (external-capability; `pdf2md doctor`). None se o md não tem tabela."""
    from pdf2md.discovery import available, find_pandoc
    pandoc = find_pandoc()
    if not available(pandoc):
        raise RuntimeError(
            "table_doc_from_md requer pandoc (external; ver `pdf2md doctor`)")
    r = subprocess.run([str(pandoc), "-f", "gfm", "-t", "html"],
                       input=md_text, capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"pandoc falhou: {r.stderr[:300]}")
    return table_doc_from_html(r.stdout)


# ============================================================================
# TEDS
# ============================================================================

def teds_score(pred_doc: str, gt_doc: str, *, structure_only: bool = False) -> float:
    """TEDS(pred, gt) em [0,1]. structure_only ignora texto das células."""
    if structure_only not in _TEDS_CACHE:
        _TEDS_CACHE[structure_only] = TEDS(structure_only=structure_only)
    return _TEDS_CACHE[structure_only](pred_doc, gt_doc)


@dataclass
class TableTedsResult:
    teds: float
    teds_struct: float
    no_table: bool        # extração não produziu tabela alguma (nota 0 por definição)

    def summary(self) -> str:
        if self.no_table:
            return "TEDS 0.000 (sem tabela no output)"
        return f"TEDS {self.teds:.3f} (struct {self.teds_struct:.3f})"


def table_roundtrip(gt_md: str, pred_md: str) -> TableTedsResult:
    """Nota de tabela do round-trip: TEDS entre a 1ª tabela do GT md e a 1ª
    tabela do md extraído. Output sem tabela = 0.0 (perda total de estrutura —
    o caso pdftotext, medido 15/15 no e25)."""
    gt_doc = table_doc_from_md(gt_md)
    if gt_doc is None:
        raise ValueError("GT md não contém tabela — nada a medir")
    pred_doc = table_doc_from_md(pred_md) if pred_md else None
    if pred_doc is None:
        return TableTedsResult(0.0, 0.0, True)
    return TableTedsResult(
        teds=round(teds_score(pred_doc, gt_doc), 4),
        teds_struct=round(teds_score(pred_doc, gt_doc, structure_only=True), 4),
        no_table=False,
    )


# ============================================================================
# Teto do markdown-transporte (H3/T440)
# ============================================================================

def best_pipe_from_table(gt_doc: str) -> str:
    """Melhor pipe-table possível para uma tabela com row/colspan: expande
    células fundidas duplicando o texto. TEDS(best_pipe, gt) é o TETO que
    QUALQUER extractor limitado a pipe-tables pode atingir (medido: 0.749 nos
    spans do e25; marker bate o teto exatamente)."""
    tree = _lxml_html.fromstring(gt_doc)
    grid: dict[tuple[int, int], str] = {}
    occupied: set[tuple[int, int]] = set()
    for ri, tr in enumerate(tree.findall(".//tr")):
        ci = 0
        for cell in tr.xpath("./td|./th"):
            while (ri, ci) in occupied:
                ci += 1
            txt = (cell.text_content() or "").strip()
            for dr in range(int(cell.get("rowspan", 1))):
                for dc in range(int(cell.get("colspan", 1))):
                    grid[(ri + dr, ci + dc)] = txt
                    occupied.add((ri + dr, ci + dc))
            ci += int(cell.get("colspan", 1))
    n_rows = max(r for r, _ in grid) + 1
    n_cols = max(c for _, c in grid) + 1
    lines = []
    for r in range(n_rows):
        lines.append("| " + " | ".join(grid.get((r, c), "") for c in range(n_cols)) + " |")
        if r == 0:
            lines.append("|" + "---|" * n_cols)
    return "\n".join(lines)
