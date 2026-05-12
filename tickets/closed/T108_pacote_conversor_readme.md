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
