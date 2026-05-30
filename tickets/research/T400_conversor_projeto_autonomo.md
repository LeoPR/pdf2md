---
id: T400
titulo: Conversor PDF↔MD como projeto autônomo (meta-ticket)
status: research
criado_em: 2026-05-07
fechado_em:
fase: 1
depende_de: [T100]
blocks: []
tags: [conversor, projeto-autonomo, meta]
kind: decisao
altitude: meta
---

## Gatilho de separação `transmutos/` (rescope 2026-05-19)

Workflow reavaliação-2-propósitos resolveu a tensão "1 repo vs 2 repos" como
**gatilho condicional explícito**:

> Separar `transmutos/` em repo próprio **SE E SOMENTE SE** segunda instância
> concreta (`pptx2md`, `docx2md`, `html2md`, etc.) for iniciada **com código**.
> Até lá, transmutos vive como [`docs/explanation/transmutos.md`](../../docs/explanation/transmutos.md)
> no próprio pdf2md, **sem custo de coordenação**.

Isso transforma a ansiedade "separar agora ou não?" em decisão futura
objetiva. Estado atual: 1 instância (pdf2md), 0 segunda — não separar.

## Contexto

A faixa T100-T199 é "conversor aplicado ao AulaQuantum". Mas o conversor já está
maduro o suficiente para virar um projeto autônomo, reutilizável em qualquer
livro/paper. Esta faixa T400-T499 cobre tudo que vai além do uso interno.

## Escopo deste meta-ticket

- Testar ferramentas alternativas (Nougat, MinerU, Mathpix, pdftotext)
- Documentar fallback para usuários sem GPU / com menos recursos
- Montar corpus de testes com PDFs livres/CC
- Investigar compactação MD-como-formato-de-transporte (vs PDF)
- Estabelecer princípios de design (já: `tools/pdf_md_converter/PHILOSOPHY.md`)

## Status — sub-tickets

- T401 (open): Hierarquia de prioridades — registrada em `PHILOSOPHY.md` ✓
- T410 (research): Testar ferramentas alternativas
- T420 (research): Fallback low-resource (sem GPU, sem ML pesado)
- T430 (open): Corpus livre para testes (URLs + licenças)
- T440 (research): MD-como-formato-de-transporte (compactação vs PDF)

## Por que está em `research/`

Este é um guarda-chuva. Sub-tickets concretos viram `open/` quando ativados.
O guarda-chuva fica em `research/` permanentemente como "norte" do projeto.

## Quando promover trabalho

- Quando alguém quiser usar o conversor em outro projeto/livro fora do AulaQuantum
- Quando o conversor for empacotado como `pip install` (T70-T74 do ROADMAP)
- Quando alguém pedir "rode num PDF que não tem GPU disponível"

## Não-objetivo

Não é objetivo deste meta-ticket replicar funcionalidade dos `T100-T199`
(que já está coberto). É expansão lateral, não duplicação.
