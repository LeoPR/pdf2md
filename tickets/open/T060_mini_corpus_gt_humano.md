---
id: T060
titulo: Mini-corpus de GT humano (4-5 páginas; gatilho condicional para 10 em T060.2)
status: open
criado_em: 2026-05-10
fechado_em:
fase: 5
depende_de: [T031, T040]
blocks: [T410]
tags: [validacao, gt, ground-truth, mini-corpus]
kind: infra
altitude: execucao
---

## Rescope 2026-05-19 (workflow reavaliação-2-propósitos)

Escopo original era 8-10 páginas (~4-6h trabalho humano). Workflow identificou
que **N=4-5** é o **sinal estatístico mínimo** para responder H_promo/H_descarta
do lab/e15. Páginas adicionais ficam para **T060.2 condicional**, disparado só
se gap WER ≥ 1pp sobreviver à variância de N=4-5.

Mudanças concretas:
- Páginas alvo: 4-5 (4 Preskill + 1 N&C opcional), em vez de 8-10
- Esforço estimado: 2-3h humano (vs 4-6h)
- Arxiv 1706/2106 + tabela CDC + Trotter movidos para T060.2 condicional

## Contexto

[`docs/explanation/literatura.md`](../../docs/explanation/literatura.md) §4 e [`docs/reference/metricas.md`](../../docs/reference/metricas.md) reconhecem que **round-trip não substitui GT humano** para validar fidelidade real do pipeline. Round-trip captura estabilidade (idempotência), mas erros silenciosos por simetria entre extrator e reconstrutor passam despercebidos.

Para a **Frente A (Validação)** ficar completa, precisa de mini-corpus pequeno com MD canônico transcrito manualmente.

## Objetivo (rescope 2026-05-19)

Curar **4-5 páginas** com MD canônico em `corpus/_gt/`, focando no corpus principal:

- **4 páginas Preskill ph219 ch5** (notes 1-col math denso): pg03 ✓ (2026-05-19), pg05, pg07, pg15 — calibra protocolo + cobertura intra-source
- **1 página N&C cap 4** opcional (math denso book) — comparação inter-source

Cortado do escopo atual (vai para T060.2 se gap WER promover GT a primária):
- ~~2 páginas N&C cap 4 (reduzido para 1 opcional)~~
- ~~1 página arxiv 1706.03762 (paper 2-col)~~
- ~~1 página arxiv 2106.05919v2 (math heavy)~~
- ~~1 página tabela complexa CDC~~
- ~~1 página fórmula multi-linha Trotter~~

Cada página GT acompanhada de:
- `<id>/<page>.expected.md` — MD canônico
- `<id>/<page>.note.md` — observações sobre desvios da regra de markdown (e.g. tabela com colspan que precisou inline-HTML)

## Critérios de aceitação (rescope)

- [x] **1 página** em `corpus/_gt/` com MD curado canônico (pg03 ✓ 2026-05-19)
- [ ] **3-4 páginas restantes** em `corpus/_gt/` (pg05, pg07, pg15 Preskill + 1 N&C cap 4 opcional)
- [ ] Para cada página: cobertura de ao menos 1 caso da categoria-meta (math denso, headers aninhados, eq numerada)
- [ ] Pipeline atual rodado nas mesmas páginas (comparação WER-prosa contra GT)
- [ ] Resultado: tabela WER-prosa + count-diff por página com **N ≥ 4**
- [ ] Comparação: gap entre `WER(GT, extracao)` e `WER(roundtrip)` quantificado

## Critério de promoção / descarte / disparo T060.2

- **Promover GT** a métrica primária (round-trip vira health-check) se `WER(GT, extracao) − WER(roundtrip) ≥ 1pp` mediano com N≥4
- **Descartar GT** (round-trip continua proxy aceitável) se gap `< 1pp` mediano
- **Disparar T060.2** (expandir para arxiv 1706/2106 + tabela + Trotter) **só** se gap promove **e** variância alta no N=4-5 indicar que mais páginas trariam sinal mais limpo. Caso contrário, T060.2 não roda — economia de 2-4h de curadoria humana

