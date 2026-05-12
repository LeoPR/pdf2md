"""Unit tests para pdf2md.normalize.normalize_md."""
from pdf2md.normalize import normalize_md


def test_strips_page_markers():
    assert normalize_md("foo {17} bar") == "foo bar"


def test_strips_html_page_comments():
    assert normalize_md("foo <!-- page 5 --> bar") == "foo bar"
    assert normalize_md("foo <!-- Page 99 --> bar") == "foo bar"


def test_image_paths_reduced_to_basename():
    out = normalize_md("![alt](deep/path/img.png)")
    assert out == "![alt](img.png)"


def test_collapses_whitespace():
    assert normalize_md("a   b\t\tc") == "a b c"
    assert normalize_md("a\n\n\n\nb") == "a\n\nb"


def test_strip_md_escapes_opt_in():
    """Q11.b: escapes markdown sumir só quando flag explícita."""
    text = r"foo \_underscore\_ and \*star\* and \( paren \)"
    default = normalize_md(text)
    assert "\\_" in default
    assert "\\*" in default
    stripped = normalize_md(text, strip_md_escapes=True)
    assert "\\_" not in stripped
    assert "\\*" not in stripped
    assert "_underscore_" in stripped
    assert "*star*" in stripped


def test_preserves_content():
    text = "# Title\n\nFoo $\\alpha = \\beta$ bar."
    out = normalize_md(text)
    # Math LaTeX deve ser preservado (não é escape markdown)
    assert "\\alpha" in out
    assert "\\beta" in out


def test_round_trip_idempotent():
    """Normalizar 2x dá o mesmo resultado."""
    text = "  foo   {17} bar  <!-- page 5 -->\n\n\n\nbaz"
    once = normalize_md(text)
    twice = normalize_md(once)
    assert once == twice
