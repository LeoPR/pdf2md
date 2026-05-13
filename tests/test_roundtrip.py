"""Tests para pdf2md.roundtrip — só funções puras (extract_tokens, compare).

Não invoca marker/pandoc/Chrome (precisaria de fixture PDF + setup pesado).
A integração end-to-end é testada via smoke manual em labs.
"""
from pathlib import Path

from pdf2md.roundtrip import (
    RoundtripResult,
    compare,
    extract_tokens,
)


def test_extract_tokens_strips_page_markers():
    """extract_tokens passa por normalize_md, que tira {17} etc."""
    tokens = extract_tokens("foo {17} bar")
    assert tokens == ["foo", "bar"]


def test_extract_tokens_basic():
    tokens = extract_tokens("Hello world.\n\nFoo bar.")
    assert tokens == ["Hello", "world.", "Foo", "bar."]


def test_compare_identical_returns_100pct(tmp_path: Path):
    md1 = tmp_path / "a.md"
    md2 = tmp_path / "b.md"
    md1.write_text("# Title\n\nHello world.", encoding="utf-8")
    md2.write_text("# Title\n\nHello world.", encoding="utf-8")
    r = compare(md1, md2)
    assert isinstance(r, RoundtripResult)
    assert r.similarity == 1.0
    assert r.tokens_md1 == r.tokens_md2
    assert r.divergences == []


def test_compare_partial_match(tmp_path: Path):
    md1 = tmp_path / "a.md"
    md2 = tmp_path / "b.md"
    md1.write_text("# X\n\nfoo bar baz quux", encoding="utf-8")
    md2.write_text("# X\n\nfoo XYZ baz quux", encoding="utf-8")  # 1 word diff
    r = compare(md1, md2)
    assert 0.5 < r.similarity < 1.0
    assert len(r.divergences) >= 1
    tag, a, b = r.divergences[0]
    assert tag != "equal"
    assert "bar" in a
    assert "XYZ" in b


def test_compare_caps_divergences_at_5(tmp_path: Path):
    """max_divergences default = 5."""
    md1 = tmp_path / "a.md"
    md2 = tmp_path / "b.md"
    md1.write_text(" ".join(["a"] * 20), encoding="utf-8")
    md2.write_text(" ".join(["b"] * 20), encoding="utf-8")
    r = compare(md1, md2)
    # 20 tokens diferentes = potencialmente 1 divergência grande
    # Mas o limite é o max_divergences param
    assert len(r.divergences) <= 5


def test_render_text_contains_tokens_and_similarity():
    r = RoundtripResult(
        tokens_md1=100, tokens_md2=98,
        similarity=0.95,
        divergences=[("replace", "foo bar", "baz qux")],
    )
    out = r.render_text()
    assert "100" in out
    assert "98" in out
    assert "95.00%" in out
    assert "foo bar" in out
