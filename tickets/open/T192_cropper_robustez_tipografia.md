---
id: T192
titulo: Robustez do cropper de fórmulas — multi-tipografia + merge por classe de fonte
status: open
criado_em: 2026-06-10
fechado_em:
fase: 4
depende_de: [T065]
blocks: []
tags: [cropper, formulas, katex, tipografia, pix2tex, robustez]
kind: experimento
altitude: execucao
---

## Contexto

O T065 (e24, ondas 2-3) mediu **dois modos de falha** do cropper promovido
(e21), que estava calibrado no espaçamento/tipografia de lecture-notes
(Preskill, pdflatex):

1. **Cego a fontes KaTeX**: 0 regiões em PDFs rendidos por Chrome+KaTeX
   (fontes `KaTeX_Main/KaTeX_Math-Italic/KaTeX_Size3` — o detector busca a
   assinatura CM/CMMI/CMSY/CMEX). PDFs web-rendered (Jupyter, docs impressos
   de browser, o próprio md→pdf do pdf2md) existem aos montes no mundo real.
2. **Merge engole prosa em layout denso** (minimal-article CM): a região
   expande além dos spans com fonte math e captura linhas de prosa vizinhas —
   o crop misto faz o pix2tex alucinar LaTeX a partir de prosa (sim ~0.02 vs
   âncora 0.80). Fórmulas display curtas (E=mc², Euler, CNOT) dão 0 regiões.

Bancada pronta: `lab/e24_gt_sintetico/` tem os MESMOS 24 itens com GT conhecido
nos DOIS renderers (`out_render/` KaTeX + `out_tectonic/` CM) — par perfeito de
teste A/B do detector.

## Hipóteses

- **H1 (tipografia)**: adicionar a família `KaTeX_*` (Math-Italic, Size*, AMS)
  ao conjunto de fontes-sinal do detector faz a detecção sair de 0/24 para
  ≥90% nos PDFs KaTeX do e24, **sem regressão** nos PDFs CM nem nos fixtures
  reais (Preskill zcache, testes existentes).
- **H2 (merge)**: limitar a expansão/merge da região a spans cuja fonte
  pertence à classe math (CMMI/CMSY/CMEX/KaTeX_Math/...; nunca CMR/KaTeX_Main
  de prosa) produz crops puros — pix2tex display no sintético CM sobe de
  ~0.02 para ≥0.6, e as fórmulas curtas passam a ser detectadas.

## Método

1. e24 onda 4: rodar o detector A/B (antes/depois de cada mudança) nos 2×24
   PDFs + nos fixtures Preskill (regressão).
2. Métricas: taxa de detecção por renderer; pureza do crop (fração de spans
   math dentro do bbox); sim pix2tex vs GT (régua da onda 3, parse corrigido).
3. Só então o teste pendente do T065: **fraqueza de matrizes ~0.5 reaparece?**

## Critério de promoção

Detecção ≥90% nos 2 renderers; crops sem prosa (pureza ≥0.9); pix2tex display
≥0.6 no sintético CM; **zero regressão** em `tests/test_formula_cropper.py` e
nos crops reais do Preskill (e21 recall mantido).

## Critério de descarte

Se H2 exigir reescrever o detector além de (lista de fontes + regra de merge)
— p.ex. exigir layout-model — registra como limite arquitetural do caminho
heurístico-CPU e o caso denso fica documentado como fora da banda (routing
pode usar densidade como gate). H1 não tem descarte plausível (é tabela de
fontes); se falhar, o detector tem acoplamento mais profundo que fonte — vale
investigação antes de qualquer outra promoção.

## Deps

Zero pip novo. Bancada e24 + tectonic (`Z:\bin`) + pix2tex (venv e18) já
instalados.

## Conexão

- Destrava a onda 4 do [T065](T065_corpus_gt_sintetico.md) (matriz ~0.5) e a
  promoção completa do corpus sintético.
- Amplia o caminho CPU ([T133](../research/T133_detector_de_formula.md)/
  [T134](../research/T134_pix2tex_formulas.md), e21) para PDFs web-rendered —
  caso real, não só o sintético.
