---
id: T180
titulo: Reconstrução vetorial de imagens-com-texto (texto + fonte + geometria + brasão residual)
status: research
criado_em: 2026-05-10
fechado_em:
fase: 4
depende_de: [T160]
blocks: []
tags: [conversor, imagens, vetorizacao, reconstrucao, frente-e]
kind: experimento
---

## Contexto

A imagem da logo Cambridge University Press em `corpus/nielsen_chuang/00_front_matter/images/_page_0_Picture_3.png` foi observação inicial ([T137](T137_denoising_jpeg_pre_compressao.md) nível 3): **se soubéssemos a fonte, o texto e a geometria, poderíamos re-renderizar perfeitamente, deixando só o brasão como bitmap pequeno**.

Isso é o **Nível 4 do eixo de representação** ([PHILOSOPHY](../../docs/explanation/philosophy.md)): texto vetorial + brasão residual.

T160 cobre a etapa de extração ("imagem → texto + bitmap residual"); T180 trata a etapa de reconstrução ("dado texto + bitmap residual, render para imagem original").

## Hipótese

Para elementos repetitivos do corpus (logos de editora, headers de página, marcas d'água), a representação Nível 4 é viável e produz:

- 90%+ de redução de bytes (KB-MB → centenas de bytes)
- Qualidade visual perceptualmente equivalente (SSIM ≥ 0.95) ou superior (sem artefatos JPEG)
- Searchability total do texto extraído

## Método (especulativo)

1. **Extração** (delegada a T160):
   - OCR para identificar texto + bbox de cada palavra
   - Detecção de fonte via matching contra Adobe / Google Fonts (ou via Surya layout)
   - Geometria: posição, tamanho, rotação de cada glyph
   - Bitmap residual: pixels não cobertos pelo texto reconstruído (brasão, ornamentos)

2. **Representação canônica**:
   ```yaml
   reconstructed:
     text:
       - content: "CAMBRIDGE UNIVERSITY PRESS"
         font: "Times New Roman"
         size: 12pt
         bbox: [x, y, w, h]
         color: "#000000"
     residual_bitmap:
       path: "logo_residual.png"  # apenas o brasão, sem texto
       bbox: [x, y, w, h]
   ```

3. **Reconstrução para PDF/render**:
   - SVG com `<text>` + `<image>` para o residual
   - HTML/CSS equivalente para o pipeline atual
   - Render → comparar com original via SSIM

## Critério de promoção

- 5 logos / elementos repetitivos do corpus reconstruídos com:
  - SSIM ≥ 0.95 contra original
  - Tamanho final ≤ 10% do original
  - Texto extraído 100% buscável e correto
- Pipeline integrável: gera campo `reconstructed: ...` em `_image_optimization.json`

## Critério de descarte

- Detecção de fonte falha em > 50% dos casos (matching contra catálogo é ruim) — adia indefinidamente
- Reconstrução perde features visuais críticas (kerning, ligature, tracking) que são importantes em logos comerciais

## Não-objetivo

- Reconstruir todas as figuras científicas do corpus (custo > benefício)
- Replicar tipografia LaTeX inteira (problema resolvido por LaTeX nativo)
- Atingir bit-exact equivalence (impossível sem rasterizar com mesmo engine)

## Esforço estimado

~10-15 dias de experimento (T-shirt size **XL**). Cabe na **Frente E** (ambição), não Frente B/C/D.

## Limites éticos

Reconstrução de logos comerciais via re-render do nome **não viola direito autoral** (texto não é protegido), mas o brasão residual mantém-se na forma original (imagem). Documentar essa distinção quando o ticket virar `open/`.

## Conexão

- Frente E da hierarquia (reconstrução vetorial) — pilar
- Depende de T160 (extração)
- Promovido a partir de T137 nível 3 (que era especulativo)
- Habilita parte de T440 (MD como transporte — assets vetoriais são naturalmente compactos)

## Origem da ideia

Observação user-driven 2026-05-08: "se soubéssemos o tipo da letra, o que está escrito e a forma, ficando só o logo sobrando, provavelmente essa logo é um copy paste em que só o brasão é realmente uma imagem".

Formalizado como pilar em 2026-05-10 conforme Frente E do ROADMAP.
