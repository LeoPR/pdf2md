---
id: T195
titulo: Roundtrip-como-prova — instrumento de fidelidade não-supervisionada em 2 eixos
status: open
criado_em: 2026-06-10
fechado_em:
fase: 4
depende_de: [T065, T070, T092]
blocks: [T194]
tags: [roundtrip, fidelidade, prova, instrumento, ssim, metrica, caixa-preta, moat]
kind: experimento
altitude: execucao
---

## Contexto — a razão de existir do projeto, posta à prova

A identidade defensável do pdf2md não é "mais um extrator" (marker/MinerU/
DeepSeek-OCR/olmOCR dominam extração bruta), e sim **roteador + instrumento
que PROVA fidelidade da extração num PDF sem ground-truth**. Esta prova é o
moat. Este ticket a desafia com critério que pode matar o projeto.

**Princípio (abstrato, ≠ instrumento):** comparar a *imagem da renderização
original* com a *imagem da renderização pós-extração*. O SSIM (pixel_roundtrip,
T070) é só UMA régua dessa comparação — escolhida por ser boa no geral, mas
com falso-negativo conhecido por reflow (extração fiel que reflui → imagem
diferente → SSIM pune). A métrica de comparação é **componente plugável**;
o teto do método não é o teto do SSIM.

**Epistemologia (caixa-preta, decompilador):** não recuperamos o processo que
*criou* o PDF (inacessível); recuperamos uma representação que **recompila ao
mesmo observável** (os pixels renderizados). O que foi extraído REPRESENTA a
informação que regenera a página — ainda que em forma programática/opaca. Isso
é cycle-consistency sobre o invariante observável, não sobre a fonte. A
fidelidade é provada *relativa ao nosso motor de reconstrução* (md→pdf) —
feature delta-E, não bug: prende a representação ao substrato MD legível.

**Os 2 eixos ortogonais (correção que o caso degenerado motivou):**

|  | qualidade ALTA (legível/simbólico/compacto) | qualidade BAIXA (raster/opaco) |
|---|---|---|
| **fidelidade ALTA** (regenera) | extração ótima | "embed-PNG": fiel mas inútil — MEDIDO, não escondido |
| **fidelidade BAIXA** (não regenera) | **alucinação** (parece ok, não confere) | falha total |

O instrumento não é enganado pelo embed-PNG: reporta fidelidade≈1.0,
qualidade≈0.1 — resposta correta ("regenera mas não te dá nada indexável").
O quadrante perigoso (alucinação) é o que benchmark one-shot não pega.

## Hipóteses

- **H1 (calibração — eixo fidelidade):** no corpus sintético (verdade de
  conteúdo CONHECIDA, T065), o score de roundtrip-imagem correlaciona com a
  fidelidade-de-conteúdo real (Spearman ρ ≥ 0.7). Entre as métricas candidatas
  de comparação (SSIM; OCR-nas-2-imagens+sim-de-texto; e ao menos uma 3ª), há
  uma que correlaciona MELHOR que o SSIM — adotada como régua de fidelidade.
- **H2 (eixo qualidade separa degeneração):** um índice de qualidade
  representacional (densidade simbólica / fração não-rasterizada / razão de
  compressão MD-vs-imagem) coloca uma extração degenerada injetada (forçar
  embed-PNG da página) em fidelidade-alta/qualidade-baixa, e uma boa em
  alta/alta — separação ≥ 2 desvios.
- **H3 (discriminação sem GT — o moat):** em PDFs reais (sem GT), o instrumento
  detecta uma degradação CONTROLADA (dropar 30% do texto da extração antes de
  reconstruir) como queda de fidelidade ≥ X (limiar fixado na calibração),
  SEM usar nenhum ground-truth — e separa pdftotext de marker de forma coerente
  com um spot-check humano pequeno.

## Resultados — onda 0 (2026-06-28, lab/e28_roundtrip_prova, .venv)

Calibração no sintético (11 docs: prosa/tabela/formula; 68 pares doc×variante;
1 renderer Chrome+KaTeX). Réguas de fidelidade candidatas comparadas img(ref)×
img(var); fidelidade-de-conteúdo CONHECIDA medida no espaço MD contra o GT
(`tok_recall` ordem-insensível, `seq_sim` ordem-sensível). Robustez em
`robustness.py` + revisão adversarial independente.

