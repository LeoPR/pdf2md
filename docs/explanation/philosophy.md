# Filosofia do conversor — hierarquia de prioridades

Quando há conflito entre objetivos da conversão, esta é a ordem de
preferência. Ferramentas, parâmetros e decisões de design devem respeitar
esta hierarquia.

## Hierarquia (do mais importante para o menos)

### 1ª prioridade — Conteúdo

**Preservar palavras, fórmulas, raciocínio, números, citações.**

Se algo precisa ser sacrificado, **conteúdo nunca é o que se sacrifica**.
Round-trip que perde uma fórmula é um bug; round-trip que perde uma quebra
de página é cosmético.

Métricas-âncora:
- Token preservation > 95%
- Math content preservation > 90% (LaTeX rendering pode variar; estrutura math não pode mudar)
- Zero perda de números, citações, referências

### 2ª prioridade — Estrutura útil

**Headers, tabelas, imagens com semântica preservadas.**

A estrutura serve à navegação e à compreensão do conteúdo. Se uma tabela
vira texto corrido, perdemos um modo de leitura. Mas isso é menos grave
que perder o conteúdo da tabela.

Métricas:
- Hierarquia de headings preservada (#/##/### consistentes)
- Tabelas como tabelas (não como `pre-formatted text`)
- Imagens com legendas/captions preservadas
- Cross-references resolvíveis (eq. 1.4, fig. 2.3)

### 3ª prioridade — Otimização intermediária

**Imagens viram texto quando faz sentido; binários ligados externamente quando viável.**

Aqui entram:
- Imagens de fórmulas → LaTeX inline (ganho semântico + compressão)
- Diagramas B&W → SVG (escalável, editável)
- Tabelas que vieram como imagem → MD reconstruído
- Imagens raster grandes → links externos (CDN, IPFS, ou caminho relativo)
- Repositório-leve: o MD é canônico, binários grandes ficam à parte

Roadmap detalhado: ver `tickets/research/T130_image_optimization.md`.

### 4ª prioridade — Formatação idêntica

**O PDF não é o destino, é a fonte. Reproduzir layout idêntico é desejável só se barato.**

Se o objetivo é ter um formato de transporte mais compacto e útil que o PDF,
focar em fidelidade visual de fonte/margem/quebra-de-página é otimização
prematura.

Onde isso vira meta:
- Quando o output precisa ir para impressão profissional
- Quando se publica em journal com template específico
- Quando há requisito legal/contratual de "PDF reproduzível"

Para os casos de **estudo, pesquisa e busca**, a 4ª prioridade pode ser
ignorada — o que importa é o conteúdo + estrutura + busca.

## Aplicação prática nas escolhas atuais

| Decisão | Prioridade aplicada |
|---|---|
| Marker como extrator (vs PyMuPDF puro) | 1ª — Marker preserva fórmulas LaTeX |
| MD como intermediário (vs LaTeX) | 2ª — MD é human-readable + git-friendly |
| Per-chapter folders (vs blob único) | 2ª — navegação útil |
| Tudo JPEG (atualmente) | (anti-padrão da 3ª) — viola otimização |
| KaTeX no preview | 2ª — math renderizado mantém compreensão |
| `_stats.md` por extração | meta — telemetria informa decisões |

## Conflitos típicos

- **"PDF reproduzível byte-a-byte"** vs **"MD editável"**: priorizar MD (1ª, 2ª).
- **"Cada figura como JPEG"** vs **"Análise por conteúdo"**: priorizar análise (3ª).
- **"Manter quebras de página"** vs **"Texto fluido para leitura"**: priorizar fluido (1ª).
- **"Formato canônico estável"** vs **"Inovações ML constantes"**: estabilidade (1ª, 2ª).

## Eixo de representação

Em paralelo à hierarquia de objetivos acima, cada elemento extraído pode ser
representado em diferentes níveis de semântica. Do menos para o mais semântico:

| Nível | Representação | Compactação | Editabilidade | Buscabilidade |
|---|---|---|---|---|
| 1 | Bitmap arbitrário (JPEG, PNG raster) | baixa-média | nula | nula |
| 2 | Bitmap otimizado (PNG paleta lossless, 1-bit) | média | nula | nula |
| 3 | Vetor (SVG path) | alta para line art | parcial | nula |
| 4 | Texto vetorial (texto + fonte + geometria + brasão residual) | muito alta | total (texto) | total (texto) |
| 5 | Texto semântico (LaTeX, MD) | máxima | total | total + estrutura |

### Regra de operação

Para cada elemento extraído, escolher a **representação mais semântica** que
**não viola a 1ª prioridade** (conteúdo). Se houver dúvida ou risco de perda,
descer para o nível mais conservador.

Exemplos práticos:

| Caso | Nível alvo | Por quê |
|---|---|---|
| Fórmula em imagem renderizada (`F = ma`) | 5 (LaTeX) se OCR confidence ≥ 0.85; senão 1 | Searchable, compacto. Nível 1 evita corromper conteúdo se OCR errar. |
| Logo Cambridge bicromática | 2 (PNG paleta lossless) hoje; 4 (re-render do nome + brasão como bitmap) ambicioso | T131 closed; T180 trata o pulo |
| Diagrama de circuito quântico (line art) | 3 (SVG via potrace) se line art puro | T132 |
| Foto / continuous tone | 1 (mantido) | Forçar paleta corromperia |
| Tabela vinda como imagem | 5 (MD reconstruído) se classificador detectar tabela; senão 3/2 | Conexão T133 + T134 |

### Como interage com a hierarquia de objetivos

Os dois eixos são **ortogonais**: a hierarquia (1ª-4ª prioridade) define **o que
vale preservar**; o eixo de representação define **como** preservar com o melhor
trade-off entre tamanho, edição e busca.

Conflito típico: aplicar Nível 4-5 pode falhar (OCR errado de fórmula) e violar
a 1ª prioridade. Por isso a regra é "mais semântico que **não viola conteúdo**" —
não "sempre o mais semântico". Quando em dúvida, **descer um nível**.

Esses dois eixos juntos sustentam a estratégia de longo prazo: **extrair o
máximo de informação primeiro, depois maximizar qualidade com a maior
compressão semântica possível** sem sacrificar conteúdo.

## Validação por fechamento recursivo de ciclos

O objetivo de longo prazo do conversor — **extrair o máximo de informação do
PDF** — é vago por construção. "Máximo" não tem medida absoluta sem
ground truth manual, e ground truth não escala. A formulação operacional
que substitui essa vagueza é:

> Se o ciclo `extract → reconstruct → render` fecha bem em todos os
> níveis recursivos da estrutura do documento, então a extração foi
> rica naquele nível. Se fecha mal num nível L_k, o erro está
> localizado lá.

Cada artefato dentro do PDF é tratado como um **mini-PDF** com seu próprio
ciclo. A qualidade global emerge da composição:

| Nível | Artefato | Ciclo (extract / reconstruct) | Métrica de fechamento |
|---|---|---|---|
| L0 | documento (texto + estrutura) | marker (PDF→MD) / pandoc+Chrome (MD→PDF) | token sim + WER + count-diffs |
| L0.5 | documento visual | pymupdf (PDF→img) / pymupdf (PDF→img) | SSIM macro/médio/micro |
| L1 | figura raster → vetor | T132 potrace (raster→SVG) / browser (SVG→raster) | SSIM local + path-count |
| L2 | fórmula em imagem | T133+T134 (pixel→LaTeX) / KaTeX (LaTeX→raster) | CDM + compile-OK |
| L3 | tabela em imagem | classificador → MD/HTML / pandoc | TEDS |
| L4 | logo / elemento repetitivo | T180 (raster → texto+fonte+brasão) / SVG+raster | SSIM + texto-WER do título |
| L5 | (futuro) blueprint CAD | (out-of-scope) | (DWG/STEP, fora do MD) |

Essa decomposição **não é uma feature** — é a **única forma de saber
quem erra** sem GT humano em escala. Cada nível tem critério de promoção
independente e pode ser desenvolvido isoladamente.

**Limite teórico explícito**: MD é estritamente menos expressivo que PDF
(sem CSS-de-impressão, sem fontes embedded arbitrárias, sem layouts
multi-coluna com fluxo livre). O ciclo nunca fecha em 1.0 — fecha
**asintoticamente para o domínio de interesse** (conteúdo + estrutura +
math + figura semântica). Por isso a 4ª prioridade ("formato idêntico")
é deliberadamente abandonada: aceitamos perda de layout fino para ganhar
editabilidade, busca e escala.

## Triângulo de métricas: macro / médio / micro

Métrica visual `pixel-diff` global é frágil — anti-aliasing, hinting,
dpi diferem entre o renderizador original e o nosso. Pior: pode
falhar **mesmo com extração perfeita**, quando o reconstrutor (pandoc +
Chrome + KaTeX) não consegue reproduzir o layout do PDF original
embora o MD contenha toda a informação ("tabela certa, layout torto").

Solução: decompor a métrica visual em três níveis hierárquicos, todos
reportados, nenhum interpretado isoladamente:

| Nível | Métrica | Captura | Ignora |
|---|---|---|---|
| **macro** | SSIM global da página inteira | layout + conteúdo agregados | nada |
| **médio** | bbox alignment estilo DocLayNet (IoU) | preservação estrutural espacial | conteúdo interno dos bboxes |
| **micro** | OCR + WER dentro de cada bbox-de-texto | conteúdo textual independente de layout | layout |

O **triângulo discrimina o erro**:

- Macro cai, médio cai, micro **OK** → erro de **reconstrução**
  (informação está no MD; reconstrutor não consegue layout fiel)
- Macro cai, médio OK, micro cai → erro de **extração local**
  (estrutura preservada, conteúdo dentro de um bbox corrompeu)
- Macro cai, médio cai, micro cai → erro **profundo de extração**

Uma única métrica visual nunca é conclusiva. O triângulo é.

## Calibração do reconstrutor como instrumento

Render do PDF é determinístico (especificação ISO 32000, ferramentas
maduras). Mas o **reconstrutor** (pandoc+Chrome+KaTeX) é uma cadeia
montada por nós, com perdas próprias mesmo dado MD perfeito (KaTeX
falha silenciosamente em macros LaTeX exóticos; Chrome não usa hinting
igual ao engine de origem; pandoc reordena elementos em casos
ambíguos).

A **perda fixa do reconstrutor** é mensurável e deve ser subtraída:

```
MD_ground_truth  ─pandoc+Chrome─▶  PDF_ref
                 ─Tectonic/Typst─▶  PDF_ideal
ruído_base = visual_diff(PDF_ref, PDF_ideal)
```

Qualquer extração futura que produza `visual_diff ≤ ruído_base` é
extração **perfeita até o limite do reconstrutor atual**. Acima disso,
há perda de extração genuína.

É a mesma lógica de **calibrar offset de instrumento antes de medir
sinal** (SNR em áudio, jitter de clock em sistemas digitais). Sem
calibração, não dá pra distinguir "extração ruim" de "reconstrutor
limitado".

Variação útil: **múltiplos reconstrutores em paralelo** (pandoc+Chrome,
Tectonic, Typst, WeasyPrint). Discordância entre eles localiza áreas
onde o MD não é expressivo o bastante — sinal para subir no eixo de
representação (HTML inline em vez de pipe table, `\begin{equation}` em
vez de `$$`).

## Ablação modular: quem erra, quanto erra, quando erra

A pergunta operacional do dia-a-dia é: dado um PDF que extraiu mal,
**qual módulo cobrar?** A tabela abaixo mapeia modo-de-falha →
módulo responsável → métrica que detecta:

| Modo de falha | Sintoma | Módulo | Métrica que detecta |
|---|---|---|---|
| Texto OCR-ed errado | typos, palavras trocadas | marker (Surya OCR) | WER-prosa (M1) |
| Fórmula display perdida | `$$..$$` faltando no MD | marker (LaTeX detector) | count-diff math_display (M4) |
| Fórmula inline → texto | "x equals 1" em vez de `$x=1$` | marker (LaTeX detector) | M4 + compile-OK |
| Tabela corrompida | colunas erradas, células fundidas | marker (table extractor) | TEDS (M3) |
| Imagem com texto = blob | nome no logo perdido | image2sem (futuro) | bbox alignment + micro-WER |
| Heading drift em livro | h2 vira h3 | marker (layout) | header-level + Kendall-τ |
| Citação truncada | `[Smith` em vez de `[Smith 2020]` | marker (reading order) | citation F1 |
| Bloat ratio alto + rt baixo | MD₂ inflado vs MD₁ | marker (re-OCR no PDF reconstruído) | bloat_ratio + roundtrip |
| Layout torto, conteúdo OK | tabela posicionada errado no PDF₁ | reconstrutor (pandoc/Chrome) | macro cai, micro mantém |
| Drift contínuo | sim% cai a cada iteração | reconstrutor OU extrator | multi_roundtrip |

**"Quando erra"** depende da categoria do PDF:

| Categoria | Modos prováveis |
|---|---|
| Livro LaTeX nativo (N&C) | rt ~95%; modos raros |
| Paper arxiv (LaTeX) | similar; tabelas podem cair |
| Slides PPTX→PDF | layout caótico, reading order; T451 |
| Scan de livro antigo | OCR alto, math errado, bloat (T071) |
| Form/AcroForm | escapes markdown, dense markup (Q11.b) |
| CDC MMWR / govdoc | URLs como math (e02 categorização) |

A categoria do PDF é detectável heuristicamente (TOC, fonte embedded,
densidade de math, scan vs digital, etc.) e deve **selecionar o perfil
de extração** apropriado.

## Tradeoffs explícitos

Decisões frequentes têm eixos consistentes. Tornar os eixos explícitos
permite trocar conscientemente em vez de tropeçar:

| Eixo | Ponta A | Ponta B | Quando preferir A |
|---|---|---|---|
| Velocidade ↔ qualidade | marker GPU | marker + use_llm | qualidade quando ROI ≥ tempo |
| Heurístico ↔ ML | regex de citação | GROBID | heurístico quando precisão > 95% basta |
| Modelo único ↔ ensemble | marker só | marker + pix2tex + table-transformer | ensemble quando categoria PDF heterogênea |
| Reconstrutor único ↔ múltiplo | só pandoc+Chrome | + Tectonic + Typst | múltiplo para calibração; único em produção |
| Nível baixo ↔ alto (representação) | PNG paleta | LaTeX inline | subir só com gate de confiança ≥ 0.85 |
| Determinismo ↔ adaptatividade | seed fixo | dynamic chunking | determinismo p/ reprodutibilidade científica |
| Acoplamento ↔ modularidade | marker monolítico | image2sem separado | modularidade quando ablação necessária |

A coluna "quando preferir A" não é decisão fixa — é **gatilho** para
abrir trade-off conscientemente. Cada decisão deve referenciar o eixo
que escolheu e por quê.

## Convergência vs divergência (estabilidade do ciclo)

Round-trip de uma iteração mede similaridade. **Round-trip de N
iterações mede estabilidade** — propriedade ortogonal e tão importante
quanto.

```
PDF₀ → MD₁ → PDF₁ → MD₂ → PDF₂ → MD₃ → ... → MDₙ
```

Três regimes possíveis:

- **Convergência** (`sim(MD₁, MDₙ) → c < 1`, estabiliza em fixed point):
  pipeline tem ponto fixo. Erro acumulado é finito. **Boa propriedade.**
- **Divergência** (`sim(MD₁, MDₙ) → 0`): drift contínuo. Cada iteração
  introduz erro novo. Pipeline tem reconstrutor instável. **Sintoma de
  bug.**
- **Convergência rápida com erro alto** (`c ≈ 0.6`, atinge cedo): há
  ponto fixo mas longe do original. Extrator OU reconstrutor tem perda
  estrutural sistemática. **Sintoma de gap de expressividade.**

Sistema 90% **estável** é preferível a sistema 95% que diverge para 70%
em 5 iter. Já temos `multi_roundtrip.py` instrumentando essa medida —
falta apenas vinculá-la formalmente à teoria neste doc.

## O ponto fundamental

Se você se perder durante uma decisão de design, pergunte:
**"Esta escolha preserva o conteúdo de forma navegável?"**

Se sim → fazer.
Se não → re-pensar.

O resto é decoração.
