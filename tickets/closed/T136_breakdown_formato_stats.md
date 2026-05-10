---
id: T136
titulo: Breakdown por formato de imagem em _stats.md
status: closed
criado_em: 2026-05-10
fechado_em: 2026-05-10
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

- [x] `stats.py` atualizado — agregação `images_by_format` e `images_bytes_by_format` em `folder_metrics()`
- [x] Render no `_stats.md` em seção `### Breakdown por formato` (após o resumo de imagens)
- [x] Campos `images_by_format` e `images_bytes_by_format` em `_stats.json`
- [x] Validado em 3 PDFs do experimento [`lab/e01_baseline_corpus_categorias/`](../../lab/e01_baseline_corpus_categorias/) — todos têm a seção, todos mostram 100% JPEG (output default do marker)

## Resultado

Implementação em [`src/stats.py`](../../src/stats.py): ~25 linhas adicionadas.

- **Agregação de bytes por formato**: loop secundário em `folder_metrics()` (linhas ~222-232) lê filesystem por chapter para obter bytes por formato com precisão. Não confia em `avg_bytes * count` que seria incorreto.
- **Render**: substitui a lista bullet anterior por tabela markdown com 3 colunas (Count, Bytes, % bytes). Mantém fallback para o caso de `totals` não ter `images_by_format`.

Validação via [`lab/e01_baseline_corpus_categorias/_stats_*.md`](../../lab/e01_baseline_corpus_categorias/) — todos 3 docs mostram a tabela. Output típico:

```
### Breakdown por formato

| Formato | Count | Bytes | % bytes |
|---|---:|---:|---:|
| `jpeg` | 6 | 389.5 KB | 100.0% |
```

100% JPEG é esperado — marker output default. Esse breakdown vai virar útil quando T131 for aplicado (mistura png+jpeg) ou quando T132 (potrace SVG) adicionar svg.

## Critério de promoção (cumprido)

Promovido direto — trabalho mecânico, baixo risco, validado em 3 PDFs reais.

## Não-objetivo

- Quebrar por subcategoria (palette vs paleta lossy) — usar campo `kind` de `_image_optimization.json` se quiser detalhe
- Adicionar histograma de tamanhos (overkill para o caso)

## Conexão

- Frente D (otimização de representação) — telemetria
- Sub-ticket de [T130](T130_image_optimization.md)
- Pequeno escopo, ~30 min de trabalho

## Esforço estimado

~30 min — lê `_image_optimization.json` se existir, ou conta extensões direto na pasta.
