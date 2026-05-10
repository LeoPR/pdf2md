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
| Telemetria por extração (`stats.py`) | Estável |
| Telemetria agregada (`aggregate_stats.py`) | Estável |
| Compressão adaptativa de imagens | Nível 1-2 (PNG paleta lossy gated) |
| Restauração de artefatos JPEG | Roadmap (T137) |
| Vetorização SVG (potrace) | Roadmap (T132) |
| Detecção fórmula → LaTeX (pix2tex) | Roadmap (T133/T134) |
| Pacote `pip install pdf2md` | Roadmap (T108) |

Filosofia de design: ver [`docs/PHILOSOPHY.md`](docs/PHILOSOPHY.md).
Como a bancada experimental funciona: ver [`docs/LAB_PROTOCOL.md`](docs/LAB_PROTOCOL.md).

## Estrutura

```
pdf2md/
├── README.md          (este arquivo — estado atual e como usar)
├── DIARIO.md          (timeline narrativa do projeto)
├── ROADMAP.md         (visão de fases e próximos passos)
├── pyproject.toml     (deps zeradas em 2026-05-09 — bancada experimental)
├── src/               (bancada limpa — scripts atuais; viram pacote ao virar T108)
│   ├── stats.py
│   ├── aggregate_stats.py
│   ├── roundtrip.py
│   ├── multi_roundtrip.py
│   ├── optimize_images.py
│   ├── gen_pdfs.py
│   └── restructure.py
├── lab/               (bancada experimental — cada eNN/ é experimento autocontido)
│   ├── README.md      (convenções)
│   └── _template/     (esqueleto para novos experimentos)
├── tickets/           (open/in_progress/blocked/research/closed/_archive)
│   ├── INDEX.md       (agrupado por kind: infra/pipeline/imagens/experimento/decisao)
│   └── README.md      (formato e convenções)
├── docs/
│   ├── PHILOSOPHY.md          (hierarquia de prioridades)
│   ├── LAB_PROTOCOL.md        (regras de bancada — ciclo, promoção, descarte)
│   └── CLAUDE_MEMORY.md       (memórias herdadas do AulaQuantum)
└── corpus/
    ├── _sources/MANIFEST.md   (refs read-only para PDFs em outros projetos)
    ├── _canonical/MANIFEST.md (refs para corpus público — cache em Z:\)
    └── nielsen_chuang/        (resultado da extração baseline — versionado)
        ├── <chapter>/<chapter>.md
        ├── <chapter>/images/*.png|jpeg
        └── _stats.{md,json}
```

PDFs binários moram fora do repo — sources canônicos em outros projetos
(ex.: AulaQuantum) e corpus público em `Z:\caches\corpus\pdf2md\`. O repo
guarda só refs (manifests YAML) e resultados de extração.

## Fluxo típico (após você criar o venv)

```bash
# 1. Extração
marker_single corpus/_sources/<doc>.pdf --output_dir /tmp/<slug> --output_format markdown

# 2. Reorganizar por capítulo (livro com TOC)
python src/restructure.py corpus/_sources/<doc>.pdf /tmp/<slug>/<slug>.md corpus/<slug>/

# 3. Round-trip + telemetria
python src/roundtrip.py corpus/<slug>/<chapter>/<chapter>.md /tmp/<slug>_rt/
python src/stats.py corpus/<slug>/ \
    --source-pdf corpus/_sources/<doc>.pdf \
    --roundtrip-md1 corpus/<slug>/<chapter>/<chapter>.md \
    --roundtrip-md2 /tmp/<slug>_rt/.../md2.md

# 4. Otimização de imagens (PNG lossless/lossy-gated)
python src/optimize_images.py corpus/<slug>/

# 5. Multi-iteration (convergência)
python src/multi_roundtrip.py corpus/<slug>/<chapter>/<chapter>.md /tmp/<slug>_mrt --iterations 5

# 6. Overview consolidado de todo corpus/
python src/aggregate_stats.py corpus/
```

## Setup do venv (instruções para você na primeira abertura)

Convenção da máquina: venv em `Z:\venvs\pdf2md`, junction local
`.venv` neste diretório. Comando:

```powershell
py -m venv Z:\venvs\pdf2md --prompt pdf2md
cmd /c mklink /J .venv Z:\venvs\pdf2md
.venv\Scripts\python.exe -m pip install marker-pdf pillow pymupdf
```

Pandoc e Chrome precisam estar no PATH. KaTeX vem via pandoc `--katex`.

Detalhes em [`docs/CLAUDE_MEMORY.md`](docs/CLAUDE_MEMORY.md) (memória da
máquina: caches em `Z:\`).

## Resultado ancoragem (snapshot 2026-05-08)

Aplicado a Nielsen & Chuang QCQI (704 páginas, 21 capítulos):

| Métrica | Valor |
|---|---:|
| PDF original | 8.1 MB, 704 páginas |
| MD extraído | 332,652 tokens |
| Round-trip (cap. 4) | **95.1%** |
| Multi-iteration (paper de teste) | drift 0.86% em 5 iter, **estável** |
| Imagens (após T131) | 4.5 MB → 2.7 MB (**−38.6%**) |
| Tempo de extração | 4145 s (~70 min, GPU RTX 3060) |

Detalhes em [`corpus/nielsen_chuang/_stats.md`](corpus/nielsen_chuang/_stats.md).

## Origem

Ver [`DIARIO.md`](DIARIO.md) para timeline cronológica desde a primeira
ideia até a separação em projeto autônomo.
