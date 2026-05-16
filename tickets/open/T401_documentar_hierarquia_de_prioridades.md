---
id: T401
titulo: Documentar hierarquia de prioridades
status: open
criado_em: 2026-05-07
fechado_em:
fase: 1
depende_de: [T400]
blocks: []
tags: [design, philosophy, hierarquia]
kind: decisao
---

## Contexto
Filosofia de design do conversor — qual prioridade quando há conflito.

## Resultado

### v1 (2026-05-07)

Documentado em `docs/explanation/philosophy.md` (originalmente `tools/pdf_md_converter/PHILOSOPHY.md`). 4 níveis:
1. Conteúdo (palavras, fórmulas, números)
2. Estrutura útil (headers, tabelas, imagens com semântica)
3. Otimização intermediária (formato adaptativo, links externos)
4. Formatação idêntica (compactação como transporte)

### v2 (2026-05-10) — adição do eixo de representação

PHILOSOPHY ganhou seção **"Eixo de representação"** com 5 níveis ortogonais à hierarquia de objetivos:

| Nível | Representação |
|---|---|
| 1 | Bitmap arbitrário (JPEG/PNG raster) |
| 2 | Bitmap otimizado (PNG paleta lossless, 1-bit) |
| 3 | Vetor (SVG) |
| 4 | Texto vetorial (texto + fonte + geometria + brasão residual) |
| 5 | Texto semântico (LaTeX, MD) |

Regra de operação: para cada elemento, escolher representação **mais semântica que não viola a 1ª prioridade**. Os dois eixos juntos sustentam a estratégia de longo prazo: **extrair máximo de informação primeiro, depois maximizar qualidade com a maior compressão semântica possível**.

Esse eixo dá origem às Frentes D (otimização de representação, T131/T135/T136/T137) e E (reconstrução vetorial, T180) do ROADMAP.

## Por que open e não closed
Documento revisado em 2026-05-10 com adição do eixo de representação. Continua aberto porque
pode precisar v3 conforme T410 (alt tools) e T180 (reconstrução vetorial) amadurecerem.
