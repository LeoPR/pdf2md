---
id: T102
titulo: Restructure output por capítulo + index.md
status: closed
criado_em: 2026-05-05
fechado_em: 2026-05-07
fase: 1
depende_de: [T101]
blocks: [T103, T105]
tags: [conversor, restructure]
---

## Contexto
Marker output é um MD único de 2.6 MB. Para navegação efetiva, precisa fatiar por capítulo.

## Objetivo
Script `restructure_nc.py` que usa PyMuPDF TOC para boundaries de capítulos, fatia o MD por headers detectados, organiza imagens por página em pastas locais.

## Critérios de aceitação
- [x] 21 seções extraídas (front matter + 12 capítulos + 6 apêndices + biblio + índice)
- [x] Cada seção em pasta própria com images/
- [x] index.md gerado com TOC + páginas + contagens

## Resultado
Estrutura em `pesquisa_geral/livros/Quantum_Computation_and_Quantum_Information_v2/` (será renomeado em T105).
- 5.9 MB total
- Índice navegável

## Notas
- Header regex teve que aceitar qualquer nível (`^#+\s+`) porque marker variou níveis (`#`, `##`, `####`)
