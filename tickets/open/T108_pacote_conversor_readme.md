---
id: T108
titulo: Empacotar fluxo do conversor + README de uso
status: open
criado_em: 2026-05-07
fechado_em:
fase: 1
depende_de: [T101, T102, T103, T107]
blocks: []
tags: [conversor, packaging, doc]
kind: pipeline
---

## Contexto
Tudo está rodando ad-hoc na pasta `pesquisa_geral/livros/`. Falta um README que documente:
- Setup (venv, dependências, ferramentas externas)
- Como extrair um livro novo (sequência de comandos)
- Como rodar round-trip
- Como gerar PDFs por capítulo
- Extensões VS Code recomendadas para visualizar o MD com fórmulas

## Objetivo
README `pesquisa_geral/livros/README.md` cobrindo o fluxo end-to-end.

## Critérios de aceitação
- [ ] Setup: marker venv, torch CUDA, ferramentas externas (pandoc, Chrome)
- [ ] Pipeline: marker → restructure → roundtrip
- [ ] VS Code extensions: Markdown All in One (KaTeX), Markdown Preview Mermaid
- [ ] Comandos copiáveis (com paths absolutos do projeto)
