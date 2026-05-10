---
id: T021
titulo: Manifest de sources read-only (N&C)
status: closed
criado_em: 2026-05-09
fechado_em: 2026-05-09
fase: 0
depende_de: []
blocks: [T040, T050]
tags: [infra, corpus, manifest]
kind: infra
---

## Contexto

PDFs originais não devem morar dentro de `pdf2md/` — são pesados, não devem ir pro git/OneDrive, e geralmente já moram em outro lugar (ex.: N&C QCQI no projeto AulaQuantum). Precisava de um schema de manifest que cobrisse os dois cenários:

1. Source canônico em path local de outro projeto (proprietary, cópia pessoal)
2. Source público com URL externa + cópia local opcional em `Z:\` por comodidade

## Objetivo

Criar `corpus/_sources/MANIFEST.md` com schema YAML (bloco por entrada) e a primeira entrada concreta: N&C QCQI apontando para o path no AulaQuantum.

## Schema (resumo)

Cada entrada tem `id`, `title`, `authors`, `year`, `license`, `category`, `pages`, e dois objetos importantes:

- `origin` (`type: local | url`) — onde o arquivo "vive" canonicamente
- `local_copy` (`null` se não há cache em `Z:\`) — cópia de trabalho

Hash sha256 detecta drift entre origin e local_copy quando ambos existem.

## Critérios de aceitação

- [x] Schema documentado no próprio `MANIFEST.md`
- [x] Entrada `nc_qcqi` com path absoluto + sha256 + tamanho corretos
- [x] Categoria taxonômica (`livro_math_heavy`) consistente com o doc

## Resultado

`corpus/_sources/MANIFEST.md` criado. N&C registrado:

- path: `C:/Users/leona/OneDrive/Documents/Projects/Acadêmicos/AulaQuantum/pesquisa_geral/_sources/livros/Nielsen_Chuang_QCQI.pdf`
- sha256: `4090c88c294fbe428114256185118b6862d8716a14f9ebf2c7df258f28eb640e`
- size: 8,125,074 bytes
- pages: 704

Estabelece padrão para próximas entradas (em `_canonical/MANIFEST.md` para corpus público).
