# Changelog

Releases do `pdf2md` por ordem decrescente. Formato inspirado em
[Keep a Changelog](https://keepachangelog.com/). Versionamento segue
[SemVer](https://semver.org/) — MAJOR.MINOR.PATCH.

## [0.8.0] — 2026-06-09

Primeiro release no PyPI. Roteador macro-intent + preparação para publicação.
Publicado sob o nome de distribuição **`pdftomd`** (`pip install pdftomd`) — o slug
`pdf2md` estava reservado por outra conta (registrado sem releases). Comando CLI e
nome de import permanecem `pdf2md`.

### Adicionado
- **Roteador macro-intent (T090)**: `pdf2md convert --intent rapido|qualidade|balanceado|auto|indexacao|low-resource`
  e `pdf2md route` (dry-run). `route()` puro, profile-driven, com degradação honesta (`.degraded`/`.rationale`).
- **Extração CPU** (`extractors.py`): pdftotext/PyMuPDF + Tesseract — caminho 100% CPU, offline, determinístico.
- **Cropper de fórmula CPU built-in** + integração pix2tex (math display → LaTeX no caminho CPU).
- **Gatilho de pass2 seletivo** no `--indexacao` (`pass2_warranted`: math denso OU densidade anômala).
- **Extras pip**: `[rtpixel]` (validador visual), `[ocr]` (wrapper pytesseract), `[all]`. numpy/scipy/scikit-image
  saíram do core (base enxuto: typer/pymupdf/pillow/psutil).
- **`pdf2md doctor` estendido** (marker/tesseract/pix2tex/ollama) + `doctor --intent` (pipeline que o host usaria).
- **`discovery.py`**: descoberta portável de ferramentas externas (env → PATH multi-SO → local do SO), sem paths
  presos a uma máquina. `LICENSE` (MIT) na raiz; docs reestruturadas (Diátaxis); `CHANGELOG.md`.

### Mudado
- `--intent` substitui `--quick`/`--best` (mantidos como legado).

## [0.7.0] — 2026-05-16

### Adicionado
- Flag `--rt-pixel` no `pdf2md convert` ativa pixel-roundtrip visual (T070)
  ao final do pipeline. `--best` ativa automaticamente.
- Flag `--rt-pixel-skip-ssim` (modo rápido, ~7× mais barato — só WER textual).
- Helper `_run_rt_pixel_on_out` no `cli.py` cobre book + paper layouts.
- Output agregado em `out/_pixel_roundtrip.json` com métricas por capítulo.

### Validação
- Lab e14 valida pipeline em 3 categorias além do baseline N&C cap 4:
  arxiv_1706 (WER 0.258), preskill (0.395), CDC MMWR (0.421). Todos atingem
  critérios de promoção (WER<0.70, SSIM>0.30, tempo<60s/doc).

## [0.6.0] — 2026-05-16

### Adicionado
- Módulo `pdf2md.pixel_roundtrip` (T070 parcial) — validador visual L0.5.
- CLI `pdf2md rt-pixel ORIG RENDER [--align dtw] [--skip-ssim] [--out X.json]`.
- Funções: `align_hungarian`, `align_dtw`, `page_wer`, `page_ssim`, `normalize_text`,
  `run_pixel_roundtrip`, dataclasses `PageMetrics` + `PixelRoundtripResult`.
- Tests (20 novos): unit + smoke end-to-end com PDFs sintéticos.

### Decisão arquitetural
- Triângulo macro/médio/micro **reduzido a 2 vértices**: macro SSIM +
  médio WER (após alinhamento). Micro (block-a-block) **dropado**
  permanentemente — labs e10/e11 provaram que fragmentação é incompatível
  com reflow.
- Thresholds calibrados: WER<0.30 ótimo, <0.60 tolerável (e13);
  SSIM>0.95 ótimo, >0.50 tolerável.

### Deps
- Adicionado: `numpy>=1.26`, `scipy>=1.14`, `scikit-image>=0.22` como deps
  obrigatórias do core (filosofia "batteries included").

### Trajetória de descoberta (5 labs encadeados)
- **e09**: macro SSIM promove; bbox IoU geométrico falha (coords absolutas
  incomparáveis entre layouts diferentes).
- **e10**: pareamento ingênuo block-a-block falha; achou bug T076 ([fix em 0.4.1](#041--2026-05-16)).
- **e11**: 4 variantes de fingerprint local não convergem (fragmentação).
- **e12**: métricas globais per-page degeneram após acúmulo de reflow.
- **e13**: alinhamento Hungarian/DTW destrava — WER med vai de 0.96 → 0.376.

## [0.5.0] — 2026-05-16

### Adicionado
- Módulo `pdf2md.telemetry` (T085) — instrumento de telemetria por step.
- `TelemetryRun` context manager com `.step("nome")` aninhado.
- Captura wall_s/cpu_s/cpu_pct/rss_peak/py_peak/gpu_vram/gpu_util/io/threads
  via amostragem em thread separada (overhead validado < 1%).
- Funciona sem GPU/torch (degrades graceful). Auto-save JSON.
- Tests (9 novos).

### Deps
- Adicionado: `psutil>=5.9`.

## [0.4.1] — 2026-05-16

### Corrigido
- **T076**: `md_to_pdf(md)` sobrescrevia silenciosamente PDF co-irmão com
  mesmo basename. Bug destruiu PDF render em `corpus/` durante lab e09
  (recuperado via `git restore`).
- Nova assinatura: `md_to_pdf(md, out_pdf=None, *, overwrite=False)`.
  Default raise `FileExistsError` quando destino existe.
- `generate_all` passa `overwrite=True` explicitamente (re-runs são uso
  esperado).

## [0.4.0] — 2026-05-13

### Articulação arquitetural
- **`PHILOSOPHY.md`** ganha 6 seções formalizando a tese implícita:
  validação por fechamento recursivo de ciclos, triângulo
  macro/médio/micro, calibração do reconstrutor, ablação modular,
  tradeoffs explícitos, convergência vs divergência.
- **`META_TRANSMUTOS.md`** (novo): tese da família — pdf2md como instância
  de decompilador/recompilador universal (objetos ↔ MD+acessórios ↔ objetos).
- **`MD_CANONICAL.md`** (novo): schema do MD canônico (provenance,
  imagens em `images/`, GFM extensions, KaTeX, validações).

### Tickets de research abertos
- T070 (pixel-roundtrip validador visual L0.5)
- T072 (calibração do reconstrutor)
- T402 (pipeline fractal — meta-organiza T132/T133/T134/T180)

### Refactor (5 batches)
- Scripts em `src/*.py` migram para `src/pdf2md/<nome>.py` como módulos
  importáveis. `src/*.py` viram shims de ~13 linhas para back-compat.
- CLI sem subprocess para subcomandos próprios (só chama `marker_single`
  externo).
- Env vars `PDF2MD_*_VERSION` eliminadas do fluxo principal (kwargs em
  `detect_tools()`); fallback env var preservado para chamada standalone.
- 79 testes em 7s.

### Bug fix
- `_marker_raw/` em pasta irmã de `out/` (não filha) — `restructure.py`
  fazia rmtree em `out/` durante operação e apagava o marker raw.
- Encoding cp1252 no `print(__doc__)` dos `_cli()` standalone com Unicode
  no docstring.

## [Antes da v0.4]

Histórico em `docs/explanation/diario.md`. Resumo:

- **2026-05-13** T108: pacote `pip install pdf2md` + CLI unificado.
- **2026-05-11/12**: provenance + ablações Marker `--use_llm` (e07
  descartado) + Granite-Docling (e08 descartado) + MinerU 2.5-Pro (e06
  blocked).
- **2026-05-10**: bancada montada (`lab/`, `corpus/`, `tickets/`).
  T050 baseline reproduzível (round-trip 95.09% em N&C cap 4).
- **2026-05-08**: separação para projeto autônomo (`transmutos/pdf2md/`).
- **2026-05-05**: origem na faixa T100 do `AulaQuantum`.

---

[0.7.0]: ./
[0.6.0]: ./
[0.5.0]: ./
[0.4.1]: ./
[0.4.0]: ./
