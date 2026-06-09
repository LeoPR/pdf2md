# Referência de CLI — `pdf2md`

Fonte autoritativa dos comandos. Para flags exaustivas e atuais de um comando,
`pdf2md help <cmd>` ou `pdf2md <cmd> --help` (o `--help` é a verdade do código).

## Macro

### `pdf2md convert FILE.pdf` — one-shot por intent
Decide e executa o pipeline (extrai → organiza → otimiza → stats → proveniência).

| Flag | Efeito |
|---|---|
| `--intent, -i <nome>` | `rapido｜qualidade｜balanceado｜auto｜indexacao｜low-resource` (roteador T090) |
| `--quick, -q` | **[legado]** pula otimização + round-trip (≈ atalho de rapido) |
| `--best` | **[legado]** otimização total + multi-roundtrip 3 iter + rt-pixel |
| `--book / --paper` | força layout (senão auto-detect via TOC do PDF) |
| `--out DIR` | diretório de saída |
| `--rt-pixel` | liga o validador visual L0.5 (requer extra `[rtpixel]`) |

`--intent` e `--quick/--best` são mutuamente exclusivos. Sem `--intent`, usa o
caminho legado (auto-detect + `--quick/--best`).

### `pdf2md route FILE.pdf --intent <nome>` — decisão do roteador
Dry-run: imprime o `Pipeline` escolhido (PRIMARY + refiners + optimizer), `.degraded`
e `.rationale`. Com `--execute` roda; `--out DIR` define a saída. **Puro** dado
host+doc — não faz I/O na decisão.

## Subcomandos finos (controle granular / retomar pipeline parcial)

| Comando | Faz |
|---|---|
| `pdf2md extract FILE.pdf --out DIR` | só o PRIMARY (ex. marker_single) |
| `pdf2md restruct DIR --pdf FILE --marker-out RAW` | split por TOC em pastas de capítulo |
| `pdf2md optimize DIR [--dry-run]` | otimização adaptativa de imagens (PNG-paleta/1-bit/JPEG) |
| `pdf2md stats DIR [--source-pdf FILE]` | telemetria por extração + round-trip → `_stats.{md,json}` |
| `pdf2md rt FILE.md --work DIR` | round-trip textual MD→PDF→MD' único |
| `pdf2md rt-multi FILE.md --work DIR -n 5` | round-trip iterativo (drift/convergência) |
| `pdf2md aggr ROOT [--out DIR]` | `_OVERVIEW` agregando múltiplos `_stats.json` |
| `pdf2md prov DIR --source PDF [...]` | marcador de proveniência idempotente |
| `pdf2md norm FILE.md [-i] [--strip-escapes]` | normalização canônica (stdout ou in-place) |
| `pdf2md pdfs DIR` | MD → PDF (pandoc + Chrome + KaTeX) por capítulo |

## Meta

| Comando | Faz |
|---|---|
| `pdf2md doctor [--intent N]` | status das capabilities (core/extras/externas); com `--intent`, o pipeline que aquele intent usaria **neste host** |
| `pdf2md version` | versão + commit |
| `pdf2md help <cmd>` | ajuda detalhada por subcomando |

## Capabilities por comando

- **convert/route/extract/stats/norm/prov/aggr** no caminho `--rapido`: só o **core**
  (pdftotext/PyMuPDF) — funciona com `pip install pdf2md-tool` puro, sem GPU.
- **rt-pixel** (e `--rt-pixel`/`--best`): extra **`[rtpixel]`** (numpy/scipy/scikit-image).
- **OCR de scan** (`stats`/`route` em scan sem GPU): extra **`[ocr]`** + engine `tesseract`.
- **extract/convert `--qualidade`** com marker: **externo** (venv + GPU + `PDF2MD_MARKER`).
- **math→LaTeX CPU** (`--qualidade` sem GPU): runtime **pix2tex** externo (`PDF2MD_PIX2TEX_PYTHON`).
- **pdfs / rt / MD→PDF**: **pandoc + Chrome** no PATH.

Rode `pdf2md doctor` para ver o que está presente. Detalhes de instalação no
[README](../../README.md#instalação); escolha de intent em
[how-to/escolher_intent](../how-to/escolher_intent.md).