**Achado forte (não-trivial): SSIM é FALSIFICADO como régua de fidelidade de
conteúdo.** ρ(SSIM, tok_recall)=+0.05; ρ(SSIM, seq_sim)=+0.49 — às vezes
negativo ao remover o contraste fácil. Duas métricas pixel-derivadas divergindo
desse jeito é evidência real: similaridade estrutural de pixels mede LAYOUT, não
conteúdo. → a régua de fidelidade do instrumento NÃO deve ser SSIM cru.

**OCR-de-texto rastreia conteúdo (com ressalvas de magnitude):**
ρ(ocr_jacc, tok_recall)=+0.82; ρ(ocr_seq, seq_sim)=+0.84; leave-one-doc-out
estável ([0.80,0.84] e [0.82,0.91]). MAS a magnitude ≥0.7 é *swap-driven* (cai
p/ 0.71 sem a variante swap) e o label `tok_recall` SATURA na prosa repetitiva
do sintético (variância ~0). Honesto: "OCR>SSIM, sinal robusto; magnitude
inflada pelo contraste fácil + label saturado" — NÃO "ρ=0.82 calibrado".

**Os 2 eixos são CONJUNTAMENTE necessários (correção da narrativa ingênua do
ticket acima, que dizia embed-PNG→fidelidade≈1.0 "resposta correta"):** na régua
ADOTADA (OCR), o `embed_png` é *enganosamente fiel* (ocr_jacc=0.69 > drop50/75=
0.64 >> swap=0.37) — o Tesseract lê o texto DA imagem rasterizada. Logo o
EIXO-1 (fidelidade) NÃO pega o raster; só o EIXO-2 (qualidade — `embed_png` é o
mínimo global, 2.6σ < bom) pega. Inversamente, a alucinação (`swap`, conteúdo
errado) é pega pelo EIXO-1 (fid 0.37) e NÃO pelo eixo-2 (qual alta — é MD
bem-formado). Nenhum eixo sozinho separa os dois degenerados ⇒ **nunca colapsar
fidelidade+qualidade num escore único.** Isto PROVA a tese dos 2 eixos (em vez
de assumi-la). Por-doc: 0 contra-exemplos (margem alucinação: min fid(identity)=
0.93 vs max fid(swap)=0.64 → separável).

**Status das hipóteses:**
- H1 — PARCIAL. SSIM falsificado (forte); OCR rastreia (sinal robusto, magnitude
  com caveat). "A régua" ainda SUBESPECIFICADA: `ocr_jacc`↔conjunto vs
  `ocr_seq`↔ordem discordam (Δρ~0.56) — fixar alvo antes da onda 1.
- H2 — PASSA, porém o eixo-2 carrega SOZINHO a defesa contra o raster (não o
  eixo-1, como o desenho ingênuo sugeria).
- H3 — não tocada (é onda 1).

**Limites de envelope (registrar honestamente):**
- `corrupt` (1 dígito trocado na fórmula) é invisível ATÉ ao label
  (`tok_recall=seq_sim=1.0`) e a todas as réguas → onda 0 dá ZERO evidência
  sobre detecção de erro semântico de math (o perigo real em fórmula).
- onda 0 é **same-engine** (ref e var saem do mesmo `md_to_pdf`); o real é
  **cross-engine** (ref = rasterização do PDF original, fonte serif/2-col/ruído ≠
  motor da reconstrução). O caminho de OCR cross-engine NÃO foi exercido aqui —
  é exatamente o teste da onda 1.
- N pequeno (11 docs), 1 renderer, prosa quasi-clonada.

**Decisão:** seguir p/ onda 1 como EXPLORAÇÃO (o teste de verdade é o
cross-engine sem GT), NÃO como "instrumento calibrado". Pré-requisitos antes de
clamar qualquer coisa: (a) fixar régua+alvo de fidelidade; (b) reportar a
magnitude com os caveats swap/saturação; (c) tratar fidelidade+qualidade como
par indissociável no `fidelity_report()`.

## Resultados — onda 1 (2026-06-28, lab/e28_roundtrip_prova/wave1.py, .venv)

