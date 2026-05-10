---
id: T137
titulo: Restauração de artefatos JPEG antes da compressão (sub-ticket de T130)
status: research
criado_em: 2026-05-08
fechado_em:
fase: 4
depende_de: [T130, T131]
blocks: []
tags: [conversor, imagens, otimizacao, denoising, fase4, research]
kind: experimento
---

## Contexto

Observação do usuário (2026-05-08): a logo da Cambridge University Press
em [`00_front_matter/images/_page_0_Picture_3.png`](../../pesquisa_geral/livros/Quantum_Computation_and_Quantum_Information/00_front_matter/images/_page_0_Picture_3.png)
mostra **pixels dispersos pretos** no fundo branco ao redor das letras —
clássicos artefatos de **JPEG ringing/mosquito noise**.

A imagem original (no livro impresso) é bicromática (preto + branco). O
PDF embutiu uma versão **JPEG-comprimida** dela, e marker apenas extraiu
o JPEG como está. T131 quantizou para 16 cores, mas os pixels dispersos
permanecem porque agora estão na paleta.

Se removêssemos os artefatos antes de comprimir, a imagem viraria
praticamente B&W puro (≤2-3 cores) e:
- PNG 1-bit ficaria muito menor
- Eventualmente vetorização SVG (T132) ficaria viável
- Qualidade visual seria **melhor** que o estado atual (mais limpo)

## Hipótese central

PDFs raster-comprimidos por JPEG carregam ruído de codificação que se
propaga pelo pipeline. Limpar o ruído antes da compressão dá:
- **economia adicional** (10-30% sobre o ganho atual de T131)
- **qualidade visual melhor** (não pior)
- **viabiliza vetorização** para line art que hoje cai em `palette_lossy`

## Técnicas a investigar

### Nível 1 — Filtros clássicos (sem ML)

| Técnica | Lib | Quando aplica | Custo |
|---|---|---|---|
| **Median filter** | `PIL.ImageFilter.MedianFilter` | Mosquito noise pequeno | Trivial |
| **Bilateral filter** | `cv2.bilateralFilter` | Suaviza áreas planas, preserva bordas | Médio (precisa cv2) |
| **Total variation denoising** | `scikit-image.restoration.denoise_tv_chambolle` | Imagens piecewise-constant (line art) | Médio |
| **Non-local means** | `cv2.fastNlMeansDenoising` | Generalista, lento | Médio |
| **Otsu binarization** | `cv2.threshold + THRESH_OTSU` | Documento B&W puro | Trivial |
| **Sauvola binarization** | `scikit-image.filters.threshold_sauvola` | Documento com iluminação variável | Trivial |

Para o caso da logo Cambridge: um Otsu/Sauvola já resolveria — bicromática
clara e iluminação uniforme.

### Nível 2 — JPEG artifact removal específico

| Técnica | Disponibilidade |
|---|---|
| **ARCNN** (Artifacts Reduction CNN, Dong et al. 2015) | ~10 MB modelo, treinado para JPEG |
| **DnCNN** (Zhang et al. 2017) | Generalista, várias versões |
| **FFDNet** (Zhang et al. 2018) | Aceita nível de ruído como input |
| **SwinIR** (2021) | State-of-the-art |
| **Real-ESRGAN** | Generalista incluindo JPEG, modelo ~50 MB |

Tradeoff: precisa GPU para tempo viável, modelos grandes.

### Nível 3 — Reconstrução semântica (especulativo)

Para casos como a logo Cambridge, em teoria poderia:
1. **Detectar partes textuais** via OCR (Tesseract → "CAMBRIDGE UNIVERSITY PRESS")
2. **Identificar a fonte** via análise de glyph (matching contra Adobe/Google Fonts)
3. **Re-renderizar o texto** vetorialmente
4. **Manter só a parte não-textual** (brasão) como bitmap pequeno

