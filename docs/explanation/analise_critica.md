# Análise crítica do projeto `pdf2md`

> *Revisão honesta do curso do projeto, lições aprendidas, decisões que se
> mostraram certas e erradas, e direções recomendadas. Snapshot 2026-05-16,
> v0.7.0. Complementa [`ARQUITETURA.md`](arquitetura.md) (estado técnico),
> [`PHILOSOPHY.md`](philosophy.md) (decisões de design) e
> [`diario.md`](diario.md) (timeline cronológica).*

## TL;DR

Em ~10 dias de trabalho ativo o projeto saiu de "scripts soltos com
hardcode" para um pacote `pip install pdf2md` v0.7.0 com:

- **10 módulos importáveis** em `src/pdf2md/`, 110 tests passing
- **Pipeline visual de validação** (T070 pixel-roundtrip) provado em
  4 categorias de PDF distintas — única feature deste tipo que encontrei
  documentada
- **Telemetria por step** (T085) instrumentando wall/cpu/mem/gpu/io
- **5 documentos arquiteturais** novos formalizando a tese antes implícita
- **15 labs** registrando experimentos com critérios pré-registrados,
  veredictos com escopo (não-N=1) e descartes instrutivos
- **9 tags semânticas** (v0.4.0 → v0.7.0) com 7 releases reais

**Custo:** alta dependência da minha máquina específica (RTX 3060, paths
absolutos OneDrive, AulaQuantum). Documentação cresceu mais que a
implementação — possível over-engineering de articulação relativo a
features concretas entregues.

**Próximo gargalo principal:** [T060](../../tickets/open/T060_mini_corpus_gt_humano.md)
(GT humano em mini-corpus) — sem ele, várias outras frentes não destravam.

---

## 1. Trajetória curta

```
2026-05-05 → origem dentro do AulaQuantum (faixa T100)
2026-05-08 → separação para projeto autônomo (transmutos/pdf2md/)
2026-05-09 → bancada montada (lab/, corpus/, tickets/)
2026-05-10 → T050 baseline reproduzível (95.09% N&C cap 4)
2026-05-11 → e05 AcroForm gate, ablação Q11.b
2026-05-12 → e07 (Ollama LLM), e08 (Granite-Docling) — ambos descartados
2026-05-13 → v0.4.0: pacote pip instalable + CLI macro
2026-05-15 → camada conceitual (PHILOSOPHY + META_TRANSMUTOS + MD_CANONICAL)
2026-05-15 → e09-e13: jornada do triângulo do pixel-roundtrip
2026-05-16 → v0.5.0 telemetry, v0.6.0 pixel_roundtrip, e14 cross-PDF, v0.7.0
```

Duas fases distintas emergem:
1. **Plumbing** (05-13): montar pipeline, ferramentas, telemetria, CLI
2. **Validation** (13-16): construir o validador permanente (pixel-roundtrip)

A segunda fase produziu mais artefatos por dia mas também mais decisões
arquiteturais finais. A primeira foi mais lenta e menos sexy mas
construiu a base sem a qual a segunda não rodaria.

---

## 2. Decisões que se mostraram certas

### 2.1 Bancada-suja → bancada-limpa (lab/eXX antes de src/)

Cada nova capacidade nasce em `lab/eNN_*/` com hipótese pré-registrada
e critério de descarte explícito antes de mexer em `src/`. Só promove
quando validado.

**Por que funcionou:**
- 4 dos 5 candidatos de fingerprint pairing (e10/e11) foram descartados —
  se tivesse codado direto em `src/`, teria que reverter
- A trajetória completa do pixel-roundtrip (e09→e10→e11→e12→e13)
  foi 5 descobertas instrutivas que só foram possíveis porque cada lab
  é descartável
- O lab e14 reusa `pdf2md.pixel_roundtrip` (promovido em v0.6) — a separação
  bancada-suja/limpa permite que labs validem código já em produção

