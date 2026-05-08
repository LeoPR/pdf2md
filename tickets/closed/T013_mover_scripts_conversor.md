---
id: T013
titulo: Mover scripts conversor para tools/pdf_md_converter/ + generalizar
status: closed
criado_em: 2026-05-07
fechado_em: 2026-05-07
fase: 1
depende_de: [T011]
blocks: [T014]
tags: [infra, refactor, ferramentas]
---

## Contexto
Scripts do conversor estavam em `pesquisa_geral/livros/` (junto com extrações). Misturava ferramenta com dados. Além disso, `restructure_nc.py` tinha PDF_PATH hardcoded para o N&C.

## Objetivo
Mover scripts para `tools/pdf_md_converter/` (ferramentas separadas dos dados) e generalizar para qualquer livro.

## Resultado

| De | Para |
|---|---|
| `pesquisa_geral/livros/restructure_nc.py` | `tools/pdf_md_converter/restructure.py` |
| `pesquisa_geral/livros/roundtrip_test.py` | `tools/pdf_md_converter/roundtrip.py` |
| `pesquisa_geral/livros/gen_chapter_pdfs.py` | `tools/pdf_md_converter/gen_pdfs.py` |
| `pesquisa_geral/livros/README.md` | `tools/pdf_md_converter/README.md` |
| `pesquisa_geral/livros/ROADMAP_CONVERSOR.md` | `tools/pdf_md_converter/ROADMAP.md` |

Movimentações via `git mv` (preserva histórico).

`restructure.py` generalizado:
- `PDF_PATH` removido (era hardcode para N&C)
- `get_chapter_boundaries()` agora recebe `pdf_path` como parâmetro
- `main()` agora pede 3 argumentos: `<pdf>`, `<marker_dir>`, `<target_dir>`
- Validação de arquivo + diretório com mensagem de erro clara

Os outros 2 scripts (`roundtrip.py`, `gen_pdfs.py`) já eram genéricos.
