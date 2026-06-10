---
id: T065
titulo: Corpus GT-por-construção — sintético, autoral, publicável
status: open
criado_em: 2026-06-09
fechado_em:
fase: 4
depende_de: [T060]
blocks: [T075, T092, T191]
tags: [corpus, gt, sintetico, copyright, delta-e, infra]
kind: infra
altitude: execucao
---

## Contexto

A privatização do GT verbatim (N&C + Preskill, 2026-06-09; ver `corpus/RIGHTS.md`)
deixou o caminho público de validação sem GT de math denso. A saída não é curar
mais páginas de terceiros — é **inverter a direção**: escrever a fonte canônica
nós mesmos e renderizá-la com o próprio `md→pdf` do projeto. O GT deixa de ser
transcrição (falível, copyright-bound) e passa a ser **conhecido por construção**:
a fonte É a resposta certa, byte a byte. Equações canônicas são fatos matemáticos
(não protegíveis — 17 U.S.C. 102(b), merger doctrine; Lei 9.610 art. 8º I);
tipografadas por nós, a expressão é 100% autoral e publicável.

## Hipótese

Um corpus 100% autoral — ~30 fórmulas LaTeX canônicas (Bell, Hadamard,
Schrödinger, Maxwell; `pmatrix` 2×2 e 4×4 mirando a fraqueza conhecida do
pix2tex em matrizes, grade 0.50 em e18/e21), ~15 tabelas md em tiers (insumo
T075), ~10 logos sintéticos (texto+formas, insumo T180/T132), diagramas mermaid
(insumo T190/T191), prosa lorem-técnica — renderizado pelo próprio
`src/pdf2md/pdfs.py` é um **instrumento válido**: as notas que produz para os
extractors **reproduzem o ranking e os modos de falha já medidos no corpus
real** (e15/e18/e21).

## Método

1. Gerador determinístico (seed fixa, stdlib) commitado — corpus reproduzível.
2. Render a PDF via `md_to_pdf` (pandoc+Chrome+KaTeX). PDF é render, não source.
3. Extrair de volta com cada algoritmo (pdftotext/marker/pix2tex).
4. Comparar contra a fonte conhecida: WER-LaTeX, page_wer/page_ssim, TEDS (T075).

## Métricas de validade do instrumento

- Concordância de ranking dos extractors por categoria vs histórico real
  (Kendall-τ; alvo: ≥4 de 5 categorias concordam).
- Reaparição dos modos de falha conhecidos (matriz ~0.5 no pix2tex) — binário.
- Teto de identidade: round-trip do próprio GT md ≥0.95 por categoria
  (senão mede-se o harness, não o extractor).

## O caveat grande (e a mitigação delta-E)

O extractor passa a ser testado contra **um** renderer (Chrome+Skia+KaTeX),
que não é a tipografia pdflatex/Computer Modern dos PDFs reais (fontes CMEX
são exatamente o sinal que o e21 explora). Mitigação: GT canônico permanece
LaTeX/md **único e puro**; cada renderer é um **adapter** que gera variante do
PDF — matriz {Chrome+KaTeX, Tectonic/pdflatex opcional} × fonte {default, STIX}
× DPI {96, 150, 300}. Nota **por célula**, nunca agregada escondendo o eixo.

## Critério de promoção

Corpus vira `corpus/examples/` (tier in-repo do registry) + entradas medidas em
`docs/profiles/` + fixtures de teste herméticos para o cropper/executor (hoje
os testes de fórmula real dependem de zcache).

## Critério de descarte

Descarta a hipótese de **substituição** (corpus segue útil como smoke-test) se:
rankings divergem do real em ≥2 categorias; OU teto de identidade <0.95 em
alguma categoria; OU a fraqueza de matrizes NÃO reaparece no sintético (sinal
de que Chrome+KaTeX é "fácil demais" — aí o eixo Tectonic vira **obrigatório**
antes de qualquer conclusão).

## Deps

Zero dep pip nova (stdlib + pdfs.py + pymupdf). Tectonic/MiKTeX como segundo
renderer: external-capability opcional (modelo do doctor), nunca no pyproject.

## Não-objetivo

- Substituir GT humano de documentos REAIS (T060 segue, no tier privado).
- Cobrir scan/manuscrito (render nativo é born-digital por definição).

## Conexão

- Destrava [T075](T075_tabelas_teds.md), [T092](T092_indexacao_utility_proxies.md),
  [T191](../research/T191_diagram_to_mermaid_vlm.md); insumo para
  [T180](T180_reconstrucao_vetorial_imagens.md) (logos sintéticos).
- Materializa o princípio delta-E articulado em T060 pg03.
- Resolve a tensão corpus público × direitos (RIGHTS.md trivial: tudo autoral).
