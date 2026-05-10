---
id: T024
titulo: Reorganização de tickets em faixas (kind)
status: closed
criado_em: 2026-05-09
fechado_em: 2026-05-09
fase: 0
depende_de: []
blocks: []
tags: [infra, tickets, organizacao]
kind: infra
---

## Contexto

Tickets atuais (T013, T100-T199, T400-T499) misturavam **infra**, **pipeline**, **decisões arquiteturais** e **hipóteses testáveis** sem distinção clara. Princípio do usuário: "para testar uma hipótese, ela não precisa se preocupar com como criar [a infra], só precisa saber qual é e como usar".

## Objetivo

Adicionar campo `kind:` ao frontmatter de todos os tickets existentes, classificando em 5 faixas (`infra`, `pipeline`, `imagens`, `experimento`, `decisao`). Criar `tickets/INDEX.md` com agrupamento por `kind:`. Atualizar `tickets/README.md` com a convenção.

## Critérios de aceitação

- [x] `kind:` adicionado em 21 tickets (todos os existentes pré-fase-0)
- [x] `tickets/INDEX.md` criado, agrupando por `kind:`
- [x] `tickets/README.md` atualizado com seção "Faixa `kind:`"
- [x] Faixa T020-T099 reservada para infra do `pdf2md`
- [x] Hipóteses (`kind: experimento`) idealmente apontam para `lab/eNN_/`

## Mapeamento aplicado

| `kind` | Tickets |
|---|---|
| `infra` | T013, T020-T024, T030, T040, T050, T105, T430 |
| `pipeline` | T101, T102, T103, T104, T107, T108 |
| `imagens` | T130, T131 |
| `experimento` | T050, T106, T137, T410, T420, T450 |
| `decisao` | T031, T100, T400, T401, T440, T451 |

## Resultado

Sistema de tickets agora distingue infra de hipótese. O experimento `lab/e00_baseline_marker/` (a ser criado em T050) é a primeira hipótese testável que adota o novo padrão (vive no lab, com ticket macro só apontando).

## Notas

- T105 tem inconsistência herdada (status no frontmatter diz `in_progress`, mas arquivo está em `closed/`). Não corrigido nesta passagem; fica como nota de housekeeping.
- T430 (corpus livre) ficou redundante com T040 + manifests; pode ser fechado em sessão futura.
