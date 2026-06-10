# Camada 4 — Métrica e validação

*MD₁ vs MD₂ → similarity, divergência categorizada. Decisão de métricas em [`../METRICS.md`](../../reference/metricas.md); contexto em [`../arquitetura.md`](../arquitetura.md).*

---

## Diagrama

```
   MD₁ ─┐
        │
        ├─▶ normalize_md() ──▶ tokens₁ ──┐
        │                                │
        │                                ├─▶ SequenceMatcher ──▶ similarity %
        │                                │
        ├─▶ normalize_md() ──▶ tokens₂ ──┘                              │
        │                                                               │
   MD₂ ─┘                                                               │
                                                                        ▼
                                                              ┌────────────────────┐
                                                              │ categorize_diverg. │
                                                              │  - math            │
                                                              │  - heading         │
                                                              │  - emphasis        │
                                                              │  - image_ref       │
                                                              │  - table           │
                                                              │  - separator       │
                                                              │  - whitespace      │
                                                              │  - other           │
                                                              └────────┬───────────┘
                                                                       │
                                                                       ▼
                                                              _stats.{md,json}
                                                              (Camada de telemetria)
```

---

## Ferramentas

### Em uso (estado atual)

| Componente | Implementação | Papel |
|---|---|---|
| `normalize_md(text)` | `roundtrip.py`, `stats.py`, `multi_roundtrip.py` (3 cópias!) | Remove markers `{N}`, normaliza paths de imagem para basename, colapsa whitespace |
| `SequenceMatcher.ratio()` | `difflib` (stdlib) | Token-level similarity (0-1) |
| `categorize_divergence(a, b)` | `stats.py:253` | Classifica delta em 8 categorias por heurística (`$`/`\\` → math, `#` → heading, etc.) |
| Multi-iteration | `multi_roundtrip.py` | Itera MD → PDF → MD' → PDF → MD'' N vezes; mede sim(MDᵢ, MD₀) e sim(MDᵢ, MDᵢ₋₁) |

### Painel definido em METRICS.md (implementação progressiva)

| Métrica | Implementada? | Camada PHILOSOPHY |
|---|---|---|
| **Round-trip token similarity** (atual) | ✓ | health-check (todas camadas) |
| **M1 WER-prosa** (com mask de fórmulas/tabelas) | futuro | 1ª (conteúdo) |
| **M2 CDM (Character Detection Matching)** para fórmulas | futuro (precisa pix2tex render) | 1ª (conteúdo) + 4ª (visual) |
| **M3 TEDS** para tabelas | futuro (precisa MD→HTML) | 2ª (estrutura) |
| **M4 count-diffs** (fórmulas, tabelas, headers, imagens, citações) | parcial (já temos counts via `stats.py`; falta diff vs GT) | 1ª + 2ª |

---

## Decisões registradas

1. **Por que `SequenceMatcher` e não Levenshtein puro?** SM é diff baseada em blocos comuns (ideal para identificar drift por categoria — math, heading, etc.). Levenshtein puro daria score similar mas sem capacidade de extrair "exemplos de divergência" por categoria.

2. **Por que normalize_md remove `{N}` (page markers do marker)?** Marker insere marcadores de página `{1}`, `{2}` etc. Esses não fazem parte do conteúdo MD canônico — sempre divergiriam no round-trip e poluiriam o score.

3. **Por que normalize basename de imagens?** Round-trip muda paths (`./images/foo.png` vs `foo.png` vs `/tmp/.../foo.png`). Apenas o basename importa para fidelidade do conteúdo.

4. **Por que 8 categorias e não mais?** Empírico — cobrem 95%+ dos deltas observados. `other` agrupa o resto (pontuação inesperada, unicode minus, etc.). Adicionar mais categorias adicionaria ruído.

5. **Round-trip rebaixado a health-check em METRICS.md** — a literatura ([`LITERATURA.md §4`](../literatura.md)) é unânime: round-trip captura estabilidade, não fidelidade. Erros silenciosos por simetria entre extrator e reconstrutor passam despercebidos. **Métrica primária real exige GT humano** (T060).

