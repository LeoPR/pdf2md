# Panorama de extratores de PDF / OCR (2023–2026) e confronto com o pdf2md

> **Snapshot datado (2026-06-28).** Este é um documento de **referência L2**
> (paisagem datada, trocável — Strata Parte III): o estado-da-arte de OCR/parsing
> de documento se move rápido; trate números e versões como ponto-no-tempo, não
> como verdade atemporal. Levantado por pesquisa web (8 frentes, todas as fichas
> marcadas `verificado` com fontes); reconferir antes de citar como fato.
>
> Alimenta **[T194-F3](../../tickets/research/T194_programa_comparativo_cientifico.md)**
> (concorrentes na mesma régua) e contextualiza
> **[T195](../../tickets/open/T195_roundtrip_prova_fidelidade.md)** (instrumento de
> fidelidade). Motivado pela pergunta dura do autor: *"no que o pdf2md faz sentido
> tendo algo melhor e publicado?"*.

## Por que isto importa para o pdf2md

A ansiedade é legítima e a resposta tem que ser honesta: **como EXTRATOR, o pdf2md
está superado.** A onda 2023→2026 convergiu para VLMs de OCR end-to-end (e VLMs
compactos) que extraem MD/LaTeX/tabela melhor que a cadeia clássica que o pdf2md
orquestra (pdftotext/marker-pinado/pix2tex) — vários com weights abertos e alguns
até CPU-viáveis. O sub-papel "transformar PDF em Markdown indexável" é um `pip
install` de distância. A tese que **sobrevive** é uma só: **nenhum deles PROVA
fidelidade por-documento SEM ground-truth** — todos reportam score agregado de
benchmark e todos são geradores que podem **alucinar texto plausível em silêncio**.
O pdf2md vira, então, **roteador + auditor** que roda EM CIMA desses extratores, não
um concorrente deles.

## Tabela comparativa

| Nome | Ano | Lógica (1 linha) | Implementação | Hardware | Conf. |
|---|---|---|---|---|---|
| **DeepSeek-OCR** | 2025 | VLM 2-partes (DeepEncoder 380M + decoder 3B-MoE/570M ativos); tese de "compressão óptica de contexto" (10 tokens-texto ≈ 1 token-visão) | pip/HF + vLLM; **MIT** (código+weights) | GPU NVIDIA ~7.3GB VRAM FP16; CPU **não** é 1ª classe | verif. |
| **olmOCR-2** (Ai2) | 2025 | Qwen2.5-VL-7B fine-tunado p/ PDF→MD; "unit-test rewards" (RL verificável) no treino | `pip install olmocr` + HF; **Apache-2.0** | **GPU obrigatória** (~12GB+ VRAM); zero CPU | verif. |
| **MinerU2.5** | 2025 | VLM 1.2B coarse-to-fine desacoplado (layout em low-res, conteúdo em crops native-res); + pipeline clássico legado | `pip install mineru` + HF; Apache-derivada c/ extras | VLM = GPU ≥8GB; **pipeline clássico roda em CPU** (qualidade menor) | verif. |
| **Docling + Granite-Docling-258M** (IBM) | 2024–25 | (A) toolkit modular **CPU-first** (layout+TableFormer+OCR)→DoclingDocument; (B) VLM 258M→DocTags | `pip install docling`; **MIT** / Apache-2.0 | Toolkit clássico **CPU-first medido (~0.79s/pág)**; Granite-VLM prefere GPU | verif. |
| **GOT-OCR2.0** | 2024 | VLM 580M end-to-end ("OCR-2.0": todo sinal óptico = caractere); seminal, hoje defasado (~48 olmOCR-bench) | `pip transformers` (classe nativa) + HF; código Apache-2.0 / **dados CC BY-NC** | GPU ~4–6GB; CPU técnico mas lento | verif. |
| **Marker + Surya/Chandra** (Datalab) | 2024–26 | Pipeline multi-estágio virando VLM (Surya-2 650M unifica layout+OCR+tabela; Chandra 9B end-to-end) | pip (marker-pdf/surya/chandra); **código GPL-3.0 / weights OpenRAIL-M (não-comercial)** | Surya-2 CPU-viável mas ~0.1pág/s; Chandra GPU-bound | verif. |
| **Nougat** (Meta) | 2023 | VLM Donut-style (Swin+mBART) image→MD+LaTeX p/ papers; pioneiro, **dormente desde 2023** | `pip nougat-ocr` + HF; código MIT / **weights CC-BY-NC** | GPU ~6GB; **CPU "very slow" + falso [MISSING_PAGE]** | verif. |
| **PaddleOCR-VL 0.9B / dots.ocr 1.7B** | 2025 | VLMs compactos layout+OCR unificado; **PaddleOCR-VL roda em CPU nativo** (109 idiomas, 0.9B) | pip + HF + vLLM/Ollama; **Apache-2.0 / MIT** | **PaddleOCR-VL = único genuinamente CPU-first**; dots.ocr ~3.5GB GPU | verif. |

