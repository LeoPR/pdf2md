---
id: T107
titulo: Gerar PDF a partir do MD de cada capítulo
status: open
criado_em: 2026-05-07
fechado_em:
fase: 1
depende_de: [T102]
blocks: []
tags: [conversor, pdf, gerar]
kind: pipeline
---

## Contexto
Usuário quer ver o resultado MD→PDF de cada capítulo para comparação visual com o original.

## Objetivo
Script `gen_chapter_pdfs.py` que:
- Para cada `<chapter>/<chapter>.md` em `Quantum_Computation_and_Quantum_Information/`
- Gera `<chapter>/<chapter>.pdf` via pandoc + Chrome headless + KaTeX
- Imagens locais resolvidas via `--resource-path`

## Critérios de aceitação
- [ ] Script genérico (funciona para qualquer livro extraído nesse padrão)
- [ ] Roda para todos os 21 capítulos do N&C
- [ ] PDFs salvos no lado dos MDs
