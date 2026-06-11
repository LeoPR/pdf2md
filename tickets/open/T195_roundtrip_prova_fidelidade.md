---
id: T195
titulo: Roundtrip-como-prova — instrumento de fidelidade não-supervisionada em 2 eixos
status: open
criado_em: 2026-06-10
fechado_em:
fase: 4
depende_de: [T065, T070, T092]
blocks: [T194]
tags: [roundtrip, fidelidade, prova, instrumento, ssim, metrica, caixa-preta, moat]
kind: experimento
altitude: execucao
---

## Contexto — a razão de existir do projeto, posta à prova

A identidade defensável do pdf2md não é "mais um extrator" (marker/MinerU/
DeepSeek-OCR/olmOCR dominam extração bruta), e sim **roteador + instrumento
que PROVA fidelidade da extração num PDF sem ground-truth**. Esta prova é o
moat. Este ticket a desafia com critério que pode matar o projeto.

**Princípio (abstrato, ≠ instrumento):** comparar a *imagem da renderização
original* com a *imagem da renderização pós-extração*. O SSIM (pixel_roundtrip,
T070) é só UMA régua dessa comparação — escolhida por ser boa no geral, mas
com falso-negativo conhecido por reflow (extração fiel que reflui → imagem
diferente → SSIM pune). A métrica de comparação é **componente plugável**;
o teto do método não é o teto do SSIM.

**Epistemologia (caixa-preta, decompilador):** não recuperamos o processo que
*criou* o PDF (inacessível); recuperamos uma representação que **recompila ao
mesmo observável** (os pixels renderizados). O que foi extraído REPRESENTA a
informação que regenera a página — ainda que em forma programática/opaca. Isso
é cycle-consistency sobre o invariante observável, não sobre a fonte. A
fidelidade é provada *relativa ao nosso motor de reconstrução* (md→pdf) —
feature delta-E, não bug: prende a representação ao substrato MD legível.

**Os 2 eixos ortogonais (correção que o caso degenerado motivou):**

|  | qualidade ALTA (legível/simbólico/compacto) | qualidade BAIXA (raster/opaco) |
|---|---|---|
| **fidelidade ALTA** (regenera) | extração ótima | "embed-PNG": fiel mas inútil — MEDIDO, não escondido |
| **fidelidade BAIXA** (não regenera) | **alucinação** (parece ok, não confere) | falha total |

O instrumento não é enganado pelo embed-PNG: reporta fidelidade≈1.0,
qualidade≈0.1 — resposta correta ("regenera mas não te dá nada indexável").
O quadrante perigoso (alucinação) é o que benchmark one-shot não pega.

## Hipóteses

- **H1 (calibração — eixo fidelidade):** no corpus sintético (verdade de
  conteúdo CONHECIDA, T065), o score de roundtrip-imagem correlaciona com a
  fidelidade-de-conteúdo real (Spearman ρ ≥ 0.7). Entre as métricas candidatas
  de comparação (SSIM; OCR-nas-2-imagens+sim-de-texto; e ao menos uma 3ª), há
  uma que correlaciona MELHOR que o SSIM — adotada como régua de fidelidade.
- **H2 (eixo qualidade separa degeneração):** um índice de qualidade
  representacional (densidade simbólica / fração não-rasterizada / razão de
  compressão MD-vs-imagem) coloca uma extração degenerada injetada (forçar
  embed-PNG da página) em fidelidade-alta/qualidade-baixa, e uma boa em
  alta/alta — separação ≥ 2 desvios.
- **H3 (discriminação sem GT — o moat):** em PDFs reais (sem GT), o instrumento
  detecta uma degradação CONTROLADA (dropar 30% do texto da extração antes de
  reconstruir) como queda de fidelidade ≥ X (limiar fixado na calibração),
  SEM usar nenhum ground-truth — e separa pdftotext de marker de forma coerente
  com um spot-check humano pequeno.

## Método (ondas)

1. **Onda 0 — régua e calibração (sintético, barata, CPU):** reusar
   `pixel_roundtrip` (SSIM+align) e adicionar 1-2 métricas de comparação
   candidatas (OCR-Tesseract nas 2 imagens + token-sim; opcional perceptual).
   Para cada doc do sintético: fidelidade-conteúdo conhecida (do GT) × cada
   métrica de roundtrip → correlação. Computar o eixo qualidade. Injetar
   degeneração embed-PNG e degradação-30%. Escolher régua de fidelidade +
   fixar limiares. **Decide H1/H2 antes de tocar em PDF real.**
