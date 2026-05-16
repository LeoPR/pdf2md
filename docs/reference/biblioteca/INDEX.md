# Biblioteca — `pdf2md`

*Catálogo bibliográfico organizado por tipo. Substitui o uso direto de `LITERATURA.md` (v1) e `LITERATURA_v2.md` (v2), que ficam como snapshots históricos.*

Cada referência aparece **uma vez** no arquivo do seu tipo, com ficha catalográfica curta (origem, ano, licença, sumário, status no projeto, links cruzados). Os demais arquivos linkam, não duplicam.

---

## Arquivos

| Arquivo | Conteúdo | # entradas |
|---|---|---:|
| [`ferramentas.md`](ferramentas.md) | Extratores PDF→MD, OCR/VLM, reconstrutores MD→PDF, libs auxiliares | 27 |
| [`benchmarks.md`](benchmarks.md) | Datasets/leaderboards para document parsing | 12 |
| [`metricas.md`](metricas.md) | Métricas de qualidade (WER, TEDS, CDM, LLM-as-judge, bloat_ratio, etc.) | 17 |
| [`papers.md`](papers.md) | Papers temáticos: hallucination, round-trip, reconstrutores, forms | 16 |
| [`glossario.md`](glossario.md) | Termos técnicos centrais (RTT, OCR hallucination, AcroForm, GRPO, etc.) | 14 |

---

## Mapa rápido — onde encontrar

### Ferramentas (`ferramentas.md`)

**Extratores PDF→MD (open-source modernos)**: Marker, MinerU 2.5 / 2.5-Pro, Nougat, olmOCR / olmOCR-2, Docling / Granite-Docling-258M, DeepSeek-OCR, dots.ocr, PaddleOCR-VL, GLM-OCR, Mistral OCR, HunyuanOCR, Qwen3-VL / Qwen3.6, GROBID, pix2tex / LaTeX-OCR, Surya

**OCR/VLM auxiliares & proprietários**: Mathpix, Microsoft Document Intelligence, LayoutLM/v2/v3, FormNet, Donut

**Libs PDF baixo-nível**: pdftotext, PyMuPDF, pypdf, PDFMiner.six

**Reconstrutores MD→PDF**: Pandoc + Chrome + KaTeX (atual), Pandoc + pdflatex/lualatex, Tectonic, Typst, Quarto, WeasyPrint

### Benchmarks (`benchmarks.md`)

OmniDocBench (v1/v1.5/v1.6 Hard/v1.7), DocLayNet, DocBank, PubLayNet, PubTabNet, SciTSR / SciTSR-COMP, DocILE, olmOCR-Bench, Marker bench, Nougat eval, READoc, KIE-HVQA, OCR-Quality

### Métricas (`metricas.md`)

**Primárias (adotadas)**: M1 WER-prosa, M2 LLM-as-judge (fórmulas), M3 TEDS, M4 count-diffs, bloat_ratio (T071)

**Secundárias / diagnóstico**: CDM (rebaixada v1→v2), TEDS-S, GriTS, Header level accuracy, Kendall-τ, Compile-OK, Citation F1, Caption match, SSIM

**Avaliadas / descartadas / mapeadas**: BLEU-LaTeX, TeXBLEU, BoW-WER, FCA, Consensus Entropy, PaIRS, Perplexity / LN-Entropy, Pearson r ranking

### Papers temáticos (`papers.md`)

**Hallucination em OCR/VLM**: Shah et al. 2025 (Seeing is Believing), Zhang et al. 2025 (Consensus Entropy), Risk-Controlled OCR 2603.19790, Nougat §B.3 (repetition), Hallucination Survey 2404.18930, Multimodal Hallucination Survey 2507.19024, Mirage of Hallucination Detection EMNLP 2025

**Round-trip / RTT**: Allamanis et al. 2024 (RTC para código), Moon et al. 2020 (RTT em MT), RTT-LiT 2026, Horn & Keuper 2512.18122 (Copy Lookup Decoding)

**Reconstrutores / typesetting**: Pandoc manual, Tectonic, Typst, Quarto LaTeX→Typst discussion, WeasyPrint

**Forms**: FormNet ACL 2022, LayoutLM family, Donut

---

## Status no projeto — visão geral

