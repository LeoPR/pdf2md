# Diário do `pdf2md`

Timeline narrativa do projeto. Captura **por que** as decisões foram
tomadas, em ordem cronológica. Para o estado atual, ver
[`README.md`](README.md). Para roadmap, ver [`ROADMAP.md`](ROADMAP.md).

---

## 2026-05-05 — Origem dentro do AulaQuantum

O projeto começou como faixa T100-T199 dentro do AulaQuantum (disciplina
de Computação Quântica UTFPR). Necessidade prática: re-extrair o livro
Nielsen & Chuang (QCQI) com qualidade superior à do PyMuPDF puro, para
poder citar páginas e seções com precisão nas semanas da disciplina.

**Decisões dessa fase:**
- `marker-pdf 1.10.2` adotado como extrator (tinha LaTeX-aware ML, GPU
  RTX 3060 disponível, 5 GB de modelos aceitáveis)
- MD escolhido como formato canônico (vs. LaTeX) — git-friendly,
  human-readable, search-friendly
- Pandoc + Chrome headless + KaTeX para MD → PDF (KaTeX renderiza
  fórmulas no Chrome com qualidade de produção)
- Round-trip MD → PDF → MD' como métrica de fidelidade (T103)

Tickets-âncora: T100, T101, T102, T103, T104.

## 2026-05-06 — Reorganização e padronização

Antes de continuar a faixa T100, foi preciso arrumar o ambiente:
- Eliminação do anti-padrão `_v2` em pastas (T105)
- Centralização de PDFs em `pesquisa_geral/_sources/` (T011)
- Estrutura de tickets `open/in_progress/blocked/research/closed/_archive`
  (T004)
- pyproject.toml + venv junction seguindo `Z:\caches\README.md`

Insights chave:
- "_v2 / _v3 / _v4 ... isso é lixo de programação amadora" (user) — git
  versiona, pastas não duplicam.
- Telemetria importa: cada extração tem que produzir `_stats.{md,json}`
  com método, versões e métricas. Sem isso não dá pra comparar
  experimentos.

## 2026-05-07 — Conversor amadurece e ganha autonomia (T400)

Marco: o usuário propôs **separar o conversor como projeto paralelo**.
Razão: a faixa T100 é "conversor aplicado ao AulaQuantum"; mas o
conversor já é maduro o suficiente para virar tooling reutilizável em
qualquer livro/paper.

**T400 — meta-ticket** abriu uma faixa nova T400-T499:
- T410: testar ferramentas alternativas (Nougat, MinerU, Mathpix, etc.)
- T420: fallback low-resource (sem GPU, sem ML pesado)
- T430: corpus livre para testes (URLs + licenças)
- T440: MD-como-formato-de-transporte (vs PDF)

**PHILOSOPHY.md** registra hierarquia de prioridades:

1. **Conteúdo** (palavras, fórmulas, números, citações)
2. **Estrutura útil** (headers, tabelas, imagens com semântica)
3. **Otimização intermediária** (formato adaptativo, links externos)
4. **Formatação idêntica** (compactação como transporte)

Quando há conflito, segue-se a hierarquia. Tudo isso fica em
[`docs/PHILOSOPHY.md`](docs/PHILOSOPHY.md).

### Telemetria virou relatório

`stats.py` evoluiu de log linha-a-linha para **relatório consolidado**:
resumo executivo, método/versões, fonte, output (overall + por seção),
densidade de math, top LaTeX commands, breakdown de imagens, round-trip
com **divergências categorizadas** (math/heading/emphasis/image_ref/
table/separator/whitespace/other), reprodutibilidade.

Insight enabled: 88.5% das divergências do round-trip do N&C cap.4 são
**math** — drift de notação LaTeX (`\rm` vs `\mathrm`, etc.), não perda
de conteúdo. Isso confirma a 1ª prioridade: o pipeline preserva
**conteúdo** e o que oscila é **formatação** (4ª prioridade).

### Multi-iteration round-trip (T103+)

Pergunta: pipeline converge ou tem drift contínuo?

