# Papers temáticos — fichas catalográficas

*Papers agrupados por tema: hallucination em OCR/VLM, round-trip, reconstrutores, forms, surveys/comparativos. Papers que introduzem métricas/benchmarks têm ficha cruzada também em [`metricas.md`](metricas.md) / [`benchmarks.md`](benchmarks.md).*

---

## Hallucination em OCR / VLM

### Shah et al. 2025 — *Seeing is Believing*

- **Tipo**: paper (NeurIPS 2025, poster)
- **Origem**: Bytedance Research
- **Ano**: 2025
- **Refs**: [arXiv 2506.20168](https://arxiv.org/abs/2506.20168)
- **Sumário**: *Seeing is Believing? Mitigating OCR Hallucinations in Multimodal Large Language Models*. VLMs sofrem com inputs degradados (blur, oclusão, contraste baixo) — substituem percepção visual por linguistic priors. Introduz [KIE-HVQA benchmark](benchmarks.md#kie-hvqa) (400 amostras pixel-level). Mitigação via [GRPO](glossario.md#grpo) com reward de "refusal to answer" em regiões ambíguas → +22pp absoluto sobre GPT-4o.
- **Status no projeto**: **referência apenas** (formaliza nome "OCR hallucination"; nosso caso ≠ degradado, é input legítimo mas esparso)
- **Relação com**: introduz [KIE-HVQA](benchmarks.md#kie-hvqa); novidade v2 (não em v1); valida [bloat_ratio](metricas.md#bloat_ratio-t071--original-do-projeto) como nicho complementar.

### Zhang et al. 2025 — *Consensus Entropy*

- **Tipo**: paper (multi-VLM agreement)
- **Origem**: Zhang, K. et al.
- **Ano**: 2025 (v6 mar/26)
- **Refs**: [arXiv 2504.11101](https://arxiv.org/abs/2504.11101)
- **Sumário**: *Consensus Entropy: Harnessing Multi-VLM Agreement for Self-Verifying and Self-Improving OCR*. Training-free, model-agnostic. +42.1% F1 sobre VLM-as-judge para detecção de OCR errors. Princípio: predições corretas convergem entre modelos; erros divergem.
- **Status no projeto**: **mapeado para futuro** (Q12)
- **Relação com**: define a métrica [Consensus Entropy](metricas.md#consensus-entropy); novidade v2; comparável a [bloat_ratio](metricas.md#bloat_ratio-t071--original-do-projeto) em filosofia (1 modelo + self-roundtrip vs N modelos + cross-agreement).

### Risk-Controlled OCR 2603.19790

- **Tipo**: paper (verifiability framework)
- **Origem**: (autores em arXiv)
- **Ano**: 2026
- **Refs**: [arXiv 2603.19790](https://arxiv.org/html/2603.19790v3)
- **Sumário**: *From Plausibility to Verifiability: Risk-Controlled Generative OCR with Vision-Language Models*. OCR via VLM como "seletivo aceitar/abster" com *geometric risk controller* que probe múltiplas vistas estruturadas e só aceita transcrição quando consenso bate threshold.
- **Status no projeto**: **referência apenas** (conceitualmente alinha-se com [bloat_ratio](metricas.md#bloat_ratio-t071--original-do-projeto) como count-based pre-filter)
- **Relação com**: novidade v2; análogo a [Consensus Entropy](metricas.md#consensus-entropy) mas via múltiplas vistas em vez de múltiplos modelos.

### Nougat §B.3 — repetition hallucination

- **Tipo**: seção §B.3 do paper Nougat
- **Origem**: Blecher et al. (Meta AI)
- **Ano**: 2023
- **Refs**: [arXiv 2308.13418](https://arxiv.org/abs/2308.13418) §B.3
- **Sumário**: Transformer com greedy decoding entra em loop, repetindo última sentença. Detectado em 1.5% das páginas in-domain, muito mais em out-of-domain. Heurística: **variance dos logits numa janela deslizante** (threshold 6.75 nos últimos 200 tokens) para parar geração precocemente.
- **Status no projeto**: **referência apenas** (mecanismo distinto do nosso [bloat_ratio](metricas.md#bloat_ratio-t071--original-do-projeto) — repetition é degenerative loop; nosso é amplification semântica)
- **Relação com**: parte do paper [Nougat](ferramentas.md#nougat); define [repetition hallucination](glossario.md#repetition-hallucination).

### Hallucination Survey 2404.18930

- **Tipo**: survey paper
- **Origem**: (autores em arXiv)
- **Ano**: 2024
- **Refs**: [arXiv 2404.18930](https://arxiv.org/abs/2404.18930)
- **Sumário**: *Hallucination of Multimodal Large Language Models: A Survey*. Taxonomia de hallucination em MLLMs.
- **Status no projeto**: **referência apenas**
- **Relação com**: complementa [Multimodal Hallucination Survey 2507.19024](#multimodal-hallucination-survey-2507-19024); novidade v2.

### Multimodal Hallucination Survey 2507.19024

- **Tipo**: survey paper
- **Origem**: (autores em arXiv)
- **Ano**: 2025
- **Refs**: [arXiv 2507.19024](https://arxiv.org/abs/2507.19024)
- **Sumário**: *A Survey of Multimodal Hallucination Evaluation and Detection*.
- **Status no projeto**: **referência apenas**
- **Relação com**: complementa [Hallucination Survey 2404.18930](#hallucination-survey-2404-18930); novidade v2.

### Mirage of Hallucination Detection (EMNLP 2025)

- **Tipo**: paper (crítica de hallucination detection)
- **Origem**: (autores em ACL Anthology)
- **Ano**: 2025 (EMNLP Findings)
- **Refs**: [PDF](https://aclanthology.org/2025.findings-emnlp.1035.pdf) · [arXiv 2504.18114](https://arxiv.org/html/2504.18114v1)
- **Sumário**: *The Mirage of Hallucination Detection*. Métricas de hallucination detection em LLM frequentemente **não alinham com human judgment e não escalam consistentemente com parâmetros**. LLM-as-judge (GPT-4) ainda dá os melhores resultados práticos.
- **Status no projeto**: **referência apenas** (atenuante para nosso plano — usar LLM-as-judge sabendo dos vieses)
- **Relação com**: justificativa parcial para manter [LLM-as-judge](metricas.md#m2-llm-as-judge-para-fórmulas-primária) como primária; novidade v2.

### GutenOCR 2601.14490

- **Tipo**: paper (constrained decoding)
- **Origem**: Roots.ai
- **Ano**: 2026
- **Refs**: [arXiv 2601.14490](https://arxiv.org/html/2601.14490v1)
- **Sumário**: *GutenOCR: A Grounded Vision–Language Front-End for Documents*. Tentou constrained decoding (OCR-token-restricted vocabulary). **Falhou na prática**: VLMs persistem em gerar tokens ausentes do input visível.
- **Status no projeto**: **avaliado e descartado** (constrained decoding não funciona p/ hallucination semântica)
- **Relação com**: define [constrained decoding](glossario.md#constrained-decoding) como mitigação rejeitada; novidade v2.

---

## Round-trip / consistency

### Allamanis et al. 2024 — Round-Trip Correctness

- **Tipo**: paper (RTC para código)
- **Origem**: (Microsoft Research / Allamanis et al.)
- **Ano**: 2024
- **Refs**: [arXiv 2402.08699](https://arxiv.org/abs/2402.08699)
- **Sumário**: *Unsupervised Evaluation of Code LLMs with Round-Trip Correctness*. Descrever código em NL e re-sintetizar, checar equivalência semântica. RTC correlaciona bem com qualidade *quando há verificador semântico downstream*.
- **Status no projeto**: **referência apenas** (aplicação mais próxima do que fazemos; ainda canônico, sem follow-up 2025/2026 estendendo formalmente para documentos)
- **Relação com**: define [RTC](glossario.md#rtc); inspiração conceitual para round-trip PDF→MD; cf. [Moon et al. 2020](#moon-et-al-2020-rtt-quality-estimation).

### Moon et al. 2020 — RTT quality estimation

- **Tipo**: paper (EAMT 2020)
- **Origem**: Moon, J. et al.
- **Ano**: 2020
- **Refs**: [PDF](https://aclanthology.org/2020.eamt-1.11.pdf)
- **Sumário**: *Revisiting Round-Trip Translation for Quality Estimation*. BLEU(input, RTT) correlaciona **pobremente** com qualidade real em MT. Recuperável quando combinada com métricas semânticas ([Zhuo et al. 2209.07351](https://arxiv.org/abs/2209.07351)).
- **Status no projeto**: **referência apenas** (justifica rebaixar round-trip a health check; ver [`../METRICS.md`](../metricas.md))
- **Relação com**: define [RTT](glossario.md#round-trip--rtt); base do rebaixamento de round-trip; ver também [Aiken & Park 2010] mencionado em v1; reforçado por [Mirage 2025](#mirage-of-hallucination-detection-emnlp-2025).

### RTT-LiT 2026 — *Round-Trip Translation Reveals What Frontier Multilingual Benchmarks Miss*

- **Tipo**: paper (multilingual)
- **Origem**: (autores em arXiv)
- **Ano**: 2026
- **Refs**: [arXiv 2604.12911](https://arxiv.org/html/2604.12911)
- **Sumário**: Pesquisa em RTT para LLMs multilíngues mostra que MQM scores ≥ 80 correlacionam **ρ=0.94** com preferência humana. Melhor evidência recente de que RTT pode ser proxy válido — *desde que* combinado com avaliação semântica estruturada (MQM), não com BLEU puro.
- **Status no projeto**: **referência apenas** (não muda decisão de v1 sobre round-trip; reforça "round-trip é OK *com* verificador semântico")
- **Relação com**: complementa [Moon et al. 2020](#moon-et-al-2020-rtt-quality-estimation); novidade v2.

### Horn et al. 2025 — *Accelerating End-to-End PDF to Markdown Conversion*

- **Tipo**: paper (NLDB 2025)
- **Origem**: Horn, P., Keuper, J.
- **Ano**: 2025-12
- **Refs**: [arXiv 2512.18122](https://arxiv.org/abs/2512.18122)
- **Sumário**: *Accelerating End-to-End PDF to Markdown Conversion Through Assisted Generation*. Usa *Copy Lookup Decoding* explorando "high n-gram overlap between PDFs and their Markdown equivalents". Implicitamente confirma que round-trip preserva muito conteúdo em documentos texto-densos, e degrada quando overlap n-gram cai (= input esparso, exatamente nosso caso).
- **Status no projeto**: **referência apenas**
- **Relação com**: novidade v2; suporte teórico ao fenômeno detectado em [bloat_ratio](metricas.md#bloat_ratio-t071--original-do-projeto) (input esparso → degradação).

### Li et al. 2025 — READoc / S³uite

- **Tipo**: paper (ACL Findings 2025)
- **Origem**: Li, Z. et al.
- **Ano**: 2025
- **Refs**: [arXiv 2409.05137](https://arxiv.org/abs/2409.05137) · [ACL](https://aclanthology.org/2025.findings-acl.1128/)
- **Sumário**: *READoc: A Unified Benchmark for Realistic Document Structured Extraction*. Primeiro benchmark a tratar DSE como PDF → Markdown end-to-end. S³uite (Standardization, Segmentation, Scoring). Métricas: EDS, TEDS, KTDS (Kendall-τ reading order). Avaliou 14 sistemas.
- **Status no projeto**: **mapeado para futuro** (Q14)
- **Relação com**: introduz [READoc benchmark](benchmarks.md#readoc); novidade v2.

---

## Reconstrutores / typesetting

### Pandoc manual

- **Tipo**: documentação oficial
- **Origem**: John MacFarlane
- **Ano**: contínuo
- **Refs**: [pandoc.org/MANUAL](https://pandoc.org/MANUAL.html)
- **Sumário**: Pandoc mantém suíte de testes round-trip intra-formato (`md → AST → md`). Doc oficial reconhece que conversão lossless cross-format é, em geral, impossível — é desejável, não teorema. Ver tb. [Wikipedia: round-trip format conversion](https://en.wikipedia.org/wiki/Round-trip_format_conversion).
- **Status no projeto**: **adotado** (base do pipeline)
- **Relação com**: ferramenta [Pandoc + Chrome + KaTeX](ferramentas.md#pandoc--chrome--katex-atual).

### Tectonic (repo + docs)

- **Tipo**: documentação
- **Origem**: tectonic-typesetting
- **Refs**: [repo](https://github.com/tectonic-typesetting/tectonic)
- **Sumário**: Distribuição XeTeX single-binary com fontes on-demand; reproducible builds.
- **Status no projeto**: **mapeado para futuro** (Q8)
- **Relação com**: ferramenta [Tectonic](ferramentas.md#tectonic).

### Typst (paper + docs)

- **Tipo**: documentação
- **Origem**: typst.app
- **Refs**: [typst.app](https://typst.app/)
- **Sumário**: Math nativo, single-binary Rust; conversão LaTeX→Typst de math ainda imperfeita.
- **Status no projeto**: **em research**
- **Relação com**: ferramenta [Typst](ferramentas.md#typst).

### Quarto issue 11368 (LaTeX→Typst math)

- **Tipo**: discussão pública
- **Origem**: Quarto / Posit
- **Ano**: 2024–2025
- **Refs**: [Quarto issue 11368](https://github.com/orgs/quarto-dev/discussions/11368)
- **Sumário**: Documenta limitações práticas de conversão LaTeX → Typst em math (motiva manter Typst como "em research" e não promover a "mapeado").
- **Status no projeto**: **referência apenas**
- **Relação com**: justifica posição cautelosa em [Typst](ferramentas.md#typst).

### WeasyPrint (docs)

- **Tipo**: documentação
- **Origem**: Kozea
- **Refs**: weasyprint.org
- **Sumário**: HTML/CSS → PDF sem Chrome. Math limitada (precisa MathML pré-renderizado; KaTeX server-side OK).
- **Status no projeto**: **mapeado para futuro** (alternativa Chrome em CI)
- **Relação com**: ferramenta [WeasyPrint](ferramentas.md#weasyprint).

---

## Forms / structured documents

### FormNet (ACL 2022)

- **Tipo**: paper
- **Origem**: Google
- **Ano**: 2022 (ACL 2022)
- **Refs**: [paper](https://aclanthology.org/2022.acl-long.260.pdf)
- **Sumário**: *FormNet: Structural Encoding beyond Sequential Modeling in Form Document Information Extraction*. Rich Attention + Super-Tokens via GCN. SOTA CORD/FUNSD em 2022.
- **Status no projeto**: **referência apenas**
- **Relação com**: ferramenta [FormNet](ferramentas.md#formnet); novidade v2; alternativa a [LayoutLM](#layoutlm).

### LayoutLM (família)

- **Tipo**: papers (Microsoft)
- **Origem**: Microsoft Research
- **Ano**: 2020 (v1), 2021 (v2), 2022 (v3)
- **Sumário**: Pré-treino conjunto texto + layout + image. Form-aware nativo.
- **Status no projeto**: **referência apenas**
- **Relação com**: ferramenta [LayoutLM/v2/v3](ferramentas.md#layoutlm--layoutlmv2--layoutlmv3).

### Donut (ECCV 2022)

- **Tipo**: paper (Naver)
- **Origem**: Naver
- **Ano**: 2022 (ECCV 2022)
- **Sumário**: OCR-free, multimodal end-to-end para document understanding.
- **Status no projeto**: **referência apenas**
- **Relação com**: ferramenta [Donut](ferramentas.md#donut).

### Tkaczyk et al. 2018 — bibliographic parsers

- **Tipo**: paper (avaliação de bibliography extractors)
- **Origem**: Tkaczyk, D. et al.
- **Ano**: 2018
- **Refs**: [arXiv 1802.01168](https://arxiv.org/pdf/1802.01168)
- **Sumário**: *Machine Learning vs. Rules and Out-of-the-Box vs. Retrained: An Evaluation of Open Source Bibliographic Reference Parsers*. Formaliza protocolo F1 (strict / soft / Levenshtein).
- **Status no projeto**: **referência apenas** (define protocolo de [Citation F1](metricas.md#citation-f1-levenshtein-normalizado))
- **Relação com**: usado em avaliação de [GROBID](ferramentas.md#grobid).

---

## Métricas — papers de origem

### Zhong et al. 2020 — TEDS / PubTabNet

- **Tipo**: paper (ECCV 2020)
- **Origem**: Zhong, X., ShafieiBavani, E., Yepes, A.J.
- **Ano**: 2020
- **Refs**: [arXiv 1911.10683](https://arxiv.org/abs/1911.10683)
- **Sumário**: *Image-based table recognition: data, model, and evaluation*. Introduz [TEDS](metricas.md#m3-teds-tree-edit-distance-similarity-para-tabelas) junto com [PubTabNet](benchmarks.md#pubtabnet).
- **Status no projeto**: **adotado** (origem da TEDS)
- **Relação com**: ver [TEDS](metricas.md#m3-teds-tree-edit-distance-similarity-para-tabelas), [PubTabNet](benchmarks.md#pubtabnet).

### Wang et al. 2025 — CDM

- **Tipo**: paper (CVPR 2025)
- **Origem**: Wang, B. et al.
- **Ano**: 2025
- **Refs**: [arXiv 2409.03643](https://arxiv.org/abs/2409.03643)
- **Sumário**: *Image Over Text: Transforming Formula Recognition Evaluation with Character Detection Matching*. Introduz [CDM](metricas.md#cdm-character-detection-matching). 96% concordância humana vs ~64% de BLEU em 2025.
- **Status no projeto**: **adotado** (CDM como secondary check)
- **Relação com**: documenta falha de [BLEU-LaTeX](metricas.md#bleu-latex); CDM foi rebaixada por [Horn & Keuper](#horn-keuper-2512-09874) em 2025-12.

### Horn & Keuper 2512.09874 — *Benchmarking Document Parsers on Mathematical Formula Extraction*

- **Tipo**: paper (benchmark + métrica)
- **Origem**: Horn, P., Keuper, J.
- **Ano**: 2025-12-10
- **Refs**: [arXiv 2512.09874](https://arxiv.org/abs/2512.09874)
- **Sumário**: 100 PDFs sintéticos + 2.000 fórmulas + 750 ratings sobre 250 pares. **LLM-as-judge r=0.78 vs humanos; CDM r=0.34; BLEU-style r~0**. Top performers: [Qwen3-VL](ferramentas.md#qwen3-vl--qwen36-plus) (9.76), Gemini 3 Pro (9.75), [PaddleOCR-VL](ferramentas.md#paddleocr-vl) (9.65), [Mathpix](ferramentas.md#mathpix) (9.64).
- **Status no projeto**: **adotado** (motiva rebaixamento de CDM e adoção de LLM-as-judge como M2 primária)
- **Relação com**: rebaixa [CDM](metricas.md#cdm-character-detection-matching) e [TeXBLEU](metricas.md#texbleu); define [LLM-as-judge](metricas.md#m2-llm-as-judge-para-fórmulas-primária) como primária; **Marker/Nougat/Docling não foram avaliados** → gap T050.
- **Conflito v1×v2**: Este paper **é a razão central** do conflito v1→v2 sobre CDM.

### Reading-order metrics (arXiv 2404.18664)

- **Tipo**: paper
- **Origem**: (autores em arXiv)
- **Ano**: 2024
- **Refs**: [arXiv 2404.18664](https://arxiv.org/html/2404.18664v1)
- **Sumário**: *Reading Order Independent Metrics for Information Extraction in Handwritten Documents*. Propõe BoW-WER e Flexible Character Accuracy.
- **Status no projeto**: **adotado** (referência metodológica para [BoW-WER](metricas.md#bow-wer-bag-of-words-wer))
- **Relação com**: define [BoW-WER](metricas.md#bow-wer-bag-of-words-wer) e [FCA](metricas.md#fca-flexible-character-accuracy).

### OCR-D Quality Assurance spec

- **Tipo**: especificação
- **Origem**: OCR-D community
- **Refs**: [ocr-d.de spec](https://ocr-d.de/en/spec/ocrd_eval.html)
- **Sumário**: WER/CER/FCA para OCR. Documenta que "a maioria das métricas de qualidade OCR baseia-se em distância de Levenshtein".
- **Status no projeto**: **adotado** (referência clássica)
- **Relação com**: origem prática de [WER-prosa](metricas.md#m1-wer-prosa).

---

## Surveys / comparativos

### Best Open-Source PDF→MD 2026 (Menon Lab)

- **Tipo**: comparativo / blog
- **Origem**: Menon Lab
- **Ano**: 2026
- **Refs**: [themenonlab.blog](https://themenonlab.blog/blog/best-open-source-pdf-to-markdown-tools-2026)
- **Sumário**: Comparativo Marker vs Docling vs MinerU vs pdf-craft vs PyMuPDF4LLM.
- **Status no projeto**: **referência apenas**

### Jimmy Song — PDF→MD deep dive 2026

- **Tipo**: comparativo / blog
- **Origem**: Jimmy Song
- **Ano**: 2026
- **Refs**: [jimmysong.io](https://jimmysong.io/blog/pdf-to-markdown-open-source-deep-dive/)
- **Sumário**: Marker vs MinerU vs MarkItDown.
- **Status no projeto**: **referência apenas**

### Procycons — PDF Data Extraction Benchmark 2025

- **Tipo**: blog comparativo
- **Origem**: Procycons
- **Ano**: 2025
- **Refs**: [procycons.com](https://procycons.com/en/blogs/pdf-data-extraction-benchmark/)
- **Sumário**: Benchmark prático de PDF data extraction tools.
- **Status no projeto**: **referência apenas**

### Regolo 2026 — DeepSeek-OCR vs GLM-OCR vs PaddleOCR

- **Tipo**: blog comparativo
- **Origem**: regolo.ai
- **Ano**: 2026
- **Refs**: [regolo.ai](https://regolo.ai/deepseek-ocr-vs-glm-ocr-vs-paddleocr-benchmark-2026/)
- **Sumário**: dots.ocr venceu em character accuracy. Comparativo de OCRs lightweight 2026.
- **Status no projeto**: **referência apenas**
- **Relação com**: cita [dots.ocr](ferramentas.md#dotsocr), [GLM-OCR](ferramentas.md#glm-ocr), [PaddleOCR-VL](ferramentas.md#paddleocr-vl), [DeepSeek-OCR](ferramentas.md#deepseek-ocr); novidade v2.

---

*Total: 16+ entradas (8 hallucination, 5 round-trip/reconstrutores, 4 forms, 5 métricas-origem, 4 surveys).*
