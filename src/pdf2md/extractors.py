"""Extratores CPU-only promovidos das bancadas e19 (pdftotext/PyMuPDF) e e20
(Tesseract OCR) para o `src/`. São os PRIMARYs CPU que o roteador (T090) escolhe
em `--rapido`/`--low-resource` e na guarda de scan.

Cada extrator devolve markdown (string) + metadados. Determinísticos, sem GPU,
sem rede. Estruturação mínima: reconstrói parágrafos, normaliza ligaturas/hífens,
detecta headings (numeração de seção + tamanho de fonte). NÃO converte math para
LaTeX (limite do caminho CPU — math fica Unicode cru).

Medição de fidelidade: ver lab/e19 (WER-prosa) e lab/e20 (scan WER 0.052 impresso).
"""
from __future__ import annotations

import re
import shutil
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF

_LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl"}
_CURLY = {"“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "−": "-"}
_SECTION_RE = re.compile(r"^(\d+)((?:\.\d+)*)\s+[A-Z][a-z]")
# linha = só número curto (page number). 1-3 dígitos p/ não confundir com ano
# isolado (ex. "2024") que costuma ser conteúdo, não número de página.
_PAGENUM_RE = re.compile(r"^\d{1,3}$")


@dataclass
class ExtractResult:
    markdown: str
    n_pages: int          # comprimento do DOCUMENTO fonte (não nº de páginas extraídas)
    backend: str
    n_headings: int = 0
    # token de placeholder -> texto cru original do bloco (fallback se pix2tex vier vazio).
    # Só populado quando extract_pdftotext recebe formula_regions (caminho pix2tex inline).
    placeholders: dict = field(default_factory=dict)


def normalize_chars(s: str) -> str:
    for k, v in _LIGATURES.items():
        s = s.replace(k, v)
    for k, v in _CURLY.items():
        s = s.replace(k, v)
    return unicodedata.normalize("NFC", s)


def join_hyphenation(text: str) -> str:
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"(\w)- (\w)", r"\1\2", text)
    return text


def _page_indices(n: int, page_range: tuple[int, int] | None) -> range:
    if page_range is None:
        return range(n)
    a, b = page_range
    return range(max(0, a), min(n, b + 1))


def _dominant_size(page: fitz.Page) -> float:
    sizes: Counter = Counter()
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                sizes[round(span["size"], 1)] += len(span.get("text", ""))
    return sizes.most_common(1)[0][0] if sizes else 10.0


def _heading_level(raw: str, max_size: float, body: float) -> int:
    s = raw.strip()
    if len(s) < 70:
        m = _SECTION_RE.match(s)
        if m:
            return min(2 + m.group(2).count("."), 6)   # "4"->## "4.1"->### "4.1.1"->####
    if re.search(r"[A-Za-z]{3,}", s):
        if max_size >= body * 1.6:
            return 2
        if max_size >= body * 1.25:
            return 3
    return 0


def _blocks_raw_text(raw_blocks, idxs) -> str:
    """Texto cru normalizado dos blocos de uma região (fallback se pix2tex vier vazio)."""
    parts = []
    for i in idxs:
        if not (0 <= i < len(raw_blocks)):
            continue
        texts = ["".join(sp.get("text", "") for sp in ln.get("spans", []))
                 for ln in raw_blocks[i].get("lines", [])]
        joined = " ".join(t.strip() for t in texts if t.strip())
        if joined:
            parts.append(joined)
    return normalize_chars(join_hyphenation(" ".join(parts))).strip()


