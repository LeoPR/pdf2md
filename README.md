# pdf2md

Converte **PDF → Markdown limpo** escolhendo sozinho o caminho mais barato que dá
conta do seu PDF — e, diferente de um extrator comum, ele consegue **medir se a
extração ficou fiel, sem precisar de um gabarito**. O núcleo roda em qualquer
máquina: só `pip`, sem GPU, sem modelos, sem internet.

```bash
pip install pdf2md-tool
pdf2md convert paper.pdf --intent fast --out out/
```

Você recebe um `.md` indexável em `out/` em ~0.02 s por página, sem instalar mais
nada. Precisa de math em LaTeX, layout e tabelas? Troque para `--intent quality`
(que usa GPU/marker se houver e **degrada com aviso honesto** se não houver).

> No PyPI o pacote chama-se **`pdf2md-tool`** (o slug `pdf2md` estava reservado). O
> **comando** e o **import** continuam `pdf2md`.

---

## Como usar

```bash
pdf2md doctor                                  # o que a sua máquina tem (o núcleo é sempre OK)
pdf2md convert FILE.pdf --intent fast --out out/   # CPU puro, velocidade máxima
pdf2md convert FILE.pdf --intent quality           # máxima fidelidade (usa GPU se houver)
pdf2md convert FILE.pdf --intent auto              # a melhor coisa que cabe nesta máquina
pdf2md route   FILE.pdf --intent quality           # dry-run: mostra o pipeline (sem rodar)
```

**Os intents aceitam inglês ou português** (são equivalentes):

| Intent (EN / PT) | Para quê serve |
|---|---|
| `fast` / `rapido` | indexar/pré-processar em massa; menor tempo de parede (CPU puro) |
| `quality` / `qualidade` | máxima fidelidade — math em LaTeX, layout, tabelas (quer GPU/marker) |
| `balanced` / `balanceado` | uso geral (marker se houver, senão CPU) |
| `auto` | "faça a melhor coisa possível aqui" — a melhor stack que a máquina comporta |
| `indexing` / `indexacao` | milhares de docs: indexa tudo no pass1, enfileira só os math-heavy no pass2 |
| `low-resource` | máquinas magras (teto de RAM 160 MB; degrada em vez de estourar) |

Detalhes de cada intent em [how-to/escolher_intent](docs/how-to/escolher_intent.md);
referência completa de CLI em [reference/cli](docs/reference/cli.md).

---

## O que você ganha

- **Funciona no seu laptop, sem setup.** O núcleo é 100% CPU, offline, determinístico
  — nenhum modelo para baixar, nenhuma chamada de rede.
- **Não te força a ferramenta errada.** Um roteador escolhe, por **custo medido**, o
  caminho mais barato que satisfaz o seu intent — e quando a máquina não comporta o
  que você pediu, **avisa e degrada** (a justificativa vai para a proveniência), nunca
  finge qualidade nem quebra em silêncio.
- **Você sabe se pode confiar na saída.** Além de extrair, o pdf2md **audita a
  fidelidade da extração por documento, sem gabarito** — o diferencial (ver abaixo).
- **Saída em Markdown.** Indexável, versionável, legível em qualquer lugar — um
  "ambiente de informação geral", não um formato preso a uma ferramenta.

---

## Por que é útil — roteador + auditor

São duas ideias, e é onde o projeto se diferencia de "mais um extrator":

**1. Roteador.** A literatura de OCR/VLM de 2024–2026 já extrai muito bem; forçar
sempre o modelo mais pesado é caro e desnecessário. O pdf2md mede cada caminho em
**primitivas de utilidade** (velocidade, qualidade por elemento, recomposição,
latência, memória) e deixa um roteador escolher o mais barato que ainda serve.

**2. Auditor (o diferencial).** Qualquer extrator — inclusive os VLMs mais novos —
pode **alucinar conteúdo plausível em silêncio** e só reporta um número médio de
*benchmark*. O pdf2md mede a **página que você acabou de processar**: re-renderiza a
extração e compara com a original, em **dois eixos** (a extração regenera a página? e
a saída é útil/indexável ou virou um raster opaco?). Isso permite **auditar — e
desafiar — qualquer extrator**, não competir com ele.

> O desenho completo do fluxo (entrada → segmentação → roteamento → extração →
> auditoria → saída), com diagramas, está no
> **[painel de arquitetura](docs/explanation/arquitetura.md)**.

---

## A teoria, simplificada

O auditor vem da **construção de compiladores**. Um decompilador não recupera o
código-fonte original (inacessível); recupera uma representação que, **recompilada,
produz o mesmo observável**. Aqui: a extração é a "decompilação" (PDF → Markdown), a
reconstrução `md → pdf` é a "recompilação", e o observável é a **página renderizada**.
Se a extração regenera a página, ela *representa* a informação dela — mesmo sem
sabermos a fonte. A modernização nossa: a régua de comparação é trocável (medimos que
SSIM de pixel **não** serve para conteúdo; usamos OCR-de-texto) e os dois eixos
(fidelidade × qualidade) são **indissociáveis**.

Leitura: [tese decompilar/recompilar](docs/explanation/transmutos.md) ·
[avaliação medida × literatura (formato artigo)](docs/explanation/avaliacao.md) ·
[panorama de extratores OCR 2023–2026](docs/reference/panorama_extractores_ocr.md).

---

## Instalação completa

