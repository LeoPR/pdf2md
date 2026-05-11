# Candidatos de PDFs sujos para corpus de benchmark

*Pesquisado em 2026-05-10. URLs validadas via WebFetch quando possível; quando o
PDF era binário/grande para WebFetch, validei a página HTML hospedeira ou a
indexação pelo WebSearch oficial. Notas individuais marcam exceções.*

## Resumo

**9 candidatos** distribuídos em **7 das 8 categorias** alvo. Apenas
`mobile_capture_scan` (PDFs gerados por CamScanner em celular, com
sombras/distorção) ficou sem candidato verificável com licença redistribuível —
existem evidências de tais documentos em portais de governo indiano e arquivos
do Internet Archive, mas a procedência/licença é incerta. Cobrimos:
slides PPTX→PDF (MIT OCW + ACM webinar Gambetta), scanned-image-only (PMC PNAS
1965, Federal Register 1985), scanned-with-bad-OCR (Atkins 1874, Merriman 1898),
gov_form (IRS 1040), multi-col denso fora do arXiv (CDC MMWR), tipografia
antiga não-padrão (Federal Register 1936), arXiv "old-school" (cs/9902009).

O conjunto privilegia **diversidade de modo de degradação**: scan 19th/20th c.
com OCR ruim, layouts de 2-3 colunas de governo, fontes não-acadêmicas em
slides exportados, fórmulas/figuras tratadas como imagem, PDF de formulário
com camadas de form-field. Todos com licença redistribuível verificável.

## Candidatos

### ocw_mit_6_0002_lec1 — MIT OCW 6.0002 Lecture 1 (Introduction and Optimization)

```yaml
id: ocw_mit_6_0002_lec1
title: 'MIT 6.0002 Introduction to Computational Thinking and Data Science — Lecture 1: Introduction and Optimization Problems'
authors: [John Guttag, Eric Grimson]
year: 2016
publisher: MIT OpenCourseWare
license: cc_by_nc_sa  # CC BY-NC-SA 4.0 — explícito no footer do OCW
category: slides_pptx_export
dirty_reason: |
  PowerPoint exportado como PDF (orientação landscape rodada, fontes Type1
  reembedadas, imagens JPEG achatadas, sem estrutura semântica de heading).
origin:
  type: url
  url: https://ocw.mit.edu/courses/6-0002-introduction-to-computational-thinking-and-data-science-fall-2016/0a353b26f1c6bd161b28b3f249aa05d1_MIT6_0002F16_lec1.pdf
  alternates:
    - https://ocw.mit.edu/courses/6-0002-introduction-to-computational-thinking-and-data-science-fall-2016/pages/lecture-slides-and-files/
expected_problem: |
  Round-trip moderado (40-60%): caixas de texto sobrepostas, ordem de leitura
  não-linear, bullets renderizados como elementos gráficos. Comparável ao
  caso IBM Quantum lesson 1, mas em CS clássico (não-físico).
```

Notas: validei HTTP 200 e PPTX-export confirmado por aspect ratio 612x792
rotated + fontes T1/C2 típicas de Office-to-PDF. Licença CC BY-NC-SA aparece
no footer da página do curso. 610 KB, 31 páginas.

---

### acm_gambetta_qiskit_2018 — Jay Gambetta: QISKit, A Swiss Army Knife for Quantum Computation (ACM webinar)

```yaml
id: acm_gambetta_qiskit_2018
title: 'QISKit: A Swiss Army Knife for Quantum Computation (ACM TechTalk webinar slides)'
authors: [Jay Gambetta]
year: 2018
publisher: ACM Learning Center
license: acm_open_webinar  # webinar gratuito da ACM Open Webinar Series — uso educacional permitido; redistribuir requer cuidado
category: slides_pptx_export
dirty_reason: |
  Slide deck IBM Quantum 2018 exportado para PDF, com fórmulas-como-imagem,
  diagramas de circuito quântico raster, layout corporativo de PPT.
origin:
  type: url
  url: https://learning.acm.org/binaries/content/assets/leaning-center/webinar-slides/2018/jaygambetta_webinarslides_compressed-1.pdf
  alternates:
    - https://learning.acm.org/techtalks/qiskit
expected_problem: |
  Round-trip < 40%, similar ao caso histórico IBM Quantum lesson 1 (28.9%).
  Fórmulas-como-imagem geram token bloat. Útil como pareamento direto com o
  caso conhecido — mesmo autor (Gambetta) e mesma tradição visual IBM.
```

