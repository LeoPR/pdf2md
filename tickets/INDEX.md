# Índice de tickets — agrupado por `kind`

Visão consolidada de todos os tickets do `pdf2md`, agrupados pela faixa
`kind:` do frontmatter. Para regras e formato ver [`README.md`](README.md).

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
| [T040](in_progress/T040_corpus_canonico_inicial.md) | (p) | Corpus canônico (7/8-12 entradas; 1 pendente download manual) |
| [T105](closed/T105_substituir_extracao_antiga_eliminar_v2_anti_padra.md) | (c) | Substituir extração antiga (eliminar `_v2`) |
| [T430](open/T430_corpus_livre_para_testes_urls_licencas.md) | (o) | Corpus livre — URLs + licenças (substituído por T040 + manifests; manter como histórico ou fechar) |

## `pipeline` — Pipeline de extração estável

Código que já roda e está estabilizado em `src/`.

| Ticket | Status | Título |
|---|---|---|
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

## `experimento` — Hipóteses testáveis

Cada um destes tem ou terá um experimento correspondente em [`../lab/eNN_/`](../lab/).

| Ticket | Status | Título | Experimento sugerido |
|---|---|---|---|
| [T050](in_progress/T050_baseline_marker_reproduzivel.md) | (p) | Baseline marker reproduzível (estrutura criada, falta executar) | `lab/e00_baseline_marker/` |
| [T106](closed/T106_extra_extraction_study.md) | (c) | Estudo extração com DPI alternativo | (rodado ad-hoc, sem lab/) |
| [T137](research/T137_denoising_jpeg_pre_compressao.md) | (r) | Denoising JPEG antes da compressão | futuro `lab/eXX_jpeg_denoise/` |
| [T410](research/T410_testar_ferramentas_alternativas_nougat_mineru_pdftotext.md) | (r) | Testar ferramentas alternativas (Nougat, MinerU, pdftotext) | família `lab/e1X_*` |
| [T420](research/T420_fallback_low_resource_sem_gpu_sem_modelos_ml_pesados.md) | (r) | Fallback low-resource (sem GPU) | futuro `lab/eXX_low_resource/` |
| [T450](open/T450_investigar_ibm_lesson_1_round_trip_critico.md) | (o) | Investigar IBM lesson 1 (round-trip 28.9%) | futuro `lab/eXX_ibm_diagnose/` |

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

## Fase 0 — montar a bancada

Estado em **2026-05-10**:

| ID | Ticket | Estado | Saída |
|---|---|---|---|
| T020 | Estrutura `lab/` + protocolo | ✓ closed | `lab/`, `docs/LAB_PROTOCOL.md` |
| T021 | Manifest sources read-only | ✓ closed | `corpus/_sources/MANIFEST.md` |
| T022 | Cache em `Z:\` | ✓ closed | `Z:\caches\corpus\pdf2md\` |
| T023 | Convenção de venv por experimento | ✓ closed | docs em LAB_PROTOCOL |
| T024 | Reorganização tickets em faixas | ✓ closed | `kind:` + `INDEX.md` |
| T030 | Revisão de literatura | ✓ closed | `docs/LITERATURA.md` |
| T031 | Definição de métricas | ✓ closed | `docs/METRICS.md` |
| T040 | Corpus canônico inicial | ⏳ in_progress | 7 entradas no MANIFEST (6 baixadas + 1 pendente). Cobre 4/9 categorias. |
| T050 | Baseline marker reproduzível | ⏳ in_progress | `lab/e00_baseline_marker/` (estrutura pronta; falta executar — venv + run) |

Para fechar a Fase 0:

- **T040**: alcançar 8-12 entradas (faltam categorias livro_image_heavy, livro_classical_typography, multilingual_pt; baixar manualmente o PMC)
- **T050**: rodar o experimento (instalar deps no venv `pdf2md_lab_e00`, executar `run.ps1`, preencher `RESULT.md`)

Depois da Fase 0, abrir família `lab/e1X_*` para comparação de
ferramentas (T410): Marker × Nougat × MinerU 2.5 × olmOCR-2 × Docling
(decisão informada pela literatura — ver [`docs/LITERATURA.md`](../docs/LITERATURA.md) §3).
