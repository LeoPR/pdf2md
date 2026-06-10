---
id: T402
titulo: Pipeline fractal — ciclo recursivo extract/reconstruct/measure por artefato
status: research
criado_em: 2026-05-15
fechado_em:
fase: 4
depende_de: [T401]
blocks: []
tags: [meta, arquitetura, recursao, modularidade, transmutos]
kind: decisao
---

## Contexto

O conversor atual trata o PDF como composição de artefatos (texto,
imagens, tabelas, fórmulas), mas o padrão `extract → reconstruct →
measure` está implementado **só no nível-doc** ([T103](../closed/T103_round_trip_test_script.md)).

Cada artefato individual também tem (ou pode ter) o mesmo padrão:

```
imagem ─extract─▶ (texto+fonte+geometria, residual) ─reconstruct─▶ imagem'
                                                        ↑
                                              compare(imagem, imagem')
```

```
fórmula_em_pixel ─extract(pix2tex)─▶ LaTeX ─reconstruct(KaTeX)─▶ fórmula_renderizada
                                                                       ↑
                                                          compare(pixel, renderizada)
```

```
diagrama_line_art ─extract(potrace)─▶ SVG ─reconstruct(browser)─▶ raster'
                                                                     ↑
                                                       compare(raster, raster')
```

Tickets [T132](T132_potrace_svg_line_art.md) /
[T133](T133_detector_de_formula.md) / [T134](T134_pix2tex_formulas.md) /
[T180](../open/T180_reconstrucao_vetorial_imagens.md) implementam pontas
individuais desse padrão sem nomear que **são instâncias do mesmo
template recursivo**. Sem articulação, viram features cosméticas; com
articulação, viram peças composicionais de uma arquitetura coerente.

Articulado em [PHILOSOPHY §"Validação por fechamento recursivo"](../../docs/explanation/philosophy.md#validação-por-fechamento-recursivo-de-ciclos)
como L0→L5. Este ticket é o **meta** que organiza as instâncias.

## Decisão de arquitetura

(D1) Toda nova capacidade de extração de artefato (potrace, pix2tex,
table-transformer, etc.) **deve implementar** o trio:

```python
extract(artefato_raw) -> representação_semântica
reconstruct(representação_semântica) -> artefato_render
measure(artefato_raw, artefato_render) -> métrica de fechamento
```

(D2) Cada nível tem **critério de promoção** independente:
- L1 (figura→SVG): SSIM ≥ 0.95 ou bytes ≥ 50% menor
- L2 (fórmula→LaTeX): CDM F1 ≥ 0.95 + compile-OK
- L3 (tabela→MD/HTML): TEDS ≥ 0.90
- L4 (logo→texto+brasão): SSIM ≥ 0.95 + texto WER ≤ 5%

Falhar critério ⇒ **descer um nível** ([PHILOSOPHY §"Eixo de representação"](../../docs/explanation/philosophy.md#eixo-de-representação)).

(D3) Reusar **mesma calibração** ([T072](T072_calibracao_reconstrutor.md))
em cada nível: medir ruído base do reconstrutor naquele nível antes de
atribuir erro à extração.

(D4) Compor erro globalmente: erro do documento = composição (não soma)
dos erros locais por bbox/artefato. Triângulo macro/médio/micro
([PHILOSOPHY §"Triângulo"](../../docs/explanation/philosophy.md#triângulo-de-métricas-macro--médio--micro))
é a função de composição.

## Implicações práticas

- [T132](T132_potrace_svg_line_art.md) precisa ter `measure(raster, raster_from_svg)` antes de ativar — não só "gerar SVG"
- [T134](T134_pix2tex_formulas.md) precisa ter CDM + compile-OK como gate, não só "extrair LaTeX"
- [T180](../open/T180_reconstrucao_vetorial_imagens.md) já tem critério SSIM + texto-WER explícitos — modelo bom
- Refatorar API comum: `pdf2md/artifacts/<type>/{extract,reconstruct,measure}.py`?
  (decisão adiada até segunda instância — over-engineering hoje)

## Critérios de aceitação

- [ ] Documentar o template recursivo em `docs/explanation/arquitetura.md` (seção nova "Pipeline fractal por artefato")
- [ ] Atualizar T132, T133, T134, T180: cada um declara explicitamente
      sua tripla `(extract, reconstruct, measure)` no front matter ou
      seção "Método"
- [ ] Reusar pixel-roundtrip ([T070](T070_pixel_roundtrip_validador_visual.md))
      como `measure` default para artefatos visuais
- [ ] Reusar calibração ([T072](T072_calibracao_reconstrutor.md)) como
      ferramenta para subtrair ruído base de cada nível

## Critério de promoção

- Pelo menos 2 dos 4 tickets de artefato (T132, T133, T134, T180)
  alinhados ao template — então o padrão é demonstrado, não só descrito
- Adicionar caso explícito em [META_TRANSMUTOS](../../docs/explanation/transmutos.md):
  "o padrão escala para a 2ª instância da família — pptx2md teria
  L0 (slide→MD), L1 (shape→SVG), L2 (fórmula embed→LaTeX), etc."

## Não-objetivo

- Implementar framework genérico de "ciclos recursivos" agora (over-engineering)
- Mover código existente para nova hierarquia de pastas — refatorar
  só quando segunda instância da família demandar
- Definir API formal de `Artifact` como ABC/Protocol — primeiro
  demonstrar com 2-3 instâncias concretas (T132, T134), depois abstrair

## Conexão

- Meta-design (kind: decisao)
- Articula [PHILOSOPHY §"Validação por fechamento"](../../docs/explanation/philosophy.md#validação-por-fechamento-recursivo-de-ciclos)
- Articula [META_TRANSMUTOS §"Pré-condições estruturais"](../../docs/explanation/transmutos.md#pré-condições-estruturais)
- Organiza [T132](T132_potrace_svg_line_art.md), [T133](T133_detector_de_formula.md),
  [T134](T134_pix2tex_formulas.md), [T180](../open/T180_reconstrucao_vetorial_imagens.md)
- Depende de [T401](../open/T401_documentar_hierarquia_de_prioridades.md) (já documentado em PHILOSOPHY)
