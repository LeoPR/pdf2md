# Avaliação do pdf2md — condensado em formato de artigo

> *Snapshot 2026-06-10 (v0.8.1 + master). Este doc condensa a avaliação do
> projeto no formato de um artigo científico: método, resultados medidos,
> posição na literatura e ameaças à validade. Os números canônicos vivem em
> [`docs/profiles/`](../profiles/); as fichas de ferramentas/benchmarks da
> literatura em [`reference/biblioteca/`](../reference/biblioteca/INDEX.md).
> Complementa [`philosophy.md`](philosophy.md) (por quê) e
> [`analise_critica.md`](analise_critica.md) (curso do projeto).*

## Resumo

O pdf2md não disputa "o melhor extrator universal": **mede** cada caminho de
extração em vértices primitivos (velocidade, RAM, VRAM, qualidade POR
ELEMENTO) e deixa um roteador escolher o caminho mais barato que satisfaz o
intent do usuário. A avaliação usa (i) um corpus em 3 tiers de direitos, com
um **corpus sintético GT-por-construção** público (a fonte É a resposta
certa, byte a byte) validado como instrumento contra âncoras do corpus real;
(ii) métricas com **calibração de harness pré-registrada** (gates de
identidade, perturbações monotônicas) antes de qualquer medição de extrator;
e (iii) o princípio **delta-E**: GT canônico puro, quirks de renderer e de
transporte isolados em adapters. Resultados centrais: o caminho CPU é ~630×
mais rápido e empata em prosa, mas perde TODA a estrutura de tabela (TEDS
0.0) e a semântica de math; o caminho GPU (marker) atinge **exatamente o
teto do formato markdown** em tabelas (TEDS 1.000; 0.749 em row/colspan =
máximo representável em pipe-table) e descarta 100% do texto vetorial
interno de figuras — que o caminho CPU recupera 100% (inversão com
consequência direta no roteamento de indexação). Comparações numéricas
diretas com benchmarks externos são metodologicamente inválidas (corpora e
métricas distintos); a posição na literatura é dada por pontes de terceiros.

## 1. Introdução

Ferramentas de PDF→Markdown publicam scores agregados altos (95+ em
leaderboards saturados), mas um score único esconde o que importa para quem
roteia trabalho real: **qual elemento** sobrevive, **a que custo**, **em que
hardware**. A tese do pdf2md é que a decisão certa é por intent
(`--rapido`/`--qualidade`/`--indexacao`...), tomada sobre perfis medidos por
elemento — e que a própria bidirecionalidade do sistema (md→pdf com pandoc,
Chrome+KaTeX, mermaid) permite construir ground-truth por construção, em vez
de transcrever GT de obras de terceiros.

## 2. Método

**Corpus (3 tiers de direitos).** `inrepo` (excertos livres + sintético
autoral), `zcache` (recuperável, não versionado), `private` (proprietário,
nunca público; só métricas derivadas com declaração — `corpus/RIGHTS.md`).
O tier público inclui o **corpus sintético GT-por-construção**
(`corpus/examples/sintetico/`, 75 itens, 8 categorias): fórmulas canônicas
(fatos matemáticos, não protegíveis), tabelas em 5 tiers de feature,
diagramas mermaid, logos SVG e prosa — renderizados pelo próprio md→pdf do
projeto. Validade como instrumento (não assumida; medida): gate de
identidade (recall de prosa 1.0000 em 8/8 categorias), concordância de
ranking com âncoras do corpus real (4/4 categorias ancoradas), e
**reaparição dos modos de falha conhecidos** (fraqueza de matriz do pix2tex
~0.5 reproduz nos DOIS renderers).

**Delta-E (adapters).** O GT canônico é um só (md/LaTeX puro); cada renderer
(Chrome+KaTeX vs Tectonic/Computer Modern) é um adapter que gera variante
medida em separado — o eixo de tipografia DOMINA o comportamento de
detectores (medido: cropper de fórmulas 0/24 → 24/24 entre renderers).
O mesmo princípio se aplica a transporte: `thead/tbody/colgroup` do caminho
pipe→pandoc são normalizados fora da comparação TEDS.

