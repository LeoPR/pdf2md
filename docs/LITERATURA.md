# Literatura — conversão PDF → texto/MD (v1)

> **Compilado histórico (snapshot 2026-05-10).** Para consulta atualizada, ver [`biblioteca/`](biblioteca/INDEX.md) — fichas catalográficas por tema (ferramentas, benchmarks, métricas, papers, glossário). Conflitos entre este v1 e v2 estão resolvidos nas fichas, com nota explícita em cada entrada afetada (especialmente CDM, rebaixada em v2).

*Compilado em 2026-05-10 para informar T031 (definição de métricas) e T040/T050 (corpus e baseline).*

> **Atualização**: ver também [`LITERATURA_v2.md`](LITERATURA_v2.md) (2026-05-10+) com:
> - Cobertura do padrão de alucinação detectado em `lab/e03_atkins_wilson_scan/` (validado por T071) — **parece ser contribuição original**
> - Atualizações de ferramentas (MinerU2.5-Pro abr/2026 95.69 OmniDocBench v1.6; Granite-Docling-258M set/2025; olmOCR-2 out/2025; DeepSeek-OCR, dots.ocr, PaddleOCR-VL, GLM-OCR — todos novos)
> - **CDM rebaixada** — LLM-as-judge (r=0.78) correlaciona ~2× melhor que CDM (r=0.34) em fórmulas ([Horn & Keuper dez/25, arXiv 2512.09874](https://arxiv.org/abs/2512.09874))
> - AcroForm via pypdf `get_fields()` — workaround para caso IRS f1040 (round-trip 46%)
> - Backlog Q11–Q17 (próximos experimentos sugeridos)

Este documento situa o `pdf2md` (marker-pdf + pandoc + Chrome/KaTeX, round-trip 95.1% no Nielsen & Chuang cap. 4) frente ao estado-da-arte de 2024–2026. Foca em conversão de livros e papers acadêmicos com matemática densa — o caso de uso de pesquisa em computação quântica.

---

## 1. Métricas estabelecidas

### 1.1 WER / CER (Word / Character Error Rate)

WER = (S + D + I) / N, onde S, D, I são substituições, deleções e inserções de palavras necessárias para transformar a hipótese no ground truth, e N é o número de palavras na referência. CER é análogo no nível de caractere. Ambas derivam da distância de Levenshtein.

**Origem.** Métrica clássica de speech recognition (avaliações DARPA dos anos 90), portada para OCR — a [especificação OCR-D](https://ocr-d.de/en/spec/ocrd_eval.html) e a literatura clássica sobre Levenshtein documentam que "a maioria das métricas de qualidade OCR baseia-se em distância de Levenshtein".

**Adequação ao MD.** Útil para fluxos de prosa pura, mas tem três limitações severas no nosso caso:

1. WER não distingue palavras de conteúdo (semântica) de tokens de marcação (`**`, `#`, `\frac`). Inserir um `**` em volta de uma palavra dispara substituição em vez de "boa formatação".
2. Reading order: WER é altamente sensível à ordem; um modelo que extraiu o texto correto mas em ordem errada (multi-coluna, callouts) recebe WER catastrófico. Existem variantes order-independent — e.g. *Bag of Words WER* e *Flexible Character Accuracy* ([Reading order metrics, arXiv 2404.18664](https://arxiv.org/html/2404.18664v1)).
3. Fórmulas: tokenizar `\frac{a}{b}` por palavra é absurdo. WER ignora estrutura matemática.

**Recomendação.** Usar CER/WER apenas no corpo de prosa após **mascarar** fórmulas, tabelas e código. Reportar separadamente "WER prosa" e "WER após desmarcadores" para diagnosticar drift de marcação vs. drift textual.

### 1.2 TEDS (Tree-Edit-Distance Similarity)

TEDS(T₁, T₂) = 1 − EditDistance(T₁, T₂) / max(|T₁|, |T₂|), onde T₁, T₂ são árvores HTML (estrutura + conteúdo de células) e |T| é o número de nós.

**Origem.** Zhong, ShafieiBavani & Yepes, *Image-based table recognition: data, model, and evaluation*, [arXiv 1911.10683](https://arxiv.org/abs/1911.10683) (ECCV 2020). Introduzido junto com PubTabNet. Variantes: **TEDS-S** (apenas estrutura, ignora texto) e **TEDS-content** (estrutura + conteúdo).

**Adequação.** É o padrão de fato para tabelas; OmniDocBench (CVPR 2025) e os papers de Marker, Docling e MinerU reportam TEDS. Granite-Docling reporta TEDS-S 0.97 no FinTabNet — número de referência prático.

**Limitação.** Nosso pipeline produz Markdown (GFM tables), não HTML. Vamos precisar normalizar MD → HTML (pandoc consegue) antes de aplicar TEDS. Isso introduz ruído quando MD não suporta merged cells / multirow. Para tabelas complexas em livros (Nielsen-Chuang tem várias com células agrupadas) considerar reportar TEDS sobre HTML diretamente, ou usar a variação **GriTS** (cell-grid F1).

### 1.3 BLEU sobre LaTeX (e por que não basta)

BLEU calcula precisão de n-gramas entre LaTeX predito e ground-truth. Foi a métrica padrão para image-to-LaTeX (Deng et al. 2017, e dataset CROHME).

**Limitação documentada.** Wang et al., *Image Over Text: Transforming Formula Recognition Evaluation with Character Detection Matching* ([arXiv 2409.03643](https://arxiv.org/abs/2409.03643), CVPR 2025) mostra que: (i) a mesma fórmula tem múltiplas representações LaTeX equivalentes (`\frac{a}{b}` vs `\dfrac{a}{b}`), penalizadas como divergentes; (ii) erros numéricos críticos ("1" → "7") podem receber BLEU alto; (iii) BLEU recompensa estilo de tokenização similar ao do treino. Conclusão dos autores: BLEU correlaciona mal com julgamento humano em fórmulas.

**Alternativas:**

- **CDM (Character Detection Matching)** — renderiza ambas as fórmulas em imagem, faz matching visual de caracteres com bounding boxes via grafo bipartido, calcula F1. 96% de concordância com humanos vs. ~64% para BLEU. [Código](https://github.com/opendatalab/UniMERNet/tree/main/cdm).
- **TeXBLEU** ([arXiv 2409.06639](https://arxiv.org/html/2409.06639v2)) — adapta BLEU com tokenizer de LaTeX e embeddings de tokens. Melhora correlação mas ainda no nível textual.
- **Exact match após canonicalização** — passa ambas LaTeX por um normalizador (e.g. `latex-cleaner`), compara strings. Métrica binária e severa, mas útil como "precisão de fórmula".

### 1.4 Métricas de fórmula complementares

Para o pdf2md, sugerimos um painel multi-métrica:

| Métrica | O que mede | Robusta a |
|---|---|---|
| Count diff | `# fórmulas predita − # GT` por página | -- |
| Exact match (canonicalizado) | string-equal após `\frac→\dfrac` etc. | trivial |
| AST distance (KaTeX/MathJax AST) | edit distance sobre árvore parseada | reordenamento |
| CDM (render + match visual) | similaridade visual da fórmula renderizada | reescritas equivalentes |
| Compile-OK rate | % de fórmulas que compilam sem erro | hallucination |

A combinação **count diff + compile-OK + CDM** detecta os três modos de falha mais relevantes: dropped formulas, fórmula corrompida, e fórmula visualmente errada.

### 1.5 Citation matching

Métrica padrão herdada da literatura de bibliographic extraction: **F1** sobre referências, com matching variando de strict, soft (substring), Levenshtein-based e Ratcliff-Obershelp. GROBID reporta F1 0.87–0.90 em corpora PMC e bioRxiv (ver [GROBID benchmarks](https://grobid.readthedocs.io/en/latest/benchmarks/Benchmarking-biorxiv/)). O paper de Tkaczyk et al., *Machine Learning vs. Rules and Out-of-the-Box vs. Retrained* ([arXiv 1802.01168](https://arxiv.org/pdf/1802.01168)), formaliza o protocolo.

**No nosso caso** as referências de livros (Nielsen-Chuang, Preskill) variam em estilo (numéricas, autor-ano, footnote-style). Sugestão: para cada referência da bibliografia, computar match contra GT por (i) DOI/arXiv-id se presente, (ii) Levenshtein normalizado sobre `(autor + ano + título)`, threshold 0.85.

### 1.6 Hierarchy / headers preservation

Não há métrica padronizada única; trabalhos recentes reportam **Tree edit distance sobre o ToC** ou **Levenshtein sobre a sequência linearizada de headers** (Marker e Docling fazem o segundo). Considerar reportar:

- Header recall: % de headers do GT presentes no predito.
- Header level accuracy: dado que o header foi achado, qual a % com `#` correto (1, 2, 3...).
- Section sequence Kendall-τ: ordem dos headers.

### 1.7 Image preservation

Métrica raramente reportada de forma padronizada. Sugestão pragmática:

- Image count diff por página.
- Caption matching (Levenshtein normalizado contra GT).
- Para cada imagem extraída, verificar se há tag/path no MD e se o arquivo existe em disco. Não tentar comparar pixels — extração já preserva bytes; o que falha é a *associação* texto–imagem e a *legenda*.

---

## 2. Benchmarks públicos

| Benchmark | Escopo | Tamanho | Licença | Adequação ao pdf2md |
|---|---|---|---|---|
| **OmniDocBench** ([CVPR 2025](https://github.com/opendatalab/OmniDocBench)) | 9 tipos de documento (academic, textbook, slides, financial, news, handwriting...), zh+en, anotação end-to-end (text, table, formula, layout, reading order) | 1.355 páginas, ~20k blocos, ~80k spans | Permissive (research) | **Alta**. Inclui textbooks com matemática. SOTA atual: MinerU 2.5 ~90.67. Inclui anotações HTML+LaTeX para tabelas. |
| **DocLayNet** ([KDD 2022](https://arxiv.org/abs/2206.01062)) | Layout COCO, 11 classes, multi-domínio | 80.863 páginas anotadas | CDLA-Permissive 1.0 | Média. É de layout-only, sem texto/fórmula GT. Útil só para sub-task layout. |
| **DocBank** ([COLING 2020](https://github.com/doc-analysis/DocBank)) | arXiv, 12 classes semânticas, weak supervision via LaTeX | 500k páginas | Apache 2.0 | Média-alta. Paper-style apenas, não livros. Boa para baseline mas pouco diverso. |
| **PubLayNet** | Layout, PMC | 360k páginas | CDLA-Permissive 1.0 | Baixa. Biomedical-only, layouts conservadores; nada de matemática densa. |
| **PubTabNet** | Tabelas + HTML, PMC | 568k tabelas | CDLA-Permissive 1.0 | Alta para sub-task tabelas. Não cobre tabelas científicas com matemática (raras em PMC). |
| **SciTSR** ([arXiv 1908.04729](https://arxiv.org/abs/1908.04729)) | Tabelas científicas, anotação a partir de fonte LaTeX | 15k tabelas (12k train / 3k test); SciTSR-COMP com 716 tabelas complexas | MIT | Alta para tabelas em papers de math/CS. Boa complementação a PubTabNet. |
| **DocILE** ([ICDAR 2023](https://arxiv.org/abs/2302.05658)) | Faturas, ordens — KILE/LIR | 6.7k anotadas + 100k sintéticas + ~1M unlabeled | CC BY-NC-SA | **Inadequada**. Business documents, não scientific. |
| **olmOCR-Bench** ([Ai2 2025](https://olmocr.allenai.org/)) | OCR end-to-end com unit tests por documento | 7.000+ test cases / 1.400 docs | ODC-By | Alta, especialmente para English print + scans. Avalia presença/ausência de fatos via testes em vez de string-match. |
| **Marker bench** | Heurística interna ([repo](https://github.com/datalab-to/marker/tree/master/benchmarks)) | ~ centenas de PDFs | Repo GPL-3.0 | Útil como referência, mas a heurística é proprietária e pondera arbitrariamente. |
| **Nougat eval** ([arXiv 2308.13418](https://arxiv.org/abs/2308.13418)) | arXiv + PMC, em-line markup (Mathpix Markdown-compatible) | Eval set é arXiv split | CC BY-NC | Boa para math papers, mas restrito ao domínio arXiv. |

**Recomendações para o lab.**

- Para baseline reprodutível: **OmniDocBench** (matched aos nossos casos: textbook + math + tabela). Disponível em GitHub, métricas via `omnidocbench` CLI.
- Para math papers em particular: alguns subsets do **Nougat eval** + um subset interno do nosso corpus (Nielsen-Chuang, Preskill notes, papers de QC).
- **Não usar DocILE/PubLayNet** — fora de domínio.
- Construir um *mini-corpus interno* de 20–30 páginas com GT manual em MD canônico (T040). É o único caminho para medir *nosso* problema (livros densos em math).

---

## 3. Ferramentas comparáveis ao marker-pdf

| Ferramenta | Paper | GitHub | Licença | GPU? | Strengths para QC | Weaknesses |
|---|---|---|---|---|---|---|
| **Marker** (Datalab) | sem paper formal; benchmarks no [repo](https://github.com/datalab-to/marker/tree/master/benchmarks) | [datalab-to/marker](https://github.com/datalab-to/marker) | GPL-3.0; pesos sob AI Pubs Open Rail-M (free p/ research) | Recomendada | Pipeline modular (Surya OCR + layout + table + equation), `--use_llm` opcional, throughput alto, math em LaTeX | Sem paper revisado; modelo de heading drift em livros longos |
| **Nougat** (Meta AI 2023) | Blecher et al., [arXiv 2308.13418](https://arxiv.org/abs/2308.13418) | [facebookresearch/nougat](https://github.com/facebookresearch/nougat) | CC BY-NC 4.0 | Sim | Foi *o primeiro* end-to-end PDF→markup p/ math, treinado em arXiv+PMC, output Mathpix-compatible | Hallucination conhecida em páginas fora-do-domínio; ~10× mais lento que Marker; manutenção parou (último release 2023) |
| **MinerU 2.5** (Shanghai AI Lab) | Wang et al. 2025 ([repo + technical report](https://github.com/opendatalab/MinerU)) | [opendatalab/MinerU](https://github.com/opendatalab/MinerU) | AGPL-3.0 | Sim (1.2B VLM); CPU possível com pipeline backend | SOTA atual em OmniDocBench (~90.67), excepcional em CJK, suporte a tabelas truncadas, gráficos | AGPL pode ser problemático para integração; modelo grande |
| **olmOCR / olmOCR-2** (Ai2 2025) | [Ai2 blog + paper](https://olmocr.allenai.org/) | [allenai/olmocr](https://github.com/allenai/olmocr) | Apache 2.0 | Recomendada (Qwen2.5-VL-7B base) | Custo absurdamente baixo ($190/M páginas), reading order excelente em multi-coluna e callouts, ELO >1800 | Foco em English print, suporte a math LaTeX inferior a Nougat/Marker em papers densos |
| **Docling** (IBM Research) | Auer et al., *Docling: An Efficient Open-Source Toolkit*, [arXiv 2501.17887](https://arxiv.org/html/2501.17887v1) (AAAI 2025); Granite-Docling ([IBM](https://www.ibm.com/new/announcements/granite-docling-end-to-end-document-conversion)) | [docling-project/docling](https://github.com/docling-project/docling) | MIT | CPU OK; GPU acelera | TEDS 0.97 em FinTabNet; integração nativa com LangChain/LlamaIndex; suporte multi-formato (PDF, DOCX, PPTX, EPUB) | Math menos polido que Nougat/Marker; otimizado para corporate docs |
| **GROBID** (Lopez 2008–) | Lopez 2009 + manutenção contínua | [kermitt2/grobid](https://github.com/kermitt2/grobid) | Apache 2.0 | Não (CRF + opcional Deep Learning add-on) | F1 ~0.89 em referências; padrão de facto para metadata e bibliografia em scholarly | Não emite Markdown; saída TEI/XML; quase nada de math |
| **pix2tex / LaTeX-OCR** (Blecher 2022) | sem paper formal | [lukas-blecher/LaTeX-OCR](https://github.com/lukas-blecher/LaTeX-OCR) | MIT | Recomendada (ViT) | Excelente formula-only OCR via image crop; útil como segundo opinion p/ fórmulas que Marker errar | Single-formula apenas; precisa pipeline de detecção upstream |
| **Surya** (Datalab) | sem paper; é o backend do Marker | [datalab-to/surya](https://github.com/datalab-to/surya) | GPL-3.0 | Recomendada | OCR + layout + reading order + tables em 90+ línguas; `surya_latex_ocr` substitui Texify | Mesmo lock-in de licença que Marker |
| **Mathpix** (comercial) | n/a | n/a | Proprietária | Cloud | Reconhecidamente uma das melhores em math; baseline comercial | Custo, lock-in, não open. Útil só como ceiling reference. |

**Para o pdf2md** (foco em livros/papers de QC com matemática densa) os candidatos a *baseline experiment* (T050) são:

1. **Marker** (atual): mantemos como controle.
2. **Nougat**: comparar especificamente em fórmulas longas (Trotter expansions, projetores) onde Marker faz drift.
3. **MinerU 2.5**: validar se o salto em OmniDocBench se traduz no nosso domínio.
4. **olmOCR-2**: estresse-teste em scans de livros antigos (Sakurai, Cohen-Tannoudji).
5. **Docling**: comparativo em tabelas complexas e como pipeline mais "MIT-licensed friendly".

---

## 4. Round-trip como técnica de validação

**Achados.**

- **Pandoc** mantém uma suíte de testes round-trip *intra-formato* (`md → AST → md`), e a documentação oficial e o [Wiki sobre round-trip format conversion](https://en.wikipedia.org/wiki/Round-trip_format_conversion) reconhecem que conversão lossless cross-format é, em geral, impossível: "a roundtrip (legacy → XML → legacy′) should result in effectively identical documents" é um *desejável*, não um teorema.
- **Round-trip translation (RTT)** como métrica de qualidade para MT foi avaliada e desencorajada como métrica direta (Aiken & Park 2010, Moon et al. 2020 [ACL](https://aclanthology.org/2020.eamt-1.11.pdf)) — BLEU(input, RTT) correlaciona pobremente com qualidade real, embora seja recuperável quando combinada com métricas semânticas (Zhuo et al. [arXiv 2209.07351](https://arxiv.org/abs/2209.07351)).
- **Round-trip correctness em código** (Allamanis et al., [arXiv 2402.08699](https://arxiv.org/abs/2402.08699), 2024) é a aplicação mais próxima do que fazemos: descrever código em NL e re-sintetizar, checar equivalência semântica. Os autores mostram que RTC correlaciona bem com qualidade de modelos de código *quando há um verificador semântico downstream*.
- **Aplicação a PDF→MD especificamente**: não encontramos literatura formal usando MD → PDF → MD' como métrica. É uma abordagem que aparece em CI de Pandoc e em testes de integração de Quarto, mas não como técnica de avaliação publicada.

**Limitações da abordagem para o pdf2md.**

1. **Erros silenciosos por simetria**: se `f` (PDF→MD) e `g` (MD→PDF) cometem o mesmo viés (e.g. ambos preferem `\frac` em vez de `\dfrac`), o round-trip é estável mas inconsistente com GT externo. Drift de 0.86%/iter é forte indício de estabilidade, mas não de fidelidade absoluta.
2. **Concentração de erros**: round-trip de 95.1% diz pouco sobre *onde* falham os 4.9%. Se concentrar em fórmulas críticas ou em tabelas, o efeito downstream (RAG, citação) é grande mesmo com score alto.
3. **A métrica round-trip mistura erros do reconstrutor (Pandoc+Chrome+KaTeX) com erros do extrator (Marker)**. Round-trip é uma soma — para isolar, precisamos de uma referência humana em MD canônico (T040).

**Recomendação.** Manter round-trip como *health check* contínuo (regressão de pipeline) e *complemento* — não como métrica primária. Métrica primária deve ser comparação contra GT humano em corpus pequeno (5–10 páginas curadas), com painel TEDS + CDM + WER-prosa + count-diff.

---

## 5. Reconstrutores MD → PDF

Comparação dos engines candidatos para "fechar o ciclo":

| Engine | Math | Tipografia | Dependências | Velocidade | Para nosso uso |
|---|---|---|---|---|---|
| **Pandoc + Chrome headless + KaTeX** (atual) | Boa (KaTeX é subset do LaTeX, suficiente para 99% do que aparece em livros de QC) | HTML/CSS — fontes não-LaTeX | Node, Chromium, Pandoc | Rápida | Está funcionando (95.1%); robusto; output não tem "look" de LaTeX, mas é fiel. |
| **Pandoc + LaTeX (pdflatex/lualatex)** | Excelente | Excelente (típica de papers) | TeX Live (~5GB) | Lenta | Maior fidelidade para math/typografia; falha em pacotes não-canônicos; debugging chato. |
| **Pandoc + Tectonic** | Excelente (mesmo backend XeTeX) | Excelente | Single-binary, ~50MB, fontes baixadas on-demand | Média | Boa alternativa ao TeX Live "completo" — Rust, reproducible builds. Recomendado se decidirmos sair do round-trip via HTML. [Repo](https://github.com/tectonic-typesetting/tectonic). |
| **Pandoc + Typst** | Adequada (Typst tem math nativo, mas é newer; alguns construtos LaTeX exóticos não traduzem 1:1) | Muito boa | Single-binary Rust | Muito rápida | Promissor, mas a literatura aponta que conversão LaTeX→Typst de math ainda é imperfeita ([Quarto issue 11368](https://github.com/orgs/quarto-dev/discussions/11368)). |
| **Quarto** (Pandoc + Typst/LaTeX) | Idem Pandoc | Templates polidos | Pandoc + (Typst ou TeX) | Idem | Nada que Pandoc puro não faça; útil se quisermos templates científicos. |
| **WeasyPrint** | Limitada (precisa MathML pré-renderizado; KaTeX server-side OK) | Boa para web-style | Python | Média | Sem GPU/Chrome necessário. Saída visualmente diferente; útil se Chrome headless for problema em CI. |

**Tradeoffs para o nosso pipeline:**

- **Atual (Pandoc + Chrome + KaTeX)**: barato em dependências, paralelizável, 95.1% no QCQI cap.4. Risco: KaTeX não suporta 100% do AMS; se um livro usar `\xymatrix` ou `tikz`, falha.
- **Migrar para Tectonic**: custo zero de qualidade, ganha auditabilidade e remove Chrome do CI. Vale T0XX como experimento isolado.
- **Typst**: monitorar; ainda imaturo para math intenso em 2026.

A *fidelidade tipográfica idêntica* ao PDF original não é prioridade pelo enunciado do projeto (prioridade 4). Logo, qualquer engine que renderize math corretamente serve.

---

## 6. Questões abertas (backlog para `lab/`)

Itens que demandam experimento real para responder, em ordem de impacto:

1. **Q1 — Round-trip vs GT humano.** Em 5 páginas curadas com GT manual em MD canônico, qual o gap entre `WER(roundtrip)` e `WER(GT)`? Se gap < 1pp, round-trip é proxy aceitável; se gap > 5pp, round-trip está enganando. *(Necessário T040 + T050.)*
2. **Q2 — Marker vs Nougat vs MinerU 2.5 em formulae longas.** Nielsen-Chuang cap. 8–10 (master equation, error correction) tem fórmulas multi-linha. Comparar count-diff + CDM. Hipótese: Nougat empata Marker em arXiv mas perde em livro; MinerU pode liderar pela escala recente.
3. **Q3 — Métrica de fórmula que correlaciona melhor com utilidade.** CDM dá número bonito; o que importa para um pesquisador é "pode citar com confiança". Definir um proxy operacional: % de fórmulas onde MD → PDF render visualmente igual ao PDF original (ground truth visual, não LaTeX-string).
4. **Q4 — Heading drift em livros longos.** Em PDFs de 400+ páginas, marker-pdf às vezes promove `subsubsection` para `section`. Quantificar via *header level accuracy* + Kendall-τ na sequência. Comparar contra MinerU.
5. **Q5 — Tabelas com células agrupadas.** GFM markdown não suporta `colspan`/`rowspan`. Quantificar perda em SciTSR-COMP convertendo via MD vs HTML embebido. Decidir se o fallback do pipeline deve emitir HTML inline para tabelas complexas.
6. **Q6 — Imagens com legenda semântica.** Métrica simples: % de figuras onde caption + label + cross-reference do texto preservam a tripla. Hipótese: Marker preserva ~80%, mas perde cross-references do tipo "see Fig. 4.2".
7. **Q7 — Sensibilidade de DPI / resolução de input.** Páginas escaneadas vs nativas-digitais: o pipeline degrada como? (Para o caso de livros antigos digitalizados.)
8. **Q8 — Reconstrutor: Tectonic substitui Chrome+KaTeX sem regressão?** Round-trip score com cada engine, mesmo corpus. Se Tectonic ≥ Chrome+KaTeX, simplificar a stack.
9. **Q9 — Citações.** Avaliar se a passada do pipeline preserva a tripla `(callout, ref, target)`. Matchear com GROBID como segundo-opinion em modo Apache-2.0.
10. **Q10 — Reading order em layouts não-triviais.** Páginas com sidebar/callouts (typical em Cohen-Tannoudji) — usar Bag-of-Words WER + Spearman footrule para isolar erro de ordem do erro de extração.

---

## Referências

### Métricas

- Zhong, X., ShafieiBavani, E., Yepes, A.J. *Image-based table recognition: data, model, and evaluation*. ECCV 2020. [arXiv 1911.10683](https://arxiv.org/abs/1911.10683). — TEDS, PubTabNet.
- Wang, B. et al. *Image Over Text: Transforming Formula Recognition Evaluation with Character Detection Matching*. CVPR 2025. [arXiv 2409.03643](https://arxiv.org/abs/2409.03643). — CDM.
- *TeXBLEU: Automatic Metric for Evaluate LaTeX Format*. [arXiv 2409.06639](https://arxiv.org/html/2409.06639v2).
- *Reading Order Independent Metrics for Information Extraction in Handwritten Documents*. [arXiv 2404.18664](https://arxiv.org/html/2404.18664v1).
- OCR-D community. *Quality Assurance specification* — CER/WER/FCA. [ocr-d.de](https://ocr-d.de/en/spec/ocrd_eval.html).
- Tkaczyk, D. et al. *Machine Learning vs. Rules and Out-of-the-Box vs. Retrained: An Evaluation of Open Source Bibliographic Reference Parsers*. [arXiv 1802.01168](https://arxiv.org/pdf/1802.01168).

### Benchmarks

- Ouyang, L. et al. *OmniDocBench: Benchmarking Diverse PDF Document Parsing with Comprehensive Annotations*. CVPR 2025. [arXiv 2412.07626](https://arxiv.org/abs/2412.07626) · [Repo](https://github.com/opendatalab/OmniDocBench).
- Pfitzmann, B. et al. *DocLayNet*. KDD 2022. [arXiv 2206.01062](https://arxiv.org/abs/2206.01062).
- Li, M. et al. *DocBank*. COLING 2020. [Repo](https://github.com/doc-analysis/DocBank).
- Chi, Z. et al. *Complicated Table Structure Recognition* (SciTSR). [arXiv 1908.04729](https://arxiv.org/abs/1908.04729).
- Šimsa, Š. et al. *DocILE*. ICDAR 2023. [arXiv 2302.05658](https://arxiv.org/abs/2302.05658).
- olmOCR-Bench. [olmocr.allenai.org](https://olmocr.allenai.org/).

### Ferramentas

- **Marker**: [datalab-to/marker](https://github.com/datalab-to/marker) — Vik Paruchuri, Datalab. GPL-3.0 + AI Pubs Open Rail-M. Sem paper formal.
- **Surya**: [datalab-to/surya](https://github.com/datalab-to/surya) — backend do Marker.
- **Nougat**: Blecher, L. et al. *Nougat: Neural Optical Understanding for Academic Documents*. [arXiv 2308.13418](https://arxiv.org/abs/2308.13418) · [Repo](https://github.com/facebookresearch/nougat).
- **MinerU 2.5**: [opendatalab/MinerU](https://github.com/opendatalab/MinerU) · Shanghai AI Lab · AGPL-3.0.
- **olmOCR / olmOCR-2**: Poznanski et al. *olmOCR: Unlocking Trillions of Tokens in PDFs with Vision Language Models*. Ai2 2025. [Paper](https://olmocr.allenai.org/papers/olmocr.pdf) · [Repo](https://github.com/allenai/olmocr).
- **Docling**: Auer, C. et al. *Docling: An Efficient Open-Source Toolkit for AI-driven Document Conversion*. AAAI 2025. [arXiv 2501.17887](https://arxiv.org/html/2501.17887v1) · [Repo](https://github.com/docling-project/docling).
- **GROBID**: Lopez, P. *GROBID: Combining Automatic Bibliographic Data Recognition and Term Extraction for Scholarship Publications*. ECDL 2009. [Repo](https://github.com/kermitt2/grobid) · [Docs](https://grobid.readthedocs.io/).
- **pix2tex / LaTeX-OCR**: [lukas-blecher/LaTeX-OCR](https://github.com/lukas-blecher/LaTeX-OCR).

### Round-trip / reconstrutores

- *Round-trip format conversion* (Wikipedia, conceito geral). [link](https://en.wikipedia.org/wiki/Round-trip_format_conversion).
- Allamanis, M. et al. *Unsupervised Evaluation of Code LLMs with Round-Trip Correctness*. [arXiv 2402.08699](https://arxiv.org/abs/2402.08699).
- Moon, J. et al. *Revisiting Round-Trip Translation for Quality Estimation*. EAMT 2020. [PDF](https://aclanthology.org/2020.eamt-1.11.pdf).
- **Pandoc**: [pandoc.org](https://pandoc.org/MANUAL.html).
- **Tectonic**: [tectonic-typesetting/tectonic](https://github.com/tectonic-typesetting/tectonic).
- **Typst**: [typst.app](https://typst.app/) · [Quarto + Typst docs](https://quarto.org/docs/output-formats/typst.html).

### Surveys / comparações práticas (2025–2026)

- *Best Open-Source PDF-to-Markdown Tools in 2026: Marker vs Docling vs MinerU vs pdf-craft vs PyMuPDF4LLM* (Menon Lab). [link](https://themenonlab.blog/blog/best-open-source-pdf-to-markdown-tools-2026).
- *Best Open Source PDF to Markdown Tools (2026): Marker vs MinerU vs MarkItDown* (Jimmy Song). [link](https://jimmysong.io/blog/pdf-to-markdown-open-source-deep-dive/).
- *PDF Data Extraction Benchmark 2025* (Procycons). [link](https://procycons.com/en/blogs/pdf-data-extraction-benchmark/).
