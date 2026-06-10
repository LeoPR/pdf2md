# Pipeline — orquestração

*Como os scripts em [`../../src/`](../../../src/) se compõem nas 4 camadas. Ver [`../arquitetura.md`](../arquitetura.md).*

---

## Diagrama de orquestração

```
                                    ┌─ stats.py (Camada 4) ─────┐
                                    │   - md_metrics()          │
                                    │   - image_breakdown()     │
                                    │   - folder_metrics()      │
                                    │   - roundtrip_metrics()   │
                                    │   - render_md()           │
                                    └────────┬──────────────────┘
                                             │
   ┌───────────┐  ┌───────────┐  ┌───────────┴───┐  ┌────────────┐
   │  marker   │  │restructure│  │  roundtrip    │  │ optimize_  │
   │ (externo) │─▶│   .py     │  │     .py       │  │ images.py  │
   │ (Cam 1)   │  │ (Cam 1+)  │  │ (Cam 1+3+4)   │  │ (Cam 2)    │
   └───────────┘  └───────────┘  └───────────────┘  └────────────┘
        │              │                │                  │
        │  raw MD +    │ MD por cap.    │  PDF' + MD'     │ imagens
        │  imagens     │ + images/      │  + similarity   │ otimizadas
        │              │                │                  │
        └──────────────┴────────────────┴──────────────────┘
                                │
                                ▼
                       <chapter>/_stats.{md,json}
                                │
                                ▼
                       aggregate_stats.py (Camada 4 — multi-doc)
                                │
                                ▼
                       <root>/_OVERVIEW.{md,json}
```

---

## Scripts e papel

### `src/restructure.py` (Camada 1 — pós-processamento)

**Função**: fatiar MD único do marker em pasta por capítulo, usando TOC do PDF (`fitz.get_toc()`).

**Input**: PDF original + diretório de output do marker.
**Output**: `<target>/<chapter_id>/<chapter_id>.md` + `images/` por capítulo + `index.md` navegável.

**Quando usar**: livros com TOC explícito (N&C, Preskill multi-chap). Papers (arxiv) pulam.

**Limitação atual**: `write_index()` tem título "Quantum Computation and Quantum Information" hardcoded; precisa generalização para outros livros (lendo metadata do PDF).

### `src/roundtrip.py` (Camada 1 + 3 + 4)

**Função**: dado MD₁, fazer MD₁ → PDF → MD₂ e comparar via `SequenceMatcher`.

**Input**: `<md_inicial>` + `<work_dir>`.
**Output**: `roundtrip.pdf`, `md2/.../md2.md`, similaridade reportada no stdout.

**Limitação**: paths hard-coded de MARKER e CHROME no topo do script. Workaround via `$env:PDF2MD_MARKER` (não implementado ainda — ticket futuro de pipeline cleanup).

### `src/multi_roundtrip.py` (Camada 4)

**Função**: iterar round-trip MD → PDF → MD' → PDF → MD'' → ... N vezes. Mede se pipeline converge (idempotente) ou tem drift contínuo.

**Resultado anterior**: 0.86% drift em 5 iterações no arxiv 2106.05919v2 — **pipeline é estável**.

### `src/stats.py` (Camada 4 — telemetria por extração)

**Função**: gerar relatório consolidado (`_stats.md` + `_stats.json`) com:
- Resumo executivo
- Método (versões)
- Fonte (PDF metadata + sha256)
- Output: texto, estrutura, matemática, imagens (com **breakdown por formato** — T136 ✓)
- Top 15 LaTeX commands
- Round-trip detalhado (se flags `--roundtrip-md1` e `--roundtrip-md2` passados)
- Reprodutibilidade

**Input**: pasta com MD(s) — layout livro (subdirs por capítulo) ou paper (MD no root).
**Output**: `_stats.{md,json}` no path da pasta.

### `src/aggregate_stats.py` (Camada 4 — agregação multi-doc)

**Função**: varrer recursivamente `_stats.json` de múltiplas extrações e gerar `_OVERVIEW.md` consolidado.

**Output**: tabela por kind (livro/paper/material), distribuição de round-trip, divergências agregadas, outliers críticos vs notáveis.

### `src/optimize_images.py` (Camada 2)

**Função**: walk `<root>/**/images/*.{jpeg,png}`, classificar (PIL `getcolors()` + quantize test), converter para PNG paleta lossy quando ganha. Atualizar refs no MD.

