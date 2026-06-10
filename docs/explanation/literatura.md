# Literatura — revisão para `pdf2md`

> **Compilado contínuo (snapshot 2026-05-16).** Fichas catalográficas
> detalhadas em [`../reference/biblioteca/`](../reference/biblioteca/INDEX.md).
> Histórico de versões anteriores (v1 e v2 separadas) consolidado neste
> documento — git log preserva (`git log -- docs/LITERATURA*.md`).
>
> Estrutura: §1 alucinação · §2 round-trip · §3 ecosystem PDF→MD · §4
> AcroForm · §5 métricas novas · §6 implicações p/ pdf2md · §7
> atualização pós-labs e09-e14 (v0.5-v0.7).

---

## Sumário executivo

Em 4 experimentos do `lab/` identificamos um padrão de degradação no qual o round-trip (MD₁ → PDF → MD₂) **alucina** quantidades enormes de conteúdo quando o input é esparso — Wilson 1800 (scan_image_only) inflou de 2.748 → 21.177 tokens (7.70×) e IBM Quantum lesson 1 (slides) de 4.629 → 15.637 tokens (3.38×). A heurística T071 flagra `bloat > 3.0` OU (`bloat > 2.0` E `densidade < 200 tok/pág`).

Conclusão da busca: **o fenômeno geral é conhecido na literatura** (chamado *OCR hallucination*, *phantom content*, *visual ungrounding*) e foi formalizado em papers de 2024–2026, mas **a forma específica que detectamos — alucinação amplificada *no re-OCR de uma reconstrução limpa* — não tem nome consolidado**. Os trabalhos cobrem ou (a) VLM alucinando *na primeira passada* sobre input degradado (Shah et al., *Seeing is Believing*, NeurIPS 2025), ou (b) detecção de hallucination via *consenso entre múltiplos modelos* (Zhang et al., *Consensus Entropy*, arXiv 2504.11101, 2025), mas a alucinação induzida pelo *próprio pipeline simétrico* sobre um documento legítimo mas esparso não aparece em publicação revisada. Isso valida T071 como contribuição metodológica original do projeto.

Em termos de **ferramentas**, o cenário mudou substantivamente desde v1: MinerU2.5-Pro (abril 2026, OmniDocBench v1.6 = 95.69) e Granite-Docling-258M (set. 2025, F1 0.968 em equações) são novos baselines a considerar; olmOCR-2 (out. 2025) introduziu RL com unit tests como reward; DeepSeek-OCR, dots.ocr, PaddleOCR-VL e GLM-OCR (todos out./nov. 2025) saturam o leaderboard de OmniDocBench v1.5 em 94+. Quanto a métricas, dois trabalhos novos rebaixam CDM: Horn & Keuper (arXiv 2512.09874, dez. 2025) mostram que **LLM-as-judge (r=0.78) correlaciona ~2× melhor com humanos do que CDM (r=0.34)** em fórmulas matemáticas.

---

## 1. Padrão de alucinação em re-extração / OCR

### 1.1 Termos técnicos da literatura

O fenômeno que detectamos cai em várias categorias relacionadas mas distintas:

