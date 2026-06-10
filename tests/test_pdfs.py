"""Tests para pdf2md.pdfs — find_chapter_mds + md_to_pdf overwrite guard (T076)."""
from pathlib import Path

import pytest

from pdf2md.pdfs import find_chapter_mds, md_to_pdf


def test_find_chapter_mds_basic(tmp_path: Path):
    """Detecta padrão <base>/<chapter>/<chapter>.md (restructure output)."""
    (tmp_path / "01_intro").mkdir()
    (tmp_path / "01_intro" / "01_intro.md").write_text("# Intro", encoding="utf-8")
    (tmp_path / "02_body").mkdir()
    (tmp_path / "02_body" / "02_body.md").write_text("# Body", encoding="utf-8")
    # Não-MD/diff name não deve entrar
    (tmp_path / "03_skip").mkdir()
    (tmp_path / "03_skip" / "different_name.md").write_text("# X", encoding="utf-8")
    (tmp_path / "index.md").write_text("# Index", encoding="utf-8")  # file at root

    found = find_chapter_mds(tmp_path)
    names = [p.parent.name for p in found]
    assert names == ["01_intro", "02_body"]


def test_find_chapter_mds_empty_returns_empty(tmp_path: Path):
    assert find_chapter_mds(tmp_path) == []


def test_find_chapter_mds_sorted(tmp_path: Path):
    """Ordem alfabética (importante para apêndices vs capítulos)."""
    for name in ["12_last", "00_first", "07_middle"]:
        d = tmp_path / name
        d.mkdir()
        (d / f"{name}.md").write_text("x", encoding="utf-8")
    found = find_chapter_mds(tmp_path)
    assert [p.parent.name for p in found] == ["00_first", "07_middle", "12_last"]


def test_md_to_pdf_raises_when_destination_exists_default(tmp_path: Path):
    """T076: sem overwrite=True, raise FileExistsError se destino existe.

    Pre-condição checada antes de invocar pandoc/Chrome — não precisa de
    tools externos para o teste.
    """
    md = tmp_path / "doc.md"
    md.write_text("# Title", encoding="utf-8")
    pdf = md.with_suffix(".pdf")
    sentinel = b"original PDF content - must NOT be overwritten"
    pdf.write_bytes(sentinel)

    with pytest.raises(FileExistsError):
        md_to_pdf(md)

    # PDF original preservado bit-a-bit
    assert pdf.read_bytes() == sentinel


def test_md_to_pdf_raises_on_explicit_out_pdf_when_exists(tmp_path: Path):
    """T076: protecao tambem para out_pdf explicito (proprio caminho conflita)."""
    md = tmp_path / "doc.md"
    md.write_text("# Title", encoding="utf-8")
    custom = tmp_path / "custom.pdf"
    custom.write_bytes(b"existing")

    with pytest.raises(FileExistsError):
        md_to_pdf(md, out_pdf=custom)

    assert custom.read_bytes() == b"existing"


# --- mermaid adapter (T190/e22) ----------------------------------------------

def _tools_available() -> bool:
    from pdf2md.discovery import available, find_chrome, find_pandoc
    return available(find_pandoc()) and available(find_chrome())


def test_mermaid_vendor_files_ship():
    """O wheel precisa carregar o JS pinado + Lua filter (package-data)."""
    from pdf2md.pdfs import MERMAID_JS, MERMAID_LUA
    assert MERMAID_JS.exists() and MERMAID_JS.stat().st_size > 1_000_000
    assert MERMAID_LUA.exists()


@pytest.mark.skipif(not _tools_available(), reason="pandoc/chrome ausentes")
def test_md_to_pdf_mermaid_renders_diagram(tmp_path: Path):
    """Detector do e22 como regressão: com mermaid=True o fonte NÃO vaza como
    texto e a página ganha desenhos vetoriais; sem a flag, vaza (code block)."""
    import fitz

    md = tmp_path / "d.md"
    md.write_text(
        "# Doc\n\ntexto antes\n\n```mermaid\nflowchart LR\n"
        "  A[caixa A] -->|e0| B[caixa B]\n  B --> C[caixa C]\n```\n\ndepois\n",
        encoding="utf-8",
    )

    pdf_on = md_to_pdf(md, tmp_path / "on.pdf", mermaid=True)
    doc = fitz.open(pdf_on)
    text = "".join(p.get_text() for p in doc)
    n_draw = sum(len(p.get_drawings()) for p in doc)
    doc.close()
    assert "-->" not in text and "flowchart" not in text   # fonte não vazou
    assert n_draw >= 5                                      # diagrama desenhado

    pdf_off = md_to_pdf(md, tmp_path / "off.pdf", mermaid=False)
    doc = fitz.open(pdf_off)
    text_off = "".join(p.get_text() for p in doc)
    doc.close()
    assert "flowchart" in text_off                          # sem flag: literal
