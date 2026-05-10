---
id: T106
titulo: Estudo extra de extração — testar settings alternativos
status: closed
criado_em: 2026-05-07
fechado_em: 2026-05-07
fase: 1
depende_de: [T101]
blocks: []
tags: [conversor, marker, qualidade, estudo]
kind: experimento
---

## Contexto
Baseline atual (T104): 95.09% similaridade no round-trip do cap. 4. Material já está em qualidade boa. Mas vale verificar se ajustes finos no marker melhoram algo perceptível.

## Objetivo
Re-extrair o cap. 4 (45 páginas, math-heavy) com `--highres_image_dpi 300` (vs default 192) e comparar métricas.

## Critérios de aceitação
- [x] Extração alternativa rodada
- [x] Métricas comparadas com baseline
- [x] Conclusão registrada

## Resultado

Cap. 4 (Quantum circuits, ~45 páginas), DPI 300 vs 192:

| Métrica | DPI 192 | DPI 300 | Δ |
|---|---|---|---|
| Linhas | 1105 | 1097 | -0.7% |
| Fórmulas display ($$..$$) | 127 | 127 | 0% |
| Headers | 30 | 31 | +3% |
| Imagens | 25 | 25 | 0% |
| Tamanho MD | 125 KB (estimado) | 124 KB | ~0% |

## Conclusão

**Ganho marginal (dentro do ruído).** O DPI maior aumentaria o tempo de extração de
~1h09min para ~2h+ no livro inteiro, sem retorno perceptível em qualidade de
detecção de fórmulas, headers ou imagens.

**Não vale aplicar ao livro inteiro.** Baseline com DPI 192 fica como configuração
canônica.

## Outros settings testáveis (não nesta sessão)
- `--use_llm` (precisa API key — Gemini/OpenAI; promete melhorar tabelas e equações ambíguas)
- `--strip_existing_ocr` (forçar marker a re-OCR mesmo se PDF já tem texto)
- Outras ferramentas comparáveis: Nougat (Meta), MinerU
