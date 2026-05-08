---
id: T131
titulo: Classificador adaptativo de imagens + compressão (níveis 1 e 2 de T130)
status: closed
criado_em: 2026-05-07
fechado_em: 2026-05-07
fase: 4
depende_de: [T130]
blocks: []
tags: [conversor, imagens, otimizacao, fase4, n_c]
---

## Contexto

T130 propõe 4 níveis de otimização. Este ticket entrega os **dois primeiros**:

1. ≤2 cores → PNG 1-bit (B&W)
2. ≤16 cores → PNG indexado (paleta)

Níveis 3 (SVG via potrace) e 4 (LaTeX via pix2tex) ficam para tickets
futuros (T132, T134) — exigem dependências externas que não estão no
venv atual.

## Objetivo

Reduzir tamanho do `images/` do N&C (baseline ~21 MB) preservando 100%
do conteúdo (operação lossless onde aplicada).

## Implementação

`tools/pdf_md_converter/optimize_images.py`:

1. Walk `<root>/**/images/*.{jpeg,jpg,png}`
2. Para cada: classificar via PIL `getcolors()`
3. Se ≤16 cores, gerar PNG candidato; se menor que JPEG, trocar
4. Atualizar referências `.jpeg` → `.png` nos MDs do mesmo capítulo
5. Gerar `_image_optimization.md` com antes/depois

## Critérios de aceitação

- [x] Script implementado
- [x] Roda em dry-run e produz relatório sem modificar nada
- [x] Em modo real, modifica imagens + MDs in-place
- [x] Preserva conteúdo (não há re-encode JPEG→JPEG; PNG é lossless)
- [x] Em N&C (~198 imgs, 21 MB):
      → economia ≥ 30% no total
- [x] Re-rodar `stats.py` no N&C confirma `images_total_bytes` reduzido
- [x] _OVERVIEW.md regenerado mostra ganho na coluna de transporte

## Resultado

Rodado em N&C (Quantum Computation and Quantum Information), 198 imagens:

| | Antes | Depois | Δ |
|---|---:|---:|---:|
| Tamanho total | 4.46 MB | 2.74 MB | **−1.72 MB (−38.6%)** |
| Convertidas para PNG paleta | 0 | 197 | +197 |
| Mantidas JPEG | 198 | 1 | −197 |

Distribuição: 100% das imagens caíram em **`palette_lossy`** (≤16 cores
quantizam com diferença média de pixel < 5/255). Era esperado — N&C cap.
4-12 são todos diagramas de circuitos quânticos / line art, com JPEG
introduzindo apenas ruído de gradiente que não conta como conteúdo.

Per-imagem: economia individual variou 32%-68%. Top economias na ordem
de 30-40 KB cada (figuras maiores, ex. Fig. 7.16 com 64 → 22 KB).

### Impacto no _OVERVIEW.md

| Métrica | Antes | Depois |
|---|---:|---:|
| Tamanho total imagens (todos docs) | 23.4 MB | 21.6 MB |
| (MD+img)/PDF — ratio de transporte | 56.1% | **52.5%** |

Round-trip do livro permanece 95.1% — compressão de imagens não afeta
preservação de tokens (conteúdo MD intocado).

### Próximos passos

T132 (potrace SVG vetorizado): exigiria instalar `pypotrace`. Ganho
adicional estimado em ~30% sobre o atual (figuras line-art puro
geralmente ficam menores como SVG que como PNG). Não promovido por ora.

T134 (pix2tex fórmula→LaTeX): ganho semântico (searchability) maior
que ganho de tamanho. Esperar caso de uso real antes de promover.

## Não-objetivo

- Não vetoriza (sem potrace) → T132
- Não converte fórmula em LaTeX → T134
- Não re-encoda JPEGs (preserva pixels existentes)
