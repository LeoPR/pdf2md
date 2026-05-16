# Métricas — fichas catalográficas

*Métricas de qualidade para PDF→MD: prosa, fórmulas, tabelas, estrutura, citações, imagens, hallucination. Painel adotado pelo projeto está em [`../METRICS.md`](../metricas.md).*

---

## Painel primário (adotado)

### M1. WER-prosa

- **Tipo**: métrica (Word Error Rate sobre prosa mascarada)
- **Origem**: clássica de speech recognition (DARPA anos 90), portada para OCR
- **Ano**: 1990s–contínuo
- **Refs**: [OCR-D spec](https://ocr-d.de/en/spec/ocrd_eval.html) · [reading-order metrics arXiv 2404.18664](https://arxiv.org/html/2404.18664v1)
- **Sumário**: `WER = (S+D+I)/N` sobre corpo de prosa após mascarar fórmulas (`$..$`, `$$..$$`), tabelas, code fences e callouts. Deriva de Levenshtein. Limitações: não distingue tokens de markup, sensível a reading order, ignora estrutura matemática.
- **Status no projeto**: **adotado** (M1 primária; threshold ok ≤ 5%, atenção 5–10%, falha > 10%)
- **Relação com**: camada 1ª (conteúdo) em [`../PHILOSOPHY.md`](../../explanation/philosophy.md); ver [`../METRICS.md` M1](../metricas.md); complemento [WER-bag / BoW-WER](#bow-wer-bag-of-words-wer) para isolar erro de ordem.

### M2. LLM-as-judge (para fórmulas) — primária

- **Tipo**: métrica (avaliação automatizada via LLM)
- **Origem**: Horn & Keuper
- **Ano**: 2025-12
- **Refs**: [arXiv 2512.09874](https://arxiv.org/abs/2512.09874)
- **Sumário**: LLM (Gemini-2.0-flash, GPT-4o) avalia pares (predicted, GT) de fórmulas. Pearson **r=0.78** com humanos em 100 PDFs sintéticos + 2.000 fórmulas + 750 ratings sobre 250 pares. **~2× melhor que [CDM](#cdm-character-detection-matching) (r=0.34)**.
- **Status no projeto**: **adotado** (M2 primária; substitui CDM após v2 update)
- **Relação com**: ver [`../METRICS.md` M2](../metricas.md); top performers no paper: [Qwen3-VL](ferramentas.md#qwen3-vl--qwen36-plus) (9.76/10), Gemini 3 Pro (9.75), [PaddleOCR-VL](ferramentas.md#paddleocr-vl) (9.65), [Mathpix](ferramentas.md#mathpix) (9.64); Marker/Nougat/Docling não avaliados → gap T050; falha geral em métricas single-shot documentada em [Mirage of Hallucination Detection EMNLP 2025](papers.md#mirage-of-hallucination-detection-emnlp-2025).
- **Conflito v1×v2**: v1 recomendava CDM como primária; v2 (Horn & Keuper 2512.09874, 10-dez-2025) rebaixou após mostrar correlação 2× menor com humanos.

### M3. TEDS (Tree-Edit-Distance Similarity) — para tabelas

- **Tipo**: métrica (edit distance sobre árvore HTML)
- **Origem**: Zhong, ShafieiBavani & Yepes (ECCV 2020)
- **Ano**: 2020
- **Refs**: [arXiv 1911.10683](https://arxiv.org/abs/1911.10683)
- **Sumário**: `TEDS(T₁,T₂) = 1 − EditDistance(T₁,T₂) / max(|T₁|,|T₂|)` sobre árvores HTML normalizadas. Padrão de facto para tabelas: OmniDocBench, Marker, Docling, MinerU reportam.
- **Status no projeto**: **adotado** (M3 primária; threshold ok ≥ 0.90, atenção 0.70–0.90, falha < 0.70)
- **Relação com**: introduzido com [PubTabNet](benchmarks.md#pubtabnet); GFM markdown não suporta colspan/rowspan → considerar HTML inline em tabelas complexas (Q5); [Granite-Docling](ferramentas.md#granite-docling-258m) reporta TEDS-S 0.97 FinTabNet; ver [`../METRICS.md` M3](../metricas.md).

### M4. Count-diffs (painel)

- **Tipo**: métrica (diferença bruta de contagem)
- **Origem**: prático (folclore OCR/IE)
- **Ano**: clássico
- **Sumário**: Diferença de contagem entre output e GT (ou input e output em round-trip), por categoria: fórmulas display, fórmulas inline, headers h1-h4, tabelas, imagens referenciadas, citações. Diagnóstico simples mas catastroficamente útil.
- **Status no projeto**: **adotado** (M4 primária; já em `stats.py` parcialmente)
- **Relação com**: camada 1ª + 2ª; threshold "0 para diff" exceto inline (≤5 para drift); detecta dropped formulas, missing headers, missing tables.

### bloat_ratio (T071) — original do projeto

- **Tipo**: métrica (length-ratio detector de hallucination)
- **Origem**: projeto `pdf2md` (Lab e03)
- **Ano**: 2026-05
- **Refs**: ticket T071; experimento `lab/e03_atkins_wilson_scan/`
- **Sumário**: `bloat = tokens(MD₂) / tokens(MD₁)` após round-trip. Heurística T071: flag se `bloat > 3.0` OU (`bloat > 2.0` E `densidade < 200 tok/pág`). Detecta amplification em re-OCR de reconstrução limpa esparsa. Wilson 1800 scan_image_only: 2.748 → 21.177 (7.70×). IBM Quantum lesson 1 slides: 4.629 → 15.637 (3.38×).
- **Status no projeto**: **adotado** (heurística T071 implementada e validada)
- **Relação com**: contribuição metodológica **original** — literatura cobre OCR hallucination *na primeira passada* sobre input degradado ([Shah 2025](papers.md#shah-et-al-2025-seeing-is-believing)) ou via consenso multi-modelo ([Zhang 2025](papers.md#zhang-et-al-2025-consensus-entropy)), mas não a forma amplification-no-round-trip; análogo conceitual ao [Risk-Controlled OCR 2603.19790](papers.md#risk-controlled-ocr-2603-19790); validada em `lab/e03_atkins_wilson_scan/`; Q12 propõe comparar T071-flag com [Consensus Entropy](#consensus-entropy) nos casos rotulados.

---

## Painel secundário (diagnóstico)

### CDM (Character Detection Matching)

- **Tipo**: métrica (visual matching de fórmula renderizada)
- **Origem**: Wang, B. et al. (CVPR 2025)
- **Ano**: 2025
- **Refs**: [arXiv 2409.03643](https://arxiv.org/abs/2409.03643) · [código UniMERNet/cdm](https://github.com/opendatalab/UniMERNet/tree/main/cdm)
- **Sumário**: Renderiza fórmula predita e GT em imagem, faz matching visual de caracteres com bounding boxes via grafo bipartido, calcula F1. 96% de concordância humana vs ~64% de BLEU em 2025.
- **Status no projeto**: **rebaixado** (era M2 primária em v1; agora secondary check em count de fórmulas idênticas)
- **Relação com**: rebaixado por [Horn & Keuper 2512.09874](papers.md#horn-keuper-2512-09874) — falsos positivos em erros estruturais, falsos negativos em símbolos Unicode (`\alpha` vs `α`); substituído por [LLM-as-judge](#m2-llm-as-judge-para-fórmulas-primária) como primária.
- **Conflito v1×v2**: v1 recomendava CDM como métrica primária de fórmula (Threshold ok F1≥0.95). v2 rebaixou após Horn & Keuper (dez/25) mostrarem r=0.34 vs 0.78 do LLM-as-judge. Versão final: CDM permanece útil para count, não para ranking fino.

### TEDS-S (Tree-Edit-Distance só estrutura)

- **Tipo**: métrica (variante TEDS sem texto)
- **Origem**: Zhong et al. (extensão de TEDS)
- **Ano**: 2020
- **Refs**: [arXiv 1911.10683](https://arxiv.org/abs/1911.10683)
- **Sumário**: TEDS ignorando conteúdo das células — só estrutura. Útil para tabelas com merged cells onde texto MD não captura colspan/rowspan.
- **Status no projeto**: **adotado** (secundária; aplicar quando TEDS-S < 0.80 → considerar HTML inline)
- **Relação com**: variante de [TEDS](#m3-teds-tree-edit-distance-similarity-para-tabelas); reportado por [Granite-Docling](ferramentas.md#granite-docling-258m) em FinTabNet (0.97).

### GriTS (Cell-Grid F1)

- **Tipo**: métrica (cell-grid F1 para tabelas)
- **Origem**: (extensão TEDS)
- **Ano**: ~2022
- **Refs**: (paper TableTransformer)
- **Sumário**: F1 sobre grid de células — alternativa a TEDS quando tabelas têm merged cells, que MD não consegue representar fielmente.
- **Status no projeto**: **mapeado para futuro** (alternativa quando TEDS é problemática)
- **Relação com**: alternativa a [TEDS](#m3-teds-tree-edit-distance-similarity-para-tabelas).

### Header level accuracy

- **Tipo**: métrica (% headers com nível `#` correto)
- **Origem**: práticas Marker/Docling
- **Sumário**: Dado que o header foi achado (recall), qual a % com nível `#` correto (1, 2, 3...).
- **Status no projeto**: **adotado** (secundária; aplicar quando M4 dispara em headers)
- **Relação com**: complementa [Kendall-τ reading order](#kendall-τ-reading-order); investiga Q4 (heading drift em livros longos).

### Kendall-τ (reading order)

- **Tipo**: métrica (correlação de ordem)
- **Origem**: clássica estatística
- **Sumário**: Spearman footrule / Kendall-τ sobre sequência de headers ou bag-of-words. Isola erro de ordem do erro de extração. KTDS (em [READoc](benchmarks.md#readoc)) é variante.
- **Status no projeto**: **adotado** (secundária; layouts com sidebar / multi-coluna; Q10)
- **Relação com**: [KTDS no READoc](benchmarks.md#readoc); endereçada por [PaIRS](#pairs-structure-aware-fidelity); ver Q10.

### Compile-OK rate

- **Tipo**: métrica (% fórmulas que compilam)
- **Origem**: práticas de OCR de fórmula
- **Sumário**: % de fórmulas que compilam sem erro (LaTeX → engine). Detecta hallucination estrutural.
- **Status no projeto**: **adotado** (secundária; suspeita de hallucination)
- **Relação com**: em painel com [CDM](#cdm-character-detection-matching) e count-diff; ver [v1 §1.4](../../explanation/literatura.md).

### Citation F1 (Levenshtein normalizado)

- **Tipo**: métrica (F1 sobre referências bibliográficas)
- **Origem**: literatura de bibliographic extraction (Tkaczyk et al.)
- **Ano**: 2018+
- **Refs**: [arXiv 1802.01168](https://arxiv.org/pdf/1802.01168)
- **Sumário**: F1 sobre referências com matching strict/soft/Levenshtein/Ratcliff-Obershelp. [GROBID](ferramentas.md#grobid) reporta F1 0.87–0.90 em PMC/bioRxiv. Para o nosso caso: (i) DOI/arXiv-id se presente, (ii) Levenshtein normalizado sobre `(autor + ano + título)` com threshold 0.85.
- **Status no projeto**: **adotado** (secundária; bibliografias longas; Q9 propõe GROBID como second-opinion)
- **Relação com**: ver [`papers.md` § Tkaczyk](papers.md#tkaczyk-et-al-2018-bibliographic-parsers); referência a [GROBID](ferramentas.md#grobid).

### Caption match (Levenshtein normalizado)

- **Tipo**: métrica (caption ↔ GT)
- **Origem**: práticas de image preservation
- **Sumário**: Levenshtein normalizado caption ↔ GT. Para cada imagem extraída, verificar se há tag/path no MD e se arquivo existe em disco.
- **Status no projeto**: **adotado** (secundária; imagens com legendas-chave)
- **Relação com**: complementa count de imagens em [M4](#m4-count-diffs-painel); Q6.

### SSIM (Structural Similarity Index)

- **Tipo**: métrica (similaridade visual de imagem)
- **Origem**: Wang et al. 2004 (clássica)
- **Sumário**: Comparação visual de imagens renderizadas. Não tentar comparar pixels diretamente no nosso caso — extração já preserva bytes; o que falha é a *associação* texto–imagem e *legenda*.
- **Status no projeto**: **avaliado e descartado** (não comparar pixels; ver v1 §1.7)
- **Relação com**: pode aparecer em rendering-comparison se mudar de [Pandoc + Chrome + KaTeX](ferramentas.md#pandoc--chrome--katex-atual) para [Tectonic](ferramentas.md#tectonic) (Q8).

---

## Avaliadas / descartadas / mapeadas

### BLEU-LaTeX

- **Tipo**: métrica (precision de n-gramas em LaTeX)
- **Origem**: Deng et al. 2017 (image-to-LaTeX); CROHME
- **Ano**: 2017
- **Refs**: ver [Wang et al. 2409.03643](papers.md#wang-et-al-2025-cdm) que documenta falhas
- **Sumário**: Mesma fórmula tem múltiplas representações LaTeX equivalentes (`\frac` vs `\dfrac`), penalizadas como divergentes. Erros numéricos críticos ("1"→"7") podem receber BLEU alto. Recompensa estilo de tokenização similar ao do treino. ~64% concordância humana (vs 96% de CDM em 2025).
- **Status no projeto**: **avaliado e descartado** (BLEU correlaciona mal com humanos em fórmulas)
- **Relação com**: descartado em [v1 §1.3](../../explanation/literatura.md); rebaixado conjuntamente com [CDM](#cdm-character-detection-matching) por [LLM-as-judge](#m2-llm-as-judge-para-fórmulas-primária) (Horn & Keuper r~0 para text-similarity).

### TeXBLEU

- **Tipo**: métrica (BLEU adaptada para LaTeX)
- **Origem**: (paper 2409.06639)
- **Ano**: 2024
- **Refs**: [arXiv 2409.06639](https://arxiv.org/html/2409.06639v2)
- **Sumário**: Adapta BLEU com tokenizer de LaTeX e embeddings de tokens. Melhora correlação mas ainda no nível textual.
- **Status no projeto**: **avaliado e descartado** (rebaixada conjuntamente com BLEU/CDM por LLM-as-judge)
- **Relação com**: variante de [BLEU-LaTeX](#bleu-latex).

### BoW-WER (Bag-of-Words WER)

- **Tipo**: métrica (variante order-independent de WER)
- **Origem**: literatura de reading-order metrics
- **Refs**: [arXiv 2404.18664](https://arxiv.org/html/2404.18664v1)
- **Sumário**: WER ignorando ordem. Útil em paralelo a [WER-prosa](#m1-wer-prosa) para isolar drift de ordem do drift textual.
- **Status no projeto**: **adotado** (em paralelo a M1 — Q10)
- **Relação com**: complementa [M1 WER-prosa](#m1-wer-prosa); usar em Q10 sobre Cohen-Tannoudji-style layouts.

### FCA (Flexible Character Accuracy)

- **Tipo**: métrica (CER order-independent)
- **Origem**: literatura clássica OCR
- **Refs**: [OCR-D spec](https://ocr-d.de/en/spec/ocrd_eval.html) · [arXiv 2404.18664](https://arxiv.org/html/2404.18664v1)
- **Sumário**: CER análoga a BoW-WER. Robusta a reading order.
- **Status no projeto**: **mapeado para futuro** (alternativa em layouts complexos)
- **Relação com**: variante char-level de [BoW-WER](#bow-wer-bag-of-words-wer).

### Consensus Entropy

- **Tipo**: métrica (entropy de inter-model agreement)
- **Origem**: Zhang, K. et al.
- **Ano**: 2025 (v6 mar/26)
- **Refs**: [arXiv 2504.11101](https://arxiv.org/abs/2504.11101)
- **Sumário**: Training-free, model-agnostic. Rodar N VLMs sobre mesmo input; se outputs concordam → low entropy (reliable); divergem → high entropy (unreliable). **+42.1% F1 sobre VLM-as-judge para OCR errors**. CE-OCR (variante adaptive-routing) supera self-consistency.
- **Status no projeto**: **mapeado para futuro** (Q12 — ensemble [Marker](ferramentas.md#marker) + [MinerU](ferramentas.md#mineru-25) + [Nougat](ferramentas.md#nougat) detecta Wilson/IBM Quantum com recall > 0.85?)
- **Relação com**: versão multi-modelo do que [bloat_ratio](#bloat_ratio-t071--original-do-projeto) faz com 1 modelo; novidade v2; ver [`papers.md` § Zhang 2025](papers.md#zhang-et-al-2025-consensus-entropy).

### PaIRS (structure-aware fidelity)

- **Tipo**: métrica (grid 2D row/cell similarity)
- **Origem**: Bhat, R. et al. (WACV 2026)
- **Ano**: 2026
- **Refs**: [WACV paper](https://openaccess.thecvf.com/content/WACV2026W/VisionDocs/papers/Bhat_SAVIOR_Sample-efficient_Adaptation_of_Vision-Language_Models_for_OCR_Representation_WACVW_2026_paper.pdf)
- **Sumário**: Aloca cada palavra numa grid 2D (row, horizontal cell). Mede similarity estrutural beyond transcription. Útil para multi-column e callouts. Limitação: requer modelo prompt-controlled.
- **Status no projeto**: **em research** (não diretamente aplicável a Marker/Nougat default)
- **Relação com**: novidade v2; endereça parcialmente reading order (complementar a [Kendall-τ](#kendall-τ-reading-order)).

### Perplexity / LN-Entropy

- **Tipo**: métrica (sinal de incerteza de modelo)
- **Origem**: literatura LLM
- **Refs**: [Lowest Span Confidence arXiv 2601.19918](https://arxiv.org/html/2601.19918)
- **Sumário**: Perplexity e length-normalized predictive entropy para hallucination em LLMs. **Não usado para OCR/VLM** na literatura padrão.
- **Status no projeto**: **avaliado e descartado** (não aplicável a OCR; nossa heurística [bloat_ratio](#bloat_ratio-t071--original-do-projeto) é alternativa para length-amplification em OCR)
- **Relação com**: justificativa para por que bloat_ratio é defensável; novidade v2.

### Pearson r (ranking)

- **Tipo**: meta-métrica (avaliar correlação entre métricas e humano)
- **Origem**: clássica estatística
- **Sumário**: Coeficiente de correlação linear entre métrica automática e julgamento humano. Usado em [Horn & Keuper](papers.md#horn-keuper-2512-09874) para rebaixar CDM.
- **Status no projeto**: **referência apenas** (não é métrica de extração; meta-métrica de avaliação de métricas)
- **Relação com**: usada em [LLM-as-judge](#m2-llm-as-judge-para-fórmulas-primária) (r=0.78) vs [CDM](#cdm-character-detection-matching) (r=0.34); Q13.

---

## Round-trip (mantido como health check, não primário)

### Round-trip token similarity

- **Tipo**: métrica (SequenceMatcher.ratio sobre tokens normalizados)
- **Origem**: implementação local (`stats.py`)
- **Sumário**: Compara MD₁ vs MD₂ após `MD → PDF → MD'`. Threshold ok ≥ 90%, atenção 80–90%, falha < 80%. Mistura erros do extrator com erros do reconstrutor.
- **Status no projeto**: **rebaixado** (era proxy de qualidade; agora health check / regressão de pipeline)
- **Relação com**: limitação documentada em [Moon et al. 2020](papers.md#moon-et-al-2020-rtt-quality-estimation), [Allamanis et al. 2024](papers.md#allamanis-et-al-2024-round-trip-correctness); ver [`../METRICS.md` § Token similarity](../metricas.md); ver Q1 (gap RT vs GT humano).
- **Conflito v1×v2**: v1 já notava limitações; v2 reforça via [Mirage 2504.18114](papers.md#mirage-of-hallucination-detection-emnlp-2025) e mantém como health check.

### Multi-iteration round-trip drift

- **Tipo**: métrica (drift entre MDᵢ e MD₀ ao longo de N iterações)
- **Origem**: implementação local (`multi_roundtrip.py`)
- **Sumário**: Mede idempotência do pipeline ao longo de 5+ iterações. T050 fechou em 0.86%/iter (estabilidade).
- **Status no projeto**: **adotado** (health check em corpus pequeno, não em toda extração)
- **Relação com**: complementa [round-trip token similarity](#round-trip-token-similarity); roda apenas em 1-2 docs.

---

*Total: 17 entradas (4 primárias adotadas + bloat_ratio original + secundárias + descartadas + round-trip).*
