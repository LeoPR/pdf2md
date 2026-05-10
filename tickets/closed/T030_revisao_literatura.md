---
id: T030
titulo: Revisão de literatura inicial
status: open
criado_em: 2026-05-09
fechado_em:
fase: 0
depende_de: []
blocks: [T031]
tags: [infra, literatura, research]
kind: infra
---

## Contexto

Antes de inventar métricas e comparar ferramentas, vale conhecer o que já foi feito. Round-trip extraction como técnica de validação, métricas estabelecidas para PDF→texto, benchmarks públicos disponíveis — tudo isso provavelmente já tem literatura, e ignorar gera retrabalho.

## Objetivo

Produzir `docs/LITERATURA.md` com revisão concisa cobrindo:

1. **Métricas estabelecidas** para conversão PDF→texto/MD:
   - WER (Word Error Rate) para texto
   - TEDS (Tree Edit Distance Score) para tabelas
   - BLEU sobre LaTeX para fórmulas
   - Estrutura: comparação TEI / DocTags / similar
2. **Benchmarks públicos**: DocILE, DocBank, PubLayNet, ScienceQA, Marker-bench, Nougat-bench
3. **Ferramentas com paper acadêmico**: Marker (Datalab), Nougat (Meta 2023), MinerU (Shanghai AI Lab 2024), GROBID, pix2tex
4. **Round-trip como técnica de validação**: quem usou? Pandoc roundtrip tests; pdfminer.six; alguns papers de Document AI
5. **Reconstrutor MD→PDF**: state-of-the-art (Quarto, Typst, LaTeX, weasyprint) com tradeoffs

## Critérios de aceitação

- [ ] `docs/LITERATURA.md` existe, ~3-5 páginas
- [ ] Cada referência com link + 1-2 frases de relevância
- [ ] Decisões iniciais informadas: que métricas adotar como base
- [ ] Lista de questões abertas (que precisam de experimento real para responder)

## Não-objetivo

- Revisão exaustiva tipo paper acadêmico
- Cobertura de áreas adjacentes (OCR clássico, vision-language models genéricos)

## Sugestão de execução

Pode ser feito em uma sessão de 1-2h via web search. Não precisa rodar código nem instalar deps.
