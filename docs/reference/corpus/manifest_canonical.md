# Manifest — corpus canônico público

PDFs livres / open-access / public domain usados para benchmark e ablação. Cada entrada é re-baixável via URL — a cópia local em `Z:\caches\corpus\pdf2md\` é por comodidade.

Para schema completo, ver [`manifest_sources.md`](manifest_sources.md). Aqui o `origin.type` será sempre `url`, e `license` sempre uma licença redistribuível.

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

## Cobertura atual (T040 v1.2, 2026-05-10)

**17 entradas, 12 baixadas + 5 pendentes.** Cobre **9 das 11 categorias** (a
taxonomia foi expandida em 2026-05-10 com categorias "sujas" — ver
[`manifest_sources.md`](manifest_sources.md)).

| categoria | entradas | baixadas |
|---|---|---|
| paper_math_heavy | 2 | 2 |
| multi_col_dense | 2 | 1 (CDC; 1 BERT já contava) |
| livro_math_heavy | 2 | 2 |
| livro_classical_typography | 1 | 1 |
| scanned_image_only | 1 | 1 (+ 1 PMC pendente também conta aqui) |
| scanned_with_bad_ocr | 3 | 1 (Atkins baixado; Merriman + FR-1985 pendentes) |
| slides_pptx_export | 2 | 1 (MIT OCW baixado; ACM Gambetta pendente) |
| gov_form | 2 | 2 (IRS f1040 e FR-1936 baixados) |
| paper_bio_med | 2 | 0 (PMC bloqueia scrapers; ambos pendentes) |

Gaps: `mobile_capture_scan` e `photo_collage_overlay` (sem fonte com
licença redistribuível clara — documentado em [`../../_archive/PDFS_SUJOS_CANDIDATOS.md`](../../_archive/PDFS_SUJOS_CANDIDATOS.md)).

Total em `Z:\caches\corpus\pdf2md\`: **12 PDFs, ~119 MB**.

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
pages: 98  # corrigido em 2026-05-10 após e01 — havia estimado 30 inicialmente

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

### ia_newton_principia — The Mathematical Principles of Natural Philosophy (Newton, 1729 translation)

```yaml
id: ia_newton_principia
title: The Mathematical Principles of Natural Philosophy
authors: [Isaac Newton]
year: 1729  # tradução inglesa do Principia (1687 original)
license: public_domain
category: livro_classical_typography
pages: 594

origin:
  type: url
  url: https://archive.org/download/newtonspmathema00newtrich/newtonspmathema00newtrich.pdf
  alternates:
    - https://archive.org/details/newtonspmathema00newtrich

local_copy:
  path: Z:\caches\corpus\pdf2md\ia_newton_principia.pdf
  sha256: 07ff23e18f431ec812a6c954ce57c3ec1e92dbc2ea01e16f228eb22ba97de370
  downloaded_at: 2026-05-10

sha256: 07ff23e18f431ec812a6c954ce57c3ec1e92dbc2ea01e16f228eb22ba97de370
size_bytes: 60451456
added_at: 2026-05-10

notes: |
  Escaneado pelo Internet Archive — também é raster (sobreposição com
  scanned_image_only). Diferença vs `ia_mathematics00wils`: este tem
  matemática clássica (geometria + cálculo nas raízes) com tipografia
  do século XVIII. Categoria primária `livro_classical_typography`
  porque o foco é tipografia/notação histórica, e a categoria
  scanned_image_only já está coberta por mathematics00wils.
  60 MB — maior PDF do corpus canônico.
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

---

## Entradas — categoria "sujos" (2026-05-10)

Documentos que **degradam o pipeline** intencionalmente. Origem da pesquisa em [`../../_archive/PDFS_SUJOS_CANDIDATOS.md`](../../_archive/PDFS_SUJOS_CANDIDATOS.md).

### ocw_mit_6_0002_lec1 — MIT OCW 6.0002 Lecture 1

```yaml
id: ocw_mit_6_0002_lec1
title: 'MIT 6.0002 Introduction to Computational Thinking and Data Science — Lecture 1'
authors: [John Guttag, Eric Grimson]
year: 2016
publisher: MIT OpenCourseWare
license: cc_by_nc_sa
category: slides_pptx_export
pages: 31

origin:
  type: url
  url: https://ocw.mit.edu/courses/6-0002-introduction-to-computational-thinking-and-data-science-fall-2016/0a353b26f1c6bd161b28b3f249aa05d1_MIT6_0002F16_lec1.pdf

local_copy:
  path: Z:\caches\corpus\pdf2md\ocw_mit_6_0002_lec1.pdf
  sha256: cf9ac01c099a3d3062493c692efbfd75554c16357c240f3b4b4e644537c6a345
  downloaded_at: 2026-05-10

sha256: cf9ac01c099a3d3062493c692efbfd75554c16357c240f3b4b4e644537c6a345
size_bytes: 624715
added_at: 2026-05-10

notes: |
  PowerPoint exportado como PDF. Esperado: round-trip 40-60% (similar
  ao caso IBM Quantum lesson 1, mas em CS clássico).
```

