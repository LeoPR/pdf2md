"""Cropper estrutural de fórmula DISPLAY — CPU, sem torch/marker (T090 / Lab e21).

Lê o metadata do próprio PDF (PyMuPDF: fonte + bbox por span) para localizar
regiões de equação DISPLAY em PDF born-digital e recortá-las como PNG p/ um
math-OCR de recorte (pix2tex). Fecha a peça que faltava no caminho CPU:

    pdftotext (prosa) + formula_cropper (este) + pix2tex (math) = LaTeX 100% CPU

Depende SÓ de pymupdf + pillow (já no venv geral) — por isso vive em src/ sem
puxar torch. O pix2tex segue externo (subprocess, venv próprio), igual marker.

União de sinais (medida em e21, GT Preskill ch5):
  (a) fonte de delimitador/operador grande  — CMEX / *EX* / MSAM / MSBM (pdfTeX)
  (b) densidade-math alta + bloco indentado/centrado
  (label de equação `(N.NN)` é usado só p/ ASSOCIAR número e EXCLUIR do crop)
depois: merge de fragmentos sobrepostos + absorção por banda-y (recupera brackets
e metades de matriz) + trim do label.

FRONTEIRA MEDIDA (e21 onda 2): pix2tex lê bem display de LINHA ÚNICA (sim ~0.80),
mas MATRIZ degrada (~0.50: trunca eq longa, embaralha 2×2). `FormulaRegion.is_complex`
sinaliza as regiões matriz/multi-linha p/ o roteador rebaixar a confiança.

LIMITES: validado em Computer Modern (pdfTeX). Display alinhado à esquerda, PDF
não-CM (Word/OpenType-math) e inline math ficam fora — sinal diferente, outra onda.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

# --- parâmetros do detector (medidos em e21) -------------------------------
DPI = 300               # sweet spot p/ pix2tex (e21): nítido sem upscaling
MARGIN_PT = 4.0         # folga pequena: +grande captura a linha vizinha → array-lixo
YBAND_EPS = 1.0         # tolerância vertical p/ absorver peças na mesma banda-y
INDENT_PT = 16.0        # x0 do bloco > margem-corpo + isto (display é offset)
MIN_WIDTH_PT = 28.0     # largura mínima da região (mata glifo solto de diagrama)
MIN_CHARS = 4           # texto mínimo da região (idem)
DENSITY_MIN = 0.30      # fração de chars math (sozinha não basta; ver _is_anchor)
COMPLEX_LINES = 5       # n_lines >= isto (com cmex) → multi-linha complexa

MATH_BIG_FONT = re.compile(r"(CMEX|MSAM|MSBM|EX\d)", re.I)          # delimitadores grandes
MATH_FONT = re.compile(r"(CMMI|CMSY|CMEX|MSAM|MSBM|EX\d|MI\d|SY\d)", re.I)
PROSE_FONT = re.compile(r"(CMR|CMTI|CMBX|CMSL|CMTT)\d", re.I)
EQNUM_RE = re.compile(r"^\(\d+(?:\.\d+)?[a-z]?\)$")


@dataclass
class FormulaRegion:
    page_index: int
    bbox: tuple[float, float, float, float]   # pt (x0, y0, x1, y1), label já excluído
    label: str | None = None                  # número da eq, ex. "5.12"
    is_complex: bool = False                   # matriz/multi-linha → pix2tex baixa confiança
    signals: dict = field(default_factory=dict)
    crop_path: Path | None = None


# ---------------------------------------------------------------------------
# helpers de bbox
# ---------------------------------------------------------------------------

def _spans(block):
    return [s for ln in block["lines"] for s in ln["spans"]]


def _overlap(a, b, eps: float = 1.0) -> bool:
    """bboxes [x0,y0,x1,y1] se sobrepõem (com folga eps)?"""
    return not (a[2] + eps < b[0] or b[2] + eps < a[0]
                or a[3] + eps < b[1] or b[3] + eps < a[1])


def _body_left(blocks) -> float:
    """Margem esquerda do corpo = menor x0 entre blocos majoritariamente prosa."""
    xs = []
    for b in blocks:
        sp = _spans(b)
        txt = "".join(s["text"] for s in sp)
        prose = sum(1 for s in sp if PROSE_FONT.search(s["font"]))
        if len(txt) > 40 and sp and prose >= 0.6 * len(sp):
            xs.append(b["bbox"][0])
    return min(xs) if xs else min((b["bbox"][0] for b in blocks), default=0.0)


def _is_prose_block(b) -> bool:
    """Bloco majoritariamente prosa de corpo (não absorver na banda da eq)."""
    sp = _spans(b)
    txt = "".join(s["text"] for s in sp)
    prose = sum(1 for s in sp if PROSE_FONT.search(s["font"]))
    return len(txt) > 40 and bool(sp) and prose >= 0.6 * len(sp)


def merge_regions(regions: list[dict]) -> list[dict]:
    """Une regiões com bbox sobreposto (matriz/eq multi-linha que o PyMuPDF quebra
    em vários blocos → 1 região). Equações distintas não se sobrepõem (bandas-y
    separadas por prosa) → ficam separadas."""
    parent = list(range(len(regions)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(regions)):
        for j in range(i + 1, len(regions)):
            if _overlap(regions[i]["bbox"], regions[j]["bbox"]):
                parent[find(i)] = find(j)

    groups: dict[int, list[dict]] = {}
    for i, r in enumerate(regions):
        groups.setdefault(find(i), []).append(r)

    merged = []
    for g in groups.values():
        bx = [r["bbox"] for r in g]
        merged.append({
            "bbox": [min(b[0] for b in bx), min(b[1] for b in bx),
                     max(b[2] for b in bx), max(b[3] for b in bx)],
            "label": next((r["label"] for r in g if r["label"]), None),
            "signals": {"cmex": any(r["signals"]["cmex"] for r in g),
                        "density": max(r["signals"]["density"] for r in g),
                        "n_lines": sum(r["signals"]["n_lines"] for r in g),
                        "merged_from": len(g)},
        })
    return merged


def _absorb_band(region: dict, blocks) -> None:
    """Cresce a bbox p/ incluir blocos NÃO-prosa na mesma banda-y (brackets grandes,
    coeficientes, metades de matriz que os filtros de anchor excluíram). Conserta o
    clipping horizontal de matriz (e21 onda 2)."""
    changed = True
    while changed:
        changed = False
        ry0, ry1 = region["bbox"][1], region["bbox"][3]
        for b in blocks:
            if _is_prose_block(b):
                continue
            bb = b["bbox"]
            bcy = (bb[1] + bb[3]) / 2
            if not ((ry0 - YBAND_EPS <= bcy <= ry1 + YBAND_EPS) or _overlap(region["bbox"], bb)):
                continue
            nb = [min(region["bbox"][0], bb[0]), min(region["bbox"][1], bb[1]),
                  max(region["bbox"][2], bb[2]), max(region["bbox"][3], bb[3])]
            if nb != region["bbox"]:
                region["bbox"] = nb
                changed = True


def _trim_label(region: dict, label_boxes) -> None:
    """Tira o label de equação (N.NN) à direita do crop e registra o número."""
    for lab, lbox in label_boxes:
        lcy = (lbox[1] + lbox[3]) / 2
        if region["bbox"][1] <= lcy <= region["bbox"][3] and lbox[0] >= region["bbox"][0]:
            region["bbox"][2] = min(region["bbox"][2], lbox[0] - 2)
            region["label"] = region["label"] or lab


def _is_complex(signals: dict) -> bool:
    """Matriz/multi-linha → pix2tex baixa confiança (e21 onda 2: sim ~0.50)."""
    return signals.get("merged_from", 1) >= 2 or (
        signals.get("cmex") and signals.get("n_lines", 1) >= COMPLEX_LINES)


# ---------------------------------------------------------------------------
# detecção
# ---------------------------------------------------------------------------

def detect_formula_regions(page, page_index: int = 0) -> list[FormulaRegion]:
    """Regiões de fórmula display de UMA página (bbox em pt, label excluído)."""
    blocks = [b for b in page.get_text("dict")["blocks"]
              if b.get("type", 0) == 0 and b.get("lines")]
    if not blocks:
        return []
    body_left = _body_left(blocks)

    label_boxes = []   # (label, bbox) de TODO span eq-number
    anchors = []
    for b in blocks:
        sp = _spans(b)
        label_ids = {id(s) for s in sp if EQNUM_RE.match(s["text"].strip())}
        for s in sp:
            if id(s) in label_ids:
                label_boxes.append((s["text"].strip().strip("()"), s["bbox"]))
        label = next((s["text"].strip().strip("()") for s in sp if id(s) in label_ids), None)
        body = [s for s in sp if id(s) not in label_ids]
        body_txt = "".join(s["text"] for s in body).strip()
        if not body_txt:
            continue

        tot = sum(len(s["text"]) for s in body) or 1
        math_chars = sum(len(s["text"]) for s in body if MATH_FONT.search(s["font"]))
        density = math_chars / tot
        has_cmex = any(MATH_BIG_FONT.search(s["font"]) for s in body)
        n_lines = len(b["lines"])
        indented = b["bbox"][0] - body_left > INDENT_PT
        bx = [s["bbox"] for s in body]
        width = max(c[2] for c in bx) - min(c[0] for c in bx)

        # ÂNCORA = peça math forte, indentada, larga e não-trivial. Brackets/coeficientes
        # (peças estreitas) NÃO são âncora; _absorb_band os recupera pela banda-y depois.
        is_math = has_cmex or density >= DENSITY_MIN
        if not (is_math and indented and width >= MIN_WIDTH_PT and len(body_txt) >= MIN_CHARS):
            continue
        anchors.append({
            "bbox": [min(c[0] for c in bx), min(c[1] for c in bx),
                     max(c[2] for c in bx), max(c[3] for c in bx)],
            "label": label,
            "signals": {"cmex": has_cmex, "density": round(density, 2),
                        "n_lines": n_lines},
        })

    anchors = merge_regions(anchors)
    out = []
    for r in anchors:
        _absorb_band(r, blocks)
        r["bbox"] = [r["bbox"][0] - MARGIN_PT, r["bbox"][1] - MARGIN_PT,
                     r["bbox"][2] + MARGIN_PT, r["bbox"][3] + MARGIN_PT]
        _trim_label(r, label_boxes)
        out.append(FormulaRegion(
            page_index=page_index,
            bbox=tuple(r["bbox"]),
            label=r["label"],
            is_complex=_is_complex(r["signals"]),
            signals=r["signals"],
        ))
    return out


def crop_formulas(pdf_path: str | Path, out_dir: str | Path, *,
                  page_range: tuple[int, int] | None = None,
                  dpi: int = DPI) -> list[FormulaRegion]:
    """Detecta e recorta as fórmulas display de um PDF em PNGs (out_dir).

    page_range = (lo, hi) 0-based inclusivo; None = doc inteiro. Devolve as
    `FormulaRegion` com `crop_path` preenchido. Fecha o doc no fim.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_path))
    try:
        n = len(doc)
        if n == 0:
            raise ValueError(f"PDF sem páginas: {pdf_path}")
        lo, hi = (0, n - 1) if page_range is None else page_range
        lo, hi = max(0, lo), min(n - 1, hi)
        scale = dpi / 72.0
        regions: list[FormulaRegion] = []
        for idx in range(lo, hi + 1):
            page = doc[idx]
            page_regs = detect_formula_regions(page, idx)
            if not page_regs:
                continue
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            for i, r in enumerate(page_regs):
                x0, y0, x1, y1 = (int(v * scale) for v in r.bbox)
                crop = img.crop((max(0, x0), max(0, y0),
                                 min(x1, pix.width), min(y1, pix.height)))
                tag = (r.label or f"eq{i}").replace(".", "-")
                p = out_dir / f"pg{idx:02d}_{tag}.png"
                crop.save(p)
                r.crop_path = p
                regions.append(r)
        return regions
    finally:
        doc.close()
