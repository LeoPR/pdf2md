---
id: T450
titulo: Investigar IBM lesson 1 — round-trip crítico (28.9%, token bloat 3.4x)
status: open
criado_em: 2026-05-07
fechado_em:
fase: 1
depende_de: [T100]
blocks: []
tags: [conversor, debug, round-trip, slides, pptx]
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
