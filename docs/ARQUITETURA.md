# Arquitetura — `pdf2md`

*Visão consolidada do conceito, das camadas e das ferramentas. Para detalhes por camada, ver [`arquitetura/`](arquitetura/).*

---

## 1. Conceito abstrato

O `pdf2md` opera num **fluxo de 4 camadas** com **round-trip como validador permanente**:

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
| **2 — Otimização** | Imagens raw → representação mais semântica | `optimize_images.py` (PNG paleta lossy, T131 closed) | [`arquitetura/02_otimizacao.md`](arquitetura/02_otimizacao.md) |
| **3 — Reconstrução** | MD → PDF visualizável | pandoc 3.9 + Chrome headless + KaTeX | [`arquitetura/03_reconstrucao.md`](arquitetura/03_reconstrucao.md) |
| **4 — Métrica** | MD vs MD' → similarity + divergências | token similarity (`SequenceMatcher`) + 6 categorias | [`arquitetura/04_metricas.md`](arquitetura/04_metricas.md) |
| **Pipeline** | Orquestração (scripts) | `src/{roundtrip,stats,restructure,...}.py` | [`arquitetura/05_pipeline.md`](arquitetura/05_pipeline.md) |

### Por que round-trip

Round-trip captura uma propriedade **mensurável** sem precisar de ground-truth: se MD → PDF → MD' converge, o pipeline preserva informação. Não é prova de fidelidade (literatura ressalta — ver [`LITERATURA.md §4`](LITERATURA.md)), mas é health-check excelente. Para fidelidade real, complementar com GT humano (T060 futuro).

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
│ Camada 4 — MÉTRICA / VALIDAÇÃO                                       │
│ ──────────────────────────────                                       │
│                                                                      │
│ ATUAL    │ SequenceMatcher token similarity (`roundtrip.py`)         │
│          │ + 6 categorias de divergência (math, heading, emphasis,   │
│          │   table, separator, other)                                │
│ FUTURO   │ M1 WER-prosa · M2 CDM (fórmulas) · M3 TEDS (tabelas)      │
│          │ M4 count-diff (fórmulas, citações, headers, imagens)      │
│          │ T060 GT humano em mini-corpus de 5-10 páginas             │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Eixo de representação (transversal)

Em paralelo às 4 camadas acima, cada elemento extraído pode subir/descer na escala de representação (definida em [`PHILOSOPHY.md`](PHILOSOPHY.md)):

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

Símbolos: ✓ closed; sem símbolo = research/open. Lista completa de tickets em [`../tickets/INDEX.md`](../tickets/INDEX.md).

---

## 5. Pipeline atual (orquestração)

Scripts em [`../src/`](../src/) compõem o fluxo end-to-end:

```
src/
├── stats.py            ← Camada 4: telemetria + round-trip metrics
├── aggregate_stats.py  ← Camada 4: agregação multi-doc
├── roundtrip.py        ← Cam 1 + Cam 3 + Cam 4: MD → PDF → MD' → compare
├── multi_roundtrip.py  ← Cam 4: iterar round-trip N vezes (estabilidade)
├── optimize_images.py  ← Camada 2: PNG paleta lossy / 1-bit
├── gen_pdfs.py         ← Camada 3: bulk MD → PDF por capítulo
└── restructure.py      ← Camada 1 (pós): fatiar MD por TOC do PDF
```

Detalhes em [`arquitetura/05_pipeline.md`](arquitetura/05_pipeline.md).

---

## 6. Estado experimental (lab/)

Experimentos validados até agora:

| ID | Variável testada | Resultado | Estado |
|---|---|---:|---|
| `lab/e00_baseline_marker` | Pipeline reproduzível em N&C cap. 4 | round-trip 95.09% (bate histórico) | `.frozen` |
| `lab/e01_baseline_corpus_categorias` | Categoria do doc (3 PDFs) | round-trip 91.34%-98.58% | `.frozen` |

Próximos candidatos a virar experimento:
- T060 (Frente A, validar round-trip vs GT humano)
- T160 (Frente B, OCR semântico generalizado)
- T410 (alt-tools — Marker × Nougat × MinerU × olmOCR × Docling)
- Expansão do e01 para PDFs scanned (Newton, Wilson — categoria scanned_image_only)
- PDFs "sujos" (categoria a ser definida — ver [`PDFS_SUJOS_CANDIDATOS.md`](PDFS_SUJOS_CANDIDATOS.md) quando criado)

---

## 7. Como navegar esta documentação

```
docs/
├── ARQUITETURA.md            (este arquivo — overview)
├── arquitetura/
│   ├── 01_extracao.md        Camada 1: ferramentas de extração
│   ├── 02_otimizacao.md      Camada 2: otimização de imagens
│   ├── 03_reconstrucao.md    Camada 3: engines MD → PDF
│   ├── 04_metricas.md        Camada 4: validação e métricas
│   └── 05_pipeline.md        Orquestração dos scripts atuais
├── PHILOSOPHY.md             Hierarquia de prioridades + eixo de representação
├── LITERATURA.md             Revisão de papers (métricas, benchmarks, ferramentas)
├── METRICS.md                Painel de métricas adotado
├── LAB_PROTOCOL.md           Regras da bancada experimental
└── PDFS_SUJOS_CANDIDATOS.md  Corpus de PDFs problemáticos (quando criado)
```

E os planos de execução estão em [`../ROADMAP.md`](../ROADMAP.md).
