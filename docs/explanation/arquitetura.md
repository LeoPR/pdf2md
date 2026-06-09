# Arquitetura — `pdf2md`

*Visão consolidada do conceito, das camadas e das ferramentas (v0.7.0, 2026-05-17).
Para detalhes por camada, ver [`arquitetura/`](arquitetura/). Perfis cross-recursos
em [`TECNOLOGIAS.md`](../reference/tecnologias.md).*

> **Atualização 2026-06-09:** este doc precede a integração do caminho CPU + roteador.
> Já **implementado/fechado**: o ROTEADOR macro-intent (T090 — `routing.py` + `executor.py`
> + `_profiles.py`), os PRIMARYs CPU `extractors.py` (pdftotext/tesseract), o cropper de
> fórmula CPU `formula_cropper.py` + pix2tex, e `discovery.py` (descoberta portável). Onde a
> Camada 1 listar pdftotext/tesseract/pix2tex como "ALT/futuro" ou a §6 listar "macro-intent
> CLI (T090)" como pendente, **leia como entregue**. Ver [README](../../README.md) e
> [`tickets/closed/T090…`](../../tickets/closed/T090_macro_intent_routing.md).

---

## 1. Conceito abstrato

O `pdf2md` opera num **fluxo de 4 camadas** com **round-trip duplo** (textual e visual)
como **validador permanente**:

```
                          ┌────────── ROUND-TRIP (validador) ──────────┐
                          │                                            │
                          ▼                                            │
   ┌─────────┐  Cam 1     ┌─────────┐  Cam 3     ┌─────────┐  Cam 1    ▼
   │   PDF   │ extração   │   MD    │ reconstr.  │  PDF'   │ extração  ┌─────────┐
   │   in    │───────────▶│   1ª    │───────────▶│  inter  │──────────▶│   MD'   │
   └─────────┘            └─────────┘            └─────────┘           └─────────┘
                               │                                            │
                               │              Cam 2                         │
                               │       (otimização de                       │
                               │        representação                       │
                               │        de imagens — opt.)                  │
                               │                                            │
                               └──────────── Cam 4: compare ────────────────┘
                                                  │
                                          similarity %, divergências
```

### O que cada camada faz

