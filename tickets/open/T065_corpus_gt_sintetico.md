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

## Progresso — onda 1 (e24, 2026-06-10): gate de identidade PASS

Corpus v1 gerado (75 itens, 8 categorias: prosa 5, formula_display 10,
formula_matriz 8, formula_multiline 6, formula_inline 6, tabela 15 em 5 tiers,
diagrama 20 — herdados do e22/T190 e rendidos com `mermaid=True` —, logo
sintético 5). Gerador 100% determinístico (crc32, sem `hash()` salteado).

**Gate (c) do ticket — teto de identidade: PASS 8/8.** Recall de tokens de
prosa (pdftotext sobre o render Chrome+KaTeX) = **1.0000 (mean e min) em todas
as categorias** — o harness não introduz ruído mensurável na camada que o
extractor base tem que capturar. Escopo honesto: o gate é prosa-only por
design; o conteúdo de fórmula/tabela/diagrama será graduado na onda 2
(rankings pdftotext × marker × pix2tex, Kendall-τ vs histórico real,
reaparição da fraqueza de matrizes ~0.5) — os critérios de descarte de
substituição continuam em aberto até lá.
## Progresso — onda 2 (e24, 2026-06-10): concordância 4/4; eixo Tectonic disparou; 3 achados novos

Marker batch (1 carga de modelo, 75 PDFs, RTX 3060; venv do marker ganhou
`psutil` — o entry-point batch exigia e o marker_single não) × pdftotext:

| categoria | pdftotext | marker | âncora histórica |
|---|---|---|---|
| prosa | 1.000 | 1.000 | empate alto ✓ |
| formula_display | 0.024 | 0.973 | marker >> ✓ |
| formula_matriz | 0.027 | 0.986 | marker >> ✓ |
| formula_multiline | 0.040 | **0.681** | (sem âncora) |
| formula_inline | 1.000 | 1.000 | — |
| tabela | 0.500 | 1.000 | marker > ✓ (pdftotext = conteúdo sem estrutura) |
| diagrama | **1.000** | **0.000** | (sem âncora) |
| logo | **1.000** | **0.000** | (sem âncora) |

**Concordância: 4/4 ancoradas** — a hipótese de substituição SEGURA para as
camadas prosa/display/matriz/tabela (com marker×pdftotext).

**Critério condicional DISPAROU (medido, não especulado):** o cropper de
fórmulas detecta **0 regiões** no render KaTeX — detector é acoplado à
assinatura de fonte CM/CMEX do pdflatex; o PDF sintético usa `KaTeX_Main/
KaTeX_Math-Italic/KaTeX_Size3`. Logo o caminho pix2tex é intestável neste
renderer e **o eixo Tectonic/pdflatex é OBRIGATÓRIO (onda 3)** para qualquer
conclusão de fórmula-CPU no sintético. Bônus de produto: PDFs web-rendered
(Jupyter/KaTeX) existem no mundo real e o cropper é cego a eles — candidato a
ticket próprio (suporte multi-tipografia no detector).

**Achados novos (o corpus descobrindo coisas):**
1. **Marker degrada em multi-linha** (`aligned`/`cases`): 0.681 vs 0.97-0.99
   em display/matriz simples — modo de falha mensurável inédito.
2. **Inversão em diagrama/logo**: o texto vetorial dentro de figuras (labels
   de mermaid, texto de logo SVG) é 100% recuperado pelo pdftotext e **0%
   pelo marker** — o layout model classifica a região como figura e descarta
   o texto interno. Implicação direta no roteamento de indexação (T092): doc
   rico em diagramas pode indexar MELHOR pelo caminho CPU.
3. **Escopo honesto das categorias logo/diagrama**: no sintético o texto da
   figura permanece VETORIAL no PDF (caminho fácil); logo real rasterizado
   (e16) é outro problema — futura variante: rasterizar os SVGs e re-embutir
   como PNG para simular o caso raster.
## Progresso — onda 3 (e24, 2026-06-10): eixo Tectonic — contra-prova OK, pix2tex segue bloqueado (2º modo de falha do cropper)

Tectonic 0.15.0 instalado (`Z:\bin`, external-capability). 24 fórmulas
compiladas em CM real. Resultados:

1. **Contra-prova da cegueira KaTeX: confirmada** — o cropper volta a detectar
   regiões em tipografia CM (24/24 docs onde há detecção vs 0 em KaTeX). O
   eixo de renderer domina o comportamento do detector, como previsto.
2. **NOVO modo de falha do cropper (medido):** em layout minimal-article
   denso, o merge da região expande além das fontes math e **engole prosa
   vizinha** — o crop misto faz o pix2tex alucinar LaTeX a partir de prosa
   (sim ~0.02 vs âncora 0.80). Fórmulas curtas (E=mc², Euler, CNOT 4×4)
   produzem **0 regiões**. O cropper foi calibrado no espaçamento generoso de
   lecture-notes (Preskill, e21) — banda de calibração mais estreita do que se
   assumia, agora com DOIS modos medidos: (a) cego a fontes KaTeX; (b) merge
   prosa+math em layout denso.
3. **Fraqueza de matrizes (~0.5): ainda não-testável** no sintético — bloqueada
   pelo instrumento (cropper), não pelo corpus. Harness teve 1 bug corrigido no
   caminho (parse do output do pix2tex cortava no ":" do drive Windows).

**Escopo honesto consolidado do T065 até aqui:** o corpus está VALIDADO como
instrumento para as camadas marker×pdftotext (onda 2, 4/4) e revelou 5 achados
de produto inéditos. A camada fórmula-CPU (cropper+pix2tex) fica pendente de
um ticket de **robustez do cropper** (multi-tipografia KaTeX + merge limitado
por classe de fonte) OU de variante de template menos denso (com o viés
registrado). Promoção parcial do corpus (camadas validadas) é o próximo passo.
## Progresso — onda 4 via T192 (2026-06-10): fraqueza de matrizes REAPARECE

Com o cropper corrigido (T192), o teste pendente fechou: pix2tex no sintético
dá display 0.852/matriz 0.384 (KaTeX) e 0.721/0.318 (CM) — o modo de falha
histórico (e18/e21: 0.80/0.50) reproduz nos DOIS renderers. **Todos os
critérios de validade do instrumento estão satisfeitos** (gate identidade 8/8;
concordância 4/4; modos de falha reproduzidos; eixo de renderer documentado
como adapter). Pendente para fechar o ticket: PROMOÇÃO — corpus →
`corpus/examples/` (tier in-repo) + entradas em `docs/profiles/` (multiline,
inversão diagrama/logo) + fixtures herméticos de teste.