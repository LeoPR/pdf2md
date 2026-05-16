# MD canônico — schema do output do `pdf2md`

> *Schema do MD + acessórios produzido pelo `pdf2md`. Qualquer conversor
> futuro da família [transmutos](../explanation/transmutos.md) deve produzir
> output compatível com este schema para que MD seja pivot universal,
> não dialeto.*

Pré-condição "independência de subobjetos" do [META_TRANSMUTOS](../explanation/transmutos.md):
uma fórmula extraída de PDF deve ser **indistinguível** de uma extraída
de DOCX no MD canônico.

## Estrutura de pasta

Dois layouts. Detecção via TOC do PDF (livros têm TOC nível ≥ 2, papers
não).

### Layout book

```
<doc_name>/
├── 01_introduction/
│   ├── 01_introduction.md
│   └── images/
│       ├── _page_0_Picture_0.png
│       └── _page_2_Figure_3.png
├── 02_overview/
│   ├── 02_overview.md
│   └── images/
├── ...
├── index.md                  (TOC agregado dos capítulos)
├── _stats.{md,json}          (telemetria)
├── _image_optimization.{md,json}
└── _OVERVIEW.{md,json}       (se gerado por aggr multi-doc)
```

### Layout paper (flat)

```
<doc_name>/
├── <doc_name>.md
├── _page_0_Picture_0.png
├── _page_1_Figure_2.png
├── ...
└── _stats.{md,json}
```

A diferença é só **agrupamento**: book separa capítulos em subpastas,
paper mantém tudo na raiz. O conteúdo do MD em si segue o mesmo schema.

## Estrutura do MD principal

```markdown
# {título}

<!-- pdf2md-provenance v1 ... -->
> *Convertido por **pdf2md** ...*

{conteúdo: parágrafos, headers, math, tabelas, imagens, etc.}
```

Regras:

- **Primeiro elemento** sempre é heading (`#`).
- **Provenance block** logo após o primeiro heading. Detalhado adiante.
- **Headings** seguem hierarquia: `#` para título do capítulo/paper,
  `##` para seções, `###` para subseções, etc. Sem pular níveis.
- **Encoding** sempre UTF-8 sem BOM.
- **Quebras de linha** Unix (`\n`); writer pode normalizar para CRLF
  no fs Windows, leitores aceitam ambos.

## Provenance block

Inserido pelo `pdf2md prov` após o primeiro heading. **Idempotente**
(re-aplicar substitui em vez de duplicar). Formato exato:

```markdown
<!-- pdf2md-provenance v1 version={ver} date={iso} commit={sha7} source={file} -->
> *Convertido por **pdf2md** `{ver}` (commit `{sha7}`) em {iso} — fonte: `{file}` (sha256 `{8chars}…`, {extractor}).*
```

Campos do HTML comment (parseável por máquina):

| Campo | Obrigatório | Conteúdo |
|---|---|---|
| `version` | sim | versão do `pdf2md` (ex. `v0.4.0`) |
| `date` | sim | ISO date do dia da conversão |
| `commit` | opcional | git short-sha do conversor |
| `source` | opcional | basename do PDF/origem |

O blockquote humano é redundante com o comment — existe para que
leitores de MD vejam a proveniência sem inspecionar HTML.

Versão do schema: `v1`. Mudanças de schema requerem bump (`v2`, ...).

## Imagens

### Naming

Convenção do marker preservada (compatibilidade histórica):

```
_page_{N}_{tipo}_{idx}.{ext}
```

Onde:
- `N` é índice de página (zero-based)
- `tipo` ∈ `{Picture, Figure, Table}` (heurística do marker)
- `idx` é índice dentro da página
- `ext` ∈ `{png, jpeg, svg}` (svg quando T132 vetorização aplicar)

### Localização

- Book: `<chapter>/images/_page_N_*.ext`
- Paper: `<root>/_page_N_*.ext` (flat)

### Referência no MD

GFM padrão:

```markdown
![{alt}]({path})
```

Onde `path` é relativo ao MD:
- Book: `images/_page_0_Picture_0.png`
- Paper: `_page_0_Picture_0.png`

O `alt` text é deixado vazio por marker em geral; conversores futuros
podem preencher (caption do PDF, OCR de texto na imagem, etc.).

## Math

Convenção KaTeX (subset reconhecido por pandoc):

| Tipo | Sintaxe | Exemplo |
|---|---|---|
| inline | `$...$` | `$E = mc^2$` |
| display | `$$...$$` | `$$\\int_0^\\infty e^{-x}\\,dx = 1$$` |
| equation com label | `$$...$$` + ancora MD adjacente | `$$x = 1 \\quad (4.1)$$` |

Regras:

- Math content **não escapa** backslash: `\frac{a}{b}` é literal, não
  `\\frac{a}{b}`.
- Texto fora de math **pode escapar** `_*[]` para evitar interpretação
  markdown indesejada (`\_underscored\_` em palavra técnica).
