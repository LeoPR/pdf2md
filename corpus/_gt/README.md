# Mini-corpus de Ground Truth (GT) humano — T060

> *Páginas selecionadas com MD canônico transcrito manualmente por humano.
> Destrava T072 (calibração reconstrutor), T410 (alt-tools comparativo),
> e várias questões do backlog de literatura (Q13/Q14/Q17).*

## Status (2026-05-16)

| Doc | Pgs | Categoria | Pré-fill | Curadoria humana |
|---|---|---|---|---|
| nielsen_chuang_cap4 | 199, 200, 204 | math denso, fórmula multi-linha | ✅ draft | ⏳ pendente |
| preskill_ph219_ch5 | 1, 2 | notes math single-col | ✅ draft | ⏳ pendente |
| arxiv_1706_03762 | 3 | paper 2-col, math moderado | ✅ draft | ⏳ pendente |
| arxiv_2106_05919v2 | 30 | math heavy | ✅ draft | ⏳ pendente |
| cdc_mmwr_73_35_a1 | 1 | tabela complexa | ✅ draft | ⏳ pendente |

Total: **8 páginas** em 5 docs cobrindo 5 categorias-meta.

## Fluxo de trabalho

```
[automático]                    [humano: 4-6h]               [automático]
                                ─────────────────
 marker extract             →   audit + correção MD     →    pdf2md gt-compare
 (já feito)                     (esta etapa)                  (lab/e15)
   ↓                              ↓                             ↓
 .expected.md.draft         →   .expected.md            →    WER + count-diff
                                + .note.md
```

## Convenção de arquivos

Para cada `<doc_id>/`:

- `pg<NN>.expected.md.draft` — pré-fill (output atual do extrator)
- `pg<NN>.note.md` — observações da curadoria (template em branco)
- `pg<NN>.expected.md` — **versão canônica, criada pelo humano** ao renomear o draft

A presença de `.expected.md` (sem `.draft`) indica que aquela página passou
pela curadoria e pode ser usada para validação.

## Como curar (passo a passo humano)

Para cada página `<doc_id>/pg<NN>`:

1. **Abrir o PDF na página correspondente** (PDF original; cap 4 N&C usa
   numeração do livro pgs 199-243; outros usam page numbers do PDF)
2. **Abrir `pg<NN>.expected.md.draft`** no editor lado a lado com o PDF
3. **Comparar visualmente cada parágrafo**:
   - Texto correto? Hyphens não-quebrados? Caracteres especiais OK (α, ≥)?
   - Math em `$..$` ou `$$..$$`? LaTeX igual ao livro?
   - Headers com `#` no nível certo?
   - Tabelas em GFM ou HTML inline se complexas?
   - Imagens referenciadas com `![alt](images/X)` (sem path absoluto)?
4. **Corrigir o que estiver errado**. Anotar **por quê** no `.note.md`
   (e.g. "marker mapeou \alpha como \alpha mas o livro tem α direto")
5. **Salvar como `pg<NN>.expected.md`** (remove o `.draft`)
6. Repetir para próxima página

Tempo estimado: ~30-45 min por página de math-heavy, ~15-20 min por
página simples. Total: **4-6h**.

## Validação automatizada (após curadoria)

```powershell
cd lab/e15_gt_validation
.\run.ps1
```

Output: `out/gt_comparison.json` + `out/gt_comparison.md` com:
- WER-prosa (com mascaramento de markup) por página
- Count-diffs (math display, math inline, headers, tabelas, imagens)
- Comparação com round-trip atual para ver se GT diverge ou converge

## Não-objetivo

- Curar livros inteiros — 8 páginas representativas é suficiente
- Validar TODAS métricas — WER + count-diffs basta para responder Q1
- Automatizar a curadoria — é trabalho humano consciente