### 2.2 Escopo de conclusão nominal

Memória `feedback_escopo_de_conclusao`: "LLM" é categoria com centenas
de modelos. Sempre nomear modelo+tool+corpus específicos.

**Onde ajudou:** e07 descartou `llama3.2-vision:11b` via Ollama em N&C —
**NÃO** "LLMs não funcionam para PDFs". A diferença é metodologicamente
crítica. Permitiu que pix2tex (outra LLM para outro propósito) continuasse
no roadmap sem contradição.

### 2.3 Round-trip como mecanismo, não objetivo

Articulação tardia (PHILOSOPHY §"Validação por fechamento") mas que
estava implícita desde o início. Trata round-trip como teste tipo
compilador: se o ciclo fecha bem, há **evidência indireta** de extração
rica, sem precisar de GT humano em escala.

**Onde ajudou:** evita o pântano de "round-trip alto é qualidade alta"
(criticado em [Moon 2020](literatura.md), Mirage 2025). Reconhece o
limite: ciclo nunca fecha 100% porque MD < PDF em expressividade.

### 2.4 Triângulo macro/médio/micro

Decomposição que **discrimina** erro de extração vs erro de reconstrução.
Sem ela, a métrica visual seria um número global frágil.

**Surpresa positiva:** durante o desenvolvimento, o vértice "micro"
(block-a-block) foi descartado por evidência empírica (e10/e11),
mas isso só foi possível porque cada vértice foi testado isoladamente.
Triângulo virou **dipolo** macro+médio em produção, mas o framework de
3 níveis ainda guia a teoria.

### 2.5 Calibração do reconstrutor como instrumento

Tese: reconstrutor tem **ruído base** mensurável. Subtrair esse ruído
isola o erro real da extração.

**Por enquanto só conceitual** — depende de T060 (GT humano) para virar
operacional. Mas a articulação já evita armadilha de v0.5.0: WER 0.40
não é necessariamente erro do marker, pode ser limite do
pandoc+Chrome+KaTeX em renderizar matemática igual ao TeX original.

### 2.6 Memórias de feedback como guia operacional

8 memórias capturando padrões repetidos do usuário (bancada-suja, escopo
de conclusão, commit por marco, etc.). Acelera continuidade entre
sessões muito mais que qualquer documentação faria.

### 2.7 Comportamento de bug → memória → fix em código

`md_to_pdf` quase destruiu PDF original durante e09. Sequência:
1. Bug observado
2. Memória `feedback_pdf_em_corpus_eh_render` salva
3. Ticket T076 criado
4. Fix em v0.4.1 com `out_pdf` + `overwrite=False`
5. Tests de regressão

Cada um desses passos era opcional; o conjunto institucionaliza prevenção
do mesmo erro futuro.

---

## 3. Decisões que se mostraram erradas (ou questionáveis)

### 3.1 Hardcode de paths absolutos a OneDrive

Vários módulos têm refs literais a `C:\Users\leona\...\AulaQuantum\...`.
**Impacto:** projeto não roda em outra máquina sem editar código.

