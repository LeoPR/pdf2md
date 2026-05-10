---
id: T100
titulo: Roadmap conversor PDF MD bidirecional
status: research
criado_em: 2026-05-07
fase: 1
depende_de: []
blocks: [T101, T102, T103, T104]
tags: [conversor, roadmap, meta]
kind: decisao
---

## Contexto
Conversor PDF↔MD com 8 fases de sofisticação progressiva (extração → qualidade → fórmulas → imagens → tipografia → layout → cross-refs → empacotamento).

## Roadmap completo
Ver `pesquisa_geral/livros/ROADMAP_CONVERSOR.md` — 35 tickets em 8 fases.

## Status atual (Fase 1 completa)
- T101 marker extraction com GPU: closed
- T102 restructure por capítulo: closed
- T103 round-trip script: closed
- T104 round-trip baseline test: open
- T105 substituir extração antiga (anti-padrão _v2): in_progress

## Decisão pendente (depois do baseline em T104)
Vale ir para Fase 2 (quality scoring, hot spots) ou parar na Fase 1 (suficiente para uso pessoal)?

## Por que research e não open
Não tem entregável imediato — é meta-direção que orienta criação de tickets concretos conforme se decide avançar.
