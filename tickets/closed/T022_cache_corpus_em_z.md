---
id: T022
titulo: Cache de corpus em Z:\caches\corpus\pdf2md\
status: closed
criado_em: 2026-05-09
fechado_em: 2026-05-09
fase: 0
depende_de: [T021]
blocks: [T040]
tags: [infra, corpus, cache]
kind: infra
---

## Contexto

PDFs públicos de benchmark (corpus canônico) precisam ficar fora do git e fora do OneDrive — são MB volumosos e sempre re-baixáveis pela URL. Convenção da máquina (`Z:\caches\README.md`) já estabelece `Z:\caches\` como home de caches centralizados.

Precisava criar a pasta dedicada e seu README, com regras claras de "o que entra / o que não entra".

## Objetivo

`Z:\caches\corpus\pdf2md\` criada com README explicando propósito e relação com os manifests do projeto.

## Critérios de aceitação

- [x] Pasta `Z:\caches\corpus\pdf2md\` existe
- [x] `Z:\caches\corpus\pdf2md\README.md` documenta o que entra e o que não entra
- [x] Convenção de naming: `<id>.<ext>` onde `id` é o slug do manifest
- [x] Regra: pasta inteira pode ser apagada sem prejuízo (re-download via manifest)

## Resultado

Pasta criada. README registra:

- O que entra: PDFs públicos baixados, cópias locais de sources externos
- O que NÃO entra: PDFs proprietary, resultados de extração
- Naming: `<id>.<ext>`
- Limpeza: pasta toda apagável; manifest é a fonte da verdade
