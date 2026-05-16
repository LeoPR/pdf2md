---
id: T134
titulo: pix2tex para fórmulas-imagem detectadas
status: research
criado_em: 2026-05-10
fechado_em:
fase: 3
depende_de: [T133]
blocks: []
tags: [conversor, imagens, formula, latex, ocr, pix2tex]
kind: experimento
---

## Contexto

Após [T133](T133_detector_de_formula.md) classificar uma imagem como fórmula, [pix2tex](https://github.com/lukas-blecher/LaTeX-OCR) converte a imagem em LaTeX. Resultado: imagem (KB) substituída por `$$<latex>$$` (bytes), ganho semântico (searchable, editável) **e** ganho de compressão (~100×).

Sub-ticket de [T130](T130_image_optimization.md) — nível 4 (texto LaTeX).

## Hipótese

Para fórmulas tipográficas em livros/papers (Nielsen-Chuang, Preskill, arxiv), pix2tex atinge **CDM ≥ 0.85** ([Character Detection Matching, LITERATURA.md §1.3](../../docs/explanation/literatura.md)) com confidence threshold ≥ 0.85.

Fallback: se confidence < 0.85, manter como imagem.

## Método

1. 20 fórmulas-imagem extraídas do N&C (cap. 4, 5, 8) com GT em LaTeX manual
2. Rodar pix2tex em todas
3. Computar:
   - **CDM** (preferido — render + matching visual; baseline na literatura)
   - **Exact match após canonicalização** (`latex-cleaner` ou regex simples)
   - **Compile-OK rate** (% que compila sem erro em KaTeX)
4. Validar threshold de confidence: para qual valor a precisão atinge 0.95?

## Critério de promoção

- CDM ≥ 0.85 em ≥ 16/20 (80%) das fórmulas
- Compile-OK ≥ 95%
- Tempo ≤ 2s por fórmula em CPU (pix2tex modelo é ~150 MB)
- Threshold escolhido tem precisão 0.95+ (poucos falsos positivos)
- Implementado como flag `--latex-formulas` em `optimize_images.py`

## Critério de descarte

- CDM < 0.70 em ≥ 30% das fórmulas → modelo ruim para nosso domínio
- Compile-OK < 80% → output muito ruidoso para uso prático
- Threshold de confidence não converge (sempre toda fórmula acima ou abaixo)

## Setup

```powershell
py -m venv Z:\venvs\pdf2md_lab_eXX --prompt eXX
pip install pix2tex pillow torch  # ~150 MB modelo + ~3 GB torch CUDA
```

Considerar usar CPU only para validação primeira (mais lento mas evita conflito com venv `marker`).

## Não-objetivo

- Cobrir Feynman diagrams, commutative diagrams, Young tableaux (pix2tex falha em notação rara — fica como imagem)
- Cobrir manuscritos (fora de domínio do pix2tex)

## Conexão

- Frente B (captura textual — fórmula é texto) **e** Frente D (compressão semântica)
- Depende de T133 (detector)
- Generalizado por T160 (OCR semântico de qualquer imagem-com-texto)
- Métrica via [docs/reference/metricas.md](../../docs/reference/metricas.md) M2 (CDM)
