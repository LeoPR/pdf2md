---
id: T194
titulo: Programa comparativo científico — pureza das cadeias, métricas canônicas, concorrentes na mesma régua, envelope de recursos
status: open
criado_em: 2026-06-10
fechado_em:
fase: 4
depende_de: [T065, T075, T092]
blocks: []
tags: [comparativo, metricas, cdm, benchmark, recursos, auditoria, planejamento]
kind: pesquisa
altitude: planejamento
---

## Por quê (pedido do autor, 2026-06-10)

(1) Verificar que as transformações não têm nada embutido (acionamento oculto
de outras ferramentas/rede); (2) comparar nossas métricas com as CANÔNICAS e
exigir firmeza científica das alegações de terceiros — *quais documentos eles
avaliam?*; (3) construir um comparativo conciso (visão ampla + drill-down que
diga ONDE atacar); (4) crítica dura ao propósito do projeto vs quem entrega
similar; (5) precisão sobre a inovação do roundtrip; (6) envelope de recursos
(máquina menor, bordas). Este ticket é o PLANO; cada fase vira bancada/ticket
de execução ao ser disparada.

## F0 — Auditoria de pureza das transformações

**Já verificado (2026-06-10, grep no src/):** nenhum `urllib/requests` no
pacote; o único `socket` é DETECÇÃO do daemon ollama local (127.0.0.1:11434,
timeout 0.5s) — não aciona nada; marker é invocado SEM `--use_llm` (zero LLM
embutido); mermaid é vendorado (offline); pesos de marker (HF) e pix2tex são
download-on-demand DOCUMENTADO (1ª execução).

**Suspeita CONFIRMÁVEL (achado da auditoria):** `pdfs.py` roda pandoc com
`--katex` SEM URL + `--embed-resources` → o default do pandoc é o **CDN** do
KaTeX, e o embed-resources baixa da rede **a cada conversão** ⇒ o md→pdf NÃO
é offline (alegação do README parcialmente falsa). O mermaid foi vendorado no
T190; o KaTeX não.

Plano de execução:
1. **Teste de rede-zero** por cadeia (firewall/HF_HUB_OFFLINE=1): matriz
   `cadeia × roda-offline?` — pdf→md CPU, pdf→md GPU, md→pdf (±mermaid),
   cropper+pix2tex, OCR.
2. Se confirmado: **vendorar KaTeX** (modelo do mermaid/T190) ou
   `--katex=<path local>`; atualizar claims.
3. **Manifesto de cadeias** (`docs/reference/cadeias.md`): cada transformação
   com a árvore COMPLETA de ferramentas/versões/pesos/origem (marker =
   Surya layout+OCR+Texify+tables; pdftotext = PyMuPDF; md→pdf =
   pandoc+Chrome+KaTeX+mermaid-vendorado) — proveniência já grava versões;
   estender a pesos/checksums.
4. `pdf2md doctor` ganha capability **offline-strict** (testável).

Critério: todo claim "offline" do README tem teste de rede-zero verde
correspondente.

## F1 — Métricas: mapear as nossas ↔ canônicas e adotar adaptadores

| dimensão | nossa régua | canônica (quem usa) | gap/ação |
|---|---|---|---|
| texto | token-sim (difflib); WER vs GT | Normalized Edit Distance (OmniDocBench); EDS (READoc) | adaptador NED (barato) |
| fórmula | `latex_sim` (difflib sobre tokens) | **CDM** (arXiv 2409.03643; render-based, casa caracteres na IMAGEM) | nossa régua é sensível à representação (`\left[\begin{array}` vs `bmatrix` — fraqueza já documentada no profile pix2tex); CDM elimina isso e é filosoficamente alinhada ao nosso eixo pixel. **Adotar.** |
| tabela | TEDS/TEDS-S (impl. canônica PubTabNet) | idem (OmniDocBench/READoc) | ✓ já canônica; manter normalização de transporte documentada |
| reading order | (nada) | KTDS (READoc, Kendall-τ) | gap real — multi-coluna; adicionar casos no sintético v1.2 |
| visual | SSIM page-level + drift multi-iteração | (sem canônica em parsing) | diferencial nosso; cruzar com CDM |

