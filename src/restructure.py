"""
Restructure marker output into per-chapter folders.

Uses:
- Marker MD output (single file)
- Marker meta.json (TOC with page_id per heading)
- Marker image files (named _page_N_*.jpeg)
- PyMuPDF TOC of original PDF (chapter boundaries with start/end pages)

Splits the MD by detecting top-level chapter headings, organizes images
into per-chapter folders by page number, and generates index.md.

Usage:
  python restructure.py <pdf_path> <marker_output_dir> <target_dir>

Example:
  python restructure.py \\
    pesquisa_geral/_sources/livros/Nielsen_Chuang_QCQI.pdf \\
    /tmp/marker_full/Nielsen_Chuang_QCQI \\
    pesquisa_geral/livros/Quantum_Computation_and_Quantum_Information
"""

import sys
import re
import shutil
import json
from pathlib import Path
import fitz

# PDF_PATH agora vem da linha de comando (argv[1])


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s[:60]


def get_chapter_boundaries(pdf_path: Path):
    """Return list of (chapter_id, title, start_page, end_page, header_pattern) using PDF TOC.

    Pages are 1-indexed.
    header_pattern: regex (string) that matches the chapter heading in the marker MD.
    """
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    total_pages = len(doc)
    chapters = []

    # Find first numbered chapter for front matter end
    fm_end = None
    for level, title, page in toc:
        m = re.match(r"^(\d+)\s+(.+)$", title)
        if m and level == 2:
            fm_end = page - 1
            break

    if fm_end:
        chapters.append({
            "id": "00_front_matter",
            "title": "Front Matter",
            "start": 1,
            "end": fm_end,
            "header_re": None,  # front matter starts at file beginning
        })

    # Numbered chapters (1-12)
    numbered = []
    for level, title, page in toc:
        m = re.match(r"^(\d+)\s+(.+)$", title)
        if m and level == 2:
            num = int(m.group(1))
            ch_title = m.group(2)
            numbered.append((num, ch_title, page))

    for i, (num, title, start) in enumerate(numbered):
        if i + 1 < len(numbered):
            end = numbered[i + 1][2] - 1
        else:
            end = total_pages
        chapters.append({
            "id": f"{num:02d}_{slugify(title)}",
            "title": f"{num}. {title}",
            "start": start,
            "end": end,
            # Aceita qualquer nivel de heading: # 6 ..., ## 6 ..., ### 6 ...
            "header_re": rf"^#+\s+{num}\s+\S",
        })

    # Appendices (level 1)
    appendices = []
    for level, title, page in toc:
        if level == 1 and title.startswith("Appendix"):
            appendices.append((title, page))
    for level, title, page in toc:
        if level == 1 and title.lower() in ("bibliography", "index"):
            appendices.append((title, page))

    if appendices and chapters:
        first_appendix_page = appendices[0][1]
        for i in range(len(chapters) - 1, -1, -1):
            if chapters[i]["id"] != "00_front_matter":
                chapters[i]["end"] = first_appendix_page - 1
                break

    for i, (title, start) in enumerate(appendices):
        if i + 1 < len(appendices):
            end = appendices[i + 1][1] - 1
        else:
            end = total_pages
        # Header pattern: aceita qualquer nivel (# / ## / ###)
        if title.startswith("Appendix"):
            m = re.match(r"Appendix\s+(\d+)", title)
            num = m.group(1) if m else "?"
            header_re = rf"^#+\s+Appendix\s+{num}\b"
        else:
            header_re = rf"^#+\s+{re.escape(title)}\s*$"
        chapters.append({
            "id": f"app_{slugify(title)}",
            "title": title,
            "start": start,
            "end": end,
            "header_re": header_re,
        })

    doc.close()
    return chapters


def split_md_by_headers(md_text: str, chapters):
    """Find chapter heading positions in MD using regex, split between them.

    Returns dict {chapter_id: text_chunk}.
    """
    lines = md_text.splitlines(keepends=True)

    # Find header positions for each chapter
    # Front matter starts at offset 0; numbered chapters and appendices have header_re.
    positions = []  # list of (chapter_idx, line_idx)

    # Front matter starts at the top
    if chapters[0]["id"] == "00_front_matter":
        positions.append((0, 0))

    # For each chapter with header_re, find the matching line
    for idx, ch in enumerate(chapters):
        if ch["header_re"] is None:
            continue
        pat = re.compile(ch["header_re"])
        for line_idx, line in enumerate(lines):
            if pat.match(line):
                positions.append((idx, line_idx))
                break

    # Sort positions by line index
    positions.sort(key=lambda x: x[1])

    # Build chunks
    chunks = {}
    for i, (ch_idx, start_line) in enumerate(positions):
        end_line = positions[i + 1][1] if i + 1 < len(positions) else len(lines)
        chunk = "".join(lines[start_line:end_line])
        chunks[chapters[ch_idx]["id"]] = chunk

    return chunks


