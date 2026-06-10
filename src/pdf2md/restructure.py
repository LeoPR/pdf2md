"""Reorganiza saída do marker em capítulos via TOC do PDF.

Usa:
- Marker MD output (single file, todo o livro)
- Marker image files nomeados `_page_N_*.jpeg`
- PyMuPDF TOC do PDF original (fronteiras de capítulo com pgs start/end)

Produz: `target/<chapter>/<chapter>.md + images/`, e `target/index.md` agregado.

Pode ser usado como módulo (`from pdf2md.restructure import restructure`) ou
script standalone (compat com `python src/restructure.py PDF MARKER TARGET`).
"""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF


@dataclass
class Chapter:
    """Fronteira de capítulo. `header_re` é None para front matter (começa no início)."""
    id: str           # ex.: "04_quantum_circuits", "app_appendix_2_group_theory"
    title: str        # ex.: "4. Quantum circuits"
    start: int        # página 1-indexed
    end: int          # página 1-indexed (inclusiva)
    header_re: str | None  # regex pra achar heading no MD; None = início do arquivo


def slugify(s: str) -> str:
    """`Quantum Circuits` → `quantum_circuits`. Trunca em 60 chars."""
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s[:60]


def get_chapter_boundaries(pdf_path: Path) -> list[Chapter]:
    """Detecta fronteiras via TOC do PDF.

    Heurística para livro N&C-like: nível 2 numerado = capítulo, nível 1 com
    'Appendix' / 'Bibliography' / 'Index' = apêndice. Funciona em livros
    com TOC bem-comportado; outros formatos podem retornar lista vazia ou parcial.
    """
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    total_pages = len(doc)
    chapters: list[Chapter] = []

    # Front matter: termina onde o primeiro capítulo numerado começa
    fm_end = None
    for level, title, page in toc:
        m = re.match(r"^(\d+)\s+(.+)$", title)
        if m and level == 2:
            fm_end = page - 1
            break

    if fm_end:
        chapters.append(Chapter(
            id="00_front_matter", title="Front Matter",
            start=1, end=fm_end, header_re=None,
        ))

    # Capítulos numerados
    numbered: list[tuple[int, str, int]] = []
    for level, title, page in toc:
        m = re.match(r"^(\d+)\s+(.+)$", title)
        if m and level == 2:
            numbered.append((int(m.group(1)), m.group(2), page))

    for i, (num, title, start) in enumerate(numbered):
        end = numbered[i + 1][2] - 1 if i + 1 < len(numbered) else total_pages
        chapters.append(Chapter(
            id=f"{num:02d}_{slugify(title)}",
            title=f"{num}. {title}",
            start=start, end=end,
            header_re=rf"^#+\s+{num}\s+\S",
        ))

    # Apêndices (level 1)
    appendices: list[tuple[str, int]] = []
    for level, title, page in toc:
        if level == 1 and title.startswith("Appendix"):
            appendices.append((title, page))
    for level, title, page in toc:
        if level == 1 and title.lower() in ("bibliography", "index"):
            appendices.append((title, page))

    if appendices and chapters:
        first_appendix_page = appendices[0][1]
        for i in range(len(chapters) - 1, -1, -1):
            if chapters[i].id != "00_front_matter":
                chapters[i].end = first_appendix_page - 1
                break

    for i, (title, start) in enumerate(appendices):
        end = appendices[i + 1][1] - 1 if i + 1 < len(appendices) else total_pages
        if title.startswith("Appendix"):
            m = re.match(r"Appendix\s+(\d+)", title)
            num = m.group(1) if m else "?"
            header_re = rf"^#+\s+Appendix\s+{num}\b"
        else:
            header_re = rf"^#+\s+{re.escape(title)}\s*$"
        chapters.append(Chapter(
            id=f"app_{slugify(title)}",
            title=title, start=start, end=end, header_re=header_re,
        ))

    doc.close()
    return chapters


def split_md_by_headers(md_text: str, chapters: list[Chapter]) -> dict[str, str]:
    """Quebra MD entre as posições dos headings dos capítulos.

    Retorna dict {chapter_id: chunk}. Capítulos cujo heading não foi encontrado
    não aparecem no dict (caller decide pular ou alertar).
    """
    lines = md_text.splitlines(keepends=True)
    positions: list[tuple[int, int]] = []  # (chapter_idx, line_idx)

    # Capítulo sem header_re (front matter, ou qualquer "começa no início do MD")
    # ancora na linha 0.
    if chapters and chapters[0].header_re is None:
        positions.append((0, 0))

    for idx, ch in enumerate(chapters):
        if ch.header_re is None:
            continue
        pat = re.compile(ch.header_re)
        for line_idx, line in enumerate(lines):
            if pat.match(line):
                positions.append((idx, line_idx))
                break

    positions.sort(key=lambda x: x[1])

    chunks: dict[str, str] = {}
    for i, (ch_idx, start_line) in enumerate(positions):
        end_line = positions[i + 1][1] if i + 1 < len(positions) else len(lines)
        chunks[chapters[ch_idx].id] = "".join(lines[start_line:end_line])
    return chunks