| Status | Significado | Exemplos |
|---|---|---|
| **adotado** | em uso no pipeline ou nas decisões registradas | Marker, Pandoc+Chrome+KaTeX, WER-prosa, TEDS, count-diffs, LLM-as-judge, bloat_ratio |
| **avaliado e descartado** | considerado e rejeitado com evidência | CDM como primária (Horn & Keuper 2512.09874), BLEU-LaTeX (Wang et al. 2409.03643), Constrained decoding (GutenOCR 2601.14490), DocILE (out-of-domain), PubLayNet (out-of-domain) |
| **rebaixado** | era primário, virou secundário/diagnóstico | CDM (de M2 primária a secondary), round-trip token similarity (de métrica a health check) |
| **mapeado para futuro** | reservado para próximos experimentos | MinerU 2.5-Pro (Q15), Granite-Docling-258M (Q16), READoc (Q14), Consensus Entropy (Q12), Tectonic (Q8), Nougat (T050), olmOCR-2 (T050) |
| **em research** | identificado mas sem decisão | Typst, Mistral OCR, HunyuanOCR, DeepSeek-OCR, PaddleOCR-VL, dots.ocr, GLM-OCR, Qwen3-VL, PaIRS, SAVIOR |
| **referência apenas** | usado para contextualizar, não para usar | Mathpix (ceiling comercial), Microsoft Doc Intelligence (cloud only), PubLayNet (fora de domínio), GROBID (apenas como second-opinion bibliografia) |

---

## Glossário curto (15 termos centrais)

Glossário completo em [`glossario.md`](glossario.md).

| Termo | Significado curto |
|---|---|
| **Round-trip / RTT** | MD₁ → PDF → MD₂; medir drift. Métrica desencorajada solo, OK como health check. |
| **RTC** | Round-trip correctness; Allamanis 2024 (código) |
| **OCR hallucination** | VLM gera conteúdo plausível mas inexistente em input degradado/esparso |
| **Visual ungrounding** | mecanismo subjacente: decoder textual sobrepuja encoder visual |
| **Repetition hallucination** | Transformer greedy entra em loop (Nougat §B.3) |
| **bloat_ratio** | razão `tokens(MD₂)/tokens(MD₁)`; original do projeto (T071) |
| **AcroForm** | forms PDF 1.2+ como `/AcroForm` dict; lê via pypdf `get_fields()` |
| **XFA** | forms Adobe legacy; depreciado PDF 2.0 |
| **Constrained decoding** | restringir vocab a tokens visíveis; não funciona p/ hallucination semântica |
| **RLVR** | Reinforcement Learning with Verifiable Rewards (olmOCR-2) |
| **GRPO** | Group Relative Policy Optimization; usado em Seeing is Believing |
| **Self-consistency** | múltiplos samples do mesmo modelo, agregar |
| **Consensus Entropy** | self-consistency entre múltiplos VLMs |
| **TEDS** | Tree-Edit-Distance Similarity (tabelas) |
| **CDM** | Character Detection Matching (render fórmula, match bbox) |

---

## Cross-reference com decisões do projeto

| Documento | Papel | Linka biblioteca |
|---|---|---|
| [`../METRICS.md`](../metricas.md) | Painel de métricas adotado | `metricas.md` (M1, M2, M3, M4) |
| [`../PHILOSOPHY.md`](../../explanation/philosophy.md) | Hierarquia conteúdo > estrutura > otimização > formato | — |
| [`../ARQUITETURA.md`](../../explanation/arquitetura.md) | Pipeline atual (Marker + Pandoc + Chrome + KaTeX) | `ferramentas.md` |
| [`../LICENSING.md`](../corpus/licensing.md) | GPL / AGPL / MIT / Apache implicações | `ferramentas.md` |
| `../../tickets/closed/T030_*` | Compilação literatura v1 | gera `LITERATURA.md` |
| `../../tickets/closed/T031_*` | Definição de métricas | gera `../METRICS.md` |
| `../../tickets/closed/T040_*` | Corpus canônico | usa `benchmarks.md` |
| `../../tickets/closed/T050_*` | Baseline marker round-trip 95.09% | usa `metricas.md` |
| `../../tickets/closed/T071_*` | Heurística bloat_ratio | adicionou bloat_ratio em `metricas.md` |
| `../../lab/e03_atkins_wilson_scan/` | Validou bloat em scan_image_only e slides | gerou `bloat_ratio` |

---

## Compilados históricos (snapshots de pesquisa)

- [`../LITERATURA.md`](../../explanation/literatura.md) — v1, 2026-05-10 (T030). Primeira compilação narrativa.
- [`../LITERATURA_v2.md`](../../explanation/literatura.md) — v2, 2026-05-10+. Complementa v1 com alucinação, releases 2025–2026, rebaixa CDM.

Para consulta atualizada, **usar esta biblioteca**. Os compilados ficam como referência para reconstruir o raciocínio em datas específicas.

---

## Convenções

- **Status** segue tabela acima — escolher 1 dos 6 valores.
- **Refs** vai como bullet list de links separados por `·`.
- **Ano** vai como `YYYY` ou `YYYY-MM` quando mês importa (releases).
- **Licença** vai por extenso (`Apache-2.0`, `MIT`, `GPL-3.0`, `AGPL-3.0`, `CC BY-NC 4.0`, `Proprietária`).
- **Relação com** cita tickets (`T031`), experimentos (`lab/e03_*`), e/ou outras entradas (`[Marker](ferramentas.md#marker)`).

Conflitos entre v1 e v2 anotados explicitamente em cada ficha afetada (CDM, round-trip status, Marker version).
