---
id: T075
titulo: TEDS bidirecional — nota de tabela por algoritmo (fecha BURACO #2)
status: closed
criado_em: 2026-06-09
fechado_em: 2026-06-10
fase: 4
depende_de: [T065]
blocks: []
tags: [tabelas, teds, metrica, validador, roundtrip]
kind: experimento
altitude: execucao
---

## Contexto

Tabela é a dimensão declarada e nunca medida: `metricas.md` define M3 (TEDS
≥0.90) mas nada em `src/` implementa; os profiles dizem `qualidade_tabelas:
nao_medido` (marker) e "fraco, estimado" (pdftotext); `stats.py` só conta
linhas-pipe. A página CDC "tabela complexa" do T060 ficou em `.draft`. É o
BURACO #2 do roteador: `--qualidade` não sabe dizer o que entrega em tabela.

## Hipótese

H1 (pdf→md): sobre tabelas sintéticas em 5 tiers — T1 grid simples; T2
alinhamentos/números; T3 células multilinha; T4 col/rowspan (que pipe-table nem
representa — mede o teto do FORMATO); T5 borderless/zebra — os extractors têm
penhascos de TEDS mensuráveis e distintos (esperado: marker ≥0.90 em T1-T2;
pdftotext <0.50 em qualquer tier).
H2 (round-trip): TEDS(source, extraído-de-pdf₂) por tier é a nota de round-trip
de tabela — análogo exato do page_wer/page_ssim para texto/pixel.
H3: o TEDS máximo atingível em T4 com pipe-tables documenta limite do
markdown-transporte (vai pro profile como contexto, não como falha; ver T440).

## Método

1. Calibração do harness PRIMEIRO: TEDS(GT→pandoc, GT→pandoc) = 1.0;
   perturbações controladas (trocar 2 células, deletar linha) → sensibilidade
   monotônica.
2. Cadeia: md → HTML via pandoc (já externo no projeto) → TEDS + TEDS-struct.
3. Uma tabela por página sintética → md extraído inteiro parseável sem detector.

## Métrica

TEDS e TEDS-struct via pip `table-recognition-metric` (implementação canônica
do PubTabNet, arXiv:1911.10683).

## Critério de promoção

Medidor TEDS vira módulo em `src/` (estilo pixel_roundtrip) + coluna `tabela`
nos profiles ativos + gate de routing futuro.

## Critério de descarte

Descarta o HARNESS (não a dimensão) se: TEDS de identidade <0.99 (ruído pandoc
domina) e não consertável com normalização no adapter; OU TEDS não discrimina
(flat entre tiers ⇒ redesenhar tiers). Descarta H1 se marker <0.90 já em T1 —
conclusão vai pro profile e segue.

## Deps

pip-safe integral: `table-recognition-metric` → apted (pure-Python) + lxml +
bs4. Sem torch, sem conflito pillow. Venv de lab primeiro; promove ao geral só
se vingar.

## Não-objetivo

- Detector de tabela em página cheia (página sintética tem 1 tabela).
- Tabelas de PDFs reais de terceiros como GT (T065 cobre a fonte).

## Conexão

- Fecha **BURACO #2**; alimenta [T440](../research/T440_md_como_formato_de_transporte_vs_pdf.md)
  com números (teto do pipe-table em T4/T5).
- Corpus vem de [T065](../closed/T065_corpus_gt_sintetico.md) — promovido:
  `corpus/examples/sintetico/` (15 tabelas em 5 tiers; `gen.py render` gera os PDFs).

## Resultado (e25, 2026-06-10) — H1/H2/H3 entregues; ticket FECHADO

**Onda 0 (calibração) PASS**: identidade 1.0 em 15/15; pandoc determinístico;
perturbações monotônicas (troca 2 células > deleta linha, estrito onde a
tabela tem ≥6 células — em 4 células os custos de edição EMPATAM, comportamento
correto de TED); TEDS-struct cego a troca de texto 15/15. 2 bugs de harness
achados e corrigidos no caminho: (a) lxml devolve a própria `<table>` como
raiz de fragmento e `.//table` não a encontra; (b) `thead/tbody/colgroup` são
artefato de TRANSPORTE (pipe→pandoc envelopa, HTML cru não) — normalizados no
adapter (princípio delta-E).

**Onda 1 (TEDS por tier, 2 extractors, render Chrome):**

| tier | pdftotext | marker | teto pipe |
|---|---|---|---|
| T1 grid | 0.0 (sem tabela 3/3) | **1.000** | 1.0 |
| T2 align+números | 0.0 | **1.000** | 1.0 |
| T3 multilinha | 0.0 | **1.000** | 1.0 |
| T4 row/colspan | 0.0 | **0.749** | **0.749** |
| T5 borderless/zebra | 0.0 | **1.000** | 1.000 (controle ✓) |

- **Achado central (H3)**: marker atinge o teto do formato EXATAMENTE, por
  item, em 4 casas (T4: 0.8095/0.8235/0.6154 = best-pipe idem) — a perda em
  spans é 100% do markdown-transporte (número para T440), não do extractor.
- **H1**: marker ≥0.90 em T1-T2 ✓ (1.000); pdftotext <0.50 em todos ✓ (0.0,
  15/15 sem NENHUMA tabela no output — estrutura zero; conteúdo já medido
  100% no e24). Penhasco T4 discrimina ✓. Âncora de direção (marker >
  pdftotext) mantém ✓.
- **H2**: TEDS(source, extraído-do-render) é a nota de round-trip de tabela —
  números acima SÃO o round-trip md→pdf→md₂ (o PDF é render do source).

**Promoção (critério cumprido):** módulo `src/pdf2md/table_teds.py` (estilo
pixel_roundtrip: normalização de transporte + `table_roundtrip()` +
`best_pipe_from_table()` p/ teto T440), extra pip `[tables]`
(table-recognition-metric, pure-pip) incluído em `[all]`,
`tests/test_table_teds.py` (5 herméticos + 1 pandoc-skipif), coluna
`qualidade_tabelas` MEDIDA nos profiles marker/pdftotext, e categoria tabela
do corpus sintético redesenhada para os tiers deste ticket (v1.1,
byte-idêntica ao medido; fixture `t4_0.pdf` re-renderizado). Gate de routing
fica para quando houver consumidor (`--qualidade` já pode citar o número).

**Escopo honesto** (sintético × realista): medido em render born-digital
(Chrome+CSS próprio) de templates próprios. Tabela LaTeX/booktabs, scan e
layouts multi-coluna reais NÃO medidos — marker 1.000 aqui NÃO significa
"marker resolve tabela" em geral; significa que no domínio coberto a única
perda mensurável é o teto do transporte.
