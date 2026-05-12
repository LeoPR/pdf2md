---
id: T108
titulo: Empacotar fluxo do conversor + CLI unificado + manual
status: closed
criado_em: 2026-05-07
fechado_em: 2026-05-11
fase: 2
depende_de: [T101, T102, T103, T107]
blocks: []
tags: [conversor, packaging, doc, cli]
kind: pipeline
resolucao: MVP entregue — pacote instalavel + CLI macro/finos + manual no README
---

## Resolução (2026-05-11)

Fechado como **MVP entregue** (v0.3.0-dev). Escopo entregue cobre os
critérios originais e adiciona o CLI unificado pedido na 2ª iteração do
design (macro inteligente + subcomandos finos).

### O que mora hoje

- **`pyproject.toml`**: deps `typer + pymupdf + pillow`, entry point
  `pdf2md = "pdf2md.cli:app"`, build-system setuptools.
- **`src/pdf2md/cli.py`**: Typer app com:
  - **Macro** `pdf2md convert FILE.pdf` — auto-detect TOC, presets
    `--quick / --best / --book / --paper`.
  - **Subcomandos finos** (10): `extract`, `restruct`, `optimize`,
    `stats`, `rt`, `rt-multi`, `aggr`, `prov`, `norm`, `pdfs`.
  - **Meta**: `doctor`, `version`, `help <cmd>`.
- **`README.md`**: manual com 7 casos de uso + variáveis de ambiente +
  estrutura do repo + status atualizado.

### Critérios originais (atendidos)

- [x] Setup documentado → `pdf2md doctor` valida em runtime
- [x] Pipeline marker → restructure → roundtrip → `pdf2md convert` (macro)
- [x] Comandos copiáveis com paths absolutos → 7 casos no README
- [ ] VS Code extensions → **não incluído** (decisão: README foca uso,
  não setup IDE; vira `docs/SETUP_VSCODE.md` se virar demanda)

### Pendências v0.4 (cleanup, não-MVP)

- Scripts em `src/*.py` (stats, restructure, etc.) invocados via subprocess
  pelo CLI. Migrar para módulos importáveis sob `pdf2md/` é cleanup natural.
- `convert` sem `--pages` (adicionar quando demanda surgir).
- `tests/` (smoke + unit em `apply_to_text`, `normalize_md`, `_detect_book`).

### Smoke validado

`pdf2md convert lab/e08_granite_docling/out/smoke_5pgs.pdf --paper --quick`
rodou end-to-end em 2m39s (5 pgs do N&C cap. 4):
extract (marker) → stats → provenance, output organizado com `_stats.md` e
marcador de proveniência em cada `.md`.

### Validação em produção (N&C completo, 2026-05-12)

`pdf2md convert Nielsen_Chuang_QCQI.pdf --out Z:/caches/pdf2md_nc_v03 --book`
rodou end-to-end em **1h54min** (livro completo, 704 pgs):

| Etapa | Resultado |
|---|---|
| [1/5] extract (marker) | 6828 s (1h53m48s) — output em pasta irmã `_marker_raw/` |
| [2/5] restruct | 21 entradas TOC, ~2 s |
| [3/5] optimize | 197/198 imagens, **1.7 MB economizados (38.6%)** — idêntico histórico |
| [4/5] stats | 332,652 tokens, 1,970 fórmulas display, 198 imagens — idêntico histórico |
| [5/5] provenance | 22 arquivos marcados (21 capítulos + index) |

**Determinismo**: 21/21 capítulos têm SHA-256 idêntico ao histórico de 2026-05-07
após stripping de provenance — pipeline bit-for-bit reproduzível.

**Bug pego em produção** (1ª tentativa): `_marker_raw/` estava dentro de `out/`;
`restructure.py` faz `shutil.rmtree(target_dir)` antes de criar a estrutura,
apagando o próprio input do marker. Custou 1h54min de GPU perdidos. Fix em
[commit 89795b4](../../) (2 lugares: cli.py usa pasta irmã + defensiva em
restructure.py). Lição salva em `memory/feedback_outputs_temporarios_fora_do_target.md`.

**Decisão sobre swap N&C no AulaQuantum**: **não substituir**. Conteúdo MD é
bit-for-bit idêntico; o `_stats.md` histórico tem mais informação (round-trip
95.09%, marker/torch/CUDA versions) que o novo (regrediu pra "n/a" porque
stats.py rodou no .venv do pdf2md, que não tem torch/marker). A versão atual
no AulaQuantum permanece canônica.

**Regressão menor identificada** (não-bloqueante): quando o `stats.py` é
invocado pelo CLI via subprocess no venv do pdf2md (sem torch/marker
instalados), os campos "marker-pdf version", "torch version", "CUDA device"
aparecem como "n/a"/"CPU only". Fix futuro (v0.4): stats.py poderia receber
esses metadados via flags `--marker-version` / `--torch-version` ou cli.py
poderia inspecionar `pdf2md doctor` e propagar.
