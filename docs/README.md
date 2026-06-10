# Documentação — `pdf2md`

Organizada pelo [framework Diátaxis](https://diataxis.fr/) (Daniele Procida,
~2017). Cada doc pertence a **um** dos 4 quadrantes; não há duplicação.

## Os 4 quadrantes

```
                  ORIENTADO A AÇÃO
                        ↑
                        │
   ┌────────────────────┼────────────────────┐
   │     tutorials/     │      how-to/       │
   │   ────────────     │   ─────────────    │
   │   APRENDER         │   RESOLVER         │
   │   passo-a-passo    │   problema real    │
   │   beginner-friendly│   pragmático       │
   │                    │                    │
   AQUISIÇÃO ◀──────────┼──────────▶ APLICAÇÃO
   │                    │                    │
   │   explanation/     │     reference/     │
   │   ────────────     │   ─────────────    │
   │   ENTENDER         │   CONSULTAR        │
   │   por quê, teoria  │   definições       │
   │   discursivo       │   autoritativas    │
   └────────────────────┼────────────────────┘
                        │
                        ↓
              ORIENTADO A CONHECIMENTO
```

**Regra:** cada conceito tem um lugar canônico. Se aparece em dois
quadrantes, é estilizado de forma distinta:
- **Tutorial** *mostra* (didático, linear)
- **How-to** *aplica* (pragmático, direto ao problema)
- **Reference** *define* (autoritativo, seco, completo)
- **Explanation** *justifica* (discursivo, contextual, "por quê")

Versionamento de conteúdo é responsabilidade do `git`, não de nomes de
arquivo. Não existe `literatura_v2.md` — existe `literatura.md` com `git log`.

---

## Mapa atual

### 🎓 tutorials/ (em construção) — aprender o sistema

*(placeholder — em construção)* Documentos passo-a-passo orientados a
quem nunca usou o `pdf2md`. Cada tutorial é uma sessão completa que
funciona do início ao fim.

### 🛠 [how-to/](how-to/) — resolver problema específico

- [`criar_novo_lab.md`](how-to/criar_novo_lab.md) — protocolo da bancada experimental

*(mais placeholders em construção: extração de livro com TOC, debug de extração ruim, etc.)*

### 📚 [reference/](reference/) — consultar fato autoritativo

- [`md_canonical.md`](reference/md_canonical.md) — schema do MD canônico produzido pelo `pdf2md`
- [`metricas.md`](reference/metricas.md) — painel multi-métrica adotado (M1-M4)
- [`tecnologias.md`](reference/tecnologias.md) — perfis cross-recursos (tempo, mem, GPU, IO)
- [`conventions.md`](reference/conventions.md) — convenções da máquina (paths, venvs, Z:\caches)
- [`corpus/`](reference/corpus/) — manifests do corpus + licensing
  - [`manifest_sources.md`](reference/corpus/manifest_sources.md) — sources canônicos (read-only, originais)
  - [`manifest_canonical.md`](reference/corpus/manifest_canonical.md) — corpus público (CC, arXiv)
  - [`licensing.md`](reference/corpus/licensing.md) — matriz de licenças por categoria
- [`biblioteca/`](reference/biblioteca/INDEX.md) — catálogo de itens externos
  - [`ferramentas.md`](reference/biblioteca/ferramentas.md) · [`papers.md`](reference/biblioteca/papers.md)
  - [`metricas.md`](reference/biblioteca/metricas.md) · [`benchmarks.md`](reference/biblioteca/benchmarks.md)
  - [`glossario.md`](reference/biblioteca/glossario.md)

### 💡 [explanation/](explanation/) — entender por quê

- [`arquitetura.md`](explanation/arquitetura.md) — visão de 4 camadas + sub-docs detalhados em [`arquitetura/01-05`](explanation/arquitetura/)
- [`philosophy.md`](explanation/philosophy.md) — hierarquia de prioridades + eixo de representação + validação por fechamento recursivo + triângulo + calibração + ablação + tradeoffs + convergência
- [`transmutos.md`](explanation/transmutos.md) — tese da família (decompilador/recompilador universal; pdf2md como instância)
- [`avaliacao.md`](explanation/avaliacao.md) — avaliação condensada em formato de artigo (método, resultados medidos, posição na literatura, ameaças à validade)
- [`analise_critica.md`](explanation/analise_critica.md) — revisão crítica do curso do projeto
- [`literatura.md`](explanation/literatura.md) — compilado de literatura (revisão narrativa; fichas detalhadas em `reference/biblioteca/`)
- [`diario.md`](explanation/diario.md) — timeline cronológica das decisões

---

## Onde colocar conteúdo novo

Antes de criar um doc novo, perguntar:

| Pergunta | Resposta | Quadrante |
|---|---|---|
| Quero ensinar do zero alguém que nunca usou? | Sim | `tutorials/` |
| Tenho uma tarefa concreta a resolver? | Sim | `how-to/` |
| Estou descrevendo um fato fixo do sistema? | Sim | `reference/` |
| Estou explicando *por quê* uma decisão foi tomada? | Sim | `explanation/` |
| Não é nada disso? | — | reavaliar: talvez seja issue/ticket, não doc |

**Se aparecer duplicação:** alguma versão está no quadrante errado. Mover,
não duplicar.

---

## Para fora do Diátaxis

| Item | Onde | Por quê |
|---|---|---|
| [`../README.md`](../README.md) | raiz | Entry point + overview rápido + status |
| [`../ROADMAP.md`](../ROADMAP.md) | raiz | Plano macro de execução |
| [`../CHANGELOG.md`](../CHANGELOG.md) | raiz | Releases por versão |
| [`../tickets/`](../tickets/) | raiz | Work items (não são docs) |
| `lab/` | bancada interna (não versionada) | Experimentos descartáveis |

Os experimentos `eNN` (e00–e21) rodam numa **bancada interna** (`lab/`) que não é versionada neste repositório público; hipóteses, critérios e vereditos estão preservados em `tickets/`, e os números promovidos vivem em `docs/profiles/`, `docs/reference/tecnologias.md` e no `CHANGELOG.md`.

---

*Documentação completamente reestruturada em 2026-05-16. Histórico anterior
(`docs/PHILOSOPHY.md`, `docs/ARQUITETURA.md`, ...) preservado via `git log`.*