Resultado: ~5-10 KB de texto vetorial + brasão raster pequeno, vs
JPEG/PNG de KB-MB. Mas é trabalho complexo e nicho — só vale para
elementos repetitivos como logos de editora que aparecem em muitos
livros.

> **Atualização 2026-05-10**: este Nível 3 foi **promovido a ticket
> próprio [T180](T180_reconstrucao_vetorial_imagens.md)** (Frente E
> da hierarquia, [PHILOSOPHY eixo de representação](../../docs/PHILOSOPHY.md#eixo-de-representação)
> Nível 4). T137 mantém o foco em **denoising** (níveis 1-2 — filtros
> clássicos e ML JPEG-specific). A reconstrução vetorial é tratada
> em T180.

## Plano de prototipagem (quando ativar)

1. **Sample**: pegar 5-10 imagens problemáticas representativas
   - Logo Cambridge ([referência exata acima](../../pesquisa_geral/livros/Quantum_Computation_and_Quantum_Information/00_front_matter/images/_page_0_Picture_3.png))
   - Diagramas de circuito quântico (cap. 4)
   - Texto puro com artefatos
   - Fórmulas-como-imagem (slides PPTX)

2. **Baseline**: tamanho atual após T131 (PNG paleta lossy)

3. **Testar nível 1** em sequência:
   - Median (3x3) → PIL quantize → comparar tamanho + visual
   - Bilateral → PNG → comparar
   - Otsu binarize → PNG 1-bit → comparar (deve ser o melhor para logos B&W)

4. **Métrica de qualidade**:
   - Tamanho final (bytes)
   - SSIM vs original (quanto a "limpeza" preservou conteúdo)
   - Inspeção visual lado a lado (10 amostras)

5. **Decidir promoção**:
   - Se nível 1 dá ≥20% economia adicional preservando SSIM > 0.95: virar T138 `open`
   - Se só nível 2 dá esse ganho: virar T139 `research` para integrar ML
   - Se ganho é marginal: documentar e arquivar

## Limites e ressalvas

- **Risco de over-cleaning**: filtros agressivos apagam detalhes finos de
  fórmulas, subscripts pequenos, símbolos delicados. Otsu falha em
  diagramas com gradiente intencional.
- **Cada técnica é case-dependent**: logo bicromática ≠ diagrama de
  circuito ≠ heatmap. Pipeline ideal é classificar antes e escolher
  filtro por classe.
- **Mat. JPEG-OCR (T134/pix2tex)**: aplicar denoising agressivo antes
  do OCR pode estragar o reconhecimento de fórmulas. Ordem importa.

## Conexão com outros tickets

- **T130** — meta-ticket; este aprofunda o nível 3 (otimização intermediária)
- **T131** — closed; PNG paleta lossy. Este é o passo seguinte natural.
- **T132** — potrace SVG; viabilizado pelo denoising para line art
- **T134** — pix2tex; sequência ordenada importa (denoising primeiro)
- **T410** — alt tools; algumas (MinerU) podem já fazer denoising interno

## Quando promover para `open/`

- Quando T132 (potrace) ficar pronto e ainda houver imagens onde
  vetorização não vai bem por causa de ruído JPEG
- Quando alguém quiser reduzir o tamanho dos `images/` por restrição
  externa (push para repo, share via web)
- Quando aparecer uma case com logo/figura repetitiva crítica que
  valha o esforço de restauração semântica (nível 3)

## Origem

Observação user-driven 2026-05-08, exemplo concreto registrado para
não perder o contexto:

> "se olhar a imagem da logo da universidade de cambridge ela parece
> que era um jpg comprimido no pdf original, o que gerou aqueles
> artefatos de pixeis em torno das letras. (...) os pontos dispersos
> parecem mais fáceis de apagar."

Ideia de longo prazo: "as partes das letras poderiam ser reconstruídas
se soubéssemos o tipo da letra, o que está escrito e a forma". Registrada
como nível 3 acima — provocação válida mas distante de implementação.
