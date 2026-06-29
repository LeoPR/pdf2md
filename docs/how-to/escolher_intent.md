# How-to: escolher o intent (`--intent`)

O `pdf2md convert FILE.pdf --intent <nome>` (ou `pdf2md route` para dry-run) passa
um **intent macro** e o roteador (T090) escolhe a stack medindo host + documento.
Você diz o que quer; ele decide o caminho mais barato que satisfaz — e **degrada
com aviso honesto** se a stack ideal não couber no host (nunca finge qualidade nem
quebra em silêncio). `pdf2md doctor --intent <nome>` mostra o que aquele intent
usaria **neste** host.

**Os intents aceitam inglês ou português** (equivalentes, com ou sem acento):
`fast`/`rapido` · `quality`/`qualidade` · `balanced`/`balanceado` · `auto` ·
`indexing`/`indexacao` · `low-resource`.

## Tabela de decisão

| Intent (EN / PT) | Use quando… | PRIMARY (com marker/GPU) | PRIMARY (sem GPU) |
|---|---|---|---|
| `fast` / `rapido` | indexar/pré-processar em massa; quer wall-time mínimo | pdftotext (ignora GPU **de propósito**) | pdftotext |
| `low-resource` | máquina magra (RAM apertada) | pdftotext (teto 160 MB) | pdftotext |
| `indexing` / `indexacao` | milhares de docs; refinar só os que valem | pass1 pdftotext · pass2 marker enfileirável | pass1 pdftotext · pass2 ∅ |
| `balanced` / `balanceado` (default) | uso geral | marker | pdftotext (adapta, não degrada) |
| `quality` / `qualidade` | máxima fidelidade; math/layout/tabelas | marker (+ refiners) | pdftotext + pix2tex (**degrada c/ aviso**) |
| `auto` | "faça a melhor coisa que cabe aqui" | converge p/ qualidade | melhor caminho CPU |

## O que cada intent liga

- **REFINERs (só `--qualidade`/`--auto`):** `pix2tex` entra se há math **e** runtime
  pix2tex (`PDF2MD_PIX2TEX_PYTHON`); com marker como PRIMARY o math já é nativo (pix2tex
  é redundante). `gemma3` (via Ollama) transcreve **logos** — nunca página inteira.
- **OPTIMIZER (imagens):** liga em balanceado/qualidade/auto; **off** em rapido/indexação;
  em `--low-resource` só liga se couber no teto de 160 MB (senão registra o porquê).
- **Matriz/multi-linha:** pix2tex é fraco (~0.50 — trunca/embaralha); o roteador **avisa** e
  recomenda marker/GPU. Display de linha única é confiável (~0.80).

## `--indexacao`: o modelo 2-pass

- **pass1** (imediato): pdftotext indexa **todos** os docs — rápido, offline, determinístico.
- **pass2** (enfileirável, não roda na hora): só os docs com **perda recuperável** medida no
  output do pass1 — **math denso** (`≥1.0/kchar`) **ou densidade de texto anômala** (`<800
  chars/pág`, sinal de text-layer esparso/garbage). `ExecResult.needs_pass2` marca quais.
  Como executar o pass2 (cron/fila) fica fora do escopo do roteador.

## Scan (sem text-layer)

A **guarda de scan** precede tudo: doc sem text-layer → marker (Surya/GPU) se houver, senão
Tesseract (CPU, impresso WER 0.052); se nenhum OCR disponível, **erro explícito** para
qualquer intent (não gera saída vazia silenciosa). Manuscrito cursivo falha de forma honesta.

## Exemplos

```bash
pdf2md doctor --intent qualidade          # o que falta p/ qualidade neste host
pdf2md route paper.pdf --intent auto      # dry-run do pipeline escolhido
pdf2md convert paper.pdf --intent rapido  # CPU puro, sem instalar nada externo
```

Ver também: [`reference/cli.md`](../reference/cli.md) · [perfis medidos](../profiles/) ·
[ticket T090](../../tickets/closed/T090_macro_intent_routing.md).
