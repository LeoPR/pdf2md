"""Tests para pdf2md.pdfs — apenas find_chapter_mds (sem invocar pandoc/Chrome)."""
from pathlib import Path

from pdf2md.pdfs import find_chapter_mds


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
