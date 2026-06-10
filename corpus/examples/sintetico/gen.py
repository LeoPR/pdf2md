"""Corpus sintético GT-por-construção (T065/e24) — gerador determinístico.

A fonte canônica (gt/) é escrita POR este script e é a resposta certa byte a
byte: fórmulas canônicas são fatos matemáticos (17 U.S.C. 102(b), merger
doctrine; Lei 9.610 art. 8º I) tipografadas por nós; prosa/tabelas/diagramas/
logos são inventados. 100% autoral, zero copyright de terceiros — publicável.

Tudo determinístico (crc32, sem random/hash() salteado): re-rodar `gen`
reproduz gt/ idêntico. Os PDFs em pdf/ são RENDERS, não source (metadata:
HeadlessChrome+Skia para katex/, Tectonic para cm/) — eixo delta-E de
renderer: o GT é um só, cada renderer é um adapter.

Uso:
  python gen.py gen                # (re)escreve gt/ + manifest.json
  python gen.py fixtures           # re-renderiza o subset commitado em pdf/
  python gen.py render <out_dir>   # renderiza os 75 itens (bancada/instrumento)

`fixtures`/`render` precisam de pandoc+chrome (caminho KaTeX, via
pdf2md.pdfs.md_to_pdf); o eixo CM precisa de tectonic no PATH ou
PDF2MD_TECTONIC (external-capability, modelo do doctor — nunca no pyproject).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).parent
GT = HERE / "gt"
PDF = HERE / "pdf"

# ------------------------------------------------------------------ fontes --
FORMULAS_DISPLAY = [
    ("emc2", r"E = m c^2"),
    ("schrodinger", r"i\hbar \frac{\partial}{\partial t}\Psi(x,t) = \hat{H}\,\Psi(x,t)"),
    ("euler", r"e^{i\pi} + 1 = 0"),
    ("fourier", r"\hat{f}(\xi) = \int_{-\infty}^{\infty} f(x)\, e^{-2\pi i x \xi}\, dx"),
    ("gauss_int", r"\int_{-\infty}^{\infty} e^{-x^2}\, dx = \sqrt{\pi}"),
    ("bayes", r"P(A \mid B) = \frac{P(B \mid A)\, P(A)}{P(B)}"),
    ("entropy", r"S = -k_B \sum_i p_i \ln p_i"),
    ("binomial", r"(x+y)^n = \sum_{k=0}^{n} \binom{n}{k} x^{n-k} y^{k}"),
    ("maxwell_gauss", r"\nabla \cdot \mathbf{E} = \frac{\rho}{\varepsilon_0}"),
    ("bell_state", r"\lvert \Phi^{+} \rangle = \frac{1}{\sqrt{2}}\bigl(\lvert 00 \rangle + \lvert 11 \rangle\bigr)"),
]
FORMULAS_MATRIZ = [
    ("hadamard", r"H = \frac{1}{\sqrt{2}} \begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}"),
    ("pauli_x", r"\sigma_x = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}"),
    ("pauli_y", r"\sigma_y = \begin{pmatrix} 0 & -i \\ i & 0 \end{pmatrix}"),
    ("pauli_z", r"\sigma_z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}"),
    ("rot2d", r"R(\theta) = \begin{pmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{pmatrix}"),
    ("cnot", r"\mathrm{CNOT} = \begin{pmatrix} 1&0&0&0 \\ 0&1&0&0 \\ 0&0&0&1 \\ 0&0&1&0 \end{pmatrix}"),
    ("densidade", r"\rho = \frac{1}{2} \begin{pmatrix} 1 & e^{-i\phi} \\ e^{i\phi} & 1 \end{pmatrix}"),
    ("bmatrix4", r"A = \begin{bmatrix} 2&0&1&3 \\ 0&1&4&0 \\ 1&4&0&2 \\ 3&0&2&1 \end{bmatrix}"),
]
FORMULAS_MULTILINE = [
    ("quadratica", "\\begin{aligned} ax^2+bx+c &= 0 \\\\ x &= \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a} \\end{aligned}"),
    ("soma_geom", "\\begin{aligned} S_n &= \\sum_{k=0}^{n} r^k \\\\ &= \\frac{1-r^{n+1}}{1-r} \\end{aligned}"),
    ("cases_abs", "\\lvert x \\rvert = \\begin{cases} x & x \\ge 0 \\\\ -x & x < 0 \\end{cases}"),
    ("dist_pontos", "\\begin{aligned} d(p,q) &= \\sqrt{\\sum_i (p_i - q_i)^2} \\\\ &\\ge 0 \\end{aligned}"),
    ("prod_tel", "\\begin{aligned} \\prod_{k=1}^{n} \\frac{k+1}{k} &= \\frac{n+1}{1} \\\\ &= n+1 \\end{aligned}"),
    ("exp_serie", "\\begin{aligned} e^x &= \\sum_{n=0}^{\\infty} \\frac{x^n}{n!} \\\\ &= 1 + x + \\frac{x^2}{2} + \\cdots \\end{aligned}"),
]

WORDS = ("o sistema", "a métrica", "o operador", "a transformação", "o algoritmo",
         "a convergência", "o resíduo", "a projeção", "o autovalor", "a norma")
VERBS = ("preserva", "minimiza", "decompõe", "estabiliza", "aproxima",
         "normaliza", "satura", "delimita", "propaga", "quantifica")
OBJS = ("a energia total", "o erro de truncamento", "a base ortonormal",
        "o espaço de estados", "a função de custo", "o fluxo numérico",
        "a entropia relativa", "o gradiente discreto", "a malha adaptativa",
        "o invariante topológico")


def _stable(s: str) -> int:
    """hash determinístico (hash() de str é salteado por processo)."""
    import zlib
    return zlib.crc32(s.encode("utf-8"))


def _w(seed: str) -> str:
    pool = ("alfa", "beta", "gama", "delta", "sigma", "fluxo", "norma",
            "malha", "campo", "fase", "modo", "polo")
    return pool[_stable(seed) % len(pool)]


def _num(seed: str, kind: int) -> str:
    n = _stable(seed)
    if kind == 0:
        return f"{(n % 90000) / 10:,.1f}"          # 1,234.5 (milhar+decimal)
    if kind == 1:
        return f"{-(n % 500)}"                     # negativo
    return f"{n % 100}%"                           # percentual


def prose_par(seed: int, n_sent: int = 5) -> str:
    sents = []
    for k in range(n_sent):
        i = (seed * 7 + k * 3) % 10
        j = (seed * 5 + k * 11) % 10
        m = (seed * 13 + k * 7) % 10
        sents.append(f"{WORDS[i].capitalize()} {VERBS[j]} {OBJS[m]} sob condições de contorno regulares.")
    return " ".join(sents)


def _t1_grid(k: int) -> str:
    head = "| item | classe | valor |"
    sep = "|---|---|---|"
    rows = "\n".join(
        f"| {_w(f'a{r}{k}')}_{r}{k} | {_w(f'b{r}{k}')} | v{r}_{k} |"
        for r in range(4))
    return f"{head}\n{sep}\n{rows}"


def _t2_align_num(k: int) -> str:
    head = "| métrica | média | desvio | taxa |"
    sep = "|:---|---:|---:|:---:|"
    rows = "\n".join(
        f"| {_w(f'm{r}{k}')}_{r} | {_num(f'x{r}{k}', 0)} | {_num(f'y{r}{k}', 1)} | {_num(f'z{r}{k}', 2)} |"
        for r in range(5))
    return f"{head}\n{sep}\n{rows}"


def _t3_multiline(k: int) -> str:
    head = "| etapa | descrição | nota |"
    sep = "|---|---|---|"
    rows = "\n".join(
        f"| e{r}_{k} | {_w(f'p{r}{k}')} primeira<br>{_w(f'q{r}{k}')} segunda | n{r}{k} |"
        for r in range(4))
    return f"{head}\n{sep}\n{rows}"


def _t4_span(k: int) -> str:
    # k=0 rowspan; k=1 colspan; k=2 ambos — pipe-table NÃO representa (T440)
    if k == 0:
        return ('<table><tr><th>grupo</th><th>par</th><th>val</th></tr>'
                '<tr><td rowspan="2">G0</td><td>p0</td><td>1</td></tr>'
                '<tr><td>p1</td><td>2</td></tr>'
                '<tr><td rowspan="2">G1</td><td>p2</td><td>3</td></tr>'
                '<tr><td>p3</td><td>4</td></tr></table>')
    if k == 1:
        return ('<table><tr><th colspan="2">cabeçalho duplo</th><th>val</th></tr>'
                '<tr><td>a0</td><td>b0</td><td>5</td></tr>'
                '<tr><td colspan="2">linha fundida</td><td>6</td></tr>'
                '<tr><td>a2</td><td>b2</td><td>7</td></tr></table>')
    return ('<table><tr><th>x</th><th colspan="2">par</th></tr>'
            '<tr><td rowspan="2">R</td><td>c0</td><td>c1</td></tr>'
            '<tr><td colspan="2">fundida</td></tr></table>')


def _t5_borderless_zebra(k: int) -> str:
    # estrutura = grid simples; o DESAFIO é o render (sem bordas, zebra)
    cell = 'style="border:none;padding:4px 10px"'
    rows = []
    for r in range(4):
        bg = ' style="background:#efefef"' if r % 2 == 0 else ""
        rows.append(f'<tr{bg}><td {cell}>z{r}a_{k}</td><td {cell}>{_w(f"z{r}{k}")}</td>'
                    f'<td {cell}>{_num(f"w{r}{k}", 0)}</td></tr>')
    return ('<table style="border-collapse:collapse;border:none">'
            f'<tr><th {cell}>chave</th><th {cell}>nome</th><th {cell}>medida</th></tr>'
            + "".join(rows) + "</table>")


def gen_diagramas() -> dict[str, str]:
    """20 diagramas mermaid em 5 tipos × 4 tamanhos (origem: e22/T190)."""
    src: dict[str, str] = {}
    for n in (4, 6, 8, 12):
        nodes = [f"N{i}" for i in range(n)]
        for ori in ("TD", "LR"):
            lines = [f"flowchart {ori}"]
            for i in range(n - 1):
                lbl = f"|e{i}|" if i % 2 == 0 else ""
                lines.append(f"  {nodes[i]}[{nodes[i]} caixa] -->{lbl} {nodes[i+1]}[{nodes[i+1]} caixa]")
            lines.append(f"  {nodes[0]} --> {nodes[n//2]}")
            src[f"flow_{ori.lower()}_{n:02d}"] = "\n".join(lines)
        lines = ["sequenceDiagram"]
        for i in range(n):
            lines.append(f"  participant P{i}")
        for i in range(n - 1):
            lines.append(f"  P{i}->>P{i+1}: msg{i}")
        src[f"seq_{n:02d}"] = "\n".join(lines)
        lines = ["stateDiagram-v2", "  [*] --> S0"]
        for i in range(n - 1):
            lines.append(f"  S{i} --> S{i+1}: t{i}")
        lines.append(f"  S{n-1} --> [*]")
        src[f"state_{n:02d}"] = "\n".join(lines)
        lines = ["classDiagram"]
        for i in range(n - 1):
            lines.append(f"  C{i} <|-- C{i+1}")
        lines.append("  C0 : +int campo")
        src[f"class_{n:02d}"] = "\n".join(lines)
    assert len(src) == 20
    return src


def gen_corpus() -> dict[str, list[str]]:
    """Escreve gt/<categoria>/<item>.md. Retorna {categoria: [itens]}."""
    cats: dict[str, list[str]] = {}

    def write(cat: str, name: str, body: str) -> None:
        d = GT / cat
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{name}.md").write_text(body, encoding="utf-8")
        cats.setdefault(cat, []).append(name)

    # prosa — 5 docs com headings
    for k in range(5):
        body = (f"# Documento técnico {k}\n\n{prose_par(k)}\n\n"
                f"## Seção intermediária\n\n{prose_par(k + 10)}\n\n"
                f"### Detalhe\n\n{prose_par(k + 20)}\n")
        write("prosa", f"prosa_{k:02d}", body)

    # fórmulas — 1 display por doc, com prosa em volta
    for name, ltx in FORMULAS_DISPLAY:
        write("formula_display", name,
              f"# Fórmula {name}\n\n{prose_par(_stable(name) % 50)}\n\n$$ {ltx} $$\n\n{prose_par((_stable(name) % 50) + 1, 3)}\n")
    for name, ltx in FORMULAS_MATRIZ:
        write("formula_matriz", name,
              f"# Matriz {name}\n\n{prose_par(_stable(name) % 50)}\n\n$$ {ltx} $$\n\n{prose_par((_stable(name) % 50) + 1, 3)}\n")
    for name, ltx in FORMULAS_MULTILINE:
        write("formula_multiline", name,
              f"# Derivação {name}\n\n{prose_par(_stable(name) % 50)}\n\n$$ {ltx} $$\n\n{prose_par((_stable(name) % 50) + 1, 3)}\n")

    # fórmulas inline — 6 docs com $..$ no meio da prosa
    inline_bits = [r"\alpha + \beta", r"x_n \to L", r"O(n \log n)", r"\langle u, v \rangle",
                   r"\det(A) \ne 0", r"f \colon X \to Y"]
    for k, bit in enumerate(inline_bits):
        body = (f"# Texto com inline {k}\n\nQuando ${bit}$ vale, {prose_par(k + 30, 2)} "
                f"Além disso ${bit}$ implica estabilidade. {prose_par(k + 40, 2)}\n")
        write("formula_inline", f"inline_{k:02d}", body)

    # tabelas — tiers v1.1 (redesenho T075/e25; v1.0 só variava TAMANHO):
    # T1 grid simples; T2 alinhamentos+números; T3 células multilinha;
    # T4 row/colspan (teto do pipe-transporte, T440); T5 borderless/zebra
    # (estrutura simples, RENDER difícil). Medidos com TEDS em e25.
    for tier, fn in (("t1", _t1_grid), ("t2", _t2_align_num), ("t3", _t3_multiline),
                     ("t4", _t4_span), ("t5", _t5_borderless_zebra)):
        for k in range(3):
            name = f"{tier}_{k}"
            write("tabela", name,
                  f"# Tabela {name}\n\n{prose_par(_stable(name) % 40, 2)}\n\n"
                  f"{fn(k)}\n\n{prose_par(_stable(name) % 40 + 1, 2)}\n")

    # diagramas mermaid
    for name, dia in gen_diagramas().items():
        write("diagrama", name,
              f"# Diagrama {name}\n\n{prose_par(_stable(name) % 30, 2)}\n\n```mermaid\n{dia}\n```\n")

    # logos sintéticos — 5 SVGs (texto + formas), embutidos via img
    for k in range(5):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="240" height="120">'
               f'<rect x="4" y="4" width="232" height="112" fill="none" stroke="#1a3a52" stroke-width="3"/>'
               f'<circle cx="60" cy="60" r="{20 + k * 4}" fill="#2a5a82"/>'
               f'<text x="110" y="55" font-family="serif" font-size="18" fill="#1a3a52">ACME LAB {k}</text>'
               f'<text x="110" y="80" font-family="serif" font-size="11" fill="#444">fundado em 19{50 + k}</text></svg>')
        d = GT / "logo"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"logo_{k}.svg").write_text(svg, encoding="utf-8")
        write("logo", f"logo_{k:02d}",
              f"# Logo sintético {k}\n\n{prose_par(k + 60, 2)}\n\n![logo {k}](logo_{k}.svg)\n")

    (HERE / "manifest.json").write_text(json.dumps(cats, indent=1), encoding="utf-8")
    return cats


# ------------------------------------------------------------------ render --
# Subset commitado em pdf/ — fixtures herméticos (testes do cropper) + prova
# pronta por categoria. Escolhidos entre os que o cropper DETECTA (e24 onda 4).
FIXTURES_KATEX = [("formula_display", "bayes"), ("formula_matriz", "hadamard"),
                  ("tabela", "t4_0"), ("diagrama", "flow_td_04"),
                  ("logo", "logo_00"), ("prosa", "prosa_00")]
FIXTURES_CM = [("formula_display", "bayes"), ("formula_matriz", "hadamard")]

# Eixo CM (delta-E adapter): mesmo GT, tipografia pdflatex/Computer Modern.
TEX_TMPL = r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb}
\usepackage[a4paper,margin=2.5cm]{geometry}
\begin{document}
\section*{%(title)s}
%(prose1)s
\[ %(formula)s \]
%(prose2)s
\end{document}
"""