`multi_roundtrip.py` itera MD → PDF → MD' → PDF → ... e mede similaridade
a cada passo.

Aplicado a um paper de teste (`2106_05919v2`):

| i | sim(MDᵢ, MD₀) |
|---:|---:|
| 1 | 98.29% |
| 2 | 97.89% |
| 3 | 97.55% |
| 4 | 97.44% |
| 5 | 97.44% |

**Veredito:** pipeline estável/idempotente — drift total 0.86% em 5
iterações, Δ entre iter 4 e 5 é 0.00%.

### `aggregate_stats.py`

Varre todas as extrações do corpus e gera `_OVERVIEW.md` com:
- resumo executivo agregado (totais)
- tabela por kind (livro/paper/material)
- distribuição de round-trip
- divergências agregadas
- outliers split em `crítico` (< 50%) e `notável` (50–70%)

## 2026-05-07 — Slides PPTX como categoria problemática (T451)

Aplicar o pipeline aos materiais de aula (10 PDFs) revelou: **todos os
materiais ruins são exports de PowerPoint**. Round-trip varia 28.9% –
80.9%, vs > 89% para livros e papers acadêmicos.

PDFs de slides têm fórmulas-como-imagem, layout multi-column por slide,
text-frames separados, fontes do sistema (Calibri/Arial). Marker é
otimizado para "documento acadêmico contínuo" — slides são edge case.

Caso crítico: IBM lesson 1 (28.9%, token bloat 4,629 → 15,637 = 3.4×).
T450 abriu para investigação dedicada. T451 cataloga a família.

## 2026-05-07 — Compressão adaptativa de imagens (T130 → T131 closed)

Hipótese: marker extrai todas as imagens como JPEG; muitas (line art,
diagramas) seriam menores como PNG indexado.

Primeira tentativa: classificar por contagem de cores únicas.
Resultado: **0/25 convertidas** em ch.4 do N&C — JPEG sempre tem >16
cores únicas por causa de anti-aliasing e ruído de codificação.

Segunda tentativa: adicionar tier `palette_lossy` — quantizar para 16
cores e medir diferença média de pixel. Aceitar se diff < 5/255.

Resultado em N&C: **197/198 convertidas, 4.5 MB → 2.7 MB (−38.6%)**.
T131 closed.

## 2026-05-08 — Artefatos JPEG e desconvolução (T137)

Observação user-driven na logo Cambridge University Press
(`00_front_matter/images/_page_0_Picture_3.png`): pixels dispersos pretos
no fundo branco — **mosquito noise / ringing artifacts** clássicos de
JPEG. Conteúdo real é bicromático.

Insight: T131 (bottom-up) aceita os pixels e escolhe formato. **T137
(top-down)** descartaria o que não é conteúdo (artefatos de
codificação) antes de escolher o formato. Combinados podem dar
economia adicional de 10-30% sobre T131, com qualidade visual
**melhor** — não pior.

Três níveis registrados em T137:
1. Filtros clássicos (median, bilateral, TV, Otsu/Sauvola) — sem ML
2. JPEG-specific deep learning (ARCNN, DnCNN, FFDNet, SwinIR)
3. Reconstrução semântica (OCR + identificação de fonte para logos)

Provocação registrada do user: "se soubéssemos o tipo da letra, o que
está escrito e a forma, ficando só o logo sobrando, provavelmente essa
logo é um copy paste em que só o brasão é realmente uma imagem". Vale
para elementos repetitivos (logos de editora aparecem em N livros).

## 2026-05-08 — Separação `pdf2md` ⊂ `transmutos/`

O AulaQuantum estava acumulando código que não era mais da disciplina.
O conversor virou tooling genérico maduro. Decisão: **mover para projeto
autônomo**.

Estrutura escolhida:
- Pasta-mãe `transmutos/` (do latim *transmutare* — mudar de forma).
  Reserva o lugar para futuros conversores (pptx2md, html2md, etc.).
- Projeto `pdf2md/` aqui dentro.

