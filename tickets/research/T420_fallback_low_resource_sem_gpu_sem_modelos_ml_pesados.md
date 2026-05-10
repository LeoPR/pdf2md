---
id: T420
titulo: Fallback low-resource (sem GPU, sem modelos ML pesados)
status: research
criado_em: 2026-05-07
fechado_em:
fase: 1
depende_de: [T400]
blocks: []
tags: [research, fallback, low-resource]
kind: experimento
---

## Contexto
Marker exige GPU + ~5 GB de modelos. Para usuários com hardware limitado, qual é o
caminho viável que ainda preserva conteúdo razoavelmente?

## Hipóteses

| Cenário | Stack viável | Qualidade esperada |
|---|---|---|
| **Sem GPU, com 8 GB RAM** | marker em CPU, paciência (5-10x mais lento) | Igual ao GPU, só lento |
| **Sem GPU, RAM limitada** | PyMuPDF + ligature fix + regex | 70-80% (sem math em LaTeX) |
| **Mínimo absoluto** | pdftotext + sed/awk pós-processing | 50-60% (texto cru) |
| **Trade-off por pixels** | tesseract + cv2 layout detection | 60-70% (OCR clássico) |

## O que documentar

`tools/pdf_md_converter/LOW_RESOURCE.md` com:
- Decision tree: dado seu hardware, qual stack
- Trade-offs explicitados (o que se perde em cada caminho)
- Scripts de fallback prontos (mesma interface dos atuais)
- Tempos esperados em hardware mediano (CPU-only laptop, 8 GB RAM)

## Quando virar open
Quando alguém pedir, ou quando T410 (testar alt tools) gerar dados suficientes para
escolher os fallbacks empiricamente.