## Lógica por abordagem (o "como pensam")

- **DeepSeek-OCR** — o novo não é o OCR, é usar a **modalidade visual como codec de
  contexto**: renderiza texto como imagem e comprime ~10 tokens-de-texto em 1
  token-de-visão (DeepEncoder = SAM-80M em série com CLIP-300M + compressor conv
  16×), decoder MoE reconstrói o texto. Lossy por design (97% a <10×, ~60% a 20×) —
  e **não te diz quanto perdeu naquele doc**. Inverso conceitual do pdf2md: ele faz
  texto→imagem como *compressão*; o pdf2md faz imagem→texto→imagem como *falsificação*.
- **olmOCR-2** — VLM (Qwen2.5-VL-7B) fine-tunado com **"unit-test rewards"**: RL onde
  a recompensa é quantos testes determinísticos (estrutura de tabela, fórmula) a
  saída passa. Ataca o MESMO problema do pdf2md (verificar OCR sem humano) pelo lado
  oposto: verificadores no **treino** (com teacher Claude Sonnet 4 + testes
  pré-gerados), não na inferência. "document anchoring" (v1): injeta texto+coords do
  PDF nativo junto da imagem no prompt.
- **MinerU2.5** — coarse-to-fine **desacoplado**: estágio I analisa layout numa imagem
  downsampled (barato); estágio II reconhece conteúdo só em crops de resolução nativa.
  90.67 OmniDocBench com 1.2B. Tem backend pipeline clássico **que roda em CPU**.
- **Docling** — na verdade já é um **orquestrador modular CPU-first** (layout DocLayNet
  + TableFormer + OCR plugável) → DoclingDocument lossless → MD/HTML. É basicamente
  "um roteador CPU-first melhor instrumentado", + o VLM Granite-Docling-258M (DocTags)
  como alternativa end-to-end.
- **GOT-OCR2.0** — tese "OCR-2.0": tratar TODO sinal óptico (texto, fórmula, química
  SMILES, partitura, geometria) como caractere num único VLM generativo. Seminal,
  definiu o paradigma; hoje defasado e propenso a n-gramas repetidos.
- **Marker/Surya/Chandra** — o pipeline que o pdf2md JÁ usa, agora virando VLM (Surya-2
  unifica layout+OCR+tabela em 650M; Chandra 9B end-to-end). **Nota:** o repo usa
  marker *pinado antigo* (conflito pillow<11) — o trade-off CPU-vs-qualidade medido
  aqui está desatualizado frente a Surya-2/Chandra.
- **Nougat** — pioneiro image→MD+LaTeX (Swin+mBART), domínio estreito (arXiv/PMC inglês),
  **alucinação/loops** conhecidos — por isso é o **sujeito-de-teste ideal** do instrumento.
- **PaddleOCR-VL / dots.ocr** — VLMs compactos unificados; **PaddleOCR-VL (0.9B, Apache-2.0)
  é o único genuinamente CPU-first** — ataca direto o flanco "CPU-first" do pdf2md.

## Confronto com o pdf2md

**Onde tornam o pdf2md redundante (eixo extração):** quase todos extraem melhor.
Como "PDF→Markdown indexável", entregam o **eixo-2 (qualidade representacional)** do
pdf2md sozinhos, com ecossistema e benchmark público. **O pdf2md NÃO deve competir
como extrator — esse sub-papel está perdido.**

**Onde o pdf2md ainda faz sentido (a única tese que sobrevive):**

1. **Roteador CPU-first** — defensável, mas **estreitando**: Docling já é um
   orquestrador CPU-first modular (62k stars, MIT), e PaddleOCR-VL roda VLM em CPU.
   O roteamento não é raro nem exclusivo. Sozinho, não é fosso.
2. **Instrumento de prova de fidelidade SEM ground-truth (o único fosso real)** —
   **nenhum dos 8 entrega prova por-documento sem GT.** Todos dão score agregado de
   benchmark (exige dataset rotulado) e todos são VLMs que **alucinam em silêncio**
   (o decoder preenche o que não leu → MD lindo, indexável e inventado). Isso é
   exatamente o **achado-chave do pdf2md**: a alucinação engana o eixo-2 (qualidade),
   o raster engana o eixo-1 (fidelidade) → os dois eixos são conjuntamente necessários.
   O roundtrip-de-imagem 2-eixos é um **verificador/harness que roda EM CIMA de
   qualquer extrator** — e fica MAIS necessário, não menos, conforme o extrator vira
   um VLM falível.

**Onde é FRÁGIL (honestidade obrigatória):**
- **Régua circular?** se a régua (OCR-de-texto, já que o SSIM caiu — T195) tiver os
  mesmos pontos cegos do VLM que audita, o auditor herda o viés do auditado. Risco real.
