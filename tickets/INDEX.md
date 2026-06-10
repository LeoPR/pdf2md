# Índice de tickets — agrupado por `kind`

Visão consolidada de todos os tickets do `pdf2md`, agrupados pela faixa
`kind:` do frontmatter. Para regras e formato ver [`README.md`](README.md).
Para o recorte por **Frente de cobertura (A-E)**, ver [`../ROADMAP.md`](../ROADMAP.md).

> Status indicado entre parênteses: `(o)` open, `(p)` in_progress,
> `(c)` closed, `(r)` research, `(b)` blocked.

## Campo `altitude:` (rescope 2026-05-19)

A partir de 2026-05-19, tickets ganham campo `altitude:` no frontmatter para
distinguir as **duas altitudes operacionais** do projeto (ver
[ROADMAP § Duas altitudes](../ROADMAP.md#duas-altitudes-operacionais-rescope-2026-05-19)):

- **`altitude: execucao`** — Frentes A-E. Tickets executáveis, ritmo dias-semanas.
  Exemplos: T060 (GT humano), T070 (pixel-roundtrip), T072 (calibração),
  T180 (image decompose), T410 (alt-tools).
- **`altitude: meta`** — Meta-design. Ritmo de meses, orienta sem prazo.
  Exemplos: T400 (autonomous project), T401 (philosophy), T402 (fractal),
  T440 (MD-as-transport).

Tickets sem `altitude:` no frontmatter herdam por heurística: `kind: decisao`
→ `meta`; demais → `execucao`. Atualizar quando re-editar.

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
| [T030](closed/T030_revisao_literatura.md) | (c) | Revisão de literatura inicial — `docs/explanation/literatura.md` |
| [T040](closed/T040_corpus_canonico_inicial.md) | (c) | Corpus canônico (8/8-12 entradas; 5/9 categorias; PMC pendente) |
| [T060](open/T060_mini_corpus_gt_humano.md) | (o) | Mini-corpus de GT humano (5-10 págs) — Frente A |
| [T065](closed/T065_corpus_gt_sintetico.md) | (c) | Corpus GT-por-construção — **promovido 2026-06-10** (`corpus/examples/sintetico/`, instrumento validado e24 ondas 1-4; destrava T075/T092/T191) |
| [T105](closed/T105_substituir_extracao_antiga_eliminar_v2_anti_padra.md) | (c) | Substituir extração antiga (eliminar `_v2`) |
| [T430](closed/T430_corpus_livre_para_testes_urls_licencas.md) | (c) | Corpus livre — URLs + licenças (fechado 2026-05-11; substituído por T040 + MANIFEST) |

## `pipeline` — Pipeline de extração estável

Código que já roda e está estabilizado em `src/`.

| Ticket | Status | Título |
|---|---|---|
| [T071](closed/T071_bloat_ratio_alucinacao_heuristica.md) | (c) | Heurística `bloat_ratio` em stats.py — detecta padrão de alucinação |
| [T076](closed/T076_md_to_pdf_overwrite_silencioso.md) | (c) | Bug: md_to_pdf sobrescreve PDF co-irmão silenciosamente — fix em v0.4.1 |
| [T101](closed/T101_marker_pdf_extraction_com_gpu_rtx_3060.md) | (c) | Marker PDF extraction com GPU (RTX 3060) |
| [T102](closed/T102_restructure_output_por_capitulo_indexmd.md) | (c) | Restructure output por capítulo + index.md |
| [T103](closed/T103_round_trip_test_script.md) | (c) | Round-trip test script |
| [T104](closed/T104_round_trip_test_em_1_capitulo_baseline.md) | (c) | Round-trip baseline (cap. 4 → 95.1%) |
| [T107](closed/T107_md_to_pdf_per_chapter.md) | (c) | MD → PDF por capítulo via Chrome — fechado 2026-05-17 (coberto por `pdf2md.pdfs.generate_all()`) |
| [T108](closed/T108_pacote_conversor_readme.md) | (c) | Pacote `pip install pdf2md` + CLI (macro + 10 subcomandos finos) — fechado 2026-05-11 |

## `imagens` — Otimização adaptativa de imagens

Decisões arquiteturais sobre tratamento de imagens extraídas.

| Ticket | Status | Título |
|---|---|---|
| [T130](research/T130_image_optimization.md) | (r) | Otimização de imagens (meta) |
| [T131](closed/T131_classificador_e_compressao_imagens_nc.md) | (c) | Classificador + compressão níveis 1-2 (−38.6% no N&C) |
| [T135](research/T135_ssim_gate_qualidade.md) | (r) | Gate SSIM antes/depois — Frente D |
| [T136](closed/T136_breakdown_formato_stats.md) | (c) | Breakdown por formato em `_stats.md` (validado em e01) — Frente D |

## `experimento` — Hipóteses testáveis

Cada um destes tem ou terá um experimento correspondente em `lab/eNN_/` — uma
**bancada interna** que não é versionada neste repositório público; hipóteses,
critérios e vereditos estão preservados em `tickets/`, e os números promovidos
vivem em `docs/profiles/`, `docs/reference/tecnologias.md` e no `CHANGELOG.md`.

| Ticket | Status | Título | Experimento sugerido | Frente |
|---|---|---|---|---|
| [T050](closed/T050_baseline_marker_reproduzivel.md) | (c) | Baseline marker reproduzível — round-trip 95.09% (bate histórico) | `lab/e00_baseline_marker/` (.frozen) | A |
| [T070](research/T070_pixel_roundtrip_validador_visual.md) | (r) | Pixel-roundtrip L0.5 — módulo promovido em v0.6.0; validado em 4 categorias (e09-e14) | `lab/e09_*` … `lab/e14_*` | A |
| [T072](research/T072_calibracao_reconstrutor.md) | (r) | Calibração do reconstrutor — ruído base + reconstrutores múltiplos | futuro `lab/eXX_calibration/` | A |
| [T085](closed/T085_telemetry_module.md) | (c) | Módulo `pdf2md.telemetry` — instrumento (tempo/mem/cpu/gpu/io por step) — v0.5.0 | `lab/e10/` promovido | A |
| [T090](closed/T090_macro_intent_routing.md) | (c) | Macro-intent + roteador profile-aware (`--rapido`/`--qualidade`/`--auto`/`--indexacao`) | feito 2026-06-08 | A |
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
| [T075](closed/T075_tabelas_teds.md) | (c) | TEDS — **entregue 2026-06-10** (`pdf2md.table_teds` + extra `[tables]`; marker NO teto do formato pipe — 1.000 T1-T3/T5, 0.749=teto em spans; pdftotext 0.0 estrutura) | `lab/e25_tabelas_teds/` | A+C |
| [T092](closed/T092_indexacao_utility_proxies.md) | (c) | Utilidade de indexação — **entregue 2026-06-10** (math-terms marker +43..78pp; braço math do `pass2_warranted` = regra MEDIDA; braço densidade falsificado em sparse-saudável → T193) | `lab/e26_indexacao_proxies/` | A+B |
| [T193](open/T193_pass2_densidade_sparse_saudavel.md) | (o) | `pass2_warranted` — discriminar sparse-garbage de sparse-saudável (braço densidade enfileira pass2 que REGRIDE em doc diagramático, −11pp medido) | futuro `lab/e27_pass2_densidade/` | A+B |
| [T180](open/T180_reconstrucao_vetorial_imagens.md) | (o) | Reconstrução vetorial (texto + fonte + brasão residual) — escopo refinado pós-e16/e17 | `lab/e16_image_decompose/` + `lab/e17_vlm_full_page/` | E |
| [T190](closed/T190_mermaid_render_md2pdf.md) | (c) | Mermaid no md→pdf — **entregue 2026-06-10** (e22: 20/20, determinístico; `md_to_pdf(mermaid=True)` + `pdfs --mermaid`) | `lab/e22_mermaid_render/` | C |
| [T191](research/T191_diagram_to_mermaid_vlm.md) | (r) | Diagrama→mermaid via VLM local (research-tier, VLM-as-tool; irmão do T180) | futuro `lab/e23_diagram_vlm/` | E |
| [T192](open/T192_cropper_robustez_tipografia.md) | (o) | Robustez do cropper — fontes KaTeX + merge por classe de fonte (2 modos medidos no e24) | `lab/e24_gt_sintetico/` onda 4 | B+C |
| [T410](research/T410_testar_ferramentas_alternativas_nougat_mineru_pdftotext.md) | (r) | Marker × Nougat × MinerU 2.5 × olmOCR-2 × Docling | família `lab/e1X_*` | A+B+C |
| [T420](research/T420_fallback_low_resource_sem_gpu_sem_modelos_ml_pesados.md) | (r) | Fallback low-resource (sem GPU) | futuro `lab/eXX_low_resource/` | B |
| [T450](closed/T450_investigar_ibm_lesson_1_round_trip_critico.md) | (c) | IBM lesson 1 — fechado como "categoria conhecida" (bloat 3.4× via padrão de e03) | (sem lab dedicado — entendido sistemicamente) | A |

## `decisao` — Princípios, categorias, design

Discussões arquiteturais que orientam outros tickets. Vivem aqui, não em `lab/`.

| Ticket | Status | Título |
|---|---|---|
| [T031](closed/T031_definicao_de_metricas.md) | (c) | Definir métricas — `docs/reference/metricas.md` |
| [T100](research/T100_roadmap_conversor_pdf_md_bidirecional.md) | (r) | Roadmap conversor (meta original) |
| [T400](research/T400_conversor_projeto_autonomo.md) | (r) | Conversor como projeto autônomo (meta) |
| [T401](open/T401_documentar_hierarquia_de_prioridades.md) | (o) | Hierarquia de prioridades (PHILOSOPHY.md) |
| [T402](research/T402_pipeline_fractal_recursivo.md) | (r) | Pipeline fractal — ciclo recursivo por artefato (meta-organiza T132/133/134/180) |
| [T440](research/T440_md_como_formato_de_transporte_vs_pdf.md) | (r) | MD como formato de transporte vs PDF |
| [T451](research/T451_slides_pptx_como_categoria_problematica.md) | (r) | Slides PPTX como categoria problemática |

---

## Fase 0 — montar a bancada ✓ COMPLETA

Estado em **2026-05-10**: 9 macro-tickets fechados.

| ID | Ticket | Estado | Saída |
|---|---|---|---|
| T020 | Estrutura `lab/` + protocolo | ✓ closed | `lab/`, `docs/how-to/criar_novo_lab.md` |
| T021 | Manifest sources read-only | ✓ closed | `docs/reference/corpus/manifest_sources.md` |
| T022 | Cache em `Z:\` | ✓ closed | `Z:\caches\corpus\pdf2md\` |
| T023 | Convenção de venv por experimento | ✓ closed | docs em LAB_PROTOCOL |
| T024 | Reorganização tickets em faixas | ✓ closed | `kind:` + `INDEX.md` |
| T030 | Revisão de literatura | ✓ closed | `docs/explanation/literatura.md` |
| T031 | Definição de métricas | ✓ closed | `docs/reference/metricas.md` |
| T040 | Corpus canônico inicial | ✓ closed | 8 entradas (7 baixadas + 1 PMC pendente). 5/9 categorias. |
| T050 | Baseline marker reproduzível | ✓ closed | `lab/e00_baseline_marker/` (.frozen). Round-trip **95.09%** — bate histórico exato. |

Próximas famílias de experimentos (alinhadas com [Frentes do ROADMAP](../ROADMAP.md)):

- **Frente B atual — extração de conhecimento**:
  - [T160](research/T160_ocr_semantico_generalizado.md): OCR semântico generalizado (núcleo da Frente B)
  - [T060](open/T060_mini_corpus_gt_humano.md): mini-corpus de GT humano (Frente A; valida se round-trip ≈ WER vs GT real)
- **Frente C/D — captura estrutural + otimização**:
  - [T132](research/T132_potrace_svg_line_art.md), [T133](research/T133_detector_de_formula.md), [T134](research/T134_pix2tex_formulas.md), [T135](research/T135_ssim_gate_qualidade.md), [T136](closed/T136_breakdown_formato_stats.md)
- **Família `lab/e1X_*`** (T410): comparação Marker × Nougat × MinerU 2.5 × olmOCR-2 × Docling
- **Frente E — ambição**: [T180](open/T180_reconstrucao_vetorial_imagens.md) (reconstrução vetorial — escopo small-image pós-e16/e17)

Packaging (T108) **fechado** em 2026-05-11 com MVP: pacote pip + CLI unificado
(macro `pdf2md convert` + 10 subcomandos finos + `doctor`/`version`).
Refatoração de scripts standalone para módulos importáveis fica para v0.4.
