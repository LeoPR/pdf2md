"""Unit tests para pdf2md.provenance — idempotência + posicionamento do marcador."""
from pdf2md.provenance import Provenance, apply_to_text


def _make_prov(version="v0.test", commit="abc1234"):
    return Provenance(
        version=version, date="2026-01-01", commit=commit,
        source="x.pdf", source_sha256="deadbeefcafe",
        extractor="marker-pdf 1.10.2",
    )


def test_inserts_after_first_heading():
    text = "# Title\n\nBody.\n"
    prov = _make_prov()
    out = apply_to_text(text, prov)
    lines = out.splitlines()
    assert lines[0] == "# Title"
    assert "<!-- pdf2md-provenance" in lines[2]
    assert "Convertido por" in lines[3]
    assert "Body." in out


def test_prepends_if_no_heading():
    """Bug pego no smoke T108: MD começa com imagem (sem heading)."""
    text = "![](_page_0.jpeg)\n\nFigure 4.15. caption.\n"
    prov = _make_prov()
    out = apply_to_text(text, prov)
    assert out.startswith("<!-- pdf2md-provenance")
    assert "![](_page_0.jpeg)" in out


def test_idempotent_same_prov():
    text = "# Title\n\nBody.\n"
    prov = _make_prov()
    once = apply_to_text(text, prov)
    twice = apply_to_text(once, prov)
    assert once == twice, "aplicar 2x mesmo prov deve ser no-op"


def test_replaces_old_marker():
    """Re-aplicar com novo prov substitui o antigo, não duplica."""
    text = "# Title\n\nBody.\n"
    out1 = apply_to_text(text, _make_prov(version="v0.1", commit="aaaaaaa"))
    out2 = apply_to_text(out1, _make_prov(version="v0.2", commit="bbbbbbb"))
    # Apenas 1 marcador no resultado final
    assert out2.count("<!-- pdf2md-provenance") == 1
    assert "v0.2" in out2
    assert "v0.1" not in out2
    assert "bbbbbbb" in out2
    assert "aaaaaaa" not in out2


def test_sha256_truncated_to_8_chars():
    prov = _make_prov()
    out = apply_to_text("# X\n\nbody\n", prov)
    # sha256_short truncado: "deadbeef…"
    assert "deadbeef" in out
    assert "deadbeefcafe" not in out  # apenas 8 chars + ellipsis


def test_optional_fields_omitted_cleanly():
    prov = Provenance(version="v0", date="2026-01-01")  # tudo opcional vazio
    out = apply_to_text("# X\n\nbody\n", prov)
    assert "<!-- pdf2md-provenance" in out
    assert "fonte:" not in out  # sem source, não menciona
    assert "commit `" not in out  # sem commit, não menciona
