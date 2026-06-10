# Protocolo da bancada `pdf2md`

> **Nota:** Os experimentos `eNN` (e00–e21) rodam numa **bancada interna** (`lab/`) que não é versionada neste repositório público; hipóteses, critérios e vereditos estão preservados em `tickets/`, e os números promovidos vivem em `docs/profiles/`, `docs/reference/tecnologias.md` e no `CHANGELOG.md`.

Regras de funcionamento do `lab/`, separação entre bancada suja e bancada limpa, e relação com tickets.

## Duas bancadas

| | Bancada suja (`lab/`) | Bancada limpa (`src/`) |
|---|---|---|
| **O que mora** | Experimentos, hipóteses sendo testadas | Código estável, validado |
| **Mutável?** | Sim — descartável a qualquer momento | Não — mudança via PR + critério |
| **Deps** | `requirements.txt` por experimento, em venv isolado | `pyproject.toml` central, controlado |
| **Vida útil** | Curta (dias a semanas) | Longa (até refactor planejado) |
| **Ticket** | Não obrigatório; experimento é sua própria documentação | Cada peça vem de um ticket |

## Princípios

1. **Não instalar no venv principal** sem critério registrado e ticket aprovado.
2. **Cada experimento tem seu venv** em `Z:\venvs\pdf2md_lab_eNN`.
3. **Hipótese e critério escritos antes** — `lab/eNN/README.md` preenchido em "Hipótese", "Critério de promoção", "Critério de descarte" antes de rodar qualquer coisa.
4. **Veredito explícito no fim** — `RESULT.md` registra promoção/descarte/congelamento, sem zona cinza.
5. **Limpar a mesa é primeira classe** — ao descartar, deletar pasta + venv. A trilha histórica fica na bancada interna do autor (não no repositório público) e (opcionalmente) em `lab/_archive/`.

## Ciclo de vida de um experimento

```
   criar (cp _template)
       │
       ▼
   preencher README.md (hipótese + critérios)
       │
       ▼
   criar venv (Z:\venvs\pdf2md_lab_eNN)
       │
       ▼
   instalar requirements.txt
       │
       ▼
   rodar run.ps1 → out/
       │
       ▼
   preencher RESULT.md (métricas + veredito)
       │
       ▼
   ┌─────────┬──────────┬────────────┐
   ▼         ▼          ▼
 promover  descartar  congelar
   │          │          │
   ▼          ▼          ▼
src/      rm -rf     .frozen
+ ticket   + venv     (mantém pasta)
   │          
   ▼
.discarded → eventual rm -rf
```

## Critério de promoção (default)

Para um experimento ser promovido a `src/`, precisa cumprir TODOS:

1. **Hipótese clara** validada pelas métricas registradas em `RESULT.md`
2. **Reproduzível** — alguém com acesso ao repo + corpus consegue rodar e obter resultados equivalentes
3. **Vence baseline** — se há baseline equivalente em `src/`, o experimento bate em pelo menos 1 dimensão sem regredir nas outras
4. **Tem ticket associado** com critério "feito" definido
5. **Deps compatíveis** — não introduz conflitos no `pyproject.toml` (caso introduza, vira ticket de infra antes)

Para experimentos exploratórios (ex.: "como Nougat se sai?"), promoção pode ser apenas **decisão documentada em `docs/`**, não código novo.

## Critério de descarte (default)

Descarta com confiança se:

- Métrica falha o critério de descarte registrado no `README.md`
- Tempo de execução inviável para o corpus alvo
- Deps conflitantes com pipeline principal e ganho não justifica isolamento permanente
- Replicação do experimento já existe (duplicidade)

## Status de experimento (sufixo)

Arquivo vazio na pasta do experimento marca status:

- `.live` — em curso (default)
- `.frozen` — concluído mas não promovido nem descartado (referência)
- `.discarded` — concluído como "não vingou", aguardando `rm -rf`

```powershell
# Marcar como discarded
New-Item lab\eNN_<slug>\.discarded
```

## Relação com tickets

- **Tickets** capturam infra, decisões arquiteturais, decisões de produto. Vida longa.
- **Experimentos** capturam hipóteses testáveis. Vida curta.
- Um ticket pode dar origem a vários experimentos. Cada experimento aponta de volta para o ticket-mãe em `README.md`.
- Quando um experimento é promovido, o ticket associado pode mudar de status (open → closed) ou abrir um novo ticket de implementação.

## O que **nunca** entra em `lab/`

- Código que outras partes do projeto importam → vai para `src/`
- Decisões de macro (arquitetura, fases, hierarquia) → vai para `tickets/` ou `docs/`
- Manifests de corpus → vai para `corpus/`
