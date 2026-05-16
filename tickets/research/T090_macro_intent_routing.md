---
id: T090
titulo: Macro-intent + roteador profile-aware (--rapido/--qualidade/--auto/--indexacao)
status: research
criado_em: 2026-05-16
fechado_em:
fase: 4
depende_de: [T085]
blocks: []
tags: [cli, routing, profile, frente-a, ux]
kind: decisao
---

## Contexto

O `pdf2md convert` macro hoje tem presets hardcoded (`--quick`, `--best`)
com escolhas opacas. Não escala para o caso de uso real: **indexar
milhares de documentos com perfis variados de hardware e demanda**.

A visão articulada (memória [[arquitetura-instrumento-mapa-roteador]]):

> O usuário passa **intent macro**; o sistema escolhe a stack baseado
> em (a) perfis dos algoritmos disponíveis, (b) recursos da máquina
> auto-detectados, (c) características do input (tamanho, tipo de PDF).

Pré-requisito: ter o **mapa** de perfis dos algoritmos — depende de
[T085](T085_telemetry_module.md) instrumentar e de N labs (e09, e10,
e11, ...) gerarem pontos do mapa.

## Decisão de arquitetura

### Macro-intents propostos

| Flag | Significado | Política |
|---|---|---|
| `--rapido` | Min wall-time, qualidade aceitável | marker base, skip optimize/rt, skip multi-iter |
| `--qualidade` | Max qualidade, sem restrição de recursos | marker + pix2tex + potrace + multi-rt |
| `--balanceado` | Default — bom trade-off | marker + optimize + single rt |
| `--auto` | Detecta recursos, escolhe stack cabível | se VRAM>=8GB use pix2tex; se RAM<8GB CPU only; etc. |
| `--indexacao` | Pass 1 rápido + queue pass 2 enriquecer | gera índice imediato + agenda re-process |
| `--low-resource` | Sem GPU, mín RAM | fallback CPU + heurísticas (T420) |

### Política de roteamento (proposta)

```python
def route(intent: str, profile_map: dict, host: HostInfo, doc: DocInfo) -> Pipeline:
    """Retorna lista de steps com configs concretas."""
    candidates = filter_compatible(profile_map, host)  # remove o que não cabe
    if intent == "rapido":
        return select_minimum_time(candidates, doc)
    elif intent == "qualidade":
        return select_maximum_quality(candidates, doc)
    elif intent == "auto":
        return optimize_pareto(candidates, host, doc)  # frente de Pareto qual×tempo
    elif intent == "indexacao":
        return two_pass_pipeline(candidates, host, doc)
    ...
```

### Detecção de recursos

```python
host = HostInfo.detect()  # CPU cores, RAM GB, GPU model + VRAM, presence of torch/marker
# Auto-detect via psutil + torch.cuda + shutil.which("marker_single")
```

### Modelo de perfil por algoritmo

```yaml
algorithm: marker
peer_step: extract
hardware_requirements:
  ram_min_mb: 4096
  gpu_vram_min_mb: 4096  # opcional, fallback CPU é 10x mais lento
  gpu_recommended: true
complexity:
  time: O(pages · model_layers)  # empírico
  memory: O(pages_per_batch · model_size)
quality_baseline:
  N&C cap4 round-trip: 95.09%
  WER-prosa GT mini-corpus: TBD (depende T060)
```

## Critérios de aceitação

- [ ] CLI flags `--rapido`, `--qualidade`, `--auto`, `--balanceado`,
      `--indexacao` mutuamente exclusivos (typer)
- [ ] `HostInfo.detect()` reportando recursos disponíveis (`pdf2md doctor`
      já faz parte)
- [ ] `pdf2md/routing.py` com função `route(intent, profile_map, host, doc)`
- [ ] Profile map carregado de `docs/profiles/*.yaml` ou
      `pdf2md/_profiles.py` (decisão pendente — YAML é mais editável,
      Python é mais validado)
- [ ] Pelo menos 3 perfis no map (marker, potrace, pix2tex) antes
      do roteador fazer sentido em produção
- [ ] `--indexacao` retorna 2 pipelines (pass 1 = imediato, pass 2 =
      offline). Como executar pass 2 fica fora do escopo (cron, fila, etc.)
- [ ] Tests cobrindo: route returns expected pipeline for each intent;
      auto-detect com mock de host info

## Critério de promoção

- 3+ perfis no map com dados reais (e09, e10, e11, ...)
- `--rapido` 2x+ mais rápido que `--qualidade` no mesmo doc (mensurável)
- `--auto` adapta corretamente entre máquina com GPU vs sem GPU (testado)
- `--indexacao` valida em corpus pequeno (10 docs) com pass 2 reprocessando
  os que tiveram round-trip baixo

## Não-objetivo

- Aprendizado de máquina para roteamento (over-engineering inicial)
- Profiles cross-hardware automáticos via fitting de curva (futuro, T091)
- Pricing/billing awareness (não-aplicável)
- Distributed execution (one-machine inicialmente)

## Conexão

- Frente A (validação) + UX
- Depende de [T085](T085_telemetry_module.md) — sem instrumento, sem mapa
- Depende de N experimentos para popular mapa (e09 já em progresso, e10 próximo)
- Articula [[arquitetura-instrumento-mapa-roteador]]
- Substitui hardcode atual de `--quick`/`--best` em cli.py convert