**Métricas.** M1 round-trip textual (token-similarity, sem GT); WER contra
GT humano (tier privado); SSIM L0.5 (pixel-roundtrip, extra `[rtpixel]`);
TEDS/TEDS-struct para tabelas (`pdf2md.table_teds`, extra `[tables]`,
implementação canônica PubTabNet); telemetria por step. **Todo harness é
calibrado antes de medir extrator**: identidade = 1.0, perturbações
controladas com resposta monotônica, controles que validam o detector nas
duas direções. Dois exemplos de bug de harness pegos por esse protocolo:
detector de render que lia só a página 0 (falso-negativo 13/20) e parse de
output que cortava no `:` de drive Windows.

**Protocolo.** Cada experimento nasce em ticket com hipótese e **critério de
descarte pré-registrados**; roda em bancada efêmera (`lab/`, não versionada);
só números promovidos entram em `docs/profiles/` com `confianca:
medido|estimado|inferido` explícita e contexto por número.

## 3. Resultados (medidos neste projeto)

Host único (RTX 3060, Win10); N pequeno por célula; escopo declarado por
linha. Caminhos: **CPU** = pdftotext/PyMuPDF (+Tesseract p/ scan, +cropper
built-in+pix2tex p/ math); **GPU** = marker 1.10.2 (Surya+Texify).

| Camada | CPU (pdftotext) | GPU (marker) | CPU recorte (pix2tex) |
|---|---|---|---|
| Prosa | WER 0.016 (real); 1.000 (sint.) | round-trip 0.951 (real, 704 pg); 1.000 (sint.) | — |
| Math display | Unicode cru, sem LaTeX (0.02 sint.) | 0.973 (sint.) | 0.80 (real CM); 0.852 KaTeX / 0.721 CM (sint.) |
| Math matriz | idem | 0.986 (sint.) | **~0.50 (real); 0.38/0.32 (sint.)** — fraqueza do modelo, cross-renderer |
| Math multi-linha (`aligned`/`cases`) | idem | **0.681 (sint.)** — modo de falha inédito | 0.51–0.65 (sint.) |
| Tabela (TEDS) | **0.0 estrutura** (conteúdo 100%, indexável) | **1.000**; spans **0.749 = teto do pipe** (== best-pipe por item) | — |
| Figura vetorial (texto interno) | **1.000** | **0.000** (layout model descarta) | — |
| Scan impresso | WER 0.052 (Tesseract) | risco de alucinação (bloat 7.7× medido) | — |
| Scan manuscrito | ilegível (fora de escopo CPU) | idem | — |
| Recursos | 0.02 s/pg, 63 MB RAM, 0 VRAM | 12.9 s/pg, ~3.4 GB VRAM | 6.5 s/fórmula, CPU |

Três achados que um score agregado esconderia:

1. **Inversão diagrama/logo**: em figura vetorial, o caminho "fraco" (CPU)
   recupera 100% do texto interno e o caminho "forte" (GPU) recupera 0% —
   para indexação, doc rico em diagramas indexa MELHOR pelo caminho barato.
2. **Teto de transporte ≠ perda de extractor**: em tabelas com row/colspan o
   marker pontua exatamente o máximo que pipe-table representa (0.749). Um
   benchmark que não separa os dois atribuiria ao extractor uma perda que é
   do formato de saída.
3. **Degradação seletiva do marker em math multi-linha** (0.681 vs 0.97+ em
   display/matriz) — invisível em médias de "formula score".

## 4. Posição na literatura

**Por que não comparar números diretamente:** nossos valores vêm dos NOSSOS
corpora e métricas; os publicados vêm de benchmarks próprios (OmniDocBench,
olmOCR-Bench, FinTabNet, READoc), com agregações distintas (ex. composite do
OmniDocBench = ((1−TextEditDist)·100 + TableTEDS + FormulaCDM)/3). Comparar
células de tabelas diferentes é inválido. O que É legítimo: (a) comparações
INTERNAS a cada benchmark; (b) pontes — ferramentas que aparecem lá e aqui.

