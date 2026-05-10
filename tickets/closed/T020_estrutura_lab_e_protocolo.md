---
id: T020
titulo: Estrutura lab/ + _template + LAB_PROTOCOL
status: closed
criado_em: 2026-05-09
fechado_em: 2026-05-09
fase: 0
depende_de: []
blocks: [T023, T050]
tags: [infra, bancada, lab]
kind: infra
---

## Contexto

Avaliação do projeto identificou que `src/` tem deps zeradas em `pyproject.toml` (proposital, conflito pillow<11) e que o ambiente é experimental. Decisão de trabalho: separar em **bancada suja** (`lab/`) e **bancada limpa** (`src/`), com cada experimento em venv isolado em `Z:\venvs\pdf2md_lab_eNN`.

## Objetivo

Criar a estrutura física da bancada suja, com template para futuros experimentos e protocolo escrito que governa criação, ciclo de vida e descarte.

## Critérios de aceitação

- [x] `lab/README.md` com convenções (naming, ciclo, venv, limpeza)
- [x] `lab/_template/` com 4 arquivos: README.md, requirements.txt, run.ps1, RESULT.md
- [x] `docs/LAB_PROTOCOL.md` com regras de promoção/descarte/congelamento
- [x] Status de experimento (sufixos `.live`/`.frozen`/`.discarded`) documentado
- [x] Relação com tickets explícita (hipótese ↔ lab; infra/decisão ↔ ticket)

## Resultado

Estrutura criada conforme plano. Próximos macro-tickets de Fase 0: T021, T022, T023, T024, T030, T031, T040, T050.

Convenção principal: experimento autocontido (README + requirements + run + out + RESULT) em venv próprio (`Z:\venvs\pdf2md_lab_eNN`), descartável quando RESULT for "discard".