Teste de verdade do moat: 5 PDFs REAIS (corpus/examples), **cross-engine, sem
GT**. Referência = rasterização nativa do PDF real; variante = md_to_pdf(extração
pdftotext). Régua FIXADA (pré-req da onda 0) = **ocr_jacc** (fidelidade-de-conjunto,
robusta a reflow). Arms: pdftotext · drop30/drop60 (degradação controlada) ·
embed_png.

**Achado-headline (o moat funcionando): o instrumento pegou uma falha
catastrófica de extração SEM nenhum GT.** `wilson_mathematics_excerpt` é um PDF
ESCANEADO (563 chars de texto em 2 pg, 4 imagens) — pdftotext não tem o que
extrair; o instrumento reportou **fid(jacc)=0.076**, sinalizando corretamente
"esta extração não regenera o observável". Primeira evidência concreta de
detecção de falha sem ground-truth.

**H3 — PARCIAL (envelope claro):**
- monotonia fid(pdftotext) ≥ drop30 ≥ drop60: **4/5** docs. Margens: drop30
  +0.043 (min **−0.058**), drop60 +0.192.
- **FORTE** em prosa acadêmica reflowável: arxiv 0.949→0.834→0.471 (drop limpo,
  margem grande); arxiv_math 0.830→0.707→0.564.
- **FRACO/quebra** em form-template: `irs_f1040` é **NÃO-monotônico** (drop30
  0.643 > pdftotext 0.585) — o observável do formulário é dominado pelo template
  (rótulos fixos), não pelos dados dropados → a régua não enxerga a perda.
- **SATURA** em relatório redundante: `cdc` drop30 margem só 0.025 (vocabulário
  redundante em 5 pg; mesma saturação da prosa sintética da onda 0).

**Confirma as escolhas de régua (medido no real):**
- SSIM cross-engine é **inútil**: μ=0.583 e — pior — embed_png SSIM (0.715) >
  pdftotext (0.631) no arxiv: o SSIM **ranquearia o raster como MAIS fiel** que a
  extração boa. Régua tem de ser OCR-texto.
- ocr_seq é punido por reflow 2col→1col (cdc: jacc 0.694 vs seq 0.471) → em
  cross-engine a régua é **ocr_jacc** (conjunto), não ocr_seq (ordem).
- eixo-2 pega o raster: qual(pdftotext) μ=1440 vs qual(embed_png) μ=4.

**O que falta p/ fechar o moat:** pegar uma **alucinação de VLM** (caso mais
difícil que a falha-vazia do wilson — texto plausível mas inventado), não só
falha catastrófica. É a próxima onda, ligada ao
[panorama de extratores](../../docs/reference/panorama_extractores_ocr.md) +
[T194](../research/T194_programa_comparativo_cientifico.md)-F3: rodar um extrator
VLM CPU-viável da shortlist (PaddleOCR-VL / Nougat — conhecido por alucinar) na
régua e ver se o instrumento o desmascara. **Envelope honesto já medido:** o
instrumento discrimina bem em doc text-bearing reflowável e pega falha grosseira;
é cego/não-monotônico em form-template e satura em doc redundante.

## Resultados — onda 2 (2026-06-28, lab e28 nougat_run.py + wave2.py)

O teste decisivo do moat: confrontar um VLM de OCR que **alucina** (Nougat,
`facebook/nougat-base` via transformers no venv do marker — GPU, saída CRUA sem
`post_process_generation`, que removeria as repetições que queremos ver) e medir,
**sem GT**, se o auditor pega a alucinação. Régua = `ocr_jacc` cross-engine (onda 1).

| doc | fid pdftotext | fid Nougat | qual Nougat | rep Nougat | leitura (spot-check) |
|---|---:|---:|---:|---:|---|
| arxiv_excerpt | 0.949 | 0.883 | 996 | 0.56 | Nougat fiel (título/autores reais) |
| arxiv_math | 0.830 | **0.864** | 1607 | 0.70 | **Nougat MAIS fiel** (terreno dele) — auditor credita |
| cdc | 0.694 | 0.582 | 2079 | 0.69 | Nougat moderadamente pior (OOD multi-col) |
| irs | 0.585 | **0.002** | 263 | **0.96** | **loop degenerado** (`# [ [ [ …`) |
| wilson (scan) | 0.076 | **0.030** | **502** | 0.72 | **alucinação fluente** (prosa-math plausível, inventada) |