- **OCR hallucination** ([Shah et al., *Seeing is Believing? Mitigating OCR Hallucinations in Multimodal Large Language Models*, NeurIPS 2025](https://arxiv.org/abs/2506.20168)) — VLMs que sofrem com inputs degradados (blur, oclusão, contraste baixo) tendem a substituir percepção visual por *linguistic priors*, produzindo conteúdo plausível mas inexistente. Apresentaram o **KIE-HVQA**, primeiro benchmark dedicado, com 400 amostras anotadas pixel-level para "reliability of OCR" em IDs, recibos e faturas degradados. Mitigação via GRPO com reward que recompensa "refusal to answer" em regiões ambíguas → 22% absoluto de melhora sobre GPT-4o.
- **Visual ungrounding / language prior over-reliance** ([Datature, 2025](https://datature.io/glossary/hallucination-in-vision-language-models)) — VLMs com arquitetura encode-then-decode confiam mais no decoder textual do que no encoder visual quando o sinal visual é fraco. Esse é o mecanismo subjacente provável do nosso caso: o pandoc+Chrome+KaTeX produz um PDF *visualmente esparso* (página com 50 tokens), e o re-OCR preenche o "vazio percebido" com formulações típicas do corpus de treino do Surya/Marker.
- **Repetition hallucination** ([Blecher et al., Nougat 2308.13418](https://arxiv.org/abs/2308.13418), §B.3) — caso degenerativo: Transformer com greedy decoding entra em loop, repetindo última sentença. Detectado em 1.5% das páginas in-domain e muito mais em out-of-domain. Nougat usa heurística baseada em **variance dos logits numa janela deslizante** (threshold 6.75 nos últimos 200 tokens) para parar geração precocemente.
- **Risk-controlled OCR / verifiability** ([*From Plausibility to Verifiability: Risk-Controlled Generative OCR with Vision-Language Models*, arXiv 2603.19790](https://arxiv.org/html/2603.19790v3)) — framework geral: tratar OCR via VLM como "seletivo aceitar/abster", com *geometric risk controller* que probe múltiplas vistas estruturadas da entrada e só aceita transcrição quando consenso e estabilidade entre vistas batem threshold pré-definido. Conceitualmente alinha-se com nossa heurística T071 (count-based pre-filter).

### 1.2 Conexão com T071

A heurística que implementamos (`bloat > 3.0` OU `bloat > 2.0 ∧ densidade < 200`) é, na taxonomia da literatura, um **detector simples de OCR hallucination baseado em length-ratio**. Não encontramos evidência de que essa razão específica tenha sido proposta antes:

- A literatura usa **perplexity** ([Lowest Span Confidence, arXiv 2601.19918](https://arxiv.org/html/2601.19918)) e **length-normalized predictive entropy** (LN-Entropy) para hallucination em LLMs, mas não para OCR/VLM.
- O sinal length-ratio aparece como *acceptance threshold* prático em pipelines de OCR (Tesseract, ocrmypdf — ver discussão geral em [Datalogics 2025](https://www.datalogics.com/blog-extract-text-from-pdf-2025)), mas sempre como "se MD₁ < N chars, fallback para OCR mais robusto", nunca como detector de *amplification* num round-trip.
- A **Consensus Entropy** (§5.1) é a abordagem rigorosa para o mesmo problema, mas requer múltiplos VLMs simultaneamente.

**Validação operacional**: T071 funciona porque o regime que pegamos é especificamente o de **input legítimo mas esparso** (não degradado por blur ou oclusão como no KIE-HVQA). É um nicho que a literatura ainda não cobre formalmente, e nossa heurística simples (1 número, 1 threshold) é defensável como contribuição prática.

### 1.3 Mitigações conhecidas

- **Constrained decoding (OCR-token-restricted vocabulary)** — falhou na prática: VLMs persistem em gerar tokens ausentes do input visível ([Roots.ai, GutenOCR 2026](https://arxiv.org/html/2601.14490v1)). Não recomendado.
- **Cross-view consensus / multi-VLM agreement** — Consensus Entropy mostra F1 +42.1% sobre VLM-as-judge ([Zhang et al., arXiv 2504.11101](https://arxiv.org/abs/2504.11101)). Custoso mas eficaz.
- **RLVR (Reinforcement Learning with Verifiable Rewards)** — olmOCR-2 ([Poznanski et al., arXiv 2510.19817](https://arxiv.org/pdf/2510.19817), out. 2025) treina diretamente contra unit tests determinísticos (e.g. "table structure preserved", "math faithfully transcribed"). Eleva olmOCR-Bench de 78.5 → 82.4.
- **Refuse-to-answer training (GRPO + uncertainty)** — *Seeing is Believing* (NeurIPS 2025) mostra 22pp de melhora em hallucination-free accuracy treinando o modelo a *recusar* em regiões ambíguas.

---

## 2. Round-trip consistency — atualizações

### 2.1 Novos achados

- **Lost in Translation (LiT) benchmark com MQM (2026)** — pesquisa em RTT para LLMs multilíngues mostra que MQM scores ≥ 80 correlacionam ρ=0.94 com preferência humana ([*Round-Trip Translation Reveals What Frontier Multilingual Benchmarks Miss*, arXiv 2604.12911](https://arxiv.org/html/2604.12911)). É a melhor evidência recente de que RTT pode ser proxy válido — *desde que* combinado com avaliação semântica estruturada (MQM), não com BLEU puro como Moon et al. 2020 já alertaram.
- **Allamanis et al. 2024 (Round-Trip Correctness)** — ainda referência canônica para código; não localizamos follow-up de 2025/2026 que estenda formalmente o framework para documentos.
- **PDF→Markdown especificamente**: o paper *Accelerating End-to-End PDF to Markdown Conversion through Assisted Generation* ([Horn et al., arXiv 2512.18122, dez. 2025](https://arxiv.org/abs/2512.18122)) usa *Copy Lookup Decoding* explorando "high n-gram overlap between PDFs and their Markdown equivalents" — implicitamente confirma que round-trip preserva muito conteúdo em documentos texto-densos, e degrada quando o overlap n-gram cai (= input esparso, exatamente nosso caso).
- **READoc** ([Li et al., ACL Findings 2025, arXiv 2409.05137](https://arxiv.org/abs/2409.05137)) — primeiro benchmark a tratar DSE (Document Structured Extraction) como **PDF → Markdown end-to-end**, com S³uite (Standardization, Segmentation, Scoring). Métricas: EDS (edit distance similarity), TEDS (tree edit), KTDS (Kendall-τ similarity para reading order). Avaliou 14 sistemas incluindo Marker, MinerU, Docling, Nougat. **Não é round-trip** — usa GT manual extraído de fonte LaTeX/HTML — mas é o benchmark mais próximo do nosso pipeline conceitualmente.

### 2.2 Implicações para pdf2md

A nossa decisão de v1 ("round-trip é health check, não métrica primária") **permanece válida**. READoc fornece um caminho para tirar GT que não depende do nosso reconstrutor:

- READoc usa documentos com fonte LaTeX/Markdown nativa (arXiv, GitHub), o que evita o "viés do reconstrutor" que a v1 §4 apontou.
- KTDS para reading order endereça parcialmente Q10 da v1.
- TEDS sobre ToC já reportada por READoc é exatamente o que sugerimos em §1.6.

**Recomendação atualizada**: rodar nosso baseline contra subset do READoc (papers + textbooks subset) **antes** de construir corpus interno completo do T040.

---

## 3. PDF→Markdown — estado 2026 atualizado

Mudanças relevantes desde maio 2026 (compilação v1):

### 3.1 Ferramentas — atualizações

| Ferramenta | Estado v1 | Atualização | Impacto |
|---|---|---|---|
| **Marker** | 1.10.x | v1.10.2 lançada em 31-jan-2026 (Surya 0.17.1 bump, licensing fix). [Block-level OCR](https://github.com/datalab-to/marker) virou default — boost de acurácia. `--use_llm` recomendado para tabelas multi-página e forms. | Compatível com nosso pipeline. Considerar `--use_llm` para casos AcroForm (§4). |
| **MinerU** | 2.5 (~90.67) | **MinerU2.5-Pro** ([arXiv 2604.04771](https://arxiv.org/abs/2604.04771), 6-abr-2026): OmniDocBench v1.6 = **95.69** (+2.71 sobre MinerU 2.5, +1.39 sobre 2º colocado). Mesma arquitetura 1.2B, ganho via *data engineering* (sample expansion 10M→65.5M, *diversity-and-difficulty-aware sampling*, *judge-and-refine* annotation pipeline). | Forte candidato a re-baseline. Table TEDS +5.54, dense formula CDM 97.29, text edit distance 0.036. AGPL ainda vigente. |
| **olmOCR** | 7B-Qwen2.5-VL base | **olmOCR-2-7B-1025** (22-out-2025): RLVR com unit-test rewards via GRPO. olmOCR-Bench 82.4 (+4 sobre v1). Math 82.3%, tables 84.9%, multi-column 83.7%. [arXiv 2510.19817](https://arxiv.org/abs/2510.19817). | Mantém Apache-2.0. Forte em English print + scans. Math ainda inferior a Mathpix/Nougat em papers densos. |
| **Docling** | base + Granite-Docling exp | **Granite-Docling-258M** (set. 2025, Apache-2.0): ultra-compact VLM 258M params. Substitui SmolLM-2 por Granite-3-base, SigLIP por SigLIP2. F1 **0.968 em equações** (vs 0.947 antes). Mitigação de loops repetitivos do SmolDocling-256M-preview. Treinado em SynthFormulaNet. [HF model card](https://huggingface.co/ibm-granite/granite-docling-258M). | Ótimo candidato para CPU-friendly pipeline. Em jan/26 IBM doou Docling para Linux Foundation AAIF. |
| **Nougat** | manutenção parada | Sem atualização. Continua referência histórica + utilidade em arXiv-only. Repetition hallucination (1.5% in-domain) ainda é limitação. | Manter apenas como comparativo em formulas longas. |

### 3.2 Ferramentas — novidades absolutas (não cobertas em v1)

- **DeepSeek-OCR / DeepSeek-OCR-2** ([arXiv 2510.18234, out. 2025](https://arxiv.org/html/2510.18234v1)) — "Contexts Optical Compression": comprime visual via DeepEncoder em 64–800 tokens (vs ~6000 do MinerU2.0). 3B MoE-A570M decoder. 97% accuracy a 10× compression; 60% a 20×. Throughput 200k+ páginas/dia em 1 GPU. **Relevante** se nosso pipeline crescer para corpora maiores.
- **PaddleOCR-VL** (0.9B, Baidu) — OmniDocBench v1.5 = 94.5, perto de GLM-OCR (94.62). Lightweight. ([HF discussion](https://huggingface.co/PaddlePaddle/PaddleOCR-VL/discussions/29))
- **dots.ocr** — vencedor em character accuracy em comparativo independente ([Regolo, 2026](https://regolo.ai/deepseek-ocr-vs-glm-ocr-vs-paddleocr-benchmark-2026/)).
- **GLM-OCR-0.9B** (Zhipu/Tsinghua) — líder OmniDocBench v1.5 com 94.62.
- **Mistral OCR** — VLM proprietário, output Markdown + HTML para tabelas + LaTeX para math. Composite output explícito.
- **HunyuanOCR** (Tencent) — discutido em comparativos, ~80 OmniDocBench.
- **Qwen3-VL / Qwen3.6 Plus** — VLMs gerais que lideram OmniDocBench v1.5 (Qwen3.6 Plus = 0.912 = 91.2%, segundo [BenchLM](https://benchlm.ai/benchmarks/omniDocBench15)).

### 3.3 Benchmarks atualizados

- **OmniDocBench v1.5 → v1.6 → v1.7** (jan–abr 2026). v1.6 fixou element-matching biases e introduziu **Hard subset** (296 páginas com fórmulas/tabelas/layouts difíceis). v1.7 adicionou Qianfan-OCR leaderboard e skills-based eval. ([Repo OmniDocBench](https://github.com/opendatalab/OmniDocBench))
- **MinerU2.5-Pro paper** demonstra que o método dominante hoje é *data scaling + render-then-verify annotation* — mesma arquitetura, mais dado curado.

---

## 4. AcroForm / form-fields

### 4.1 O problema técnico

PDFs com forms têm dois sistemas:

- **AcroForm** (PDF 1.2+): forms como objetos `/AcroForm` no PDF dictionary, com campos `/Fields` cujo valor (`/V`) é um string ou número.
- **XFA** (Adobe, depreciado em PDF 2.0): forms como XML separado. Removido oficialmente do PDF spec, mas ainda em uso em governo e jurídico.

Quando o pipeline `pdf → markdown` trata AcroForm como texto comum, os field-labels e values viram pseudo-tabelas que sofrem drift severo (caso IRS 1040: round-trip 46%).

### 4.2 Abordagens da comunidade

**Rule-based / structural (recomendado para forms estáticos):**

- **pypdf** ([docs](https://pypdf.readthedocs.io/en/stable/user/forms.html)): `reader.get_fields()` e `reader.get_form_text_fields()` retornam dict campo→valor. Output trivialmente serializável.
- **pdftk** + ruby `pdf-forms` ou substituto Go [`read-form`](https://github.com/maelvls/read-form): dump JSON dos fields.
- **PDFMiner** ([howto](https://pdfminersix.readthedocs.io/en/latest/howto/acro_forms.html)): walk `/AcroForm` → `/Fields` → `/V`.

**LLM/VLM-based (recomendado para forms scaneados ou degradados):**

- **MinerU** ([repo](https://github.com/opendatalab/MinerU)) detecta scans automaticamente e ativa OCR. Não é form-aware em sentido estrito, mas o backend VLM 2.5-Pro lida razoavelmente com structure detection.
- **Mistral OCR** emite output "interleaved stream of text + images, often Markdown enriched with HTML-based table reconstruction" — útil para forms parciais.
- **Microsoft Document Intelligence** prebuilt model "Unified US Tax" para W2/1098/1040/1099 ([docs](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/tax-document?view=doc-intel-4.0.0)) — pré-treinado em forms específicos. Cloud-only.
- **Affinda / Unstract / Parseur / DocuClipper** — comerciais, todos com pré-treino em 1040 + W2 + 1099.

**Modelos research (form-understanding clássicos):**

- **LayoutLM / LayoutLMv2 / LayoutLMv3** (Microsoft) — pré-treino conjunto texto + layout + image em FUNSD, CORD. Form-aware nativo.
- **FormNet** (Google, ACL 2022, [paper](https://aclanthology.org/2022.acl-long.260.pdf)) — Rich Attention + Super-Tokens via GCN. SOTA em CORD/FUNSD em 2022.
- **Donut** (Naver, ECCV 2022) — OCR-free, multimodal end-to-end.

### 4.3 Recomendação para pdf2md

Para o nicho do projeto (livros + papers científicos), forms são *case-marginal*. Mas para os documentos do corpus que têm forms (IRS 1040 no nosso caso de teste):

1. **Detectar AcroForm antes de OCR**: rodar pypdf `reader.get_fields()`; se retornar non-empty dict, o pipeline deve usar **path estruturado** (campo → valor → MD-list ou MD-table), não OCR.
2. **Heurística estrutural**: se XFA detectado, converter para AcroForm via Foxit/Aspose (out-of-scope no nosso pipeline OSS) ou aceitar perda.
3. **Não tentar resolver forms scaneados** sem modelo específico — está fora do escopo de um conversor PDF→MD genérico.

**Conexão com T071**: forms também produzem bloat alto via re-OCR (campos vazios viram texto inventado). A heurística captura mas não atribui. Próximo experimento (Q11 sugerido): adicionar detector AcroForm como gate precoce.

---

## 5. Métricas novas (2025–2026)

### 5.1 Consensus Entropy ([Zhang et al., arXiv 2504.11101](https://arxiv.org/abs/2504.11101), 2025; v6 mar/26)

Métrica **training-free, model-agnostic** que estima reliability medindo entropia de inter-model agreement. *Princípio*: predições corretas convergem; erros divergem. Operacionalmente: rodar N VLMs sobre mesmo input; se outputs concordam → low entropy (reliable); se divergem → high entropy (unreliable, flag for review).

**Empírico**: +42.1% F1 sobre VLM-as-judge para detecção de OCR errors. Plug-and-play. CE-OCR (variante adaptive-routing) supera self-consistency e single-model baselines a mesmo custo computacional.

**Relevância T071**: é a versão *com múltiplos modelos* do que nossa heurística faz com 1 modelo + comparação self-roundtrip. Próximo experimento (Q12 sugerido): comparar T071-flag com Consensus Entropy (Marker + Nougat + MinerU) nos casos Wilson/IBM Quantum.

### 5.2 LLM-as-judge para fórmulas ([Horn & Keuper, arXiv 2512.09874](https://arxiv.org/abs/2512.09874), dez. 2025)

Benchmark com 100 PDFs sintéticos + 2.000 fórmulas + 750 ratings humanos sobre 250 pares. Compara métricas:

| Métrica | Pearson r vs humano |
|---|---|
| **LLM-as-judge (Gemini/GPT)** | **0.78** |
| CDM | 0.34 |
| Text similarity (BLEU-style) | ~0 |

**Implicação severa para v1 §1.3/§1.4**: CDM, que a v1 recomenda como métrica primária de fórmula, correlaciona **menos da metade** com humanos do que LLM-as-judge. O paper aponta limitações específicas: CDM tem false positives em erros estruturais e false negatives em símbolos Unicode (e.g. `\alpha` vs `α`).

**Recomendação atualizada**: substituir CDM por LLM-as-judge (Gemini-2.0-flash ou GPT-4o) como métrica primária de fórmula no painel multi-métrica. Manter CDM apenas como secondary check (continua útil para *count* de fórmulas idênticas, só falha em ranking fino).

**Top performers no paper**: Qwen3-VL (9.76/10), Gemini 3 Pro (9.75), PaddleOCR-VL (9.65), Mathpix (9.64). **Marker, Nougat e Docling não foram avaliados** — gap a preencher no nosso T050.

### 5.3 PaIRS — structure-aware fidelity ([Bhat et al., WACV 2026](https://openaccess.thecvf.com/content/WACV2026W/VisionDocs/papers/Bhat_SAVIOR_Sample-efficient_Adaptation_of_Vision-Language_Models_for_OCR_Representation_WACVW_2026_paper.pdf))

Métrica que aloca cada palavra numa grid 2D (row, horizontal cell) e mede similarity estrutural beyond transcription. Útil para multi-column e callouts. Endereça parcialmente o problema que v1 §1.1 levantou sobre reading order. **Limitação**: requer que o modelo seja prompt-controlled (gerar saída no formato grid esperado), o que não é o caso de Marker/Nougat default.

### 5.4 Outras métricas e benchmarks novos

- **KIE-HVQA** ([Bytedance, HF Dataset](https://huggingface.co/datasets/bytedance-research/KIE-HVQA)) — 400 amostras anotadas pixel-level para OCR hallucination em ID cards/invoices/receipts. Não diretamente aplicável (forms only), mas template metodológico (annotation reliability) é replicável.
- **OCR-Quality** ([Zhang et al., arXiv 2510.21774, out. 2025](https://arxiv.org/pdf/2510.21774)) — dataset human-annotated para OCR quality assessment. Permite calibrar métricas automáticas contra GT humano.
- **READoc S³uite** (§2.1) — Standardization + Segmentation + Scoring. Mais robusto que round-trip puro.
- **olmOCR-Bench** já estava em v1; agora com 7.000+ unit tests, treinável via RLVR como em olmOCR-2.

### 5.5 Falha geral em hallucination detection metrics

[*The Mirage of Hallucination Detection*, EMNLP Findings 2025](https://aclanthology.org/2025.findings-emnlp.1035.pdf) (e versão arXiv [2504.18114](https://arxiv.org/html/2504.18114v1)) mostra que métricas de hallucination detection em LLM **frequentemente não alinham com human judgment e não escalam consistentemente com parâmetros**. LLM-as-judge (GPT-4) ainda dá os melhores resultados práticos. *Atenuante para nosso plano*: usar LLM-as-judge sabendo dos vieses; não confiar em métricas single-shot.

---

## 6. Implicações para o pdf2md

### 6.1 Adotar

- **MinerU2.5-Pro como novo competidor no T050 baseline**, junto com Marker. OmniDocBench v1.6 = 95.69 vs Marker baseline. AGPL ainda é o ponto chato — usar como reference, não dependência.
- **Granite-Docling-258M como alternativa CPU-friendly**: 258M params, Apache-2.0, F1 0.968 em equações. Vale rodar como sanity check de baseline mínimo.
- **LLM-as-judge para fórmulas** substituindo CDM como métrica primária. Implementar via Gemini-2.0-flash ou GPT-4o; CDM passa a secondary.
- **READoc subset** (papers + textbooks) como GT externo *antes* de construir corpus T040 completo. Reduz risco de viés do nosso GT.
- **Heurística T071** já implementada se mantém — é defensável como detector original de bloat-via-resparse-roundtrip.

### 6.2 Descartar / desprioritizar

- **CDM como métrica primária**: rebaixar para secondary (mantém valor diagnóstico de count, mas não de ranking).
- **Constrained decoding** como mitigação: literatura mostra que não funciona para hallucination semântica.
- **Round-trip puro** como métrica de qualidade: confirmação adicional via Moon 2020 + Mirage 2025; manter só como CI health-check.

### 6.3 Novos experimentos sugeridos (backlog v2)

| ID | Hipótese / pergunta | Métrica de descarte |
|---|---|---|
| **Q11** | AcroForm detection (pypdf `get_fields()`) como gate elimina drift em forms (IRS 1040 → round-trip > 90%). | Round-trip score Form 1040 com vs sem gate. |
| **Q12** | Consensus Entropy (Marker + MinerU + Nougat ensemble) detecta os casos Wilson/IBM Quantum **antes** do round-trip, com >0.85 recall. | Recall em corpus de 8 casos rotulados. |
| **Q13** | LLM-as-judge (Gemini-2.0-flash) correlaciona melhor com nosso julgamento humano (3 reviewers, 50 fórmulas) que CDM. | Pearson r > 0.6. |
| **Q14** | READoc S³uite (EDS+TEDS+KTDS) sobre 20 papers arXiv ranqueia Marker → MinerU → olmOCR-2 → Nougat similar ao nosso painel atual. | Spearman ρ > 0.7 entre ranks. |
| **Q15** | MinerU2.5-Pro supera Marker em Nielsen-Chuang cap. 4 (nosso baseline 95.1%)? | Round-trip% > 96%. |
| **Q16** | Granite-Docling-258M é viável como pipeline-CPU-only? (sem GPU, < 8GB RAM) | Tempo < 10s/página, RAM < 8GB. |
| **Q17** | LLM-as-judge sobre o output da heurística T071 (input Wilson 1800) confirma que o bloat é alucinação semântica genuína (não só repetição de tokens). | Reviewer agreement ≥ 0.7. |

---

## Referências

### Hallucination em OCR/VLM

- Shah, A. et al. *Seeing is Believing? Mitigating OCR Hallucinations in Multimodal Large Language Models*. **NeurIPS 2025** (poster). [arXiv 2506.20168](https://arxiv.org/abs/2506.20168). Bytedance Research.
- Zhang, K. et al. *Consensus Entropy: Harnessing Multi-VLM Agreement for Self-Verifying and Self-Improving OCR*. [arXiv 2504.11101](https://arxiv.org/abs/2504.11101) (v6 mar/26).
- *From Plausibility to Verifiability: Risk-Controlled Generative OCR with Vision-Language Models*. [arXiv 2603.19790](https://arxiv.org/html/2603.19790v3).
- *GutenOCR: A Grounded Vision–Language Front-End for Documents*. [arXiv 2601.14490](https://arxiv.org/html/2601.14490v1). Roots.ai.
- Blecher et al., *Nougat* (§B.3 repetition detection). [arXiv 2308.13418](https://arxiv.org/abs/2308.13418).
- *Hallucination of Multimodal Large Language Models: A Survey*. [arXiv 2404.18930](https://arxiv.org/abs/2404.18930).
- *A Survey of Multimodal Hallucination Evaluation and Detection*. [arXiv 2507.19024](https://arxiv.org/abs/2507.19024).
- KIE-HVQA dataset. [Hugging Face](https://huggingface.co/datasets/bytedance-research/KIE-HVQA).

### Round-trip / consistency

- Allamanis, M. et al. *Unsupervised Evaluation of Code LLMs with Round-Trip Correctness*. [arXiv 2402.08699](https://arxiv.org/abs/2402.08699) (já em v1).
- *Round-Trip Translation Reveals What Frontier Multilingual Benchmarks Miss*. [arXiv 2604.12911](https://arxiv.org/html/2604.12911) (2026).
- Moon, J. et al. *Revisiting Round-Trip Translation for Quality Estimation*. EAMT 2020. [PDF](https://aclanthology.org/2020.eamt-1.11.pdf) (já em v1).
- Horn, P., Keuper, J. *Accelerating End-to-End PDF to Markdown Conversion Through Assisted Generation*. NLDB 2025. [arXiv 2512.18122](https://arxiv.org/abs/2512.18122).
- Li, Z. et al. *READoc: A Unified Benchmark for Realistic Document Structured Extraction*. ACL Findings 2025. [arXiv 2409.05137](https://arxiv.org/abs/2409.05137) · [ACL](https://aclanthology.org/2025.findings-acl.1128/).

### Ferramentas — releases 2025–2026

- **Marker 1.10.2** (31-jan-2026, Surya 0.17.1 bump). [Repo + Releases](https://github.com/datalab-to/marker/releases).
- **MinerU2.5-Pro**. *Pushing the Limits of Data-Centric Document Parsing at Scale*. [arXiv 2604.04771](https://arxiv.org/abs/2604.04771) (6-abr-2026). [HF model](https://huggingface.co/opendatalab/MinerU2.5-Pro-2604-1.2B).
- **olmOCR-2-7B-1025**. Poznanski, J., Soldaini, L. *olmOCR 2: Unit Test Rewards for Document OCR*. [arXiv 2510.19817](https://arxiv.org/abs/2510.19817) · [Blog](https://allenai.org/blog/olmocr-2) · [HF model](https://huggingface.co/allenai/olmOCR-2-7B-1025) (22-out-2025).
- **Granite-Docling-258M** (IBM, set. 2025, Apache-2.0). [HF model](https://huggingface.co/ibm-granite/granite-docling-258M) · [IBM announcement](https://www.ibm.com/new/announcements/granite-docling-end-to-end-document-conversion).
- **DeepSeek-OCR**. *DeepSeek-OCR: Contexts Optical Compression*. [arXiv 2510.18234](https://arxiv.org/html/2510.18234v1) (out. 2025).
- **PaddleOCR-VL** (Baidu, 0.9B). [HF discussion](https://huggingface.co/PaddlePaddle/PaddleOCR-VL/discussions/29).
- Comparativo independente: *DeepSeek-OCR-2 vs GLM-OCR vs PaddleOCR* — [regolo.ai 2026](https://regolo.ai/deepseek-ocr-vs-glm-ocr-vs-paddleocr-benchmark-2026/).

### Métricas / benchmarks 2025–2026

- Horn, P., Keuper, J. *Benchmarking Document Parsers on Mathematical Formula Extraction from PDFs*. [arXiv 2512.09874](https://arxiv.org/abs/2512.09874) (10-dez-2025).
- *The Mirage of Hallucination Detection*. EMNLP Findings 2025. [PDF](https://aclanthology.org/2025.findings-emnlp.1035.pdf) · [arXiv 2504.18114](https://arxiv.org/html/2504.18114v1).
- **OmniDocBench v1.6/v1.7** (jan–abr 2026), Hard subset 296 páginas. [Repo](https://github.com/opendatalab/OmniDocBench).
- Bhat, R. et al. *SAVIOR: Sample-efficient Adaptation of Vision-Language Models for OCR Representation* (introduz PaIRS metric). [WACV 2026](https://openaccess.thecvf.com/content/WACV2026W/VisionDocs/papers/Bhat_SAVIOR_Sample-efficient_Adaptation_of_Vision-Language_Models_for_OCR_Representation_WACVW_2026_paper.pdf).
- *OCR-Quality: A Human-Annotated Dataset for OCR Quality Assessment*. [arXiv 2510.21774](https://arxiv.org/pdf/2510.21774) (out. 2025).

### AcroForm / forms

- **pypdf** form handling: [docs](https://pypdf.readthedocs.io/en/stable/user/forms.html).
- **PDFMiner.six** AcroForm howto: [docs](https://pdfminersix.readthedocs.io/en/latest/howto/acro_forms.html).
- **read-form** (Go, drop-in pdftk replacement): [Maël Valais, GitHub](https://github.com/maelvls/read-form).
- **Microsoft Document Intelligence — US Tax**: [docs](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/tax-document?view=doc-intel-4.0.0).
- Lee, C.-Y. et al. *FormNet: Structural Encoding beyond Sequential Modeling in Form Document Information Extraction*. ACL 2022. [paper](https://aclanthology.org/2022.acl-long.260.pdf).
- *XFA Wikipedia* (deprecated PDF 2.0). [link](https://en.wikipedia.org/wiki/XFA).

---

*Última atualização: 2026-05-10. Próxima revisão sugerida: após Q15/Q16 completarem (decisão de re-baseline MinerU2.5-Pro vs Marker) ou se um competidor open-source publicar OmniDocBench v1.7 score > 96.*

---

## 7. Atualização 2026-05-16 — pós-experimentos e versions v0.4-v0.7

### 7.1 Q15 (MinerU 2.5-Pro) → blocked operacional

Lab `e06` (`lab/e06_mineru25_pro`): 3 tentativas em Win+RTX3060.
Install OK via `uv` (após primeiro falhar com `pip` em loop de uvicorn);
mas FastAPI server interno crasha silenciosamente após download dos
modelos. Não foi possível obter outputs.

**Status:** Q15 **blocked**, não respondido. Tentativas adicionais
fariam sentido em ambiente Linux ou via API REST direta.

### 7.2 Q16 (Granite-Docling-258M) → respondido parcialmente

Lab `e08` (`lab/e08_granite_docling`): install limpo via `uv pip install docling`,
1 comando, sem servidor. Rodou foreground transparente. **Descartado
para N&C** (50× mais lento que Marker GPU, imagens em base64 inline,
LaTeX verboso) mas **viable para casos curtos / single-file / sem GPU**.

**Status:** Q16 **respondido com escopo**. Confirma que Granite-Docling
é operacionalmente fácil (lição arquitetural: CLI direta + transformers
> servidor FastAPI opaco), mas não é o caminho para nosso corpus principal.

### 7.3 Q7 (e07) descartado — não estava no backlog Q11-17 original mas vale registrar

Marker `--use_llm` + Ollama `llama3.2-vision:11b` no cap 4 N&C
(Lab `e07`, `lab/e07_marker_llm`): 40× mais lento que Marker
base, ganho zero. **Descartado para esse modelo específico em Ollama**.

**Conclusão metodológica:** "LLM" é categoria com centenas de modelos;
conclusão se aplica só a essa combinação específica. Outros VLMs
(Gemini, Qwen3-VL, GPT-4V) podem performar diferente.

### 7.4 Pipeline visual de validação (T070) — contribuição original

**Achado de literatura:** pixel-roundtrip combinando alinhamento de
páginas + macro SSIM + médio WER **não tem precedente claro** que
encontrei. Trabalhos relacionados:

- **READoc** ([Li et al. 2025](https://aclanthology.org/2025.findings-acl.1128/)) compara
  via TEDS, EDS, KTDS contra GT extraído de fonte LaTeX/HTML —
  **não é pixel-based** e exige GT externo. Conceitualmente diferente.
- **OmniDocBench** ([OpenDataLab](https://github.com/opendatalab/OmniDocBench))
  compara contra GT manual via métricas hibridas. Também não pixel-based.
- **Mathpix** e similares fazem pixel-comparison interno para QA mas
  não publicam o algoritmo.
- **DocLayNet** (IBM) tem bbox annotations mas não compara DOIS PDFs
  alinhados.

A combinação `Hungarian align over WER + SSIM macro per pair` no contexto
de validação PDF↔MD não aparece em paper revisado encontrado. Defensável
como instrumentação prática (não pretende ser benchmark formal — é
health-check estrutural).

**Possível paper para o futuro:** "Pixel-Roundtrip: A Calibrated Visual
Validator for PDF↔Markdown Pipelines" — focando no triângulo (com
descobertas dos labs e09-e13 sobre o que **não** funciona).

### 7.5 Ecosystem update — modelos novos desde 2026-05-10

Pequenas atualizações:
- **MinerU 3.0+ branch** (não testado) inclui FastAPI server por design,
  reinforcing concern de Win+GPU compat
- **Qwen3-VL-Plus** continua líder OmniDocBench v1.7 (92.7) — modelo
  proprietário, API paga
- **PaddleOCR-VL 0.9B** continua candidato CPU-friendly não testado

### 7.6 Backlog v2 atualizado

| Q | Status (2026-05-16) | Próximo |
|---|---|---|
| Q11 AcroForm gate | **respondido** (e05) | implementar gate em `pdf2md.stats` se quiser produção |
| Q12 Consensus Entropy | pendente | depende de ensemble multi-VLM setup |
| Q13 LLM-as-judge vs CDM | pendente | depende de T060 GT + API setup |
| Q14 READoc S³uite | pendente | depende de T060 GT |
| Q15 MinerU 2.5-Pro | **blocked** | Linux retry ou API direta |
| Q16 Granite-Docling viable CPU | **respondido com escopo** (e08) | considerar p/ docs curtos |
| Q17 LLM-as-judge alucinação | pendente | depende de API setup |

3 de 7 respondidos. Bloqueio principal: T060 (GT humano em mini-corpus)
destrava Q13, Q14, Q17. Q12 e Q15 são caminhos paralelos.

### 7.7 Triagem da literatura — novidades a investigar (não-prioridade alta)

Não houve revisão sistemática nas 2 semanas seguintes a 2026-05-10. Mas
áreas onde valeria olhar:

- **OmniDocBench v1.7 leaderboard** atualizado (procura por novos
  open-source com score > 96)
- **Paper de MinerU 3.0** (se publicado) para entender o redesign
- **Acceleration / RTX 5090 compat** — alguma ferramenta SOTA exige
  GPU Blackwell?
- **Novos benchmarks específicos PDF↔MD** — READoc é de set/2024, pode
  ter follow-up

*Próxima revisão sugerida: quando T060 (GT humano) estiver pronto e
permitir comparativo mais sério.*
