---
id: T450
titulo: Investigar IBM lesson 1 — round-trip crítico (28.9%, token bloat 3.4x)
status: closed
criado_em: 2026-05-07
fechado_em: 2026-05-10
fase: 1
depende_de: [T100]
blocks: []
tags: [conversor, debug, round-trip, slides, pptx]
kind: experimento
---

## Contexto

Único documento marcado como **crítico** no `_OVERVIEW.md` da pasta
`pesquisa_geral/`. Round-trip caiu para **28.90%** vs média geral de
~72%. O sintoma incomum é o **token bloat na re-extração**:

| | Tokens |
|---|---|
| MD original (extração 1) | 4,629 |
| MD re-extraído (após PDF→MD) | **15,637** |
| Razão | **3.4x** |

98.5% das divergências são `math`. O conteúdo "explodiu" no segundo
passe pelo marker.

## Hipóteses a investigar

| # | Hipótese | Como testar |
|---|---|---|
| H1 | Marker re-OCR'iza fórmulas que viraram imagens no PDF intermediário, gerando texto duplicado (fórmula em LaTeX + texto OCR'izado da imagem da fórmula renderizada) | Diff visual MD₁ vs MD₂; procurar por padrão de fórmula seguida de transcrição em texto plano |
| H2 | Pandoc+KaTeX renderiza fórmulas como SVG/PNG inline no PDF, e marker as captura DUAS vezes — uma como math e outra como bloco de texto | Inspecionar HTML intermediário gerado pelo pandoc |
| H3 | Slides PPTX têm fórmulas como **imagens embutidas** (não LaTeX nativo). Marker já tinha que OCR'izar no extract 1; no extract 2, com PDF re-renderizado, a OCR fica menos consistente | Comparar `_page_*.jpeg` no `images/` — quantos parecem fórmulas |
| H4 | `--virtual-time-budget=20000` no Chrome insuficiente para slides longos com KaTeX; PDF intermediário sai cortado/parcial e marker preenche com lixo | Testar com budget de 60s ou validar PDF intermediário |
| H5 | Marker em modo padrão usa fluxo de "livros" e quebra em slides PPT — cada slide vira mini-página e o agrupador estoura | Tentar `--use_llm` ou outro flag de marker |

## Plano de investigação

1. Re-rodar `roundtrip.py` mas **preservar o PDF intermediário** e o MD₂ para inspeção
2. Diff visual `MD₁` vs `MD₂` — focar nos primeiros 50 e últimos 50 tokens divergentes
3. Inspecionar `images/` da extração original — quantas das 49 imagens são fórmulas?
4. Validar H1/H2 olhando se há repetição literal de strings entre versões
5. Re-extrair com flags alternativas do marker (se disponíveis)

## Critério para fechar

Diagnosticada a causa do bloat 3.4x. Pelo menos uma destas:
- Patch no `roundtrip.py` que mitiga o problema (ex: limpar imagens de fórmula renderizadas antes do marker), com nova métrica > 60%
- Documentação clara: "slides PPTX com fórmulas-como-imagem têm round-trip ruim por X — workaround: Y"
- Decisão de **não tentar round-trip** para slides PPTX e sinalizar isso no `_stats.md`

## Não-objetivo

- Não é objetivo trazer slide PPTX para 95%+. Slides são intrinsecamente
  lossy para o pipeline (fórmulas-como-imagem). Objetivo é entender o
  failure mode e parar de mostrar como "outlier" o que é apenas
  "categoria conhecida".

## Dados disponíveis

- Stats: `pesquisa_geral/material_aulas/semana2_ibm_lesson_1_singlesystems/_stats.md`
- MD₁: `pesquisa_geral/material_aulas/semana2_ibm_lesson_1_singlesystems/semana2_ibm_lesson_1_singlesystems.md`
- PDF original: `pesquisa_geral/_sources/material_aulas/Semana2_IBM-Lesson-1-SingleSystems.pdf`

---

## Resolução (2026-05-10)

**Fechado como "categoria conhecida"** após o experimento `lab/e03_atkins_wilson_scan/` (commit `e194ad5`) revelar o **padrão sistemático** que explica o bloat.

### Diagnóstico definitivo

O bloat de 3.4× **não é peculiaridade de IBM lesson 1** — é manifestação de um padrão geral observado em **outros casos**:

| caso | MD₁ tokens | MD₂ tokens | bloat | rt% |
|---|---:|---:|---:|---:|
| Wilson 1800 (e03) | 2,748 | 21,177 | **7.7×** | **13.62%** |
| **IBM lesson 1 (este ticket)** | **4,629** | **15,637** | **3.4×** | **28.9%** |

Causa raiz: **descompasso entre input pobre e re-OCR sem âncora**. Quando o marker extrai pouco conteúdo do PDF original (slides com fórmulas-como-imagem, scans manuscritos), o MD₁ fica esparso. Esse MD₁ → PDF (via pandoc + Chrome + KaTeX) gera um PDF intermediário **renderizado limpo** que o marker processa novamente, e dessa vez **OCR-iza muito mais coisa** — incluindo fórmulas que nem estavam no MD₁ (alucinação massiva).

Das 5 hipóteses H1-H5 originais, **H1 e H3 estão corretas e combinadas**: marker re-OCR-iza fórmulas-como-imagem (H1) **porque** o PPTX tem fórmulas embutidas como imagem (H3), gerando texto que não estava no original.

H4 (Chrome virtual-time-budget) **não é causa** — Wilson teve o mesmo padrão sem usar slides PPTX.

### Decisão

- **Não há fix técnico simples**. O problema é da Camada 3 (reconstrução) reagindo a Camada 1 com pouco conteúdo.
- **Sinalização automática implementada** em [T071](T071_bloat_ratio_alucinacao_heuristica.md) — `stats.py` agora reporta `bloat_ratio` e dispara flag 🚨 PADRÃO DE ALUCINAÇÃO quando bloat > 3.0 ou (bloat > 2.0 + densidade < 200 tokens/página).
- **PDFs nessa categoria** (slides com math-como-imagem, scans manuscritos densos) ficam tratados como **caso conhecido**, não outlier. T451 (slides PPTX) já cataloga a família.

### O que não precisava ser investigado mais

H4 (Chrome budget) — descartada via Wilson (e03) que tem o mesmo padrão sem ser PPTX.
H5 (marker flag) — irrelevante; problema não é fluxo do marker, é descompasso de informação.

### Cross-references

- [T071](T071_bloat_ratio_alucinacao_heuristica.md) — heurística implementada
- [T451](../research/T451_slides_pptx_como_categoria_problematica.md) — categoria PPTX em research (continua)
- `lab/e03_atkins_wilson_scan/RESULT.md` — discussão completa
