---
id: T133
titulo: Detector de fórmula (heurística + bbox)
status: research
criado_em: 2026-05-10
fechado_em:
fase: 3
depende_de: [T131]
blocks: [T134]
tags: [conversor, imagens, formula, deteccao]
kind: experimento
---

## Contexto

Para que [T134](T134_pix2tex_formulas.md) (pix2tex) funcione, precisa primeiro **detectar quais imagens são fórmulas**. Aplicar pix2tex em todas as imagens é caro (~2s/img em CPU, mais em GPU se modelo carregado) e gera falsos positivos quando a imagem não é fórmula (output: LaTeX sem sentido).

## Hipótese

Heurística de baixo custo (sem ML novo) consegue detectar > 80% das fórmulas-como-imagem com < 10% de falsos positivos em corpus acadêmico:

- Aspect ratio (width/height): fórmulas costumam ser largas (≥ 3:1) ou compactas (1:1 a 2:1) com poucas linhas
- Densidade de pixels não-fundo (após binarização): 5-30%
- Ausência de áreas grandes com cor uniforme (continuous tone)
- Posição na página: fórmulas isoladas geralmente em bloco, não inline

## Método

1. Ground-truth manual: marcar 30 imagens em N&C como "fórmula" / "não-fórmula"
2. Computar features (aspect ratio, density, color count, bbox-position) em todas as 30
3. Treinar regra simples (decision tree de 3-5 nós, ou regras manuais) para classificar
4. Validar em hold-out de 10 imagens

## Critério de promoção

- Precision ≥ 0.80, Recall ≥ 0.80 no hold-out
- Heurística implementada em < 100 linhas de Python (PIL + numpy)
- Tempo < 0.05s por imagem
- Output: campo `is_formula` em `_image_optimization.json` por imagem

## Critério de descarte

- Heurística só consegue Precision < 0.65 ou Recall < 0.65 → trocar por modelo ML simples (LayoutLMv3 ou DocLayout-YOLO)
- Falsos positivos viram ruído sistemático que polui `_stats.md`

## Não-objetivo

- Classificar tipo de fórmula (display vs inline) — só "é fórmula?"
- Localizar fórmulas em texto corrido (Marker já faz)
- Detectar fórmulas dentro de tabelas (caso edge)

## Conexão

- Frente C (captura estrutural)
- Bloqueia T134 (pix2tex)
- Sub-ticket de T130
