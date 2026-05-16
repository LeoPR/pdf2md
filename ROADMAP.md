# Roadmap

*Atualizado 2026-05-16, v0.7.0. Para perfis cross-recursos das tecnologias
ver [`docs/reference/tecnologias.md`](docs/reference/tecnologias.md); para análise crítica da
trajetória ver [`docs/explanation/analise_critica.md`](docs/explanation/analise_critica.md).*

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

**Detalhamento completo**: [`docs/explanation/arquitetura.md`](docs/explanation/arquitetura.md). Por camada:

| Camada | Documento | Estado atual |
|---|---|---|
| 1 — Extração | [`docs/explanation/arquitetura/01_extracao.md`](docs/explanation/arquitetura/01_extracao.md) | marker-pdf 1.10.2 (GPU) |
| 2 — Otimização | [`docs/explanation/arquitetura/02_otimizacao.md`](docs/explanation/arquitetura/02_otimizacao.md) | PNG paleta lossy (T131) |
| 3 — Reconstrução | [`docs/explanation/arquitetura/03_reconstrucao.md`](docs/explanation/arquitetura/03_reconstrucao.md) | pandoc + Chrome + KaTeX |
| 4 — Métrica | [`docs/explanation/arquitetura/04_metricas.md`](docs/explanation/arquitetura/04_metricas.md) | round-trip 95.09% N&C, 91-99% corpus |
| Pipeline | [`docs/explanation/arquitetura/05_pipeline.md`](docs/explanation/arquitetura/05_pipeline.md) | scripts standalone em `src/` |

Eixo ortogonal de **representação** (raster → texto semântico) em [`docs/explanation/philosophy.md §"Eixo de representação"`](docs/explanation/philosophy.md).

---

## Frentes de cobertura

Cinco frentes representam o escopo total do conversor. Cada frente tem ROI
decrescente. Trabalho ativo segue ordem alfabética dentro do que está priorizado;
**Frente B (extração de conhecimento) é a frente atual** após Fase 0 (bancada montada).

