# Manifest — corpus canônico público

PDFs livres / open-access / public domain usados para benchmark e ablação. Cada entrada é re-baixável via URL — a cópia local em `Z:\caches\corpus\pdf2md\` é por comodidade.

Para schema completo, ver [`../_sources/MANIFEST.md`](../_sources/MANIFEST.md). Aqui o `origin.type` será sempre `url`, e `license` sempre uma licença redistribuível.

## Cobertura desejada

Objetivo: corpus pequeno mas representativo das categorias problemáticas do conversor. Meta de **8-12 entradas**, distribuídas:

- 1-2 livros math-heavy
- 1-2 papers math-heavy (arXiv)
- 1 paper bio/med (PMC)
- 1 PDF "image-only" (scanned)
- 1-2 slides PPTX export
- 1 layout 2-coluna denso (IEEE)
- 1 multilíngue / pt-BR
- 1 tipografia clássica

## Entradas

*Nenhuma ainda. Próxima ação: T040 (corpus canônico inicial — preencher manifest).*

<!-- Template para próximas entradas:

### <id> — <título curto>

```yaml
id: <slug>
title: <título completo>
authors: [<a1>, <a2>]
year: <YYYY>
license: <cc_by | cc_by_sa | public_domain | arxiv non-exclusive | ...>
category: <ver schema>
pages: <N>

origin:
  type: url
  url: https://...
  alternates:
    - https://mirror.../

local_copy:
  path: Z:\caches\corpus\pdf2md\<id>.pdf
  sha256: <hex>
  downloaded_at: <YYYY-MM-DD>

sha256: <hex>     # mesmo hash da local_copy enquanto sincronizadas
size_bytes: <N>
added_at: <YYYY-MM-DD>

notes: |
  <contexto, escolha, links relevantes>
```

-->
