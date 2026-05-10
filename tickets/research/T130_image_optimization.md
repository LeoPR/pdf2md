---
id: T130
titulo: Otimização de imagens — classificação + formato adaptativo + fórmula-como-texto
status: research
criado_em: 2026-05-07
fechado_em:
fase: 4
depende_de: []
blocks: []
tags: [conversor, imagens, otimizacao, fase4, research]
kind: imagens
---

## Contexto

Marker hoje extrai todas as imagens como JPEG, independentemente do conteúdo.
JPEG é lossy e ruim para diagramas binários, line art e fórmulas — desperdiça
bytes e introduz artefatos visuais em conteúdo de baixa entropia.

Hipótese do usuário: classificar cada imagem por tipo e usar o formato/representação
ótima para cada caso.

## Objetivo

Para cada imagem extraída do PDF, decidir entre 4 destinos:

1. **SVG vectorizado** (line art B&W) → menor + escalável + editável
2. **PNG indexado** (line art com poucas cores) → lossless, ~3x menor que JPEG
3. **Texto LaTeX/MD embutido** (fórmulas) → ~100x menor + searchable
4. **JPEG** (fotos / continuous tone) → mantém comportamento atual

## Árvore de decisão

```
para cada imagem em <chapter>/images/:
  cores = contar_cores_unicas(imagem)
  if cores <= 2:
      # B&W puro — line art
      svg = potrace(imagem)
      if size(svg) < size(png):
          salvar como .svg, atualizar referência no MD
      else:
          salvar como .png
  elif cores <= 16:
      # paleta limitada — line art colorido
      salvar como .png (paleta indexada)
  else:
      # continuous tone — foto/diagrama complexo
      # Tentar detecção de fórmula ANTES de JPEG
      if é_provável_fórmula(imagem):
          latex = pix2tex(imagem)
          if confidence(latex) >= 0.85:
              substituir referência no MD por $$<latex>$$, deletar imagem
          else:
              salvar como .png (preserva precisão)
      else:
          salvar como .jpeg (atual)
```

## Tooling proposto

| Etapa | Ferramenta | Licença | Observação |
|---|---|---|---|
| Color count, paleta | `Pillow` | PIL | Trivial; já no venv |
| Edge detection (heurística) | `Pillow` + `numpy` | PIL+BSD | Já no venv |
| Bitmap → SVG | `potrace` (Python wrapper: `pypotrace`) | GPL | Estado da arte para B&W |
| Detecção de fórmula | Heurística (aspect ratio + densidade) ou CLIP zero-shot | Próprio / MIT | Heurística é 80% boa |
| Imagem → LaTeX | `pix2tex` (LaTeX-OCR) | MIT | Modelo ML, ~150 MB; bom para math tipográfico |
| Tabela → MD | `tabula-py` ou `Camelot` | MIT/MIT | Pode complementar |

## Estimativas de ganho

Baseado no N&C (198 imagens, ~25 MB total):

| Cenário | Tamanho final | Notas |
|---|---|---|
| Atual (tudo JPEG) | 25 MB | Baseline |
| PNG indexado para B&W | ~12 MB | Sem mudar formato JPEG nas fotos |
| + SVG quando vetoriza bem | ~7 MB | SVG é grátis pra line art simples |
| + LaTeX para fórmulas isoladas | ~5 MB | Mas ganho semântico é maior que de tamanho |

**Ganho semântico (mais importante):**
- Fórmulas em LaTeX são **searcháveis** (`grep "alpha_z = "` funciona)
- SVG é **editável** se quiser anotar
- Imagens binárias em PNG não têm artefatos de compressão

## Riscos

- **Falso positivo em "é fórmula?"**: classificar um diagrama como fórmula e tentar LaTeX-OCR pode produzir texto sem sentido. Mitigação: threshold alto (≥0.85 confiança) e fallback PNG.
- **pix2tex não cobre tudo**: notação rara (Feynman diagrams, commutative, Young tableaux) falha. Mitigação: deixar como imagem.
- **potrace engessa texturas**: se a origem tem rasterização suave, vetorizar pode parecer "afiado demais". Mitigação: comparação visual via SSIM antes de aceitar SVG.
- **Complexidade adiciona pontos de falha**: cada novo classificador é um lugar onde a pipeline pode quebrar. Mitigação: cada estágio é opt-in via flag, e fallback sempre cai no JPEG atual (comportamento conhecido).

## Plano de execução (sub-tickets ao virar in_progress)

| # | Trabalho | Complexidade |
|---|---|---|
| T131 ✓ | Classificador de cores (≤2, ≤16, contínuo) — só PIL, escolhe extensão | Baixa, ~1 dia (closed em 2026-05-07, −38.6% no N&C) |
| T132 | potrace integrado — vectorize quando B&W e SVG menor | Média, ~2 dias |
| T133 | Detector de fórmula (heurística + bbox) | Média, ~2 dias |
| T134 | pix2tex para fórmulas detectadas | Média, ~3 dias (modelo + threshold) |
| T135 | Validação SSIM antes/depois — gate de qualidade | Baixa, ~1 dia |
| T136 | Atualizar `_stats.md` com breakdown por formato | Baixa |
| T137 | Denoising/restoration de artefatos JPEG antes da compressão | Média-alta, ~3-5 dias (research) |

Total estimado: ~2 semanas se virar trabalho ativo.

## Por que está em `research/` e não `open/`

Cada sub-ideia precisa de prototipagem antes de virar tarefa concreta. Sequência natural:
1. **Prototipar em 1 capítulo do N&C** (cap. 4 — só line art, dataset perfeito)
2. **Medir ganhos reais** vs estimativas acima
3. **Decidir quais sub-fases promover** para `open/`
4. Os que valerem viram tickets T131-T136 com critérios concretos
5. Os que não valerem ficam documentados como "tentado, não compensa"

## Conexão com Fase 3 (fórmulas)

Esta proposta sobrepõe parcialmente com **T120-T122** do ROADMAP.md original
(Fase 3: AST diff, render comparison, "fórmula virou imagem"). Especificamente
o T122 ("Detecção de fórmula virou imagem") é parente do "imagem é fórmula?"
desta proposta.

Ao consolidar, vale unir Fase 3 e parte da Fase 4 num único bloco "Fidelidade
matemática + visual" — fica mais coerente que tratar fórmulas e imagens em
silos separados.

## Quando promover para `open/`

Ativar quando:
- Tiver tempo livre para experimentação (≥1-2 semanas)
- Storage da extração começar a incomodar (atualmente N&C ocupa ~25 MB de imagens, gerenciável)
- Houver caso real de busca por conteúdo de fórmula que falhou por estar em imagem

Até lá, fica como roadmap registrado.
