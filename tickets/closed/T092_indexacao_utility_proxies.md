---
id: T092
titulo: Utilidade de indexação — proxies tool-agnostic + validação do pass2_warranted
status: closed
criado_em: 2026-06-09
fechado_em: 2026-06-10
fase: 4
depende_de: [T090, T065]
blocks: []
tags: [indexacao, rag, retrieval, routing, pass2, metrica]
kind: experimento
altitude: execucao
---

## Contexto

O intent `--indexacao` existe e o gatilho `pass2_warranted()` decide, por doc,
se vale enfileirar marker — mas a UTILIDADE do output para retrieval nunca foi
medida, e o gatilho é heurística calibrada em N=5, não regra validada. O
pdf2md não precisa "saber de RAG"; precisa que o md que ele emite **sirva** a
quem indexa. Proxies tool-agnostic medem isso sem acoplar stack nenhuma.

## Hipóteses

H1: a utilidade-para-retrieval é mensurável com 4 proxies sem stack de RAG:
(a) integridade de chunking, (b) term-recall vs fonte, (c) self-retrieval BM25,
(d) structure-loss — e eles DISCRIMINAM pdftotext de marker em docs math-densos
(≥10pp de gap em term-recall de termos dentro de math) enquanto empatam em
prosa pura.
H2 (a parte mais valiosa, falsificável): `pass2_warranted()` prevê ganho REAL —
docs flagados PASS2 ganham ≥5pp de term-recall indo pass1→pass2; docs ok-pass1
ganham <2pp. Se segura, o gatilho vira regra MEDIDA (profile `confianca:
medido`); se não, abre recalibração com números em mãos.

## Método / métricas

- (a) chunk-integrity: chunker de referência mínimo (split por heading + janela
  de N chars, stdlib) → % de chunks sem corte no meio de `$$..$$`/fence/tabela
  + % com breadcrumb de headings reconstruível. Medido com DUAS janelas
  (~512/1024 tokens) — se o veredito muda com o chunker, o proxy cai.
- (b) term-recall: top-20 termos distintivos por página (TF-IDF caseiro,
  stdlib, sobre a fonte — GT T065 onde existe; `pdftotext -layout` como proxy
  nos examples) → fração presente no md indexado.
- (c) self-retrieval: query = frase amostrada da página k → BM25 (`rank-bm25`)
  sobre os chunks → acerto se top-3 contém chunk da região da página k.
- (d) structure-loss: count-diff (headings, list items, linhas de tabela,
  blocos math) output vs GT — reusa o espírito do e15.

## Critério de promoção

Proxies viram medidor em `src/` ou lab promovível; coluna de utilidade-indexação
nos profiles; `pass2_warranted` reclassificado de heurística para regra medida
(ou recalibrado).

## Critério de descarte

Descarta os proxies se: não discriminam pdftotext vs marker em math-denso; OU
o veredito inverte entre as 2 janelas de chunk (proxy mede o chunker, não o
output). Falsificar H2 NÃO descarta os proxies — é resultado valioso
(recalibração do gatilho).

## Escopo honesto

Conclusões valem para retrieval léxico (BM25/term-match). NÃO extrapolar para
retrieval denso/embeddings sem teste próprio — não generalizar de N=1 stack.

## Deps

`rank-bm25` (pure-Python + numpy; numpy já vem de `[rtpixel]`) — única dep
nova, só no venv do lab até vingar. Resto stdlib + registry/extractors/routing.

## Não-objetivo

- Montar stack de RAG (embeddings, vector store) — fora do escopo do projeto.
- Otimizar chunking — o chunker aqui é régua, não produto.

## Conexão

- Valida a promessa central do [T090](../closed/T090_macro_intent_routing.md)
  (caminho executivo de indexação); corpus misto [T065](../closed/T065_corpus_gt_sintetico.md)
  + `corpus/examples`. Docs privados: só métricas derivadas publicáveis (RIGHTS.md).

## Resultado (e26, 2026-06-10) — H1 confirmada; H2 confirmada p/ braço MATH e FALSIFICADA p/ braço densidade em sparse-saudável; ticket FECHADO

Escopo decidido ANTES de medir: ganho real pass1→pass2 exige GT ⇒ sintético
(e24: 75 docs, renders+marker reusados); reais (4 examples in-repo) validam
FLAG e proxies sem GT; scan fora (route() já barra scan antes do pass2).

**H1 — proxies discriminam math-denso e empatam em prosa: CONFIRMADA.**
Term-recall de math-terms (gregas/operadores, unicode↔latex normalizado),
marker − pdftotext: display **+43.8pp**, matriz **+78.3pp**, multiline
**+30.5pp** (≥10pp ✓✓✓); prosa empata 1.000/1.000 ✓; vereditos idênticos nas
2 janelas de chunk (proxy não mede o chunker) ✓. Status por proxy:
- (b) term-recall: **discrimina** — é o proxy central. Bônus: a inversão
  diagrama reaparece no léxico (pdftotext 0.872 > marker 0.816).
- (d) structure-loss: **discrimina** (pdftotext 0.965 vs marker 0.544).
- (a) chunk-integrity: quase não discrimina NESTE corpus (1.0 vs 0.99 —
  docs pequenos/limpos); janelas concordam; segue válido, pouco informativo
  em sintético curto.
- (c) self-retrieval BM25: ~0.30 nos DOIS — **limite do instrumento**: a
  prosa sintética sai de pools de ~30 palavras e o vocabulário colide entre
  docs (BM25 não separa). Não mede extractor neste corpus; precisa de corpus
  real ou vocabulário sintético rico (melhoria registrada p/ gen.py).

**H2 — pass2_warranted prevê ganho real: o split por braço é o veredito.**
Média agregada (+15.6pp flagged vs 0.0 ok-pass1) ESCONDE a mistura; por
braço do gatilho:

| braço | n | ganho médio | min | max |
|---|---|---|---|---|
| math (≥1.0/kchar) | 28 | **+43.0pp** | 0.0 | +100.0 |
| densidade puro (<800 c/pg) | 42 | **−2.7pp** | **−11.1** | 0.0 |
| ok-pass1 | 5 | 0.0 | 0.0 | 0.0 |

- **Braço MATH: regra MEDIDA** (era heurística N=5). Flags reais consistentes:
  arxiv-math PASS2 (3.57/kchar), arxiv-intro/cdc/irs ok-pass1.
- **Braço DENSIDADE: FALSIFICADO para sparse-SAUDÁVEL** — docs born-digital
  de baixa densidade (diagrama/tabela/logo; análogo real: slides, páginas
  diagramáticas) NUNCA ganham com pass2 e podem REGREDIR (−11.1pp: marker
  descarta texto de figura — coerente com a inversão do e24). O caso
  calibrado do braço (text-layer garbage, padrão wilson) não existe no
  sintético e segue não-discriminado ⇒ recalibração em
  [T193](../open/T193_pass2_densidade_sparse_saudavel.md).

**Promoção/registro:** bancada e26 = lab promovível (critério aceita);
coluna `utilidade_indexacao_lexica` MEDIDA nos profiles marker/pdftotext;
`pass2_warranted` reclassificado no comentário do código (math=medido,
densidade=heurística com risco medido). Escopo honesto: retrieval LÉXICO;
não extrapolar para embeddings.