## Não-objetivo

- Curar livro inteiro — 4-5 páginas respondem Q1 da [literatura.md §6](../../docs/explanation/literatura.md)
- Validar todas as métricas de [metricas.md](../../docs/reference/metricas.md) — apenas WER-prosa + count-diffs
- Automatizar a curadoria — é trabalho humano consciente, **~2-3h com rescope** (vs 4-6h escopo original)
- Cobrir paper 2-col, tabela gov, math heavy nesta passagem — vão para T060.2 condicional

## Esforço estimado

~4-6h de trabalho humano + ~1-2h de comparação automatizada.

## Progresso (2026-05-16)

### Infraestrutura pronta (1-2h automatizadas)

- ✅ `corpus/_gt/` criado com estrutura por doc-id
- ✅ `corpus/_gt/README.md` com fluxo de curadoria + status por doc
- ✅ `corpus/_gt/_TEMPLATE_note.md` template em branco para notas
- ✅ `corpus/_gt/_prefill.py` gera drafts via PyMuPDF text-extract para
  8 páginas em 5 docs (cobrindo 5 categorias-meta)
- ✅ 8 `pg<NN>.expected.md.draft` + 8 `pg<NN>.note.md` criados
- ✅ `lab/e15_gt_validation/` com:
  - `compare_gt.py` — WER-prosa com mascaramento + count-snapshots por categoria
  - `run.py` — itera sobre `.expected.md` curados, compara com extração
    via PyMuPDF cache, gera relatório JSON + MD
  - `run.ps1` runner com venv dedicado
- ✅ Smoke test do `compare_gt.py` passou; `run.py` reporta corretamente
  "0 curadas + 8 drafts pendentes" no estado atual

### Trabalho humano pendente (4-6h)

- [ ] **nielsen_chuang_cap4/pg199.expected.md** (math denso)
- [ ] **nielsen_chuang_cap4/pg200.expected.md** (math denso)
- [ ] **nielsen_chuang_cap4/pg204.expected.md** (Theorem 4.1 + fórmula multi-linha)
- [ ] **preskill_ph219_ch5/pg01.expected.md** (notes 1-col)
- [ ] **preskill_ph219_ch5/pg02.expected.md** (notes 1-col)
- [ ] **arxiv_1706_03762/pg03.expected.md** (paper 2-col, math moderado)
- [ ] **arxiv_2106_05919v2/pg30.expected.md** (math heavy)
- [ ] **cdc_mmwr_73_35_a1/pg01.expected.md** (tabela complexa gov)

Fluxo por página: abrir PDF + draft lado a lado, comparar parágrafo a
parágrafo, corrigir, anotar desvios no `.note.md`, renomear de `.draft`
para `.expected.md`. ~30-45min por página math-heavy.

### Próxima ação (automatizada, após GT pronto)

```powershell
cd lab/e15_gt_validation
.\run.ps1
```

Reporta WER-prosa + count-diffs por página. Veredito:
- Gap < 1pp vs round-trip → promove round-trip como métrica primária
- Gap ≥ 1pp → GT vira métrica primária; round-trip = health-check

### Limitação conhecida (sub-ticket potencial)

`extract_hyp_for_page` em `lab/e15/run.py` usa PyMuPDF text-extract direto
como hipótese, não marker output. Em fase 2 (após validação inicial), pode-se
re-extrair via `marker_single --page_range N-N` para isolar o efeito do
marker. PyMuPDF extract puro serve como **baseline mais conservador** (sem
ML, sem reordering) — útil pra entender se o gap GT vs marker é causado
pelo marker ou já existe no PyMuPDF.

## Conexão

- Frente A da hierarquia (validação)
- Bloqueia T410 (alt tools): comparação Marker × Nougat × MinerU precisa de GT para ser confiável
- Q1 do backlog em LITERATURA.md
