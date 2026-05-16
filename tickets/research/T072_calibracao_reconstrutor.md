---
id: T072
titulo: Calibração do reconstrutor como instrumento (ruído base + reconstrutores múltiplos)
status: research
criado_em: 2026-05-15
fechado_em:
fase: 4
depende_de: [T060, T070]
blocks: []
tags: [conversor, roundtrip, reconstrucao, calibracao, frente-a]
kind: experimento
---

## Contexto

A cadeia `MD → PDF` atual (pandoc + Chrome + KaTeX) tem **perdas
próprias** mesmo dado MD perfeito:

- KaTeX falha silenciosamente em macros LaTeX exóticos
- Chrome não usa hinting de fonte igual ao engine de origem
- Pandoc reordena elementos em casos ambíguos
- Limite expressivo do MD (sem CSS-de-impressão, sem multi-coluna fluido)

Sem **calibração**, não dá pra distinguir "extração ruim" de
"reconstrutor limitado". Métrica visual (T070) mistura os dois.

Formulação em [PHILOSOPHY §"Calibração do reconstrutor"](../../docs/explanation/philosophy.md#calibração-do-reconstrutor-como-instrumento):
medir o ruído base da cadeia subtrai a perda fixa do reconstrutor.

## Hipótese

(H1) Existe ruído base **mensurável e estável** do reconstrutor atual
(pandoc+Chrome+KaTeX) — propriedade do toolchain, não do PDF de
entrada. Manifesta-se como `visual_diff_floor` ≈ constante para uma
classe de docs.

(H2) Reconstrutores alternativos (Tectonic, Typst, WeasyPrint) têm
perfis de perda **diferentes**. Discordância entre eles localiza áreas
onde o MD não é expressivo o bastante — sinal para subir no eixo de
representação.

## Método

1. **Ruído base** (depende de T060 ter mini-corpus GT):
   - Para cada doc GT em `corpus/_gt/`:
     - `MD_GT → pandoc+Chrome+KaTeX → PDF_ref`
     - `MD_GT → Tectonic / LaTeX → PDF_ideal` (quando MD é LaTeX-renderizável)
     - `ruído_base[doc] = pixel_roundtrip_triangle(PDF_ref, PDF_ideal)`
   - Reportar mediana + desvio: caracteriza "ruído fixo"

2. **Subtração na métrica futura**:
   - Para extração nova: `erro_extração ≈ pixel_diff - ruído_base`
   - Métrica reportada: `acima_do_floor = diff - ruído_base`

3. **Diversidade de reconstrutores** (sub-experimento):
   - Mesmo MD em pandoc+Chrome, Tectonic, Typst (quando aplicável), WeasyPrint
   - Comparar SSIM de cada vs `PDF_ideal`
   - Discordância > threshold → flag "MD ambíguo" (sinal para subir
     no eixo de representação)

4. **Output**:
   - Módulo `pdf2md/calibration.py` com:
     - `compute_reconstructor_floor(md_gt_dir) -> dict[doc, triangle_diff]`
     - `subtract_floor(measured_diff, floor) -> adjusted_diff`
   - Subcomando `pdf2md calibrate <md_gt_dir>`

## Critérios de aceitação

- [ ] Ruído base computado em N=5 docs do mini-corpus GT (T060)
- [ ] Variância do ruído entre docs < 30% da mediana (sinal de
      propriedade do toolchain, não do doc)
- [ ] Pelo menos 1 caso em que `acima_do_floor` muda a interpretação
      (ex: doc com SSIM 0.85 mas floor 0.83 → extração ~perfeita)
- [ ] Comparação com ≥ 2 reconstrutores (mín. pandoc+Chrome + Tectonic
      ou Typst)
- [ ] Tests cobrindo: floor de MD idêntico = baixo, MD com erro alto = alto

## Critério de promoção

- Métrica `acima_do_floor` incorporada ao `_stats.json` para todas as extrações
- Atualizar METRICS.md classificando "Pixel-roundtrip calibrado" como métrica primária
- Documentar quando floor precisa ser recomputado (mudança de versão de pandoc, Chrome, KaTeX)

## Não-objetivo

- Implementar reconstrutor próprio
- Substituir pandoc+Chrome+KaTeX em produção (continua sendo padrão; outros são para calibração)
- Calibrar contra cada PDF individualmente — floor é por classe/toolchain, não por doc

## Conexão

- Frente A (validação)
- Depende de [T060](../open/T060_mini_corpus_gt_humano.md) (GT humano) — sem MD com
  garantia "tem toda a info", não dá pra medir o ruído base
- Depende de [T070](T070_pixel_roundtrip_validador_visual.md) (pixel-roundtrip)
- Vincula a [PHILOSOPHY §"Calibração"](../../docs/explanation/philosophy.md#calibração-do-reconstrutor-como-instrumento)
- Habilita [T402](T402_pipeline_fractal_recursivo.md) — calibração é a mesma ideia
  recursivamente em outros níveis (calibrar pix2tex contra LaTeX, calibrar
  potrace contra SVG vetorial puro, etc.)
