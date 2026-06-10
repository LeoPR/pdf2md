---
id: T193
titulo: pass2_warranted — discriminar sparse-garbage de sparse-saudável no braço de densidade
status: open
criado_em: 2026-06-10
fechado_em:
fase: 4
depende_de: [T092]
blocks: []
tags: [routing, indexacao, pass2, recalibracao]
kind: experimento
altitude: execucao
---

## Contexto (motivação MEDIDA — e26/T092)

O braço de densidade do `pass2_warranted` (<800 chars/pág ⇒ enfileira marker)
foi calibrado para text-layer **garbage** (padrão wilson, 261 c/pg de lixo de
OCR). O e26 mediu o braço em docs **sparse-SAUDÁVEIS** born-digital
(diagrama/tabela/logo; análogo real: slides, páginas diagramáticas): ganho de
term-recall pass1→pass2 **nunca positivo** (média −2.7pp, mín **−11.1pp**) —
o marker descarta o texto vetorial interno de figuras (inversão medida no
e24). Hoje o gatilho enfileiraria pass2 que REGRIDE a indexação exatamente
nos docs ricos em diagrama.

## Hipótese

Um discriminador barato sobre o PRÓPRIO output do pass1 separa os dois casos
de baixa densidade: **taxa de não-palavras** (tokens fora de padrão
lexical/dicionário, razão símbolo/letra, entropia de bigramas — escolher 1-2
sinais stdlib) é ALTA em garbage (re-OCR ajuda) e BAIXA em sparse-saudável
(pass2 não ajuda e pode regredir). Alternativa/complemento: verificação
pós-hoc — rodar pass2 e SÓ substituir o doc indexado se o term-recall não
cair (custo: 1 comparação de tokens, zero stack nova).

## Método

1. Corpus de calibração: sparse-saudável = sintético e24 (diagrama/logo/
   tabela, GT conhecido); garbage = wilson (zcache, text-layer real de OCR
   ruim) + degradações sintéticas (embaralhar/charset-noise sobre prosa).
2. Medir o(s) sinal(is) nos dois grupos; escolher threshold com folga (mesmo
   protocolo dos thresholds atuais).
3. Re-rodar o split do e26 com o braço corrigido: densidade só flagga
   garbage; sparse-saudável vai pra ok-pass1 (ou pass2-com-verificação).

## Critério de promoção

Braço de densidade reclassificado de "heurística com risco medido" para
regra medida: zero falso-positivo em sparse-saudável do sintético E flag
mantido no caso garbage (wilson). Atualiza `routing.py` + profiles + e26.

## Critério de descarte

Se nenhum sinal stdlib separar os grupos com folga (overlap nas
distribuições), o braço de densidade vira **pass2-com-verificação pós-hoc**
(substituição condicionada a não-regressão) — solução operacional sem
discriminador. Registrar distribuições medidas no ticket.

## Conexão

- Nasce da falsificação parcial de H2 no [T092](../closed/T092_indexacao_utility_proxies.md).
- Usa a inversão diagrama/logo medida no [T065/e24](../closed/T065_corpus_gt_sintetico.md).
- Afeta `pass2_warranted()` em `src/pdf2md/routing.py` (intent `--indexacao`, T090).
