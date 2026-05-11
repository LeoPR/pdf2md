# Índice de tickets — agrupado por `kind`

Visão consolidada de todos os tickets do `pdf2md`, agrupados pela faixa
`kind:` do frontmatter. Para regras e formato ver [`README.md`](README.md).
Para o recorte por **Frente de cobertura (A-E)**, ver [`../ROADMAP.md`](../ROADMAP.md).

> Status indicado entre parênteses: `(o)` open, `(p)` in_progress,
> `(c)` closed, `(r)` research, `(b)` blocked.

---

## `infra` — Bancada, corpus, manifests, baseline

Tickets que montam o ambiente para que outros tickets possam ser
trabalhados sem se preocupar com setup.

| Ticket | Status | Título |
|---|---|---|
| [T013](closed/T013_mover_scripts_conversor.md) | (c) | Mover scripts conversor + generalizar |
| [T020](closed/T020_estrutura_lab_e_protocolo.md) | (c) | Estrutura `lab/` + `_template/` + LAB_PROTOCOL |
| [T021](closed/T021_manifest_sources_read_only.md) | (c) | Manifest de sources read-only (N&C) |
| [T022](closed/T022_cache_corpus_em_z.md) | (c) | Cache de corpus em `Z:\caches\corpus\pdf2md\` |
| [T023](closed/T023_convencao_venv_por_experimento.md) | (c) | Convenção de venv por experimento |
| [T024](closed/T024_reorganizacao_tickets_em_faixas.md) | (c) | Reorganização tickets em faixas (`kind:`) |
| [T030](closed/T030_revisao_literatura.md) | (c) | Revisão de literatura inicial — `docs/LITERATURA.md` |
| [T040](closed/T040_corpus_canonico_inicial.md) | (c) | Corpus canônico (8/8-12 entradas; 5/9 categorias; PMC pendente) |
| [T060](open/T060_mini_corpus_gt_humano.md) | (o) | Mini-corpus de GT humano (5-10 págs) — Frente A |
| [T105](closed/T105_substituir_extracao_antiga_eliminar_v2_anti_padra.md) | (c) | Substituir extração antiga (eliminar `_v2`) |
| [T430](open/T430_corpus_livre_para_testes_urls_licencas.md) | (o) | Corpus livre — URLs + licenças (substituído por T040 + manifests; manter como histórico ou fechar) |

## `pipeline` — Pipeline de extração estável

Código que já roda e está estabilizado em `src/`.

| Ticket | Status | Título |
|---|---|---|
| [T071](closed/T071_bloat_ratio_alucinacao_heuristica.md) | (c) | Heurística `bloat_ratio` em stats.py — detecta padrão de alucinação |
| [T101](closed/T101_marker_pdf_extraction_com_gpu_rtx_3060.md) | (c) | Marker PDF extraction com GPU (RTX 3060) |
| [T102](closed/T102_restructure_output_por_capitulo_indexmd.md) | (c) | Restructure output por capítulo + index.md |
| [T103](closed/T103_round_trip_test_script.md) | (c) | Round-trip test script |
| [T104](closed/T104_round_trip_test_em_1_capitulo_baseline.md) | (c) | Round-trip baseline (cap. 4 → 95.1%) |
| [T107](open/T107_md_to_pdf_per_chapter.md) | (o) | MD → PDF por capítulo via Chrome |
| [T108](open/T108_pacote_conversor_readme.md) | (o) | Pacote `pip install pdf2md` |

## `imagens` — Otimização adaptativa de imagens

Decisões arquiteturais sobre tratamento de imagens extraídas.

| Ticket | Status | Título |
|---|---|---|
| [T130](research/T130_image_optimization.md) | (r) | Otimização de imagens (meta) |
| [T131](closed/T131_classificador_e_compressao_imagens_nc.md) | (c) | Classificador + compressão níveis 1-2 (−38.6% no N&C) |
| [T135](research/T135_ssim_gate_qualidade.md) | (r) | Gate SSIM antes/depois — Frente D |
| [T136](closed/T136_breakdown_formato_stats.md) | (c) | Breakdown por formato em `_stats.md` (validado em e01) — Frente D |

## `experimento` — Hipóteses testáveis

Cada um destes tem ou terá um experimento correspondente em [`../lab/eNN_/`](../lab/).

| Ticket | Status | Título | Experimento sugerido | Frente |
|---|---|---|---|---|
| [T050](closed/T050_baseline_marker_reproduzivel.md) | (c) | Baseline marker reproduzível — round-trip 95.09% (bate histórico) | `lab/e00_baseline_marker/` (.frozen) | A |
| (sem ticket) | — | **Baseline em 3 categorias do corpus canônico** — round-trip 91.34%-98.58% | `lab/e01_baseline_corpus_categorias/` (.frozen) | A |
| (sem ticket) | — | **Pipeline em 5 PDFs "sujos"** — rt 46-97%; AcroForm divisor; scan+OCR quebra roundtrip (não extract) | `lab/e02_pdfs_sujos/` (.frozen) | A |
| (sem ticket) | — | **Atkins vs Wilson scan**: Atkins 92.11% (com text-layer), Wilson 13.62% (sem) — text-layer **ajuda**; bloat 7.7× revela padrão de alucinação | `lab/e03_atkins_wilson_scan/` (.frozen) | A |
| (sem ticket) | — | **T131 validado em 7 PDFs**: 45-55% em line art, 0% em fotos | `lab/e04_t131_validation_corpus/` (.frozen) | D |
| (sem ticket) | — | **AcroForm gate (Q11)**: IRS f1040 46.16% → 73.36% (normalizado); achado: rt atual penaliza escapes markdown | `lab/e05_acroform_gate/` (.frozen) | B+C |
| (sem ticket) | — | **MinerU2.5-Pro (Q15)**: 3 tentativas; uv install OK, server FastAPI crasha silenciosamente em Win+RTX3060; mover para Q16 (Granite-Docling) | `lab/e06_mineru25_pro/` (.blocked) | Alt-tools |
| [T106](closed/T106_extra_extraction_study.md) | (c) | Estudo extração com DPI alternativo | (rodado ad-hoc, sem lab/) | C |
| [T132](research/T132_potrace_svg_line_art.md) | (r) | potrace para line art → SVG | futuro `lab/eXX_potrace/` | C+D |
| [T133](research/T133_detector_de_formula.md) | (r) | Detector de fórmula heurístico | futuro `lab/eXX_formula_detect/` | C |
| [T134](research/T134_pix2tex_formulas.md) | (r) | pix2tex para fórmulas-imagem detectadas | futuro `lab/eXX_pix2tex/` | B+D |
| [T137](research/T137_denoising_jpeg_pre_compressao.md) | (r) | Denoising JPEG antes da compressão | futuro `lab/eXX_jpeg_denoise/` | D |
| [T160](research/T160_ocr_semantico_generalizado.md) | (r) | OCR semântico generalizado de imagens-com-texto | futuro `lab/eXX_semantic_ocr/` | **B (atual)** |
| [T180](research/T180_reconstrucao_vetorial_imagens.md) | (r) | Reconstrução vetorial (texto + fonte + brasão residual) | futuro `lab/eXX_reconstrutor_vetorial/` | E |
| [T410](research/T410_testar_ferramentas_alternativas_nougat_mineru_pdftotext.md) | (r) | Marker × Nougat × MinerU 2.5 × olmOCR-2 × Docling | família `lab/e1X_*` | A+B+C |
| [T420](research/T420_fallback_low_resource_sem_gpu_sem_modelos_ml_pesados.md) | (r) | Fallback low-resource (sem GPU) | futuro `lab/eXX_low_resource/` | B |
| [T450](closed/T450_investigar_ibm_lesson_1_round_trip_critico.md) | (c) | IBM lesson 1 — fechado como "categoria conhecida" (bloat 3.4× via padrão de e03) | (sem lab dedicado — entendido sistemicamente) | A |

## `decisao` — Princípios, categorias, design

Discussões arquiteturais que orientam outros tickets. Vivem aqui, não em `lab/`.

| Ticket | Status | Título |
|---|---|---|
| [T031](closed/T031_definicao_de_metricas.md) | (c) | Definir métricas — `docs/METRICS.md` |
| [T100](research/T100_roadmap_conversor_pdf_md_bidirecional.md) | (r) | Roadmap conversor (meta original) |
| [T400](research/T400_conversor_projeto_autonomo.md) | (r) | Conversor como projeto autônomo (meta) |
| [T401](open/T401_documentar_hierarquia_de_prioridades.md) | (o) | Hierarquia de prioridades (PHILOSOPHY.md) |
| [T440](research/T440_md_como_formato_de_transporte_vs_pdf.md) | (r) | MD como formato de transporte vs PDF |
| [T451](research/T451_slides_pptx_como_categoria_problematica.md) | (r) | Slides PPTX como categoria problemática |

---

## Fase 0 — montar a bancada ✓ COMPLETA

Estado em **2026-05-10**: 9 macro-tickets fechados.

| ID | Ticket | Estado | Saída |
|---|---|---|---|
| T020 | Estrutura `lab/` + protocolo | ✓ closed | `lab/`, `docs/LAB_PROTOCOL.md` |
| T021 | Manifest sources read-only | ✓ closed | `corpus/_sources/MANIFEST.md` |
| T022 | Cache em `Z:\` | ✓ closed | `Z:\caches\corpus\pdf2md\` |
| T023 | Convenção de venv por experimento | ✓ closed | docs em LAB_PROTOCOL |
| T024 | Reorganização tickets em faixas | ✓ closed | `kind:` + `INDEX.md` |
| T030 | Revisão de literatura | ✓ closed | `docs/LITERATURA.md` |
| T031 | Definição de métricas | ✓ closed | `docs/METRICS.md` |
| T040 | Corpus canônico inicial | ✓ closed | 8 entradas (7 baixadas + 1 PMC pendente). 5/9 categorias. |
| T050 | Baseline marker reproduzível | ✓ closed | `lab/e00_baseline_marker/` (.frozen). Round-trip **95.09%** — bate histórico exato. |

Próximas famílias de experimentos (alinhadas com [Frentes do ROADMAP](../ROADMAP.md)):

- **Frente B atual — extração de conhecimento**:
  - [T160](research/T160_ocr_semantico_generalizado.md): OCR semântico generalizado (núcleo da Frente B)
  - [T060](open/T060_mini_corpus_gt_humano.md): mini-corpus de GT humano (Frente A; valida se round-trip ≈ WER vs GT real)
- **Frente C/D — captura estrutural + otimização**:
  - [T132](research/T132_potrace_svg_line_art.md), [T133](research/T133_detector_de_formula.md), [T134](research/T134_pix2tex_formulas.md), [T135](research/T135_ssim_gate_qualidade.md), [T136](open/T136_breakdown_formato_stats.md)
- **Família `lab/e1X_*`** (T410): comparação Marker × Nougat × MinerU 2.5 × olmOCR-2 × Docling
- **Frente E — ambição**: [T180](research/T180_reconstrucao_vetorial_imagens.md) (reconstrução vetorial)

Decisões de packaging (T108) e refatoração de paths hard-coded em `src/` ficam pendentes — não bloquearam Fase 0 (baseline foi reproduzido usando venv legado `Z:\venvs\marker\` como fornecedor do marker, sem tocar em `src/`).