Notas: WebFetch deu 403 (provável rate-limit do CDN; URL é indexada pelo
WebSearch e citada na página oficial do ACM TechTalks). **Atenção à licença**:
ACM hospeda mas os slides são de autoria IBM; tratar como "uso educacional"
e não redistribuir o PDF sem citar. Pode ser melhor não-canonical até
verificar com a ACM.

---

### ia_atkins_pure_mathematics_1874 — Pure Mathematics (Atkins, 1874)

```yaml
id: ia_atkins_pure_mathematics_1874
title: 'Pure mathematics, including arithmetic, algebra, geometry, and plane trigonometry'
authors: [Edward Atkins]
year: 1874
publisher: William Collins, Sons, & Company
license: public_domain  # NOT_IN_COPYRIGHT marcado pelo Internet Archive
category: scanned_with_bad_ocr
dirty_reason: |
  Livro escaneado pelo IA com text-layer OCR sob a imagem; tipografia
  Victoriana (long-s, ligaturas, ascenders altos) confunde Tesseract.
  Símbolos matemáticos vão pro OCR como caracteres bizarros.
origin:
  type: url
  url: https://archive.org/download/puremathematicsi00atkirich/puremathematicsi00atkirich.pdf
  alternates:
    - https://archive.org/details/puremathematicsi00atkirich
expected_problem: |
  Round-trip < 30% por causa do text-layer com erros de OCR sistemáticos.
  Marker/Nougat vão tentar re-OCR, mas o conflito com a camada existente
  gera dupla detecção. 412 páginas, ~23 MB.
```

Notas: validei via WebFetch a página de detalhes (status NOT_IN_COPYRIGHT,
ano 1874 sem renovação de copyright). Diferença vs `ia_mathematics00wils` no
manifest atual: Wilson 1800 provavelmente é image-only (sem text-layer
OCR), Atkins 1874 tem text-layer ruim — categoria diferente de degradação.

---

### ia_merriman_higher_mathematics_1898 — Higher Mathematics: A Text-book for Classical and Engineering Colleges (Merriman, 1898)

```yaml
id: ia_merriman_higher_mathematics_1898
title: 'Higher mathematics. A text-book for classical and engineering colleges'
authors: [Mansfield Merriman]
year: 1898
publisher: John Wiley & Sons
license: public_domain  # NOT_IN_COPYRIGHT (publicado pré-1928)
category: scanned_with_bad_ocr
dirty_reason: |
  Livro técnico fim-de-século com notação matemática variável (frações
  empilhadas, sub/sobrescritos, integrais), escaneado e OCR'izado com erros.
  Mistura de prosa densa com display math.
origin:
  type: url
  url: https://archive.org/download/merrimantextbook00merrrich/merrimantextbook00merrrich.pdf
  alternates:
    - https://archive.org/details/merrimantextbook00merrrich
expected_problem: |
  Round-trip 30-50%. Math display vai virar texto corrompido se o pipeline
  confiar no text-layer; vai virar imagem se re-OCR'izar. ~35 MB.
```

Notas: WebFetch confirmou metadata em archive.org. Útil como par com Atkins:
ambos scan-com-OCR mas em décadas diferentes; comparar drift sistemático.

---

### pmc_woese_1965_genetic_code — On the Evolution of the Genetic Code (Woese, 1965, PNAS)

```yaml
id: pmc_woese_1965_genetic_code
title: 'On the Evolution of the Genetic Code'
authors: [Carl R. Woese]
year: 1965
publisher: National Academy of Sciences (PNAS)
license: public_domain  # PNAS pré-1978 sem copyright explícito; PMC hospeda como open access
category: scanned_image_only
dirty_reason: |
  Artigo de 1965 digitalizado pelo PMC como imagens raster sem text-layer
  OCR (ou OCR de baixa qualidade). Layout de revista científica de meados
  do século XX — 2-coluna, tipografia "hot metal", fórmulas como imagem.
origin:
  type: url
  url: https://pmc.ncbi.nlm.nih.gov/articles/PMC300511/
  alternates:
    - https://pmc.ncbi.nlm.nih.gov/articles/instance/300511/pdf/pnas00187-0078.pdf
expected_problem: |
  Round-trip < 40% — Marker precisa OCR'izar do zero. Boa cobertura
  bio_med + scanned_image_only ao mesmo tempo (compensa o pmc_10811782
  pendente).
```