### acm_gambetta_qiskit_2018 — Gambetta QISKit ACM Webinar (pendente)

```yaml
id: acm_gambetta_qiskit_2018
title: 'QISKit: A Swiss Army Knife for Quantum Computation (ACM TechTalk)'
authors: [Jay Gambetta]
year: 2018
publisher: ACM Learning Center / IBM
license: acm_open_webinar  # ambíguo — slides IBM hospedados em ACM
category: slides_pptx_export

origin:
  type: url
  url: https://learning.acm.org/binaries/content/assets/leaning-center/webinar-slides/2018/jaygambetta_webinarslides_compressed-1.pdf
  alternates:
    - https://learning.acm.org/techtalks/qiskit

local_copy: null

sha256: null
size_bytes: null
added_at: 2026-05-10

notes: |
  WebFetch deu 403 (rate-limit ACM). Tentar com User-Agent de browser real
  ou download manual. **Atenção à licença**: slides são IBM hospedados em
  ACM — tratar como "uso educacional", não redistribuir o PDF binário.
  Pareamento direto com o caso histórico IBM Quantum lesson 1 (28.9%).
```

### ia_atkins_pure_mathematics_1874 — Pure Mathematics (Atkins, 1874)

```yaml
id: ia_atkins_pure_mathematics_1874
title: 'Pure mathematics, including arithmetic, algebra, geometry, and plane trigonometry'
authors: [Edward Atkins]
year: 1874
publisher: William Collins, Sons, & Company
license: public_domain
category: scanned_with_bad_ocr

origin:
  type: url
  url: https://archive.org/download/puremathematicsi00atkirich/puremathematicsi00atkirich.pdf
  alternates:
    - https://archive.org/details/puremathematicsi00atkirich

local_copy:
  path: Z:\caches\corpus\pdf2md\ia_atkins_pure_mathematics_1874.pdf
  sha256: 44f60228ef044c75cab8bba1632ebb308fe555c21e2228fb6431a5700af2e6b2
  downloaded_at: 2026-05-10

sha256: 44f60228ef044c75cab8bba1632ebb308fe555c21e2228fb6431a5700af2e6b2
size_bytes: 32280168
added_at: 2026-05-10

notes: |
  IA scan com text-layer OCR sob a imagem. Tipografia Victoriana
  (long-s, ligaturas) confunde Tesseract. Esperado: round-trip < 30%.
  Categoria diferente de `ia_mathematics00wils` (Wilson 1800 é image-only;
  Atkins tem text-layer OCR ruim — degradação distinta).
```

### ia_merriman_higher_mathematics_1898 — Higher Mathematics (Merriman, 1898) (pendente)

```yaml
id: ia_merriman_higher_mathematics_1898
title: 'Higher mathematics. A text-book for classical and engineering colleges'
authors: [Mansfield Merriman]
year: 1898
publisher: John Wiley & Sons
license: public_domain
category: scanned_with_bad_ocr

origin:
  type: url
  url: https://archive.org/download/merrimantextbook00merrrich/merrimantextbook00merrrich.pdf
  alternates:
    - https://archive.org/details/merrimantextbook00merrrich

local_copy: null

sha256: null
size_bytes: null
added_at: 2026-05-10

notes: |
  Redundante com Atkins (mesma categoria) — pendente download para v2 do
  corpus se quisermos comparar drift sistemático entre décadas diferentes
  de scan-com-OCR. Tamanho esperado: ~35 MB.
```

### pmc_woese_1965_genetic_code — Woese 1965 PNAS (pendente)

```yaml
id: pmc_woese_1965_genetic_code
title: 'On the Evolution of the Genetic Code'
authors: [Carl R. Woese]
year: 1965
publisher: National Academy of Sciences (PNAS)
license: public_domain  # PNAS pré-1978
category: scanned_image_only

origin:
  type: url
  url: https://pmc.ncbi.nlm.nih.gov/articles/PMC300511/
  alternates:
    - https://pmc.ncbi.nlm.nih.gov/articles/instance/300511/pdf/pnas00187-0078.pdf

local_copy: null

sha256: null
size_bytes: null
added_at: 2026-05-10

notes: |
  PMC bloqueia download automatizado (mesmo problema do pmc_10811782).
  Download manual via browser. Substitui parcialmente o gap bio_med +
  scanned_image_only ao mesmo tempo. Layout 2-coluna de revista
  científica mid-20th-c, "hot metal" typography.
```

