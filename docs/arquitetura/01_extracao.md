# Camada 1 — Extração

*PDF → texto + estrutura + imagens + fórmulas. Ver [`../ARQUITETURA.md`](../ARQUITETURA.md) para o contexto.*

---

## Diagrama

```
                            ┌────────────────────┐
                            │       Marker       │
                            │     (atual ✓)      │
                            └────────┬───────────┘
              extract                │
   PDF ───────────────────▶          ├─ Surya (OCR + layout + reading order)
                                     ├─ Equation (math detection)
                                     ├─ Texify (math → LaTeX)
                                     └─ output MD + images/
                                              │
                                              ▼
                                     MD + JPEG por padrão
                                     (passa para Camada 2)
```

---

## Ferramentas

### Em uso (estado atual)

| Ferramenta | Versão | Licença | Papel | Tickets |
|---|---|---|---|---|
| **marker-pdf** | 1.10.2 | GPL-3.0 (modelo Open Rail-M) | Extrator principal: PDF → MD com matemática em LaTeX | T101 ✓ |
| Surya (parte do Marker) | (junto) | GPL-3.0 | Backend OCR + layout + reading order multilíngue | (junto) |
| PyMuPDF (`fitz`) | 1.27.2 | AGPL-3.0 | TOC de capítulos para `restructure.py`; metadata | T102 ✓ |

### Experimentadas

| Ferramenta | Status |
|---|---|
| marker DPI 192 (default) vs DPI 300 | Testado em T106 ✓ — DPI 300 não melhora (ganho marginal, custo 2× tempo). DPI 192 fica como canônico. |

### Alternativas planejadas (T410 — Frente Alt-tools)

| Ferramenta | Paper | Licença | GPU? | Strengths para nosso caso | Decisão |
|---|---|---|---|---|---|
| **Nougat** (Meta 2023) | [arXiv 2308.13418](https://arxiv.org/abs/2308.13418) | CC BY-NC 4.0 | sim | Foi o primeiro end-to-end PDF→markup p/ math arXiv | Comparar em fórmulas longas |
| **MinerU 2.5** (Shanghai AI Lab) | [repo](https://github.com/opendatalab/MinerU) | AGPL-3.0 | sim | SOTA em OmniDocBench (~90.67) | Validar no nosso domínio |
| **olmOCR-2** (Ai2 2025) | [Ai2 paper](https://olmocr.allenai.org/) | Apache 2.0 | Qwen2.5-VL-7B | Reading order excelente em multi-col | Stress-teste em scans antigos |
| **Docling** (IBM Research) | [arXiv 2501.17887](https://arxiv.org/html/2501.17887v1) | MIT | CPU OK | TEDS 0.97 em tabelas; multi-formato | Tabelas complexas |
| **GROBID** | [repo](https://github.com/kermitt2/grobid) | Apache 2.0 | não | F1 ~0.89 em citações | Segundo opinion para Citation F1 |

### Especializados (sub-componentes)

| Ferramenta | Papel | Ticket |
|---|---|---|
| **pix2tex / LaTeX-OCR** | fórmula-imagem → LaTeX (Nível 5 do eixo de representação) | T134 |
| **tesseract** | OCR clássico genérico (fallback / segundo opinion) | T420 |
| **potrace** | bitmap → SVG (Nível 3) | T132 |

### Fallback low-resource (T420)

| Cenário hardware | Stack viável | Qualidade esperada |
|---|---|---|
| Sem GPU, 8 GB RAM | marker em CPU (5-10× mais lento) | igual GPU, só lento |
| Sem GPU, RAM limitada | PyMuPDF + ligature fix + regex | 70-80% (sem math LaTeX) |
| Mínimo absoluto | pdftotext (poppler) | 50-60% (texto cru) |

---

## Decisões registradas

1. **Por que Marker e não Nougat como base?** Marker é mais moderno, mais rápido, e tem pipeline modular (Surya + Equation + Texify). Nougat parou em 2023 (sem releases novos). T410 confirmará se Marker continua sendo a melhor escolha.

2. **Por que MD como formato canônico?** Git-friendly, human-readable, search-friendly. LaTeX seria mais fiel mas exige toolchain TeX para visualizar — MD renderiza no GitHub e em qualquer editor.

3. **Por que GPU?** Marker em CPU é 5-10× mais lento. Para N&C completo (704 páginas), CPU levaria ~10h vs ~70 min em GPU RTX 3060. T420 documenta o fallback.

4. **Por que DPI 192 e não 300?** T106 mediu: DPI 300 não melhora detecção de fórmulas/headers/imagens. Custo 2× tempo. DPI 192 é o canônico.

5. **Por que não substituir Marker depois de T410?** Marker é a **base**; T410 valida se outras ferramentas **superam em nichos específicos** (ex.: MinerU em tabelas complexas). Pipeline pode ser híbrido (Marker base + Nougat para math longas).

---

## Inputs e outputs

### Input

PDF (qualquer fonte: arxiv, book scan, paper PMC, slides PPTX, scanned). Path absoluto via `corpus/_sources/MANIFEST.md` ou `corpus/_canonical/MANIFEST.md`.

### Output

```
<output_dir>/<slug>/
├── <slug>.md             ← MD₁ com fórmulas em LaTeX, imagens referenciadas
├── <slug>_meta.json      ← TOC, page boundaries, metadados do marker
└── _page_N_*.{jpeg,png}  ← imagens extraídas (JPEG default; otimizar via Camada 2)
```

Para livros (com TOC), `restructure.py` fatia por capítulo.

---

## Limitações conhecidas

1. **Slides PPTX exportados**: round-trip cai para 28-80% (T451 closed como categoria). Fórmulas-como-imagem geram token bloat na re-extração.
2. **PDFs scanned puros**: dependem 100% de OCR; Marker faz via Surya mas qualidade varia com legibilidade do scan.
3. **Tipografia não-acadêmica**: fontes Calibri/Arial (PowerPoint) ou comerciais antigas geram drift maior que LaTeX/serif puros.
4. **Math notação rara**: Feynman diagrams, commutative diagrams, Young tableaux — fica como imagem.

---

## Tickets ativos / próximos

- **T101 ✓ closed** — Marker base implementado
- **T102 ✓ closed** — Restructure por capítulo
- **T106 ✓ closed** — Estudo DPI (192 vence)
- **T160 research** — OCR semântico generalizado (Frente B — núcleo)
- **T410 research** — Alt-tools comparison
- **T420 research** — Low-resource fallback
- **T450 open** — Investigar IBM lesson 1 (28.9% round-trip)
- **T451 research** — Slides PPTX como categoria

---

## Referências

- Marker: [datalab-to/marker](https://github.com/datalab-to/marker) · sem paper formal
- Surya: [datalab-to/surya](https://github.com/datalab-to/surya)
- Nougat: Blecher et al., [arXiv 2308.13418](https://arxiv.org/abs/2308.13418)
- MinerU 2.5: [opendatalab/MinerU](https://github.com/opendatalab/MinerU)
- olmOCR-2: [olmocr.allenai.org](https://olmocr.allenai.org/)
- Docling: Auer et al., [arXiv 2501.17887](https://arxiv.org/html/2501.17887v1)
- Detalhes adicionais: [`../LITERATURA.md §3`](../LITERATURA.md)
