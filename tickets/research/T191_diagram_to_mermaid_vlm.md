---
id: T191
titulo: Diagrama→mermaid via VLM local (research-tier, VLM-as-tool)
status: research
criado_em: 2026-06-09
fechado_em:
fase: 4
depende_de: [T190, T065]
blocks: []
tags: [mermaid, diagramas, vlm, ollama, extracao, research]
kind: experimento
altitude: execucao
---

## Contexto

A metade CARA do eixo diagramas: flowchart no PDF → código mermaid. É o mesmo
padrão imagem→texto→imagem provado nas fórmulas (e18/e21: crop isolado +
modelo + verificação por re-render), agora com diagrama. Enquadramento honesto
do estado da arte: **research-tier como T180, não feasible-tier** — não existe
equivalente CPU-leve do pix2tex para diagrama→mermaid; modelos CPU-viáveis
(pix2struct/DePlot/MatCha) fazem chart→tabela, não flowchart→mermaid; a
literatura (Flowchart2Mermaid arXiv:2512.02170; FlowLearn; Arrow-Guided VLM
arXiv:2505.07864) mostra VLMs degradando justamente em topologia (arestas), e
resultados decentes usam modelos cloud ou Qwen2-VL fine-tunado. Conclusões
escopadas ao modelo concreto testado (não generalizar de N=1).

## Hipótese

H1: qwen3-vl:8b (Ollama, profile ativo) converte crops ISOLADOS de flowcharts
sintéticos (tier 1: ≤4 nós; tier 2: 5-8 nós) — renderizados em PDF pelo
próprio T190 — em mermaid cujo GRAFO bate com o source: **edge-set F1 ≥0.8 no
tier 1**. Detecção/crop de regiões vetoriais (análogo do e21, via
`get_drawings`) fica explicitamente FORA — outra onda.

## Método / métricas

- Primária — comparação de GRAFO contra o source conhecido (GT por construção):
  parse do mermaid extraído com gramática restrita (subset flowchart definido
  por nós, ~50 linhas de parser) → node-label F1, edge-set F1 (par dirigido +
  label), exact-match de grafo. Strip de code-fence pós-VLM (lição registrada:
  qwen3-vl/gemma3 wrappam em ```` ``` ````).
- Secundária — round-trip honesto: renderizar o mermaid extraído via T190 e
  comparar pixel (page_ssim) com o render do SOURCE via T190. **Caveat
  central**: SSIM cru contra o diagrama original do PDF NÃO vale como nota
  (auto-layout do mermaid não reproduz layout da imagem); mas
  render(extraído) vs render(source) no MESMO renderer é teste de EXATIDÃO
  (grafos idênticos ⇒ layout determinístico ⇒ SSIM≈1), sem crédito parcial —
  o gradiente vem do F1 de arestas.

## Critério de promoção (declarado por simetria; improvável)

edge-F1 ≥0.8 no tier 2 + determinismo razoável ⇒ vira VLM-as-tool atrás de
flag — mesmo confinamento decidido para T180. Nunca caminho executivo default.

## Critério de descarte (= confina a research, registra, não promove)

edge-F1 <0.5 no tier 1 (≤4 nós) para todos os VLMs locais disponíveis
(qwen3-vl:8b, gemma3:12b/4b) — se nem o trivial sai, o gargalo é capability do
modelo local, não prompt; OU latência >60s/diagrama local (inviável até como
tool).

## Deps

Ollama + modelos locais (external-capability, já na stack de profiles; zero
torch no repo). Parser mermaid: stdlib/regex, pip-safe. Render de verificação:
T190 promovido. Para futura imagem SEM GT, métrica reference-free
RecallOCR/PrecisionVE (arXiv:2602.13376) é o caminho citável.

## Não-objetivo

- Página inteira (e17 já falsificou full-page VLM).
- Charts de dados (bar/line → tabela é outro eixo, DePlot-style).
- Detector de região de diagrama (onda própria, análogo do cropper e21).

## Conexão

- Par de [T190](../closed/T190_mermaid_render_md2pdf.md); corpus de
  [T065](../closed/T065_corpus_gt_sintetico.md); irmão metodológico de
  [T180](../open/T180_reconstrucao_vetorial_imagens.md) (mesma família
  imagem-elaborada→representação-textual→reconstrução; T180 = logo→SVG/texto,
  T191 = flowchart→mermaid, e18/e21 = fórmula→LaTeX já entregue).
