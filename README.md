# pdf2md

Conversor PDF ↔ MD com round-trip mensurável e otimização adaptativa de imagens.

Projeto autônomo nascido do `AulaQuantum` (faixa T400) quando o conversor
amadureceu além do escopo daquela disciplina. Mora em
`Acadêmicos/transmutos/pdf2md/` por convenção da máquina (ver
[`Z:\caches\README.md`](Z:\caches\README.md) para padrões locais).

## Status

| Componente | Estado |
|---|---|
| Extração `marker-pdf` (GPU) | Estável |
| MD → PDF via `pandoc + Chrome + KaTeX` | Estável |
| Round-trip MD → PDF → MD' com similaridade | Estável |
| Multi-iteration round-trip (convergência) | Estável (97.4% após 5 iter no paper de teste) |
| Telemetria por extração + agregada | Estável |
| Compressão adaptativa de imagens | Nível 1-2 (PNG paleta lossy gated) |
| Marcador de proveniência por arquivo | Estável (v0.3 — `pdf2md prov`) |
| **CLI unificado `pdf2md` (T108)** | **MVP** — macro + 10 subcomandos finos |
| Restauração de artefatos JPEG | Roadmap (T137) |
| Vetorização SVG (potrace) | Roadmap (T132) |
| Detecção fórmula → LaTeX (pix2tex) | Roadmap (T133/T134) |

Arquitetura completa: [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) ·
Filosofia de design: [`docs/PHILOSOPHY.md`](docs/PHILOSOPHY.md) ·
Bancada experimental: [`docs/LAB_PROTOCOL.md`](docs/LAB_PROTOCOL.md).

---

## Instalação

```powershell
# 1. Venv (convenção da máquina: junction em Z:\)
py -m venv Z:\venvs\pdf2md --prompt pdf2md
cmd /c mklink /J .venv Z:\venvs\pdf2md

# 2. Instalar pdf2md (editable, para desenvolvimento)
.venv\Scripts\python.exe -m pip install -e .

# 3. Ferramentas externas (marker, pandoc, Chrome — não-pip)
# Cada uma vive no seu venv/PATH. `pdf2md doctor` valida.
.venv\Scripts\pdf2md.exe doctor
```

Pandoc e Chrome precisam estar no PATH. Marker pode viver em outro venv
(`Z:\venvs\marker\Scripts\marker_single.exe` é o fallback default).

---

## Uso — manual de comandos

```
$ pdf2md --help

  MACRO (one-shot inteligente)
  ─────────────────────────────
    pdf2md convert FILE.pdf                # auto-detect layout via TOC
    pdf2md convert FILE.pdf --quick        # rápido (sem otimização + sem rt)
    pdf2md convert FILE.pdf --best         # tudo + multi-roundtrip 3 iter
    pdf2md convert FILE.pdf --book/--paper # forçar layout

  SUBCOMANDOS (controle granular)
  ────────────────────────────────
    pdf2md extract  FILE.pdf  --out DIR        # só marker_single
    pdf2md restruct DIR --pdf FILE  --marker-out RAW    # split por TOC
    pdf2md optimize DIR  [--dry-run]           # PNG-paleta + JPEG adaptativo
    pdf2md stats    DIR  [--source-pdf FILE]   # telemetria + round-trip
    pdf2md rt       FILE.md --work DIR         # round-trip single
    pdf2md rt-multi FILE.md --work DIR -n 5    # round-trip iterativo
    pdf2md aggr     ROOT [--out DIR]           # OVERVIEW de múltiplos PDFs
    pdf2md prov     DIR --source PDF [...]     # marcador proveniência
    pdf2md norm     FILE.md [-i]               # normalize_md canônico
    pdf2md pdfs     DIR                        # MD → PDF (pandoc+Chrome)

  META
  ────
    pdf2md doctor      # status: marker / pandoc / chrome / PyMuPDF / CUDA
    pdf2md version     # versão + commit
    pdf2md help <cmd>  # ajuda detalhada por subcomando
```

### Caso 1: livro com TOC (default inteligente)

```bash
pdf2md convert Nielsen_Chuang_QCQI.pdf --out nc_extraido/
```

Detecta TOC (PyMuPDF `get_toc`) → split por capítulo automático. Saída:

```
nc_extraido/
├── 00_front_matter/00_front_matter.md
├── 01_introduction/01_introduction.md
├── ...
├── 12_quantum_information_theory/...
├── app_*/
├── index.md
├── _stats.md           (agregado)
└── _image_optimization.md
```

Cada `.md` inclui o marcador de proveniência (`<!-- pdf2md-provenance v1 ... -->`).

### Caso 2: paper curto (sem TOC, output flat)

```bash
pdf2md convert paper.pdf --paper --out paper_md/
```

Output flat (todos os arquivos no diretório raiz). Útil para arXiv preprints.

### Caso 3: rápido (sem otimização nem round-trip)

```bash
pdf2md convert paper.pdf --quick
```

Pula otimização de imagens (compressão demora em PDFs com muitas figuras) e
não roda round-trip. ~3-5× mais rápido que default em livros.

### Caso 4: máxima qualidade (com convergência mensurada)

