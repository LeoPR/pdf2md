---
id: T040
titulo: Popular corpus canônico inicial (8-12 PDFs)
status: closed
criado_em: 2026-05-09
fechado_em: 2026-05-10
fase: 0
depende_de: [T021, T022, T030]
blocks: [T050]
tags: [infra, corpus, benchmark]
kind: infra
---

## Contexto

`docs/reference/corpus/manifest_canonical.md` foi criado vazio (T021 + T022). Para validar o pipeline em casos reais e comparar com ferramentas alternativas (T410+), precisa de 8-12 PDFs públicos categorizados.

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

- [x] 8-12 entradas no `docs/reference/corpus/manifest_canonical.md` — **8 entradas**
- [x] Cada entrada com schema completo
- [~] Pelo menos 1 PDF por categoria meta — **5/9 cobertas** (paper_math_heavy×2, multi_col_dense, livro_math_heavy×2, livro_classical_typography, scanned_image_only, paper_bio_med pendente)
- [x] PDFs baixados em `Z:\caches\corpus\pdf2md\` — **7/8 baixados** (~84 MB total)
- [x] Licenças validadas

## Resultado

8 entradas no MANIFEST canonical:

| id | categoria | size |
|---|---|---:|
| arxiv_2106_05919v2 | paper_math_heavy | 1.96 MB |
| arxiv_1706_03762 (Attention) | paper_math_heavy | 2.21 MB |
| arxiv_1810_04805 (BERT) | multi_col_dense | 0.77 MB |
| preskill_ph229_ch1 | livro_math_heavy | 0.26 MB |
| preskill_ph219_ch5 | livro_math_heavy | 0.32 MB |
| ia_newton_principia | livro_classical_typography | 60.45 MB |
| ia_mathematics00wils (Wilson) | scanned_image_only | 18.10 MB |
| pmc_10811782 | paper_bio_med | (pendente) |

Cobertura: 5/9 categorias-meta atingidas. Categorias `livro_image_heavy`, `multilingual_pt`, `slides_pptx_export` ficam para uma v2 do corpus (`slides_pptx_export` já é coberto pelos sources do AulaQuantum). PMC bloqueia scrapers automatizados — pendente download manual via browser.

## Notas para v2 do corpus (futuro)

- `livro_image_heavy`: Goodfellow DL não tem PDF baixável CC. Buscar Bishop PRML edition de cortesia ou textbook open-access tipo Murphy "ML Probabilistic Perspective" online.
- `multilingual_pt`: tese UTFPR ou USP — pesquisar repositório `repositorio.utfpr.edu.br` com filtro PDF baixável.
- `paper_bio_med`: tentar bioRxiv DOI direto, ou PLOS One que tem URL `journals.plos.org/.../article/file?id=...&type=printable`.

## Conexão com tickets

- T430 (corpus livre, antigo) — substituído por este; pode fechar como "superseded by T040".
- T050 (baseline) — desbloqueado, usa nielsen_chuang (sources) como entrada.
- Família futura `lab/e1X_*` (T410, alt tools) — vai usar este corpus como benchmark.
