# Camada 3 — Reconstrução (MD → PDF)

*MD canônico → PDF visualizável. Fecha o ciclo de round-trip (Camada 4). Ver [`../ARQUITETURA.md`](../ARQUITETURA.md) para o contexto.*

---

## Diagrama

```
   MD ──pandoc──▶ HTML ──Chrome headless──▶ PDF'
   │   3.9        │       --print-to-pdf
   │              │
   │              └─ inline CSS (gen_pdfs.py: estilo academia)
   │              └─ KaTeX server-side (math → MathML/HTML)
   │              └─ --embed-resources (imagens inline base64)
   │              └─ --resource-path <chapter_dir>
   │
   └─ (para round-trip: PDF' volta a marker, gera MD')
```

---

## Ferramentas

### Em uso (estado atual)

| Ferramenta | Versão | Licença | Papel |
|---|---|---|---|
| **pandoc** | 3.9 | GPL-2.0+ | MD → HTML (com KaTeX embutido) |
| **Chrome headless** | (sistema) | proprietary | HTML → PDF via `--print-to-pdf` |
| **KaTeX** | (via pandoc `--katex`) | MIT | render server-side de math em HTML |

Configuração no `gen_pdfs.py`:
- `pandoc <md> -o <html> --standalone --embed-resources --katex --css <css> --resource-path <dir>`
- `chrome --headless --disable-gpu --no-pdf-header-footer --print-to-pdf=<pdf> --virtual-time-budget=20000 <html>`

CSS academic embarcado (em `gen_pdfs.py` linha 23-44): headers azuis, tabelas zebradas, código com border-left, math em background suave.

### Alternativas mapeadas (não experimentadas ainda)

| Engine | Math | Tipografia | Dependências | Tradeoff |
|---|---|---|---|---|
| **Tectonic** | excelente (XeTeX) | excelente | single binary ~50 MB | TeX moderno, reproducible builds — alternativa robusta ao "TeX Live completo" |
| **Pandoc + pdflatex/lualatex** | excelente | excelente | TeX Live ~5 GB | Fidelidade máxima de typographs; debug complicado |
| **Typst** | bom (math nativo) | muito boa | single binary Rust | Promissor mas LaTeX→Typst de math ainda imperfeito (2026) |
| **Quarto** | idem Pandoc | templates polidos | Pandoc + Typst/TeX | Útil para templates científicos; não muda fundamentos |
| **WeasyPrint** | limitada (precisa MathML pré-render) | boa (web-style) | Python | Sem GPU/Chrome — útil em CI |

---

## Decisões registradas

1. **Por que Chrome em vez de TeX?** Round-trip 95.09% no N&C cap. 4 com pipeline atual. TeX adicionaria 5 GB de dependências sem ganho perceptível em fidelidade. Chrome+KaTeX cobre 99% do math em livros de QC.

2. **Por que KaTeX e não MathJax?** KaTeX renderiza **server-side via pandoc** (estático no HTML), enquanto MathJax exige JS no client. Chrome headless lida com ambos, mas KaTeX é mais rápido e produz HTML autocontido (`--embed-resources`).

3. **Por que `--virtual-time-budget=20000`?** Chrome precisa esperar fonts carregarem + KaTeX render antes de capturar. 20s funciona para 99% dos casos; slides longos (T450 IBM lesson) podem precisar mais.

4. **Por que não Typst?** Por enquanto, Typst converte LaTeX→Typst de math imperfeitamente (literatura cita issues). Quando o suporte melhorar, vira candidato a substituir Chrome+KaTeX (single binary é vantagem grande em CI).

5. **Por que CSS inline e não tema externo?** Reprodutibilidade — `gen_pdfs.py` versiona o estilo. Mudar tema requer mudar o arquivo, não esquecer um CSS externo.

---

## Inputs e outputs

### Input

- MD canônico do capítulo (`<chapter>/<chapter>.md`)
- Imagens em `<chapter>/images/*.{png,jpeg,svg}` (referenciadas no MD)
- Resource path (`--resource-path`) para resolver paths relativos

### Output

- `<chapter>/<chapter>.pdf` (gen_pdfs.py)
- Ou PDF intermediário do round-trip (`out/roundtrip/roundtrip.pdf`)

---

## Limitações conhecidas

1. **KaTeX não cobre todo AMS-LaTeX**: notação rara (commutative diagrams via `\xymatrix`, `tikz`) falha. Mitigação: fórmula vira imagem (que volta a marker como math via OCR — perde-perde).
2. **Chrome adiciona metadados** (timestamps internos) que mudam sha256 do PDF em runs diferentes. Round-trip token similarity não é afetado, mas fingerprint de PDF varia.
3. **Multi-coluna não-preservado**: pandoc gera HTML single-column. PDFs gerados são single-column. Aceitável pela 4ª prioridade (formato).
4. **Fontes do sistema**: Chrome usa fontes do Windows quando disponível; em CI Linux pode renderizar diferente. Não impacta nosso uso atual (rodamos local).

---

## Validação

Round-trip atinge **95.09% no N&C cap. 4** (controle). Em 3 PDFs do corpus canônico (e01), variou 91.34%-98.58%. Pipeline atual é **estável** — pode evoluir, mas substituir Chrome+KaTeX precisa demonstrar ganho material primeiro.

---

## Tickets ativos / próximos

- **T103 ✓ closed** — Script de round-trip implementado
- **T107 open** — MD → PDF por capítulo (gen_pdfs.py já existe; falta integrar)
- **T108 open** — Pacote pip-installable + CLI (toca esta camada via API consistente)
- **Futuro sem ticket**: experimento `lab/eXX_tectonic_vs_chrome` — comparar mesma MD com Tectonic e WeasyPrint

---

## Referências

- pandoc: [pandoc.org](https://pandoc.org/MANUAL.html)
- KaTeX: [katex.org](https://katex.org/)
- Tectonic: [tectonic-typesetting/tectonic](https://github.com/tectonic-typesetting/tectonic)
- Typst: [typst.app](https://typst.app/)
- WeasyPrint: [weasyprint.org](https://weasyprint.org/)
- Comparação detalhada: [`../LITERATURA.md §5`](../literatura.md)
