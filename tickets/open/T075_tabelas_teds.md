---
id: T075
titulo: TEDS bidirecional — nota de tabela por algoritmo (fecha BURACO #2)
status: open
criado_em: 2026-06-09
fechado_em:
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
- Corpus vem de [T065](T065_corpus_gt_sintetico.md).
