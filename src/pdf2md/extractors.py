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
from dataclasses import dataclass
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


def _page_to_md(page: fitz.Page, body: float) -> tuple[str, int]:
    out: list[str] = []
    headings = 0
    for block in page.get_text("dict").get("blocks", []):
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
    return "\n\n".join(out), headings


def extract_pdftotext(pdf_path: str | Path, page_range: tuple[int, int] | None = None) -> ExtractResult:
    """Extração estruturada via PyMuPDF text-layer (CPU). Prose fiel, math cru."""
    doc = fitz.open(str(pdf_path))
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
            md, h = _page_to_md(doc[i], body)
            headings += h
            if md.strip():
                parts.append(md)
    finally:
        doc.close()
    full = re.sub(r"\n{3,}", "\n\n", "\n\n".join(parts)).strip() + "\n"
    return ExtractResult(markdown=full, n_pages=n, backend="pdftotext", n_headings=headings)


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
