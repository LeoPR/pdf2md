---
id: T401
titulo: Documentar hierarquia de prioridades
status: open
criado_em: 2026-05-07
fechado_em:
fase: 1
depende_de: [T400]
blocks: []
tags: [design, philosophy, hierarquia]
---

## Contexto
Filosofia de design do conversor — qual prioridade quando há conflito.

## Resultado
Documentado em `tools/pdf_md_converter/PHILOSOPHY.md`. 4 níveis:
1. Conteúdo (palavras, fórmulas, números)
2. Estrutura útil (headers, tabelas, imagens com semântica)
3. Otimização intermediária (formato adaptativo, links externos)
4. Formatação idêntica (compactação como transporte)

## Por que open e não closed
Documento criado, mas vai precisar revisão conforme outros tickets do T400 amadurecem
(testes alternativos, fallback low-resource podem expor casos não previstos).
