---
id: T060
titulo: Mini-corpus de GT humano (5-10 páginas curadas)
status: open
criado_em: 2026-05-10
fechado_em:
fase: 5
depende_de: [T031, T040]
blocks: [T410]
tags: [validacao, gt, ground-truth, mini-corpus]
kind: infra
---

## Contexto

[`docs/explanation/literatura.md`](../../docs/explanation/literatura.md) §4 e [`docs/reference/metricas.md`](../../docs/reference/metricas.md) reconhecem que **round-trip não substitui GT humano** para validar fidelidade real do pipeline. Round-trip captura estabilidade (idempotência), mas erros silenciosos por simetria entre extrator e reconstrutor passam despercebidos.

Para a **Frente A (Validação)** ficar completa, precisa de mini-corpus pequeno com MD canônico transcrito manualmente.

## Objetivo

Curar 5-10 páginas com MD canônico em `corpus/_gt/`, cobrindo casos representativos:

- 2 páginas N&C cap. 4 (math denso, já tem MD₁ histórico — auditar e corrigir)
- 2 páginas Preskill ph219 ch5 (matéria pareada com N&C cap. 4 — comparação inter-source)
- 1 página de arxiv 1706.03762 (multi-col denso, math moderado)
- 1 página de arxiv 2106.05919v2 (math heavy, paper longo)
- 1 página com tabela complexa
- 1 página com fórmula multi-linha (Trotter expansion ou similar)

Cada página GT acompanhada de:
- `<id>/<page>.expected.md` — MD canônico
- `<id>/<page>.note.md` — observações sobre desvios da regra de markdown (e.g. tabela com colspan que precisou inline-HTML)

## Critérios de aceitação

- [ ] 8-10 páginas em `corpus/_gt/` com MD curado
- [ ] Para cada página: cobertura de pelo menos 1 caso de cada categoria-meta
- [ ] Pipeline atual rodado nas mesmas páginas (extração → MD; comparação WER-prosa contra GT)
- [ ] Resultado: tabela WER-prosa, count-diff de fórmulas, count-diff de citações por página
- [ ] Comparação: gap entre `WER(GT, extracao)` e `WER(roundtrip)` quantificado

## Critério de promoção / descarte

- Promover para `lab/eXX_gt_validation/` se a comparação revelar gap significativo (> 1pp) entre round-trip e GT — vira métrica primária do projeto
- Descartar / congelar se gap < 1pp — round-trip continua sendo proxy aceitável

## Não-objetivo

- Curar livro inteiro — 8-10 páginas representativas é suficiente para responder a Q1 da [LITERATURA.md §6](../../docs/explanation/literatura.md)
- Validar todas as métricas de [METRICS.md](../../docs/reference/metricas.md) — apenas WER-prosa + count-diffs nesta passagem
- Automatizar a curadoria — é trabalho humano consciente, ~4-6h

## Esforço estimado

~4-6h de trabalho humano + ~1-2h de comparação automatizada.

## Conexão

- Frente A da hierarquia (validação)
- Bloqueia T410 (alt tools): comparação Marker × Nougat × MinerU precisa de GT para ser confiável
- Q1 do backlog em LITERATURA.md
