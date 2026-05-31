---
id: T090
titulo: Macro-intent + roteador profile-aware (--rapido/--qualidade/--auto/--indexacao)
status: research
criado_em: 2026-05-16
reescrito_em: 2026-05-31
fechado_em:
fase: 4
depende_de: [T085, T060]
blocks: []
tags: [cli, routing, profile, frente-a, ux]
kind: decisao
altitude: execucao
---

## Contexto

O `pdf2md convert` macro hoje tem presets hardcoded (`--quick`/`--best` em
[cli.py](../../src/pdf2md/cli.py)) com escolhas opacas. Não escala para o caso
de uso real: **indexar milhares de documentos com perfis variados de hardware e
demanda**.

Visão (memória [[arquitetura-instrumento-mapa-roteador]] + [[caminho-executivo-vs-cientifico]]):

> O usuário passa **intent macro**; o sistema escolhe a stack baseado em
> (a) perfis MEDIDOS dos algoritmos, (b) recursos da máquina auto-detectados,
> (c) características do input.

**Mudança desde a 1ª versão (2026-05-31): o MAPA agora existe.** Há **7 perfis
ativos medidos** em [docs/profiles/ativo/](../../docs/profiles/ativo/). O
pré-requisito ("3+ perfis com dados reais") está satisfeito. Este ticket sai do
plano abstrato para **gates concretos derivados de medição** — e, ao fazê-lo,
expõe 3 buracos que limitam as gates (ver fim).

> Esta versão passou por revisão adversarial (3 lentes: host-feasibility,
> intent-coverage, profile-consistency) contra os 7 perfis. As correções estão
> incorporadas; os limites honestos viraram BURACOS explícitos.

## Status de implementação (2026-05-31)

**IMPLEMENTADO** (3 marcos, cada um com revisão adversarial → 7+8+8 defeitos corrigidos):
- **Marco 1 — decisão** (commit 20f71c9): `pdf2md/_profiles.py` (mapa machine-readable
  dep-free) + `pdf2md/routing.py` (`HostInfo.detect`/`DocInfo.probe`/`route()` PURO,
  profile-driven) + `pdf2md/cli.py route` dry-run + 24 testes.
- **Marco 2 — execução** (commit 8b9af3e): `pdf2md/extractors.py` (pdftotext/tesseract
  CPU) + `pdf2md/executor.py` (`run_pipeline`) + `route --execute` + 18 testes.
- **Marco 3 — macro** (este): `--intent` integrado ao `pdf2md convert`. CPU primary
  (pdftotext/tesseract) → branch enxuto (extract+stats+provenance); marker primary →
  fluxo legado (restructure/stats/prov). `--quick`/`--best` mantidos como legado.

CLI realizado como **`--intent <nome>`** (não 6 flags booleanas) — consistente com o
comando `route`; semanticamente equivalente ao critério de aceitação.

**Suite: 155 passed.** E2E: `pdf2md convert FILE.pdf -i rapido` → pdftotext + stats + prov.

