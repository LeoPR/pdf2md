---
id: T180
titulo: Reconstrução vetorial de imagens-com-texto (texto + fonte + geometria + brasão residual)
status: open
criado_em: 2026-05-10
fechado_em:
fase: 4
depende_de: []
blocks: []
tags: [conversor, imagens, vetorizacao, reconstrucao, frente-e]
kind: experimento
---

## Estado pós-experimental (2026-05-17)

`lab/e16_image_decompose/` (logo Cambridge, N=1) e `lab/e17_vlm_full_page/`
(pg 204 N&C math, N=1) trouxeram evidência empírica que redesenha o ticket:

**Confirmado** (e16):
- 4/4 VLMs locais via Ollama leem texto curto em logo simples
- `gemma3:4b` é o **mais rápido E correto** (46s, transcrição fiel)
- `gemma3:12b` empata em qualidade mas é 2.6× mais lento
- `llama3.2-vision:11b` regride (troca caso e adiciona pontuação)
- VLM substitui o passo de "OCR semântico para small-image" originalmente
  delegado a T160 — para o escopo limitado de T180, VLM é auto-suficiente

**Falsificado** (e17):
- VLMs (4/4) **alucinam massivamente** em página math+prosa+layout
  (nível 5 da hierarquia de testes)
- Não escalam para extração full-page — Marker continua insubstituível
- Mais capacidade = alucinação mais confiante (gemma3:12b alucinou mais
  elaboradamente que gemma3:4b)

**Implicação para T180**:
- T180 fica **escopado a small-image decompose** (logos, headers, badges,
  brasões institucionais)
- **Não tentar** generalizar para figuras complexas / diagramas multi-elemento /
  páginas
- Dependência de T160 **removida** (VLM faz a parte de OCR para o escopo
  pequeno; T160 fica para "OCR semântico generalizado" que é problema maior)
- Ferramenta padrão: **`gemma3:4b` via Ollama** (rapidez + custo + acerto
  em small-image)

Status promovido `research → open`: existe caminho empiricamente apoiado
para começar implementação, mesmo que XL em escopo.

---

## Contexto

A imagem da logo Cambridge University Press em `corpus/nielsen_chuang/00_front_matter/images/_page_0_Picture_3.png` foi observação inicial ([T137](../research/T137_denoising_jpeg_pre_compressao.md) nível 3): **se soubéssemos a fonte, o texto e a geometria, poderíamos re-renderizar perfeitamente, deixando só o brasão como bitmap pequeno**.

Isso é o **Nível 4 do eixo de representação** ([PHILOSOPHY](../../docs/explanation/philosophy.md)): texto vetorial + brasão residual.

T160 cobre a etapa de extração ("imagem → texto + bitmap residual"); T180 trata a etapa de reconstrução ("dado texto + bitmap residual, render para imagem original").

## Hipótese

Para elementos repetitivos do corpus (logos de editora, headers de página, marcas d'água), a representação Nível 4 é viável e produz:

- 90%+ de redução de bytes (KB-MB → centenas de bytes)
- Qualidade visual perceptualmente equivalente (SSIM ≥ 0.95) ou superior (sem artefatos JPEG)
- Searchability total do texto extraído

## Método (revisado pós-e16)

1. **Extração** (VLM-as-tool, escopo small-image):
   - **OCR + estrutura via VLM Ollama** (default `gemma3:4b` — escolhido por
     custo-acerto em logos): prompt fiel-de-transcrição
   - **Detecção de fonte**: VLM descritivo ("serif Times-like, all caps, bold")
     em vez de matching formal — N=1 (Cambridge logo) ainda não testou
     classificador fino; usar Times como fallback
   - **Geometria**: bbox via prompt VLM + heurística baseada nas dimensões
     da imagem em pixels
   - **Bitmap residual**: inpaint do texto via Pillow simples (paint sobre
     bbox) → sobra o brasão

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
- **Dependência de T160 removida pós-e16**: VLM faz OCR no escopo small-image
- Promovido a partir de T137 nível 3 (que era especulativo)
- Habilita parte de T440 (MD como transporte — assets vetoriais são naturalmente compactos)
- Apoiado empiricamente em `lab/e16_image_decompose/notes.md` (bancada interna)
- Limite externo empírico em `lab/e17_vlm_full_page/notes.md` (bancada interna):
  VLM não escala para full-page; não tentar generalizar T180 além de small-image

## Origem da ideia

Observação user-driven 2026-05-08: "se soubéssemos o tipo da letra, o que está escrito e a forma, ficando só o logo sobrando, provavelmente essa logo é um copy paste em que só o brasão é realmente uma imagem".

Formalizado como pilar em 2026-05-10 conforme Frente E do ROADMAP.
