---
id: T440
titulo: MD como formato de transporte (vs PDF)
status: research
criado_em: 2026-05-07
fechado_em:
fase: 1
depende_de: [T400]
blocks: []
tags: [research, transport, packaging, distribution]
---

## Contexto
PDF é formato de visualização. Para distribuir/compartilhar conteúdo academico,
o trade-off é:

| | PDF | MD + assets |
|---|---|---|
| Tamanho típico | ~5-50 MB para livro | ~3-10 MB (MD + imagens) |
| Editável | Não (precisa source) | Sim |
| Searchable | Sim, mas frágil | Sim, robusto |
| Versionável | Não (binário) | Sim (texto) |
| Renderizável offline | Sim, qualquer reader | Precisa renderer (KaTeX, pandoc) |
| Layout fixo | Sim | Não (responsivo) |
| Metadata estruturada | Limitada | Rica (frontmatter, anchors) |

## Hipótese
Para conteúdo de estudo/pesquisa, MD + assets pode ser **formato de transporte
superior** ao PDF: mais compacto, mais editável, mais buscável.

## Sub-investigações

### Compactação inteligente
- MD canônico zipado: tamanho vs PDF original?
- Imagens otimizadas (T130) podem reduzir 50-70% do total
- Bibliografia em BibTeX externa, citada por chave

### Resolução de assets
- Imagens via CDN/IPFS — MD distribuído sem binários
- Assets cacheados localmente quando online
- Modo offline (tudo embutido, ~PDF original)

### Empacotamento
- `.tar.gz` ou `.7z` com MD + imagens otimizadas
- Manifest JSON com metadata (autor, licença, fonte)
- Idealmente: 1 arquivo único portátil

## Quando explorar
Depois de T410 (alt tools) e T130 (image optimization). Faz sentido empacotar
quando o conversor já está produzindo output estável.