O que veio do AulaQuantum:
- `tools/pdf_md_converter/*.py` → `pdf2md/src/`
- `pesquisa_geral/livros/Quantum_..._Information/` → `pdf2md/corpus/nielsen_chuang/`
- `pesquisa_geral/_sources/livros/Nielsen_Chuang_QCQI.pdf` → `pdf2md/corpus/_sources/` (gitignored)
- Tickets T100-T199, T130-T137, T400-T499 → `pdf2md/tickets/`
- `tools/pdf_md_converter/PHILOSOPHY.md` → `pdf2md/docs/PHILOSOPHY.md`

O que ficou no AulaQuantum:
- `pesquisa_geral/material_aulas/` (input dos slides da disciplina)
- `pesquisa_geral/papers/` (input das pesquisas complementares)
- Tickets T200+ (disciplina) e T300+ (pesquisa complementar)
- Setup geral (T001-T015)

## 2026-05-11/12 — Bancada-suja → bancada-limpa, ablações e T108

Sessão longa (dois dias). Três grandes blocos:

1. **Provenance** (`pdf2md.provenance`): marcador idempotente por arquivo
   (versão + commit + data + fonte + sha256 + extractor). Aplicado ao N&C
   completo no AulaQuantum (22 arquivos, commit 0431464).

2. **Ablação extratores** (e07 + e08): testamos Marker `--use_llm` com
   `llama3.2-vision:11b` via Ollama e Granite-Docling-258M via docling
   2.93.0. Ambos descartados para N&C — 40-50× mais lentos sem ganho
   qualitativo. Lição metodológica: não generalizar de N=1; conclusões
   nomear modelo+tool+corpus (salva em memory).
   Achado positivo de e08: `docling` instala limpo via `uv pip` (resolve
   o problema OPERACIONAL que bloqueou Q15 MinerU). Marker baseline 95.09%
   é teto operacional testado.

3. **T108 fechado**: pacote pdf2md instalável (`pip install -e .`) com
   CLI unificado — macro `pdf2md convert FILE.pdf` (auto-detect via TOC)
   + 10 subcomandos finos + `doctor`/`version`. Validação em produção
   re-extraindo N&C completo (1h54min) revelou um bug: `_marker_raw/`
   filho de `out/` é apagado pelo `rmtree(target_dir)` do restructure.
   Fix em duas camadas (cli.py usa pasta irmã + defensiva no restructure
   para falhar cedo). Após fix, 21/21 capítulos com SHA-256 bit-for-bit
   idêntico ao histórico — determinismo confirmado.

Decisão sobre N&C no AulaQuantum: **manter versão atual** (`_stats.md`
histórico tem mais info — round-trip 95.09%, versões marker/torch/CUDA
— que o novo gerado pelo venv do pdf2md, que regrediu para "n/a").
Conteúdo MD é idêntico de qualquer forma. Próximo passo natural seria
fix do `stats.py` para propagar metadados via flags (v0.4 cleanup).

## 2026-05-13 — v0.4: scripts → módulos, env vars → kwargs

Limpeza arquitetural em 5 batches, todos com tests/ acompanhando.

Antes da v0.4 o `cli.py` delegava todo subcomando via `subprocess.run`
chamando scripts em `src/*.py`. Funcionava mas tinha custos: cada chamada
fork+spawn (lento no Windows), erros viravam stderr-eco em vez de
exceções tratáveis, e a passagem de metadados (versões marker/torch/CUDA)
exigia env vars `PDF2MD_*_VERSION` — um workaround para o fato do
`stats.py` rodar num venv sem torch/marker importáveis (conflito histórico
pillow<11 do marker vs pillow>=11 da otimização).

A v0.4 inverte o fluxo. Cada script vira módulo importável em
`pdf2md/<nome>.py` com:
- Função top-level pública (`compute_stats`, `run_roundtrip`,
  `optimize_dir`, etc.) recebendo paths + callbacks de progresso.
- `_cli()` interno para compat com chamada standalone (preservada via
  shims de ~13 linhas em `src/`).

