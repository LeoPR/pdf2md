# pdf2md

Conversor PDF ↔ MD com round-trip mensurável e otimização adaptativa de imagens.

Projeto autônomo nascido do `AulaQuantum` (faixa T400) quando o conversor
amadureceu além do escopo daquela disciplina. Mora em
`Acadêmicos/transmutos/pdf2md/` por convenção da máquina (ver
[`Z:\caches\README.md`](Z:\caches\README.md) para padrões locais).

## Status (v0.7.0, 2026-05-16)

| Camada / capacidade | Estado | Versão | Notas |
|---|---|---|---|
| **Extração** marker-pdf 1.10.2 (GPU) | Estável | v0.1+ | 95.09% round-trip em N&C cap 4 |
| **MD → PDF** pandoc 3.9 + Chrome + KaTeX | Estável | v0.1+ | |
| **Round-trip textual** MD → PDF → MD' | Estável | v0.1+ | mediana sim 95% LaTeX nativo |
| **Multi-iteration round-trip** | Estável | v0.2+ | 97.4% após 5 iter em paper |
| **CLI unificado `pdf2md`** | Estável | v0.4 | macro convert + 10 subcomandos, sem subprocess |
| **Telemetria por extração + agregada** | Estável | v0.4 | `_stats.json`, `_OVERVIEW.json` |
| **Otimização adaptativa de imagens** | Estável (níveis 1-2) | v0.4 | PNG paleta lossy + 1-bit + JPEG mantido; -38.6% em N&C |
| **Marcador de proveniência idempotente** | Estável | v0.4 | `pdf2md prov`, HTML comment + blockquote |
| **Telemetria por step** (wall/cpu/mem/gpu/io) | Estável | v0.5 | `pdf2md.telemetry` (psutil + nvidia-smi) |
| **Pixel-roundtrip visual L0.5** | Estável | v0.6 | `pdf2md rt-pixel`: align Hungarian/DTW + SSIM + WER |
| **rt-pixel integrado no convert** | Estável | v0.7 | `--rt-pixel` ou `--best` ativam automaticamente |
| Vetorização SVG (potrace) | Roadmap | — | T132 |
| Detecção + extração fórmula → LaTeX | Roadmap | — | T133/T134 (pix2tex) |
| Reconstrução vetorial de logos | Roadmap | — | T180 (texto+fonte+brasão) |
| Macro-intent CLI (`--rapido`/`--auto`) | Roadmap | — | T090 (depende mapa de perfis) |
| Mini-corpus GT humano | Roadmap | — | T060 (destrava T072 calibração) |
| Alt-tools (Nougat/MinerU/olmOCR/Docling) | Pesquisa | — | T410, e06/e07/e08 descartados — ver [`docs/reference/tecnologias.md`](docs/reference/tecnologias.md) |

**Documentação:**
- Arquitetura completa: [`docs/explanation/arquitetura.md`](docs/explanation/arquitetura.md)
- Filosofia de design: [`docs/explanation/philosophy.md`](docs/explanation/philosophy.md)
- Tese da família transmutos: [`docs/explanation/transmutos.md`](docs/explanation/transmutos.md)
- Schema do MD canônico: [`docs/reference/md_canonical.md`](docs/reference/md_canonical.md)
- **Perfis de tecnologias (tempo/mem/gpu)**: [`docs/reference/tecnologias.md`](docs/reference/tecnologias.md)
- **Análise crítica do curso**: [`docs/explanation/analise_critica.md`](docs/explanation/analise_critica.md)
- Painel de métricas: [`docs/reference/metricas.md`](docs/reference/metricas.md)
- Revisão de literatura: [`docs/explanation/literatura.md`](docs/explanation/literatura.md) · [`v2`](docs/explanation/literatura.md)
- Bancada experimental: [`docs/how-to/criar_novo_lab.md`](docs/how-to/criar_novo_lab.md)

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
├── README.md          overview + uso rápido (este arquivo)
├── ROADMAP.md         frentes A-E + fases
├── CHANGELOG.md       releases e mudanças por versão
├── pyproject.toml     v0.7.0; deps + entry point
├── src/pdf2md/        (10 módulos — toda a lógica do pacote)
│   ├── cli.py · normalize.py · provenance.py · stats.py · aggregate.py
│   ├── roundtrip.py · multi_roundtrip.py · pdfs.py · restructure.py · optimize.py
│   ├── telemetry.py            wall/cpu/mem/gpu/io por step (v0.5)
│   └── pixel_roundtrip.py      validador visual L0.5 (v0.6)
├── lab/               bancada experimental — eNN/ por experimento (15 labs)
├── tickets/           work items: open/closed/research/blocked + INDEX.md
├── corpus/nielsen_chuang/   extrações de referência (gitignored se push público)
└── docs/              **organizado por Diátaxis** (Procida ~2017)
    ├── README.md          índice + explicação do método
    ├── tutorials/         LEARNING — passo-a-passo
    ├── how-to/            GOAL — soluções para problemas concretos
    ├── reference/         INFO — definições autoritativas
    │   ├── cli.md · md_canonical.md · metricas.md · tecnologias.md · conventions.md
    │   ├── modulos/       API por módulo
    │   ├── corpus/        manifests + licensing
    │   └── biblioteca/    catálogo (ferramentas/métricas/papers/benchmarks/glossário)
    ├── explanation/       UNDERSTANDING — por quê, conceitual
    │   ├── arquitetura.md (+ sub-arquitetura/01-05 detalhes por camada)
    │   ├── philosophy.md · transmutos.md · analise_critica.md
    │   ├── literatura.md  revisão de literatura (papers, ferramentas, benchmarks)
    │   └── diario.md      timeline cronológica do projeto
    └── _archive/          documentos históricos
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

Ver [`docs/explanation/diario.md`](docs/explanation/diario.md) para timeline cronológica desde a primeira
ideia até a separação em projeto autônomo.
