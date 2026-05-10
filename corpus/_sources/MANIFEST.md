# Manifest — sources canônicos

Lista de PDFs cuja **origem é local** (em outro projeto) ou **proprietary**, com possível cópia de trabalho.

Use este manifest para fontes "minhas" — extrações iniciais que vieram de outro contexto, ou cópias pessoais de livros adquiridos. Para corpus público de benchmark (CC, public domain, arXiv), ver [`../_canonical/MANIFEST.md`](../_canonical/MANIFEST.md).

## Schema

Cada entrada é um bloco `yaml` precedido por `## <id> — <título curto>`.

Campos:

- `id` (str): slug snake_case único. Usado por scripts e nomes de pastas em `lab/`.
- `title` (str): título completo do documento.
- `authors` (list[str]): lista de autores.
- `year` (int): ano de publicação.
- `edition` (str, opt): edição/versão.
- `publisher` (str, opt): editora.
- `pages` (int): número de páginas.
- `license` (str): `proprietary` | `cc_by` | `cc_by_sa` | `cc_by_nc` | `public_domain` | `arxiv non-exclusive` | `read-only-online` | outro.
- `category` (str): taxonomia controlada (ver `docs/METRICS.md` quando criado). Atual:
    - `livro_math_heavy`, `livro_image_heavy`, `livro_classical_typography`
    - `paper_math_heavy`, `paper_bio_med`
    - `slides_pptx_export`, `scanned_image_only`
    - `multi_col_dense`, `multilingual_pt`
- `origin` (obj):
    - `type`: `local` (path em outro projeto) ou `url` (download externo).
    - `path` (se local): path absoluto, read-only.
    - `url` (se url): URL primária.
    - `alternates` (list[str], opt): URLs alternativos / espelhos.
- `local_copy` (obj | null):
    - `path`: path absoluto da cópia em `Z:\caches\corpus\pdf2md\`.
    - `sha256`: hash da cópia (string hex 64 chars).
    - `downloaded_at` ou `copied_at`: ISO date.
- `sha256` (str): hash do arquivo na origin (detecta drift quando origin é local).
- `added_at` (date): quando foi adicionado a este manifest.
- `notes` (str, opt): contexto livre.

---

## Entradas

### nc_qcqi — Nielsen & Chuang, Quantum Computation and Quantum Information

```yaml
id: nc_qcqi
title: Quantum Computation and Quantum Information
authors: [Michael A. Nielsen, Isaac L. Chuang]
year: 2010
edition: 10th anniversary
publisher: Cambridge University Press
pages: 704
license: proprietary
category: livro_math_heavy

origin:
  type: local
  path: C:/Users/leona/OneDrive/Documents/Projects/Acadêmicos/AulaQuantum/pesquisa_geral/_sources/livros/Nielsen_Chuang_QCQI.pdf

local_copy: null

sha256: 4090c88c294fbe428114256185118b6862d8716a14f9ebf2c7df258f28eb640e
size_bytes: 8125074
added_at: 2026-05-09

notes: |
  Source canônico vive no AulaQuantum (extração original foi lá, T101).
  Não duplicar em Z:\ — basta referenciar via path absoluto.
  Resultado da extração marker fica em `corpus/nielsen_chuang/` deste repo.
```
