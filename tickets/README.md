# Tickets — convenção e fluxo (`pdf2md`)

Sistema de tickets local. Versionado junto com o código no git — cada
mudança de status é um commit.

Sistema herdado do AulaQuantum em 2026-05-08 (separação T400). Faixas
T100-T199 e T400-T499 originais foram **migradas integralmente** para
cá. T001-T099, T200-T299, T300-T399 ficaram lá.

## Estrutura

```
tickets/
├── README.md          (este arquivo)
├── open/              tickets criados, sem trabalho ativo
├── in_progress/       trabalho em andamento (somente 1-3 ao mesmo tempo)
├── blocked/           bloqueados aguardando decisão/dependência externa
├── research/          investigação aberta sem entregável definido
├── closed/            concluídos (com resultado registrado)
└── _archive/          fechados há mais de 60 dias (rotação periódica)
```

Movimentação entre pastas = `git mv`. O histórico do ticket fica preservado.

## Naming

Cada ticket é um arquivo `T<NNN>_<slug-curto>.md`. Numeração crescente, sem reuso.

Slug em snake_case, no máximo 5-6 palavras. Sem prefixos de status (a pasta indica).

## Formato do ticket

Frontmatter YAML obrigatório, depois markdown livre:

```markdown
---
id: T012
titulo: Marker PDF extraction com GPU
status: closed
criado_em: 2026-05-05
fechado_em: 2026-05-05
fase: 1
depende_de: []
blocks: [T013, T014]
tags: [conversor, marker, gpu]
---

## Contexto
Por que esse ticket existe.

## Objetivo
Resultado esperado, mensurável.

## Critérios de aceitação
- [ ] Item 1
- [ ] Item 2

## Notas / decisões
Registro do que foi decidido durante a execução.

## Resultado (quando fechado)
O que ficou pronto, links para artefatos, métricas finais.
```

## Status — fluxo

```
   open ──► in_progress ──► closed
              │       ▲
              ▼       │
            blocked ──┘
```

## Convenções de commit

```
git mv tickets/open/T012_xxx.md tickets/in_progress/
git commit -m "T012: open → in_progress"
```

Mensagens curtas com a métrica/decisão chave no fim.

## Numeração — blocos (no contexto pdf2md)

| Faixa | Tema |
|---|---|
| T100-T199 | Pipeline de extração (marker, restructure, round-trip, stats) |
| T130-T139 | Otimização adaptativa de imagens (família T130) |
| T400-T499 | Projeto autônomo (testes alternativos, corpus livre, fallback low-resource, design philosophy) |
| T900+ | Reservados para emergências/hotfix sem categorização |

T001-T099 (infra), T200-T299 (disciplina) e T300-T399 (pesquisa
complementar) **não se aplicam aqui** — pertencem ao AulaQuantum.

## Rotação para `_archive`

Tickets `closed` há mais de 60 dias migram para `_archive` por:
```
git mv tickets/closed/T012_xxx.md tickets/_archive/
```
Não são apagados — só saem do caminho da listagem ativa.
