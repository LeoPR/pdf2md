# Tecnologias — perfis cross-recursos

> *Snapshot 2026-05-16 (v0.7.0). Compila perfis das ferramentas e algoritmos
> em uso, com dados empíricos dos labs e09-e14 (RTX 3060 / i7-6850K / 128 GB
> RAM). Valores absolutos variam por máquina; razões e complexidades não.
> Articula o "mapa" da arquitetura `instrumento → mapa → roteador` (ver
> [PHILOSOPHY](../explanation/philosophy.md), tickets [T085](../../tickets/closed/T085_telemetry_module.md),
> [T090](../../tickets/research/T090_macro_intent_routing.md)).*

## Sumário executivo

Quatro perfis distintos emergem dos labs:

| Tipo | Exemplo | Tempo | Mem peak | GPU | Quando preferir |
|---|---|---:|---:|---|---|
| **GPU-bound ML pesado** | marker-pdf, pix2tex | 5-10 min / 50pg | 4-8 GB VRAM | sim | qualidade máxima |
| **CPU-bound paralelo** | PyMuPDF render @ 150dpi | ~4s / 50pg | <200 MB | não | sempre que viável |
| **CPU-bound single-thread** | scikit-image SSIM | ~22s / 50pg | ~320 MB | não | só quando necessário (`--best`) |
| **I/O-bound subprocess** | pandoc + Chrome | ~13s independente | <150 MB | não | reconstrução (incontornável) |

Recomendação inicial de **macro-intents** (T090):

| Intent | Stack | Tempo esperado / livro 50pg |
|---|---|---:|
| `--rapido` | marker → MD; sem optimize; rt-pixel `--skip-ssim` | ~6 min |
| `--default` | + optimize + stats | ~8 min |
| `--qualidade` | + rt-pixel full + multi-rt | ~12 min |
| `--best` | tudo + diversidade reconstrutores (futuro) | ~20 min |

---

## 1. Camada de extração (PDF → MD)

### 1.1 Em uso: `marker-pdf 1.10.2` (GPU)

| Vetor | Valor | Como medido |
|---|---|---|
| Wall-time | ~7 min / 49 pgs (cap 4 N&C) | smoke test produção 2026-05-13 |
| Wall-time normalizado | ~8.5s / página | mesmo run, dividido |
| RAM peak | ~3 GB | psutil (e10 instrumentado) |
| VRAM peak | ~3.4 GB (RTX 3060 12GB) | nvidia-smi via pdf2md.telemetry |
| GPU util média | 40-60% | observação durante extract |
| Stack interna | Surya (layout/OCR) + Equation + Texify | upstream `datalab-to/marker` |
| Round-trip mediano | 95.09% (cap 4 N&C, e00 baseline) | T050 baseline |
| Licença | GPL-3 (uso permitido, redistribuição cuidadosa) | github.com/datalab-to/marker |

**Pontos fortes:**
- Math LaTeX nativamente extraído via Texify
- GPU 12 GB cobre livro inteiro sem quebra
- 100% determinístico com seed fixo

**Pontos fracos:**
- Escapa automaticamente `_`, `*`, `[`, etc. em texto (penaliza round-trip textual; pegou Q11.b AcroForm — ver [LITERATURA_v2 §4](../explanation/literatura.md))
- Pode alucinar em re-OCR de PDF esparso (heurística T071 detecta — bloat ratio > 2.0× + densidade < 200 tokens/pg)
- Sem fallback CPU prático (Surya não roda decentemente sem GPU)

### 1.2 Alternativas testadas (não promovidas)

| Tool | Lab | Resultado | Por quê descartado | Recuperável? |
|---|---|---|---|---|
| Marker `--use_llm` + `llama3.2-vision:11b` via Ollama | [e07](../../lab/e07_marker_llm/RESULT.md) | descartado | 40× mais lento, ganho zero em N&C; bugs do Ollama (servidor crasha) | Sim — outro modelo VLM via outra tool poderia render |
| MinerU 2.5-Pro (Q15) | [e06](../../lab/e06_mineru25_pro/RESULT.md) | **blocked** | uv install OK; FastAPI server crasha silenciosamente em Win+RTX 3060 | Investigação aberta — pode rodar em Linux ou via API direta |
| Granite-Docling-258M (Q16) | [e08](../../lab/e08_granite_docling/RESULT.md) | descartado | tempo 50× pior; imagens em base64 inline; LaTeX verboso | Sim para casos curtos / single-file output / sem GPU |

