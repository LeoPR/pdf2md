# Manifest — corpus canônico público

PDFs livres / open-access / public domain usados para benchmark e ablação. Cada entrada é re-baixável via URL — a cópia local em `Z:\caches\corpus\pdf2md\` é por comodidade.

Para schema completo, ver [`../_sources/MANIFEST.md`](../_sources/MANIFEST.md). Aqui o `origin.type` será sempre `url`, e `license` sempre uma licença redistribuível.

## Cobertura desejada

Objetivo: corpus pequeno mas representativo das categorias problemáticas do conversor. Meta de **8-12 entradas**, distribuídas:

- 1-2 livros math-heavy
- 1-2 papers math-heavy (arXiv)
- 1 paper bio/med (PMC)
- 1 PDF "image-only" (scanned)
- 1-2 slides PPTX export
- 1 layout 2-coluna denso (IEEE)
- 1 multilíngue / pt-BR
- 1 tipografia clássica

## Cobertura atual (T040 v1, 2026-05-10)

7 entradas (6 baixadas + 1 pendente). Cobre 4 das 9 categorias-meta. Categorias `livro_image_heavy`, `livro_classical_typography`, `slides_pptx_export` (já coberto via `_sources/`), `multilingual_pt` ficam para v2 do corpus.

| categoria | entradas |
|---|---|
| paper_math_heavy | 2 |
| multi_col_dense | 1 |
| livro_math_heavy | 2 |
| scanned_image_only | 1 |
| paper_bio_med | 1 (pendente download manual — publishers bloqueiam scrapers) |

---

## Entradas

### arxiv_2106_05919v2 — A practical guide to quantum machine learning and quantum optimisation

```yaml
id: arxiv_2106_05919v2
title: A Practical Guide to Quantum Machine Learning and Quantum Optimisation
authors: [Elías F. Combarro, Samuel Gonzalez-Castillo]
year: 2021
arxiv_id: 2106.05919v2
license: arxiv non-exclusive
category: paper_math_heavy
pages: 30

origin:
  type: url
  url: https://arxiv.org/pdf/2106.05919v2.pdf
  alternates:
    - https://arxiv.org/abs/2106.05919

local_copy:
  path: Z:\caches\corpus\pdf2md\arxiv_2106_05919v2.pdf
  sha256: 302109c2c0cab1929ae2a858ad09294d4b5e06ceaf632d96a16627ecf1f08061
  downloaded_at: 2026-05-10

sha256: 302109c2c0cab1929ae2a858ad09294d4b5e06ceaf632d96a16627ecf1f08061
size_bytes: 1963837
added_at: 2026-05-10

notes: |
  Já usado historicamente em multi-iteration round-trip — 0.86% drift em
  5 iterações. Útil como caso conhecido para regressão.
```

### arxiv_1706_03762 — Attention Is All You Need (Vaswani et al.)

```yaml
id: arxiv_1706_03762
title: Attention Is All You Need
authors: [Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin]
year: 2017
arxiv_id: 1706.03762
license: arxiv non-exclusive
category: paper_math_heavy
pages: 15

origin:
  type: url
  url: https://arxiv.org/pdf/1706.03762.pdf
  alternates:
    - https://arxiv.org/abs/1706.03762

local_copy:
  path: Z:\caches\corpus\pdf2md\arxiv_1706_03762.pdf
  sha256: bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697
  downloaded_at: 2026-05-10

sha256: bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697
size_bytes: 2215244
added_at: 2026-05-10

notes: |
  Paper canônico (Transformer). Math-heavy moderado, layout 2-coluna,
  tabelas, diagramas de arquitetura. Boa diversidade fora de física.
```

### arxiv_1810_04805 — BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding

```yaml
id: arxiv_1810_04805
title: 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding'
authors: [Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova]
year: 2018
arxiv_id: 1810.04805
license: arxiv non-exclusive
category: multi_col_dense
pages: 16

origin:
  type: url
  url: https://arxiv.org/pdf/1810.04805.pdf
  alternates:
    - https://arxiv.org/abs/1810.04805

local_copy:
  path: Z:\caches\corpus\pdf2md\arxiv_1810_04805.pdf
  sha256: 5692a5514787a8c6727b4ff3b726a3385798bc68e12138d1d4af83947e2acf6e
  downloaded_at: 2026-05-10

sha256: 5692a5514787a8c6727b4ff3b726a3385798bc68e12138d1d4af83947e2acf6e
size_bytes: 775166
added_at: 2026-05-10

notes: |
  Layout 2-coluna NeurIPS-style típico, tabelas comparativas grandes,
  pouco math em equação display, muito em texto. Bom contraste com
  arxiv_2106_05919v2 (math-heavy).