### govinfo_fr_1985_08_30 — Federal Register 1985-08-30 (pendente)

```yaml
id: govinfo_fr_1985_08_30
title: 'Federal Register, Vol. 50, No. 169 (August 30, 1985)'
authors:
  source: U.S. Government Publishing Office
year: 1985
license: public_domain  # US Government Work, 17 USC § 105
category: scanned_with_bad_ocr

origin:
  type: url
  url: https://www.govinfo.gov/content/pkg/FR-1985-08-30/pdf/FR-1985-08-30.pdf
  alternates:
    - https://www.govinfo.gov/app/details/FR-1985-08-30

local_copy: null

sha256: null
size_bytes: null
added_at: 2026-05-10

notes: |
  Federal Register pré-1994 — scan retroativo da GPO, OCR posterior, 3
  colunas densas, regulamentos. Pendente porque > 10 MB; baixar via curl
  separado se precisar comparar com FR-1936 (born-digital).
```

### govinfo_fr_1936_07_09 — Federal Register 1936 Vol. I

```yaml
id: govinfo_fr_1936_07_09
title: 'Federal Register, Vol. 1, No. 84 (July 9, 1936)'
authors:
  source: U.S. Government Publishing Office
year: 1936
license: public_domain  # US Government Work, 17 USC § 105
category: gov_form
pages: 10

origin:
  type: url
  url: https://www.govinfo.gov/content/pkg/FR-1936-07-09/pdf/FR-1936-07-09.pdf

local_copy:
  path: Z:\caches\corpus\pdf2md\govinfo_fr_1936_07_09.pdf
  sha256: 71feac562d5565e813b1bffb3a8ef3418e666f46d1b0a79915de36f33306a9e7
  downloaded_at: 2026-05-10

sha256: 71feac562d5565e813b1bffb3a8ef3418e666f46d1b0a79915de36f33306a9e7
size_bytes: 1896025
added_at: 2026-05-10

notes: |
  Born-digital recente (digitalização da GPO produziu PDF nativo); fontes
  BookmanOldStyle embeded. Contraste com FR-1985-08-30 (scan puro com OCR).
  Tipografia anos 30 + densidade de citações cruzadas.
```

### cdc_mmwr_73_35_a1 — CDC MMWR (2024) — caso "limpo mas multi-col"

```yaml
id: cdc_mmwr_73_35_a1
title: 'E-Cigarette and Nicotine Pouch Use Among Middle and High School Students — United States, 2024'
authors:
  source: Centers for Disease Control and Prevention (CDC), MMWR
year: 2024
license: public_domain
category: multi_col_dense

origin:
  type: url
  url: https://www.cdc.gov/mmwr/volumes/73/wr/pdfs/mm7335a1-H.pdf
  alternates:
    - https://www.cdc.gov/mmwr/volumes/73/wr/mm7335a1.htm

local_copy:
  path: Z:\caches\corpus\pdf2md\cdc_mmwr_73_35_a1.pdf
  sha256: 95570c7dc7f6cf11f1789de207e67dc7bb559d6392db312a4d80430827b25c03
  downloaded_at: 2026-05-10

sha256: 95570c7dc7f6cf11f1789de207e67dc7bb559d6392db312a4d80430827b25c03
size_bytes: 270005
added_at: 2026-05-10

notes: |
  Caso "limpo mas multi-col" — valida que o pipeline não quebra em PDFs
  governamentais bem-feitos. Diferencia degradação por tipografia (Atkins,
  Wilson) vs por layout (este). Esperado: round-trip 70-85%.
```

### irs_f1040_2025 — IRS Form 1040 (2025)

```yaml
id: irs_f1040_2025
title: 'IRS Form 1040 — U.S. Individual Income Tax Return (2025)'
authors:
  source: Internal Revenue Service
year: 2025
license: public_domain  # US Government Work
category: gov_form

origin:
  type: url
  url: https://www.irs.gov/pub/irs-pdf/f1040.pdf
  alternates:
    - https://www.irs.gov/forms-pubs/about-form-1040

local_copy:
  path: Z:\caches\corpus\pdf2md\irs_f1040_2025.pdf
  sha256: 3d31c226df0d189ced80e039d01cf0f8820c1019681a0f0ca6264de277b7e982
  downloaded_at: 2026-05-10

sha256: 3d31c226df0d189ced80e039d01cf0f8820c1019681a0f0ca6264de277b7e982
size_bytes: 220237
added_at: 2026-05-10

notes: |
  AcroForm (form-fields PDF) + checkboxes + camadas sobrepostas. Conteúdo
  fragmentado em pequenas caixas. Esperado: round-trip < 50% — pipeline
  PDF→MD raramente lida bem com form-fields. IRS atualiza URL por ano
  fiscal; sha256 pode mudar quando 2026 for publicado.
```
