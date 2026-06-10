# Direitos e proveniência do corpus

Este projeto trata PDFs como **fontes de dados** organizadas em 3 tiers
(ver [`registry.py`](registry.py)). Política de direitos por tier:

## Tier IN-REPO (`corpus/examples/`) — versionado, redistribuível

Só material **livre**: public domain ou US Government Work. Excertos de arXiv:
atenção — a licença *non-exclusive* do arXiv concede direitos **ao arXiv**, não a
terceiros; os excertos aqui são curtos, atribuídos e se apoiam em **citação/fair
use**, não em licença de redistribuição. Ver
[`examples/README.md`](examples/README.md) para o status de cada arquivo.

## Tier ZCACHE — referenciado, não versionado

Fontes livres porém pesadas/recuperáveis. Bytes ficam em `Z:/caches/corpus/pdf2md/`
(fora do git); o registry guarda URL + sha256 para re-download. Inclui itens
**não redistribuíveis** (ex. Preskill `read-only-online`) — por isso ficam fora do git
mesmo sendo "grátis": referenciar é OK, redistribuir não. Pelo mesmo critério, o GT
de itens não-redistribuíveis (transcrições + rasters de página, ex.
`corpus/_gt/preskill_ph219_ch5/`) foi **removido do repo público em 2026-06-09**,
alinhando o conteúdo a esta política.

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
  contêm expressão original da obra — métricas, telemetria, vereditos. Ex.:
  - Tabelas de WER/grade, contagens, modos de falha.
- **Transcrições verbatim (GT) NÃO são mais publicadas:** `corpus/_gt/nielsen_chuang_cap4/`
  (3 páginas) era publicado como excerto fair-use; em **2026-06-09** foi tornado privado e
  purgado do histórico por decisão do autor — critério mais conservador que o fair use
  (publica-se o que é **licenciado ou domínio público**, não o que é apenas "defensável").
  O GT segue existindo localmente para o caminho científico (tier private).

### Declaração

> O material derivado do N&C QCQI presente neste repositório é usado por um detentor de
> licença legítima do livro, para fins de pesquisa em extração de documentos. Não
> constitui reprodução substancial da obra. O PDF original e reproduções completas são
> mantidos fora do repositório e do domínio público.

## Caminho para push público

Ver [`docs/reference/corpus/licensing.md`](../docs/reference/corpus/licensing.md).
Resumo: código (MIT) + docs + manifests + `corpus/examples/` (livre) + resultados
derivados-com-declaração são publicáveis; tier private nunca.
