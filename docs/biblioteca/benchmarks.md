# Benchmarks — fichas catalográficas

*Datasets e leaderboards para document parsing, layout, tabelas, fórmulas, formulas/forms, OCR hallucination.*

---

### OmniDocBench

- **Tipo**: benchmark (end-to-end document parsing)
- **Origem**: OpenDataLab / Shanghai AI Lab (CVPR 2025)
- **Ano**: 2024 (v1), 2025–2026 (v1.5/v1.6/v1.7)
- **Licença**: Permissive (research)
- **Refs**: [arXiv 2412.07626](https://arxiv.org/abs/2412.07626) · [repo](https://github.com/opendatalab/OmniDocBench) · [BenchLM v1.5](https://benchlm.ai/benchmarks/omniDocBench15)
- **Sumário**: 9 tipos de documento (academic, textbook, slides, financial, news, handwriting, etc.), zh+en. 1.355 páginas, ~20k blocos, ~80k spans. Anotação end-to-end (text, table, formula, layout, reading order). Inclui textbooks com matemática. v1.6 introduz **Hard subset** (296 páginas com fórmulas/tabelas/layouts difíceis). v1.7 adiciona Qianfan-OCR leaderboard e skills-based eval.
- **Status no projeto**: **adotado** (baseline reprodutível para T050; melhor match com nossos casos — textbook + math + tabela)
- **Relação com**: SOTA inicial [MinerU 2.5](ferramentas.md#mineru-25) ~90.67; v1.6 [MinerU 2.5-Pro](ferramentas.md#mineru-25-pro) = 95.69; v1.5 saturado em 94+ por [DeepSeek-OCR](ferramentas.md#deepseek-ocr), [dots.ocr](ferramentas.md#dotsocr), [PaddleOCR-VL](ferramentas.md#paddleocr-vl), [GLM-OCR](ferramentas.md#glm-ocr); avaliação via `omnidocbench` CLI.
- **Conflito v1×v2**: v1 menciona SOTA 90.67 (MinerU 2.5); v2 atualiza para 95.69 (MinerU 2.5-Pro v1.6) e nota saturação do leaderboard com VLMs novos.

### DocLayNet

- **Tipo**: benchmark (layout-only)
- **Origem**: IBM (KDD 2022)
- **Ano**: 2022
- **Licença**: CDLA-Permissive 1.0
- **Refs**: [arXiv 2206.01062](https://arxiv.org/abs/2206.01062)
- **Sumário**: Layout COCO, 11 classes, multi-domínio. 80.863 páginas anotadas. Layout-only, sem texto/fórmula GT.
- **Status no projeto**: **referência apenas** (útil só para sub-task layout)
- **Relação com**: classe relacionada à [PubLayNet](#publaynet).

### DocBank

- **Tipo**: benchmark (semantic structure)
- **Origem**: Microsoft + Beihang (COLING 2020)
- **Ano**: 2020
- **Licença**: Apache-2.0
- **Refs**: [repo](https://github.com/doc-analysis/DocBank)
- **Sumário**: arXiv, 12 classes semânticas, weak supervision via LaTeX. 500k páginas. Paper-style apenas, não livros.
- **Status no projeto**: **referência apenas** (boa para baseline; pouco diverso)
- **Relação com**: cobertura semelhante a [Nougat eval](#nougat-eval).

### PubLayNet

- **Tipo**: benchmark (layout, PMC)
- **Origem**: IBM
- **Ano**: 2019
- **Licença**: CDLA-Permissive 1.0
- **Refs**: (paper IBM)
- **Sumário**: Layout, PMC. 360k páginas. Biomedical-only, layouts conservadores; nada de matemática densa.
- **Status no projeto**: **avaliado e descartado** (out-of-domain para QC books/papers)
- **Relação com**: classe semelhante a [DocLayNet](#doclaynet).

### PubTabNet

- **Tipo**: benchmark (tabelas + HTML)
- **Origem**: IBM
- **Ano**: 2020 (ECCV junto com [TEDS](metricas.md#m3-teds-tree-edit-distance-similarity-para-tabelas))
- **Licença**: CDLA-Permissive 1.0
- **Refs**: ver [Zhong et al. 1911.10683](papers.md#zhong-et-al-2020-teds--pubtabnet)
- **Sumário**: 568k tabelas com HTML. Não cobre tabelas científicas com matemática (raras em PMC).
- **Status no projeto**: **referência apenas** (alto valor para sub-task tabelas; out-of-domain para math)
- **Relação com**: dataset onde [TEDS](metricas.md#m3-teds-tree-edit-distance-similarity-para-tabelas) foi introduzida; complementado por [SciTSR](#scitsr--scitsr-comp).

### SciTSR / SciTSR-COMP

- **Tipo**: benchmark (tabelas científicas)
- **Origem**: Tencent
- **Ano**: 2019
- **Licença**: MIT
- **Refs**: [arXiv 1908.04729](https://arxiv.org/abs/1908.04729)
- **Sumário**: 15k tabelas (12k train / 3k test); **SciTSR-COMP** com 716 tabelas complexas. Anotação a partir de fonte LaTeX.
- **Status no projeto**: **mapeado para futuro** (Q5 — tabelas com células agrupadas: GFM markdown vs HTML inline)
- **Relação com**: usado em [TEDS-S](metricas.md#teds-s-tree-edit-distance-só-estrutura) para tabelas complexas; complementa [PubTabNet](#pubtabnet).

### DocILE

- **Tipo**: benchmark (faturas, ordens)
- **Origem**: Rossum (ICDAR 2023)
- **Ano**: 2023
- **Licença**: CC BY-NC-SA
- **Refs**: [arXiv 2302.05658](https://arxiv.org/abs/2302.05658)
- **Sumário**: KILE/LIR (Key-Information Localization / Line Item Recognition). 6.7k anotadas + 100k sintéticas + ~1M unlabeled. Business documents.
- **Status no projeto**: **avaliado e descartado** (out-of-domain — não scientific)
- **Relação com**: relacionado a [forms](glossario.md#acroform); não usar para QC.

### olmOCR-Bench

- **Tipo**: benchmark (unit tests por documento)
- **Origem**: Allen AI
- **Ano**: 2025
- **Licença**: ODC-By
- **Refs**: [olmocr.allenai.org](https://olmocr.allenai.org/)
- **Sumário**: 7.000+ test cases / 1.400 docs. Avalia presença/ausência de fatos via testes em vez de string-match. Especialmente forte para English print + scans.
- **Status no projeto**: **adotado** (referência para English print + scans)
- **Relação com**: dataset que [olmOCR-2](ferramentas.md#olmocr-2) treina via RLVR; usa filosofia de test-as-reward (≈ [RLVR](glossario.md#rlvr)).

### Marker bench

- **Tipo**: benchmark interno (heurística)
- **Origem**: Datalab
- **Ano**: 2024–
- **Licença**: GPL-3.0 (repo)
- **Refs**: [marker benchmarks](https://github.com/datalab-to/marker/tree/master/benchmarks)
- **Sumário**: ~centenas de PDFs. Heurística proprietária com pesos arbitrários.
- **Status no projeto**: **referência apenas** (heurística pondera arbitrariamente)
- **Relação com**: parte do ecosistema [Marker](ferramentas.md#marker).

### Nougat eval

- **Tipo**: benchmark (arXiv + PMC)
- **Origem**: Meta AI
- **Ano**: 2023
- **Licença**: CC BY-NC
- **Refs**: [arXiv 2308.13418](https://arxiv.org/abs/2308.13418)
- **Sumário**: Em-line markup (Mathpix Markdown-compatible). Eval set é arXiv split. Boa para math papers; restrito ao domínio arXiv.
- **Status no projeto**: **mapeado para futuro** (math papers — alguns subsets em T050)
- **Relação com**: avalia [Nougat](ferramentas.md#nougat); inspiração para [Mathpix Markdown format](ferramentas.md#mathpix).

### READoc

- **Tipo**: benchmark (Document Structured Extraction end-to-end)
- **Origem**: (Li, Z. et al.) ACL Findings 2025
- **Ano**: 2025
- **Licença**: (consultar repo)
- **Refs**: [arXiv 2409.05137](https://arxiv.org/abs/2409.05137) · [ACL](https://aclanthology.org/2025.findings-acl.1128/)
- **Sumário**: Primeiro benchmark a tratar DSE como **PDF → Markdown end-to-end**, com S³uite (Standardization, Segmentation, Scoring). Métricas: EDS (edit distance similarity), TEDS, **KTDS** (Kendall-τ similarity para reading order). Avaliou 14 sistemas (Marker, MinerU, Docling, Nougat...). Usa GT de fonte LaTeX/HTML — não é round-trip.
- **Status no projeto**: **mapeado para futuro** (Q14 — rodar baseline contra subset READoc *antes* de T040 completo)
- **Relação com**: novidade v2; endereça parcialmente Q10 (reading order); evita "viés do reconstrutor" do round-trip puro; ver também [`papers.md` § Round-trip](papers.md#li-et-al-2025-readoc-s3uite).
- **Conflito v1×v2**: v1 não menciona READoc; v2 recomenda rodar baseline contra subset READoc *antes* de construir corpus T040 completo.

### KIE-HVQA

- **Tipo**: benchmark (OCR hallucination em forms)
- **Origem**: Bytedance Research
- **Ano**: 2025 (NeurIPS 2025)
- **Refs**: [arXiv 2506.20168](https://arxiv.org/abs/2506.20168) · [HF Dataset](https://huggingface.co/datasets/bytedance-research/KIE-HVQA)
- **Sumário**: Primeiro benchmark dedicado a OCR hallucination em VLMs. 400 amostras anotadas pixel-level em ID cards, recibos e faturas degradadas (blur, oclusão, contraste baixo).
- **Status no projeto**: **referência apenas** (forms only; não diretamente aplicável; template metodológico)
- **Relação com**: produto do paper [Shah et al. 2025](papers.md#shah-et-al-2025-seeing-is-believing); novidade v2; introduz mitigação via [GRPO](glossario.md#grpo) + refuse-to-answer.

### OCR-Quality

- **Tipo**: benchmark (human-annotated OCR quality)
- **Origem**: Zhang et al. (out. 2025)
- **Ano**: 2025-10
- **Licença**: (consultar paper)
- **Refs**: [arXiv 2510.21774](https://arxiv.org/pdf/2510.21774)
- **Sumário**: Dataset human-annotated para calibrar métricas automáticas contra GT humano.
- **Status no projeto**: **em research**
- **Relação com**: novidade v2.

---

*Total: 12 entradas.*