**H4 CONFIRMADO no caso DIFÍCIL (wilson):** num scan que não conseguiu ler, o
Nougat **confabulou** prosa-matemática fluente e bem-formada — *"Release the given
number of the regions it by the rules in Reduction, then multiply the scenario…"* —
que **passaria num check "é MD bom"** (qual=502, ênfases, sem garbage óbvio), mas é
pura invenção. O **eixo-1 (fid=0.030, cross-engine, SEM GT) pegou** exatamente onde o
eixo-2 (qualidade) seria enganado. É a materialização, num VLM REAL, do quadrante
perigoso da onda 0 (alucinação engana qualidade, fidelidade pega) — os 2 eixos juntos
são o que separa. O irs (loop, fid 0.002) é o caso ÓBVIO; o wilson é o caso que prova
o moat.

**Auditor NÃO é enviesado contra VLM:** credita a fidelidade real do Nougat no
terreno dele (arxiv_math 0.864 **>** pdftotext 0.830). Logo "fid baixa" significa
infidelidade real, não "penalidade Nougat".

**Sem circularidade / sem engano:** em NENHUM dos 5 docs a alucinação do Nougat
marcou fid alta; o ranking do auditor bateu com o spot-check manual nos 5. O risco de
régua-circular (auditor herdar o viés do auditado) que a revisão adversarial apontou
**não se materializou** neste conjunto.

**Caveats honestos:** (1) a heurística automática de H4 (qual alta + fid<pdftotext)
**super-sinaliza** — marcou arxiv/cdc, que o spot-check mostra fiéis; o árbitro é o
spot-check, não a heurística. (2) N pequeno (5 docs, 1 VLM, 1 host). (3) `rep_ratio`
~0.68 é normal em prosa (palavras comuns repetem); só ~0.96 (irs) é loop inequívoco —
não é discriminador limpo fora do extremo; a **fidelidade** é o sinal real.

**Decisão:** o moat saiu de **tese** para **evidência medida**. O auditor de fidelidade
sem-GT detecta alucinação de VLM real no caso difícil (qualidade alta, conteúdo
inventado) e credita fidelidade real — fechando a lacuna que o
[panorama](../../docs/reference/panorama_extractores_ocr.md) apontava ("ainda é tese").

**Replicação cross-VLM (onda 2b — GOT-OCR2.0, mesmo venv/zero-install):** a conclusão
NÃO é específica do Nougat. 2º VLM, arquitetura e modos de falha distintos, mesmos 5 docs:

| doc | fid pt | fid Nougat | fid GOT | qual GOT | leitura GOT (spot-check) |
|---|---:|---:|---:|---:|---|
| arxiv_math | 0.830 | 0.864 | 0.823 | 1720 | fiel (terreno dele) — auditor credita |
| cdc | 0.694 | 0.582 | 0.677 | 2781 | fiel-ish |
| arxiv_excerpt | 0.949 | 0.883 | 0.649 | 670 | perdeu a capa (pg0 só 209c) → fid cai |
| wilson (scan) | 0.076 | 0.030 | 0.031 | 772 | **alucinação garbada** (qual alta, fid ~0) |
| irs (form) | 0.585 | 0.002 | 0.082 | 1243 | rich-but-wrong (labels reais + `\section` espúrio + loop rep 0.91) |

GOT replica o H4: nos OOD (wilson, irs) produz saída de **qualidade alta** (772/1243 —
parece MD rico) mas **infiel** (fid 0.031/0.082), e o auditor flagra SEM GT; credita a
fidelidade real no terreno dele (arxiv_math 0.823 ≈ pdftotext 0.830). Em **nenhum dos 10
casos** (5 docs × 2 VLMs) a alucinação marcou fid alta. Texturas de falha distintas
(Nougat: confabulação fluente + loop `[`; GOT: OCR garbado + `\section` repetido) — todas
pegas pela FIDELIDADE, não pela qualidade. **Evidência do moat: N=2 VLMs.**

**Próximo:** generalizar `fidelity_report()` promovível (T194-F3); opcional ampliar p/
PaddleOCR-VL (CPU-first) p/ N=3.

## Método (ondas)