def find_tectonic() -> str | None:
    cand = os.environ.get("PDF2MD_TECTONIC") or shutil.which("tectonic")
    return cand if cand and Path(cand).exists() else None


def render_katex(cat: str, name: str, out_pdf: Path) -> None:
    from pdf2md.pdfs import md_to_pdf
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    md_to_pdf(GT / cat / f"{name}.md", out_pdf, overwrite=True,
              mermaid=(cat == "diagrama"))


def render_cm(cat: str, name: str, out_pdf: Path, tectonic: str) -> None:
    formulas = dict(FORMULAS_DISPLAY + FORMULAS_MATRIZ + FORMULAS_MULTILINE)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    tex = out_pdf.with_suffix(".tex")
    tex.write_text(TEX_TMPL % {
        "title": name.replace("_", " "),
        "prose1": prose_par(_stable(name) % 50),
        "prose2": prose_par((_stable(name) % 50) + 1, 3),
        "formula": formulas[name],
    }, encoding="utf-8")
    subprocess.run([tectonic, str(tex)], check=True, capture_output=True,
                   cwd=str(out_pdf.parent), timeout=600)
    tex.unlink()


def render_fixtures() -> None:
    for cat, name in FIXTURES_KATEX:
        render_katex(cat, name, PDF / "katex" / cat / f"{name}.pdf")
        print(f"  [katex] {cat}/{name} ok")
    tectonic = find_tectonic()
    if tectonic is None:
        print("  [cm] tectonic ausente (PATH ou PDF2MD_TECTONIC) — eixo CM pulado")
        return
    for cat, name in FIXTURES_CM:
        render_cm(cat, name, PDF / "cm" / cat / f"{name}.pdf", tectonic)
        print(f"  [cm] {cat}/{name} ok")


def render_all(out_dir: Path) -> None:
    cats = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    for cat, items in cats.items():
        for item in items:
            render_katex(cat, item, out_dir / cat / f"{item}.pdf")
        print(f"  [render] {cat}: {len(items)} ok")


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "gen"
    if step == "gen":
        cats = gen_corpus()
        print(f"[gen] {sum(len(v) for v in cats.values())} itens em {len(cats)} categorias")
    elif step == "fixtures":
        render_fixtures()
    elif step == "render":
        if len(sys.argv) < 3:
            sys.exit("uso: python gen.py render <out_dir>  (renders fora do repo — são output)")
        render_all(Path(sys.argv[2]))
    else:
        sys.exit(f"step desconhecido: {step} (gen | fixtures | render)")
