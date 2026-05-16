---
id: T070
titulo: Pixel-roundtrip (validador visual L0.5) com triângulo macro/médio/micro
status: research
criado_em: 2026-05-15
fechado_em:
fase: 4
depende_de: []
blocks: [T072]
tags: [conversor, roundtrip, ssim, validacao, frente-a]
kind: experimento
---

## Contexto

Round-trip atual ([T050](../closed/T050_baseline_marker_reproduzivel.md))
mede similaridade só no eixo **texto**: `compare(MD₁, MD₂)` via
`SequenceMatcher` em tokens. Ignora completamente:

- Imagens (passam como blob opaco no MD)
- Layout, posicionamento, kerning
- Fórmulas que falham silenciosamente no KaTeX (viram pixel quando o
  rendering falha mas o `$..$` permanece "válido" como texto)

A formulação de [PHILOSOPHY §"Validação por fechamento recursivo"](../../docs/PHILOSOPHY.md#validação-por-fechamento-recursivo-de-ciclos)
nomeia esse nível como **L0.5** (documento visual). Falta instrumentar.

Assimetria importante: `PDF → imagem` é **operação determinística**
(ISO 32000, ferramentas maduras como PyMuPDF/Poppler/Chrome PDFium).
Diferente de `PDF → MD` que é ill-posed. Isso torna o pivot visual
**mais confiável** que o textual — o erro fica isolado na cadeia
`MD → PDF₁` (reconstrutor).

## Hipótese

Métrica visual decomposta em **triângulo macro / médio / micro**
(definido em [PHILOSOPHY §"Triângulo de métricas"](../../docs/PHILOSOPHY.md#triângulo-de-métricas-macro--médio--micro))
**discrimina** erro de extração vs erro de reconstrução:

- Macro cai, médio cai, micro **OK** → erro de **reconstrução** (info
  está no MD; reconstrutor não consegue layout fiel)
- Macro cai, médio OK, micro cai → erro de **extração local** (estrutura
  preservada, conteúdo dentro de bbox corrompeu)
- Macro cai, médio cai, micro cai → erro **profundo de extração**

Uma métrica visual única não é conclusiva. O triângulo é.

## Método

1. **Lab inicial** `lab/eXX_pixel_roundtrip/`:
   - Render `PDF₀ → img_pdf₀_p[0..N]` via PyMuPDF @ 150dpi
   - Pipeline atual: `PDF₀ → MD₁ → PDF₁` (já existe)
   - Render `PDF₁ → img_pdf₁_p[0..N]` mesma config
   - Aplicar triângulo em cada página

2. **Macro**: `scikit-image.metrics.structural_similarity(img_0, img_1, multichannel=True)`
   - Output: 1 número por página

3. **Médio**: bbox alignment estilo DocLayNet
   - Extrair bboxes de elementos em `img_0` e `img_1` via PyMuPDF (texto/imagem/path)
   - Computar IoU agregado dos bbox sets
   - Output: 1 número por página + lista de bboxes não-alinhados

4. **Micro**: WER por bbox-de-texto
   - Para cada bbox de texto correspondente, OCR independente (Tesseract ou Surya) ou texto-extract direto via PyMuPDF
   - WER entre os textos pareados
   - Output: 1 WER por bbox + mediana agregada por página

5. **Corpus inicial**: cap 4 N&C (49 pgs, denso de math) + arxiv 1706 + CDC MMWR

6. **Output**: módulo `pdf2md/pixel_roundtrip.py` + `pdf2md rt-pixel` no CLI

## Critérios de aceitação

- [ ] Triângulo computado em cap 4 N&C com tempo total < 5min
- [ ] Discrimina os 3 modos de erro em casos sintéticos (corromper MD intencionalmente)
- [ ] Casos reais: identifica pelo menos 1 erro de reconstrução (macro/médio cai, micro OK) no N&C
- [ ] Output JSON parseável para integração futura com `_stats.json`
- [ ] Tests cobrindo: SSIM em imagens iguais (=1.0), em imagens muito diferentes (~0)

## Critério de promoção

- Triângulo aplicado em ≥ 5 docs do corpus
- Pelo menos 1 categoria de erro identificada que round-trip textual missing
- Decisão sobre integrar como métrica primária (atualizar METRICS.md) ou secundária

## Não-objetivo

- Métrica visual global única (frágil — pixel diff puro)
- Substituir round-trip textual (complementa, não substitui)
- Render PDF em ferramentas múltiplas — fixar PyMuPDF como padrão
- Implementar OCR próprio — usar PyMuPDF text-extract direto onde possível

## Conexão

- Frente A (validação)
- Pré-requisito de [T072](T072_calibracao_reconstrutor.md) — calibração precisa do pixel-roundtrip rodando
- Complementa [T050](../closed/T050_baseline_marker_reproduzivel.md) (textual)
- Sub-mecanismo de [T402](T402_pipeline_fractal_recursivo.md) (meta)
- Vincula a [PHILOSOPHY §"Validação por fechamento"](../../docs/PHILOSOPHY.md#validação-por-fechamento-recursivo-de-ciclos) e §"Triângulo"
