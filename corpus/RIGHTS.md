# Direitos e proveniência do corpus

Este projeto trata PDFs como **fontes de dados** organizadas em 3 tiers
(ver [`registry.py`](registry.py)). Política de direitos por tier:

## Tier IN-REPO (`corpus/examples/`) — versionado, redistribuível

Só material **livre**: public domain, US Government Work, ou arXiv non-exclusive.
Excertos pequenos, commitados como prova reproduzível. Ver
[`examples/README.md`](examples/README.md) para licença de cada arquivo.

## Tier ZCACHE — referenciado, não versionado

Fontes livres porém pesadas/recuperáveis. Bytes ficam em `Z:/caches/corpus/pdf2md/`
(fora do git); o registry guarda URL + sha256 para re-download. Inclui itens
**não redistribuíveis** (ex. Preskill `read-only-online`) — por isso ficam fora do git
mesmo sendo "grátis": referenciar é OK, redistribuir não.

## Tier PRIVATE — proprietary, fora do git e do público

### Nielsen & Chuang, *Quantum Computation and Quantum Information* (QCQI)

- **Copyright** Cambridge University Press (10th Anniversary Ed., 2010).
- **Direito de uso do autor deste repo:** Leonardo Marques de Souza é acadêmico e
  possui **licença legítima do livro** (cópia adquirida / acesso institucional).
  O uso aqui é para estudo e pesquisa (ground-truth de avaliação de OCR/extração).
- **O que NÃO pode ir a público:** o PDF original e qualquer **reprodução substancial**
  (ex. capítulos inteiros extraídos). Por isso:
  - O source vive read-only no AulaQuantum (`pesquisa_geral/_sources/livros/`), nunca no repo.
  - O output de uso (MD extraído do livro inteiro) tem como **destiny o próprio AulaQuantum**,
    não o repo.
  - `corpus/nielsen_chuang/` (reprodução completa dos 21 caps) foi **purgado do histórico
    git** em 2026-05-31 (`git filter-repo`).
- **O que PODE ir a público (com esta declaração):** **resultados derivados** que NÃO
  constituem reprodução substancial — métricas, telemetria, e **excertos curtos**
  (fair use), desde que acompanhados desta declaração de direito. Ex.:
  - `corpus/_gt/nielsen_chuang_cap4/` — 3 páginas de ground-truth (excerto fair-use,
    usado sob licença acadêmica do detentor).
  - Tabelas de WER/grade, contagens, modos de falha.

### Declaração

> O material derivado do N&C QCQI presente neste repositório é usado por um detentor de
> licença legítima do livro, para fins de pesquisa em extração de documentos. Não
> constitui reprodução substancial da obra. O PDF original e reproduções completas são
> mantidos fora do repositório e do domínio público.

## Caminho para push público

Ver [`docs/reference/corpus/licensing.md`](../docs/reference/corpus/licensing.md).
Resumo: código (MIT) + docs + manifests + `corpus/examples/` (livre) + resultados
derivados-com-declaração são publicáveis; tier private nunca.