1. **Onda 0 — régua e calibração (sintético, barata, CPU):** reusar
   `pixel_roundtrip` (SSIM+align) e adicionar 1-2 métricas de comparação
   candidatas (OCR-Tesseract nas 2 imagens + token-sim; opcional perceptual).
   Para cada doc do sintético: fidelidade-conteúdo conhecida (do GT) × cada
   métrica de roundtrip → correlação. Computar o eixo qualidade. Injetar
   degeneração embed-PNG e degradação-30%. Escolher régua de fidelidade +
   fixar limiares. **Decide H1/H2 antes de tocar em PDF real.**
2. **Onda 1 — discriminação no real (sem GT):** PDFs `corpus/examples` (arxiv,
   cdc, irs, wilson) + diversos. pdftotext vs marker → posicionar no plano
   2-eixos. Degradação controlada → o instrumento pega sem GT? Spot-check
   humano de 4-6 casos confirma o ranking? **Decide H3.**
3. **Onda 2 (condicional, só se H1-H3 passam):** generalizar o instrumento
   como `fidelity_report()` promovível e ligá-lo ao T194-F3 (rodar a saída de
   QUALQUER extrator — marker/MinerU/etc. — no mesmo plano; é assim que se
   gera a evidência que falta sobre outros extratores).

## Métricas

- Fidelidade: a régua vencedora da onda 0 (SSIM ou melhor), em [0,1].
- Qualidade representacional: índice composto (fração de área não-rasterizada
  do output; densidade de tokens simbólicos vs página; razão bytes-MD/bytes-se-
  fosse-imagem). Reusa structure-counts do e26/T092.
- Correlação fidelidade↔verdade-conhecida: Spearman/Pearson no sintético.
- Sensibilidade: queda de fidelidade sob degradação-30% (efeito mensurável).

## Critério de promoção

Régua de fidelidade calibrada (correlação ≥0.7 no sintético) + eixo qualidade
que separa degeneração + detecção de degradação sem GT no real ⇒ `fidelity_
report()` vira módulo/lab promovível, coluna nos profiles, e **base do T194-F3**
(referee de extratores externos). O projeto ganha sua prova de valor.

## Critério de descarte (pode matar o moat — registrar honestamente)

- Se NENHUMA métrica de comparação correlacionar com a verdade conhecida no
  sintético (ρ<0.7 em todas) ⇒ o roundtrip-imagem não mede fidelidade de
  conteúdo; o moat como "prova" cai (vira no máximo smoke-test de layout).
- Se o eixo qualidade não separar embed-PNG de extração boa ⇒ o instrumento é
  enganável; precisa redesenho antes de qualquer claim.
- Se no real o instrumento não distinguir extração boa de degradada-30% ⇒ sem
  poder discriminativo onde importa (PDF sem GT). Registrar o envelope: pode
  valer só em doc texto-pesado e ser cego em foto-pesado (limite conhecido).

## Deps

Zero pip novo no núcleo: pixel_roundtrip (extra `[rtpixel]`, já existe),
Tesseract (external, `[ocr]`) p/ a métrica OCR-based, corpus sintético (T065),
structure-counts (e26). marker p/ a onda 1 (GPU já em uso). Bancada efêmera
`lab/e28_roundtrip_prova/`.

## Não-objetivo

- Recuperar o processo gerador original do PDF (inacessível por design —
  caixa-preta; só provamos recompilação ao observável).
- Treinar uma métrica perceptual nova (usar prontas; calibrar a ESCOLHA).
- Cobrir foto-pesado como caso forte (registrar como borda do envelope).
- Ranking público de extratores externos (isso é T194-F3, ALIMENTADO por aqui).

## Conexão

- Endurece o princípio de [T070](../research/T070_pixel_roundtrip_validador_visual.md)
  (pixel-roundtrip) de "validador visual" para "instrumento de prova de
  fidelidade não-supervisionada em 2 eixos".
- Usa o GT-por-construção do [T065](../closed/T065_corpus_gt_sintetico.md) p/
  calibrar a régua (a verdade conhecida que falta no real).
- Reusa eixo de qualidade/densidade do [T092](../closed/T092_indexacao_utility_proxies.md).
- É a fundação do [T194](../research/T194_programa_comparativo_cientifico.md)-F3:
  só com o instrumento provado dá pra rodar marker/MinerU/DeepSeek-OCR na nossa
  régua e gerar a evidência que hoje falta sobre outros extratores.
- Materializa a tese decompilador/recompilador do
  [transmutos.md](../../docs/explanation/transmutos.md).
