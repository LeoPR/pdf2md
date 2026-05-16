# transmutos — meta-arquitetura

> *Doc hóspede neste repo. Tema é da pasta-mãe `transmutos/`; vive aqui
> porque a tese amplificada **muda decisões de design dentro do
> `pdf2md`**. Será promovido para `transmutos/README.md` quando uma
> segunda instância (`pptx2md`, `docx2md`, ...) nascer.*

## O conceito de família

`transmutos/` (do latim *transmutare* — mudar de forma) é o nome da
família de conversores onde `pdf2md` é a primeira instância. O propósito
da família é mais amplo que qualquer conversor individual:

> **Decompilar / recompilar objetos de documentos em geral**, usando
> MD + acessórios como representação canônica intermediária.

Cada conversor instancia o mesmo padrão:

```
formato_origem ──extract──▶ MD + acessórios ──reconstruct──▶ formato_destino
                  ▲                                              │
                  └──────── ciclo de validação ◀─────────────────┘
```

Origem e destino podem ser **o mesmo formato** (round-trip de
validação) ou **formatos diferentes** (uso prático: PDF → editar em
MD → publicar como ODT).

## Tese

Para um conjunto suficientemente amplo de documentos textuais (livros,
papers, slides, formulários, manuais), **MD + acessórios estruturados
é representação canônica viável**. A 1ª-3ª prioridades da
[PHILOSOPHY](PHILOSOPHY.md) (conteúdo + estrutura + otimização semântica)
fica preservada; a 4ª (layout idêntico) é deliberadamente abandonada.

Acessórios cobrem o que MD puro não expressa:
- Imagens (bitmap, SVG, fórmula renderizada)
- Tabelas complexas (HTML inline quando GFM falha)
- Metadata (provenance, sha256, autor, data)
- Estrutura (TOC, references, anchors)

A combinação `MD + acessórios` em pasta versionada é o "objeto
descompilado universal".

## Pré-condições estruturais

A ousadia só funciona se três propriedades arquiteturais forem
respeitadas em cada conversor:

### 1. Modularidade interna por artefato

Cada classe de artefato (texto, imagem, fórmula, tabela, citação) tem
seu próprio pipeline `extract → reconstruct → measure`. O conversor não
trata o documento como blob; trata como composição de mini-pipelines.

No `pdf2md` isso aparece como os níveis L0-L5 da
[PHILOSOPHY §"Validação por fechamento recursivo"](PHILOSOPHY.md#validação-por-fechamento-recursivo-de-ciclos).

### 2. Independência de subobjetos

Cada artefato extraído deve ser **utilizável fora do conversor de
origem**. Uma fórmula extraída do PDF deve ser indistinguível (no MD)
de uma fórmula extraída de DOCX. Uma tabela extraída de slides PPTX
deve casar com uma tabela extraída de ODT.

Sem isso, MD não é canônico — é dialeto. Cada conversor produziria MD
incompatível com os outros, quebrando a tese.

### 3. MD como pivot, não como gargalo

MD deve ser **suficientemente expressivo** para o domínio de interesse,
mas **deliberadamente menos expressivo** que o formato origem em
aspectos não-essenciais (layout fino). Caso contrário viraria
alternativa do formato origem, não pivot.

Quando MD falha como pivot (ex: blueprint CAD com geometria
paramétrica), o conversor reconhece o limite e descarta o caso — não
estica MD para cobrir tudo.

## Como o `pdf2md` é instância desta tese

| Propriedade transmutos | Onde aparece no pdf2md |
|---|---|
| Modularidade por artefato | L0-L5 em [PHILOSOPHY](PHILOSOPHY.md); módulos `pdf2md/{stats,roundtrip,optimize,...}` |
| Independência de subobjetos | MD output usa GFM padrão + KaTeX `$..$`; imagens em pasta `images/`; provenance em block separado |
| MD como pivot expressivo | 4ª prioridade abandonada (formato idêntico); 1ª-3ª preservadas |
| Validação por fechamento | round-trip MD↔PDF + (futuro) pixel-roundtrip; multi-iteration |
| Calibração de reconstrutor | (futuro) MD GT + Tectonic/Typst como diversidade |

O `pdf2md` está construindo as ferramentas e métricas que serão
**reutilizadas** quando o segundo conversor da família nascer. Não é
trabalho perdido — é investimento em arquitetura.

## Pré-requisitos para a segunda instância

Quando `pptx2md` (ou outro) começar, terá baixo custo se:

- O MD canônico produzido pelo `pdf2md` for **bem documentado** (schema
  + convenções de acessórios). [TODO: criar `docs/MD_CANONICAL.md`]
- As métricas de validação forem **independentes do conversor de
  origem**. WER-prosa, TEDS, CDM, count-diffs são todas formato-agnósticas.
- O reconstrutor MD → formato_destino for **modular** (pandoc + Chrome
  + KaTeX já é assim para PDF; ODT seria pandoc → ODT direto).

Inversamente, se essas peças estiverem acopladas demais ao PDF, a
expansão custará reescrita.

## Escopo atual

**Foco: PDF → MD.** A tese transmutos guia decisões de design (não
acoplar ao formato origem onde possível) mas não introduz features
agora. A segunda instância só faz sentido depois que:

- O `pdf2md` fechar o triângulo de métricas (macro/médio/micro)
- O MD canônico estiver documentado
- Houver demanda concreta (uso interno, pedido externo, ou lab
  exploratório)

Até lá, este doc é **norte estratégico**, não roadmap.
