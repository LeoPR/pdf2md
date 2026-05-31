"""corpus/examples/_build_examples.py — gera os excertos livres in-repo.

Tier INREPO = "prova pronta": excertos pequenos de fontes LIVRES (public domain,
US-gov, arXiv non-exclusive) commitados no git, para qualquer um clonar e rodar o
pipeline sem baixar nada. NUNCA inclui material proprietary (N&C fica fora).

Reproduz a partir das fontes zcache via corpus/registry.resolve(). Rodar:
    python corpus/examples/_build_examples.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import fitz  # PyMuPDF

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
sys.path.insert(0, str(PROJECT / "corpus"))
from registry import resolve, SourceUnavailable  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# (doc_id fonte, arquivo destino, page_range_0based|None=copiar inteiro, licença, nota)
EXAMPLES = [
    ("arxiv_1706_03762", "arxiv_1706_03762_excerpt.pdf", (0, 2),
     "arXiv non-exclusive", "Vaswani et al. — 2 págs (título+abstract+intro)"),
    ("ia_mathematics00wils", "wilson_mathematics_excerpt.pdf", (40, 42),
     "public domain (pré-1928)", "Wilson, Mathematics — 2 págs (scan PD, math típica)"),
    ("cdc_mmwr_73_35_a1", "cdc_mmwr_73_35_a1.pdf", None,
     "US Gov public domain", "CDC MMWR — inteiro (~0.3MB, gov multi-col)"),
    ("irs_f1040_2025", "irs_f1040_2025.pdf", None,
     "US Gov public domain", "IRS Form 1040 — inteiro (~0.2MB, AcroForm)"),
]


def build_excerpt(src: Path, dst: Path, page_range: tuple[int, int] | None) -> int:
    if page_range is None:
        shutil.copy2(src, dst)
        return dst.stat().st_size
    a, b = page_range
    out = fitz.open()
    src_doc = fitz.open(src)
    out.insert_pdf(src_doc, from_page=a, to_page=b - 1)
    src_doc.close()
    out.save(dst, deflate=True, garbage=4)
    out.close()
    return dst.stat().st_size


def main() -> int:
    rows = []
    for doc_id, dst_name, prange, lic, note in EXAMPLES:
        try:
            src = resolve(doc_id, prefer_excerpt=False)
        except SourceUnavailable as exc:
            print(f"[SKIP] {doc_id}: fonte zcache ausente — {exc}")
            continue
        # se prefer full source: resolve devolve excerpt se tier indisponível; force full
        dst = HERE / dst_name
        size = build_excerpt(src, dst, prange)
        rows.append((dst_name, size, lic, note))
        print(f"[OK] {dst_name} ({size/1e3:.0f} KB) — {lic}")
    total = sum(r[1] for r in rows)
    print(f"\n[RESUMO] {len(rows)} exemplos, {total/1e6:.2f} MB total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