| Camada | Função | Estado atual | Detalhes |
|---|---|---|---|
| **1 — Extração** | PDF → texto + estrutura + imagens + fórmulas | marker-pdf 1.10.2 (GPU RTX 3060) | [`arquitetura/01_extracao.md`](arquitetura/01_extracao.md) |
| **2 — Otimização** | Imagens raw → representação mais semântica | `pdf2md.optimize` (PNG paleta lossy/1-bit, T131 closed) | [`arquitetura/02_otimizacao.md`](arquitetura/02_otimizacao.md) |
| **3 — Reconstrução** | MD → PDF visualizável | pandoc 3.9 + Chrome headless + KaTeX | [`arquitetura/03_reconstrucao.md`](arquitetura/03_reconstrucao.md) |
| **4 — Métrica** | Textual (MD vs MD') + Visual (PDF render-render comparado) | textual: `SequenceMatcher` + bloat_ratio. Visual: `pdf2md.pixel_roundtrip` (align Hungarian + SSIM + WER) | [`arquitetura/04_metricas.md`](arquitetura/04_metricas.md) |
| **Pipeline + Instrumento** | Orquestração + telemetria por step | `pdf2md/{cli,stats,roundtrip,pixel_roundtrip,telemetry,...}.py` | [`arquitetura/05_pipeline.md`](arquitetura/05_pipeline.md) |

### Por que round-trip

Round-trip captura uma propriedade **mensurável** sem precisar de ground-truth: se MD → PDF → MD' converge, o pipeline preserva informação. Não é prova de fidelidade (literatura ressalta — ver [`LITERATURA.md §4`](literatura.md)), mas é health-check excelente. Para fidelidade real, complementar com GT humano (T060 futuro).

---

## 2. As 4 camadas em detalhe

```
┌──────────────────────────────────────────────────────────────────────┐
│ Camada 1 — EXTRAÇÃO                                                  │
│ ────────────────────                                                 │
│                                                                      │
│ ATUAL    │ marker-pdf 1.10.2 (GPU)                                   │
│          │ ├─ Surya (layout, OCR, reading order)                     │
│          │ ├─ Equation (math detection)                              │
│          │ └─ Texify (math → LaTeX)                                  │
│ ALT.     │ Nougat · MinerU 2.5 · olmOCR-2 · Docling · GROBID (T410)  │
│ MATH-OCR │ pix2tex (T134 — fórmulas específicas)                     │
│ FALLBACK │ pdftotext · PyMuPDF puro · tesseract (T420)               │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Camada 2 — OTIMIZAÇÃO DE REPRESENTAÇÃO                               │
│ ──────────────────────────────────────                               │
│                                                                      │
│ ATUAL    │ optimize_images.py (T131 ✓ −38.6% em N&C)                 │
│          │ ├─ PIL: classify por cores únicas                         │
│          │ ├─ PNG 1-bit (≤2 cores)                                   │
│          │ ├─ PNG paleta indexada (≤16 cores)                        │
│          │ └─ JPEG mantido (>16 cores / continuous tone)              │
│ FUTURO   │ T132 potrace (SVG) · T134 pix2tex (LaTeX)                 │
│          │ T135 SSIM gate · T136 ✓ breakdown formato                 │
│          │ T137 denoise JPEG · T180 reconstrução vetorial            │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Camada 3 — RECONSTRUÇÃO (MD → PDF)                                   │
│ ─────────────────────────────────                                    │
│                                                                      │
│ ATUAL    │ pandoc 3.9 → HTML (com KaTeX) → Chrome headless → PDF     │
│ ALT.     │ Tectonic (TeX moderno) · Typst · WeasyPrint               │
│          │ Quarto (Pandoc + Typst/LaTeX)                             │
│          │ (avaliar em experimento futuro)                           │
└──────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Camada 4 — MÉTRICA / VALIDAÇÃO (textual + visual)                    │
│ ──────────────────────────────────────────────                       │
│                                                                      │
│ TEXTUAL  │ SequenceMatcher token similarity (`pdf2md.roundtrip`)     │
│          │ + 8 categorias de divergência (math, heading, emphasis,   │
│          │   table, image_ref, separator, whitespace, other)         │
│          │ + bloat_ratio (T071: detector de alucinação)              │
│ VISUAL   │ `pdf2md.pixel_roundtrip` (v0.6, T070 promovido parcial):  │
│          │ - Alinhamento Hungarian (default) / DTW (monotônico)      │
│          │ - Macro SSIM por par alinhado                             │
│          │ - Médio WER da página (após alinhamento)                  │
│          │ - Micro block-a-block DESCARTADO (e10/e11 provaram que    │
│          │   fragmentação incompatível com reflow)                   │
│ INSTRUM. │ `pdf2md.telemetry` (v0.5, T085): wall/cpu/mem/gpu/io      │
│          │ por step. Overhead < 1%. Sem dep torch obrigatória.       │
│ FUTURO   │ M1 WER-prosa mascarado · M3 TEDS · LLM-as-judge (CDM      │
│          │   rebaixado em LITERATURA_v2 §5.2) · GT humano (T060)     │
│          │   · Calibração reconstrutor (T072, depende T060)          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Eixo de representação (transversal)

Em paralelo às 4 camadas acima, cada elemento extraído pode subir/descer na escala de representação (definida em [`PHILOSOPHY.md`](philosophy.md)):

```
Nível 1 ──────────────────────────────────────────────────▶ Nível 5
[raster                                                    [texto
 arbitrário]                                                semântico]

JPEG/PNG       PNG paleta      SVG vetor        texto+fonte+        LaTeX
arbitrário     lossless        (line art)       brasão residual     MD
   |              |                |                  |                |
   |        T131 ✓ (−38.6%)        |          T160+T180 (Frente E)    |
   |                            T132                                  T134
   ▼              ▼                ▼                  ▼                ▼
   1              2                3                  4                5

   └─ baixa ──────┴────────────────┴──────────────────┴──── alta ─────┘
              ↑ compactação · editabilidade · buscabilidade ↑
```

**Regra de operação**: subir para o nível mais semântico que **não viola a 1ª prioridade** (conteúdo).

---

## 4. Mapeamento Frente × Camada × Ticket

| Frente | Camada 1 (Extração) | Camada 2 (Otimização) | Camada 3 (Reconstrução) | Camada 4 (Métrica) |
|---|---|---|---|---|
| **A** Validação | — | — | — | T050 ✓ T060 |
| **B** Textual | T101 ✓ · T160 | — | — | — |
| **C** Estrutural | T102 ✓ · T106 ✓ | T132 · T133 · T134 | — | — |
| **D** Otimização | — | T131 ✓ · T135 · T136 ✓ · T137 | — | — |
| **E** Vetorial | — | T180 | — | — |
| **Alt-tools** (T410) | Nougat · MinerU · olmOCR · Docling | — | — | — |
| **Empacotamento** | — | — | T107 · T108 | — |

Símbolos: ✓ closed; sem símbolo = research/open. Lista completa de tickets em [`../../tickets/INDEX.md`](../../tickets/INDEX.md).

---

## 5. Pipeline atual (orquestração)

Pacote `pdf2md/` em [`../../src/pdf2md/`](../../src/pdf2md/) com 10 módulos:

```
src/pdf2md/
├── cli.py              ← Typer app: macro convert + 11 subcomandos
├── normalize.py        ← Token-stream canônico para comparação
├── provenance.py       ← Marcador idempotente (HTML comment + blockquote)
├── stats.py            ← Cam 4: telemetria + métricas
├── aggregate.py        ← Cam 4: agregação multi-doc (_OVERVIEW)
├── roundtrip.py        ← Cam 1+3+4: MD → PDF → MD' → compare textual
├── multi_roundtrip.py  ← Cam 4: N iterações de round-trip
├── pdfs.py             ← Cam 3: md_to_pdf (v0.4.1: out_pdf + overwrite=False)
├── restructure.py      ← Cam 1 pós: split MD por TOC
├── optimize.py         ← Cam 2: PNG paleta lossy / 1-bit / JPEG
├── telemetry.py        ← v0.5 T085: wall/cpu/mem/gpu/io por step
└── pixel_roundtrip.py  ← v0.6 T070: align + macro SSIM + médio WER
```

Shims de back-compat em `src/*.py` (13 linhas cada) preservam invocação
standalone histórica (`python src/stats.py FOLDER`, etc.).

CLI subcomandos (v0.7.0):

| Subcomando | Função |
|---|---|
| `pdf2md convert FILE.pdf [flags]` | macro one-shot inteligente (auto-detect via TOC) |
| `pdf2md extract / restruct / optimize / stats / prov` | etapas isoladas do pipeline |
| `pdf2md rt / rt-multi` | round-trip textual single ou iterativo |
| `pdf2md rt-pixel ORIG RENDER` | round-trip visual (Hungarian + SSIM + WER) |
| `pdf2md pdfs DIR` | bulk MD → PDF por capítulo |
| `pdf2md aggr ROOT` | OVERVIEW de múltiplos docs |
| `pdf2md norm FILE.md` | normalize canônico |
| `pdf2md doctor / version / help` | meta |

Detalhes em [`arquitetura/05_pipeline.md`](arquitetura/05_pipeline.md).

---

## 6. Estado experimental (lab/) — atualizado 2026-05-17

17 labs + infra T060. Sumário cronológico:

| ID | Variável testada | Resultado | Estado |
|---|---|---|---|
| `e00_baseline_marker` | Pipeline reproduzível em N&C cap 4 | rt 95.09% (bate histórico) | `.frozen` |
| `e01_baseline_corpus_categorias` | 3 PDFs (paper LaTeX, notes, livro_clássico) | rt 91-98% | `.frozen` |
| `e02_pdfs_sujos` | 5 PDFs degradados (CDC, IRS, scan, slides) | rt 46-97%; padrões de falha identificados | `.frozen` |
| `e03_atkins_wilson_scan` | text-layer vs sem-text-layer | text-layer ajuda; bloat 7.7× é alucinação | `.frozen` |
| `e04_t131_validation_corpus` | T131 em 7 docs | 45-55% economia line art; 0% fotos | `.frozen` |
| `e05_acroform_gate` | Q11 escapes markdown penalizam rt | sim — IRS f1040 46→73% sem escapes | `.frozen` |
| `e06_mineru25_pro` | Q15 MinerU 2.5-Pro | **blocked** (FastAPI crash Win+RTX3060) | `.blocked` |
| `e07_marker_llm` | Marker `--use_llm` + Ollama llama3.2-vision | descartado p/ esse modelo+tool (40× lento, 0 ganho) | descarte com escopo |
| `e08_granite_docling` | Q16 Granite-Docling-258M via docling | descartado p/ N&C (50× lento, base64 imgs) | descarte com escopo |
| `e09_pixel_roundtrip_proto` | T070 protótipo + macro SSIM | macro promove; bbox-IoU geom falha | promoção parcial |
| `e10_pixel_roundtrip_fingerprint` | block-a-block fingerprint matching | descarta (cobertura 0%); +bug T076 descoberto | descarta |
| `e11_fingerprint_refinado` | 4 variantes de fingerprint local | descarta — fragmentação incompatível com reflow | descarta |
| `e12_metricas_globais_pagina` | G1 WER global / G2 grid / G3 anchors | **insight**: páginas desalinham após reflow | replano |
| `e13_alinhamento_paginas` | DTW vs Hungarian align | **destrava T070** — Hungarian WER med 0.376 | promove |
| `e14_pixel_roundtrip_cross_pdf` | pixel-roundtrip em 3 categorias além N&C | generaliza — WER med 0.26-0.42, todos passam | promove |
| `e15_gt_validation` | Infraestrutura para T060 (GT humano vs PyMuPDF) | scripts prontos, aguarda curadoria humana | infra (não-experimental) |
| `e16_image_decompose` | T180 piloto: 4 VLMs Ollama no logo Cambridge (N=1) | 3/4 transcrevem fiel; `gemma3:4b` mais rápido E correto (46s) | promove parcial → T180 |
| `e17_vlm_full_page` | VLM como extrator full-page em pg204 N&C math (N=1) | **0/4 acertam** — 3 alucinam, 1 vazio. Nível 5 da hierarquia falsificado | descarte com escopo |

### Lição transversal e16+e17 (VLM-as-tool)

Sequência testou se VLMs locais via Ollama (4–12B) viabilizam capacidade
nova. **Resposta empírica**:

- ✓ **Small-image OCR** (logo curto, header, badge): VLM **funciona** —
  `gemma3:4b` (4B) basta. Apoia T180 com escopo realista.
- ✗ **Full-page extraction** (página math+prosa+layout): VLM **aluci
  confiantemente** — não substitui Marker. Mais capacidade ≠ mais fidelidade.

Conclusão: VLM-as-tool **confinado a T180** (Frente E). Marker / Surya /
pipeline atual permanece único caminho viável para extração full-page.
Não há "Eixo C" formal — VLM é ferramenta auxiliar dentro de T180, não
camada ortogonal.

### Próximos candidatos

- **T060** (Frente A, mini-corpus GT humano 5-10 pgs) — destrava T072 calibração e T410 (alt tools)
- **T180** start (escopo small-image refinado pós-e16/e17)
- **e1X** alt-tools comparativo Marker × Nougat × olmOCR-2 × Docling (T410)
  com pixel-roundtrip como métrica — depende T060
- **macro-intent CLI** (T090) usando os perfis já coletados

---

## 7. Como navegar esta documentação

```
docs/
├── ARQUITETURA.md            (este arquivo — overview de camadas)
├── arquitetura/
│   ├── 01_extracao.md        Camada 1: ferramentas de extração
│   ├── 02_otimizacao.md      Camada 2: otimização de imagens
│   ├── 03_reconstrucao.md    Camada 3: engines MD → PDF
│   ├── 04_metricas.md        Camada 4: validação e métricas
│   └── 05_pipeline.md        Orquestração dos scripts atuais
├── PHILOSOPHY.md             Hierarquia de prioridades + eixo de representação +
│                             validação por fechamento recursivo + tradeoffs + triângulo
├── META_TRANSMUTOS.md        Tese da família (pdf2md como instância)
├── MD_CANONICAL.md           Schema do output (pivot universal)
├── METRICS.md                Painel de métricas adotado (M1-M4)
├── TECNOLOGIAS.md            ** Perfis cross-recursos (tempo/mem/gpu) **
├── ANALISE_CRITICA.md        Trajetória + lições + análise crítica do curso
├── LITERATURA.md             Revisão v1 de papers
├── LITERATURA_v2.md          v2: alucinação + MinerU 2.5-Pro + olmOCR-2 + LLM-judge
├── LAB_PROTOCOL.md           Regras da bancada experimental
├── LICENSING.md              Matriz de licenças do corpus
├── biblioteca/               Catálogo (ferramentas/métricas/papers/benchmarks/glossário)
├── arquitetura/              Sub-docs por camada (01-05)
└── _archive/                 Documentos históricos
```

Documentos novos desde a v0.4 (2026-05):
- **PHILOSOPHY.md** ganhou validação por fechamento recursivo + triângulo macro/médio/micro + calibração reconstrutor + ablação modular + tradeoffs + convergência
- **META_TRANSMUTOS.md** (novo) — tese da família de conversores
- **MD_CANONICAL.md** (novo) — schema do output
- **TECNOLOGIAS.md** (novo) — perfis e dados empíricos cross-recursos
- **ANALISE_CRITICA.md** (novo) — trajetória e revisão crítica
- **LITERATURA_v2.md** — atualizações pós-experimentos lab/

E os planos de execução estão em [`../../ROADMAP.md`](../../ROADMAP.md).
