---
id: T085
titulo: Módulo pdf2md.telemetry — instrumento de telemetria por step
status: research
criado_em: 2026-05-16
fechado_em:
fase: 4
depende_de: []
blocks: [T090]
tags: [telemetry, frente-a, profiling, instrumentation]
kind: pipeline
---

## Contexto

Para construir o roteador profile-aware (T090), precisamos primeiro do
**instrumento** que captura telemetria por step do pipeline: tempo (wall
+ CPU), memória (RSS + Python heap), GPU (VRAM + util%), I/O e threads.

Atualmente cada `_stats.json` reporta `tools.cuda_device` e
`extraction_time_seconds` (agregado, único), mas nenhuma breakdown por
step nem captura de pico de recursos.

Lab e10 implementa versão local em `lab/e10/telemetry.py`; este ticket
**promove** para módulo importável após validação.

## Decisão de arquitetura

Vetores capturados por step (validado via [[arquitetura-instrumento-mapa-roteador]]):

| Vetor | Como (Windows) | Crítico? |
|---|---|---|
| Wall-clock | `time.perf_counter()` | sim |
| CPU time (user+sys) | `psutil.Process().cpu_times()` | sim |
| CPU% médio | sampling em thread (`cpu_percent` interval=0.5s) | sim |
| RSS peak | `psutil.Process().memory_info().rss` sampling | sim |
| Python heap peak | `tracemalloc.get_traced_memory()` | médio |
| GPU VRAM peak | `torch.cuda.max_memory_allocated()` (se torch) ou `nvidia-smi` polling | sim quando GPU |
| GPU% util médio | `nvidia-smi --query-gpu=utilization.gpu` polling | sim quando GPU |
| Disk I/O bytes | `psutil.Process().io_counters()` | médio |
| Threads peak | `psutil.Process().num_threads()` | baixo |

Hardware context capturado uma vez por run:

| Item | Por quê |
|---|---|
| CPU model + cores | normalização cross-hardware |
| RAM total GB | saturação relativa |
| GPU model + VRAM total | comparação cross-hardware |
| Python version + OS | reprodução |

API proposta:

```python
from pdf2md.telemetry import TelemetryRun

with TelemetryRun("e10-fingerprint") as run:
    with run.step("render_pdf_orig"):
        render_pdf_to_images(pdf_orig, out)
    with run.step("md_to_pdf"):
        md_to_pdf(md, out_pdf=...)
    with run.step("compute_triangle_fp"):
        ...
    # auto-save em out/telemetry.json no exit
```

Output `telemetry.json`:

```json
{
  "run_id": "e10-fingerprint-20260516",
  "host": {"cpu": "...", "ram_gb": 32, "gpu": "RTX 3060 12GB", "py": "3.13"},
  "steps": [
    {"name": "render_pdf_orig", "wall_s": 4.81, "cpu_s": 4.65,
     "cpu_pct_mean": 96.0, "rss_peak_mb": 312.5, ...},
    ...
  ],
  "total_wall_s": 47.3
}
```

## Critérios de aceitação

- [ ] Módulo `pdf2md/telemetry.py` exporta `TelemetryRun` (context manager)
      + `step(name)` (nested context manager)
- [ ] Auto-save em `out/telemetry.json` (path configurável)
- [ ] Sampling em thread separada (overhead < 5% do wall-time)
- [ ] Funciona sem GPU (campos GPU = null) — não força dep torch
- [ ] Funciona sem `nvidia-smi` (degrada graceful)
- [ ] Tests cobrindo: smoke run (sem deps externos), peak detection
      simulada (alocar/desalocar buffer), context manager aninhado
- [ ] Integrado em `stats.py` como passo opcional (`compute_stats(...,
      telemetry=True)`)

## Critério de promoção

- e10 valida o padrão na bancada-suja
- Pelo menos 1 ferramenta (marker, ou potrace, ou pix2tex) instrumentada
  para gerar primeiro ponto do mapa de perfis
- Tempo de overhead da própria telemetria < 5% do wall-time

## Não-objetivo

- Profiler estatístico tipo `cProfile` (granularidade de função)
- Energia (joules) — Windows não tem API simples
- Network counters
- Tracing distribuído (over-engineering p/ uso atual)

## Conexão

- Frente A (validação/instrumentação)
- Bloqueia [T090](T090_macro_intent_routing.md) — roteador precisa do mapa que vem dessa instrumentação
- Promovido do lab `lab/e10_pixel_roundtrip_fingerprint/telemetry.py` após validação
- Articula [[arquitetura-instrumento-mapa-roteador]] (memória do projeto)