2. **Onda 1 — discriminação no real (sem GT):** PDFs `corpus/examples` (arxiv,
   cdc, irs, wilson) + diversos. pdftotext vs marker → posicionar no plano
   2-eixos. Degradação controlada → o instrumento pega sem GT? Spot-check
   humano de 4-6 casos confirma o ranking? **Decide H3.**
3. **Onda 2 (condicional, só se H1-H3 passam):** generalizar o instrumento
   como `fidelity_report()` promovível e ligá-lo ao T194-F3 (rodar a saída de
   QUALQUER extrator — marker/MinerU/etc. — no mesmo plano; é assim que se
   gera a evidência que falta sobre outros extratores).

## Métricas

- Fidelidade: a régua vencedora da onda 0 (SSIM ou melhor), em [0,1].
- Qualidade representacional: índice composto (fração de área não-rasterizada
  do output; densidade de tokens simbólicos vs página; razão bytes-MD/bytes-se-
  fosse-imagem). Reusa structure-counts do e26/T092.
- Correlação fidelidade↔verdade-conhecida: Spearman/Pearson no sintético.
- Sensibilidade: queda de fidelidade sob degradação-30% (efeito mensurável).

## Critério de promoção

Régua de fidelidade calibrada (correlação ≥0.7 no sintético) + eixo qualidade
que separa degeneração + detecção de degradação sem GT no real ⇒ `fidelity_
report()` vira módulo/lab promovível, coluna nos profiles, e **base do T194-F3**
(referee de extratores externos). O projeto ganha sua prova de valor.

## Critério de descarte (pode matar o moat — registrar honestamente)

- Se NENHUMA métrica de comparação correlacionar com a verdade conhecida no
  sintético (ρ<0.7 em todas) ⇒ o roundtrip-imagem não mede fidelidade de
  conteúdo; o moat como "prova" cai (vira no máximo smoke-test de layout).
- Se o eixo qualidade não separar embed-PNG de extração boa ⇒ o instrumento é
  enganável; precisa redesenho antes de qualquer claim.
- Se no real o instrumento não distinguir extração boa de degradada-30% ⇒ sem
  poder discriminativo onde importa (PDF sem GT). Registrar o envelope: pode
  valer só em doc texto-pesado e ser cego em foto-pesado (limite conhecido).

## Deps

Zero pip novo no núcleo: pixel_roundtrip (extra `[rtpixel]`, já existe),
Tesseract (external, `[ocr]`) p/ a métrica OCR-based, corpus sintético (T065),
structure-counts (e26). marker p/ a onda 1 (GPU já em uso). Bancada efêmera
`lab/e28_roundtrip_prova/`.

## Não-objetivo

- Recuperar o processo gerador original do PDF (inacessível por design —
  caixa-preta; só provamos recompilação ao observável).
- Treinar uma métrica perceptual nova (usar prontas; calibrar a ESCOLHA).
- Cobrir foto-pesado como caso forte (registrar como borda do envelope).
- Ranking público de extratores externos (isso é T194-F3, ALIMENTADO por aqui).

## Conexão

- Endurece o princípio de [T070](../research/T070_pixel_roundtrip_validador_visual.md)
  (pixel-roundtrip) de "validador visual" para "instrumento de prova de
  fidelidade não-supervisionada em 2 eixos".
- Usa o GT-por-construção do [T065](../closed/T065_corpus_gt_sintetico.md) p/
  calibrar a régua (a verdade conhecida que falta no real).
- Reusa eixo de qualidade/densidade do [T092](../closed/T092_indexacao_utility_proxies.md).
- É a fundação do [T194](../research/T194_programa_comparativo_cientifico.md)-F3:
  só com o instrumento provado dá pra rodar marker/MinerU/DeepSeek-OCR na nossa
  régua e gerar a evidência que hoje falta sobre outros extratores.
- Materializa a tese decompilador/recompilador do
  [transmutos.md](../../docs/explanation/transmutos.md).
