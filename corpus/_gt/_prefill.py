"""Gerador de pré-fills `.expected.md.draft` para o mini-corpus GT humano (T060).

Para cada (doc_id, pdf_path, pages_target):
1. Extrai texto da(s) página(s) via PyMuPDF (text-layer direto, sem OCR)
2. Aplica formatação mínima como ponto de partida (headings óbvios,
   paragrafos quebrados, math em $..$)
3. Grava em `<doc_id>/pg<NN>.expected.md.draft`
4. Cria `<doc_id>/pg<NN>.note.md` em branco (copia template se não existir)

Não tenta substituir marker — é pre-fill mínimo. Humano polirá manualmente.

Rodar:
    python corpus/_gt/_prefill.py
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import fitz  # PyMuPDF

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent
PROJECT = ROOT.parent.parent
TEMPLATE_NOTE = ROOT / "_TEMPLATE_note.md"

# Resolver central de fontes (corpus/registry.py) — substitui paths hardcoded.
sys.path.insert(0, str(PROJECT / "corpus"))
from registry import resolve, SourceUnavailable  # noqa: E402


# (doc_id, [page_indices_0based], categoria) — o path vem de resolve(doc_id).
TARGETS = [
    (
        "nielsen_chuang_cap4",
        # pgs 199, 200, 204 do livro = indices 198, 199, 203 (1-based to 0-based)
        [198, 199, 203],
        "math_denso + formula_multilinha (Theorem 4.1 Z-Y decomposition pg 204)",
    ),
    (
        "preskill_ph219_ch5",
        # Originalmente [0, 1] mas eram cover + TOC (sem math).
        # [2, 4, 6, 14] = pg3 + pg5 + pg7 + pg15 (T060 ciclo #1, #2, #3, #4)
        # Decisão 2026-05-18 ao iniciar afunilamento T060. Estendido pg7+pg15 em 2026-05-30.
        [2, 4, 6, 14],
        "notes_1col math_denso",
    ),
    (
        "arxiv_1706_03762",
        [2],
        "paper_2col math_moderado",
    ),
    (
        "arxiv_2106_05919v2",
        [29],
        "math_heavy",
    ),
    (
        "cdc_mmwr_73_35_a1",
        [0],
        "gov_multicol tabela_complexa",
    ),
]


def extract_page_text(pdf_path: Path, page_idx: int) -> str:
    """Extrai texto cru da página via PyMuPDF (text-layer)."""
    doc = fitz.open(pdf_path)
    if page_idx >= len(doc):
        doc.close()
        return f"<página {page_idx} fora do range do PDF (total {len(doc)})>"
    text = doc[page_idx].get_text()
    doc.close()
    return text


def basic_format_md(text: str, doc_id: str, page_1based: int) -> str:
    """Formatação mínima: comentário de fonte + texto + dicas inline.

    Não tenta gerar GFM final — é só ponto de partida humano.
    """
    lines = [
        f"<!-- pre-fill draft — {doc_id} pg {page_1based} (PyMuPDF text-layer cru) -->",
        f"<!-- ATENÇÃO: este é apenas pre-fill. Curar manualmente comparando ao PDF. -->",
        f"<!-- Renomear para `pg{page_1based:02d}.expected.md` quando canônico. -->",
        "",
    ]
    # Dividir em parágrafos por linhas em branco múltiplas
    paragraphs = re.split(r"\n\s*\n", text.strip())
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Heurística: se uma linha curta isolada virar fonte de heading?
        lines_p = para.split("\n")
        # Junta linhas de um parágrafo (remove quebras intra-parágrafo)
        joined = " ".join(line.strip() for line in lines_p if line.strip())
        # Sugere math se há padrão tipo "X = Y" ou simbolos especiais
        if re.search(r"[αβγδλΣΦΨΩ∂∇∫≥≤≠∈]", joined) and not joined.startswith("$"):
            lines.append(f"<!-- math? --> {joined}")
        else:
            lines.append(joined)
        lines.append("")
    return "\n".join(lines)


def ensure_note(out_dir: Path, page_1based: int) -> None:
    """Cria `<page>.note.md` se não existir, copiando do template."""
    note_path = out_dir / f"pg{page_1based:02d}.note.md"
    if not note_path.exists():
        if TEMPLATE_NOTE.exists():
            shutil.copy2(TEMPLATE_NOTE, note_path)
        else:
            note_path.write_text("# Notas\n\n(pendente)\n", encoding="utf-8")


def main() -> int:
    skipped = []
    created = []
    for doc_id, page_indices, categoria in TARGETS:
        try:
            pdf_path = resolve(doc_id)
        except SourceUnavailable as exc:
            print(f"[SKIP] {doc_id}: {exc}")
            skipped.append(doc_id)
            continue
        out_dir = ROOT / doc_id
        out_dir.mkdir(exist_ok=True)
        for idx in page_indices:
            page_1based = idx + 1
            draft_path = out_dir / f"pg{page_1based:02d}.expected.md.draft"
            if draft_path.exists():
                print(f"[skip-existe] {draft_path.relative_to(ROOT)}")
                continue
            text = extract_page_text(pdf_path, idx)
            md = basic_format_md(text, doc_id, page_1based)
            draft_path.write_text(md, encoding="utf-8")
            ensure_note(out_dir, page_1based)
            created.append(str(draft_path.relative_to(ROOT)))
            print(f"[OK] {draft_path.relative_to(ROOT)} ({categoria})")

    # README de cada doc
    for doc_id, page_indices, categoria in TARGETS:
        if doc_id in skipped:
            continue
        out_dir = ROOT / doc_id
        readme = out_dir / "README.md"
        if not readme.exists():
            content = [
                f"# {doc_id}",
                "",
                f"**Categoria:** {categoria}",
                "",
                f"**PDF source:** via `corpus/registry.py` → `resolve(\"{doc_id}\")`",
                "",
                f"**Páginas alvo:** {', '.join(str(i+1) for i in page_indices)}",
                "",
                "## Arquivos",
                "",
            ]
            for idx in page_indices:
                p1b = idx + 1
                content.append(f"- `pg{p1b:02d}.expected.md.draft` — pre-fill (PyMuPDF)")
                content.append(f"- `pg{p1b:02d}.expected.md` — canônico (criar via rename do draft após curadoria)")
                content.append(f"- `pg{p1b:02d}.note.md` — notas da curadoria")
                content.append("")
            content.append("Ver [`../README.md`](../README.md) para fluxo geral de curadoria.")
            readme.write_text("\n".join(content), encoding="utf-8")
            created.append(str(readme.relative_to(ROOT)))

    print(f"\n[RESUMO]")
    print(f"  criados: {len(created)} arquivos")
    print(f"  pulados: {len(skipped)} docs (PDFs não encontrados)")
    if skipped:
        print(f"    {', '.join(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
