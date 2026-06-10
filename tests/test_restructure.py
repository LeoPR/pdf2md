"""Tests para pdf2md.restructure — funções puras (sem PDF real).

get_chapter_boundaries + organize_images requerem fixtures pesados,
ficam para integration tests futuros.
"""
from pathlib import Path

import pytest

from pdf2md.restructure import (
    Chapter,
    derive_book_header,
    fix_image_paths_in_md,
    restructure,
    slugify,
    split_md_by_headers,
    write_index,
)


def _mini_book_pdf(path: Path, title: str = "", author: str = "") -> None:
    """PDF mínimo com TOC de 1 capítulo (+ metadata opcional) via fitz."""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "1 Intro")
    doc.new_page().insert_text((72, 72), "conteudo")
    doc.set_toc([[1, "1 Intro", 1]])
    if title or author:
        doc.set_metadata({"title": title, "author": author})
    doc.save(str(path))
    doc.close()


def test_slugify_basic():
    assert slugify("Quantum Circuits") == "quantum_circuits"
    assert slugify("Hello, World!") == "hello_world"
    assert slugify("4. Quantum Circuits") == "4_quantum_circuits"


def test_slugify_trims_underscores():
    assert slugify("__foo__") == "foo"
    assert slugify("---bar---") == "bar"


def test_slugify_truncates_at_60():
    long_input = "a" * 80
    out = slugify(long_input)
    assert len(out) <= 60


def test_fix_image_paths_to_local():
    chunk = "![alt](/deep/path/img.png)"
    out = fix_image_paths_in_md(chunk, "ch_x")
    assert out == "![alt](images/img.png)"


def test_fix_image_paths_multiple():
    chunk = "![a](one.png) text ![b](deep/two.jpeg)"
    out = fix_image_paths_in_md(chunk, "ch_x")
    assert "images/one.png" in out
    assert "images/two.jpeg" in out


def test_split_md_by_headers_basic():
    chapters = [
        Chapter(id="00_fm", title="Front", start=1, end=10, header_re=None),
        Chapter(id="01_intro", title="1. Intro", start=11, end=20, header_re=r"^#+\s+1\s+\S"),
        Chapter(id="02_body", title="2. Body", start=21, end=30, header_re=r"^#+\s+2\s+\S"),
    ]
    md = (
        "Prelude text.\n\n"
        "More front matter.\n\n"
        "# 1 Intro\n\n"
        "Intro content.\n\n"
        "# 2 Body\n\n"
        "Body content.\n"
    )
    chunks = split_md_by_headers(md, chapters)
    assert "00_fm" in chunks
    assert "01_intro" in chunks
    assert "02_body" in chunks
    assert "Prelude" in chunks["00_fm"]
    assert "Intro content" in chunks["01_intro"]
    assert "Body content" in chunks["02_body"]
    assert "Intro content" not in chunks["00_fm"]


def test_split_md_skips_chapter_without_match():
    """Chapter cujo header_re não casa não aparece no dict."""
    chapters = [
        Chapter(id="x", title="X", start=1, end=10, header_re=r"^#\s+NEVER_FOUND"),
    ]
    md = "Just text without any heading match.\n"
    chunks = split_md_by_headers(md, chapters)
    assert "x" not in chunks


def test_write_index_basic(tmp_path: Path):
    chapters = [
        Chapter(id="01_intro", title="1. Intro", start=1, end=10, header_re=None),
        Chapter(id="02_body", title="2. Body", start=11, end=30, header_re=None),
    ]
    counts = {"01_intro": 5, "02_body": 3}
    out = write_index(tmp_path, chapters, counts, book_title="Test Book", book_subtitle="*test*")
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "# Test Book" in text
    assert "[1. Intro](01_intro/01_intro.md)" in text
    assert "2 seções" in text
    assert "8 imagens" in text  # 5+3
    assert "30 páginas" in text  # último end


def test_restructure_rejects_marker_inside_target(tmp_path: Path):
    """Defensiva: marker_dir ⊂ target_dir levanta ValueError (não rmtree)."""
    target = tmp_path / "out"
    target.mkdir()
    marker = target / "_marker"  # filho!
    marker.mkdir()
    (marker / "x.md").write_text("# X", encoding="utf-8")

    # Stub PDF (não precisa ser válido — vai falhar antes na defensiva)
    pdf = tmp_path / "fake.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")

    with pytest.raises(ValueError, match="dentro de target_dir"):
        restructure(pdf, marker, target)


# --- regressão: título default do index (era hardcoded "Nielsen & Chuang") --

def test_derive_book_header_from_metadata(tmp_path: Path):
    pdf = tmp_path / "qualquer.pdf"
    _mini_book_pdf(pdf, title="Meu Livro de Teste", author="Fulano de Tal")
    title, subtitle = derive_book_header(pdf)
    assert title == "Meu Livro de Teste"
    assert "Fulano de Tal" in subtitle


def test_derive_book_header_fallback_stem(tmp_path: Path):
    pdf = tmp_path / "tratado_de_fisica.pdf"
    _mini_book_pdf(pdf)
    title, subtitle = derive_book_header(pdf)
    assert title == "tratado de fisica"
    assert subtitle == ""


def test_restructure_default_title_nao_eh_nielsen_chuang(tmp_path: Path):
    """Sem book_title explícito, o index deriva do PDF — nunca do default fóssil."""
    pdf = tmp_path / "meu_livro.pdf"
    _mini_book_pdf(pdf, title="Meu Livro", author="Autora X")
    marker = tmp_path / "marker"
    marker.mkdir()
    (marker / "x.md").write_text("# 1 Intro\n\nconteudo\n", encoding="utf-8")

    restructure(pdf, marker, tmp_path / "out")
    idx = (tmp_path / "out" / "index.md").read_text(encoding="utf-8")
    assert "# Meu Livro" in idx
    assert "Autora X" in idx
    assert "Nielsen" not in idx and "Chuang" not in idx


def test_restructure_refuses_nonempty_target_sem_force(tmp_path: Path):
    """Destino pré-existente não-vazio só é apagado com force=True."""
    pdf = tmp_path / "meu_livro.pdf"
    _mini_book_pdf(pdf, title="Meu Livro")
    marker = tmp_path / "marker"
    marker.mkdir()
    (marker / "x.md").write_text("# 1 Intro\n\nconteudo\n", encoding="utf-8")
    target = tmp_path / "out"
    target.mkdir()
    (target / "dados_do_usuario.txt").write_text("importante", encoding="utf-8")

    with pytest.raises(ValueError, match="não está vazio"):
        restructure(pdf, marker, target)
    assert (target / "dados_do_usuario.txt").exists()   # nada foi apagado

    restructure(pdf, marker, target, force=True)        # com force, procede
    assert (target / "index.md").exists()
