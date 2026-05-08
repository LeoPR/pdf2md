# Roadmap

Quadro de fases. Cada item aponta para tickets concretos em
[`tickets/`](tickets/).

## Fase 1 — Pipeline básico (estável)

- [x] Extração via `marker-pdf` com GPU (T101)
- [x] Reorganização por capítulo via TOC (T102)
- [x] Round-trip MD → PDF → MD' (T103)
- [x] Telemetria por extração (`stats.py`)
- [x] Telemetria agregada (`aggregate_stats.py`)
- [x] Multi-iteration round-trip (`multi_roundtrip.py`)

## Fase 2 — Adoção e empacotamento

- [ ] [T107](tickets/open/T107_md_to_pdf_per_chapter.md): MD → PDF
      por capítulo via Chrome (parcialmente feito; falta integrar)
- [ ] [T108](tickets/open/T108_pacote_conversor_readme.md): empacotar
      como `pip install pdf2md` com CLI unificado (`pdf2md extract`,
      `pdf2md roundtrip`, `pdf2md stats`, etc.)

## Fase 3 — Otimização de imagens (`T130` família)

- [x] [T131](tickets/closed/T131_classificador_e_compressao_imagens_nc.md):
      classificador adaptativo PNG B&W / paleta lossy (níveis 1-2)
- [ ] T132: integrar potrace para line art → SVG
- [ ] T133: detector de fórmula (heurística + bbox)
- [ ] T134: pix2tex para fórmulas detectadas
- [ ] T135: gate de qualidade SSIM antes/depois
- [ ] T136: breakdown por formato no `_stats.md`
- [ ] [T137](tickets/research/T137_denoising_jpeg_pre_compressao.md):
      restauração de artefatos JPEG antes da compressão

## Fase 4 — Diversificação do pipeline

- [ ] [T410](tickets/research/T410_testar_ferramentas_alternativas_nougat_mineru_pdftotext.md):
      Nougat, MinerU, pdftotext, PyMuPDF heurístico, Mathpix, pix2tex
- [ ] [T420](tickets/research/T420_fallback_low_resource_sem_gpu_sem_modelos_ml_pesados.md):
      stack viável sem GPU / com pouca RAM
- [ ] [T440](tickets/research/T440_md_como_formato_de_transporte_vs_pdf.md):
      MD compactado como formato de distribuição

## Fase 5 — Corpus e validação

- [ ] [T430](tickets/open/T430_corpus_livre_para_testes_urls_licencas.md):
      lista de PDFs livres/CC para teste sistemático
- [ ] [T450](tickets/open/T450_investigar_ibm_lesson_1_round_trip_critico.md):
      diagnóstico do caso crítico (slide PPTX, 28.9%, token bloat 3.4×)
- [ ] [T451](tickets/research/T451_slides_pptx_como_categoria_problematica.md):
      enquadramento dos slides PPTX como categoria distinta

## Meta — design

- [ ] [T401](tickets/open/T401_documentar_hierarquia_de_prioridades.md):
      registrar e refinar hierarquia conforme novos casos surgirem
- [ ] [T400](tickets/research/T400_conversor_projeto_autonomo.md): meta-ticket
      do projeto autônomo (este projeto inteiro)
- [ ] [T100](tickets/research/T100_roadmap_conversor_pdf_md_bidirecional.md):
      roadmap original (mantido como histórico)

## Não-objetivos atuais

- Reproduzir layout PDF byte-a-byte (4ª prioridade da PHILOSOPHY)
- Suportar todos os tipos de PDF — slides PPTX são caso conhecido com
  qualidade reduzida (T451)
- Substituir `marker-pdf` — é a base; ferramentas alternativas (T410)
  são para fallback ou comparação, não substituição
