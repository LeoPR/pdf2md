# Notas de curadoria — `<doc_id> pg<NN>`

> Template em branco. Renomear para `pg<NN>.note.md` ao começar curadoria.

## Categoria da página

`<math_denso | tabela_complexa | formula_multilinha | paper_2col | notes_1col | gov_multicol | scanned | form>`

## Modos de falha observados no extrator atual (marker-pdf 1.10.2)

*Listar concretamente cada desvio entre extração e PDF original. Formato:
linha de output errado → o que deveria ser → categoria do erro.*

- [ ] (exemplo) `\alpha + \beta` mapeado como `α + β` em texto plain
  → deveria ser `$\alpha + \beta$` em math display → escape markdown
- [ ] (exemplo) parágrafo cortado no meio (provavelmente por reflow do marker)
  → continuar
- [ ] ...

## Casos onde precisei desviar do GFM padrão

*Se tabela exigiu HTML inline, fórmula precisou de LaTeX inline em vez de
KaTeX, etc.*

- [ ] (exemplo) tabela com colspan exigiu `<table>` HTML inline em vez de pipe
- [ ] ...

## Itens com ambiguidade real

*Onde foi difícil decidir "qual é o GT canônico" — devolver pro grupo.*

- [ ] (exemplo) page header "p. 199" do livro deve aparecer no MD GT? Decisão: não
- [ ] ...

## Confiança da curadoria

- [ ] Auditei contra o PDF original
- [ ] Confiante que o resultado é o GT canônico
- [ ] Tempo gasto: ~_X_ min

## Próxima ação

- [ ] Renomear `.expected.md.draft` para `.expected.md` (sinaliza pronto)
- [ ] Ou pendente: ___________