def organize_images(
    marker_dir: Path, target_dir: Path, chapters: list[Chapter]
) -> dict[str, int]:
    """Copia imagens para `target/<chapter>/images/` baseado em `_page_N_` no nome.

    Marker nomeia: `_page_0_Picture_3.jpeg` (0-indexed). Mapeamos via página.
    Retorna {chapter_id: image_count}.
    """
    img_pattern = re.compile(r"_page_(\d+)_(?:Picture|Figure|Table)_(\d+)\.\w+", re.IGNORECASE)
    all_images = (
        list(marker_dir.glob("*.png"))
        + list(marker_dir.glob("*.jpeg"))
        + list(marker_dir.glob("*.jpg"))
    )
    by_chapter: dict[str, int] = {ch.id: 0 for ch in chapters}
    for img in all_images:
        m = img_pattern.search(img.name)
        if not m:
            continue
        page_num = int(m.group(1)) + 1  # marker é 0-indexed
        for ch in chapters:
            if ch.start <= page_num <= ch.end:
                img_dir = target_dir / ch.id / "images"
                img_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy(img, img_dir / img.name)
                by_chapter[ch.id] += 1
                break
    return by_chapter


def fix_image_paths_in_md(chunk: str, chapter_id: str) -> str:
    """`![alt](some/path/img.png)` → `![alt](images/img.png)`."""
    return re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)",
        lambda m: f"![{m.group(1)}](images/{Path(m.group(2)).name})",
        chunk,
    )


def derive_book_header(pdf_path: Path) -> tuple[str, str]:
    """Título/subtítulo do index a partir do metadata do PDF.

    Fallback: nome do arquivo. Subtítulo vazio quando o PDF não declara autor.
    """
    title, author = "", ""
    try:
        import fitz
        with fitz.open(pdf_path) as doc:
            meta = doc.metadata or {}
            title = (meta.get("title") or "").strip()
            author = (meta.get("author") or "").strip()
    except Exception:
        pass
    if not title:
        title = pdf_path.stem.replace("_", " ").strip() or pdf_path.stem
    subtitle = f"**{author}**" if author else ""
    return title, subtitle