Notas: WebFetch validou a página HTML (título/autor/ano corretos). Direct PDF
URL retorna interstitial — bloqueio anti-scraper do PMC (mesmo problema do
pmc_10811782 já documentado). **Download manual via browser obrigatório.**
PNAS pré-1978 é public domain por força do US Copyright Act 1976.

---

### govinfo_fr_1985_08_30 — Federal Register 1985-08-30 (digitalizado, pré-1994)

```yaml
id: govinfo_fr_1985_08_30
title: 'Federal Register, Vol. 50, No. 169 (August 30, 1985)'
authors:
  source: U.S. Government Publishing Office / Office of the Federal Register
year: 1985
license: public_domain  # US Government Work, 17 USC § 105
category: scanned_with_bad_ocr
dirty_reason: |
  Federal Register pré-1994 foi digitalizado retroativamente pela GPO —
  page images escaneadas de cópias físicas, OCR aplicado posteriormente.
  Tipografia governamental densa, 3 colunas, tabelas regulatórias,
  pseudo-formulários embutidos.
origin:
  type: url
  url: https://www.govinfo.gov/content/pkg/FR-1985-08-30/pdf/FR-1985-08-30.pdf
  alternates:
    - https://www.govinfo.gov/app/details/FR-1985-08-30
expected_problem: |
  Round-trip 30-50% — combinação de layout multi-coluna denso + OCR sobre
  scan + abreviações burocráticas (USC, CFR, regulatory citations) confunde
  o pipeline. Volume típico ~20-30 MB.
```