Os 5 batches (em ordem):
1. `provenance` + `tests/` inicial (49 tests).
2. `roundtrip`, `gen_pdfs`, `multi_roundtrip` migrados.
3. `restructure`, `aggregate_stats` migrados. Bug de generalização achado
   no test_restructure: assertion `chapters[0].id == "00_front_matter"`
   era literal demais; trocado por `header_re is None`.
4. `stats.py` (737 linhas, o maior). Trocou env var override por kwargs
   em `detect_tools()` — precedência kwargs > env vars > auto-detect. CLI
   agora passa metadados direto via `tool_overrides=...`. Env var
   fallback preservado para compat com chamada standalone antiga.
5. `optimize_images.py` (397 linhas, o último). Adicionou ProgressCb
   `(i, total, record)` para o CLI renderizar progresso a cada 20 imagens.

Estado final:
- 79 testes em 7.01s (cobrindo todas as funções puras dos 7 módulos).
- `cli.py` sem subprocess para subcomandos próprios — só ainda chama
  `marker_single` externo (que vive em outro venv por design).
- `src/` agora: 6 shims de 13 linhas + pacote `pdf2md/` com 9 módulos.

Decisão de escopo: nenhuma feature nova nesta release. Só refactor +
tests. Mas a base agora permite features impossíveis antes — por
exemplo, `pdf2md aggr` pode passar dicts em memória entre módulos sem
rodar `_stats.json` round-trip em disco. Próximas releases ganham
velocidade de iteração.

Tag `v0.4.0`. Próxima frente prevista: pesquisa (Frentes A-E) ou
mini-corpus GT humano (T060) destravando validação não-circular do
round-trip.

## 2026-05-16 — Camada conceitual + lab e09 + v0.4.1

Sessão de articulação arquitetural seguida de validação empírica.

**Articulação** (4 docs formalizando a tese implícita):
- `PHILOSOPHY.md` ganha 6 seções (validação por fechamento recursivo,
  triângulo macro/médio/micro, calibração do reconstrutor, ablação
  modular, tradeoffs explícitos, convergência vs divergência)
- `META_TRANSMUTOS.md` (novo): tese da família — pdf2md como instância
  de decompilador/recompilador universal `objeto ↔ MD+acessórios ↔ objeto`
- `MD_CANONICAL.md` (novo): schema do output como pivot canônico
- Tickets T070 (pixel-roundtrip), T072 (calibração), T402 (meta-fractal)

**Validação empírica** em `lab/e09_pixel_roundtrip_proto/`:
- Macro SSIM (median 0.615) discrimina cap 4 N&C vs render → promove
- Pareamento por ordem-de-leitura para bbox IoU **falha** (45 pgs orig
  vs 49 pgs render, reflow torna ordem inválida). Médio/micro adiados
  para versão com pareamento por texto-fingerprint
- Lab achou 2 bugs colaterais mais valiosos que o resultado primário:
  - PDFs em `corpus/<doc>/<cap>/<cap>.pdf` são **renders do pdf2md**,
    não sources do livro (metadata HeadlessChrome+Skia). Documentado
    em `MD_CANONICAL.md§"Distinção crítica"`.
  - `md_to_pdf(md)` sobrescreve PDF co-irmão silenciosamente (T076).
    Destruiu o PDF render do cap 4; recuperado via `git restore`.

**v0.4.1 (patch)**: T076 fixado — `md_to_pdf(md, out_pdf=None, *, overwrite=False)`.
Default agora levanta `FileExistsError` quando destino existe.
`generate_all` passa `overwrite=True` explicitamente (re-runs são uso
esperado). 81 tests passando (2 novos cobrindo o guard).

## Próximos passos planejados

Ver [`ROADMAP.md`](ROADMAP.md) para o quadro completo. Curto prazo:
- T060: mini-corpus GT humano (4-6h humanas) — destrava validação
  não-circular do round-trip.
- T132: integrar potrace para vetorização SVG.
- Q11 AcroForm pipeline: integrar `pypdf.get_fields()` em `src/` para
  PDFs de formulário (achado de e05).

---

*Este diário é apêndice histórico. Estado atual mora em [`README.md`](README.md).*