| Frente | Conteúdo | Tickets | Estado (2026-05-16) |
|---|---|---|---|
| **A — Validação** | round-trip textual + visual + GT humano + multi-iteration; instrumentação | [T050](tickets/closed/T050_baseline_marker_reproduzivel.md) ✓, [T060](tickets/open/T060_mini_corpus_gt_humano.md) (open), [T070](tickets/research/T070_pixel_roundtrip_validador_visual.md) (parcial v0.6), [T072](tickets/research/T072_calibracao_reconstrutor.md), [T085](tickets/closed/T085_telemetry_module.md) ✓ v0.5, [T076](tickets/closed/T076_md_to_pdf_overwrite_silencioso.md) ✓ v0.4.1 | **avançada** — pixel-roundtrip pipeline pronto (v0.6+v0.7); falta GT humano + calibração |
| **B — Captura textual** | máximo de texto incluindo OCR de imagens-com-texto; preserva 1ª prioridade da [PHILOSOPHY](docs/explanation/philosophy.md) | [T101](tickets/closed/T101_marker_pdf_extraction_com_gpu_rtx_3060.md) ✓, [T160](tickets/research/T160_ocr_semantico_generalizado.md) (research) | parcial; T160 generaliza |
| **C — Captura estrutural** | tabelas, headers, fórmulas e imagens com semântica preservada (2ª prioridade) | [T102](tickets/closed/T102_restructure_output_por_capitulo_indexmd.md) ✓, [T132](tickets/research/T132_potrace_svg_line_art.md), [T133](tickets/research/T133_detector_de_formula.md), [T134](tickets/research/T134_pix2tex_formulas.md) | em progresso |
| **D — Otimização de representação** | formato adaptativo, lossless, denoise; ascende no [eixo de representação](docs/explanation/philosophy.md#eixo-de-representação) | [T131](tickets/closed/T131_classificador_e_compressao_imagens_nc.md) ✓, [T135](tickets/research/T135_ssim_gate_qualidade.md), [T136](tickets/closed/T136_breakdown_formato_stats.md) ✓, [T137](tickets/research/T137_denoising_jpeg_pre_compressao.md) | parcial |
| **E — Reconstrução vetorial** | texto + fonte + geometria + brasão residual; Nível 4 do eixo de representação | [T180](tickets/research/T180_reconstrucao_vetorial_imagens.md) (research) | ambição — ainda 0% |
| **Meta-design** | tese da família + roteamento profile-aware | [T401](tickets/open/T401_documentar_hierarquia_de_prioridades.md), [T402](tickets/research/T402_pipeline_fractal_recursivo.md), [T090](tickets/research/T090_macro_intent_routing.md) | **avançada** — PHILOSOPHY + META_TRANSMUTOS + MD_CANONICAL + TECNOLOGIAS prontos; routing pendente |

A ordem natural de execução é A → B → C → D → E, mas frentes podem rodar em paralelo conforme experimentos abrem.

**Frente atual** (2026-05-16): A está chegando ao final do ciclo "validar como medir" — T060 (GT humano) é o último gargalo para destravar calibração T072 e fechar T070 plenamente.

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

### Fase 2 — Adoção e empacotamento ✓ ESTÁVEL

- [x] [T107](tickets/open/T107_md_to_pdf_per_chapter.md) MD → PDF por capítulo (`pdf2md pdfs`)
- [x] [T108](tickets/closed/T108_pacote_conversor_readme.md) `pip install pdf2md` com CLI unificado (v0.4)
- [x] **v0.5.0** `pdf2md.telemetry` ([T085](tickets/closed/T085_telemetry_module.md))
- [x] **v0.6.0** `pdf2md.pixel_roundtrip` ([T070](tickets/research/T070_pixel_roundtrip_validador_visual.md) parcial)
- [x] **v0.7.0** rt-pixel integrado no convert (`--rt-pixel` / `--best`)

### Fase 3 — Otimização adaptativa de imagens (família T130)

- [x] [T131](tickets/closed/T131_classificador_e_compressao_imagens_nc.md) Classificador adaptativo PNG B&W / paleta lossy
- [ ] [T132](tickets/research/T132_potrace_svg_line_art.md) potrace para line art → SVG
- [ ] [T133](tickets/research/T133_detector_de_formula.md) Detector de fórmula (heurística + bbox)
- [ ] [T134](tickets/research/T134_pix2tex_formulas.md) pix2tex para fórmulas detectadas
- [ ] [T135](tickets/research/T135_ssim_gate_qualidade.md) Gate SSIM antes/depois
- [ ] [T136](tickets/open/T136_breakdown_formato_stats.md) Breakdown por formato no `_stats.md`
- [ ] [T137](tickets/research/T137_denoising_jpeg_pre_compressao.md) Restauração de artefatos JPEG

### Fase 4 — Diversificação do pipeline (em progresso)

**Alt-tools (T410) — status de cada candidato testado:**

| Tool | Lab | Resultado | Próximo |
|---|---|---|---|
| Marker `--use_llm` + Ollama `llama3.2-vision:11b` | [e07](lab/e07_marker_llm/RESULT.md) | descartado p/ esse modelo+tool específico (40× lento) | testar outros VLMs via outras tools |
| MinerU 2.5-Pro | [e06](lab/e06_mineru25_pro/RESULT.md) | **blocked** Win+RTX3060 (FastAPI server crash silencioso) | re-tentar Linux ou API direta |
| Granite-Docling-258M (Q16) | [e08](lab/e08_granite_docling/RESULT.md) | descartado p/ N&C (50× lento, base64 imgs) | considerar p/ casos curtos / single-file |
| Nougat / olmOCR-2 / Docling full | — | pendentes | sequenciar após T060 GT pronto |
| pdftotext / PyMuPDF puro / Tesseract (T420) | — | pendentes | fallback low-resource explícito |

- [ ] [T410](tickets/research/T410_testar_ferramentas_alternativas_nougat_mineru_pdftotext.md) (em andamento — 3 candidatos testados; 3+ pendentes)
- [ ] [T420](tickets/research/T420_fallback_low_resource_sem_gpu_sem_modelos_ml_pesados.md) Stack low-resource (sem GPU)
- [ ] [T440](tickets/research/T440_md_como_formato_de_transporte_vs_pdf.md) MD compactado como formato de distribuição
- [ ] [T160](tickets/research/T160_ocr_semantico_generalizado.md) OCR semântico generalizado (Frente B)
- [ ] [T180](tickets/research/T180_reconstrucao_vetorial_imagens.md) Reconstrução vetorial (Frente E)
- [ ] [T090](tickets/research/T090_macro_intent_routing.md) Macro-intent CLI (`--rapido`/`--qualidade`/`--auto`) — depende de mapa de perfis com 3+ tools

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
