# Licenciamento e push público

*Auditoria de licenças do conteúdo versionado para decidir o que vai pro GitHub público.*

## Resumo

| Categoria | OK para repo público? | Notas |
|---|---|---|
| **Código** (`src/`, `lab/*/run.ps1` *(bancada interna, não versionada)*, etc.) | ✅ MIT (já em `pyproject.toml`) | Reescrito do zero |
| **Documentação** (`docs/`, `README`, `ROADMAP`, etc.) | ✅ Próprio | Inclui referências a obras de terceiros (fair use citacional) |
| **Tickets** (`tickets/`) | ✅ Próprio | Notas internas, sem conteúdo proprietary |
| **Manifests** (`corpus/_*/MANIFEST.md`) | ✅ Próprio | URLs + sha256 + metadados, sem PDFs |
| **PDFs originais (zcache)** | ⛔ Excluídos via `.gitignore` | `corpus/_sources/*` e `corpus/_canonical/*` ignorados; ref via `corpus/registry.py` |
| **`corpus/examples/` (in-repo)** | ✅ Livre | Excertos public-domain / US-gov / arXiv — prova pronta, ~0.83MB. Ver `corpus/examples/README.md` |
| **Extrações no `lab/`** *(bancada interna, não versionada)* | ⚠️ Caso a caso | Evidência sumária OK (`_stats_*.md`); MD inteiro NÃO |
| **`corpus/nielsen_chuang/`** | ✅ **RESOLVIDO (2026-05-31)** | Purgado do histórico via `git filter-repo`. Ver `corpus/RIGHTS.md` |
| **Resultados derivados N&C** | ✅ Com declaração | Excertos GT + métricas OK público COM declaração de direito (`corpus/RIGHTS.md`) |

## Auditoria detalhada

### ✅ Conteúdo OK para push público

**Código + documentação criada no projeto** — autoria própria, MIT (declarado em `pyproject.toml`).

**Manifests de corpus** — listam URLs e sha256, não conteúdo. Schema declara licenças de cada source.

**Resultados de extração em `lab/`** (bancada interna, não versionada; a partir de `e00_baseline_marker` em diante):
- `_stats_*.md/json` — apenas telemetria (tokens, similarity, divergence counts), zero conteúdo
- `_md1_acroform_excerpt.md` (e05) — nomes de form-fields do IRS Form 1040 (**US Government Work, public domain**)
- `_atkins_md1_extract_ok.md` (e03) — extração parcial de Wilson 1800 / Atkins 1874 (**public domain**, pré-1928)
- `dryrun/<id>/_image_optimization.{md,json}` (e04) — só estatísticas de tamanho

### ⛔ Conteúdo NÃO OK para push público

**`corpus/nielsen_chuang/`** — **248 arquivos** versionados desde o init do repo (commit `be19f01`, antes da reorganização atual):
- 21 capítulos/apêndices em MD completo (cap. 1-12, app 1-6, biblio, index)
- PNGs extraídos de cada capítulo (line art / paleta lossy via T131)
- PDFs gerados por capítulo (gen_pdfs.py output)

**Origem**: Nielsen, Michael A. & Chuang, Isaac L. *Quantum Computation and Quantum Information* (10th Anniversary Edition, 2010). Cambridge University Press. **Copyright Cambridge University Press**.

**Status legal**:
- Uso individual para estudo/pesquisa: provavelmente fair use
- **Distribuição pública (GitHub): violação de copyright**
- A versão extraída é derivada do PDF, herda o copyright

### ⚠️ Conteúdo em zona cinza

**Tickets que mencionam material de cursos**:
- T450 cita IBM Quantum lessons (uso educacional autorizado pela IBM; mas o PDF não está no repo, só foi medido em e02)
- T451 enquadra slides PPTX como categoria — sem distribuir conteúdo

Esses estão OK porque não distribuem o material — só medem características.

## Atualização 2026-05-31 — purge executado + tiers consolidados

A **Opção A foi executada**: `corpus/nielsen_chuang/` (17MB, 248 arquivos, reprodução
completa dos 21 caps) foi removido de TODA a history via `git filter-repo` (repo era
local-only, sem remote → purge limpo). Os 3 excertos de ground-truth em
`corpus/_gt/nielsen_chuang_cap4/` **permanecem** (fair use + declaração — ver
`corpus/RIGHTS.md`).

Tiers consolidados em `corpus/registry.py` (fonte-de-verdade para código):
- **in-repo** (`corpus/examples/`, versionado): livre, prova pronta.
- **zcache** (`Z:/caches/...`, não versionado): livre pesado + não-redistribuível.
- **private** (AulaQuantum, fora do repo): proprietary (N&C); source E destiny lá.

## Caminho para push público (3 opções) — histórico da decisão

### Opção A — Caminho mínimo (RECOMENDADO para marco inicial)

1. **`.gitignore` atualizado** para que `corpus/nielsen_chuang/` não seja mais commitado em mudanças futuras
2. **Tag de marco atual** (`v0.2-lab-completo` ou similar) para preservar histórico interno
3. **Não criar branch público ainda** — quando quiser push público, fazer:
   - Branch novo a partir do master atual
   - `git rm -r corpus/nielsen_chuang/ --cached`
   - Commit do remove
   - `git filter-branch` ou `git filter-repo` para purgar de toda history
   - Push do branch limpo

### Opção B — Branch público desde já

Mais complexo: criar branch `public` agora, manter `master` privado, sincronizar manualmente conteúdo OK entre eles. Sobrecarrega o workflow.

### Opção C — Repositório separado para release público

Repo `pdf2md-public` contendo só código + docs. Mantém repo atual privado. Mais limpo a longo prazo, mas exige sincronização ao publicar.

## Recomendação imediata

**Opção A** com 3 ações agora:

1. Adicionar `corpus/nielsen_chuang/` ao `.gitignore` (não remove o que já está, mas evita futuros adds)
2. Marcar **tag `v0.2-lab-completo`** no estado atual como ponto de partida
3. Quando decidir push público: rodar `git filter-repo --path corpus/nielsen_chuang/ --invert-paths` no clone-fork específico

## Materiais públicos que poderiam virar exemplos

Quando publicarmos, os exemplos do `corpus/_canonical/` (sem N&C) cobrem o pipeline:
- Preskill ph229 ch1 + ph219 ch5 (Caltech, read-only-online)
- arxiv (1706.03762, 1810.04805, 2106.05919v2) — non-exclusive redistribution
- Newton Principia, Wilson Mathematics (public domain)
- Federal Register 1936, CDC MMWR, IRS f1040 (US Government Work)
- MIT OCW 6.0002 (CC BY-NC-SA)

11 docs reproduzíveis, ~80 MB total, cobrindo todas categorias do pipeline. Suficiente para demonstrar o sistema sem precisar do N&C.

## Convenção para futuros sources proprietary

Adicionados a `docs/reference/corpus/manifest_sources.md` (refs, não PDFs):
- `license: proprietary` → automaticamente sinaliza "não redistribuir extração derivada"
- Manter PDFs sempre fora do repo (`Z:\caches\corpus\` ou caminho absoluto em outro projeto)
- Extrações ficam **fora** do versionado se a licença for proprietary
