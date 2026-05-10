---
id: T071
titulo: Heurística de detecção de alucinação via bloat_ratio em stats.py
status: closed
criado_em: 2026-05-10
fechado_em: 2026-05-10
fase: 5
depende_de: [T031]
blocks: []
tags: [stats, validacao, bloat, alucinacao, heuristica]
kind: pipeline
---

## Contexto

O experimento [`lab/e03_atkins_wilson_scan/`](../../lab/e03_atkins_wilson_scan/) descobriu um **padrão de degradação não-óbvio** do pipeline: quando o MD₁ extraído pelo marker é esparso (pouco conteúdo por página), o re-OCR do PDF intermediário **alucina** muito mais conteúdo no MD₂, resultando em round-trip catastrófico.

Casos confirmados:

| caso | MD₁ tokens | MD₂ tokens | bloat | rt% | categoria |
|---|---:|---:|---:|---:|---|
| Wilson 1800 (e03) | 2,748 | 21,177 | **7.7×** | **13.62%** | scan_image_only manuscrita |
| IBM lesson 1 (T450) | 4,629 | 15,637 | **3.4×** | **28.9%** | slide PPTX com math-imagem |
| (todos os outros casos do projeto) | _ | _ | ~1.0× | 89-99% | normal |

**Hipótese**: o `bloat_ratio = tokens(MD₂) / tokens(MD₁)` é um **sinal forte de alucinação**. Vale capturar automaticamente no `_stats.md` em vez de descobrir caso a caso.

## Objetivo

Adicionar campo `bloat_ratio` no `_stats.json` e flag visual no `_stats.md`, com heurística de classificação em 3 níveis.

## Heurística adotada

```python
strong_alucinacao = (
    bloat > 3.0
    or (bloat > 2.0 and density < 200)
)
```

Onde `density = tokens(MD₁) / pages` (do PDF original).

- **🚨 PADRÃO DE ALUCINAÇÃO**: bloat > 3.0 OU (bloat > 2.0 + density < 200 tokens/página)
- **⚠️ anormal**: bloat > 1.5 (mas não dispara o forte)
- **✓**: caso normal (bloat ≤ 1.5)

## Critérios de aceitação

- [x] `roundtrip_metrics()` retorna `bloat_ratio`
- [x] `render_md()` mostra bloat no Resumo executivo + seção Round-trip com flag visual
- [x] Quando flag forte dispara, adiciona bloco quotado explicando o padrão
- [x] Smoke test confirma 2/2 casos problemáticos pegos (Wilson 7.71×, IBM 3.38×) sem falsos positivos em 5/5 casos normais

## Smoke test (validação)

```
caso                bloat    dens   flag                rt%
Wilson 1800          7.71    91.6   [FORTE] alucinação  13.62  ✓
IBM lesson 1         3.38   289.3   [FORTE] alucinação  28.90  ✓ (via bloat > 3.0)
Atkins (e03)         1.05   238.6   [OK]    normal      92.11  ✓
OCW slides           0.97    45.3   [OK]    normal      89.84  ✓ (densidade baixa mas sem bloat)
IRS f1040            0.81  1427.5   [OK]    normal      46.16  ✓ (rt baixo, mas é AcroForm, não alucinação)
CDC MMWR             1.00  3137.0   [OK]    normal      95.64  ✓
arxiv 2106           1.00   280.9   [OK]    normal      98.58  ✓
```

**Captura 2/2 alucinações conhecidas, zero falsos positivos em 5/5 normais.**

## Implementação

`src/stats.py`:
- `roundtrip_metrics()`: adicionado campo `bloat_ratio` (float ou None se MD₁ vazio)
- `render_md()` no Resumo executivo: linha "Bloat ratio MD₂/MD₁" quando há roundtrip
- `render_md()` na seção Round-trip: linha "Bloat ratio" + bloco quotado explicativo se flag forte dispara

## Não-objetivos

- **Não substituir** round-trip similarity como métrica primária; é complementar
- **Não detectar** casos limítrofes onde bloat moderado (1.5-2.0) com densidade alta é problema real — mais dados necessários
- **Não corrigir** o problema (que é da Camada 3 — reconstrução); só sinalizar para análise

## Conexão com outros tickets

- Origem: `lab/e03_atkins_wilson_scan/` (e194ad5)
- Fecha implicitamente uma sub-investigação do [T450](T450_investigar_ibm_lesson_1_round_trip_critico.md): IBM lesson 1 agora tem categorização sistêmica, não é mais "outlier".
- Complementa [`docs/METRICS.md`](../../docs/METRICS.md) — bloat_ratio é métrica de detecção, não de qualidade.

## Esforço final

~30 min: implementação + smoke test + ticket. Trabalho pequeno com retorno alto.
