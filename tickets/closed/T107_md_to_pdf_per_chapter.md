---
id: T107
titulo: Gerar PDF a partir do MD de cada capítulo
status: closed
criado_em: 2026-05-07
fechado_em: 2026-05-17
fase: 1
depende_de: [T102]
blocks: []
tags: [conversor, pdf, gerar]
kind: pipeline
resolucao: Coberto por `pdf2md.pdfs.generate_all()` + CLI `pdf2md pdfs DIR` (v0.4+)
---

## Resolução (2026-05-17)

O escopo do ticket foi absorvido pelo refactoring de v0.4 que migrou
scripts standalone para o pacote `pdf2md`. Hoje vive em:

- **`src/pdf2md/pdfs.py:43`** `md_to_pdf(md_path, out_pdf=None, ..., overwrite=False)`
  — single chapter, pandoc + Chrome headless + KaTeX
- **`src/pdf2md/pdfs.py:128`** `generate_all(base, on_progress=...)` — itera
  sobre `find_chapter_mds(base)` e roda `md_to_pdf` para cada
- **CLI**: `pdf2md pdfs DIR` (exposto em `src/pdf2md/cli.py:566`)

### Critérios atendidos

- [x] **Script genérico** — `find_chapter_mds()` descobre capítulos por
  convenção `<chapter>/<chapter>.md`; funciona para qualquer livro nesse padrão
- [x] **Roda para todos os 21 capítulos do N&C** — validado em produção
  (ver [T108](T108_pacote_conversor_readme.md) § "Validação em produção")
- [x] **PDFs salvos lado a lado dos MDs** — `out_pdf` default =
  `md_path.with_suffix(".pdf")`

## Contexto original

Usuário queria ver o resultado MD→PDF de cada capítulo para comparação
visual com o original.

## Objetivo original

Script `gen_chapter_pdfs.py` que para cada `<chapter>/<chapter>.md` em
`Quantum_Computation_and_Quantum_Information/` gere `<chapter>/<chapter>.pdf`
via pandoc + Chrome headless + KaTeX, com imagens locais resolvidas via
`--resource-path`.
