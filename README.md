# pdf2md

Conversor PDF → Markdown que **mede cada extrator em vértices primitivos**
(velocidade, memória, VRAM, latência, qualidade por elemento, footprint de
instalação) e deixa um **roteador escolher o caminho mais barato que ainda
satisfaz o seu intent**. Em vez de "o melhor extrator universal", entrega a
decisão: `--rapido` usa um caminho CPU puro (offline, determinístico, ~0.02 s/pg);
`--qualidade` gasta GPU/marker só quando você pede e o host comporta.

O **núcleo roda em qualquer máquina** — só `pip`, sem GPU, sem modelos, sem rede.
As capacidades pesadas (marker/GPU, pix2tex, OCR, VLM) são **opcionais** e
detectadas em runtime por `pdf2md doctor`.

```bash
pip install pdf2md-tool           # núcleo CPU — nada externo
pdf2md convert paper.pdf --intent rapido
```
> No PyPI o pacote chama-se **`pdf2md-tool`** (o slug `pdf2md` estava reservado por
> outra conta). O **comando** e o **import** continuam `pdf2md`.

---

## Quickstart sem GPU (o caminho portável)

```bash
pip install pdf2md-tool
pdf2md doctor                       # o que você tem (core sempre OK; resto opcional)
pdf2md convert paper.pdf --intent rapido --out out/
```

`--rapido` roteia para **pdftotext (PyMuPDF)**: prosa fiel, math como Unicode cru,
0 VRAM, ~63 MB RAM, ~0.1 s de cold-start, determinístico. Não precisa instalar
mais nada. Para recuperar math em LaTeX, layout e tabelas, use `--qualidade` (que
quer marker/GPU) — `pdf2md doctor --intent qualidade` diz exatamente o que falta.

---

## Por que vale a pena — vértices medidos (RTX 3060, N pequeno)

| Vértice | Como o roteador fecha | Âncora medida |
|---|---|---|
| **Velocidade** | `--rapido`/`--low-resource`/`--indexacao` → pdftotext | **0.02 s/pg** vs marker 12.9 (~**630×**) |
| **RAM** | teto duro 160 MB em `--low-resource`; degrada, não estoura | pdftotext **63 MB** vs marker ~1500 (est.) |
| **CPU-only** | pipeline 100% CPU (pdftotext + cropper built-in + pix2tex) | math display **0.80** sem GPU |
| **Latência** | default sem warm-up; refiners caros só quando o intent paga | pdftotext **0.1 s** vs marker ~30 s (est.) |
| **Qualidade** | roteada por **sub-elemento** (prosa/math/matriz/logo) | prosa 0.95 · scan impresso WER 0.052 · matriz 0.50 ⚠️ |
| **Footprint** | core offline; pesado é opt-in (`doctor`) | core = só wheels do pyproject |

> **Escopo honesto:** perfis medidos em **1 host** (RTX 3060) e N pequeno; RAM/cold-start
> de marker/VLM são **estimados**. É "roteamento medido para este corpus", não benchmark
> universal. Ver [`docs/profiles/`](docs/profiles/) (os 7 perfis) e
> [`tickets/closed/T090…`](tickets/closed/T090_macro_intent_routing.md).

---

## Status

