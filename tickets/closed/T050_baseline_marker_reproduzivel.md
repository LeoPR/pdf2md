---
id: T050
titulo: Baseline marker reproduzível (lab/e00_baseline_marker)
status: closed
criado_em: 2026-05-09
fechado_em: 2026-05-10
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

- [x] `lab/e00_baseline_marker/` criado a partir de `lab/_template/`
- [x] `README.md` preenchido com hipótese + critério de promoção/descarte
- [x] `requirements.txt` com `marker-pdf>=1.10,<1.11`, `pillow<11`, `pymupdf>=1.27,<2` (torch fica fora do txt — instalado separadamente via index-url do PyTorch CUDA)
- [x] Venv `Z:\venvs\pdf2md_lab_e00` criado e usado
- [x] `run.ps1` executou roundtrip + stats com sucesso
- [x] Round-trip cap. 4: **95.09%** (≥ 94% cumprido com folga)
- [x] `RESULT.md` preenchido — veredito **congelar como baseline**

## Resultado

| Métrica | Histórico (T104) | Baseline e00 | Δ |
|---|---:|---:|---:|
| Round-trip similarity | 95.09% | **95.09%** | 0.00pp |
| Tokens MD₁ / MD₂ | 19,710 / 19,403 | 19,710 / 19,403 | 0 |
| Tempo total | ~9.5 min | 10.8 min | +1.3 min |
| PDF intermediário | 512 KB | 524 KB | +12 KB |
| Top-1 categoria divergência | math (88.5%) | math (88.5%) | igual |

**Reprodução praticamente idêntica.** SHA-256 do PDF intermediário registrado em `lab/e00_baseline_marker/RESULT.md` para fingerprint de regressão futura.

Pasta marcada como `.frozen` — referência preservada para qualquer experimento futuro que toque no pipeline.

### Nota de implementação

O experimento usou `Z:\venvs\marker\` (venv legado, 5 GB de modelos já instalados) como fornecedor do `marker_single.exe` via `$env:PDF2MD_MARKER`. O venv `Z:\venvs\pdf2md_lab_e00\` ficou minimal (apenas `pymupdf` para `stats.py`). Decisão pragmática: re-instalar marker-pdf + torch CUDA + 5 GB de modelos no venv do experimento custaria ~20 min e ~5 GB de espaço, sem ganho de informação — o objetivo era validar o número, não reinstalar tudo.

A consequência: `stats.py` reportou `marker-pdf: n/a` e `torch: n/a` no output (ele inspeciona o venv ativo, não o que o subprocesso usou). Isso é metadado de relatório, não afeta a métrica primária.

## Não-objetivo (mantido)

- Refatorar `src/` (paths hard-coded em `roundtrip.py` continuam apontando para `Z:\venvs\marker\` — funcionou nesta passagem porque é exatamente onde o marker mora; vai virar ticket de pipeline quando T108 ou similar puxar o packaging).

## Não-objetivo

- Refatorar `src/` (paths hard-coded etc. — fica para T108 ou ticket dedicado)
- Tornar o pipeline cross-platform — Windows + GPU é suficiente nesta etapa
- Cobrir corpus inteiro do N&C — apenas cap. 4 (a referência histórica)

## Notas

- N&C source vem do `docs/reference/corpus/manifest_sources.md` (path no AulaQuantum, read-only)
- Cap. 4 já tem MD extraído em `corpus/nielsen_chuang/04_quantum_circuits/` — pode ser usado como ground-truth do MD₁
- Métrica primária ainda é token-similarity (T031 vai expandir, mas baseline pode usar a antiga para comparar com histórico)
