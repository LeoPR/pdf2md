# Camada 2 — Otimização de representação

*Imagens raw → representação mais semântica que não viola a 1ª prioridade (conteúdo). Ver [`../ARQUITETURA.md`](../ARQUITETURA.md) para o contexto e [`../PHILOSOPHY.md`](../philosophy.md#eixo-de-representação) para os níveis de representação.*

---

## Diagrama (decisão tree)

```
                            cada imagem
                                 │
                                 ▼
                  ┌──── PIL: count_colors ────┐
                  │                           │
              ≤ 2 cores             > 2 cores  > 16 cores
                  │                  ≤ 16            │
                  ▼                    │             ▼
            ┌──────────┐               ▼      ┌──────────────┐
            │ PNG 1-bit│         ┌──────────┐ │ tenta palette│
            │  (B&W)   │         │PNG paleta│ │ lossy (16c)  │
            └─────┬────┘         │  (4-16c) │ │ + diff<5/255 │
                  │              └─────┬────┘ └───┬──────────┘
                  │                    │          │
                  ▼                    ▼          │
            compare size vs JPEG original ◀───────┘
                              │
                  ┌───────────┴───────────┐
                  │                       │
              menor?                    maior?
                  │                       │
                  ▼                       ▼
           ┌──────────┐            ┌──────────┐
           │ trocar   │            │  manter  │
           │ ext em MD│            │  JPEG    │
           └──────────┘            └──────────┘

FUTURO: T132 (potrace SVG) · T134 (pix2tex LaTeX) · T180 (reconstrução vetorial)
        T135 (SSIM gate antes de aceitar) · T137 (denoise antes de classificar)
```

---

## Ferramentas

### Em uso (estado atual — T131 closed)

| Ferramenta | Papel | Implementação |
|---|---|---|
| **PIL (Pillow)** | classificação por cores únicas; PNG paleta | `optimize_images.py` |
| **PIL `Image.Quantize`** | quantização para 16 cores (palette lossy) | `optimize_images.py` |
| **PIL `ImageChops + ImageStat`** | medir diferença média de pixel (gate < 5/255) | `optimize_images.py` |

Tier de classificação:

| Tier | Critério | Saída | Resultado em N&C |
|---|---|---|---|
| `bw` | ≤ 2 cores | PNG 1-bit | 0 / 198 |
| `palette` | ≤ 16 cores únicas | PNG paleta indexada | 0 / 198 |
| `palette_lossy` | > 16 mas quantiza com diff < 5/255 | PNG paleta 16-color | **197 / 198** |
| `continuous` | quantização degrada visualmente | JPEG mantido | 1 / 198 |

**Resultado T131 (closed)**: 197 das 198 imagens do N&C viram PNG paleta. **−38.6% no tamanho total** (4.46 MB → 2.74 MB).

### Em uso (T136 closed)

`stats.py` agora reporta breakdown por formato em `_stats.md`:

```markdown
### Breakdown por formato

| Formato | Count | Bytes | % bytes |
|---|---:|---:|---:|
| `png`  | 197 | 2.74 MB | 99.6% |
| `jpeg` |   1 | 11.3 KB |  0.4% |
```

Validado pelo experimento `lab/e01_baseline_corpus_categorias` (3 PDFs, 100% JPEG sem T131 aplicado).

### Futuro

| Ticket | Ferramenta | Papel | Nível alvo |
|---|---|---|---|
| **T132** | potrace | line art bitmap → SVG vetor | 3 |
| **T133** | heurística (aspect ratio + density + bbox) | detector de fórmula-imagem | (pré-condição para T134) |
| **T134** | pix2tex / LaTeX-OCR | fórmula-imagem → LaTeX | 5 |
| **T135** | scikit-image SSIM | gate de qualidade antes de aceitar otimização | (validador) |
| **T137** | filtros (median, bilateral, Otsu) + ARCNN/DnCNN | denoise JPEG **antes** da classificação | (pré-condição) |
| **T180** | OCR + font matching + render | reconstrução vetorial (texto+fonte+brasão) | 4 |

---

## Decisões registradas

1. **Por que tier `palette_lossy`?** JPEG anti-aliasing introduz dezenas de cores únicas mesmo em line art bicromático. Sem `palette_lossy`, 0/198 imagens em N&C virariam PNG paleta. Com o tier, 197/198 viram. Tradeoff: pequena perda visual (diff < 5/255 médio).

2. **Por que não re-encodar JPEG → JPEG?** Lossy duas vezes acumula artefatos. Se já é JPEG e não cabe em paleta, mantemos. T137 cobre o caso "JPEG ruim → limpar artefatos antes de classificar".

3. **Por que threshold 5/255?** Empírico — diff médio menor que isso é imperceptível para o usuário em line art bicromático. T135 (SSIM gate) vai validar mais formalmente com métrica perceptual.

4. **Por que MD ref update?** Após trocar `_page_5_Figure_3.jpeg` → `_page_5_Figure_3.png`, o MD precisa apontar para o novo arquivo. `optimize_images.py` faz a substituição via regex `IMG_RE`.

5. **Por que potrace (T132) é "futuro"?** Vale só se SVG < PNG paleta em ≥ 70% dos casos do nosso corpus. Hipótese ainda não testada. Custo: instalar `pypotrace` que tem dependências nativas.

---

## Inputs e outputs

### Input

`<corpus>/<chapter>/images/*.{jpeg,png}` extraídas pela Camada 1.

### Output

- Imagens otimizadas **in-place** (substituem as originais)
- `<root>/_image_optimization.{md,json}` — relatório com tabela antes/depois, top economias individuais, agregados
- MD do capítulo com refs atualizadas (`.jpeg` → `.png` onde aplicável)

---

## Limitações conhecidas

1. **Fotografias / continuous tone**: ficam como JPEG (correto — paleta corromperia).
2. **Imagens > 16 cores únicas mas que quantizam bem**: passam por `palette_lossy` com risco mínimo, mas não há gate SSIM ainda (T135).
3. **SVG não testado**: T132 dependeria de potrace; pode dar 30-50% adicional sobre PNG paleta para line art puro.
4. **Fórmulas-imagem**: pix2tex (T134) traria ~100× compressão e ganho semântico, mas exige detector confiável (T133).

---

## Tickets ativos / próximos

- **T130 research** — meta-ticket da família imagens
- **T131 ✓ closed** — PIL classificador + paleta lossy (Frente D)
- **T132 research** — potrace SVG (Frente C+D)
- **T133 research** — detector de fórmula (Frente C)
- **T134 research** — pix2tex (Frente B+D)
- **T135 research** — SSIM gate (Frente D)
- **T136 ✓ closed** — breakdown por formato em `_stats.md`
- **T137 research** — denoise JPEG (Frente D)
- **T180 research** — reconstrução vetorial (Frente E)

---

## Referências

- T131: [`tickets/closed/T131_classificador_e_compressao_imagens_nc.md`](../../../tickets/closed/T131_classificador_e_compressao_imagens_nc.md)
- T130 meta: [`tickets/research/T130_image_optimization.md`](../../../tickets/research/T130_image_optimization.md)
- potrace: [potrace.sourceforge.net](http://potrace.sourceforge.net/)
- pix2tex: [lukas-blecher/LaTeX-OCR](https://github.com/lukas-blecher/LaTeX-OCR)
- SSIM: Wang et al., *Image Quality Assessment* (2004); implementação em `scikit-image.metrics.structural_similarity`