Critério: relatório por categoria nas DUAS réguas no sintético; correlação
alta ⇒ tradução documentada; baixa ⇒ investigar antes de qualquer claim.

## F2 — Corpus de comparação: o que cada um avalia (firmeza das alegações)

Composição dos corpora por trás dos números publicados (pesquisado):

| benchmark | documentos avaliados | GT | métricas |
|---|---|---|---|
| OmniDocBench (CVPR'25) | 1.355 págs, ~20k blocos, **9 tipos** (academic, textbook, slides, financial, news, handwriting...), zh+en; Hard subset 296 págs | anotação humana end-to-end | NED + TEDS + CDM (composite) |
| READoc (ACL'25) | **3.576 docs**: arXiv 1.009 (média 11,7 pg), GitHub 1.224, Zenodo 1.343 | derivado da FONTE (LaTeX/HTML→md) | EDS + TEDS + KTDS |
| olmOCR-Bench | 1.400 docs / 7k+ unit tests | testes de presença de fato | pass-rate |
| FinTabNet (claim Docling 0.97) | tabelas de relatórios financeiros (S&P) | da fonte | TEDS |
| **nosso sintético** | 75 docs, 8 categorias, 2 renderers | por construção (byte-exato) | as de F1 |

Plano: (a) tabela acima entra no `avaliacao.md` §4 ("o que foi avaliado");
(b) rodar LOCALMENTE OmniDocBench-en subset + READoc-arXiv subset como
terreno neutro (licenças research-friendly; Q14 já previa); (c) **sintético
v1.2**: vocabulário rico (mata a colisão BM25 do e26), variantes raster,
eixo CM em todas as categorias, casos de reading-order (2 colunas).

Critério: nenhum número comparativo sem corpus+N+métrica declarados; proibido
comparar células de benchmarks diferentes.

## F3 — Concorrentes na mesma régua → o comparativo conciso

**Pré-requisito: [T195](../open/T195_roundtrip_prova_fidelidade.md)** — o
instrumento de fidelidade não-supervisionada PROVADO. Só com ele dá pra rodar
a saída de qualquer extrator externo na nossa régua sem GT. Sem T195, F3 é
"comparar contra GT que não temos".
**Status 2026-06-28:** T195 onda 0+1 deram a 1ª evidência (o instrumento pegou
falha catastrófica do pdftotext no `wilson` escaneado, fid=0.076, **sem GT**) e
fixaram a régua cross-engine = **ocr_jacc**. Gate restante p/ destravar F3 de
verdade: provar que pega **alucinação de VLM** (não só falha-vazia).

**Paisagem dos concorrentes levantada:**
[docs/reference/panorama_extractores_ocr.md](../../docs/reference/panorama_extractores_ocr.md)
(8 frentes, 2023-2026, `verificado`). Veredito honesto: como EXTRATOR o pdf2md
está superado; o que sobrevive é roteador + **auditor de fidelidade sem-GT** (que
NENHUM dos 8 entrega).

Rodar na MESMA máquina, MESMOS corpora (sintético v1.2 + subsets F2), MESMAS
métricas (F1 + os 2 eixos do T195), telemetria ligada (custo JUNTO da
qualidade — o eixo que os benchmarks não publicam). **Shortlist priorizada (do
panorama, por implementação aberta + viabilidade CPU/GPU-modesta):**
Docling toolkit (MIT, CPU-first medido), MinerU pipeline clássico (CPU-only),
**PaddleOCR-VL 0.9B** (único VLM CPU-first — desafia DIRETO o flanco CPU e é
sujeito-de-teste de alucinação), **Nougat** (alucinação/loops conhecidos — caso
ideal p/ provar que o roundtrip pega alucinação), GOT-OCR2.0 (2º sujeito barato);
olmOCR-2/MinerU2.5-VLM se couber em GPU (senão registrar como borda, não omitir).

Saída "ampla→detalhe" (`docs/reference/comparativo.md`, gerado de RESULT.json):
1 página com matriz elemento×ferramenta em bandas, e drill-down por elemento
com custo (s/pg, RAM, VRAM) + casos de falha → **backlog priorizado de
ataque** (o "onde melhorar" vira lista ordenada por ganho/custo).

## F4 — Envelope de recursos (máquina menor, bordas)

Medido hoje (1 host): pdftotext 63MB/0 VRAM; tesseract ~124MB; pix2tex
~800MB CPU; marker GPU-required ~3.4GB VRAM; teto `--low-resource` 160MB.
Plano:
1. Bordas por contenção REAL: `docker --memory={256m,512m,1g,2g}` (ou Job
   Objects) × cada caminho → matriz roda/degrada/morre + curva
   qualidade×recurso (hoje o teto 160MB é política, não borda medida).
2. GPU mínima do marker: VRAM 4/6/8GB — onde quebra (máquina T091 ou cap).
3. Teste duro falsificável: Granite-Docling-258M (CPU, <8GB RAM?) vs nosso
   pdftotext+cropper+pix2tex — se ele ganhar math no CPU com custo similar,
   nosso caminho CPU perde a razão de ser e o roteador deve adotá-lo.
4. Cross-hardware (T091): repetir perfis em 1 máquina menor; validar f(n).

Critério: profiles/README com "requisitos mínimos MEDIDOS por caminho".

## F5 — Posição e inovação (insumo p/ crítica dura no avaliacao.md)

Pré-registro do que é e do que NÃO é novo (falsificadores incluídos):
- **Intent-routing NÃO é novo**: Unstructured `auto/fast/hi_res/ocr_only` é
  roteamento página-a-página custo×qualidade com adoção massiva. Delta nosso
  (a defender com F3): perfis MEDIDOS e publicados por elemento, degradação
  honesta gravada na proveniência, roteamento por SUB-elemento, doctor.
- **GT-da-fonte NÃO é novo**: READoc deriva GT de LaTeX/HTML de terceiros;
  PubTabNet de XML. Delta nosso: fonte ESCRITA por nós (zero copyright,
  redistribui INCLUSIVE renders), dois renderers (delta-E), e o reconstrutor
  é o do PRÓPRIO produto (bidirecionalidade operacional, não só avaliação).
- **Cycle-consistency é princípio antigo** (CycleGAN, back-translation);
  em parsing, READoc REJEITA roundtrip por "viés do reconstrutor". Nossa
  resposta técnica (a manter explícita): (a) pixel-roundtrip SSIM pega o que
  o textual perde; (b) multi-iteração mede DRIFT que avaliação one-shot não
  vê; (c) GT-por-construção quebra a circularidade (a fonte é verdade
  externa ao extractor); (d) teto-de-transporte separa formato de extractor
  — resposta direta ao viés. Falsificador: paper de doc-parsing com
  roundtrip+pixel+drift ⇒ reescrever claim como replicação.
- Sem prior art encontrado até agora: separação teto-de-transporte;
  perfil elemento×custo acoplado para routing; inversão diagrama/logo como
  insumo de roteamento. (Busca dirigida em F5 antes de qualquer publicação.)

## Ordem, riscos, descarte

F0 → F1 (CDM primeiro) → F2/F3 em ondas → F4 em paralelo (barato) → F5 fecha
no `avaliacao.md`. Riscos: spend de GPU-tempo (limitar por onda); AGPL do
MinerU (venv isolado, sem vínculo de código); olmOCR-2 pode não caber em
12GB (vira linha "borda de hardware" no comparativo). Descarte por fase: se
CDM não rodar local (deps), manter latex_sim com a limitação declarada; se
subsets externos tiverem fricção de licença, comparativo fica no sintético +
nota de não-comparabilidade (nunca números de papers lado a lado como se
fossem nossos).

## Conexão

- Consolida [T065](../closed/T065_corpus_gt_sintetico.md) /
  [T075](../closed/T075_tabelas_teds.md) /
  [T092](../closed/T092_indexacao_utility_proxies.md) e absorve o escopo do
  [T410](T410_testar_ferramentas_alternativas_nougat_mineru_pdftotext.md)
  (re-baseline) e do Q14/READoc; alimenta
  [avaliacao.md](../../docs/explanation/avaliacao.md) e T091 (cross-hardware).
