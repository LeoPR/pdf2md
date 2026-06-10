# Instalar do código-fonte (dev)

Para USAR o pdf2md basta `pip install pdf2md-tool` (ver
[README](../../README.md)). Esta página é para quem vai **desenvolver** ou
quer rodar a versão do master.

```bash
git clone https://github.com/LeoPR/pdf2md && cd pdf2md
pip install -e .                 # núcleo CPU (typer, pymupdf, pillow, psutil)
pip install -e ".[rtpixel]"      # + validador visual (numpy/scipy/scikit-image)
pip install -e ".[ocr]"          # + wrapper pytesseract (engine é externa)
pip install -e ".[tables]"       # + medidor TEDS de tabelas (apted/lxml)
pip install -e ".[all]"          # tudo que é pip-puro seguro
```

Dev roda a suíte completa com:

```bash
uv sync --all-extras
python -m pytest tests -q
```

Os testes que dependem de ferramentas externas (pandoc/Chrome, zcache em
`PDF2MD_ZCACHE`) fazem `skipif` limpo — a suíte passa num clone cru.

## Capacidades externas (não-pip)

marker/GPU, pix2tex, Tesseract, pandoc/Chrome e ollama ficam **fora do
pyproject de propósito** (conflito `pillow<11` do marker; torch pesado e
OS-específico; binários de sistema). `pdf2md doctor` valida cada uma; a
tabela de como obter cada capacidade está no [README](../../README.md#instalação).

> *Setup do autor (não é requisito):* venvs em `Z:\venvs\` via junction;
> ver [conventions](../reference/conventions.md).
