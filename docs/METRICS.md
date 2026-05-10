# Métricas — `pdf2md`

*Decisão derivada de [`LITERATURA.md`](LITERATURA.md) (T030) e da hierarquia de [`PHILOSOPHY.md`](PHILOSOPHY.md). Ticket: [T031](../tickets/open/T031_definicao_de_metricas.md).*

Este documento define **quais métricas o `pdf2md` reporta** em cada extração e em cada experimento da bancada (`lab/`). A escolha é informada pela literatura de Document AI / OCR (2024–2026) e pela hierarquia de prioridades do projeto: **conteúdo > estrutura > otimização > formato**.

---

## Princípio

Uma métrica só entra no painel se cumpre dois critérios:

1. **Mapeia inequivocamente para uma camada da [PHILOSOPHY](PHILOSOPHY.md)** (1ª, 2ª, 3ª ou 4ª prioridade).
2. **É computável sem GT humano** OU **com GT humano em mini-corpus** já viável (5-10 páginas curadas).

Métricas que misturam camadas (e.g. round-trip token similarity, que junta conteúdo + estrutura + formatação) são úteis como *health check* mas não como métrica primária — não dão para decidir o que melhorar.

---

## Painel primário (4 métricas)

Aplicado a toda extração via `stats.py` e a todo experimento `lab/eNN_*`. Threshold de "atenção" é o ponto onde abrimos sub-investigação.

### M1. WER-prosa (conteúdo textual)

`WER = (S + D + I) / N` sobre o **corpo de prosa** depois de mascarar fórmulas (`$..$`, `$$..$$`), tabelas (`|..|`), code fences e callouts.

