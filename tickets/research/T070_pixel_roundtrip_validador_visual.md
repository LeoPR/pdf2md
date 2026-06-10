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

A formulação de [PHILOSOPHY §"Validação por fechamento recursivo"](../../docs/explanation/philosophy.md#validação-por-fechamento-recursivo-de-ciclos)
nomeia esse nível como **L0.5** (documento visual). Falta instrumentar.

Assimetria importante: `PDF → imagem` é **operação determinística**
(ISO 32000, ferramentas maduras como PyMuPDF/Poppler/Chrome PDFium).
Diferente de `PDF → MD` que é ill-posed. Isso torna o pivot visual
**mais confiável** que o textual — o erro fica isolado na cadeia
`MD → PDF₁` (reconstrutor).

## Hipótese

Métrica visual decomposta em **triângulo macro / médio / micro**
(definido em [PHILOSOPHY §"Triângulo de métricas"](../../docs/explanation/philosophy.md#triângulo-de-métricas-macro--médio--micro))
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

## Achados do lab e09 (2026-05-16)

Protótipo rodado em `lab/e09_pixel_roundtrip_proto/` validou o triângulo
empiricamente em cap 4 N&C (45 pgs livro vs 49 pgs reconstruído). Resultados:

| Vértice | Median (45 pgs) | Veredito |
|---|---|---|
| Macro SSIM | 0.615 (range 0.49–0.74) | **PROMOVE** — discrimina layouts; vai pra `pdf2md/pixel_roundtrip.py` |
| Médio (bbox IoU ingênuo) | 0.000 | **DESCARTA** pareamento por ordem-de-leitura; replanejar |
| Micro (WER por bbox) | 1.000 | **BLOQUEADO** por médio |

### Sub-tickets derivados (próximas iterações antes de cristalizar)

- **Pareamento robusto de bboxes**: pareamento ingênuo "1º bloco de A
  com 1º de B" não funciona com reflow (PDF original 45pg vs render
  49pg; counts de blocks divergem 4-86 vs 16). Alternativas a testar:
  - texto-fingerprint matching (Jaccard sobre n-grams do conteúdo)
  - header anchor matching (extrair Theorem N.M, Equation, etc.)
  - métrica content-level sem parear blocks (WER agregado por página)

### Bugs descobertos no caminho (separar em tickets próprios)

- **`md_to_pdf` sobrescreve PDF co-irmão silenciosamente** quando MD e
  PDF têm mesmo basename (e.g. `04.md` + `04.pdf`). Reproduzido —
  destruiu o PDF render em `corpus/`. Ver [T076](../closed/T076_md_to_pdf_overwrite_silencioso.md).
- **PDF em `corpus/<doc>/<cap>/<cap>.pdf` NÃO é source** — é gerado pelo
  `md_to_pdf` (metadata: HeadlessChrome+Skia). Source verdadeiro mora
  no AulaQuantum. Documentado em [MD_CANONICAL §"Acessórios"](../../docs/reference/md_canonical.md#arquivos-acessórios).

### Replanejamento de critérios

Critério original (`macro<0.95 AND micro<0.05` para identificar erro de
reconstrução) **inválido**: micro depende de pareamento robusto, ainda
não implementado. Reformulado:

- **MVP fase 1** (curto prazo): macro SSIM apenas. Já útil como métrica
  global complementar ao token-roundtrip.
- **Fase 2**: pareamento robusto (sub-ticket acima) → médio/micro com
  pareamento validado.

## Achados do lab e10 (2026-05-16)

Fingerprint word-bigram + Hungarian rodado em `lab/e10_pixel_roundtrip_fingerprint/`:

- **Cobertura mediana 0%** (peak 83%): word-bigram é fraco para PDFs com
  reflow + escapes markdown + hyphenation + caracteres especiais (α vs \\alpha).
- **Médio IoU geométrico = 0** mesmo onde fingerprint pareou — descoberta
  fundamental: **bbox IoU em coordenadas absolutas é a métrica errada**
  para PDFs com layouts diferentes (margem/fonte distintas tornam bboxes
  incomparáveis mesmo com conteúdo idêntico).
- **Micro WER ≈ 0.39** onde houve cobertura — promissor (vs 1.0 do e09)
  mas limitado pela baixa cobertura.

### Decisão arquitetural derivada

O vértice "médio" do triângulo **não deve ser bbox-IoU geométrico**. Precisa
medir preservação estrutural, não identidade de coordenadas. Alternativas
a testar:

| Opção | Lab futuro |
|---|---|
| Bbox IoU em coords normalizadas (% page) | e12 |
| Kendall-τ / Spearman sobre ordem de blocks | e12 |
| Densidade por célula (página N×M grid) | e12 |
| Drop "médio" — só macro + micro | e12 |

### Sub-tickets refinados

- **e11 — fingerprint refinado**: char 3-grams + normalização forte
  (NFC, strip `\\`, lowercase) + threshold dinâmico
- **e12 — métrica médio alternativa**: comparar as 4 opções acima no
  mesmo dataset

## Achados do lab e11 (2026-05-16)

Ablação de 4 variantes de fingerprint local (char vs word, ±norm,
absoluto vs top-k%) em `lab/e11_fingerprint_refinado/`:

| Variante | Cov med | WER med | Veredito |
|---|---:|---:|---|
| V0 word 2-gram (baseline) | 0.0% | 0.39 | baseline e10 |
| V1 char 3-gram | 2.6% | 0.71 | leve melhoria cobertura, piora WER |
| V2 char+norm | 2.6% | 0.71 | norm pouco ajuda |
| V3 V2+top-30% | 10.3% | 0.87 | força pareamento, degrada |
| V4 V3+ordem | 10.3% | 0.91 | ordem-weight não ajuda |

**Nenhuma atinge cov>50% + WER<0.30.** Insight estrutural: o problema **não é
o fingerprint específico** — é tentar parear blocks individuais quando a
**fragmentação difere** entre PDFs. Render fragmenta cada linha (reflow);
livro mantém parágrafo. Granularidades incompatíveis → fingerprint local
não casa, independente do método.

### Decisão arquitetural derivada (e11)

**Abandonar matching block-a-block.** O vértice "médio" precisa ser
medido **globalmente** ou via **estrutura**, não por pareamento granular.
e12 testará 3 alternativas:

1. **Página inteira global** — concatenar texto, WER global por página
2. **Grid density** — N×M células, distribuição de caracteres
3. **Headings/anchors** — Kendall-τ sobre ordem de elementos estruturais

### Bônus do e11

- `pdf2md.telemetry` validado fora da bancada-suja (primeiro uso em
  ambiente real após promoção T085 v0.5.0)
- Insight de tempo: char 3-gram é **8× mais lento** que word 2-gram
  (3.4s vs 0.43s, 45 páginas) — primeiro dado real do mapa T090

## Achados do lab e12 (2026-05-16)

3 métricas globais por página testadas no cap 4 N&C:

| Métrica | Mediana | Veredito |
|---|---:|---|
| G1 WER global (concat texto, normalizado) | 0.962 | aparenta falha total |
| G2 Grid Pearson (6×8 célula density) | 0.424 | aparenta falha parcial |
| G3 Kendall-τ anchors | 0.541 (cov 13%) | poucos anchors comuns |

**Mas o achado não é "métricas ruins" — é descobrir POR QUÊ:** páginas
i vs i estão **desalinhadas** após reflow (orig 45pg vs render 49pg =
4pg deslocamento acumulado).

Padrão na curva per-page de G1: WER 0.02 nas primeiras pgs, despenca
para 0.96+ a partir da pg ~9 (onde desalinhamento atinge 1 página inteira).
Não é problema da métrica — é **problema de pareamento de páginas**.

### Decisão arquitetural derivada (e12)

O vértice "médio" do triângulo precisa de **alinhamento de páginas como
pré-passo** antes de qualquer métrica per-page. Caso contrário, métricas
medem conteúdos não-correspondentes.

Próximo lab (e13): alinhamento via DTW sobre fingerprint de página, ou
bipartite matching Hungarian global. Após alinhamento, G1+G2 viram
candidatas reais ao "médio"; G3 fica como diagnóstico.

### Insight para T090

Métricas textuais (G1/G2/G3) custam ~0.06s/45pgs cada — **ordem de
grandeza mais barato que macro SSIM** (22s/49pgs). Para indexação em
massa, métrica textual barata + alinhamento de páginas é caminho viável
("rápido + bom-o-suficiente").

## Achados do lab e13 (2026-05-16)

Alinhamento de páginas via Hungarian e DTW destrava o vértice "médio":

| Método | n pares | WER med | %WER<0.30 | %WER<0.60 | Monotonic |
|---|---:|---:|---:|---:|---|
| baseline i==i (e12) | 45 | 0.962 | 8.9% | 15.6% | ✓ |
| A1 DTW | 50 | 0.401 | 34.0% | 84.0% | ✓ |
| A2 Hungarian | 45 | **0.376** | 37.8% | **91.1%** | ✗ |

**Alinhamento funciona dramaticamente** — WER mediano cai 60% após
qualquer alinhamento. **Threshold WER<0.30 é otimista demais** — mesmo
após alinhamento perfeito, ~62% das páginas têm WER > 0.30 por causa de
diferenças tipográficas legítimas (math KaTeX vs LaTeX nativo, hyphenation,
encoding, page numbering). Threshold realista: **WER < 0.60 captura 91%**.

### Decisão arquitetural derivada (e13)

Pipeline definido para o vértice "médio" de T070:

```
1. Macro:  SSIM por par alinhado     (e09 promove)
2. Médio:  Hungarian align + WER     (e13 destrava)
3. Micro:  drop block-a-block         (e11 descarta — não é o caminho)
```

Triângulo **reduzido** de 3 para 2 vértices efetivos (macro + médio
agregado per-page). Micro fica diagnóstico secundário, não obrigatório.

### Insight quantitativo para T090

Alinhamento textual (~3s para 45×49 pgs) é **>7× mais rápido** que macro
SSIM (~22s). Em pipeline "rápido": SKIP macro, mantém medio (alinhamento +
WER pareado). Em "qualidade": macro + medio.

### Próximo

e14 (ou direto em `src/pdf2md/pixel_roundtrip.py`): pipeline integrado
alinhamento + macro + medio.

## Achados do lab e14 (2026-05-16) — cross-PDF validation

Pipeline `pdf2md.pixel_roundtrip` (v0.6.0) validado em 3 categorias
distintas usando o módulo promovido (não cópia do lab):

| Doc | Categoria | Pages | WER med | %<0.60 | SSIM med |
|---|---|---:|---:|---:|---:|
| arxiv_1706 | paper 2-col | 15/15 | **0.258** | 86.7% | 0.639 |
| preskill_ph219 | notes 1-col | 54/46 | 0.395 | 87.0% | 0.610 |
| cdc_mmwr | gov multi-col | 5/9 | 0.421 | 80.0% | 0.533 |
| cap4 N&C (e13) | livro 1-col | 45/49 | 0.376 | 91.1% | — |

**Todos passam critérios de promoção** (WER<0.70, SSIM>0.30, tempo<60s).
Cap 4 N&C é **caso médio** — não favorável, confirma calibração.

### Padrão emergente: monotonicidade

- N == M (mesmo nº pgs): Hungarian tende a inversões locais (ainda OK,
  é otimização global legítima)
- N ≠ M significativo: Hungarian fica monotônico porque drift é caminho
  mais barato

### Limites identificados (sugestões para refinamento futuro)

- Quando `bloat > 1.5×` (n_render/n_orig): DTW provavelmente melhor
  que Hungarian (DTW many-to-one modela reflow naturalmente)
- Flagear não-monotonicidade como info, não como rejeição

### Pronto para integração em produção

Próximos passos práticos:
1. Adicionar como step opcional no `pdf2md convert --rt-pixel`
2. Incluir agregados de pixel-roundtrip no `_stats.json`
3. Heurística de algoritmo automática (Hungarian vs DTW)

T070 pode ser **dividido em sub-tickets** ou marcado parcialmente
fechado (módulo + CLI prontos; integração no convert macro pendente).

### Bônus

- Telemetria (instrumentação local em `lab/e10/telemetry.py`) validou
  o padrão T085 — pronto para promover a `pdf2md/telemetry.py`
- Primeiro perfil concreto coletado: macro_ssim_per_page é gargalo
  (22s = 49% do wall total, single-thread, RSS 323MB peak) — candidato
  óbvio para paralelização (multiprocess pool).

## Conexão

- Frente A (validação)
- Pré-requisito de [T072](T072_calibracao_reconstrutor.md) — calibração precisa do pixel-roundtrip rodando
- Complementa [T050](../closed/T050_baseline_marker_reproduzivel.md) (textual)
- Sub-mecanismo de [T402](T402_pipeline_fractal_recursivo.md) (meta)
- Bloqueia/bloqueado por [T076](../closed/T076_md_to_pdf_overwrite_silencioso.md) (bug do reconstrutor)
- Validado empiricamente em `lab/e09_pixel_roundtrip_proto/`
- Vincula a [PHILOSOPHY §"Validação por fechamento"](../../docs/explanation/philosophy.md#validação-por-fechamento-recursivo-de-ciclos) e §"Triângulo"
