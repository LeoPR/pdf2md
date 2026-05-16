---
id: T430
titulo: Corpus livre para testes (URLs + licenças)
status: closed
criado_em: 2026-05-07
fechado_em: 2026-05-11
fase: 1
depende_de: [T400]
blocks: []
tags: [corpus, free, test-data, licenses]
kind: infra
resolucao: substituído por T040 + docs/reference/corpus/manifest_sources.md
---

## Resolução

Fechado como **substituído** em 2026-05-11. A intenção original (lista de PDFs com URLs/licenças/categoria/tamanho/layout/math-density) foi cumprida com mais rigor por:

- **T040** (closed): corpus canônico inicial com 8 entradas + 9 PDFs "sujos" (orientou e02)
- **`docs/reference/corpus/manifest_sources.md`**: paths absolutos, SHA-256, tamanho, licença por entrada
- **`docs/_archive/PDFS_SUJOS_CANDIDATOS.md`**: pesquisa histórica que orientou a expansão dos "sujos"

Conteúdo original preservado abaixo como referência.

---

## Contexto
Para validar o conversor em PDFs variados, precisamos de um corpus de teste com
licenças que permitam uso (testes locais, share de métricas).

## Fontes mapeadas (todas livres ou CC)

### Lecture notes / livros open access
- **Preskill — Quantum Computation Lecture Notes** (Caltech)
  - URL: http://theory.caltech.edu/~preskill/ph229/
  - Licença: free for academic use
- **Mermin — Quantum Computer Science** (notas online)
- **Wikiversity / OpenStax**: livros open

### Papers (arXiv preprints)
- **arXiv** preprints — geralmente licenciados arXiv.org perpetual non-exclusive
- Boas para teste de pipeline, não para redistribuição

### Open access journals
- **Quantum Journal** (quantum-journal.org) — todo conteúdo CC-BY 4.0
- **PRX Quantum** — alguns artigos open access

### Public domain
- Papers antigos (>70 anos pós-morte do autor) em domínio público
- Government reports (NIST publications, alguns arXiv classics)

## Critério para fechar
Lista de 10-20 PDFs em `corpus/CORPUS.md`:
- URL de download
- Licença
- Tópico (math, physics, CS)
- Tamanho (curto/médio/longo)
- Layout (single/multi-column)
- Math density (low/medium/high)

## Política
- Os PDFs em si **não vão pro git** (mesmo CC-BY, são MB volumosos)
- O `CORPUS.md` lista URLs para o usuário baixar
- Cada extração testada gera `_stats.md` que é versionado