- **Evidência (T195, ondas 1–2):** o instrumento pegou a falha catastrófica do
  pdftotext no `wilson` (scan, fid=0.076 **sem GT**) **e** — onda 2 — uma **alucinação
  de VLM real**: o Nougat confabulou prosa-matemática fluente sobre o mesmo scan
  (qualidade ALTA, passaria por "MD bom") e o auditor flagrou (fid=0.030, sem GT) onde a
  qualidade seria enganada, sem ser enviesado (credita o Nougat fiel no terreno dele,
  arxiv_math 0.864 > pdftotext). A lacuna "ainda é só tese" está **fechada** no caso
  difícil; falta **ampliar** (mais VLMs da shortlist, N maior) — é o que a shortlist
  abaixo serve para
  testar.
- **CPU-first sozinho perde força** (Docling + PaddleOCR-VL já ocupam o terreno). O
  diferencial tem que ser **roteador + auditor juntos**.

## Convergência conceitual a registrar

- **olmOCR-2 "unit-test rewards"** e o **roundtrip mensurável do pdf2md** atacam o
  mesmo problema (verificar OCR sem confiar no humano) por lados opostos do pipeline —
  eles no treino (com teacher), o pdf2md na inferência (sem teacher, sem GT). Valida a
  direção e mostra que o nicho "auditor em inferência" está **vago**.
- **DeepSeek-OCR** formaliza o inverso da intuição do pdf2md (texto→imagem como
  compressão); os 2 eixos do pdf2md seriam exatamente a métrica que diria se a
  "descompressão óptica" perdeu informação naquele doc.

## Próximo passo (F3): shortlist para confrontar EMPIRICAMENTE na régua sem-GT

Priorizados por (a) implementação aberta e (b) viabilidade de rodar (CPU ou GPU modesta):

1. **Docling (toolkit clássico)** — CPU-first medido, MIT, `pip install docling`; baseline honesto de roteador CPU + produtor de MD para o roundtrip auditar.
2. **MinerU pipeline clássico** — roda CPU-only, `pip install mineru`; saída estruturada para falsificar o instrumento no caminho sem-GPU.
3. **PaddleOCR-VL 0.9B** — único VLM genuinamente CPU-first (Apache-2.0, ~2GB); concorrente direto do eixo CPU-first **e** ótimo sujeito-de-teste (VLM que pode alucinar mas roda em CPU).
4. **Nougat** — leve (~350M), MIT código, offline; alucinação/loops conhecidos = **caso ideal para PROVAR que o roundtrip pega alucinação sem GT**.
5. **GOT-OCR2.0** — classe nativa no Transformers, ~580M, CPU técnico; defasado/propenso a repetição = 2º sujeito-de-teste barato.

## Veredito (resposta dura à pergunta do autor)

Como EXTRATOR o pdf2md está superado — MinerU2.5, olmOCR-2, Surya-2, PaddleOCR-VL
extraem melhor, e vários são CPU-capazes, então nem o flanco "CPU-first" é exclusivo
(Docling e PaddleOCR-VL já jogam aí). O que sobrevive é **uma** coisa: nenhum desses
prova fidelidade por-documento SEM ground-truth — todos dão score de benchmark agregado
e todos alucinam texto plausível em silêncio. O roundtrip-de-imagem 2-eixos é o
auditor/harness que falta a todos eles, e fica MAIS necessário conforme o extrator vira
um VLM falível. Mas isso só é fosso de verdade se (a) o pdf2md **parar de se vender como
extrator** e se reposicionar como roteador+auditor que roda EM CIMA desses modelos, e
(b) **provar empiricamente** que a régua (OCR-de-texto) pega uma alucinação real sem
herdar o viés do que audita. As ondas 1–2 (T195) deram essa evidência: o auditor pegou
falha real **e** alucinação de VLM (Nougat confabulando sobre um scan) sem GT, no caso
difícil (qualidade alta, conteúdo inventado), sem ser enganado em nenhum dos 5 docs.
Falta **ampliar** (mais VLMs da shortlist, N maior) e promover o instrumento.

## Fontes

Levantamento por pesquisa web em 2026-06-28; papers/repos principais por abordagem:
DeepSeek-OCR (arXiv:2510.18234), olmOCR/olmOCR-2 (arXiv:2502.18443, 2510.19817),
MinerU2.5 (arXiv:2509.22186), Docling (arXiv:2501.17887, 2408.09869), GOT-OCR2.0
(arXiv:2409.01704), Marker/Surya (datalab-to, sem paper), Nougat (arXiv:2308.13418),
PaddleOCR-VL (arXiv:2510.14528), dots.ocr (rednote-hilab). Benchmarks citados:
OmniDocBench (CVPR 2025), olmOCR-Bench.
