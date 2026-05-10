# Roadmap

Dois recortes complementares do trabalho:

- **Frentes de cobertura** (eixo do que se quer cobrir) — abaixo
- **Fases cronológicas** (eixo de execução, herdado do projeto original) — mais adiante

Cada item aponta para tickets concretos em [`tickets/`](tickets/) e ao [`INDEX.md`](tickets/INDEX.md).

---

## Arquitetura em 4 camadas

```
   ┌──────── ROUND-TRIP (validador permanente) ────────┐
   ▼                                                   │
 PDF ──▶ [Cam 1: extração]   ──▶ MD ──┐                │
        marker / Nougat / MinerU      │                │
        / olmOCR / Docling             │ [Cam 2: otim.]│
                                       │  PNG paleta   │
                                       │  SVG, LaTeX   │
                                       ▼               │
 PDF' ◀── [Cam 3: reconstrução] ◀── MD' ───────────────┤
        pandoc + Chrome + KaTeX                        │
        (alt: Tectonic, Typst, WeasyPrint)             │
                                                       ▼
                                  [Cam 4: métrica] → sim%, divergências
                                  SequenceMatcher + 8 categorias
                                  (futuro: WER, TEDS, CDM, count-diff)
```

**Detalhamento completo**: [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md). Por camada:

| Camada | Documento | Estado atual |
|---|---|---|
| 1 — Extração | [`docs/arquitetura/01_extracao.md`](docs/arquitetura/01_extracao.md) | marker-pdf 1.10.2 (GPU) |
| 2 — Otimização | [`docs/arquitetura/02_otimizacao.md`](docs/arquitetura/02_otimizacao.md) | PNG paleta lossy (T131) |
| 3 — Reconstrução | [`docs/arquitetura/03_reconstrucao.md`](docs/arquitetura/03_reconstrucao.md) | pandoc + Chrome + KaTeX |
| 4 — Métrica | [`docs/arquitetura/04_metricas.md`](docs/arquitetura/04_metricas.md) | round-trip 95.09% N&C, 91-99% corpus |
| Pipeline | [`docs/arquitetura/05_pipeline.md`](docs/arquitetura/05_pipeline.md) | scripts standalone em `src/` |

Eixo ortogonal de **representação** (raster → texto semântico) em [`docs/PHILOSOPHY.md §"Eixo de representação"`](docs/PHILOSOPHY.md).

---

## Frentes de cobertura

Cinco frentes representam o escopo total do conversor. Cada frente tem ROI
decrescente. Trabalho ativo segue ordem alfabética dentro do que está priorizado;
**Frente B (extração de conhecimento) é a frente atual** após Fase 0 (bancada montada).

