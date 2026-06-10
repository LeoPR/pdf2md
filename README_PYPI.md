# pdf2md

Conversor **PDF → Markdown CPU-first** com roteamento por intent: cada
extrator tem um **perfil medido** (velocidade, RAM, VRAM, qualidade por
elemento) e o roteador escolhe **o caminho mais barato que satisfaz o que
você pediu** — em vez de prometer "o melhor extrator universal".

```bash
pip install pdf2md-tool
pdf2md convert paper.pdf --intent rapido
```

> O pacote chama-se `pdf2md-tool` no PyPI; o **comando** e o **import**
> são `pdf2md`.

## O que você ganha

- **Núcleo 100% offline**: só `pip`, sem GPU, sem modelos, sem rede.
  `--intent rapido` extrai a ~0.02 s/página com ~63 MB de RAM, determinístico.
- **Qualidade opt-in**: `--intent qualidade` usa marker/GPU **se o host
  tiver** — senão degrada com aviso honesto na proveniência, nunca em silêncio.
- **Capacidades pesadas são externas e detectadas em runtime**:
  `pdf2md doctor` diz o que o seu host tem e o que cada intent usaria.
- **Métricas embutidas**: round-trip textual, validador visual (SSIM),
  TEDS de tabelas, telemetria por etapa.

## Intents

| Intent | Caminho | Para quê |
|---|---|---|
| `--rapido` | pdftotext (CPU) | indexar/pré-processar em massa |
| `--low-resource` | pdftotext, teto de RAM | máquinas magras |
| `--indexacao` | pass1 CPU + pass2 seletivo | milhares de docs |
| `--balanceado` | marker se houver | uso geral (default) |
| `--qualidade` | marker/GPU, degrada honesto | máxima fidelidade (math LaTeX, tabelas) |
| `--auto` | melhor que o host comporta | "faça o melhor possível aqui" |

## Extras pip (todos pure-pip, opcionais)

```bash
pip install "pdf2md-tool[rtpixel]"   # validador visual L0.5 (SSIM/alinhamento)
pip install "pdf2md-tool[ocr]"       # wrapper pytesseract (engine é externa)
pip install "pdf2md-tool[tables]"    # medidor TEDS de tabelas
pip install "pdf2md-tool[all]"       # tudo acima
```

marker/GPU, pix2tex, Tesseract, pandoc/Chrome e VLMs **não são extras pip de
propósito** (conflitos reais de dependência, ex. marker fixa `Pillow<11`) —
são capacidades externas validadas pelo `pdf2md doctor`. Detalhes:
[instalação completa](https://github.com/LeoPR/pdf2md/blob/master/README.md#instalação).

## Números (medidos, escopo declarado)

Round-trip textual 95.1% (livro técnico de 704 págs, GPU); caminho CPU: prosa
WER 0.016, scan impresso WER 0.052, math display→LaTeX 0.80; tabelas: marker
no teto do formato pipe (TEDS 1.0; 0.749 em row/colspan = limite do próprio
markdown). Perfis e contexto de cada número:
[docs/profiles](https://github.com/LeoPR/pdf2md/tree/master/docs/profiles).

## Links

- **Repositório**: <https://github.com/LeoPR/pdf2md>
- **Documentação** (Diátaxis): <https://github.com/LeoPR/pdf2md/tree/master/docs>
- **Changelog**: <https://github.com/LeoPR/pdf2md/blob/master/CHANGELOG.md>
- **Corpus e direitos**: <https://github.com/LeoPR/pdf2md/blob/master/corpus/RIGHTS.md>

Licença: MIT.