- **Camada PHILOSOPHY**: 1ª (conteúdo)
- **Threshold**: ok ≤ 5%; atenção 5–10%; falha > 10%
- **Origem**: variante da WER clássica de OCR/ASR; uso para MD seguindo [arXiv 2404.18664](https://arxiv.org/html/2404.18664v1) (mascaramento de markup)
- **Limitação aceita**: sensível a reading order. Reportar **WER-bag** (bag-of-words variant) em paralelo para isolar erro de ordem.

### M2. ~~CDM~~ → **LLM-as-judge** para fórmulas

> **Atualização 2026-05-10 (via [LITERATURA_v2.md §5.2](LITERATURA_v2.md))**: CDM foi **rebaixada** a métrica secundária após Horn & Keuper ([arXiv 2512.09874](https://arxiv.org/abs/2512.09874), dez/2025) mostrarem que **LLM-as-judge correlaciona 2× melhor com julgamento humano** (Pearson r=0.78 vs CDM r=0.34) em fórmulas. CDM tem falsos positivos em erros estruturais e falsos negativos em símbolos Unicode (`\alpha` vs `α`).
>
> **Recomendação atualizada**: M2 primária = LLM-as-judge (Gemini-2.0-flash ou GPT-4o); CDM mantém-se como secondary check (continua útil para *count* de fórmulas idênticas, falha em ranking fino).
> Backlog Q13 (em LITERATURA_v2 §6.3) propõe validação concreta no nosso corpus.

#### CDM (Character Detection Matching) — agora secondary

Renderiza fórmula predita e GT em imagem, faz matching visual de caracteres com bounding boxes, calcula F1.

- **Camada PHILOSOPHY**: 1ª (conteúdo matemático) + 4ª (renderização visual)
- **Threshold**: ok F1 ≥ 0.95; atenção 0.85–0.95; falha < 0.85
- **Origem**: Wang et al., CVPR 2025 ([arXiv 2409.03643](https://arxiv.org/abs/2409.03643)); 96% de concordância humana vs ~64% de BLEU
- **Implementação**: usar [`UniMERNet/cdm`](https://github.com/opendatalab/UniMERNet/tree/main/cdm). Roda offline.
- **Quando aplica**: como secondary check em experimentos que comparam ferramentas de extração de fórmula (T410, futuras famílias `lab/e1X_*`)

### M3. TEDS para tabelas

`TEDS(T₁, T₂) = 1 − EditDistance(T₁, T₂) / max(|T₁|, |T₂|)` sobre árvore HTML normalizada (Pandoc faz MD → HTML).

- **Camada PHILOSOPHY**: 2ª (estrutura)
- **Threshold**: ok ≥ 0.90; atenção 0.70–0.90; falha < 0.70
- **Origem**: Zhong et al., ECCV 2020 ([arXiv 1911.10683](https://arxiv.org/abs/1911.10683))
- **Caveat**: GFM markdown não suporta `colspan`/`rowspan`. Para tabelas complexas, reportar separadamente `TEDS-S` (estrutura, sem texto). Considerar fallback HTML inline em casos onde TEDS-S < 0.80 (decidir em Q5 do backlog de literatura).

### M4. Painel de count-diffs

Diferença bruta de contagem entre output e GT (ou input e output, em round-trip). Diagnóstico simples mas catastroficamente útil.

| Subitem | Diff aceitável | Atenção |
|---|---:|---:|
| Fórmulas display ($$..$$) | 0 (qualquer diff é flag) | ≥1 |
| Fórmulas inline ($..$) | ≤ 5 (margem de drift de notação) | > 5 |
| Headers (h1-h4) | 0 | ≥1 |
| Tabelas | 0 | ≥1 |
| Imagens referenciadas | 0 | ≥1 |
| Citações (count regex `\[\d+\]` ou similar) | 0 | ≥1 |

- **Camada PHILOSOPHY**: 1ª (count de itens críticos) + 2ª (estrutura)
- **Implementação**: já parcialmente em `stats.py` (math display, math inline, headers, images_referenced, tables_rough). Expandir para citações.

---

## Painel secundário (diagnóstico, não compulsório)

Aplicar quando uma métrica primária dispara atenção, ou em experimentos comparativos específicos.

| Métrica | Camada | Quando aplicar |
|---|---|---|
| **Header level accuracy** (% headers com `#` correto) | 2ª | M4 dispara em headers |
| **Kendall-τ** sobre sequência de headers | 2ª | Suspeita de heading drift em livros longos |
| **Compile-OK rate** (% fórmulas que compilam) | 1ª | Suspeita de hallucination em fórmulas |
| **Caption match** (Levenshtein normalizado caption ↔ GT) | 2ª | Imagens com legendas-chave (figuras científicas) |
| **Citation F1** (Levenshtein 0.85 sobre `(autor + ano + título)`) | 1ª | Bibliografias longas; usar GROBID como segundo opinion |
| **Reading order Spearman footrule** | 2ª | Layouts com sidebar / multi-coluna |
| **TEDS-S** (apenas estrutura) | 2ª | Tabelas com merged cells |

---

## Métricas que continuam sendo computadas mas **não são primárias**

### Token similarity round-trip (atual)

`SequenceMatcher.ratio()` sobre tokens normalizados de MD₁ vs MD₂ (após MD→PDF→MD').

- **Continua sendo computada** em `stats.py` por compatibilidade histórica e como **health check** (regressão de pipeline)
- **Não é primária** porque mistura erros do extrator com erros do reconstrutor (Pandoc + Chrome + KaTeX)
- **Limitação documentada na literatura**: round-trip translation foi desencorajada como métrica direta de qualidade em MT (Aiken & Park 2010, Moon et al. 2020). RTT precisa de verificador semântico downstream para ser informativa
- **Threshold (atual, mantido)**: ok ≥ 90%; atenção 80–90%; falha < 80%

### Multi-iteration round-trip drift

Drift entre MDᵢ e MD₀ ao longo de 5+ iterações.

- **Continua sendo computado** em `multi_roundtrip.py`
- **Útil para**: detectar se o pipeline é idempotente/estável vs. se tem drift contínuo
- **Decisão**: roda apenas em corpus pequeno (1-2 docs), não em toda extração

---

## Mapeamento métrica × PHILOSOPHY

Visão consolidada — qual prioridade cada métrica protege:

| Métrica | 1ª (conteúdo) | 2ª (estrutura) | 3ª (otimização) | 4ª (formato) | Health |
|---|:-:|:-:|:-:|:-:|:-:|
| M1 WER-prosa | ● | | | | |
| M2 CDM (fórmulas) | ● | | | ● | |
| M3 TEDS | | ● | | | |
| M4 count-diffs | ● | ● | | | |
| Header level accuracy | | ● | | | |
| Compile-OK | ● | | | | |
| Citation F1 | ● | | | | |
| Caption match | | ● | | | |
| (existente) Round-trip token sim | | | | | ● |
| (existente) Multi-iter drift | | | | | ● |
| (existente) Image breakdown bytes | | | ● | | |

A 1ª prioridade tem 4 métricas principais (WER-prosa, CDM, count-diffs, compile-OK); a 2ª tem 3 (TEDS, header level, caption match). Sem métrica para 3ª além das já existentes em `optimize_images.py` (compressão, formato adaptativo). 4ª prioridade é deliberadamente sub-medida (fora de escopo).

---

## Plano de implementação progressiva

Não é viável implementar tudo de uma vez. Sequência:

| Fase | Métricas a adicionar | Esforço | Pré-requisitos |
|---|---|---|---|
| **F1** (próximas semanas) | M4 ampliado (citações), M1 WER-prosa básico | Baixo (regex + difflib) | Mascaramento de markup robusto |
| **F2** (após T050) | M3 TEDS via Pandoc → HTML | Médio (precisa parser HTML, e.g. lxml) | Decidir se MD complexo vai inline-HTML |
| **F3** (após T410) | M2 CDM | Alto (precisa instalar UniMERNet, GPU) | Subset de fórmulas com GT |
| **F4** | Painel secundário (header level, citation F1, etc.) | Médio | Experimentos comparativos abertos |

A cada fase, atualizar `stats.py` para emitir as métricas novas no `_stats.json` e na tabela do `_stats.md`.

---

## GT (ground truth) humano em mini-corpus

A literatura aponta inequivocamente: **round-trip não substitui GT humano** para o caso `pdf2md`. Plano:

- **Mini-corpus inicial**: 5-10 páginas curadas com MD canônico transcrito manualmente.
  - Candidatos: 2 páginas N&C cap. 4 (já tem MD₁ histórico — basta auditar e corrigir), 2 páginas Preskill ph219 ch5, 1 página arxiv 1706.03762, 1 página arxiv 2106.05919v2, 1 página tabela complexa, 1 página com fórmulas multi-linha
- **Esforço**: ~4-6h de trabalho humano para curar 8-10 páginas
- **Saída**: `corpus/_gt/<id>/<page>.md` com `<id>.expected.md` e nota sobre desvios da regra de markdown
- **Quando**: depois de T050 fechar e antes de T410, porque a comparação Marker vs Nougat vs MinerU precisa de ground-truth para ser confiável

Vira ticket dedicado (`T060` futuro): "Mini-corpus de GT humano para validação".

---

## Não-objetivos

- **Métricas tipográficas** (font matching, kerning, line-break similarity): fora da PHILOSOPHY (4ª prioridade); só relevante se usuário pedir.
- **Métricas de redação/estilo** (legibilidade, Flesch-Kincaid): irrelevantes para conversão.
- **Métricas computacionalmente proibitivas**: tudo que precise de cluster ou modelos > 5GB. Lab é uma máquina + GPU 12GB.
- **Reproduzir métricas internas de outras ferramentas** (Marker bench, Nougat eval): fica como referência, não como métrica do `pdf2md`.

---

## Referências chave

Lista mínima — para revisão completa ver [`LITERATURA.md`](LITERATURA.md).

- WER/CER em OCR: [OCR-D Quality Assurance spec](https://ocr-d.de/en/spec/ocrd_eval.html)
- TEDS: Zhong et al., [arXiv 1911.10683](https://arxiv.org/abs/1911.10683)
- CDM: Wang et al., [arXiv 2409.03643](https://arxiv.org/abs/2409.03643)
- Round-trip como métrica (limitações): Moon et al., [aclanthology.org/2020.eamt-1.11](https://aclanthology.org/2020.eamt-1.11.pdf); Allamanis et al., [arXiv 2402.08699](https://arxiv.org/abs/2402.08699)
- Reading-order metrics: [arXiv 2404.18664](https://arxiv.org/html/2404.18664v1)
