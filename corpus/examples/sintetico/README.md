# corpus/examples/sintetico — GT-por-construção (T065/e24)

Corpus de avaliação **100% autoral e publicável**: a fonte canônica (`gt/`) é
escrita pelo gerador determinístico [`gen.py`](gen.py) e é a resposta certa
**byte a byte** — GT por construção, não por transcrição. Fórmulas canônicas
são fatos matemáticos (não protegíveis — 17 U.S.C. 102(b), merger doctrine;
Lei 9.610 art. 8º I) tipografadas por nós; prosa, tabelas, diagramas mermaid e
logos SVG são inventados. Zero material de terceiros.

**75 itens, 8 categorias** (`manifest.json`): prosa 5, formula_display 10,
formula_matriz 8, formula_multiline 6, formula_inline 6, tabela 15 (5 tiers,
T4/T5 = HTML rowspan/colspan), diagrama 20 (mermaid, 5 tipos × 4 tamanhos),
logo 5 (SVG texto+formas).

## gt/ é source; pdf/ é render

Os PDFs commitados em `pdf/` são **renders** do GT (metadata comprova:
HeadlessChrome+Skia em `katex/`, Tectonic em `cm/`) — subset pequeno (~330KB)
para testes herméticos do cropper e prova pronta. O eixo de renderer é o
**adapter delta-E** do T065: GT único e puro; cada tipografia
(Chrome+KaTeX vs pdflatex/Computer Modern) é uma variante medida em separado,
porque o comportamento do detector de fórmulas é DOMINADO pela tipografia
(e24 ondas 2-4 / T192).

Regenerar: `python gen.py gen` (gt/, determinístico — crc32, sem random);
`python gen.py fixtures` (pdf/, precisa pandoc+chrome; eixo CM precisa
tectonic no PATH ou `PDF2MD_TECTONIC`); `python gen.py render <out_dir>`
(os 75 itens, para bancadas — renders completos são output, ficam fora do repo).

## Validade como instrumento (e24, 2026-06-10)

- **Gate de identidade**: recall de prosa (pdftotext sobre o render) = 1.0000
  em 8/8 categorias — o harness não introduz ruído na camada base.
- **Concordância com o corpus real**: ranking marker × pdftotext concorda com
  as âncoras históricas em 4/4 categorias ancoradas (prosa, display, matriz,
  tabela).
- **Modos de falha conhecidos reaparecem**: pix2tex display≫matriz nos DOIS
  renderers (0.852/0.384 KaTeX; 0.721/0.318 CM; âncoras e18/e21: 0.80/0.50).
- **Achados novos** (o corpus descobrindo coisas): marker degrada em
  multi-linha `aligned`/`cases` (0.681); inversão em figuras vetoriais —
  texto interno 100% recuperado por pdftotext e 0% por marker; ver
  `docs/profiles/ativo/`.

Resultados completos: `tickets/closed/T065_corpus_gt_sintetico.md` (ondas 1-4).