**Output**: imagens otimizadas in-place + `_image_optimization.{md,json}`.

**Resultado em N&C**: 197/198 → PNG paleta, **−38.6%** no tamanho (T131 closed).

### `src/gen_pdfs.py` (Camada 3 — bulk)

**Função**: para cada `<chapter>/<chapter>.md`, gerar `<chapter>/<chapter>.pdf` via pandoc + Chrome + CSS academic inline.

**Quando usar**: visualização final do output (não round-trip).

---

## Fluxos típicos

### Fluxo 1 — extração inicial de livro

```
marker_single <pdf> --output_dir /tmp/<slug>/ --output_format markdown
python src/restructure.py <pdf> /tmp/<slug> corpus/<slug>/
python src/optimize_images.py corpus/<slug>/
python src/stats.py corpus/<slug>/ --source-pdf <pdf>
```

### Fluxo 2 — round-trip para validar

```
python src/roundtrip.py corpus/<slug>/<chapter>/<chapter>.md /tmp/<slug>_rt/
python src/stats.py corpus/<slug>/<chapter>/ \
    --source-pdf <pdf> \
    --roundtrip-md1 corpus/<slug>/<chapter>/<chapter>.md \
    --roundtrip-md2 /tmp/<slug>_rt/md2/.../md2.md
```

### Fluxo 3 — multi-iteração (estabilidade)

```
python src/multi_roundtrip.py corpus/<slug>/<chapter>/<chapter>.md /tmp/<slug>_mrt --iterations 5
```

### Fluxo 4 — visão agregada

```
python src/aggregate_stats.py corpus/
```

---

## Estado de empacotamento

Hoje os scripts são standalone (`python src/<script>.py`). T108 (open) prevê packaging:

```
pdf2md extract  <pdf> <out>           # Fluxo 1 parte 1
pdf2md restructure <pdf> <md> <out>   # Fluxo 1 parte 2
pdf2md roundtrip <md> <work>          # Fluxo 2
pdf2md stats <folder> --source-pdf <pdf> [--roundtrip-md1 <md1>] [--md2 <md2>]
pdf2md optimize-images <root>
pdf2md aggregate <root>
```

CLI unificado com mesmo conjunto de flags. Refator de paths hard-coded acompanha.

---

## Dependências externas

| Item | Versão | Como obter |
|---|---|---|
| Python | ≥ 3.11 (testado 3.13.13) | `py -m venv` |
| marker-pdf | 1.10.x | `pip install marker-pdf` (no venv `marker` ou `pdf2md_lab_eXX`) |
| torch CUDA | 2.11+cu128 | `pip install torch --index-url https://download.pytorch.org/whl/cu128` |
| PyMuPDF | 1.27.x | `pip install pymupdf` |
| Pillow | < 11 (compat marker) | `pip install "pillow<11"` |
| pandoc | 3.9 | sistema (`winget install pandoc` no Windows) |
| Chrome | qualquer | sistema |

Para a bancada experimental, cada `lab/eNN_*/requirements.txt` lista o que aquele experimento precisa em **seu próprio venv** (ver [`../LAB_PROTOCOL.md`](../../how-to/criar_novo_lab.md)).

---

## Limitações conhecidas

1. **Paths hard-coded** em `roundtrip.py`, `multi_roundtrip.py`, `gen_pdfs.py`: `CHROME`, `MARKER` apontam para paths Windows específicos. Funciona aqui, quebra em CI/Linux/Mac. T108 vai resolver.
2. **`normalize_md` duplicado** em 3 scripts com variações ligeiras. Refator pendente.
3. **`stats.py` usa versão hard-coded de PyMuPDF** (`"1.27.2"` literal). Deveria usar `importlib.metadata.version()` igual ao marker.
4. **`restructure.py` tem título do N&C hardcoded** no `write_index()`. Generalizar lendo metadata do PDF.

Todas essas são **dívida técnica conhecida**; nada bloqueia uso atual.

---

## Tickets ativos / próximos

- **T013 ✓ closed** — Scripts movidos para `src/`
- **T101-T104 ✓ closed** — Pipeline básico estável
- **T107 open** — gen_pdfs.py integrado (parcial)
- **T108 open** — Pacote pip-installable + CLI (refator de paths)
- **T136 ✓ closed** — Breakdown por formato em stats.py
- **Futuro sem ticket**: refatorar `normalize_md` para `src/pdf2md/normalize.py` ao virar T108