def write_index(
    target_dir: Path,
    chapters: list[Chapter],
    image_counts: dict[str, int],
    *,
    book_title: str,
    book_subtitle: str = "",
) -> Path:
    """Gera `target/index.md` com sumário navegável. Retorna path."""
    lines = [f"# {book_title}", ""]
    if book_subtitle:
        lines += [book_subtitle, ""]
    lines += [
        "*Extração organizada por capítulo via TOC do PDF. Estrutura:*",
        "*MD por capítulo + imagens locais + index navegável.*",
        "",
        "---",
        "",
        "## Sumário",
        "",
    ]
    for ch in chapters:
        link = f"[{ch.title}]({ch.id}/{ch.id}.md)"
        imgs = image_counts.get(ch.id, 0)
        pages = ch.end - ch.start + 1
        lines.append(f"- {link}")
        lines.append(f"  - p. {ch.start}–{ch.end} ({pages} páginas, {imgs} imagens)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        f"**Total:** {len(chapters)} seções, {sum(image_counts.values())} imagens, "
        f"{chapters[-1].end if chapters else 0} páginas."
    )
    out = target_dir / "index.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def restructure(
    pdf_path: Path,
    marker_dir: Path,
    target_dir: Path,
    *,
    book_title: str | None = None,
    book_subtitle: str | None = None,
    on_chapter=None,
    force: bool = False,
) -> dict[str, int]:
    """Pipeline completo: detecta TOC, copia imagens, escreve MDs por capítulo + index.

    Args:
        pdf_path: PDF original (para TOC).
        marker_dir: pasta com o MD bruto do marker + imagens.
        target_dir: destino — será LIMPO (rmtree) antes de recriar.
        book_title, book_subtitle: cabeçalho do index.md. Default (None): derivados
            do metadata do PDF (título/autor), fallback nome do arquivo.
        on_chapter: callback opcional `(chapter_id, chars, images)`.
        force: permite apagar um target_dir pré-existente NÃO-vazio. Sem force,
            destino não-vazio levanta ValueError (proteção contra wipe de dados
            do usuário; re-runs do pipeline passam force=True explicitamente).

    Returns:
        dict {chapter_id: image_count} — útil para stats agregados.

    Raises:
        ValueError se marker_dir está dentro de target_dir (rmtree apagaria
        próprio input — bug pego 2026-05-12), ou se target_dir não-vazio sem force.
        RuntimeError se marker_dir não tem .md.
    """
    # Defensiva: marker_dir ⊂ target_dir é fatal (rmtree apagaria input).
    try:
        marker_abs = marker_dir.resolve()
        target_abs = target_dir.resolve()
        if marker_abs == target_abs or target_abs in marker_abs.parents:
            raise ValueError(
                f"marker_dir ({marker_dir}) está dentro de target_dir ({target_dir}). "
                f"O rmtree(target_dir) deletaria o próprio input."
            )
    except (OSError, ValueError) as e:
        if isinstance(e, ValueError):
            raise
        # OSError em resolve() é tolerável

    md_candidates = list(marker_dir.glob("*.md"))
    if not md_candidates:
        raise RuntimeError(f"Nenhum .md em {marker_dir}")
    md_path = md_candidates[0]

    chapters = get_chapter_boundaries(pdf_path)
    md_text = md_path.read_text(encoding="utf-8")
    chunks = split_md_by_headers(md_text, chapters)

    if target_dir.exists():
        if any(target_dir.iterdir()) and not force:
            raise ValueError(
                f"target_dir ({target_dir}) já existe e não está vazio — restructure "
                f"APAGA o destino antes de recriar. Use force=True (CLI: --force) "
                f"para confirmar."
            )
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True)

    image_counts = organize_images(marker_dir, target_dir, chapters)

    for ch in chapters:
        if ch.id not in chunks:
            if on_chapter:
                on_chapter(ch.id, 0, 0, error="header não encontrado no MD")
            continue
        chunk = fix_image_paths_in_md(chunks[ch.id], ch.id)
        ch_dir = target_dir / ch.id
        ch_dir.mkdir(parents=True, exist_ok=True)
        header = (
            f"# {ch.title}\n\n"
            f"*Páginas {ch.start}–{ch.end} do PDF original. "
            f"{image_counts.get(ch.id, 0)} imagens.*\n\n---\n\n"
        )
        # Remove heading duplicado do chunk (o marker já gerou um, mas usamos o nosso)
        chunk_lines = chunk.splitlines()
        if chunk_lines and re.match(r"^#\s+", chunk_lines[0]):
            chunk = "\n".join(chunk_lines[1:])
        (ch_dir / f"{ch.id}.md").write_text(header + chunk, encoding="utf-8")
        if on_chapter:
            on_chapter(ch.id, len(chunk), image_counts.get(ch.id, 0), error=None)

    if book_title is None or book_subtitle is None:
        meta_title, meta_subtitle = derive_book_header(pdf_path)
        book_title = meta_title if book_title is None else book_title
        book_subtitle = meta_subtitle if book_subtitle is None else book_subtitle
    write_index(target_dir, chapters, image_counts,
                book_title=book_title, book_subtitle=book_subtitle)
    return image_counts


def _cli() -> int:
    """CLI standalone (compat com `python src/restructure.py PDF MARKER TARGET`)."""
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if len(sys.argv) < 4:
        print(__doc__)
        return 1

    pdf_path = Path(sys.argv[1])
    marker_dir = Path(sys.argv[2])
    target_dir = Path(sys.argv[3])

    if not pdf_path.is_file():
        print(f"[ERRO] PDF não encontrado: {pdf_path}")
        return 1
    if not marker_dir.is_dir():
        print(f"[ERRO] Pasta marker não encontrada: {marker_dir}")
        return 1

    print(f"[INFO] PDF original: {pdf_path}")
    print(f"[INFO] Marker dir: {marker_dir}")
    print(f"[INFO] Target: {target_dir}")

    def _report(cid: str, chars: int, imgs: int, error: str | None) -> None:
        if error:
            print(f"  [pulo] {cid}: {error}")
        else:
            print(f"  [{cid}] {chars:,} chars, {imgs} imagens")

    try:
        image_counts = restructure(pdf_path, marker_dir, target_dir, on_chapter=_report)
    except (ValueError, RuntimeError) as e:
        print(f"[ERRO] {e}")
        print(f"       O rmtree(target_dir) deletaria o próprio input. Aborte.")
        return 1

    print(f"\n[OK] Estrutura criada em {target_dir}")
    print(f"[OK] index.md gerado com {len(image_counts)} entradas")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
