# `docs/profiles/` — catálogo de algoritmos por dimensão

*Criado 2026-05-19 pós workflow `revisao-visao-macro-multi-algoritmo`.*

Estrutura consumível por código (`yaml.safe_load`) que serializa o catálogo de
algoritmos testados ou previstos no projeto, organizados por dimensão segundo a
visão macro "vários algoritmos por perspectiva, não um único vencedor"
(ver [ROADMAP § Duas altitudes](../../ROADMAP.md) + memória `project_telemetria_profile_routing`).

## Particionamento (refutação R2 do workflow)

```
docs/profiles/
├── _schema.yaml             # template canônico das chaves
├── ativo/                   # PROFILE_MAP_ATIVO — alimenta route() do T090 futuro
│   └── *.yaml               # confiança ≥5/8 dimensões medidas end-to-end
├── inferido/                # ROADMAP_INFERIDO — alimenta priorização de labs, NÃO o roteador
│   └── *.yaml               # algoritmos previstos ou parcialmente testados (escopo nicho)
└── descartado/              # registro histórico — sem vantagem em nenhuma dimensão
    └── *.yaml               # mantidos para evitar re-testar e documentar motivos
```

**Critério de promoção `inferido → ativo`**:
- ≥5 das 8 dimensões core medidas end-to-end (não inferidas)
- Pelo menos 1 dimensão vencida no espaço total
- Lab origem documentado

**Critério de demoção `ativo → descartado`**:
- Algoritmo dominado em **todas** as dimensões por outro do mesmo escopo
- Aplica regra do usuário: "para que usar um sem benefício em qualquer dimensão?"

## Dimensões catalogadas (8 core + 12 extensões do workflow)

### Eixo RECURSOS (3 dim)

- `velocidade_wall_full_doc` (s ou s/pg) — tempo de parede end-to-end
- `uso_hardware_acelerador` (CPU-only / GPU-opcional / GPU-required + pico_vram_mb)
- `uso_memoria_RAM_host` (MB)

### Eixo FIDELIDADE (4 dim)

- `qualidade_prose_texto` (token_similarity ou WER)
- `qualidade_math_semantica` (WER-LaTeX-semântico ou qualitativo)
- `qualidade_tabelas` (TEDS ou qualitativo)
- `preservacao_numeros_citacoes` (qualitativo) — 1ª prioridade philosophy.md

### Eixo PROPRIEDADES ARQUITETURAIS (5 dim — promovidos do workflow R1)

- `determinismo` (deterministico-com-seed / estavel-sem-seed / nao-deterministico)
- `estabilidade_runtime` (taxa_crash% + taxa_output_vazio%)
- `granularidade_operacional` (recorte / pagina / documento)
- `riqueza_formato_intermediario` (texto-puro / MD / MD+LaTeX / MD+DocTags / HTML+anotacoes)
- `licenca` (MIT / Apache-2.0 / HPND / GPL-3 / proprietario)

### Eixo OPERACIONAL (3 dim)

- `dependencias_externas` (offline / download-on-demand / server-externo / API-cloud)
- `tempo_cold_start` (s) — separado de inferência (workflow R1)
- `cobertura_tipo_documento` (livro/paper/slides/scan/form com qualitativo cada)

## Consumo previsto

```python
from pathlib import Path
import yaml

def load_active_profiles(root=Path("docs/profiles/ativo")) -> dict[str, dict]:
    return {f.stem: yaml.safe_load(f.read_text()) for f in root.glob("*.yaml")}

def filter_by_dimension(profiles, dim, predicate) -> list[dict]:
    return [p for p in profiles.values()
            if predicate(p.get("dimensoes", {}).get(dim))]
```

Quando `src/pdf2md/routing.py` (T090) for implementado, vai consumir
`load_active_profiles()` para filtrar candidatos por intent macro.

## Não-objetivo

- Substituir [`docs/reference/tecnologias.md`](../reference/tecnologias.md) — esse continua sendo narrativa human-readable. Este aqui é máquina-consumível
- Catalogar exaustivamente — só algoritmos com lab/origem ou previstos no ROADMAP
- Decidir "melhor algoritmo" — a estrutura mostra trade-offs, não rankings

## Próximos passos

1. ~~Materializar 6 perfis MEDIDOS em `ativo/`~~ ✓ (2026-05-19)
2. ~~Materializar 4-5 perfis PREVISTOS em `inferido/`~~ ✓ (2026-05-19)
3. ~~Materializar 3 perfis DESCARTADOS em `descartado/`~~ ✓ (2026-05-19)
4. Lab E1: cobrir buraco "CPU-only end-to-end" (pdftotext + PyMuPDF + Tesseract)
5. Lab E2: instrumentar `estabilidade_runtime` (10 runs) + cold-start separado
6. Reescrever T090 spec com gates explícitos por intent macro