---

## Telemetria gerada (`_stats.md` e `_stats.json`)

`stats.py` consolida em relatório por extração:

| Seção | Conteúdo |
|---|---|
| Resumo executivo | Páginas, tokens, fórmulas, imagens, ligaduras quebradas, round-trip% |
| Método | Versões de Python, marker, torch, CUDA, pandoc, PyMuPDF |
| Fonte (PDF) | Path, tamanho, sha256, metadata |
| Output texto | Linhas, tokens, palavras, frases estimadas, tamanho MD |
| Estrutura | Headers totais, code blocks, tabelas |
| Matemática | Display, inline, densidade, top 15 LaTeX commands |
| Imagens | Count, tamanho total, **breakdown por formato** (T136 ✓) |
| Round-trip | Tokens MD₁/MD₂, similaridade, **divergências por categoria + exemplos** |
| Reprodutibilidade | Pasta de output, sha256 do PDF, comando para re-extrair |

Output JSON é a versão machine-readable; `aggregate_stats.py` consome para gerar `_OVERVIEW.md` multi-doc.

---

## Limitações conhecidas

1. **Erros silenciosos do round-trip**: extrator e reconstrutor podem compartilhar viés. Round-trip 99% pode esconder perda real.
2. **Token similarity insensível a estrutura**: 95% pode significar "tudo bem" ou "perdi 1 tabela inteira mas o texto compensa". Por isso o painel multi-métrica (M1-M4) é necessário.
3. **Heurísticas de categoria**: `categorize_divergence` usa regras simples; pode classificar errado em casos limítrofes (ex.: `***` vira "emphasis" mas pode ser parte de uma fórmula).
4. **`stats.py` reporta versões do venv ativo**, não do venv que rodou o marker. Isso pode confundir relatórios (visto em e00: reportou `marker-pdf: n/a` porque o venv ativo era `pdf2md_lab_e00` sem marker).

---

## Validação atual

| Doc | Round-trip | Top divergência |
|---|---:|---|
| N&C cap. 4 (T050, controle) | **95.09%** | math 88.5% |
| arxiv_1706_03762 (e01) | 94.33% | math 33 + other 32 + table 22 |
| arxiv_2106_05919v2 (e01) | 98.58% | other 41 + math 40 |
| preskill_ph219_ch5 (e01) | 91.34% | math 71 + other 22 |

Pipeline consistentemente ≥ 90% em paper/livro de math (validado por e01).

---

## Tickets ativos / próximos

- **T103 ✓ closed** — roundtrip.py implementado
- **T104 ✓ closed** — baseline 95.09% no N&C cap. 4
- **T050 ✓ closed** — baseline reproduzível
- **T031 ✓ closed** — painel de métricas definido (M1-M4)
- **T060 open** — mini-corpus GT humano (valida round-trip vs WER real — **bloqueador da Frente A**)
- **Futuro sem ticket**: implementação progressiva de M1 (WER-prosa) → M3 (TEDS) → M2 (CDM) em fases (METRICS.md §"Plano de implementação progressiva")

---

## Refactor pendente (baixa prioridade)

`normalize_md` está duplicado em **3 scripts** com variações ligeiras:
- `src/roundtrip.py:22`
- `src/stats.py:245`
- `src/multi_roundtrip.py:79`

Refatorar para `src/pdf2md/normalize.py` quando T108 (packaging) for ativado.

---

## Referências

- METRICS.md (decisão de painel): [`../METRICS.md`](../../reference/metricas.md)
- LITERATURA.md (limitação do round-trip): [`../LITERATURA.md §4`](../literatura.md)
- difflib SequenceMatcher: [docs.python.org](https://docs.python.org/3/library/difflib.html#difflib.SequenceMatcher)
- TEDS: Zhong et al., [arXiv 1911.10683](https://arxiv.org/abs/1911.10683)
- CDM: Wang et al., [arXiv 2409.03643](https://arxiv.org/abs/2409.03643)
