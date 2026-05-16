---
id: T076
titulo: md_to_pdf sobrescreve PDF co-irmão silenciosamente quando basenames colidem
status: open
criado_em: 2026-05-16
fechado_em:
fase: 2
depende_de: []
blocks: [T070]
tags: [bug, pdf2md, pdfs, seguranca-dados]
kind: pipeline
---

## Contexto

`pdf2md.pdfs.md_to_pdf(md_path)` salva o PDF gerado em
`md_path.with_suffix(".pdf")` (mesmo diretório do MD, mesmo basename,
extensão `.pdf`). Não recebe parâmetro de destino.

Quando o diretório do MD já contém um arquivo `<basename>.pdf` (caso
comum em `corpus/<doc>/<cap>/` que tem `<cap>.md` + `<cap>.pdf`
co-irmãos), **o PDF existente é silenciosamente sobrescrito** —
sem warning, sem flag de proteção.

## Como reproduzir

```python
from pathlib import Path
from pdf2md.pdfs import md_to_pdf

# corpus/nielsen_chuang/04_quantum_circuits/ tem 04.md + 04.pdf
md = Path("corpus/nielsen_chuang/04_quantum_circuits/04_quantum_circuits.md")
pdf_pre = md.with_suffix(".pdf")
sha_before = hashlib.sha256(pdf_pre.read_bytes()).hexdigest()

md_to_pdf(md)  # silenciosamente sobrescreve o PDF original

sha_after = hashlib.sha256(pdf_pre.read_bytes()).hexdigest()
assert sha_before != sha_after  # PDF foi sobrescrito
```

Reproduzido em `lab/e09_pixel_roundtrip_proto/` (2026-05-16). Foi
necessário `git restore` para recuperar o PDF.

## Impacto

- **Severidade alta**: destruição silenciosa de arquivo gerado por outro
  passo do pipeline. Em casos sem git, perda definitiva.
- **Casos afetados**: qualquer uso de `pdf2md pdfs` ou `pdf2md.pdfs.md_to_pdf`
  num diretório que já tenha PDFs co-irmãos. O pipeline padrão do
  `pdf2md convert` produz justamente essa estrutura (MD + PDF render
  no mesmo diretório), então **o próprio pipeline pode se autocorromper**
  em re-runs.

## Decisão

Mudar a assinatura para aceitar `out_pdf: Path | None`:

```python
def md_to_pdf(
    md_path: Path,
    out_pdf: Path | None = None,  # default: md_path.with_suffix(".pdf")
    *,
    pandoc: str = DEFAULT_PANDOC,
    chrome: str = DEFAULT_CHROME,
    css: str = CSS_INLINE,
    overwrite: bool = False,  # NEW
) -> Path:
```

- Se `out_pdf=None` e o destino default existe → raise `FileExistsError`
  a menos que `overwrite=True`.
- Se `out_pdf` é passado → respeita.
- `pdf2md convert` (macro) e `pdf2md pdfs` passam `overwrite=True`
  explicitamente, mantendo compatibilidade do uso normal.

Tests:
- [ ] Chamar com destino existente sem `overwrite=True` levanta erro
- [ ] Chamar com `overwrite=True` sobrescreve
- [ ] Chamar com `out_pdf` explícito ignora destino default
- [ ] Re-run de `pdf2md convert` no mesmo diretório não corrompe outputs

## Critério de aceitação

- [ ] Assinatura nova implementada com `out_pdf` + `overwrite`
- [ ] Default behavior: raise se destino existe (proteção)
- [ ] Tests cobrindo os 4 casos acima
- [ ] CLI subcommands (`pdf2md pdfs`, `pdf2md convert`) passam
      `overwrite=True` explicitamente
- [ ] Patch release v0.4.1

## Não-objetivo

- Backup automático do PDF sobrescrito (out of scope)
- Detecção semântica de "PDF gerado pelo pdf2md vs original" (resolvido
  pelo MD_CANONICAL §"Acessórios" — sempre usar AulaQuantum como source)

## Conexão

- Bloqueia [T070](../research/T070_pixel_roundtrip_validador_visual.md) — descoberto durante lab e09
- Patch v0.4.1
