"""Tests do table_teds (medidor TEDS de tabelas, T075).

- Unit HERMÉTICOS sem pandoc: TEDS sobre HTML inline (identidade, sensibilidade,
  cegueira do struct a texto, normalização de transporte, teto best-pipe).
- Caminho md→tabela com skipif pandoc (external-capability).
- Tudo skipa limpo se o extra [tables] não estiver instalado.
"""
import pytest

pytest.importorskip("table_recognition_metric", reason="extra [tables] ausente")

from pdf2md.table_teds import (  # noqa: E402
    TableTedsResult, best_pipe_from_table, table_doc_from_html,
    table_doc_from_md, table_roundtrip, teds_score,
)

GRID = ("<table><tr><th>a</th><th>b</th></tr>"
        "<tr><td>1</td><td>2</td></tr><tr><td>3</td><td>4</td></tr></table>")
GRID_WRAPPED = ("<table><thead><tr><th>a</th><th>b</th></tr></thead>"
                "<tbody><tr><td>1</td><td>2</td></tr><tr><td>3</td><td>4</td></tr></tbody></table>")
SPAN = ('<table><tr><th>g</th><th>p</th></tr>'
        '<tr><td rowspan="2">G0</td><td>x</td></tr><tr><td>y</td></tr></table>')


# --- herméticos (sem pandoc) -------------------------------------------------

def test_identity_eh_1():
    doc = table_doc_from_html(GRID)
    assert teds_score(doc, doc) == 1.0
    assert teds_score(doc, doc, structure_only=True) == 1.0


def test_sensibilidade_e_struct_cego_a_texto():
    gt = table_doc_from_html(GRID)
    swapped = table_doc_from_html(GRID.replace(">1<", ">4<").replace(">4</td></tr></table>", ">1</td></tr></table>"))
    deleted = table_doc_from_html(GRID.replace("<tr><td>3</td><td>4</td></tr>", ""))
    assert teds_score(swapped, gt) < 1.0                      # detecta troca de células
    assert teds_score(deleted, gt) < teds_score(swapped, gt)  # deletar linha pesa mais
    assert teds_score(swapped, gt, structure_only=True) == 1.0  # struct ignora texto


def test_normalizacao_transporte_thead_tbody():
    # pipe→pandoc envelopa em thead/tbody; HTML cru não — MESMA estrutura canônica
    assert teds_score(table_doc_from_html(GRID_WRAPPED), table_doc_from_html(GRID)) == 1.0


def test_fragmento_cuja_raiz_eh_table():
    # regressão do bug e25: lxml devolve a própria <table> como raiz e .// não a via
    assert table_doc_from_html(GRID) is not None
    assert table_doc_from_html(f"<div>{GRID}</div>") is not None
    assert table_doc_from_html("<p>sem tabela</p>") is None


def test_best_pipe_expande_spans_e_mede_teto():
    gt = table_doc_from_html(SPAN)
    pipe = best_pipe_from_table(gt)
    assert pipe.count("G0") == 2                 # célula rowspan duplicada
    assert pipe.splitlines()[1].count("---") == 2
    # teto < 1.0: pipe não representa o span (T440); mas >> 0 (conteúdo+grade ok)
    # (conversão pipe→doc sem pandoc: monta HTML direto p/ manter o teste hermético)
    rows = [ln for ln in pipe.splitlines() if not set(ln) <= {"|", "-"}]
    cells = [[c.strip() for c in ln.strip("|").split("|")] for ln in rows]
    html = "<table>" + "".join(
        "<tr>" + "".join(f"<{'th' if i == 0 else 'td'}>{c}</{'th' if i == 0 else 'td'}>"
                         for c in row) + "</tr>"
        for i, row in enumerate(cells)) + "</table>"
    ceiling = teds_score(table_doc_from_html(html), gt)
    assert 0.5 < ceiling < 1.0


# --- caminho md (pandoc external) -------------------------------------------

def _has_pandoc() -> bool:
    from pdf2md.discovery import available, find_pandoc
    return available(find_pandoc())


@pytest.mark.skipif(not _has_pandoc(), reason="pandoc ausente")
def test_table_roundtrip_md_identidade_e_sem_tabela():
    md = "| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |"
    r = table_roundtrip(md, md)
    assert r == TableTedsResult(1.0, 1.0, False)
    r0 = table_roundtrip(md, "só prosa, nenhuma tabela aqui")
    assert r0.no_table and r0.teds == 0.0
    with pytest.raises(ValueError):
        table_roundtrip("sem tabela no GT", md)
