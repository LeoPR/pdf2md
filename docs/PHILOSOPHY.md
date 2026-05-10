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

## O ponto fundamental

Se você se perder durante uma decisão de design, pergunte:
**"Esta escolha preserva o conteúdo de forma navegável?"**

Se sim → fazer.
Se não → re-pensar.

O resto é decoração.