**Padrão metodológico:** todos os descartes nomeiam o modelo+tool+corpus específico. "LLM em geral" não é avaliado — só `llama3.2-vision:11b` via Ollama em N&C cap 4. Ver [feedback memory escopo-de-conclusao](#).

### 1.3 No roadmap

| Tool | Por quê interessante | Ticket | Status |
|---|---|---|---|
| Nougat | math-heavy benchmark histórico | [T410](../../tickets/research/T410_testar_ferramentas_alternativas_nougat_mineru_pdftotext.md) | research |
| olmOCR-2 | RLVR com unit tests; Apache-2.0 | T410 | research |
| Docling (full) | F1 0.968 em equações (Granite version) | T410 | research |
| pdftotext / PyMuPDF puro / Tesseract | fallback low-resource sem GPU/ML pesado | [T420](../../tickets/research/T420_fallback_low_resource_sem_gpu_sem_modelos_ml_pesados.md) | research |
| pix2tex | extração específica de fórmulas-imagem | [T134](../../tickets/research/T134_pix2tex_formulas.md) | research |

---

## 2. Camada de otimização (raster → representação semântica)

### 2.1 Em uso: `pdf2md.optimize` (níveis 1-2 do eixo de representação)

| Vetor | Valor | Como medido |
|---|---|---|
| Wall-time | ~3s / 25 imagens (cap 4 N&C) | smoke test produção |
| RAM peak | <100 MB | PIL operações in-memory |
| GPU | não usa | — |
| Economia média | -38.6% no N&C, -43.1% no cap 4 | T131 closed |
| Stack interna | PIL `quantize` + `getcolors` + lossy gate (median diff < 5/255) | `pdf2md/optimize.py` |
| Licença | MIT (pdf2md), HPND (PIL) | — |

**O que faz:**
- ≤2 cores únicas → PNG 1-bit
- ≤16 cores únicas → PNG paleta indexada
- >16 cores + quantize-com-perda aceitável → PNG paleta lossy (anti-aliasing/JPEG noise)
- Caso contrário → mantém JPEG original

**Limites:**
- Nível 3 (SVG via potrace) não implementado — perde line art editável
- Nível 4 (texto+fonte+brasão) não implementado — logos viram bitmap
- Nível 5 (fórmula → LaTeX em imagem) — só via marker upstream

### 2.2 No roadmap

| Capacidade | Ticket | Estado |
|---|---|---|
| SSIM gate antes de aceitar conversão | [T135](../../tickets/research/T135_ssim_gate_qualidade.md) | research |
| Line art → SVG via potrace | [T132](../../tickets/research/T132_potrace_svg_line_art.md) | research |
| Detector + extrator fórmula→LaTeX | [T133](../../tickets/research/T133_detector_de_formula.md) + [T134](../../tickets/research/T134_pix2tex_formulas.md) | research |
| Denoise JPEG antes da compressão | [T137](../../tickets/research/T137_denoising_jpeg_pre_compressao.md) | research |
| Reconstrução vetorial logos (Nível 4) | [T180](../../tickets/open/T180_reconstrucao_vetorial_imagens.md) | open — escopo small-image refinado pós-e16/e17 |

---

## 3. Camada de reconstrução (MD → PDF)

### 3.1 Em uso: `pandoc 3.9` + Chrome headless + KaTeX

| Vetor | Valor | Como medido |
|---|---|---|
| Wall-time | ~13s / capítulo médio | e10 telemetria |
| CPU usage médio | 6% (I/O-bound) | espera pandoc + chrome subprocess |
| Wall vs CPU | cpu_s 0.94s, wall 13.5s → **>90% tempo é wait** | e10 |
| RAM peak | ~100 MB (process pdf2md); Chrome separado | psutil |
| GPU | não usa | — |
| Output | A4, Segoe UI 10.5pt, margens 2cm, KaTeX para math | CSS_INLINE em `pdf2md/pdfs.py` |

**Custo de mudar:** alto. CSS calibrado para N&C; trocar engine muda layout-fingerprint e quebra reproduções históricas.

### 3.2 No roadmap (para calibração T072)

| Tool | Por quê | Status |
|---|---|---|
| Tectonic (TeX moderno) | Diversidade — detectar perda do reconstrutor atual | research (T072) |
| Typst | Engine moderno open-source | research (T072) |
| WeasyPrint | HTML/CSS engine alternativo | research (T072) |
| Quarto (pandoc + Typst/LaTeX) | Stack academic-friendly | research (T072) |

---

## 4. Camada de validação (métricas)

### 4.1 Em uso

| Métrica | Custo wall-time | Stack | Quando aplicar |
|---|---|---|---|
| **Round-trip textual** (`SequenceMatcher`) | ~3s / 50pg após render | difflib stdlib | sempre — health check |
| **bloat_ratio** | trivial | aritmética | sempre — detecção alucinação (T071) |
| **count-diffs** (math, headers, tables, imgs) | trivial | regex | sempre |
| **Pixel-roundtrip macro SSIM** | ~22s / 50pg | scikit-image | opt-in (`--rt-pixel`) |
| **Pixel-roundtrip médio WER** (align Hungarian + WER) | ~3s / 50pg | scipy + difflib | opt-in junto com macro |
| **Multi-iter drift** | N × custo single rt | — | só corpus pequeno (e09) |

### 4.2 Comparação dos vértices do triângulo (pixel-roundtrip)

| Vértice | Métrica | Tempo p/ 50pg | Discrimina? | Decisão |
|---|---|---:|---|---|
| **Macro** | SSIM global por par | 22s | sim (median 0.6 cross-doc) | **mantém** |
| Médio (bbox IoU geom) | bbox IoU per-page | ~3s | **não** (~0 sempre — coords diferem) | **dropado** (e10) |
| Médio (fingerprint pareado) | Hungarian sobre fingerprints | ~3s | parcial (cov<30%) | **dropado** (e11) |
| **Médio (page-WER após align)** | WER global p/ par alinhado | ~3s | sim (median 0.38 cross-doc) | **mantém** |
| Micro (block-a-block) | WER por par de blocks | n/a | **não** (fragmentação) | **dropado** (e11) |

Triângulo final: **macro SSIM + médio WER (após align)**. Micro descartado.

### 4.3 No roadmap

| Métrica | Ticket | Por quê |
|---|---|---|
| WER-prosa M1 (com mascaramento markup) | [METRICS.md M1](metricas.md) | Primary content-only |
| TEDS M3 (tabelas) | METRICS.md M3 | Estrutura tabular |
| LLM-as-judge para fórmulas | LITERATURA_v2 §5.2 | substitui CDM (rebaixado) |
| Calibração do reconstrutor (ruído base) | [T072](../../tickets/research/T072_calibracao_reconstrutor.md) | isola erro extração vs reconstrutor |
| GT humano em mini-corpus (5-10 pgs) | [T060](../../tickets/open/T060_mini_corpus_gt_humano.md) | destrava T072 e validação não-circular |

---

## 5. Infra / instrumentação

### 5.1 `pdf2md.telemetry` (v0.5, T085 closed)

| Campo capturado | Como |
|---|---|
| wall_s | `time.perf_counter` |
| cpu_s, cpu_pct_mean, cpu_pct_peak | `psutil.cpu_times` + amostragem em thread (0.5s) |
| rss_peak_mb, rss_delta_mb | `psutil.memory_info` amostrado |
| py_peak_mb | `tracemalloc.get_traced_memory` |
| gpu_vram_peak_mb, gpu_vram_delta_mb | `nvidia-smi` polling (sem dep torch) |
| gpu_util_pct_mean | idem |
| io_read_mb, io_write_mb | `psutil.io_counters` |
| threads_peak | `psutil.num_threads` |

Overhead validado < 1% wall-time (e10). Funciona sem GPU (campos None).

### 5.2 `pdf2md.pixel_roundtrip` (v0.6, T070 promovido parcial)

- Alinhamento Hungarian (default) sobre matriz WER per-page
- Alinhamento DTW alternativo (monotônico, para reflow grande)
- Macro SSIM via scikit-image grayscale
- Médio WER após alinhamento (não block-a-block — e11 descartou)
- Flags por página (`high_wer`, `medium_ssim`, etc.) com thresholds calibrados (WER<0.30 ótimo, <0.60 tolerável; SSIM>0.95 ótimo, >0.50 tolerável)
- 110 tests cobrindo

---

## 6. Dados empíricos cross-PDF (lab/e14)

| Doc | Categoria | Pages orig/rend | WER med | %<0.60 | SSIM med | Mono |
|---|---|---:|---:|---:|---:|:-:|
| arxiv_1706 (Attention) | paper LaTeX 2-col | 15/15 | **0.258** | 86.7% | 0.639 | ✗ |
| cap4 N&C (baseline e13) | livro LaTeX 1-col | 45/49 | 0.376 | 91.1% | — | ✗ |
| preskill_ph219 | notes LaTeX 1-col | 54/46 | 0.395 | 87.0% | 0.610 | ✓ |
| cdc_mmwr | gov multi-col, sem math | 5/9 | 0.421 | 80.0% | 0.533 | ✓ |

Faixa de WER mediano 0.26-0.42 em todas. Nenhum doc atinge SSIM 0.95 (esperado:
pdf2md CSS é visualmente distinto do source).

**Padrão emergente sobre monotonicidade:**
- N==M (mesmo nº pgs): Hungarian tende a inversões locais ótimas (`monotonic=False`)
- N≠M significativo: Hungarian fica monotônico naturalmente (drift é caminho barato)

---

## 7. Tradeoffs explícitos do projeto

Reusando os eixos do [PHILOSOPHY §"Tradeoffs explícitos"](../explanation/philosophy.md):

| Eixo | Ponta atual | Possível mover para... | Quando |
|---|---|---|---|
| Velocidade ↔ qualidade | marker GPU (default) | marker + pix2tex + multi-rt | usuário pedir `--qualidade` |
| Heurístico ↔ ML | regex em count-diffs | LLM-as-judge para fórmulas | Q13 confirmar Pearson r > 0.6 |
| Mono-tool ↔ ensemble | marker só | + Nougat / olmOCR / Docling ensemble | Q12 / Consensus Entropy validar |
| Mono-reconstrutor ↔ múltiplo | pandoc+Chrome+KaTeX | + Tectonic/Typst para calibração | T072 (precisa T060 GT) |
| Nível baixo ↔ alto (representação) | PNG paleta (2) | SVG line art (3) → LaTeX (5) | T132/T134 |
| Determinismo ↔ adaptatividade | seed fixo + escolhas hardcoded | macro-intent profile-aware | T090 |
| Acoplamento ↔ modularidade | marker monolítico | image2sem separado | T160/T180 |

---

## 8. O que falta para o "roteador" (T090)

Para macro-intent CLI (`--rapido`/`--qualidade`/`--auto`) virar real, precisa:

1. **Mais perfis no mapa** — hoje temos só marker (extração), pandoc+chrome (reconstr), pix-rt (validação). Faltam pix2tex, potrace, alt-tools.
2. **Auto-detect de hardware** — `HostInfo.detect()` em `pdf2md doctor` já lê GPU/RAM; integrar com routing.
3. **Schema de perfil em YAML** — algo como `docs/profiles/<tool>.yaml` com complexity + thresholds.
4. **Função `route(intent, profile_map, host, doc)`** → pipeline concreto.

Hoje os labs e09-e14 produziram **3-4 perfis sólidos**. T090 ainda research; estimar 2-3 sessões para virar código.

---

## 9. Glossário rápido

| Termo | Significado |
|---|---|
| **L0 / L0.5 / L1-L5** | Níveis da arquitetura recursiva ([PHILOSOPHY](../explanation/philosophy.md)). L0=doc, L0.5=doc visual, L1=figura→vetor, L2=fórmula→LaTeX, L3=tabela, L4=logo (texto+brasão), L5=CAD (out-of-scope) |
| **Bloat ratio** | tokens(MD₂) / tokens(MD₁) no round-trip. > 2× é sinal de alucinação |
| **Round-trip textual** | MD₁ → PDF → MD₂; comparar via SequenceMatcher |
| **Pixel-roundtrip** | PDF_orig → render → img; comparar com img de PDF₁ = MD→PDF (T070) |
| **Triângulo macro/médio/micro** | Decomposição da métrica visual em níveis de granularidade ([PHILOSOPHY](../explanation/philosophy.md)) |
| **Frente A-E** | Cobertura do conversor (Validação, Textual, Estrutural, Otimização, Vetorial — ver [ROADMAP](../../ROADMAP.md)) |