def organize_images(marker_dir: Path, target_dir: Path, chapters):
    """Copy images to per-chapter image folders based on _page_N_ in filename."""
    img_pattern = re.compile(r"_page_(\d+)_(?:Picture|Figure|Table)_(\d+)\.\w+", re.IGNORECASE)
    all_images = list(marker_dir.glob("*.png")) + list(marker_dir.glob("*.jpeg")) + list(marker_dir.glob("*.jpg"))

    by_chapter = {ch["id"]: 0 for ch in chapters}

    for img in all_images:
        m = img_pattern.search(img.name)
        if not m:
            continue
        page_num = int(m.group(1)) + 1  # marker uses 0-indexed pages

        for ch in chapters:
            if ch["start"] <= page_num <= ch["end"]:
                img_dir = target_dir / ch["id"] / "images"
                img_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy(img, img_dir / img.name)
                by_chapter[ch["id"]] += 1
                break

    return by_chapter


def fix_image_paths_in_md(chunk: str, chapter_id: str) -> str:
    """Rewrite image paths in MD to point to local images/ folder."""
    return re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)",
        lambda m: f"![{m.group(1)}](images/{Path(m.group(2)).name})",
        chunk
    )


def write_index(target_dir: Path, chapters, image_counts):
    lines = [
        "# Quantum Computation and Quantum Information",
        "",
        "**Michael A. Nielsen & Isaac L. Chuang — 10th Anniversary Edition**",
        "",
        "*Re-extração via marker-pdf (GPU), organizada por capítulo. Estrutura simétrica:*",
        "*MD por capítulo + imagens locais + index navegável.*",
        "",
        "---",
        "",
        "## Sumário",
        "",
    ]
    for ch in chapters:
        link = f"[{ch['title']}]({ch['id']}/{ch['id']}.md)"
        imgs = image_counts.get(ch["id"], 0)
        pages = ch["end"] - ch["start"] + 1
        lines.append(f"- {link}")
        lines.append(f"  - p. {ch['start']}–{ch['end']} ({pages} páginas, {imgs} imagens)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"**Total:** {len(chapters)} seções, {sum(image_counts.values())} imagens, "
                 f"{chapters[-1]['end']} páginas.")
    (target_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    marker_dir = Path(sys.argv[2])
    target_dir = Path(sys.argv[3])

    if not pdf_path.is_file():
        print(f"[ERRO] PDF não encontrado: {pdf_path}")
        sys.exit(1)
    if not marker_dir.is_dir():
        print(f"[ERRO] Pasta marker não encontrada: {marker_dir}")
        sys.exit(1)

    md_candidates = list(marker_dir.glob("*.md"))
    if not md_candidates:
        print(f"[ERRO] Nenhum .md em {marker_dir}")
        sys.exit(1)
    md_path = md_candidates[0]

    print(f"[INFO] PDF original: {pdf_path}")
    print(f"[INFO] Marker MD: {md_path}")
    print(f"[INFO] Target: {target_dir}")

    chapters = get_chapter_boundaries(pdf_path)
    print(f"[INFO] {len(chapters)} seções no TOC do PDF")

    md_text = md_path.read_text(encoding="utf-8")
    chunks = split_md_by_headers(md_text, chapters)
    print(f"[INFO] {len(chunks)} chunks identificados pelos headers")

    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True)

    image_counts = organize_images(marker_dir, target_dir, chapters)

    for ch in chapters:
        cid = ch["id"]
        if cid not in chunks:
            print(f"  [pulo] {cid}: header não encontrado no MD")
            continue
        chunk = fix_image_paths_in_md(chunks[cid], cid)
        ch_dir = target_dir / cid
        ch_dir.mkdir(parents=True, exist_ok=True)
        header = (f"# {ch['title']}\n\n"
                  f"*Páginas {ch['start']}–{ch['end']} do PDF original. "
                  f"{image_counts.get(cid, 0)} imagens.*\n\n---\n\n")
        # Strip duplicate top-level header from chunk if present
        chunk_lines = chunk.splitlines()
        if chunk_lines and re.match(r"^#\s+", chunk_lines[0]):
            chunk = "\n".join(chunk_lines[1:])
        (ch_dir / f"{cid}.md").write_text(header + chunk, encoding="utf-8")
        print(f"  [{cid}] {len(chunk):,} chars, {image_counts.get(cid, 0)} imagens")

    write_index(target_dir, chapters, image_counts)
    print(f"\n[OK] Estrutura criada em {target_dir}")
    print(f"[OK] index.md gerado com {len(chapters)} entradas")


if __name__ == "__main__":
    main()
