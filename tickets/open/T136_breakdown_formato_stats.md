---
id: T136
titulo: Breakdown por formato de imagem em _stats.md
status: open
criado_em: 2026-05-10
fechado_em:
fase: 3
depende_de: [T131]
blocks: []
tags: [conversor, stats, imagens, breakdown]
kind: imagens
---

## Contexto

[`stats.py`](../../src/stats.py) hoje reporta `images_count` e `images_total_bytes` agregados, sem distinguir formatos. Após T131 (closed), o corpus N&C tem uma mistura de PNG paleta lossy (197) + JPEG (1) — informação invisível no relatório consolidado.

`_image_optimization.md` (gerado por `optimize_images.py`) tem o breakdown, mas é separado. Útil consolidar no `_stats.md` principal para visão única.

## Objetivo

Adicionar tabela em `stats.py` que mostra por formato: count, total bytes, average bytes, % do total.

Exemplo de saída desejada:

```markdown
## Imagens — breakdown por formato

| Formato | Count | Bytes | % bytes |
|---|---:|---:|---:|
| png  | 197 | 2.74 MB | 99.6% |
| jpeg |   1 | 11.3 KB |  0.4% |
```

## Critérios de aceitação

- [ ] `stats.py` atualizado com `image_breakdown_by_format()` helper
- [ ] Render no `_stats.md` em seção "Imagens" (junto com count e total)
- [ ] Campos `images_by_format` em `_stats.json` (machine-readable)
- [ ] Re-gerar `_stats.md` do N&C para confirmar

## Critério de promoção

Trabalho mecânico, baixa complexidade. Promover direto: implementar + re-gerar N&C stats + commit.

## Não-objetivo

- Quebrar por subcategoria (palette vs paleta lossy) — usar campo `kind` de `_image_optimization.json` se quiser detalhe
- Adicionar histograma de tamanhos (overkill para o caso)

## Conexão

- Frente D (otimização de representação) — telemetria
- Sub-ticket de [T130](T130_image_optimization.md)
- Pequeno escopo, ~30 min de trabalho

## Esforço estimado

~30 min — lê `_image_optimization.json` se existir, ou conta extensões direto na pasta.
