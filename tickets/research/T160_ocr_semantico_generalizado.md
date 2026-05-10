---
id: T160
titulo: OCR semântico generalizado de imagens-com-texto
status: research
criado_em: 2026-05-10
fechado_em:
fase: 4
depende_de: [T133, T134]
blocks: [T180]
tags: [conversor, imagens, ocr, semantico, frente-b]
kind: experimento
---

## Contexto

[T134](T134_pix2tex_formulas.md) trata especificamente fórmulas-imagem → LaTeX. [T137](T137_denoising_jpeg_pre_compressao.md) nível 3 trata logos com texto + brasão. Mas a operação subjacente é a mesma: **identificar texto em uma imagem, OCR-izar, decidir se substitui a imagem por texto vetorial ou texto semântico**.

Generalização registra esse princípio como núcleo da **Frente B (captura textual)** — máximo de texto, incluindo o que está dentro de imagens.

## Hipótese

Pipeline unificado de detecção + OCR + decisão de representação cobre múltiplos casos com mesma lógica:

| Caso | Detecção | OCR | Saída |
|---|---|---|---|
| Fórmula tipográfica | T133 (heurística) | pix2tex | `$$LaTeX$$` (Nível 5) |
| Logo de editora | classificador "tem texto?" | tesseract / Surya | texto + fonte + bitmap residual (Nível 4) |
| Caption dentro de figura | OCR na bbox da caption | tesseract | parte da caption do markdown |
| Texto em diagrama | OCR de regiões | tesseract / Surya | overlay textual no SVG (futuro) |

## Método

1. Componente A — **classificador "tem texto?"**: heurística leve (densidade + aspect ratio + entropia local) para evitar OCR-izar fotos
2. Componente B — **OCR genérico**: tesseract (CPU) ou Surya (GPU, já usado pelo Marker)
3. Componente C — **decisão de representação** baseada em confidence + tamanho:
   - LaTeX se reconhecedor matemático sucedeu (T134)
   - Texto + fonte + brasão se logo (T180)
   - Texto + bitmap se caption/diagrama
   - Mantém imagem se confidence < 0.7

## Critério de promoção

- Pipeline unificado em `extract_text_from_image.py` (novo) que classifica + OCR-iza + decide
- Em corpus de teste de 30 imagens (10 fórmulas, 10 logos, 10 outras): precisão ≥ 0.85 do classificador "tem texto?"
- Substituições efetivas em ≥ 15/30 com SSIM ou compile-OK validado
- Integrado em `optimize_images.py` como flag `--semantic-ocr`

## Critério de descarte

- Tesseract / Surya falham em > 50% dos casos no nosso corpus (acadêmico, math-heavy) — manter T134 isolado é suficiente
- Falsos positivos (OCR-izar imagens de continuous tone) se torna ruído

## Não-objetivo

- Substituir o OCR interno do Marker (Marker já faz texto-em-imagem dentro de figuras)
- Reconstruir tipografia exata (T180 trata)

## Conexão

- Frente B (captura textual) — núcleo desta frente
- Generaliza T134 (pix2tex) e T137 nível 3 (logos)
- Habilita T180 (reconstrução vetorial)

## Esforço estimado

~5-7 dias de experimento (T-shirt size **L**).

## Origem da ideia

Discussão 2026-05-10 sobre hierarquia de prioridades: usuário enfatizou "máximo de texto em primeiro lugar, mesmo que seja texto de imagens de alguma forma inicial (tipo OCR)". Esta generalização operacionaliza a ideia.