```

### preskill_ph229_ch1 — Quantum Computation Lecture Notes (Caltech), Chapter 1

```yaml
id: preskill_ph229_ch1
title: 'Quantum Computation: Lecture Notes (Ch. 1 — Introduction and Overview)'
authors: [John Preskill]
year: 1997
publisher: Caltech (Ph229/CS219 course notes)
license: read-only-online
category: livro_math_heavy
pages: 30

origin:
  type: url
  url: http://www.preskill.caltech.edu/ph229/notes/chap1.pdf

local_copy:
  path: Z:\caches\corpus\pdf2md\preskill_ph229_ch1.pdf
  sha256: 992f1c5469587aca584781f98d7b7bc6416345795cb702fa4baf583644f74e5b
  downloaded_at: 2026-05-10

sha256: 992f1c5469587aca584781f98d7b7bc6416345795cb702fa4baf583644f74e5b
size_bytes: 260328
added_at: 2026-05-10

notes: |
  Caltech ph229/CS219 course notes — sem licença explícita na página.
  Tratar como "read-only-online" (uso acadêmico, não redistribuir).
  Capítulo 1 cobre fundamentos (similar ao cap. 1 do N&C). Útil para
  comparar tratamento do mesmo material por autor diferente.
```

### preskill_ph219_ch5 — Quantum Computation Lecture Notes (Caltech), Chapter 5: Classical and Quantum Circuits

```yaml
id: preskill_ph219_ch5
title: 'Quantum Computation: Lecture Notes (Ch. 5 — Classical and Quantum Circuits)'
authors: [John Preskill]
year: 2015
publisher: Caltech (Ph219/CS219 course notes)
license: read-only-online
category: livro_math_heavy
pages: 54

origin:
  type: url
  url: http://www.preskill.caltech.edu/ph219/chap5_15.pdf

local_copy:
  path: Z:\caches\corpus\pdf2md\preskill_ph219_ch5.pdf
  sha256: e5f011c45dd67810ae6de81276c8a15c02948a772264fdfd7b638e4006aa62c3
  downloaded_at: 2026-05-10

sha256: e5f011c45dd67810ae6de81276c8a15c02948a772264fdfd7b638e4006aa62c3
size_bytes: 332702
added_at: 2026-05-10

notes: |
  **Pareado com N&C cap. 4 (Quantum Circuits)** — mesma matéria, autor
  diferente, tradição tipográfica diferente. Excelente para validar se
  a métrica de extração captura conteúdo independente de estilo. Versão
  de Julho/2015 — mais recente que ph229_ch1.
```

### ia_mathematics00wils — Mathematics (Wilson, c. 1799-1800)

```yaml
id: ia_mathematics00wils
title: Mathematics
authors: [William Wilson]
year: 1800
license: public_domain
category: scanned_image_only
pages: null  # ler do PDF quando rodar baseline

origin:
  type: url
  url: https://archive.org/download/mathematics00wils/mathematics00wils.pdf
  alternates:
    - https://archive.org/details/mathematics00wils

local_copy:
  path: Z:\caches\corpus\pdf2md\ia_mathematics00wils.pdf
  sha256: e61dcd29747da4a4e849ab0c7b70430c0e6ab42202beda5c51b9683f5aeda6c4
  downloaded_at: 2026-05-10

sha256: e61dcd29747da4a4e849ab0c7b70430c0e6ab42202beda5c51b9683f5aeda6c4
size_bytes: 18104395
added_at: 2026-05-10

notes: |
  Livro escaneado pelo Internet Archive — provavelmente PDF de imagens
  (raster-only), sem texto embutido. Categoria-teste para o caso onde
  marker precisa OCR'izar tudo. Domínio público (publicado pré-1928).
  18 MB.
```

### pmc_10811782 — Accelerating an integrative view of quantum biology *(pendente download)*

```yaml
id: pmc_10811782
title: Accelerating an integrative view of quantum biology
authors: [TBD]  # preencher quando baixar
year: 2024
license: cc_by
category: paper_bio_med
pages: null

origin:
  type: url
  url: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10811782/pdf/fphys-14-1349013.pdf
  alternates:
    - https://pmc.ncbi.nlm.nih.gov/articles/PMC10811782/
    - https://europepmc.org/article/MED/PMC10811782

local_copy: null

sha256: null
size_bytes: null
added_at: 2026-05-10

notes: |
  Tentativa de download automatizado via curl falhou (PMC retorna página
  interstitial; europepmc.org/backend deu timeout; MDPI 403). Publishers
  bloqueiam scrapers.

  **Pendente**: baixar manualmente pelo browser (clicar "Download PDF"
  na página do artigo) e salvar em `Z:\caches\corpus\pdf2md\pmc_10811782.pdf`.
  Após salvar, atualizar este bloco com:
    - sha256 (rodar `sha256sum`)
    - size_bytes
    - local_copy.path / sha256 / downloaded_at
    - authors / pages

  Frontiers in Physiology, CC-BY (redistribuível). Categoria bio_med
  representa pipeline em domínio fora da física/CS.
```
