---
id: T023
titulo: Convenção de venv por experimento (manual, descartável)
status: closed
criado_em: 2026-05-09
fechado_em: 2026-05-09
fase: 0
depende_de: [T020]
blocks: [T050]
tags: [infra, venv, lab]
kind: infra
---

## Contexto

`pyproject.toml` foi zerado em 2026-05-09 (deps vazias) por causa de conflito pillow<11 (marker-pdf) × pillow>=11. Continuar instalando coisas no venv principal (`Z:\venvs\pdf2md`) reintroduz o problema.

Decisão (memória `feedback_lab_workflow`): cada experimento tem seu próprio venv, ativado manualmente, descartável.

## Objetivo

Documentar a convenção em `lab/README.md` e `docs/LAB_PROTOCOL.md` com comandos copiáveis para criar / ativar / descartar venv de experimento.

## Critérios de aceitação

- [x] Padrão `Z:\venvs\pdf2md_lab_eNN` documentado
- [x] Comando de criação registrado: `py -m venv Z:\venvs\pdf2md_lab_eNN --prompt eNN`
- [x] Ativação manual (sem auto-activate VSCode): `Z:\venvs\pdf2md_lab_eNN\Scripts\Activate.ps1`
- [x] Limpeza segura: `Remove-Item -Recurse Z:\venvs\pdf2md_lab_eNN` (porque é venv direto, não junction)
- [x] Distinção do venv principal `Z:\venvs\pdf2md` (que fica mínimo)

## Resultado

Convenção documentada. Princípio: nunca instalar deps experimentais no venv principal antes de validar via experimento.

Aviso registrado: se algum dia houver `.venv` no projeto como junction para `Z:\`, **não** usar `Remove-Item -Recurse` (segue o link e destrói o venv real). Aqui no lab os venvs são diretamente em `Z:\`, então `Remove-Item -Recurse` é seguro.
