---
id: T103
titulo: Round-trip test script
status: closed
criado_em: 2026-05-05
fechado_em: 2026-05-05
fase: 1
depende_de: []
blocks: [T104]
tags: [conversor, roundtrip, validacao]
---

## Contexto
Hipótese do usuário: MD₁ → PDF → MD₂. Se MD₁ ≈ MD₂, conversão é "perfeita" (consistência do toolchain).

## Objetivo
Script `roundtrip_test.py` que:
1. Converte MD₁ → PDF via pandoc + Chrome
2. Converte PDF → MD₂ via marker
3. Compara via tokens normalizados (SequenceMatcher)
4. Reporta similaridade % e top divergências

## Critérios de aceitação
- [x] Normalização: remove page markers, basename de imagens, colapsa whitespace
- [x] SequenceMatcher para diff token-level
- [x] Relatório com 5 primeiras divergências

## Resultado
Script em `pesquisa_geral/livros/roundtrip_test.py`. Pronto, mas ainda não executado num capítulo (T104).

## Caveat documentado
Round-trip não pega erros sistemáticos da extração inicial — testa estabilidade do toolchain, não fidelidade ao livro original.
