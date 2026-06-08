# corpus/examples — prova pronta (tier IN-REPO)

Excertos **livres e pequenos** commitados no git para qualquer pessoa clonar e rodar o
pipeline **sem baixar nada**. Servem de prova reproduzível das categorias do pipeline.

Regenerável: `python corpus/examples/_build_examples.py` (lê as fontes completas via
`corpus/registry.py`, tier `zcache`, e recorta).

| Arquivo | Fonte (doc_id) | Licença | Categoria | Conteúdo |
|---|---|---|---|---|
| `arxiv_1706_03762_excerpt.pdf` | arxiv_1706_03762 | arXiv non-exclusive | paper_2col math | 2 págs (título+abstract+intro) |
| `arxiv_1706_03762_math_excerpt.pdf` | arxiv_1706_03762 | arXiv non-exclusive | paper_2col math (denso) | 3 págs (eqs attention/multi-head/positional) |
| `wilson_mathematics_excerpt.pdf` | ia_mathematics00wils | public domain (pré-1928) | scanned_image_only | 2 págs (scan PD) |
| `cdc_mmwr_73_35_a1.pdf` | cdc_mmwr_73_35_a1 | US Gov public domain | gov multi-col | inteiro (~0.3MB) |
| `irs_f1040_2025.pdf` | irs_f1040_2025 | US Gov public domain | gov_form (AcroForm) | inteiro (~0.2MB) |

**Total: ~1.1 MB.** Cobre 4 categorias (paper math, scan PD, gov multi-col, AcroForm).
O par intro/math do mesmo paper é proposital: o **gatilho de pass2 do T090** discrimina por
conteúdo (math-denso → pass2; prosa → não) no mesmo doc. Sem inflar o git.

## Política de tiers (ver `corpus/registry.py`)

- **inrepo** (aqui): excerto livre, commitado, prova pronta.
- **zcache**: fonte completa recuperável em `Z:/caches/corpus/pdf2md/` (não versionada).
- **private**: proprietary (ex. N&C) — fora do git; ver `corpus/RIGHTS.md`.

## O que NÃO entra aqui

- Nada proprietary (Nielsen & Chuang etc.) — copyright de terceiros.
- Nada com licença não-redistribuível (ex. Preskill `read-only-online` fica só em zcache).
- Fontes pesadas inteiras — só excertos pequenos; o completo vive em zcache.