| Frente | Conteúdo | Tickets | Estado |
|---|---|---|---|
| **A — Validação** | round-trip + GT humano + multi-iteration; o validador permanente do pipeline | [T050](tickets/closed/T050_baseline_marker_reproduzivel.md) (closed), [T060](tickets/open/T060_mini_corpus_gt_humano.md) (open) | base estabelecida; falta GT humano |
| **B — Captura textual** ← **atual** | máximo de texto incluindo OCR de imagens-com-texto; preserva 1ª prioridade da [PHILOSOPHY](docs/PHILOSOPHY.md) | [T101](tickets/closed/T101_marker_pdf_extraction_com_gpu_rtx_3060.md) (closed, Marker base), [T160](tickets/research/T160_ocr_semantico_generalizado.md) (research) | parcial; T160 generaliza |
| **C — Captura estrutural** | tabelas, headers, fórmulas e imagens com semântica preservada (2ª prioridade) | [T102](tickets/closed/T102_restructure_output_por_capitulo_indexmd.md) (closed), [T132](tickets/research/T132_potrace_svg_line_art.md), [T133](tickets/research/T133_detector_de_formula.md), [T134](tickets/research/T134_pix2tex_formulas.md) | em progresso |
| **D — Otimização de representação** | formato adaptativo, lossless, denoise; ascende no [eixo de representação](docs/PHILOSOPHY.md#eixo-de-representação) | [T131](tickets/closed/T131_classificador_e_compressao_imagens_nc.md) (closed), [T135](tickets/research/T135_ssim_gate_qualidade.md), [T136](tickets/open/T136_breakdown_formato_stats.md), [T137](tickets/research/T137_denoising_jpeg_pre_compressao.md) | parcial |
| **E — Reconstrução vetorial** | texto + fonte + geometria + brasão residual; Nível 4 do eixo de representação | [T180](tickets/research/T180_reconstrucao_vetorial_imagens.md) (research) | ambição |

A ordem natural de execução é A → B → C → D → E, mas frentes podem rodar em paralelo conforme experimentos abrem.

---

## Fases cronológicas

### Fase 0 — Bancada experimental ✓ COMPLETA (2026-05-09 a 2026-05-10)

Montagem do `lab/`, manifests, métricas, literatura, baseline reproduzível.
Detalhes em [`tickets/INDEX.md`](tickets/INDEX.md) seção "Fase 0".

### Fase 1 — Pipeline básico ✓ ESTÁVEL

- [x] [T101](tickets/closed/T101_marker_pdf_extraction_com_gpu_rtx_3060.md) Extração via `marker-pdf` com GPU
- [x] [T102](tickets/closed/T102_restructure_output_por_capitulo_indexmd.md) Reorganização por capítulo via TOC
- [x] [T103](tickets/closed/T103_round_trip_test_script.md) Round-trip MD → PDF → MD'
- [x] Telemetria (`stats.py`, `aggregate_stats.py`)
- [x] Multi-iteration round-trip (`multi_roundtrip.py`)

### Fase 2 — Adoção e empacotamento

- [ ] [T107](tickets/open/T107_md_to_pdf_per_chapter.md) MD → PDF por capítulo (parcial)
- [ ] [T108](tickets/open/T108_pacote_conversor_readme.md) `pip install pdf2md` com CLI unificado

### Fase 3 — Otimização adaptativa de imagens (família T130)

- [x] [T131](tickets/closed/T131_classificador_e_compressao_imagens_nc.md) Classificador adaptativo PNG B&W / paleta lossy
- [ ] [T132](tickets/research/T132_potrace_svg_line_art.md) potrace para line art → SVG
- [ ] [T133](tickets/research/T133_detector_de_formula.md) Detector de fórmula (heurística + bbox)
- [ ] [T134](tickets/research/T134_pix2tex_formulas.md) pix2tex para fórmulas detectadas
- [ ] [T135](tickets/research/T135_ssim_gate_qualidade.md) Gate SSIM antes/depois
- [ ] [T136](tickets/open/T136_breakdown_formato_stats.md) Breakdown por formato no `_stats.md`
- [ ] [T137](tickets/research/T137_denoising_jpeg_pre_compressao.md) Restauração de artefatos JPEG

### Fase 4 — Diversificação do pipeline

- [ ] [T410](tickets/research/T410_testar_ferramentas_alternativas_nougat_mineru_pdftotext.md) Marker × Nougat × MinerU 2.5 × olmOCR-2 × Docling
- [ ] [T420](tickets/research/T420_fallback_low_resource_sem_gpu_sem_modelos_ml_pesados.md) Stack low-resource
- [ ] [T440](tickets/research/T440_md_como_formato_de_transporte_vs_pdf.md) MD compactado como formato de distribuição
- [ ] [T160](tickets/research/T160_ocr_semantico_generalizado.md) OCR semântico generalizado (Frente B)
- [ ] [T180](tickets/research/T180_reconstrucao_vetorial_imagens.md) Reconstrução vetorial (Frente E)

### Fase 5 — Corpus e validação

- [x] [T040](tickets/closed/T040_corpus_canonico_inicial.md) Corpus canônico inicial (8 entradas)
- [ ] [T060](tickets/open/T060_mini_corpus_gt_humano.md) Mini-corpus GT humano (Frente A)
- [ ] [T430](tickets/open/T430_corpus_livre_para_testes_urls_licencas.md) Lista de PDFs livres/CC (substituído por T040; manter como histórico)
- [ ] [T450](tickets/open/T450_investigar_ibm_lesson_1_round_trip_critico.md) Diagnóstico IBM lesson 1
- [ ] [T451](tickets/research/T451_slides_pptx_como_categoria_problematica.md) Enquadramento slides PPTX

## Meta — design

- [ ] [T401](tickets/open/T401_documentar_hierarquia_de_prioridades.md) Hierarquia de prioridades (vivo, expandido em 2026-05-10 com eixo de representação)
- [ ] [T400](tickets/research/T400_conversor_projeto_autonomo.md) Meta-ticket projeto autônomo
- [ ] [T100](tickets/research/T100_roadmap_conversor_pdf_md_bidirecional.md) Roadmap original (histórico)

## Não-objetivos atuais

- Reproduzir layout PDF byte-a-byte (4ª prioridade da PHILOSOPHY)
- Suportar todos os tipos de PDF — slides PPTX são caso conhecido (T451)
- Substituir `marker-pdf` — é a base; ferramentas alternativas (T410) são para fallback ou comparação, não substituição
- Reconstruir cada figura científica vetorialmente — T180 vale só onde elementos se repetem (logos, fórmulas-imagem)
