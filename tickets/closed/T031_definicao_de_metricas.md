---
id: T031
titulo: Definição de métricas além de token-similarity
status: closed
criado_em: 2026-05-09
fechado_em: 2026-05-10
fase: 0
depende_de: [T030]
blocks: [T050]
tags: [decisao, metricas, validacao]
kind: decisao
---

## Contexto

Métrica atual (`SequenceMatcher` de tokens normalizados) reconhecidamente captura mal a 1ª prioridade de PHILOSOPHY.md (conteúdo): drift LaTeX (`\rm` vs `\mathrm`) conta como divergência; uma fórmula que **suma** também conta — sem separar os dois casos a métrica é opaca.

`aggregate_stats.py:252-256` já reconhece o problema:

> Para validar **preservação de conteúdo** (1ª prioridade), seria preciso comparar AST math e contagem de fórmulas em vez de tokens.

## Objetivo

Decidir, baseado na revisão de literatura (T030) e nas necessidades reais do projeto, **quais métricas adotar** e por quê. Documentar em `docs/reference/metricas.md`.

Métricas candidatas (a discutir):

| Métrica | O que mede | Categoria PHILOSOPHY |
|---|---|---|
| Token similarity (atual) | Estabilidade textual genérica | mistura tudo |
| Formula count diff | Fórmulas perdidas/adicionadas | 1ª (conteúdo) |
| Formula AST distance | Drift de notação LaTeX | 4ª (formato) |
| Citation count diff | Citações perdidas | 1ª (conteúdo) |
| Header structure diff (TEDS-like) | Hierarquia de títulos | 2ª (estrutura) |
| Image ref preservation | Imagens referenciadas | 2ª (estrutura) |
| Table preservation (TEDS) | Tabelas como tabelas | 2ª (estrutura) |
| Words-only similarity (sem `$..$`) | Conteúdo de prosa | 1ª (conteúdo) |

## Critérios de aceitação

- [ ] `docs/reference/metricas.md` existe com a lista escolhida
- [ ] Cada métrica tem: definição, fórmula, threshold de "ok / atenção / falha"
- [ ] Mapeamento métrica → categoria de PHILOSOPHY (conteúdo / estrutura / etc.)
- [ ] Plano de implementação progressiva (começar por 2-3, expandir)
- [ ] Decisão sobre se token-similarity continua sendo computada (provavelmente sim, mas com peso reduzido)

## Não-objetivo

- Implementar as métricas (fica para tickets de pipeline depois)
- Cobrir todas as métricas possíveis — escolher o que importa para os casos reais

## Conexão com outros tickets

- T030 (literatura) informa este
- T050 (baseline) será o primeiro a aplicar essas métricas
- T100/T410 (comparação de ferramentas) precisa dessas métricas para gerar resultados comparáveis