| Ferramenta | Benchmark (de terceiros) | Número publicado | Ficha |
|---|---|---|---|
| MinerU 2.5-Pro | OmniDocBench v1.6 | **95.69** (SOTA; TEDS tabela +5.54; CDM fórmula 97.29) | [ferramentas](../reference/biblioteca/ferramentas.md#mineru-25-pro) |
| MinerU 2.5 | OmniDocBench | ~90.67 | [ferramentas](../reference/biblioteca/ferramentas.md#mineru-25) |
| **Marker** (nosso GPU) | READoc (ACL 2025) | **81.02** (média; melhor pipeline geral) | [benchmarks](../reference/biblioteca/benchmarks.md#readoc) |
| MinerU | READoc | 80.39 | idem |
| Nougat | READoc | 81.42 (arXiv) → 74.12 (GitHub) — não transfere | idem |
| Docling | READoc / FinTabNet | 49.87 / TEDS 0.97 (tabelas corporate) | [ferramentas](../reference/biblioteca/ferramentas.md#docling) |
| olmOCR-2 | olmOCR-Bench | 82.4 (math 82.3, tabelas 84.9) | [ferramentas](../reference/biblioteca/ferramentas.md#olmocr-2) |
| DeepSeek-OCR | próprio | 97% @ compressão 10× | [ferramentas](../reference/biblioteca/ferramentas.md#deepseek-ocr) |

Leitura honesta dos claims: (i) o leaderboard OmniDocBench v1.5 está
**saturado** (94+ por vários VLMs) — diferenças no topo dizem pouco; (ii) o
Marker avaliado no paper do OmniDocBench era **v0.2.17**, gerações atrás do
1.10.2 que usamos — o score publicado não descreve a ferramenta atual;
(iii) claims fortes valem no domínio do benchmark (Docling brilha em tabela
corporate e cai a 49.87 no READoc; Nougat não transfere para fora do arXiv).
A ponte mais útil: no READoc, **Marker é a melhor pipeline geral** — o que
sustenta tê-lo como PRIMARY do `--qualidade` enquanto MinerU 2.5-Pro (AGPL)
não for re-baselined localmente.

**O que este projeto acrescenta que os benchmarks acima não dão:** separação
perda-de-formato × perda-de-extractor (teto pipe), perfil por elemento com
custo acoplado (roteamento, não ranking), a inversão em figuras vetoriais, e
um corpus GT-por-construção publicável que qualquer um regenera
byte-a-byte — sem depender de anotação humana nem de obras de terceiros.

## 5. Ameaças à validade

1. **Host único e N pequeno** — perfis são "roteamento medido para este
   corpus", não benchmark universal (T091 cross-hardware aberto).
2. **Sintético é born-digital** — render Chrome/Tectonic de templates
   próprios; tabela LaTeX/booktabs, scan e layouts selvagens não cobertos.
3. **Versões**: nossos números são do marker 1.10.2; números externos citam
   outras versões (até v0.2.17) — pontes são qualitativas, não numéricas.
4. **GT-proxy** em docs reais livres (pdftotext -layout como referência de
   conteúdo) mede recall de texto, não fidelidade estrutural.
5. **Métrica ≠ métrica**: TEDS daqui usa normalização de transporte própria
   (documentada); composites externos agregam diferente.

## 6. Conclusão e agenda

O conjunto medido sustenta a tese do roteador: nenhum caminho domina todas
as camadas, e as fraquezas são **complementares** (tabela/math → GPU;
velocidade/figura-vetorial/custo → CPU). Agenda: re-baseline de
MinerU 2.5-Pro, olmOCR-2 e Docling **no nosso corpus sintético público**
(T410 — aí sim comparação direta válida, mesma régua); subset READoc como
ponte externa (Q14); proxies de utilidade de indexação (T092); GT humano
mínimo para WER real ampliado (T060).

---

### Referências externas citadas

- OmniDocBench — [arXiv 2412.07626](https://arxiv.org/abs/2412.07626) (CVPR 2025)
- MinerU 2.5-Pro — [arXiv 2604.04771](https://arxiv.org/abs/2604.04771)
- READoc — [arXiv 2409.05137](https://arxiv.org/abs/2409.05137) (ACL Findings 2025)
- olmOCR-2 — [arXiv 2510.19817](https://arxiv.org/abs/2510.19817)
- Docling — [arXiv 2501.17887](https://arxiv.org/abs/2501.17887) (AAAI 2025)
- Nougat — [arXiv 2308.13418](https://arxiv.org/abs/2308.13418)
- TEDS/PubTabNet — [arXiv 1911.10683](https://arxiv.org/abs/1911.10683)
- DeepSeek-OCR — [arXiv 2510.18234](https://arxiv.org/abs/2510.18234)
