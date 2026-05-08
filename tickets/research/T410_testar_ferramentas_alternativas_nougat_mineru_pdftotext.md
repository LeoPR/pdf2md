---
id: T410
titulo: Testar ferramentas alternativas (Nougat, MinerU, pdftotext)
status: research
criado_em: 2026-05-07
fechado_em:
fase: 1
depende_de: [T400]
blocks: []
tags: [research, alt-tools, comparison]
---

## Contexto
Atual stack usa marker-pdf (estado da arte 2024-2025). Mas:
- Marker exige GPU + 5 GB de modelos ML para qualidade alta
- Outras ferramentas têm tradeoffs diferentes que valem mapear

## Ferramentas a testar

| Tool | Característica | License | Custo |
|---|---|---|---|
| **Nougat** (Meta) | ML, especializado em academic PDFs com math | CC-BY-NC-4.0 | Modelo ~1.5 GB, GPU recomendado |
| **MinerU** | OCR + layout + table extraction | AGPL | Modelo ~2 GB, CPU OK lento |
| **pdftotext** (poppler) | Extração simples de texto | GPL | Trivial, sem ML |
| **PyMuPDF + heurísticas** | Extração + reconstrução manual | AGPL | Trivial, leve |
| **Mathpix** | Comercial, math state-of-the-art | proprietary | API paga, ~$5/1k páginas |
| **pix2tex** (LaTeX-OCR) | Math-only, image → LaTeX | MIT | Modelo ~150 MB |

## O que medir
Para cada ferramenta + um corpus de teste pequeno (ver T430):
- Tempo por página
- Tokens preservados
- Fórmulas reconhecidas
- Imagens extraídas
- Round-trip similarity (se aplicável)
- Requisitos de hardware (RAM, GPU/CPU)

## Critério para fechar
Tabela comparativa em `tools/pdf_md_converter/COMPARISON.md` com recomendação
por cenário (low-resource, math-heavy, academic, papers, livros).