```bash
pdf2md convert paper.pdf --best
```

Tudo do default + multi-roundtrip 3 iterações para medir estabilidade. Útil
quando o documento é para distribuição pública.

### Caso 5: pipeline manual (cada etapa isolada)

```bash
# Útil quando algo no macro falhou e você quer retomar do meio
pdf2md extract paper.pdf --out _raw/
pdf2md restruct paper_out/ --pdf paper.pdf --marker-out _raw/
pdf2md optimize paper_out/
pdf2md stats paper_out/ --source-pdf paper.pdf
pdf2md prov paper_out/ --source paper.pdf --extractor "marker-pdf 1.10.2"
```

### Caso 6: medir só round-trip de um MD existente

```bash
pdf2md rt corpus/nc/04_quantum_circuits/04_quantum_circuits.md --work /tmp/rt
# ou para detectar drift / blow-up:
pdf2md rt-multi 04_quantum_circuits.md --work /tmp/mrt -n 5
```

### Caso 7: normalização ad-hoc

```bash
pdf2md norm file.md > normalized.md
pdf2md norm file.md -i                  # in-place
pdf2md norm file.md --strip-escapes     # Q11.b (form-fields)
```

---

## Variáveis de ambiente

| Variável | Default | Função |
|---|---|---|
| `PDF2MD_MARKER` | `marker_single` no PATH, ou `Z:\venvs\marker\Scripts\marker_single.exe` | path do marker |
| `PDF2MD_PANDOC` | `pandoc` no PATH | path do pandoc |
| `PDF2MD_CHROME` | `chrome` no PATH, ou `C:\Program Files\Google\Chrome\Application\chrome.exe` | path do Chrome |

---

## Estrutura do repo

```
pdf2md/
├── README.md          (este arquivo — manual de uso)
├── DIARIO.md          (timeline narrativa do projeto)
├── ROADMAP.md         (frentes A-E + fases)
├── pyproject.toml     (deps mínimas: typer, pymupdf, pillow)
├── src/
│   ├── pdf2md/        (pacote — ponto de entrada)
│   │   ├── cli.py     (Typer app)
│   │   ├── normalize.py
│   │   └── provenance.py
│   ├── stats.py       (scripts standalone que o cli.py delega via subprocess)
│   ├── aggregate_stats.py
│   ├── roundtrip.py
│   ├── multi_roundtrip.py
│   ├── optimize_images.py
│   ├── gen_pdfs.py
│   └── restructure.py
├── lab/               (bancada experimental — eNN/ por experimento)
├── tickets/           (open/closed/research/blocked — agrupados em INDEX.md)
├── docs/
│   ├── ARQUITETURA.md         (overview 4 camadas)
│   ├── arquitetura/           (detalhes por camada)
│   ├── PHILOSOPHY.md          (hierarquia + eixo de representação)
│   ├── METRICS.md             (painel multi-métrica)
│   ├── LITERATURA.md          (snapshot v1 — ver v2)
│   ├── LITERATURA_v2.md       (incl. T071 alucinação + Q-list)
│   ├── biblioteca/            (catálogo: ferramentas/métricas/papers/benchmarks)
│   ├── LAB_PROTOCOL.md        (regras de bancada)
│   ├── LICENSING.md           (matriz de licenças do corpus)
│   └── _archive/              (docs históricos)
└── corpus/
    ├── _sources/MANIFEST.md   (refs read-only)
    ├── _canonical/MANIFEST.md (corpus público)
    └── nielsen_chuang/        (extração de referência — versionada)
```

PDFs binários moram fora do repo — sources canônicos em outros projetos
(ex.: AulaQuantum) e corpus público em `Z:\caches\corpus\pdf2md\`. O repo
guarda só refs (manifests YAML) e resultados de extração.

---

## Resultado ancoragem (snapshot 2026-05-08, baseline e00)

Aplicado a Nielsen & Chuang QCQI (704 páginas, 21 capítulos):

| Métrica | Valor |
|---|---:|
| PDF original | 8.1 MB, 704 páginas |
| MD extraído | 332,652 tokens |
| **Round-trip (cap. 4)** | **95.09%** |
| Multi-iteration (paper de teste) | drift 0.86% em 5 iter, **estável** |
| Imagens (após T131) | 4.5 MB → 2.7 MB (**−38.6%**) |
| Tempo de extração | 4145 s (~70 min, GPU RTX 3060) |

Detalhes em [`corpus/nielsen_chuang/_stats.md`](corpus/nielsen_chuang/_stats.md).

Ablações validadas (todas em `lab/`):

- **e07 Marker `--use_llm`** (llama3.2-vision/Ollama): 40× mais lento, qualidade ≈ baseline → descartado para N&C LaTeX nativo
- **e08 Granite-Docling-258M**: 50× mais lento, imagens em base64 inline → descartado para livro; install limpo (resolve fricção Q15)

Conclusão atual: **Marker baseline 95.09% é o teto operacional testado** para este PDF específico.

---

## Origem

Ver [`DIARIO.md`](DIARIO.md) para timeline cronológica desde a primeira
ideia até a separação em projeto autônomo.