def _page_to_md(page: fitz.Page, body: float, regions=None) -> tuple[str, int, dict]:
    """Markdown de UMA página. Se `regions` (FormulaRegion já cropadas desta página)
    dado, emite um placeholder no lugar do math cru — alinhado por ÍNDICE de bloco
    (region.block_indices referem o mesmo array cru que enumeramos aqui)."""
    raw_blocks = page.get_text("dict").get("blocks", [])
    emit_at: dict[int, str] = {}      # raw_idx do 1º bloco da região -> token
    suppress: set[int] = set()        # raw_idx dos demais blocos da região (matriz)
    placeholders: dict[str, str] = {}
    if regions:
        from pdf2md.formula_cropper import formula_token   # lazy: fast-path (--rapido) sem PIL
        for r in regions:
            idxs = [i for i in r.block_indices if 0 <= i < len(raw_blocks)]
            if not idxs:
                continue
            emit_idx = min(idxs)
            if emit_idx in emit_at:       # colisão (2 regiões compartilham o 1º bloco): suprime
                suppress.update(idxs)     # do corpo e deixa a 2ª virar órfã (sem token) → ao fim
                continue
            token = formula_token(r)
            emit_at[emit_idx] = token
            suppress.update(i for i in idxs if i != emit_idx)
            placeholders[token] = _blocks_raw_text(raw_blocks, idxs)

    out: list[str] = []
    headings = 0
    for idx, block in enumerate(raw_blocks):
        if idx in emit_at:                # math cru -> placeholder (pula heading/pagenum)
            out.append(emit_at[idx])
            continue
        if idx in suppress:               # bloco coberto pelo crop → fora do corpo (consistente)
            continue
        lines = block.get("lines", [])
        if not lines:
            continue
        texts, max_size = [], 0.0
        for line in lines:
            spans = line.get("spans", [])
            if not spans:
                continue
            texts.append("".join(sp.get("text", "") for sp in spans))
            max_size = max(max_size, *(sp.get("size", 0.0) for sp in spans))
        raw = normalize_chars(join_hyphenation(" ".join(t.strip() for t in texts if t.strip()))).strip()
        if not raw or _PAGENUM_RE.match(raw):     # dropa page-number solto
            continue
        level = _heading_level(raw, max_size, body)
        if level:
            out.append("#" * level + " " + raw)
            headings += 1
        else:
            out.append(raw)
    return "\n\n".join(out), headings, placeholders


def extract_pdftotext(pdf_path: str | Path, page_range: tuple[int, int] | None = None,
                      formula_regions=None) -> ExtractResult:
    """Extração estruturada via PyMuPDF text-layer (CPU). Prose fiel, math cru.

    `formula_regions` (FormulaRegion já cropadas, do caminho pix2tex inline) é OPCIONAL:
    quando None (default) o comportamento é byte-idêntico ao histórico; quando dado, o
    math cru de cada região vira um placeholder (posição inline) e ExtractResult.placeholders
    mapeia token->texto-cru-original p/ fallback. Alinhamento por block_indices (exato).
    """
    by_page: dict[int, list] = {}
    for r in (formula_regions or []):
        by_page.setdefault(r.page_index, []).append(r)
    doc = fitz.open(str(pdf_path))
    placeholders: dict = {}
    try:
        n = len(doc)
        if n == 0:
            raise ValueError(f"PDF sem páginas: {pdf_path}")
        idxs = _page_indices(n, page_range)
        if len(idxs) == 0:
            raise ValueError(f"page_range {page_range} vazio/fora do documento ({n}pg)")
        body = _dominant_size(doc[idxs.start])
        parts, headings = [], 0
        for i in idxs:
            md, h, ph = _page_to_md(doc[i], body, regions=by_page.get(i))
            headings += h
            placeholders.update(ph)
            if md.strip():
                parts.append(md)
    finally:
        doc.close()
    full = re.sub(r"\n{3,}", "\n\n", "\n\n".join(parts)).strip() + "\n"
    return ExtractResult(markdown=full, n_pages=n, backend="pdftotext", n_headings=headings,
                         placeholders=placeholders)


def tesseract_cmd() -> str | None:
    """Caminho do binário tesseract (PATH ou install padrão Windows)."""
    if shutil.which("tesseract"):
        return "tesseract"
    win = Path(r"C:/Program Files/Tesseract-OCR/tesseract.exe")
    return str(win) if win.exists() else None


def extract_tesseract(pdf_path: str | Path, page_range: tuple[int, int] | None = None,
                      dpi: int = 300) -> ExtractResult:
    """OCR CPU via Tesseract para scan (renderiza página → image_to_string).

    Requer pytesseract + binário tesseract. Scan impresso forte (e20 WER 0.052);
    manuscrito falha de forma honesta (sem alucinar). Math fica cru.
    """
    import pytesseract
    from PIL import Image

    cmd = tesseract_cmd()
    if cmd is None:
        raise RuntimeError("tesseract não encontrado (instalar UB-Mannheim.TesseractOCR).")
    pytesseract.pytesseract.tesseract_cmd = cmd

    doc = fitz.open(str(pdf_path))
    try:
        n = len(doc)
        if n == 0:
            raise ValueError(f"PDF sem páginas: {pdf_path}")
        idxs = _page_indices(n, page_range)
        if len(idxs) == 0:
            raise ValueError(f"page_range {page_range} vazio/fora do documento ({n}pg)")
        parts = []
        for i in idxs:
            pm = doc[i].get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
            txt = normalize_chars(join_hyphenation(pytesseract.image_to_string(img, lang="eng"))).strip()
            if txt:
                parts.append(txt)
    finally:
        doc.close()
    full = re.sub(r"\n{3,}", "\n\n", "\n\n".join(parts)).strip() + "\n"
    return ExtractResult(markdown=full, n_pages=n, backend="tesseract")