| Camada / capacidade | Estado | Notas |
|---|---|---|
| **Roteador macro-intent** `--rapido/--qualidade/--balanceado/--auto/--indexacao/--low-resource` | Estável (T090) | `route()` puro profile-driven; degradação honesta |
| **Extração CPU** pdftotext (PyMuPDF) + Tesseract (scan) | Estável | offline, determinístico |
| **Cropper de fórmula CPU + pix2tex** (math display → LaTeX) | Estável | cropper built-in; runtime pix2tex externo (torch) |
| **Extração GPU** marker-pdf (Surya+Texify) | Estável | venv próprio + GPU; math/layout nativo |
| **MD → PDF** pandoc + Chrome + KaTeX | Estável | |
| **Round-trip textual + multi-iteração** | Estável | validador sem ground-truth |
| **Pixel-roundtrip visual L0.5** (SSIM + align) | Estável | extra `[rtpixel]` |
| **Otimização adaptativa de imagens** | Estável | −38.6% em N&C, sem perda visual |
| **Telemetria por step + agregada** | Estável | `psutil` + `nvidia-smi` |
| **TEDS de tabelas** (`pdf2md.table_teds`) | Estável (T075) | extra `[tables]`; marker no teto do formato pipe |
| **Mermaid no md→pdf** (```` ```mermaid ```` → SVG) | Estável (T190) | vendorado, offline |
| Reconstrução vetorial de logos (VLM small-image) | Pesquisa | T180 (não promovido) |
| Vetorização SVG (potrace) · cross-hardware | Pesquisa | T132 · T091 |

---

## Instalação

```bash
pip install pdf2md-tool                # núcleo CPU (typer, pymupdf, pillow, psutil)
pip install "pdf2md-tool[rtpixel]"     # + validador visual (numpy/scipy/scikit-image)
pip install "pdf2md-tool[ocr]"         # + wrapper pytesseract (engine é externo)
pip install "pdf2md-tool[tables]"      # + medidor TEDS de tabelas (apted/lxml)
pip install "pdf2md-tool[all]"         # tudo que é pip-puro seguro
```

Para desenvolver / rodar o master: [instalar do fonte](docs/how-to/instalar_do_fonte.md).

**Capacidades externas (NÃO instaláveis por pip deste pacote — `pdf2md doctor` valida):**

| Capacidade | Como obter | Por que externo |
|---|---|---|
| **marker/GPU** (math+layout nativo) | venv próprio + `PDF2MD_MARKER` | conflito `pillow<11` + torch/CUDA |
| **pix2tex** (math→LaTeX CPU) | venv com torch + `PDF2MD_PIX2TEX_PYTHON` | torch é pesado/OS-específico |
| **tesseract** (OCR scan) | engine UB-Mannheim no PATH + extra `[ocr]` | binário de sistema |
| **pandoc + Chrome** (MD→PDF) | no PATH | binários de sistema |
| **ollama + gemma3/qwen** (logos) | daemon `:11434` + `ollama pull` | server + modelos fora do pip |

> `pip install pdf2md-tool[gpu]` **não existe de propósito**: marker fixa `Pillow<11` e é
> impossível co-instalar no mesmo ambiente. A interface honesta para a stack pesada é o
> `doctor`, não um extra pip.

---

## Uso

```
  MACRO por intent (roteador T090 — escolhe a stack por host+doc)
    pdf2md convert FILE.pdf --intent rapido       # CPU puro, velocidade máxima
    pdf2md convert FILE.pdf --intent qualidade    # marker/GPU se houver; senão degrada
    pdf2md convert FILE.pdf --intent auto          # melhor stack que CABE no host
    pdf2md convert FILE.pdf --intent indexacao     # pass1 indexa tudo; pass2 enfileira math-heavy
    pdf2md route   FILE.pdf --intent qualidade     # dry-run: mostra o pipeline (--execute roda)

  LEGADO (mantido; --intent substitui)
    pdf2md convert FILE.pdf --quick / --best

  SUBCOMANDOS FINOS (controle granular / retomar pipeline parcial)
    pdf2md extract · restruct · optimize · stats · rt · rt-multi · aggr · prov · norm · pdfs

  META
    pdf2md doctor [--intent N]   # capabilities do host (+ o que um intent usaria aqui)
    pdf2md version · help <cmd>
```

### Os 6 intents (resumo; detalhes em [how-to/escolher_intent](docs/how-to/escolher_intent.md))

| Intent | PRIMARY | Para quê |
|---|---|---|
| `--rapido` | pdftotext (mesmo com GPU) | indexar/pré-processar em massa; wall-time mínimo |
| `--low-resource` | pdftotext (teto RAM 160 MB) | máquinas magras; optimize desliga se estourar |
| `--indexacao` | pdftotext (pass1) + marker (pass2 enfileirável) | milhares de docs; pass2 só nos de perda recuperável |
| `--balanceado` (default) | marker se houver, senão pdftotext | uso geral |
| `--qualidade` | marker (degrada p/ pdftotext+pix2tex sem GPU) | máxima fidelidade; math LaTeX, layout |
| `--auto` | melhor que o host comporta | "faça a melhor coisa possível aqui" |

Sem GPU, `--qualidade` **degrada com aviso honesto** (`.rationale` vai pra proveniência),
nunca finge qualidade nem quebra em silêncio.

---

## Variáveis de ambiente

| Variável | Função |
|---|---|
| `PDF2MD_MARKER` | path do `marker_single` (sem fallback de máquina — **necessária** p/ usar marker) |
| `PDF2MD_PIX2TEX_PYTHON` | python de um venv com `pix2tex` (runtime math→LaTeX CPU) |
| `PDF2MD_TESSERACT` | path do `tesseract` (senão PATH → local padrão do SO) |
| `PDF2MD_PANDOC` / `PDF2MD_CHROME` | paths de pandoc / Chrome (senão PATH → local padrão do SO) |
| `PDF2MD_ZCACHE` / `PDF2MD_AULAQUANTUM` | raízes de corpus zcache / source privado (default = drives do autor) |

Descoberta (em `pdf2md/discovery.py`): `env → PATH (multi-nome, multi-SO) → local padrão
do SO → nome do comando`. Sem paths absolutos presos a uma máquina.

---

## Estrutura do repo

```
pdf2md/
├── src/pdf2md/                 (lógica do pacote)
│   ├── cli.py                  CLI (macro --intent, route, doctor, subcomandos)
│   ├── routing.py              ROTEADOR T090: route() puro + HostInfo/DocInfo + pass2_warranted
│   ├── _profiles.py            MAPA: perfis medidos (route-relevant), dep-free
│   ├── executor.py             executa o Pipeline que route() decide
│   ├── extractors.py           PRIMARYs CPU: pdftotext + tesseract
│   ├── formula_cropper.py      cropper de fórmula display CPU (built-in)
│   ├── discovery.py            descoberta portável de ferramentas externas
│   ├── optimize.py             otimização adaptativa de imagens
│   ├── telemetry.py            INSTRUMENTO: wall/cpu/mem/gpu/io por step
│   ├── pixel_roundtrip.py      validador visual L0.5 (extra [rtpixel])
│   ├── roundtrip.py · multi_roundtrip.py   round-trip textual + estabilidade
│   ├── pdfs.py · restructure.py · normalize.py · provenance.py · stats.py · aggregate.py
│   └── _pix2tex_runner.py      script no venv externo do pix2tex (subprocess)
├── corpus/                     dataset em 3 tiers (ver corpus/RIGHTS.md)
│   ├── examples/               excertos LIVRES commitados (prova pronta, sem baixar nada)
│   └── registry.py             resolve(doc_id) → in-repo | zcache | private
├── docs/                       Diátaxis (tutorials/how-to/reference/explanation/profiles)
├── lab/                        bancada experimental interna (não versionada; resultados promovidos em docs/ e tickets/)
└── tickets/                    work items (open/closed/research) + INDEX.md
```

PDFs pesados ficam **fora do repo** (zcache `Z:/caches/...` via `PDF2MD_ZCACHE`, ou sources
privados). O tier in-repo (`corpus/examples/`) tem só excertos livres pequenos.

---

## Resultados (medidos)

Round-trip e telemetria sobre **Nielsen & Chuang QCQI** (704 pág, RTX 3060):

| Métrica | Valor |
|---|---:|
| Round-trip textual (cap. 4, marker) | **95.09%** |
| Multi-iteração (paper) | drift 0.86% em 5 iter (**estável**) |
| Otimização de imagens (cap. 4) | 4.5 → 2.7 MB (**−38.6%**) |
| Extração full-doc (marker) | ~4145 s (~70 min) |

> Os números do N&C são **resultados derivados** (métricas, não reprodução da obra),
> usados sob licença legítima do detentor — ver [`corpus/RIGHTS.md`](corpus/RIGHTS.md). O
> PDF original e reproduções completas ficam fora do repositório.

Caminho CPU validado em corpus livre in-repo: pdftotext prosa WER 0.016 (pg estruturada),
Tesseract scan impresso WER 0.052, pix2tex math display 0.80 (linha única; matriz ~0.50).
Tabelas (corpus sintético, TEDS): marker **1.000** nos tiers sem span e **0.749** em
row/colspan — exatamente o **teto do formato pipe**; pdftotext 0.0 em estrutura
(conteúdo 100%, indexável).

---

## Documentação

- Arquitetura: [`docs/explanation/arquitetura.md`](docs/explanation/arquitetura.md) · Filosofia: [`philosophy.md`](docs/explanation/philosophy.md)
- Perfis medidos: [`docs/profiles/`](docs/profiles/) · Tecnologias: [`docs/reference/tecnologias.md`](docs/reference/tecnologias.md)
- Referência de CLI: [`docs/reference/cli.md`](docs/reference/cli.md) · Escolher intent: [`docs/how-to/escolher_intent.md`](docs/how-to/escolher_intent.md)
- Direitos do corpus: [`corpus/RIGHTS.md`](corpus/RIGHTS.md) · Timeline: [`docs/explanation/diario.md`](docs/explanation/diario.md)

Licença: MIT (ver [`LICENSE`](LICENSE)).
