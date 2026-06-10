# Ferramentas — fichas catalográficas

*Extratores PDF→MD, OCR/VLM, reconstrutores MD→PDF, libs auxiliares. Cada ficha tem links cruzados para [`benchmarks.md`](benchmarks.md), [`metricas.md`](metricas.md), [`papers.md`](papers.md) e [`glossario.md`](glossario.md).*

---

## Extratores PDF→MD (open-source)

### Marker

- **Tipo**: ferramenta open-source (pipeline modular)
- **Origem**: Datalab (Vik Paruchuri)
- **Ano**: 2024–2026 (v1.10.2 em 31-jan-2026)
- **Licença**: GPL-3.0 (código); AI Pubs Open Rail-M (pesos, free p/ research)
- **Refs**: [repo](https://github.com/datalab-to/marker) · [benchmarks](https://github.com/datalab-to/marker/tree/master/benchmarks) · [releases](https://github.com/datalab-to/marker/releases)
- **Sumário**: pipeline modular Surya (OCR + layout + table + equation) com opção `--use_llm`. Throughput alto. Math em LaTeX. Block-level OCR é default a partir de v1.10.x.
- **Status no projeto**: **adotado** (extrator atual)
- **Relação com**: backend é [Surya](#surya); foi o baseline em T050 (round-trip 95.09% no N&C cap. 4); `--use_llm` recomendado para AcroForm (ver [`papers.md` § forms](papers.md#formnet)); aparece em [`arquitetura.md`](../../explanation/arquitetura.md).
- **Conflito v1×v2**: v1 mencionava 1.10.x genérico; v2 fixa v1.10.2 (31-jan-2026) com Surya 0.17.1.

### MinerU 2.5

- **Tipo**: ferramenta open-source (VLM 1.2B)
- **Origem**: Shanghai AI Lab / OpenDataLab
- **Ano**: 2025
- **Licença**: AGPL-3.0
- **Refs**: [repo](https://github.com/opendatalab/MinerU)
- **Sumário**: SOTA OmniDocBench v1.6 ~90.67 em 2025; excelente em CJK, tabelas truncadas, gráficos. VLM 1.2B + CPU possível com pipeline backend.
- **Status no projeto**: **mapeado para futuro** (candidato a re-baseline em T050)
- **Relação com**: avaliado em [OmniDocBench](benchmarks.md#omnidocbench); AGPL é o ponto chato para integração (ver [`../LICENSING.md`](../corpus/licensing.md)).

### MinerU 2.5-Pro

- **Tipo**: ferramenta open-source (VLM 1.2B)
- **Origem**: Shanghai AI Lab / OpenDataLab
- **Ano**: 2026-04 (6-abr-2026)
- **Licença**: AGPL-3.0
- **Refs**: [arXiv 2604.04771](https://arxiv.org/abs/2604.04771) · [HF model](https://huggingface.co/opendatalab/MinerU2.5-Pro-2604-1.2B)
- **Sumário**: Mesma arquitetura 1.2B do 2.5; ganho via data engineering (10M→65.5M, diversity-and-difficulty-aware sampling, judge-and-refine annotation). OmniDocBench v1.6 = 95.69 (+2.71). Table TEDS +5.54, dense formula CDM 97.29, text edit distance 0.036.
- **Status no projeto**: **mapeado para futuro** (Q15 — supera Marker no N&C cap. 4?)
- **Relação com**: [OmniDocBench v1.6](benchmarks.md#omnidocbench); evolução de [MinerU 2.5](#mineru-25); novidade v2 (não estava em v1).

### Nougat

- **Tipo**: ferramenta open-source (Transformer encoder-decoder)
- **Origem**: Meta AI
- **Ano**: 2023
- **Licença**: CC BY-NC 4.0
- **Refs**: [arXiv 2308.13418](https://arxiv.org/abs/2308.13418) · [repo](https://github.com/facebookresearch/nougat)
- **Sumário**: Primeiro end-to-end PDF→markup p/ math, treinado em arXiv+PMC, output Mathpix-compatible. Hallucination conhecida em out-of-domain. ~10× mais lento que Marker. Manutenção parada (último release 2023).
- **Status no projeto**: **mapeado para futuro** (comparativo em fórmulas longas — T050, Q2)
- **Relação com**: gerou o conceito de [repetition hallucination](glossario.md#repetition-hallucination) (§B.3 do paper) — ver [`papers.md`](papers.md#nougat-repetition); usado como referência para [Nougat eval](benchmarks.md#nougat-eval).

### olmOCR

- **Tipo**: ferramenta open-source (Qwen2.5-VL-7B fine-tune)
- **Origem**: Allen AI (Ai2)
- **Ano**: 2025
- **Licença**: Apache-2.0
- **Refs**: [olmocr.allenai.org](https://olmocr.allenai.org/) · [paper](https://olmocr.allenai.org/papers/olmocr.pdf) · [repo](https://github.com/allenai/olmocr)
- **Sumário**: Custo ~$190/M páginas, reading order excelente em multi-coluna e callouts, ELO >1800. Foco em English print. Math LaTeX inferior a Nougat/Marker em papers densos.
- **Status no projeto**: **mapeado para futuro** (T050 — scans de livros antigos: Sakurai, Cohen-Tannoudji)
- **Relação com**: evoluiu para [olmOCR-2](#olmocr-2); base é Qwen2.5-VL.

### olmOCR-2

- **Tipo**: ferramenta open-source (Qwen2.5-VL-7B + RLVR)
- **Origem**: Allen AI (Ai2)
- **Ano**: 2025-10 (olmOCR-2-7B-1025, 22-out-2025)
- **Licença**: Apache-2.0
- **Refs**: [arXiv 2510.19817](https://arxiv.org/abs/2510.19817) · [blog](https://allenai.org/blog/olmocr-2) · [HF model](https://huggingface.co/allenai/olmOCR-2-7B-1025)
- **Sumário**: RLVR (Reinforcement Learning with Verifiable Rewards) via GRPO; reward = unit tests determinísticos ("table structure preserved", "math faithfully transcribed"). olmOCR-Bench 82.4 (+4 sobre v1). Math 82.3%, tables 84.9%, multi-column 83.7%.
- **Status no projeto**: **mapeado para futuro** (T050)
- **Relação com**: introduz [RLVR](glossario.md#rlvr) no domínio; treinado contra [olmOCR-Bench](benchmarks.md#olmocr-bench); evolução do [olmOCR](#olmocr); novidade v2.

### Docling

- **Tipo**: toolkit open-source (não-VLM por padrão)
- **Origem**: IBM Research
- **Ano**: 2025 (AAAI 2025)
- **Licença**: MIT
- **Refs**: [arXiv 2501.17887](https://arxiv.org/html/2501.17887v1) · [repo](https://github.com/docling-project/docling)
- **Sumário**: TEDS 0.97 em FinTabNet; integração nativa com LangChain/LlamaIndex; suporte multi-formato (PDF, DOCX, PPTX, EPUB). Math menos polido que Nougat/Marker. Otimizado para corporate docs. Em jan/26 IBM doou para Linux Foundation AAIF.
- **Status no projeto**: **mapeado para futuro** (T050 — tabelas complexas, MIT-licensed friendly)
- **Relação com**: VLM exp é [Granite-Docling-258M](#granite-docling-258m).

### Granite-Docling-258M

- **Tipo**: VLM ultra-compact (258M params)
- **Origem**: IBM
- **Ano**: 2025-09
- **Licença**: Apache-2.0
- **Refs**: [HF model card](https://huggingface.co/ibm-granite/granite-docling-258M) · [IBM announcement](https://www.ibm.com/new/announcements/granite-docling-end-to-end-document-conversion)
- **Sumário**: Substitui SmolLM-2 por Granite-3-base; SigLIP por SigLIP2. F1 0.968 em equações (vs 0.947 antes). Mitigação de loops repetitivos do SmolDocling-256M-preview. Treinado em SynthFormulaNet.
- **Status no projeto**: **mapeado para futuro** (Q16 — viável CPU-only? < 8GB RAM, < 10s/página)
- **Relação com**: faz parte do ecossistema [Docling](#docling); novidade v2.

### DeepSeek-OCR

- **Tipo**: VLM (3B MoE-A570M decoder + DeepEncoder)
- **Origem**: DeepSeek
- **Ano**: 2025-10
- **Licença**: open-source (consultar repo)
- **Refs**: [arXiv 2510.18234](https://arxiv.org/html/2510.18234v1)
- **Sumário**: "Contexts Optical Compression" — comprime visual em 64–800 tokens (vs ~6000 do MinerU2.0). 97% accuracy a 10× compression; 60% a 20×. Throughput 200k+ páginas/dia em 1 GPU.
- **Status no projeto**: **em research** (relevante se corpus crescer)
- **Relação com**: novidade v2; aparece em [comparativo Regolo 2026](benchmarks.md#omnidocbench).

### dots.ocr

- **Tipo**: ferramenta open-source (OCR)
- **Origem**: (comunidade)
- **Ano**: 2025–2026
- **Licença**: open-source (consultar repo)
- **Refs**: [comparativo Regolo 2026](https://regolo.ai/deepseek-ocr-vs-glm-ocr-vs-paddleocr-benchmark-2026/)
- **Sumário**: Vencedor em character accuracy em comparativo independente.
- **Status no projeto**: **em research**
- **Relação com**: novidade v2.

### PaddleOCR-VL

- **Tipo**: VLM (0.9B)
- **Origem**: Baidu
- **Ano**: 2025
- **Licença**: open-source (consultar repo)
- **Refs**: [HF discussion](https://huggingface.co/PaddlePaddle/PaddleOCR-VL/discussions/29)
- **Sumário**: OmniDocBench v1.5 = 94.5. Lightweight. Top performer em [Horn & Keuper 2512.09874](papers.md#horn-keuper-2512-09874) (LLM-as-judge: 9.65/10).
- **Status no projeto**: **em research**
- **Relação com**: novidade v2; avaliada em [Horn & Keuper](metricas.md#m2-llm-as-judge-para-fórmulas-primária).

### GLM-OCR

- **Tipo**: VLM (0.9B)
- **Origem**: Zhipu / Tsinghua
- **Ano**: 2025
- **Licença**: open-source (consultar repo)
- **Refs**: leaderboard [OmniDocBench v1.5](benchmarks.md#omnidocbench)
- **Sumário**: Líder OmniDocBench v1.5 com 94.62.
- **Status no projeto**: **em research**
- **Relação com**: novidade v2.

### Mistral OCR

- **Tipo**: VLM proprietário
- **Origem**: Mistral AI
- **Ano**: 2025
- **Licença**: Proprietária
- **Refs**: (release notes Mistral)
- **Sumário**: Output Markdown + HTML para tabelas + LaTeX para math; "interleaved stream of text + images". Útil para forms parciais.
- **Status no projeto**: **em research** (cloud-only, fora do nicho OSS principal)
- **Relação com**: novidade v2; mencionado em [§ AcroForm](papers.md#acroform--forms).

### HunyuanOCR

- **Tipo**: VLM
- **Origem**: Tencent
- **Ano**: 2025
- **Licença**: (consultar release)
- **Refs**: discussões em comparativos (sem paper direto consultado)
- **Sumário**: ~80 OmniDocBench. Discutido em comparativos.
- **Status no projeto**: **em research**
- **Relação com**: novidade v2.

### Qwen3-VL / Qwen3.6 Plus

- **Tipo**: VLM geral
- **Origem**: Alibaba
- **Ano**: 2025–2026
- **Licença**: (consultar release)
- **Refs**: [BenchLM OmniDocBench v1.5](https://benchlm.ai/benchmarks/omniDocBench15)
- **Sumário**: VLMs gerais que lideram OmniDocBench v1.5 (Qwen3.6 Plus = 0.912 = 91.2%). Qwen3-VL = top performer em [Horn & Keuper 2512.09874](papers.md#horn-keuper-2512-09874) (LLM-as-judge: 9.76/10).
- **Status no projeto**: **em research**
- **Relação com**: novidade v2.

### GROBID

- **Tipo**: ferramenta open-source (CRF + opcional DL)
- **Origem**: Patrice Lopez
- **Ano**: 2008– (manutenção contínua); paper ECDL 2009
- **Licença**: Apache-2.0
- **Refs**: [repo](https://github.com/kermitt2/grobid) · [docs](https://grobid.readthedocs.io/) · [biorxiv benchmarks](https://grobid.readthedocs.io/en/latest/benchmarks/Benchmarking-biorxiv/)
- **Sumário**: F1 ~0.87–0.90 em referências em corpora PMC e bioRxiv. Padrão de facto para metadata + bibliografia scholarly. Saída TEI/XML (não Markdown). Quase nada de math.
- **Status no projeto**: **referência apenas** (second-opinion para Citation F1 quando aplicável; ver Q9 de v1)
- **Relação com**: usado em [Citation F1](metricas.md#citation-f1); citado por Tkaczyk et al. em [`papers.md`](papers.md).

### pix2tex / LaTeX-OCR

- **Tipo**: ferramenta open-source (ViT)
- **Origem**: Lukas Blecher
- **Ano**: 2022
- **Licença**: MIT
- **Refs**: [repo](https://github.com/lukas-blecher/LaTeX-OCR)
- **Sumário**: Formula-only OCR via image crop. Útil como segundo opinion p/ fórmulas que Marker errar. Single-formula; precisa detecção upstream.
- **Status no projeto**: **mapeado para futuro** (segundo opinion em fórmulas; eventualmente em T410)
- **Relação com**: complementa [Marker](#marker)/[Nougat](#nougat); mesmo autor de [Nougat](#nougat).

### Surya

- **Tipo**: backend OCR + layout do Marker
- **Origem**: Datalab (Vik Paruchuri)
- **Ano**: 2024–
- **Licença**: GPL-3.0
- **Refs**: [repo](https://github.com/datalab-to/surya)
- **Sumário**: OCR + layout + reading order + tables em 90+ línguas. `surya_latex_ocr` substitui Texify. Backend que [Marker](#marker) usa por baixo dos panos.
- **Status no projeto**: **adotado** (via Marker)
- **Relação com**: backend de [Marker](#marker); mesmo lock-in de licença.

---

## OCR/VLM auxiliares & proprietários

### Mathpix

- **Tipo**: SaaS comercial
- **Origem**: Mathpix
- **Ano**: 2014–
- **Licença**: Proprietária (cloud)
- **Refs**: [mathpix.com](https://mathpix.com/)
- **Sumário**: Reconhecidamente uma das melhores em math. Baseline comercial. Top performer em [Horn & Keuper 2512.09874](papers.md#horn-keuper-2512-09874) (LLM-as-judge: 9.64/10).
- **Status no projeto**: **referência apenas** (ceiling comercial; lock-in)
- **Relação com**: define formato de "Mathpix Markdown" usado por [Nougat](#nougat).

### Microsoft Document Intelligence

- **Tipo**: SaaS (Azure AI Services)
- **Origem**: Microsoft
- **Ano**: (contínuo)
- **Licença**: Proprietária (cloud)
- **Refs**: [docs](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/tax-document?view=doc-intel-4.0.0)
- **Sumário**: Prebuilt model "Unified US Tax" para W2/1098/1040/1099. Pré-treinado em forms específicos. Cloud-only.
- **Status no projeto**: **referência apenas** (fora do escopo OSS)
- **Relação com**: alternativa para forms ([AcroForm](glossario.md#acroform)), discutida em [`papers.md`](papers.md#acroform--forms).

### LayoutLM / LayoutLMv2 / LayoutLMv3

- **Tipo**: modelo research (Transformer com layout embedding)
- **Origem**: Microsoft Research
- **Ano**: 2020 (v1), 2021 (v2), 2022 (v3)
- **Licença**: MIT
- **Refs**: papers em arXiv (1912.13318, 2012.14740, 2204.08387)
- **Sumário**: Pré-treino conjunto texto + layout + image em FUNSD, CORD. Form-aware nativo.
- **Status no projeto**: **referência apenas** (classe form-understanding clássica)
- **Relação com**: contraposto a [FormNet](#formnet) e [Donut](#donut) em [`papers.md`](papers.md#layoutlm).

### FormNet

- **Tipo**: modelo research (Rich Attention + Super-Tokens via GCN)
- **Origem**: Google
- **Ano**: 2022 (ACL 2022)
- **Licença**: research
- **Refs**: [paper](https://aclanthology.org/2022.acl-long.260.pdf)
- **Sumário**: SOTA em CORD/FUNSD em 2022. Form-understanding via grafo.
- **Status no projeto**: **referência apenas**
- **Relação com**: ver [`papers.md` § Forms](papers.md#formnet).

### Donut

- **Tipo**: modelo research (OCR-free, end-to-end)
- **Origem**: Naver
- **Ano**: 2022 (ECCV 2022)
- **Licença**: MIT
- **Refs**: (paper ECCV 2022)
- **Sumário**: OCR-free multimodal end-to-end para document understanding.
- **Status no projeto**: **referência apenas**
- **Relação com**: ver [`papers.md` § Forms](papers.md#donut).

---

## Libs PDF baixo-nível

### pdftotext

- **Tipo**: lib CLI (parte de poppler-utils)
- **Origem**: Glyph & Cog / Poppler
- **Ano**: contínuo
- **Licença**: GPL-2.0
- **Refs**: poppler.freedesktop.org
- **Sumário**: Extrai texto puro de PDFs digitais. Não emite Markdown nem preserva estrutura.
- **Status no projeto**: **referência apenas** (fallback minimal)
- **Relação com**: mencionado em [v1 §3](../../explanation/literatura.md).

### PyMuPDF

- **Tipo**: lib Python (bind do MuPDF)
- **Origem**: Artifex
- **Ano**: contínuo
- **Licença**: AGPL-3.0 (livre) / comercial
- **Refs**: pymupdf.readthedocs.io
- **Sumário**: Lib robusta para extrair texto, layout e imagens. Variante `pymupdf4llm` emite Markdown.
- **Status no projeto**: **referência apenas** (alternativa para extração baixo-nível)
- **Relação com**: comparado em [surveys](papers.md#surveys-comparativos).

### pypdf

- **Tipo**: lib Python (pure)
- **Origem**: comunidade
- **Ano**: contínuo
- **Licença**: BSD-3-Clause
- **Refs**: [docs](https://pypdf.readthedocs.io/en/stable/user/forms.html)
- **Sumário**: `reader.get_fields()` e `reader.get_form_text_fields()` retornam dict campo→valor para AcroForm. Output trivialmente serializável.
- **Status no projeto**: **adotado** (workaround AcroForm IRS f1040 — round-trip de 46% para >90% esperado em Q11)
- **Relação com**: caso [AcroForm](glossario.md#acroform); novidade v2 (não estava em v1); ver [`papers.md` § Forms](papers.md#acroform--forms).

### PDFMiner.six

- **Tipo**: lib Python (pure)
- **Origem**: comunidade
- **Ano**: contínuo
- **Licença**: MIT
- **Refs**: [docs](https://pdfminersix.readthedocs.io/en/latest/howto/acro_forms.html)
- **Sumário**: Walk `/AcroForm` → `/Fields` → `/V` para acessar form data.
- **Status no projeto**: **referência apenas** (alternativa a pypdf)
- **Relação com**: forms; ver [`papers.md` § Forms](papers.md#acroform--forms).

---

## Reconstrutores MD → PDF

### Pandoc + Chrome + KaTeX (atual)

- **Tipo**: pipeline reconstrutor (Pandoc → HTML → Chrome headless → PDF)
- **Origem**: John MacFarlane (Pandoc) + Google Chrome + Khan Academy (KaTeX)
- **Ano**: contínuo
- **Licença**: GPL-2.0 (Pandoc), BSD (Chrome), MIT (KaTeX)
- **Refs**: [pandoc.org](https://pandoc.org/MANUAL.html) · [katex.org](https://katex.org/)
- **Sumário**: Robusto, 95.09% round-trip no N&C cap. 4 (T050). KaTeX é subset do LaTeX, suficiente para 99% do que aparece em livros de QC. HTML/CSS, sem "look" LaTeX mas fiel.
- **Status no projeto**: **adotado** (reconstrutor atual)
- **Relação com**: usado no pipeline ([`arquitetura.md`](../../explanation/arquitetura.md)); falha em `\xymatrix` ou `tikz`; potencial substituição por [Tectonic](#tectonic) em Q8.

### Pandoc + pdflatex / lualatex

- **Tipo**: pipeline reconstrutor (Pandoc → TeX → PDF)
- **Origem**: Pandoc + TeX Live
- **Ano**: contínuo
- **Licença**: GPL-2.0 (Pandoc), LPPL (TeX Live)
- **Refs**: [pandoc.org](https://pandoc.org/MANUAL.html)
- **Sumário**: Maior fidelidade math/tipografia. Falha em pacotes não-canônicos. TeX Live ~5GB. Debugging chato. Lento.
- **Status no projeto**: **avaliado e descartado** (peso de TeX Live, fidelidade tipográfica não é prioridade — ver [PHILOSOPHY 4ª prioridade](../../explanation/philosophy.md))
- **Relação com**: alternativa a [Pandoc + Chrome + KaTeX](#pandoc--chrome--katex-atual).

### Tectonic

- **Tipo**: distribuição XeTeX
- **Origem**: tectonic-typesetting
- **Ano**: contínuo
- **Licença**: MIT
- **Refs**: [repo](https://github.com/tectonic-typesetting/tectonic)
- **Sumário**: Single-binary ~50MB, fontes baixadas on-demand. Rust, reproducible builds. Excelente math/tipografia. Boa alternativa ao TeX Live "completo".
- **Status no projeto**: **mapeado para futuro** (Q8 — substituir Chrome+KaTeX sem regressão?)
- **Relação com**: candidato a sair do round-trip via HTML; ver [`papers.md` § Reconstrutores](papers.md#reconstrutores).

### Typst

- **Tipo**: typesetting system
- **Origem**: typst.app
- **Ano**: 2023–
- **Licença**: Apache-2.0
- **Refs**: [typst.app](https://typst.app/) · [quarto docs](https://quarto.org/docs/output-formats/typst.html) · [Quarto issue 11368](https://github.com/orgs/quarto-dev/discussions/11368)
- **Sumário**: Math nativo, single-binary Rust, muito rápido. Conversão LaTeX→Typst de math ainda é imperfeita em 2026.
- **Status no projeto**: **em research** (monitorar; imaturo para math intenso em 2026)
- **Relação com**: alternativa a [Tectonic](#tectonic); discutida via [Quarto](#quarto).

### Quarto

- **Tipo**: framework de publicação (Pandoc + Typst/LaTeX)
- **Origem**: Posit
- **Ano**: contínuo
- **Licença**: MIT
- **Refs**: [quarto.org](https://quarto.org/)
- **Sumário**: Templates polidos. Nada que Pandoc puro não faça, mas útil para templates científicos.
- **Status no projeto**: **referência apenas**
- **Relação com**: aciona [Typst](#typst) ou TeX por baixo.

### WeasyPrint

- **Tipo**: lib Python (HTML/CSS → PDF)
- **Origem**: Kozea
- **Ano**: contínuo
- **Licença**: BSD-3-Clause
- **Refs**: weasyprint.org
- **Sumário**: Sem GPU/Chrome necessário. Math limitada (precisa MathML pré-renderizado; KaTeX server-side OK). Útil se Chrome headless for problema em CI.
- **Status no projeto**: **mapeado para futuro** (alternativa a Chrome em CI)
- **Relação com**: alternativa a [Pandoc + Chrome + KaTeX](#pandoc--chrome--katex-atual).

---

*Total: 27 entradas (17 extratores/OCR-VLM, 4 libs baixo-nível, 6 reconstrutores).*
