---
id: T190
titulo: Mermaid no md→pdf — render client-side no pipeline pandoc+Chrome
status: closed
criado_em: 2026-06-09
fechado_em: 2026-06-10
fase: 4
depende_de: []
blocks: [T191]
tags: [mermaid, diagramas, md2pdf, render, bidirecional]
kind: experimento
altitude: execucao
---

## Contexto

O eixo diagramas está AUSENTE nas duas direções (grep mermaid = 0 no repo).
Um bloco ```` ```mermaid ```` hoje sai como code block literal no PDF. Esta é
a metade BARATA do eixo: o pipeline `pdfs.py` já renderiza KaTeX client-side
no Chrome headless (`--virtual-time-budget`) — mermaid.js é a mesma classe de
solução. Sem render não há round-trip de diagrama; logo T190 destrava T191.

## Hipótese

H1: injetar mermaid.js (v11, pinado) no HTML do pandoc — Lua filter (~10
linhas) convertendo CodeBlock `.mermaid` em `<pre class="mermaid">` +
`--include-in-header` com `mermaid.initialize({startOnLoad:true})` — faz o
Chrome headless EXISTENTE renderizar ≥95% de uma suíte de 20 diagramas
sintéticos (flowchart TD/LR, sequence, state, class) **sem alterar a invocação
do Chrome** e sem novo processo no pipeline.
H1-aux: render determinístico — 3 execuções → SSIM par-a-par ≥0.99 por página.

## Método / métricas

- Taxa de render: % de diagramas com tinta na região esperada (raster via
  pymupdf + contagem de pixels não-brancos no bbox; bloco não-renderizado fica
  como texto monoespaçado — assinatura detectável).
- SSIM (`page_ssim` do pixel_roundtrip) contra render de referência do MESMO
  source via mmdc (mermaid-cli) — mesmo engine, esperado ≥0.90.
- Determinismo: SSIM entre 3 runs.
- Latência adicional por página vs md_to_pdf sem mermaid (futura dimensão de
  profile).

## Critério de promoção

Flag/adapter opcional em `pdfs.py` (princípio delta-E: quirk de renderer vive
em adapter, não contamina o caminho canônico) + suíte sintética versionada
(insumo do T065) + entrada no doctor se houver dependência detectável.

## Critério de descarte

Taxa de render <80% após ajuste de virtual-time-budget; OU render
não-determinístico (páginas em branco intermitentes em 3 runs — flakiness de
timing JS é veneno pro instrumento); OU a integração exigir fork de
`md_to_pdf` além de flag/adapter. Fallback documentado antes do descarte
definitivo: pré-render via mmdc/mermaid-filter no passo pandoc (npm+puppeteer,
dependência externa mais pesada).

## Deps

Nenhuma dep pip nova. mermaid.min.js pinado (~2.5MB, MIT): vendorado ou via
CDN absorvido pelo `--embed-resources` que o pandoc já usa — mesma classe da
dep KaTeX atual. mmdc só como renderer de REFERÊNCIA no lab
(external-capability opcional, não entra no produto).

## Não-objetivo

- Extrair diagrama de PDF (T191).
- Suportar TODOS os tipos mermaid (gantt, pie, etc.) — flowchart/sequence/
  state/class bastam para a hipótese.

## Conexão

- Destrava [T191](../research/T191_diagram_to_mermaid_vlm.md) (round-trip de
  diagrama) e enriquece [T065](T065_corpus_gt_sintetico.md) (categoria
  diagrama no corpus sintético).
- Bidirecionalidade: primeira capacidade rica do md→pdf além de KaTeX.

## Resultado (e22, 2026-06-10) — H1 CONFIRMADA, promovido

- **Render 20/20** (flowchart TD/LR, sequence, state, class × 4 tamanhos);
  detector validado nos dois sentidos (20/20 controles sem adapter acusaram
  code block literal).
- **Determinismo perfeito**: SSIM 1.0000 par-a-par em 3 runs, 20/20 docs.
- **Achado**: diagramas altos (TD/state/class ≥6-8 nós) eram empurrados pelo
  `page-break-inside: avoid` e fatiados em 2-5 páginas. Primeira leitura do
  detector (só pg0) deu falso-negativo 13/20 — lição: detector de render tem
  que agregar TODAS as páginas. Mitigado na promoção com
  `pre.mermaid svg { max-height: 23cm }`: piores casos (12 nós) caem para
  2 páginas, diagrama inteiro sem corte.
- **Latência**: ~7s/doc com adapter (JS 2.6MB inline no header).
- **Promoção**: `md_to_pdf(..., mermaid=True)` + `pdf2md pdfs --mermaid`;
  mermaid 11.4.1 (MIT) + Lua filter vendorados em `src/pdf2md/_vendor/`
  (package-data) — md→pdf segue offline. 2 testes de regressão (detector do
  e22) em `tests/test_pdfs.py`. Sem entrada nova no doctor (zero dependência
  externa nova).