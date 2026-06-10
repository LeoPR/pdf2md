---
id: T132
titulo: potrace para line art → SVG vectorizado
status: research
criado_em: 2026-05-10
fechado_em:
fase: 3
depende_de: [T131]
blocks: []
tags: [conversor, imagens, svg, potrace, vetorizacao]
kind: experimento
---

## Contexto

T131 (closed) cobre níveis 1-2 da decisão tree de [T130](T130_image_optimization.md) (PNG B&W e PNG paleta lossy). O **nível 3** é vetorizar line art puro como **SVG** via [potrace](http://potrace.sourceforge.net/) — para diagramas binários, ganho adicional de 30-50% sobre PNG paleta + escalabilidade total.

Hipótese de [T130](T130_image_optimization.md): SVG é mais barato que PNG paleta para line art simples e infinitamente escalável.

## Hipótese

Para imagens em N&C cap. 4 (diagramas de circuito quântico, line art puro): vectorização via potrace produz SVG cujo tamanho é < tamanho do PNG paleta correspondente, **e** o resultado renderiza visualmente equivalente (SSIM ≥ 0.95).

## Método

1. Subset de teste: 10 imagens já classificadas como `bw` ou `palette` em `corpus/nielsen_chuang/04_quantum_circuits/images/`
2. Para cada: potrace → SVG → comparar bytes vs PNG atual
3. Render SVG para bitmap → comparar SSIM contra PNG original
4. Decisão: se SVG < PNG E SSIM ≥ 0.95 → promover SVG, atualizar refs no MD

## Critério de promoção

- SVG ≤ 70% do tamanho do PNG paleta correspondente em ≥ 7/10 imagens do subset
- SSIM ≥ 0.95 em todas as 10
- Tempo de vectorização ≤ 2s por imagem em CPU
- Implementação como flag `--vectorize` em `optimize_images.py`

## Critério de descarte

- SVG maior que PNG em > 50% dos casos → vetorização não compensa para nosso corpus
- SSIM < 0.90 em qualquer caso (perda visual perceptível)
- pypotrace tem dependências nativas que conflitam com pillow / pymupdf no venv

## Setup

```powershell
py -m venv Z:\venvs\pdf2md_lab_eXX --prompt eXX
pip install pypotrace pillow scikit-image
```

`pypotrace` precisa de `libpotrace` no sistema (Windows: vem precompilado via wheel; Linux: `apt install libpotrace-dev`).

## Não-objetivo

- Vetorizar imagens com texto (T160 cobre)
- Vetorizar continuous tone (impossível)
- Substituir T131 — é complemento, não troca

## Conexão

- Frente D (otimização de representação)
- Sub-ticket de [T130](T130_image_optimization.md) — nível 3 da decisão tree
- Pode habilitar [T180](../open/T180_reconstrucao_vetorial_imagens.md): SVG limpo facilita reconstrução vetorial textual
