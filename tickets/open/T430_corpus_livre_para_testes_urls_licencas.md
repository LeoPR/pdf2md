---
id: T430
titulo: Corpus livre para testes (URLs + licenças)
status: open
criado_em: 2026-05-07
fechado_em:
fase: 1
depende_de: [T400]
blocks: []
tags: [corpus, free, test-data, licenses]
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
