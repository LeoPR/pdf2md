---
id: T101
titulo: Marker PDF extraction com GPU (RTX 3060)
status: closed
criado_em: 2026-05-05
fechado_em: 2026-05-05
fase: 1
depende_de: []
blocks: [T102]
tags: [conversor, marker, gpu]
kind: pipeline
---

## Contexto
Extração antiga de N&C via PyMuPDF puro tinha qualidade ruim — fórmulas como texto solto, ligaduras quebradas (`ﬁ`, `ﬂ`), estrutura por Parte (3 blobs grandes).

## Objetivo
Re-extrair com marker-pdf usando GPU (RTX 3060 com 12 GB VRAM). LaTeX para fórmulas, zero ligaduras quebradas.

## Critérios de aceitação
- [x] marker-pdf instalado em `Z:/venvs/marker/`
- [x] Torch com CUDA suporte (torch 2.11+cu128)
- [x] Extração completa do livro
- [x] Zero ligaduras quebradas
- [x] Fórmulas em LaTeX

## Resultado
- 17,264 linhas de MD, 2.6 MB
- 1,975 fórmulas display ($$..$$)
- 511 headers
- 198 imagens
- Tempo: 1h09min em GPU
- Output em `C:/Users/leona/AppData/Local/Temp/marker_full/Nielsen_Chuang_QCQI/`
