# Glossário — termos técnicos centrais

*Termos que aparecem em fichas e que precisam definição operacional. Não duplicar conteúdo das fichas: aqui só a definição mínima + ponteiro.*

---

### Round-trip / RTT

Aplicação sequencial `f → g` produzindo `g(f(x))`, comparado contra `x`. No contexto pdf2md: **MD₁ → PDF → MD₂**. Métrica round-trip = similaridade(MD₁, MD₂). Genérica para qualquer par `(f, g)` de conversões inversas.

- **Status**: técnica conhecida; rebaixada a *health check* — não é proxy direto de qualidade.
- **Mais em**: [`metricas.md` § Round-trip token similarity](metricas.md#round-trip-token-similarity); [`papers.md` § Moon et al. 2020](papers.md#moon-et-al-2020-rtt-quality-estimation).

### RTC (Round-Trip Correctness)

Variante de round-trip aplicada a *código*: descrever em NL → re-sintetizar → checar equivalência semântica. Allamanis et al. 2024. Correlaciona com qualidade *quando há verificador semântico downstream*.

- **Mais em**: [`papers.md` § Allamanis et al. 2024](papers.md#allamanis-et-al-2024-round-trip-correctness).

### OCR hallucination

Fenômeno em que OCR/VLM produz conteúdo plausível mas inexistente. Subtipo "phantom content" / "visual ungrounding". Causa típica: input degradado (blur, contraste) ou — caso pdf2md — input legítimo mas **esparso** (poucos tokens visíveis).

- **Mais em**: [`papers.md` § Shah et al. 2025](papers.md#shah-et-al-2025-seeing-is-believing); [`metricas.md` § bloat_ratio](metricas.md#bloat_ratio-t071--original-do-projeto).

### Visual ungrounding / language prior over-reliance

Mecanismo subjacente da OCR hallucination: em VLMs encode-then-decode, o decoder textual sobrepuja o encoder visual quando o sinal visual é fraco. Modelo "preenche o vazio percebido" com formulações típicas do corpus de treino.

- **Mais em**: [`papers.md` § Shah et al. 2025](papers.md#shah-et-al-2025-seeing-is-believing); Datature 2025 (referência em LITERATURA_v2 §1.1).

### Repetition hallucination

Caso degenerativo: Transformer com greedy decoding entra em loop, repetindo última sentença. Detectado em Nougat §B.3 (1.5% das páginas in-domain). Distinto de amplification semântica (bloat_ratio).

- **Mais em**: [`papers.md` § Nougat §B.3](papers.md#nougat-b3--repetition-hallucination).

### bloat_ratio

Métrica original do projeto (T071, lab/e03). Razão `tokens(MD₂) / tokens(MD₁)` no round-trip. Detecta amplification: input esparso → re-OCR alucina conteúdo. Heurística: flag se `bloat > 3.0` OU (`bloat > 2.0` E `densidade < 200 tok/pág`).

- **Mais em**: [`metricas.md` § bloat_ratio](metricas.md#bloat_ratio-t071--original-do-projeto).

### AcroForm

Forms em PDF 1.2+ implementados como objetos `/AcroForm` no PDF dictionary; campos `/Fields` com valor (`/V`) string ou número. Acessível via [pypdf](ferramentas.md#pypdf) `reader.get_fields()`. Quando tratado como texto comum no pipeline OCR, sofre drift severo (IRS f1040: round-trip 46%).

- **Mais em**: [`papers.md` § Forms](papers.md#forms--structured-documents); [`ferramentas.md` § pypdf](ferramentas.md#pypdf).

### XFA

Forms Adobe legacy implementados como XML separado. Depreciado em PDF 2.0 mas ainda em uso (governo, jurídico). Conversão para AcroForm via Foxit/Aspose (proprietário) ou aceitar perda.

- **Mais em**: LITERATURA_v2 §4.1; [Wikipedia XFA](https://en.wikipedia.org/wiki/XFA).

### Constrained decoding

Mitigação de hallucination que restringe vocabulário do decoder a tokens visíveis no input. **Falhou na prática** — VLMs persistem em gerar tokens ausentes do input visível ([GutenOCR 2601.14490](papers.md#gutenocr-2601-14490)).

- **Status**: avaliado e descartado para hallucination semântica.
- **Mais em**: [`papers.md` § GutenOCR](papers.md#gutenocr-2601-14490).

### RLVR (Reinforcement Learning with Verifiable Rewards)

Treinamento por RL onde a recompensa vem de testes determinísticos (unit tests, e.g. "table structure preserved", "math faithfully transcribed"). Usado em olmOCR-2 via [GRPO](#grpo). Eleva olmOCR-Bench de 78.5 → 82.4.

- **Mais em**: [`ferramentas.md` § olmOCR-2](ferramentas.md#olmocr-2); [`papers.md` § (olmOCR-2 paper, ref 2510.19817)].

### GRPO (Group Relative Policy Optimization)

Algoritmo de RL post-training usado em Seeing is Believing (NeurIPS 2025) com reward de "refusal to answer" em regiões ambíguas — +22pp absoluto em hallucination-free accuracy sobre GPT-4o. Também usado em [olmOCR-2](ferramentas.md#olmocr-2) para [RLVR](#rlvr).

- **Mais em**: [`papers.md` § Shah et al. 2025](papers.md#shah-et-al-2025-seeing-is-believing).

### Self-consistency

Geração de múltiplos samples do mesmo modelo, agregar por consenso. Base teórica do que [Consensus Entropy](#consensus-entropy) generaliza para múltiplos modelos.

- **Mais em**: [`metricas.md` § Consensus Entropy](metricas.md#consensus-entropy).

### Consensus Entropy

Métrica training-free, model-agnostic: rodar N VLMs sobre mesmo input; se outputs concordam → low entropy (reliable); divergem → high entropy. +42.1% F1 sobre VLM-as-judge para OCR errors. Versão multi-modelo do que [bloat_ratio](#bloat_ratio) faz com 1 modelo.

- **Mais em**: [`metricas.md` § Consensus Entropy](metricas.md#consensus-entropy); [`papers.md` § Zhang et al. 2025](papers.md#zhang-et-al-2025-consensus-entropy).

### TEDS (Tree-Edit-Distance Similarity)

`TEDS(T₁,T₂) = 1 − EditDistance(T₁,T₂) / max(|T₁|,|T₂|)` sobre árvores HTML. Métrica padrão de facto para tabelas. Variantes: **TEDS-S** (só estrutura), **TEDS-content** (estrutura + conteúdo).

- **Mais em**: [`metricas.md` § M3 TEDS](metricas.md#m3-teds-tree-edit-distance-similarity-para-tabelas); [`papers.md` § Zhong et al. 2020](papers.md#zhong-et-al-2020-teds--pubtabnet).

### CDM (Character Detection Matching)

Renderiza fórmula predita e GT em imagem, faz matching visual de caracteres com bounding boxes, calcula F1. 96% concordância humana (vs 64% de BLEU em 2025). **Rebaixada em 2025-12** por LLM-as-judge (Horn & Keuper: r=0.34 vs r=0.78).

- **Mais em**: [`metricas.md` § CDM](metricas.md#cdm-character-detection-matching).

---

*Total: 14 termos.*
