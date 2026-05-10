---
id: T040
titulo: Popular corpus canônico inicial (8-12 PDFs)
status: in_progress
criado_em: 2026-05-09
fechado_em:
fase: 0
depende_de: [T021, T022, T030]
blocks: [T050]
tags: [infra, corpus, benchmark]
kind: infra
---

## Contexto

`corpus/_canonical/MANIFEST.md` foi criado vazio (T021 + T022). Para validar o pipeline em casos reais e comparar com ferramentas alternativas (T410+), precisa de 8-12 PDFs públicos categorizados.

## Objetivo

Popular o manifest com PDFs livres (CC, public domain, arXiv) cobrindo as categorias problemáticas:

| Categoria | Alvo |
|---|---|
| `livro_math_heavy` | 1-2 |
| `livro_image_heavy` | 1-2 |
| `livro_classical_typography` | 1 |
| `paper_math_heavy` | 1-2 (arXiv) |
| `paper_bio_med` | 1 (PMC open-access) |
| `slides_pptx_export` | 1-2 (CC ou autorizado) |
| `scanned_image_only` | 1 (Internet Archive) |
| `multi_col_dense` | 1 (paper IEEE-style) |
| `multilingual_pt` | 1 (tese UTFPR / USP / repositório livre) |

## Critérios de aceitação

- [ ] 8-12 entradas no `corpus/_canonical/MANIFEST.md`
- [ ] Cada entrada com: id, title, authors, year, license, category, origin.url, sha256 (depois de baixar), local_copy.path apontando para `Z:\caches\corpus\pdf2md\`
- [ ] Pelo menos 1 PDF por categoria meta
- [ ] PDFs baixados em `Z:\caches\corpus\pdf2md\` (verificável via sha256)
- [ ] Licenças validadas (não confiar só no "está na internet")

## Não-objetivo

- Cobrir todas as 9 categorias na primeira passagem (algumas podem ficar para v2 do corpus)
- Validar qualidade do conteúdo (foco é diversidade, não curadoria)
- Rodar o pipeline neles ainda (isso é T050+)

## Sugestões iniciais (a validar licença)

- arXiv 2106.05919v2 (já usado em multi-iteration test) — paper math-heavy
- Preskill quantum lecture notes (Caltech) — math-heavy, free for academic use
- Goodfellow Deep Learning — image-heavy (verificar se há PDF baixável CC)
- Project Gutenberg — livro tipografia clássica
- arXiv qualquer paper LLM recente — multi-col / paper acadêmico

Lista completa de candidatos no T430 (que vira histórico depois deste fechar).