- Comandos LaTeX suportados: subset KaTeX (https://katex.org/docs/supported.html).
- Macros customizadas (`\newcommand`) não são suportadas no pivot —
  expandir antes ou aceitar como ruído no round-trip.

## Tabelas

Preferência por GFM pipe table:

```markdown
| col1 | col2 | col3 |
|---|---|---|
| a | b | c |
| d | e | f |
```

Quando GFM falha (colspan/rowspan, células com block content, math
complexo dentro de células): **HTML inline**.

```markdown
<table>
<tr><th colspan="2">Header</th></tr>
<tr><td>a</td><td>b</td></tr>
</table>
```

Decisão entre GFM e HTML é por classificador (futuro): TEDS-S contra
GFM render simulado; se cair < 0.80, escalar para HTML.

## Code blocks e blockquotes

GFM padrão. Code fences `` ``` `` com info string opcional:

```markdown
```python
def f(x): return x
```
```

Blockquotes `>` com nesting permitido. Usado para callouts (provenance,
notas, citações).

## Arquivos acessórios

Tudo prefixado por `_` (Unix convention para artefatos não-essenciais).
Ignorados por `find_chapter_mds()` em `pdf2md/pdfs.py`.

| Arquivo | Quem produz | Propósito |
|---|---|---|
| `_stats.{md,json}` | `pdf2md stats` | Telemetria + métricas |
| `_image_optimization.{md,json}` | `pdf2md optimize` | Relatório PNG/JPEG |
| `_OVERVIEW.{md,json}` | `pdf2md aggr` | Agregação multi-doc |
| `_multi_roundtrip.{md,json}` | `pdf2md rt-multi` | Drift N iterações |
| `_marker_raw/` | etapa interna do `convert` | Saída crua do marker (efêmera) |
| `index.md` | `pdf2md restruct` (book) | TOC agregado |
| `<basename>.pdf` co-irmão do `<basename>.md` | `pdf2md pdfs` (render via pandoc+Chrome) | **PDF reconstruído (render), NÃO o PDF original do livro** |

### ⚠ Distinção crítica: `<cap>.pdf` em corpus/ é render, não source

PDFs em `corpus/<doc>/<chapter>/<chapter>.pdf` foram **gerados pelo
próprio pdf2md** via `pdf2md.pdfs.md_to_pdf` — não são o source original.

Sinais inequívocos no metadata:
- `creator`: `Mozilla/5.0 ... HeadlessChrome/<version>`
- `producer`: `Skia/PDF m<version>`
- footer: `p. N / M` (formato do CSS_INLINE do pdf2md)

**Source original** do PDF (livro, paper) mora **fora do `corpus/`** —
ou em `corpus/_sources/` (gitignored, referenciado em
`docs/reference/corpus/manifest_sources.md` via path absoluto), ou em outro projeto
read-only (caso N&C → AulaQuantum).

**Como confirmar antes de comparar PDFs**:
```python
import fitz
doc = fitz.open(pdf_path)
print(doc.metadata.get("creator"), doc.metadata.get("producer"))
# Se contém "HeadlessChrome" ou "Skia" → é render pdf2md, não source
```

Quando precisar do PDF original para benchmark visual (T070
pixel-roundtrip): extrair páginas-alvo do source verdadeiro via PyMuPDF
`insert_pdf(doc, from_page, to_page)`.

JSON é canônico (machine-readable); MD é renderizado a partir do JSON
(human-readable). Modificar manualmente o MD não atualiza o JSON.

## Normalização canônica para round-trip

O `pdf2md.normalize.normalize_md()` define a forma **comparável** do MD,
removendo diferenças cosméticas que não afetam fidelidade de conteúdo:

- Page markers (`{17}` do marker, `<!-- page 17 -->` do pandoc) → removidos
- Paths de imagem → reduzidos a basename (caminhos variam entre runs)
- Whitespace múltiplo → único
- Opcional: escapes markdown (`\_`, `\*`, ...) → unescaped (flag
  `strip_md_escapes=True` para markup denso tipo AcroForm)

Round-trip métrico usa essa forma normalizada como input — não o MD
canônico bruto. **Salvar e versionar é o MD canônico bruto.**

## Validação de um MD canônico

Critérios mínimos para um MD passar como canônico:

1. Primeiro elemento é heading
2. UTF-8 sem BOM
3. Quebras de linha Unix
4. Math em `$...$` ou `$$...$$` (não `\(...\)` nem `\[...\]`)
5. Imagens via `![alt](path)` GFM (não HTML `<img>`)
6. Tabelas em pipe GFM **ou** HTML inline (não MultiMarkdown nem reST)
7. Sem entidades HTML escapadas no texto comum (`&amp;` → `&`)
8. Provenance block presente se output do `pdf2md convert`

Implementação futura: `pdf2md lint <md>` validando esses critérios.

## Não inclui (deliberadamente)

- **Layout pixel-fiel** — 4ª prioridade abandonada
- **Embed-fonts** — MD não controla fonte
- **Page breaks** — `{N}` markers removidos na normalização
- **Anotações PDF** (highlights, comments) — fora de escopo no pivot
- **Formulários AcroForm interativos** — extraídos como texto (Q11.b)

Cada um desses é deliberado: o pivot canônico paga preço de
expressividade em troca de portabilidade.
