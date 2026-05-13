"""Tests para pdf2md.aggregate — fmt_bytes, classify_doc, collect/render via fixture."""
import json
from pathlib import Path

from pdf2md.aggregate import (
    aggregate,
    classify_doc,
    collect_docs,
    fmt_bytes,
    render_overview,
)


def test_fmt_bytes_units():
    assert fmt_bytes(0) == "0 B"
    assert fmt_bytes(512) == "512 B"
    assert fmt_bytes(1024) == "1.0 KB"
    assert fmt_bytes(1024 * 1024) == "1.0 MB"
    assert fmt_bytes(2 * 1024**3) == "2.0 GB"


def test_classify_doc_by_path():
    assert classify_doc({}, Path("/x/livros/N&C/_stats.json")) == "livro"
    assert classify_doc({}, Path("/x/papers/arxiv_1706/_stats.json")) == "paper"
    assert classify_doc({}, Path("/x/material_aulas/cap2/_stats.json")) == "material"
    assert classify_doc({}, Path("/x/random/_stats.json")) == "outro"


def test_render_overview_empty(tmp_path: Path):
    out = render_overview(tmp_path, [])
    assert "Nenhum" in out


def _write_stats(folder: Path, **overrides):
    """Cria _stats.json mínimo num diretório (helper de fixture)."""
    folder.mkdir(parents=True, exist_ok=True)
    base = {
        "source": {"pages": 10, "size_bytes": 1000},
        "output": {"totals": {
            "tokens": 5000, "words": 5500, "math_display": 20, "math_inline": 100,
            "headers_total": 8, "tables_rough": 2, "images_count": 3,
            "images_total_bytes": 100_000, "ligature_artifacts": 0,
            "size_bytes": 50_000, "chapter_count": 1,
        }},
        "roundtrip": {"similarity": 0.95, "divergence_categories": {"math": 100, "other": 10}},
        "tools": {"marker": "1.10.2", "torch": "2.11", "cuda_device": "RTX 3060"},
        "extraction_time_seconds": 60.0,
        "generated_at": "2026-01-01T00:00:00",
    }
    base.update(overrides)
    (folder / "_stats.json").write_text(json.dumps(base), encoding="utf-8")


def test_collect_docs_basic(tmp_path: Path):
    _write_stats(tmp_path / "livros" / "n_c")
    _write_stats(tmp_path / "papers" / "arxiv_1706")
    docs = collect_docs(tmp_path)
    assert len(docs) == 2
    kinds = {d["kind"] for d in docs}
    assert kinds == {"livro", "paper"}


def test_collect_docs_extracts_metrics(tmp_path: Path):
    _write_stats(tmp_path / "livros" / "doc")
    docs = collect_docs(tmp_path)
    d = docs[0]
    assert d["tokens"] == 5000
    assert d["pages"] == 10
    assert d["similarity"] == 0.95
    assert d["tools"]["marker"] == "1.10.2"


def test_render_overview_with_docs(tmp_path: Path):
    _write_stats(tmp_path / "livros" / "doc_a")
    _write_stats(tmp_path / "papers" / "doc_b", **{
        "roundtrip": {"similarity": 0.60, "divergence_categories": {"math": 200}}
    })
    docs = collect_docs(tmp_path)
    md = render_overview(tmp_path, docs)
    # Resumo agregado
    assert "**2**" in md  # 2 documentos
    assert "Livros" in md
    assert "Papers" in md
    # Análise round-trip: doc_b com 60% deve aparecer como notável
    assert "Notável" in md or "Crítico" in md  # 60% < 70%


def test_aggregate_writes_files(tmp_path: Path):
    _write_stats(tmp_path / "papers" / "doc")
    md, js = aggregate(tmp_path)
    assert md.exists() and md.name == "_OVERVIEW.md"
    assert js.exists() and js.name == "_OVERVIEW.json"
    data = json.loads(js.read_text(encoding="utf-8"))
    assert len(data["docs"]) == 1
    assert "generated_at" in data
