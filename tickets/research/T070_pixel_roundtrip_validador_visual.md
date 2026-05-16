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
  destruiu o PDF render em `corpus/`. Ver [T076](T076_md_to_pdf_overwrite_silencioso.md).
- **PDF em `corpus/<doc>/<cap>/<cap>.pdf` NÃO é source** — é gerado pelo
  `md_to_pdf` (metadata: HeadlessChrome+Skia). Source verdadeiro mora
  no AulaQuantum. Documentado em [MD_CANONICAL §"Acessórios"](../../docs/MD_CANONICAL.md#arquivos-acessórios).

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
- Bloqueia/bloqueado por [T076](T076_md_to_pdf_overwrite_silencioso.md) (bug do reconstrutor)
- Validado empiricamente em `lab/e09_pixel_roundtrip_proto/`
- Vincula a [PHILOSOPHY §"Validação por fechamento"](../../docs/PHILOSOPHY.md#validação-por-fechamento-recursivo-de-ciclos) e §"Triângulo"
