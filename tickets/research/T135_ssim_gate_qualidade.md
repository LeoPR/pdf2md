---
id: T135
titulo: Gate SSIM antes/depois para validar otimizações de imagem
status: research
criado_em: 2026-05-10
fechado_em:
fase: 3
depende_de: [T131]
blocks: []
tags: [conversor, imagens, ssim, qualidade, validacao]
kind: imagens
---

## Contexto

Hoje `optimize_images.py` (T131) escolhe entre PNG paleta e JPEG original baseado em **diferença média de pixel** (threshold 5/255 para `palette_lossy`). Métrica simples mas não captura distorção perceptual — duas imagens com mesmo erro médio podem parecer muito diferentes.

[SSIM (Structural Similarity Index)](https://en.wikipedia.org/wiki/Structural_similarity_index_measure) é métrica de qualidade perceptual padrão. Vale aplicar como gate de qualidade antes de aceitar qualquer otimização.

## Objetivo

Para cada otimização proposta (PNG paleta lossy, SVG via potrace, quantização agressiva), computar SSIM(original, otimizado). Aceitar apenas se SSIM ≥ 0.95.

## Método

1. Adicionar dependência `scikit-image` (tem `skimage.metrics.structural_similarity`)
2. Em `optimize_images.py`: após gerar candidato, render para bitmap (se SVG) e computar SSIM
3. Threshold default 0.95; configurável via flag `--ssim-min`
4. Output: campo `ssim` por imagem em `_image_optimization.json`

## Critérios de aceitação

- [ ] `optimize_images.py --ssim-min 0.95` rejeita otimizações que não passam
- [ ] Re-rodar em N&C: medir quantas das 197 conversões T131 sobrevivem ao gate
- [ ] Documentar imagens rejeitadas (caso houver) em `_image_optimization.md`
- [ ] Tempo overhead: ≤ 0.1s por imagem em CPU

## Critério de promoção

- 0 imagens com SSIM < 0.95 sendo aceitas após implementação
- < 5% de imagens rejeitadas no corpus N&C (validação que T131 já era conservador)

## Não-objetivo

- Trocar a métrica primária (continua sendo size-savings)
- Implementar SSIM customizado (usar a do scikit-image)

## Conexão

- Frente D (otimização de representação)
- Pré-requisito para T132 (potrace SVG) e T134 (pix2tex) — ambos precisam validar qualidade visual antes de promover
- Sub-ticket de [T130](T130_image_optimization.md)
