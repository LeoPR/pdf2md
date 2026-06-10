---
id: T092
titulo: Utilidade de indexação — proxies tool-agnostic + validação do pass2_warranted
status: open
criado_em: 2026-06-09
fechado_em:
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