**Ainda NÃO executável** (pula com nota honesta): refiners pix2tex (BURACO #3 cropper-CPU)
e gemma3/qwen (T180 small-image). Marker via intent não auto-roda em testes (GPU/tempo).

## Modelo de roteamento — taxonomia dos algoritmos

Os 7 perfis ativos não competem todos no mesmo slot. Há **3 papéis**:

| Papel | Algoritmos | Granularidade | Composição |
|---|---|---|---|
| **PRIMARY** (extrator full-doc, exclusivo) | `marker`, `pdftotext` | documento | escolher 1 |
| **REFINER** (componível, opera em recorte) | `pix2tex` (math), `gemma3-4b-small-image` (logo), `qwen3-vl-8b-small-image` (fallback logo) | recorte | 0..N add-ons |
| **OPTIMIZER** (pós-extração, universal) | `pdf2md-optimize` | recorte/imagem | 0..1 |

`medidores` (telemetria/roundtrip) é **científico** — NÃO entra no pipeline
executivo que `route()` devolve (ver [[caminho-executivo-vs-cientifico]]).

Pipeline = `PRIMARY [+ REFINERs] [+ OPTIMIZER]`.

### Constraints medidos que viram gates

| Algoritmo | Hardware (VRAM pico) | RAM host | Cold | Velocidade | Papel | Vence |
|---|---|---|---|---|---|---|
| marker | **GPU-required** (3400MB medido) | 1.5GB *(est)* | 30s | 12.9s/pg | PRIMARY | prose 0.951, math nativo (Texify), livro/paper, MD+LaTeX |
| pdftotext | CPU-only (0) | 63MB | 0.1s | 0.02s/pg | PRIMARY | velocidade, RAM, offline, determinismo |
| pix2tex | CPU-only (0) | 800MB *(est)* | 11.9s | 6.5s/fórmula | REFINER | math **display** 100% sem. em N=1 (Eq 4.12); inline=medio |
| gemma3-4b-small-image | GPU-opcional (3500MB) / Ollama | 600MB *(est)* | 5s | 45.9s/img | REFINER | logo (transcrição exata) |
| qwen3-vl-8b-small-image | GPU-opcional (5500MB) / Ollama | 700MB *(est)* | 5s | 112s/img | REFINER | logo (fallback Apache-2.0) |
| pdf2md-optimize | CPU-only (0) | 100MB | 0.1s | 0.12s/img | OPTIMIZER | bytes, determinismo, universal |

*(est)* = `confianca: estimado` no perfil de origem (medir em Lab E2). Os
thresholds *load-bearing* (gate GPU 4096 ← VRAM 3400 medido; teto
`--low-resource` ← pdftotext 63MB + optimize 100MB, ambos medidos) NÃO dependem
dos valores estimados.

### Insight-chave (e seu limite honesto)

A medição mostra que o monopólio do Marker em **math** *poderia* evaporar sem
GPU: `pix2tex` roda em CPU e acertou 100% semântico uma matriz 2×2 complexa.
**MAS** `pix2tex` tem `granularidade=recorte` — precisa receber a **fórmula já
recortada**. O único caminho de recorte MEDIDO é via Marker (detecção de
regiões), que é GPU-required. **Não há, hoje, um detector/cropper de fórmula
CPU-only** (a heurística `DocInfo.math_density` é um float de densidade, não um
cropper). Logo:

- **Com GPU:** Marker já faz math LaTeX nativo (Texify, `math_display/inline:
  forte`). `pix2tex` vira refiner *marginal* (re-extrair fórmulas específicas).
- **Sem GPU:** `pix2tex` é a única fonte de LaTeX-math, mas **falta o cropper que
  o alimenta** → math fica como **Unicode cru** (não-LaTeX), igual ao baseline
  pdftotext. O "`--qualidade` sem GPU recupera math" é um **alvo de design
  bloqueado por BURACO #3** (cropper CPU), não uma entrega atual.

Resumo: sem GPU, hoje, `--qualidade` entrega **prose-alto + math cru**; entrega
math-LaTeX *quando* o cropper CPU existir.

## Detecção de recursos (HostInfo) — thresholds concretos

```python
@dataclass
class HostInfo:
    cpu_cores: int
    ram_gb: float
    gpu_vram_mb: int          # 0 se sem GPU
    has_ollama: bool          # daemon alcançável (gemma/qwen são server-externo)
    has_marker: bool          # shutil.which("marker_single")

    @classmethod
    def detect(cls) -> "HostInfo": ...  # psutil + torch.cuda + ollama ping + which
```

Gates de compatibilidade (de `uso_hardware_acelerador` + `dependencias_externas`):

- **`marker` disponível ⟺ `has_marker AND gpu_vram_mb >= 4096`** (peak medido
  3400; folga). As DUAS condições contam — `has_marker=False` com GPU presente
  **não** habilita marker (ver degradação).
- `gemma3`/`qwen` disponível ⟺ `has_ollama`. VLM e PRIMARY rodam **sequencialmente**
  (Ollama carrega/descarrega), então não há co-residência marker+VLM na VRAM; se
  a VRAM apertar, o VLM cai pra CPU (GPU-opcional). Por isso o gate 4096
  (dimensionado pro marker sozinho) é suficiente.
- `pix2tex`, `pdftotext`, `pdf2md-optimize`: **sempre** (CPU-only, offline).

`pdf2md doctor` já reporta parte disso ([cli.py:201](../../src/pdf2md/cli.py));
expandir para preencher `HostInfo`.

## Caracterização do input (DocInfo) — barato, pré-roteamento

```python
@dataclass
class DocInfo:
    n_pages: int
    has_text_layer: bool      # fitz: get_text() não-vazio na amostra
    math_density: float       # heurística: regiões equation-like / página
    has_raster_logos: bool    # imagens pequenas raster (candidatas a refiner logo)
```

- **`has_text_layer=False` (scan) ⇒ pdftotext NÃO serve** (`scan: nao_medido`,
  Tesseract não testado). Tratado por **guarda de scan** abaixo, antes das gates
  de intent.
- `math_density` alto ⇒ candidato a refiner `pix2tex` **se houver cropper** (ver
  BURACO #3).
- `has_raster_logos` ⇒ candidato a refiner `gemma3`.
- `n_pages` × velocidade do PRIMARY ⇒ estimativa de wall; avisar se proibitivo
  (ex. `--qualidade` marker em 1000pg ≈ 3.6h).

## Guarda de scan (precede TODAS as gates de intent)

Documento sem text-layer não tem caminho CPU (nenhum extrator ativo faz OCR sem
GPU — Surya do Marker é o único OCR medido, e é GPU). Antes de aplicar a gate de
intent:

```
se DocInfo.has_text_layer == False:
    se marker disponível (has_marker AND vram>=4096):  PRIMARY = marker   # Surya OCR
    senão:  ERRO explícito p/ QUALQUER intent:
            "doc é scan (sem text-layer); único OCR é Marker (GPU), indisponível.
             BURACO scan-sem-GPU (Tesseract não testado — T420)."
```

Isso vale inclusive para `--rapido`/`--low-resource`/`--indexacao` pass1 — a
regra "força pdftotext" é **sobreposta** pela guarda de scan (pdftotext em scan =
output vazio, falha silenciosa proibida).

## Gates por intent (assumem text-layer presente; scan já tratado acima)

### PRIMARY por intent × host

| intent | marker disponível (`has_marker` & VRAM≥4096) | senão (sem GPU **ou** sem marker_single) |
|---|---|---|
| `--rapido` | **pdftotext** (velocidade > tudo, mesmo com GPU) | pdftotext |
| `--qualidade` | **marker** | **pdftotext** (degrade c/ aviso — math fica cru, ver BURACO #3) |
| `--balanceado` (default) | **marker** | pdftotext |
| `--auto` | marker | pdftotext |
| `--low-resource` | **pdftotext** (força CPU, RAM≤~63MB; ver teto abaixo) | pdftotext |
| `--indexacao` | pass1: pdftotext · pass2: marker | pass1: pdftotext · pass2: ∅ (sem GPU não há ganho de math sem cropper) |

`--auto` ≡ "melhor stack que CABE": filtra os gates de `--qualidade` por
viabilidade do host. Com `marker` disponível + Ollama, **converge para
`--qualidade`**; sem isso, cai para o melhor caminho CPU.

### REFINERs por intent (add-on, só quando o intent paga o custo E o host comporta)

| refiner | --rapido | --balanceado | --qualidade | --auto | --low-resource |
|---|---|---|---|---|---|
| pix2tex (math, CPU 6.5s/fórmula) — **requer cropper de fórmula (BURACO #3)** | ✗ | ✗ | se math **e** cropper disponível¹ | = --qualidade (se afford) | ✗ |
| gemma3/qwen (logo, 46–112s/img) — requer `has_ollama` | ✗ | ✗ | se `has_raster_logos` **e** `has_ollama` | = --qualidade (se afford) | ✗ |

¹ Hoje o cropper só existe via Marker (GPU). Então, na prática: com marker, math
já é nativo (pix2tex marginal); sem marker, pix2tex **não roda** (sem cropper) →
math cru. `pix2tex` só é roteado se um detector-de-região estiver presente — não
basta `math_density` alto.

### OPTIMIZER por intent

| pdf2md-optimize | --rapido | --balanceado | --qualidade | --auto | --low-resource |
|---|---|---|---|---|---|
| (CPU, determinístico, barato) | ✗ (pré-index não precisa) | ✓ | ✓ | ✓ | **off por padrão** (ligar = +100MB, estoura o teto) |

### Degradação honesta (gate do marker falha em doc text-layer)

Quando o intent pede marker mas o gate falha (`sem GPU` **OU** `marker_single
não instalado`), não erra silenciosamente nem inventa qualidade — degrada para o
melhor CPU e registra na proveniência, **nomeando a causa real**:

```
[aviso] --qualidade pediu marker mas ele está indisponível: {causa}.
        causa ∈ { "sem GPU (VRAM<4096)", "marker_single não instalado" }
        Degradando para CPU-only: pdftotext (prose-alto).
        Math: fica Unicode cru (sem LaTeX) — falta cropper de fórmula CPU (BURACO #3).
        Perde também: layout/tabela do marker.
```

(Scan sem caminho viável já vira ERRO na guarda de scan, para todos os intents —
não só `--qualidade`.)

## Decisões resolvidas

1. **Carregamento de perfis (sem pyyaml; pyproject zerado):** `route()` consome um
   índice machine-readable dep-free, espelhando [corpus/registry.py](../../corpus/registry.py).
   Criar `pdf2md/_profiles.py` com os campos *route-relevant* (id, papel,
   hardware-gate, deps, granularidade, velocidade, wins). Os yaml em
   `docs/profiles/ativo/` seguem como fonte-de-verdade humana; `_profiles.py` é o
   subconjunto que o código consulta. (Alternativa adiada: `pyyaml` como 1ª dep —
   não tem o conflito pillow<11 do marker-pdf.)
2. **Degradação dispara no gate COMPLETO do marker** (`has_marker AND VRAM≥4096`),
   não só em "sem GPU" — cobre o caso "GPU presente, marker não instalado".
3. **`--qualidade` em doc text-layer sem marker = degradar com aviso** (não erro);
   **scan sem marker = ERRO** para todos os intents (guarda de scan).
4. **`--rapido` ignora GPU de propósito** — pdftotext mesmo com GPU (objetivo é
   wall-time mínimo: pré-index de milhares).
5. **`pix2tex` é roteado por presença de cropper-de-região, não por `math_density`.**
   Sem cropper CPU (BURACO #3), `pix2tex` só compõe atrás do Marker.

## API alvo

```python
# pdf2md/routing.py
def route(intent: str, host: HostInfo, doc: DocInfo,
          profiles: dict = load_active_profiles()) -> Pipeline:
    """Pipeline = [Step(algo_id, config), ...] determinístico, com gates acima.
    Inclui .degraded + .rationale (vão pra provenance). Pode levantar ScanNoOCR."""
```

`--indexacao` devolve **2 pipelines** (pass1 imediato, pass2 enfileirável); como
executar pass2 (cron/fila) fica fora do escopo.

**Critério de pass2 (mensurável no output do pdftotext, que é o pass1):**
- `math_density` alto (regiões equation-like / página acima de limiar), E/OU
- proxy de perda estrutural barato: razão de "labels soltos" de figura vetorial
  (padrão medido no e19 — diagrama vira `Fourier transform / NP` solto), ou
  anomalia de densidade de tokens/página.
- (Removido o critério vago "sinais de baixa qualidade": pdftotext é
  determinístico e `alucinacao_risco: zero` — não tem sinal de baixa-confiança
  próprio como o `bloat_ratio` do marker.)

## Critérios de aceitação

- [ ] CLI flags `--rapido`/`--qualidade`/`--balanceado`/`--auto`/`--indexacao`/
      `--low-resource` mutuamente exclusivos (typer); substituem `--quick`/`--best`.
- [ ] `HostInfo.detect()` (psutil + torch.cuda + ollama ping + which); `doctor` usa.
- [ ] `DocInfo.probe(pdf)` barato (amostra de páginas via fitz), incluindo `has_text_layer`.
- [ ] `pdf2md/_profiles.py` dep-free com os 7 perfis ativos (route-relevant subset).
- [ ] `pdf2md/routing.py::route()` implementa: guarda de scan → gates de intent → degradação.
- [ ] `route()` devolve `.degraded` + `.rationale` e levanta erro explícito em scan-sem-OCR.
- [ ] Tests: cada intent × {com-marker, sem-marker-c/GPU, sem-GPU, scan, math-heavy, logo}
      → pipeline esperado (mock de HostInfo/DocInfo). Cobre: degrade-por-sem-GPU,
      degrade-por-sem-marker, ERRO-scan-sem-marker (todos os intents), teto RAM `--low-resource`.

## Critério de promoção (research → fazer)

- [x] 7 perfis no mapa com dados reais (era "3+"). **Satisfeito.**
- [ ] `--rapido` mensuravelmente mais rápido que `--qualidade`: medido **~630×**
      (pdftotext 0.02s/pg vs marker 12.9s/pg) — supera de longe o alvo "2×+".
- [ ] `--auto` adapta corretamente: com-marker→qualidade, sem-GPU→CPU, scan-sem-GPU→erro.
- [ ] `--indexacao` valida em `corpus/examples/` (4 docs livres in-repo): pass1 indexa
      todos; pass2 marca os math-heavy.

## Não-objetivos

- ML para roteamento (over-engineering).
- Profiles cross-hardware via fitting de curva f(n) — futuro [[T091]] (a curva
  `scaling_behavior` já está nos perfis; faltam pontos cross-hardware).
- Pricing/billing; execução distribuída.

## BURACOS abertos que limitam as gates (mapa do que falta medir/construir)

1. **scan-sem-GPU**: PARCIALMENTE FECHADO (Lab e20, 2026-05-31). Scan **impresso**
   tem caminho CPU: Tesseract 5.4.0 (WER 0.052 em Atkins 1874 p80, zero alucinação,
   ~2.74s/pg, 124MB). A guarda de scan pode rotear Tesseract quando marker indisponível
   e o scan é impresso. ABERTO ainda: scan **manuscrito** (Tesseract garbage; Marker
   alucina) e scan ruim (baixo DPI/multi-coluna/tabela) — não medidos.
2. **tabela**: TEDS não medido em nenhum extrator (marker `tabela: medio` estimado) —
   nenhuma gate diferencia qualidade de tabela ainda.
3. **cropper de fórmula CPU**: sem ele, `pix2tex` só compõe atrás do Marker (GPU), e o
   caminho "`--qualidade` CPU com math-LaTeX" fica bloqueado. Candidato a lab dedicado.
4. **cross-hardware**: perfis medidos em 1 host (RTX 3060). Gates de VRAM/velocidade
   não generalizam para outras GPUs sem os pontos f(n) do T091.

## Conexão

- Frente A (validação) + UX. Substitui `--quick`/`--best` em [cli.py](../../src/pdf2md/cli.py).
- Consome [docs/profiles/ativo/](../../docs/profiles/ativo/) (7 perfis) — o **mapa**.
- Depende de [T085](T085_telemetry_module.md) (instrumento ✓) e [T060](T060_mini_corpus_gt_humano.md) (GT N=7 ✓ — qualidade dos perfis ancorada).
- Articula [[arquitetura-instrumento-mapa-roteador]], [[caminho-executivo-vs-cientifico]], [[arquitetura-delta-e-ideal-vs-pratico]].
