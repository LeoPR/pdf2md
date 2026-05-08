---
id: T104
titulo: Round-trip test em 1 capítulo (baseline)
status: closed
criado_em: 2026-05-07
fechado_em: 2026-05-07
fase: 1
depende_de: [T103]
blocks: []
tags: [conversor, roundtrip, baseline]
---

## Contexto
Script existe (T103) mas nunca rodado. Sem baseline real não dá pra avaliar qualidade do toolchain.

## Objetivo
Rodar `roundtrip_test.py` no Capítulo 4 (médio em tamanho, rico em fórmulas e diagramas) e medir similaridade MD₁ vs MD₂.

## Critérios de aceitação
- [x] Round-trip executado sem erro
- [x] Similaridade ≥ 85% em tokens
- [x] Relatório com top divergências
- [x] Resultado documentado neste ticket

## Resultado

**Capítulo 4 — Quantum circuits** (~45 páginas, ~25 figuras, math-heavy):

| Métrica | Valor |
|---|---|
| MD₁ tokens | 19,710 |
| MD₂ tokens | 19,403 |
| Similaridade | **95.09 %** |
| Tempo MD→PDF (pandoc + Chrome) | ~5 s |
| Tempo PDF→MD (marker GPU) | ~9.5 min (568 s) |
| PDF intermediário | 512 KB |

## Análise das top divergências

Todas as 5 primeiras divergências são **cosméticas**, não perda de conteúdo:

1. `# 4.` vs `### **4.` — diferença de nível de heading + bold
2. `circuits` vs `circuits**` — bold marker
3. `---` desaparece — separator HTML
4. `####` aparece em MD₂ — re-detecção de subsection
5. `####` idem

Nenhuma divergência atingiu fórmula, conteúdo de parágrafo ou imagem. As diferenças são de **estrutura de marcação** que o marker re-interpreta após o round-trip.

## Decisão (per critério do roadmap)

> "Se similaridade > 90%: pipeline estável, pode parar na Fase 1"

**Resultado bate com esse critério.** Pipeline está estável e usável. Fases 2+ ficam como roadmap futuro (T100), não trabalho ativo.

## Caveat preservado
Round-trip não pega erros sistemáticos da extração inicial — testa estabilidade do toolchain (marker → pandoc → marker), não fidelidade ao livro original. Para isso seria necessário comparar com texto manualmente certificado, fora de escopo.