```bash
pip install pdf2md-tool                # núcleo CPU (typer, pymupdf, pillow, psutil)
pip install "pdf2md-tool[rtpixel]"     # + validador visual (numpy/scipy/scikit-image)
pip install "pdf2md-tool[ocr]"         # + wrapper pytesseract (engine é externo)
pip install "pdf2md-tool[tables]"      # + medidor TEDS de tabelas (apted/lxml)
pip install "pdf2md-tool[all]"         # tudo que é pip-puro seguro
```

Para desenvolver / rodar o master: [instalar do fonte](docs/how-to/instalar_do_fonte.md).

**Capacidades externas** (não instaláveis por pip deste pacote — `pdf2md doctor` valida
e diz o que falta para cada intent):

| Capacidade | Como obter | Por que é externa |
|---|---|---|
| **marker/GPU** (math+layout nativo) | venv próprio + `PDF2MD_MARKER` | conflito `pillow<11` + torch/CUDA |
| **pix2tex** (math→LaTeX em CPU) | venv com torch + `PDF2MD_PIX2TEX_PYTHON` | torch é pesado/OS-específico |
| **tesseract** (OCR de scan) | engine no PATH + extra `[ocr]` | binário de sistema |
| **pandoc + Chrome** (MD→PDF, para o auditor) | no PATH | binários de sistema |
| **ollama + gemma3/qwen** (logos) | daemon `:11434` + `ollama pull` | server + modelos fora do pip |

> Não existe `pip install pdf2md-tool[gpu]` **de propósito**: marker fixa `Pillow<11` e
> é impossível co-instalar no mesmo ambiente. A interface honesta para a stack pesada é
> o `doctor`, não um extra pip.

**Variáveis de ambiente** (descoberta portável em `pdf2md/discovery.py`: `env → PATH →
local padrão do SO`): `PDF2MD_MARKER`, `PDF2MD_PIX2TEX_PYTHON`, `PDF2MD_TESSERACT`,
`PDF2MD_PANDOC`, `PDF2MD_CHROME`, `PDF2MD_ZCACHE`, `PDF2MD_AULAQUANTUM`.

---

## Resultados medidos

Âncoras em **1 host** (RTX 3060, N pequeno) — é "roteamento medido para este corpus",
não benchmark universal; RAM/cold-start de marker/VLM são *estimados*.

| Vértice | Âncora | Ganho do roteamento |
|---|---|---|
| **Velocidade** | pdftotext **0.02 s/pg** vs marker 12.9 | ~630× no caminho `fast` |
| **RAM** | pdftotext **63 MB** vs marker ~1500 (est.) | teto duro 160 MB em `low-resource` |
| **Latência** | pdftotext **0.1 s** vs marker ~30 s (est.) | sem warm-up no default |
| **Qualidade** | prosa **0.95** · scan impresso WER **0.052** · matriz **0.50** ⚠ | roteada por sub-elemento |
| **Round-trip textual** (N&C cap.4, marker) | **95.09%** · multi-iteração drift 0.86% (estável) | health-check sem gabarito |
| **Tabelas** (sintético, TEDS) | marker **1.000** (sem span) · **0.749** (span = teto do formato pipe) | pdftotext 100% conteúdo, 0 estrutura |

Os números do N&C são **resultados derivados** (métricas, não a obra), sob licença
legítima — ver [`corpus/RIGHTS.md`](corpus/RIGHTS.md). Perfis completos em
[`docs/profiles/`](docs/profiles/).

---

## Status

**Pronto e estável:** roteador por intent (CPU/GPU, degradação honesta) · extração CPU
(pdftotext/PyMuPDF + Tesseract para scan) · cropper de fórmula CPU + pix2tex ·
extração GPU (marker, externo) · MD→PDF (pandoc + Chrome + KaTeX + mermaid offline) ·
telemetria por step · round-trip textual + pixel-roundtrip · TEDS de tabelas ·
otimização adaptativa de imagens · corpus em 3 tiers (com sintético GT-por-construção).

**Em desenvolvimento:** o **auditor de fidelidade** (round-trip como prova, 2 eixos —
já mede sem gabarito e já pegou uma falha real, falta cobrir alucinação de VLM) ·
confronto com extratores externos na mesma régua · reconstrução vetorial de logos ·
perfis cross-hardware. Estado e desenho no [painel de arquitetura](docs/explanation/arquitetura.md).

---

## Estrutura do repositório

```
pdf2md/
├── src/pdf2md/      lógica do pacote (routing · executor · extractors · pixel_roundtrip · telemetry · …)
├── corpus/          dataset em 3 tiers (examples livres in-repo; pesados fora do repo) + RIGHTS.md
├── docs/            Diátaxis (tutorials/how-to/reference/explanation/profiles)
├── lab/             bancada experimental interna (não versionada; resultados promovidos em docs/ e tickets/)
└── tickets/         work items (open/closed/research) + INDEX.md
```

## Documentação

- **[Painel de arquitetura](docs/explanation/arquitetura.md)** — posicionamento, fluxo, desenhos, teoria, estado
- [Panorama de extratores OCR](docs/reference/panorama_extractores_ocr.md) — confronto 2023–2026
- [Avaliação (formato artigo)](docs/explanation/avaliacao.md) · [Filosofia](docs/explanation/philosophy.md) · [Tese transmutos](docs/explanation/transmutos.md)
- [Escolher intent](docs/how-to/escolher_intent.md) · [Referência de CLI](docs/reference/cli.md) · [Perfis medidos](docs/profiles/)
- [Direitos do corpus](corpus/RIGHTS.md)

Licença: MIT (ver [`LICENSE`](LICENSE)).
