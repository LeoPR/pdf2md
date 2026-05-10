---
id: T050
titulo: Baseline marker reproduzível (lab/e00_baseline_marker)
status: open
criado_em: 2026-05-09
fechado_em:
fase: 0
depende_de: [T020, T021, T023, T031]
blocks: []
tags: [experimento, baseline, marker, n_c]
kind: experimento
---

## Contexto

Antes de comparar ferramentas alternativas (T410), precisa garantir que o pipeline atual ainda roda e atinge o número histórico (round-trip cap. 4 do N&C: **95.1%**). Isso é o **baseline de regressão** — sem ele, qualquer experimento futuro não tem com o que comparar.

Hoje os scripts em `src/` funcionam, mas:
- Paths hard-coded (`Z:/venvs/marker/...`, `C:/Program Files/.../chrome.exe`)
- pyproject.toml com `dependencies = []` — `pip install -e .` não instala nada do necessário
- Venv principal `Z:\venvs\pdf2md` está mínimo

Solução proposta: o experimento usa seu próprio venv (`Z:\venvs\pdf2md_lab_e00`), instala as deps necessárias, roda os scripts existentes (sem mudar `src/`).

## Objetivo

Criar `lab/e00_baseline_marker/` rodando, validando que:

1. Round-trip do N&C cap. 4 ≥ 94% (margem ±1pp do histórico)
2. Tempo de extração na mesma ordem de grandeza do registro histórico (~10 min na GPU)
3. Métricas de T031 calculáveis (mesmo que ainda manualmente nesta passagem)

## Critérios de aceitação

- [ ] `lab/e00_baseline_marker/` criado a partir de `lab/_template/`
- [ ] `README.md` preenchido com hipótese + critério de promoção/descarte
- [ ] `requirements.txt` com `marker-pdf==1.10.x`, `pillow<11`, `pymupdf>=1.27,<2`, `torch` (versão CUDA)
- [ ] Venv `Z:\venvs\pdf2md_lab_e00` criado, deps instaladas, isolado do principal
- [ ] `run.ps1` executando: extract → restructure → roundtrip → stats
- [ ] Round-trip cap. 4: ≥ 94%
- [ ] `RESULT.md` preenchido com veredito (provavelmente "congelar como baseline")

## Critério de promoção / descarte

- **Promover**: número bate histórico → este experimento vira baseline congelado em `.frozen` para regressão futura
- **Descartar**: número regrediu sem motivo claro → abrir sub-ticket de investigação antes de seguir para T410
- **Congelar**: cumprido + documentado, e a frequência de re-rodar é baixa (1× por mudança de pipeline)

## Não-objetivo

- Refatorar `src/` (paths hard-coded etc. — fica para T108 ou ticket dedicado)
- Tornar o pipeline cross-platform — Windows + GPU é suficiente nesta etapa
- Cobrir corpus inteiro do N&C — apenas cap. 4 (a referência histórica)

## Notas

- N&C source vem do `corpus/_sources/MANIFEST.md` (path no AulaQuantum, read-only)
- Cap. 4 já tem MD extraído em `corpus/nielsen_chuang/04_quantum_circuits/` — pode ser usado como ground-truth do MD₁
- Métrica primária ainda é token-similarity (T031 vai expandir, mas baseline pode usar a antiga para comparar com histórico)
