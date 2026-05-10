---
id: T451
titulo: Slides PPTX como categoria problemática para o conversor
status: research
criado_em: 2026-05-07
fechado_em:
fase: 1
depende_de: [T400, T450]
blocks: []
tags: [conversor, slides, pptx, fonte-mista, research]
kind: decisao
---

## Contexto

Olhando o `_OVERVIEW.md` do `pesquisa_geral/`, há um padrão:

| Doc | Origem (PDF metadata) | Round-trip |
|---|---|---|
| `livros/Quantum_Computation_and_Quantum_Information` | Livro tradicional | **95.1%** |
| `papers/2106_05919v2` | Paper LaTeX/arXiv | **98.6%** |
| `papers/s41586_2025_09917_9` | Paper LaTeX/arXiv | **89.5%** |
| `material_aulas/intro_analysis_math_ch1` | Sem metadata (livro) | 82.8% |
| `material_aulas/semana4_lesson3_circuits_ibm` | PowerPoint export | 80.9% |
| `material_aulas/semana3_cap2_nielsen_chuang` | PowerPoint export | 76.5% |
| `material_aulas/semana1_1st_overview_part1a` | PowerPoint export | 74.6% |
| `material_aulas/semana5_lesson4_entanglement_alt` | PowerPoint export | 73.4% |
| `material_aulas/extra_inner_outer_tensor_productsv2` | PowerPoint export | 70.1% |
| `material_aulas/semana5_..._nielsenchuang_entanglement` | PowerPoint export | 59.1% |
| `material_aulas/semana2_ibm_lesson_2_multiplesystems` | PowerPoint export | 55.2% |
| `material_aulas/extra_inner_outer_tensor_productsv2_alt` | PowerPoint export | 53.3% |
| `material_aulas/semana2_ibm_lesson_1_singlesystems` | PowerPoint export | **28.9%** ← T450 |

**Todo material_aulas vem de PowerPoint exportado para PDF.** Round-trip
varia 28.9% – 80.9% (média ~63%). Livros e papers ficam sempre acima
de 80%, geralmente acima de 89%.

## Hipótese

PDFs gerados a partir de PPTX são **estruturalmente diferentes** dos PDFs
de livros/papers:

- Fórmulas inseridas como **imagem rasterizada** ou via Equation Editor
  embutida (não LaTeX nativo)
- Texto distribuído em **caixas/text-frames** sem fluxo único de leitura
- Layout multi-coluna por slide, fundo gráfico, footers
- Fontes dependentes do sistema (Calibri/Arial não são padrão acadêmico)
- Numeração, bullets e headers vêm de templates do PPT, não de markup

Marker é otimizado para o caso "documento acadêmico contínuo" (LaTeX/Word
exports limpos, papers arXiv). Slides são edge case.

## O que este ticket investiga

Não é um bug fix — é um **enquadramento**. Decidir como o pipeline trata
slides:

### Opção A — Aceitar e sinalizar
Adicionar em `stats.py` heurística que detecta "PDF originado de PPTX"
(via `pdf_metadata.title` começando com `Microsoft PowerPoint -`) e
imprime aviso no `_stats.md`: "fonte é slide PPTX; round-trip baixo
esperado, validar conteúdo manualmente".

### Opção B — Pipeline alternativo para slides
Se o usuário tiver o `.pptx` original (não só o PDF):
- Usar `python-pptx` para extrair texto + imagens diretamente
- Pular marker para esses casos
- Round-trip não faz sentido (não há "MD canônico" do PPTX)

### Opção C — Fonte alternativa quando disponível
Para os slides do projeto, há os `.pptx` no Drive da disciplina.
Buscar lá e re-importar via `python-pptx` em vez de via PDF.

## O que medir antes de decidir

1. Quantos `_sources/material_aulas/*.pptx` o usuário tem disponíveis?
2. Comparar tempo + qualidade de `python-pptx` vs marker para 1-2 amostras
3. Validar: slides com fórmulas-como-imagem realmente perdem semântica
   irrecuperável, ou marker poderia ser empurrado?

## Quando promover para `open/`

- Quando T450 fechar com diagnóstico claro
- Quando o usuário precisar editar/buscar conteúdo dos slides (hoje só
  são consumidos como leitura, daí o impacto é menor)
- Quando houver tempo livre para experimento isolado

## Conexão com tickets existentes

- **T450** — investigação concreta do pior caso (IBM lesson 1)
- **T410** — testar Nougat/MinerU; pode ser que outras tools lidem
  melhor com slides
- **T440** — MD-como-transporte; relevante porque slides são onde MD
  ganha mais (PPTX é binário pesado, MD seria muito mais leve)
