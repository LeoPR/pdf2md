"""Tests para pdf2md.multi_roundtrip — funções puras só.

Iteração end-to-end requer marker/pandoc/Chrome → não testado aqui.
"""
from pathlib import Path

from pdf2md.multi_roundtrip import (
    IterationResult,
    MultiRoundtripReport,
    render_report,
    similarity,
)


def test_similarity_identical(tmp_path: Path):
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("hello world", encoding="utf-8")
    b.write_text("hello world", encoding="utf-8")
    sim, ta, tb = similarity(a, b)
    assert sim == 1.0
    assert ta == tb == 2


def test_similarity_partial(tmp_path: Path):
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("foo bar baz", encoding="utf-8")
    b.write_text("foo XXX baz", encoding="utf-8")
    sim, _, _ = similarity(a, b)
    assert 0.5 < sim < 1.0


def test_render_report_empty():
    r = MultiRoundtripReport(md0="x.md", generated_at="2026-01-01T00:00:00")
    assert "sem iterações" in render_report(r)


def test_render_report_estavel():
    """Pipeline estável: drift < 1% entre 1ª e última iteração."""
    r = MultiRoundtripReport(
        md0="x.md",
        generated_at="2026-01-01",
        iterations=[
            IterationResult(i=1, tokens=1000, sim_to_md0=0.975, seconds=30),
            IterationResult(i=2, tokens=1000, sim_to_md0=0.974, sim_to_prev=0.99, seconds=30),
            IterationResult(i=3, tokens=1000, sim_to_md0=0.973, sim_to_prev=0.99, seconds=30),
        ],
        total_seconds=90.0,
    )
    out = render_report(r)
    assert "Pipeline estável" in out
    assert "97.50%" in out  # iter 1
    assert "97.30%" in out  # iter 3


def test_render_report_drift():
    """Pipeline com drift contínuo: perdeu > 1% e ainda variando."""
    r = MultiRoundtripReport(
        md0="x.md",
        generated_at="2026-01-01",
        iterations=[
            IterationResult(i=1, tokens=1000, sim_to_md0=0.95, seconds=30),
            IterationResult(i=2, tokens=1000, sim_to_md0=0.85, sim_to_prev=0.90, seconds=30),
            IterationResult(i=3, tokens=1000, sim_to_md0=0.75, sim_to_prev=0.88, seconds=30),
        ],
        total_seconds=90.0,
    )
    out = render_report(r)
    assert "Drift contínuo" in out


def test_render_report_with_error():
    r = MultiRoundtripReport(
        md0="x.md",
        generated_at="2026-01-01",
        iterations=[
            IterationResult(i=1, tokens=1000, sim_to_md0=0.95, seconds=30),
            IterationResult(i=2, error="RuntimeError: marker crashed", seconds=10),
        ],
        total_seconds=40.0,
    )
    out = render_report(r)
    assert "falha:" in out
    assert "RuntimeError" in out


def test_to_dict_roundtrip():
    r = MultiRoundtripReport(
        md0="x.md", generated_at="2026-01-01",
        iterations=[IterationResult(i=1, tokens=500, sim_to_md0=0.97, seconds=42)],
        total_seconds=42.0,
    )
    d = r.to_dict()
    assert d["md0"] == "x.md"
    assert d["iterations"][0]["sim_to_md0"] == 0.97
    assert d["total_seconds"] == 42.0