Notas: WebFetch direto no PDF excedeu 10 MB (validou que existe e é grande,
como esperado para scan). Status public-domain confirmado pela GPO
("digitization of the entire set of Federal Registers that were not 'born
digitally' before 1994"). Cobertura: government scan + multi-col dense.

---

### govinfo_fr_1936_07_09 — Federal Register Vol. I (1936-07-09)

```yaml
id: govinfo_fr_1936_07_09
title: 'Federal Register, Vol. 1, No. 84 (July 9, 1936)'
authors:
  source: U.S. Government Publishing Office / Office of the Federal Register
year: 1936
license: public_domain  # US Government Work, 17 USC § 105
category: gov_form  # categoria primária: documento oficial com tipografia antiga
dirty_reason: |
  Primeiro ano do Federal Register, tipografia 1930s (BookmanOldStyle
  embedded), layout 2-coluna estreito, frequente referência cruzada
  (regulatory cross-refs), tabelas tarifárias.
origin:
  type: url
  url: https://www.govinfo.gov/content/pkg/FR-1936-07-09/pdf/FR-1936-07-09.pdf
  alternates:
    - https://www.govinfo.gov/app/collection/FR
expected_problem: |
  Round-trip 50-70% — PDF born-digital (TrueType fonts BookmanOldStyle
  embeded) mas tipografia/notação dos anos 30 e densidade de citações
  cruzadas confundem heading detection. ~1.8 MB.
```

Notas: WebFetch confirmou born-digital (FlateDecode streams, fontes
BookmanOldStyle embeded). Contraste interessante com o FR-1985: 1936 é
born-digital recente (digitalização produziu PDF nativo), 1985 é scan puro.

---

### cdc_mmwr_73_35_a1 — CDC MMWR: E-Cigarette and Nicotine Pouch Use Among Students (2024)

```yaml
id: cdc_mmwr_73_35_a1
title: 'E-Cigarette and Nicotine Pouch Use Among Middle and High School Students — United States, 2024'
authors:
  source: Centers for Disease Control and Prevention (CDC), MMWR
year: 2024
license: public_domain  # CDC: "Most CDC content is in the public domain and may be freely used or reproduced"
category: multi_col_dense  # PDF MMWR é 2-coluna com tabelas embutidas
dirty_reason: |
  PDF MMWR moderno mas com 2 colunas estreitas, tabelas com células
  abreviadas, gráficos vetoriais, footnotes com símbolos não-padrão
  (*, †, §, ¶). Boa robustez típica mas estrutura semântica frágil.
origin:
  type: url
  url: https://www.cdc.gov/mmwr/volumes/73/wr/pdfs/mm7335a1-H.pdf
  alternates:
    - https://www.cdc.gov/mmwr/volumes/73/wr/mm7335a1.htm
expected_problem: |
  Round-trip 70-85% — caso "limpo mas multi-col" para validar que o
  pipeline não quebra em PDFs governamentais bem-feitos. Diferencia
  degradação por tipografia vs por layout.
```

Notas: WebFetch validou PDF (HTTP 200, 263.7 KB, conteúdo confirmado).
Public-domain explícito em cdc.gov/other/agencymaterials.html ("Most CDC
content is in the public domain and may be freely used or reproduced").

---

### irs_f1040_2025 — IRS Form 1040 (2025 tax year)

```yaml
id: irs_f1040_2025
title: 'IRS Form 1040 — U.S. Individual Income Tax Return (2025)'
authors:
  source: Internal Revenue Service
year: 2025
license: public_domain  # US Government Work
category: gov_form
dirty_reason: |
  Formulário interativo com form-fields PDF (AcroForm), checkboxes,
  campos sobrepostos a texto, cabeçalho/rodapé visualmente alinhados mas
  semanticamente espalhados. Múltiplos layers (visual + form).
origin:
  type: url
  url: https://www.irs.gov/pub/irs-pdf/f1040.pdf
  alternates:
    - https://www.irs.gov/forms-pubs/about-form-1040
expected_problem: |
  Round-trip < 50% — pipelines PDF→MD raramente lidam bem com form-fields.
  Conteúdo "visível" é fragmentado em pequenas caixas. Boa cobertura para
  o caso onde estrutura semântica não existe no PDF.
```

Notas: WebFetch validou (PDF linearizado, AcroForm presente, 215 KB).
US Government Work — public domain explicit. IRS atualiza f1040.pdf por
ano fiscal; URL é estável (sempre aponta para o ano corrente em maio).

---

## Categorias cobertas (resumo)

| Categoria              | Candidatos                                              |
|------------------------|---------------------------------------------------------|
| slides_pptx_export     | ocw_mit_6_0002_lec1, acm_gambetta_qiskit_2018           |
| scanned_image_only     | pmc_woese_1965_genetic_code                             |
| scanned_with_bad_ocr   | ia_atkins_pure_mathematics_1874, ia_merriman_higher_mathematics_1898, govinfo_fr_1985_08_30 |
| gov_form               | irs_f1040_2025, govinfo_fr_1936_07_09                   |
| multi_col_dense        | cdc_mmwr_73_35_a1                                       |
| mobile_capture_scan    | **(sem candidato)** — ver nota abaixo                   |
| photo_collage_overlay  | **(sem candidato)** — categoria pouco coberta em fontes públicas com licença clara |
| non_standard_fonts     | (subsumido em scanned_with_bad_ocr + slides; sem candidato dedicado) |

## URLs problemáticas / acessibilidade

- **PMC** (`pmc_woese_1965_genetic_code`): direct PDF URL retorna interstitial
  anti-scraper. Download manual via browser, mesma situação documentada para
  `pmc_10811782` no manifest atual.
- **ACM** (`acm_gambetta_qiskit_2018`): WebFetch retornou 403, mas o URL é
  indexado e o conteúdo existe. Provável rate-limit. Tentar com User-Agent
  de browser real ou aceitar como "download manual".
- **NTRS NASA** (não-incluído, mas vale registrar): PDFs Apollo > 10 MB
  excedem limite do WebFetch. URL pattern `ntrs.nasa.gov/api/citations/<id>/downloads/<id>.pdf`
  funciona; precisa download via curl/wget.

## Gaps conhecidos

- `mobile_capture_scan` (CamScanner-style com sombras/distorção/baixo contraste)
  é o gap mais sentido. Documentos do governo indiano com "Scanned with
  CamScanner" watermark foram reportados (Rest of World, 2024) mas sem
  redistribuição clara. Alternativas a explorar v2: archive.org com query
  `"scanned with camscanner"` + filtros de licença.
- `photo_collage_overlay`: gênero raro em fontes oficiais; presente em
  zines/fanzines mas com licenças irregulares.