**Justificativa parcial:** convenção da máquina documentada (Z:\caches,
Acadêmicos/, etc.), aceita explicitamente em [`docs/explanation/analise_critica.md`
no contexto da memória pessoal do usuário](#). Mas:
- Onboarding de colaborador externo seria longo
- Push público (preparado mas não feito) exige sanitização
- Tests passam apenas porque usam tmp_path; tests de integração com
  PDFs reais (e07 onwards) dependem dos paths

**Recomendação:** quando push público virar prioridade, mover paths
para config `pdf2md.config.toml` com fallbacks.

### 3.2 Bumps de versão sem release notes formais

7 versions criadas (v0.4.0 → v0.7.0) mas nenhuma `CHANGELOG.md`. Mensagens
de commit têm contexto, mas não há arquivo único leve para "o que mudou
entre versões".

**Impacto baixo agora** (uma pessoa só usa); mas problemático se outros
colaboradores entrarem ou se quisermos publicar releases no GitHub.

**Recomendação:** criar `CHANGELOG.md` extraindo dos commits + tags.
Trabalho ~20 minutos.

### 3.3 Documentação cresceu mais que features

| Bloco | LOC aprox | LOC docs |
|---|---:|---:|
| Antes de v0.4 (10 docs principais) | ~3500 | ~1500 |
| v0.4-v0.7 (5 docs novos + atualizações) | ~5500 | ~3000 |

Documentos novos somam ~1500 linhas. Pacote `pdf2md/` (código mais
features novas) somou ~800 linhas no mesmo período.

**Tradeoff legítimo:** a articulação conceitual destravou decisões
(triângulo, calibração, fractal recursivo). Sem ela, o projeto seria
"vários scripts".

**Mas:** alguma parte é over-engineering relativo ao escopo real
(1 usuário, 1 corpus, 1 máquina). META_TRANSMUTOS articula uma família
de conversores que ainda não existe; PHILOSOPHY ganhou 6 seções para
formalizar tese de teste que tem só 110 cobrindo. ANALISE_CRITICA.md
(este) é mais um exemplo — vale a pena se outras pessoas usarem; é
puro overhead se ficar só comigo.

**Recomendação:** reconhecer e aceitar; mas evitar criar **mais** docs
"meta" até features concretas como T060/T132/T160 saírem do roadmap.

### 3.4 Memorização inicial subdimensionada

Memórias começaram tarde (após e07 já ter erro de generalização N=1).
A primeira memória de workflow ("bancada-suja") foi salva em 2026-05-09,
mas comportamentos similares já estavam em vigor desde 2026-05-05.

**Recomendação:** quando memórias virarem útil, registrar **imediatamente**
mesmo que ainda incertas. Vale revogar/atualizar do que perder o padrão.

### 3.5 Dependências grandes adicionadas sem questionamento real

v0.5 adicionou `psutil`. v0.6 adicionou `numpy + scipy + scikit-image`.
v0.7 expandiu uso de tudo isso. Não houve análise de "vale tornar deps
obrigatórias vs `optional-dependencies`?"

**Justificativa:** filosofia "pdf2md tem batteries included" é coerente.
Mas implícita até este doc.

**Tradeoff escondido:** instalação total pulou de ~50 MB (pymupdf+pillow+typer)
para ~400 MB (scipy+scikit-image são pesados). Para usuário com hardware
modesto ou ambiente containerized, isso pode ser problema.

**Recomendação:** se T420 (low-resource fallback) virar prioridade,
migrar `pixel_roundtrip` deps para `optional-dependencies`:

```toml
[project.optional-dependencies]
pixel-roundtrip = ["numpy>=1.26", "scipy>=1.14", "scikit-image>=0.22"]
```

E import lazy no módulo. ~30 min de trabalho.

### 3.6 CSS_INLINE como variável em pdfs.py

Hardcoded ~30 linhas de CSS em string Python. Impossível editar sem
editar o módulo. Sem fallback configurável.

**Impacto:** todos os PDFs gerados têm o mesmo "look" — Segoe UI,
margens 2cm, caixas coloridas para math. Para alguém querendo outro
estilo (Times, sem cores, A5), tem que editar `pdfs.py`.

**Recomendação:** mover CSS para `pdf2md/templates/default.css` carregado
por path; adicionar flag `--css FILE` no `pdf2md pdfs` e `md_to_pdf`.

### 3.7 ROADMAP era mais hipotético que realista

A versão original tinha "Fase 5 — Corpus e validação" e listas de tickets
sem sinais de prioridade ou estimativa. Não acompanhava o estado real
dos labs nem o progresso por frente.

**Atualizei agora** (2026-05-16) mas o padrão histórico foi: roadmap
fica obsoleto silenciosamente, conversa com o usuário re-prioriza
informalmente, e novas tarefas aparecem fora do roadmap. ROADMAP
funciona como "esboço macro", não como ferramenta operacional.

**Recomendação:** aceitar ROADMAP como esboço; usar `tickets/INDEX.md`
como fonte de verdade operacional (já está mais atualizado). Re-revisar
o ROADMAP **uma vez por semana** ou após cada release.

---

## 4. Surpresas técnicas

### 4.1 Marker é muito bom em LaTeX nativo, frágil em casos degradados

Round-trip 95% em N&C LaTeX, 13.6% em Wilson 1800 scan (e03), 46% em
IRS f1040 form (e05). Variância enorme **por categoria de PDF**.

**Implicação:** "qualidade do conversor" não é número único.
[`docs/reference/metricas.md`](../reference/metricas.md) já capturava isso; e02/e03/e05
quantificaram empiricamente.

### 4.2 Bloat ratio detecta alucinação de re-OCR (T071)

Padrão original do projeto: quando MD₁ é esparso (<200 tokens/pg), o
marker alucina no PDF intermediário do round-trip, inflando MD₂ em 3-8×.
Não encontrei nome consolidado para isso na literatura (Shah 2025
"Seeing is Believing" e Zhang 2025 "Consensus Entropy" cobrem casos
relacionados mas distintos — ver
[`LITERATURA_v2.md §1`](literatura.md)).

**Status:** heurística simples (1 número, 1 threshold), implementada
em `stats.py`, defensável como contribuição metodológica original.

### 4.3 Pareamento block-a-block fundamentalmente não funciona com reflow

Aprendizado dos labs e10/e11: o problema não é o fingerprint específico,
é que **a fragmentação difere** entre PDFs com reflow. Render quebra
parágrafo em N linhas; livro mantém junto. Block-a-block exige
granularidades comparáveis, e reflow muda granularidade — sem alinhamento
prévio das **páginas**, qualquer matching local degenera.

**Implicação para a arquitetura:** o vértice "micro" do triângulo
(que era a aspiração para localização fina de erro) foi reduzido a
diagnóstico. Vencer essa limitação exige reconstrução semântica (não
faz sentido com o stack atual).

### 4.4 Hungarian alignment supera DTW na maioria dos casos

Espera-se DTW (monotônico por construção) ser melhor para reflow.
Empiricamente Hungarian dá WER mediano ligeiramente menor (0.376 vs
0.401) — porque permite trocas globais que minimizam custo total.

**Não-monotonicidade não é bug.** É otimização global legítima quando
N≈M (mesmo nº páginas). Para N≠M significativo, ambos convergem.

### 4.5 SSIM nunca atinge 0.95 em casos reais (com PDF render do pdf2md)

Esperado. pdf2md usa Segoe UI sans + CSS próprio; livros usam Times
serif + tipografia editorial. SSIM mediano cross-PDF: 0.53-0.64. O
**range** discrimina (alguns pares 0.86, outros 0.31), mas o valor
absoluto não atinge "perfeição visual" porque os PDFs são
visualmente diferentes por design (4ª prioridade abandonada).

### 4.6 GPU VRAM tem floor de ~3.3 GB do driver (RTX 3060 12 GB)

Lab e10 telemetria revelou: nvidia-smi reporta sempre ~3.3 GB usado
mesmo sem nenhuma carga ML. É overhead do driver/CUDA runtime. Por isso
T085 captura `vram_delta_mb` além de `vram_peak_mb` — só delta é
informativo para perfil do step.

### 4.7 macro_ssim é o gargalo do pixel-roundtrip

22s para 49 páginas (CPU 99%, single-thread, RSS 320 MB peak). 49% do
wall total do e10. Candidato óbvio para `multiprocess.Pool` (estimativa:
3-4s com 8 workers). Trabalho pendente.

---

## 5. O que sabemos hoje sobre as alternativas

| Tool | Promessa | Realidade no nosso teste | Status |
|---|---|---|---|
| Marker (atual) | math LaTeX nativo | 95% rt em N&C; falha em scans/forms | **default** |
| Marker `--use_llm` + Ollama VLM | hybrid LLM | 40× lento, 0 ganho em N&C com llama3.2-vision | descartado p/ esse modelo |
| MinerU 2.5-Pro | OmniDocBench 95.69 | install OK, server crash Win+RTX3060 | **blocked** |
| Granite-Docling-258M | Apache, CPU-friendly | 50× lento p/ N&C, base64 imgs | descartado p/ N&C |
| Nougat | math benchmark | não testado ainda | pendente |
| olmOCR-2 | RLVR Apache | não testado ainda | pendente |
| pix2tex | fórmula → LaTeX | T134 não iniciado | pendente |
| pdftotext / PyMuPDF puro | fallback CPU-only | T420 não iniciado | pendente |

**Gap importante:** o ecossistema 2025-2026 mudou muito (MinerU 2.5,
Granite-Docling, olmOCR-2, DeepSeek-OCR, PaddleOCR-VL — ver
[LITERATURA_v2 §3](literatura.md)). Continuamos com Marker como base
mais porque funciona do que porque é o melhor. Re-baseline com Marker
× Nougat × olmOCR-2 × Granite-Docling em N&C cap 4 + arxiv_1706 seria
o experimento de maior ROI hoje.

---

## 6. Backlog de literatura ainda em aberto (do LITERATURA_v2 §6.3)

| Q | Pergunta | Status |
|---|---|---|
| Q11 | AcroForm gate em IRS 1040 elimina drift? | **respondido** em e05 (rt 46→73% com normalização) |
| Q12 | Consensus Entropy detecta Wilson/IBM antes do round-trip? | pendente |
| Q13 | LLM-as-judge (Gemini) > CDM em fórmulas em corpus nosso? | pendente |
| Q14 | READoc S³uite ranqueia ferramentas igual ao nosso painel? | pendente |
| Q15 | MinerU2.5-Pro > Marker em N&C cap 4? | **blocked** — e06 server crash |
| Q16 | Granite-Docling viable CPU-only? | **respondido** em e08 (não p/ N&C, sim p/ casos específicos) |
| Q17 | LLM-as-judge confirma alucinação semântica em Wilson 1800? | pendente |

3 de 7 respondidos. Q12, Q13, Q14 dependem de LLM externo (Gemini API)
não setup ainda. Q17 também.

---

## 7. Próximos passos recomendados (por ROI estimado)

### Alta prioridade (destrava muita coisa)

1. **T060 — Mini-corpus GT humano** (5-10 páginas curadas manualmente)
   ROI: destrava T072 (calibração do reconstrutor), T410 (alt-tools com
   métrica não-circular), Q13 (LLM-as-judge), Q14 (READoc). 4-6h humanas
   uma vez; valor permanente.

2. **Re-baseline Marker × Nougat × olmOCR-2** com pixel-roundtrip
   como métrica (T410, primeiro subset).
   ROI: confirma ou refuta hipótese implícita "Marker é o melhor disponível".
   ~2 dias com infra pronta.

### Média prioridade (consolida o atual)

3. **Multiprocess para macro SSIM** — pixel_roundtrip 4× mais rápido.
   30 min de código; ganho permanente.

4. **CHANGELOG.md** e sanitização de paths para push público.
   ~1 hora de trabalho.

5. **CSS configurável** em `pdfs.py`. ~30 min.

### Baixa prioridade (frentes paralelas)

6. **T132 potrace SVG** — line art L1. Frente C+D.
7. **T134 pix2tex** — fórmula → LaTeX. Frente B+D.
8. **T090 macro-intent CLI** — depende dos perfis de T410 completos.

### Aceitar como "talvez nunca"

9. **T180 reconstrução vetorial** (logos texto+brasão). L4 ambição.
   Custo alto, benefício marginal sem caso de uso concreto.

10. **CAD/blueprint** — out-of-scope explicit (META_TRANSMUTOS).
    Mencionado como direção asintótica, não roadmap.

---

## 8. Riscos identificados

### 8.1 Sobre-confiança no triângulo macro+médio

O triângulo foi validado em **4 documentos** (N&C cap4, arxiv 1706,
preskill, CDC). Todos com text-layer; nenhum scanned-only ou
form-heavy. Pode degenerar em casos não testados.

**Mitigação:** validar em scan (Wilson 1800), form (IRS f1040) antes
de marcar T070 como closed.

### 8.2 Marker está se afastando do estado da arte

OmniDocBench v1.6 (jan/26): MinerU 2.5-Pro 95.69 > Marker baseline.
Continuar com Marker porque é o que temos.

**Mitigação:** Q15 retry (Linux ou via API). Se MinerU 2.5-Pro for
mensuravelmente melhor, considerar troca apesar de AGPL.

### 8.3 Telemetria depende da minha máquina específica

Perfis em [`TECNOLOGIAS.md`](../reference/tecnologias.md) são valores absolutos da
minha RTX 3060 + i7. Outras máquinas terão números muito diferentes.

**Mitigação:** complexidade é invariante (memória `arquitetura-instrumento-mapa-roteador`).
Se rodarmos ablação com tamanho de input variável, dá pra inferir
f(n) independente de hardware.

### 8.4 Push público nunca foi exercitado

`docs/reference/corpus/licensing.md` discute preparação mas o repo nunca foi pushado.
Riscos:
- Paths hardcoded vazariam pra usuários externos
- N&C content em `corpus/` é copyrighted (Cambridge UP)
- Tags `v*.0` aparecerão sem CHANGELOG
- Documentação cresceu muito mas pode estar fora-de-sync com código

**Mitigação:** push só quando T060 + CHANGELOG + CSS configurável +
sanitização de paths estiverem prontos. Algumas semanas de trabalho.

---

## 9. Métricas operacionais do projeto

Sessões medidas (parcialmente):

```
Total commits desde fork:           ~80
Total tags:                          7 (v0.4.0 → v0.7.0)
Total tests passing:                 110
LOC src/pdf2md/:                     ~3500
LOC tests/:                          ~1800
LOC docs/:                           ~5500
LOC lab/eXX:                         ~3000
Total labs (e00-e14):                15 (12 .frozen, 1 .blocked, 2 ativos)
Tickets fechados:                    ~15
Tickets open/research:               ~25
```

Custo de manutenção projetado:
- Cada sessão: 1-3 marcos coerentes (commits agrupados)
- Cada marco: ~50-300 LOC + 1-2 docs atualizados + 1-3 tests novos
- Cadência sustentável: 1 sessão/dia (interativa) ou 1 sessão/semana
  (background)

---

## 10. Síntese

O `pdf2md` evoluiu de "scripts" para "biblioteca instrumentada com
camada conceitual articulada" em ~10 dias. O preço foi alguma quantidade
de over-engineering documental e dependência da máquina específica do
autor.

A maior conquista técnica é **o pipeline pixel-roundtrip validado em 4
categorias** — feature que não encontrei em outras ferramentas de
conversão PDF↔MD open-source. A maior conquista metodológica é o
**hábito de descartes com escopo nominal** (sempre modelo+tool+corpus,
nunca "categoria toda").

A maior dívida é **T060 (GT humano)** — sem ele, várias frentes ficam
em loop de auto-validação circular. 4-6 horas humanas resolvem.

O maior risco é **push público**: o projeto não foi exercitado fora
desta máquina; quando for, vai expor inconsistências e paths hardcoded
que hoje são invisíveis.

A direção que faz mais sentido agora não é "mais features", mas
**consolidar o que tem com GT humano + re-baseline alt-tools**. Depois
disso, T090 (macro-intent routing) vira útil porque tem mapa real para
basear decisões.
