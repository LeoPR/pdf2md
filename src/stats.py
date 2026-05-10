"""
Gera relatório de telemetria de uma extração do conversor.

Output:
- `_stats.json` (machine-readable, completo)
- `_stats.md`   (human-readable, relatório)

O relatório inclui: resumo executivo, método/versões, fonte, output (overall +
por seção), densidade de math, top LaTeX commands, breakdown de imagens,
round-trip com divergências categorizadas, reprodutibilidade.

Uso:
  python stats.py <md_folder> [--source-pdf <pdf>]
                              [--roundtrip-md1 <md>] [--roundtrip-md2 <md>]
                              [--extraction-time <sec>]
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


# ============================================================================
# Detecção de tooling
# ============================================================================

def _run_safe(cmd, default="?"):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return out.stdout.strip().splitlines()[0] if out.stdout else default
    except Exception:
        return default


def detect_tools() -> dict:
    """Coleta versões dos tools usados no pipeline."""
    info = {
        "python": sys.version.split()[0],
        "platform": sys.platform,
    }
    # marker (pacote chama-se marker-pdf no PyPI)
    try:
        from importlib.metadata import version as _v
        info["marker"] = _v("marker-pdf")
    except Exception:
        try:
            import marker
            info["marker"] = getattr(marker, "__version__", "?")
        except ImportError:
            info["marker"] = "n/a"
    # torch + cuda
    try:
        import torch
        info["torch"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            info["cuda_device"] = torch.cuda.get_device_name(0)
            info["cuda_memory_gb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 1)
    except ImportError:
        info["torch"] = "n/a"
    # pandoc
    if shutil.which("pandoc"):
        v = _run_safe(["pandoc", "--version"])
        info["pandoc"] = v.replace("pandoc ", "") if v.startswith("pandoc ") else v
    else:
        info["pandoc"] = "n/a"
    # PyMuPDF
    info["pymupdf"] = "1.27.2" if HAS_FITZ else "n/a"
    return info


# ============================================================================
# PDF metrics
# ============================================================================

def pdf_metrics(pdf_path: Path) -> dict:
    if not pdf_path or not pdf_path.exists():
        return {}
    h = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    out = {
        "path": str(pdf_path),
        "size_bytes": pdf_path.stat().st_size,
        "sha256": h.hexdigest(),
    }
    if HAS_FITZ:
        try:
            doc = fitz.open(pdf_path)
            out["pages"] = len(doc)
            md = doc.metadata or {}
            out["pdf_metadata"] = {
                "title": md.get("title", "") or "",
                "author": md.get("author", "") or "",
                "creator": md.get("creator", "") or "",
            }
            doc.close()
        except Exception:
            pass
    return out


# ============================================================================
# MD analysis (per-file)
# ============================================================================

LATEX_CMD_RE = re.compile(r"\\([a-zA-Z]+)")
WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)
SENT_RE = re.compile(r"[.!?]\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ]")  # rough


def md_metrics(md_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    # LaTeX command frequency (apenas dentro de math markers para não contar markdown como \n etc)
    math_segments = re.findall(r"\$\$.*?\$\$|\$[^$\n]+?\$", text, flags=re.DOTALL)
    latex_text = "\n".join(math_segments)
    latex_cmds = Counter(LATEX_CMD_RE.findall(latex_text))

    return {
        "path": str(md_path),
        "size_bytes": md_path.stat().st_size,
        "lines": len(lines),
        "tokens": len(re.findall(r"\S+", text)),
        "words": len(WORD_RE.findall(text)),
        "sentences_estimated": len(SENT_RE.findall(text)),
        "headers": {
            "h1": len(re.findall(r"^# [^#]", text, re.MULTILINE)),
            "h2": len(re.findall(r"^## [^#]", text, re.MULTILINE)),
            "h3": len(re.findall(r"^### [^#]", text, re.MULTILINE)),
            "h4_plus": len(re.findall(r"^####+ ", text, re.MULTILINE)),
        },
        "math": {
            "display": text.count("$$") // 2,
            "inline_markers": len(re.findall(r"(?<!\\)\$[^$\n]+?\$", text)),
            "latex_cmd_count": sum(latex_cmds.values()),
            "latex_cmd_unique": len(latex_cmds),
            "latex_cmd_top10": dict(latex_cmds.most_common(10)),
        },
        "ligature_artifacts": len(re.findall(r"[ﬀ-ﬄ]", text)),
        "tables_rough": len(re.findall(r"^\|.*\|$", text, re.MULTILINE)) // 2,
        "code_blocks": text.count("```") // 2,
        "images_referenced": len(re.findall(r"!\[[^\]]*\]\([^)]+\)", text)),
    }


# ============================================================================
# Image breakdown
# ============================================================================

def image_breakdown(folder: Path) -> dict:
    """Coleta tamanhos e formatos das imagens em folder/ ou folder/images/."""
    candidates = []
    for sub in [folder, folder / "images"]:
        if sub.is_dir():
            candidates += list(sub.glob("*.jpeg")) + list(sub.glob("*.jpg")) \
                       + list(sub.glob("*.png")) + list(sub.glob("*.svg"))
    out = {
        "count": len(candidates),
        "by_format": Counter(f.suffix.lower().lstrip(".") for f in candidates),
        "total_bytes": sum(f.stat().st_size for f in candidates),
    }
    if candidates:
        sizes = [f.stat().st_size for f in candidates]
        out["avg_bytes"] = sum(sizes) // len(sizes)
        out["max_bytes"] = max(sizes)
        out["min_bytes"] = min(sizes)
    return out


# ============================================================================
# Folder-level (book vs paper layout)
# ============================================================================

def folder_metrics(folder: Path) -> dict:
    out = {"folder": str(folder), "chapters": {}, "totals": {}}

    md_root = [m for m in folder.glob("*.md")
               if not m.name.startswith("_")
               and m.name not in ("index.md", "README.md")]

    if md_root:
        # Layout paper
        for md in md_root:
            ch = md_metrics(md)
            ch["images"] = image_breakdown(folder)
            out["chapters"][md.stem] = ch
    else:
        # Layout book
        for chap in sorted(folder.iterdir()):
            if not chap.is_dir() or chap.name.startswith(("_", ".")):
                continue
            md = chap / f"{chap.name}.md"
            if not md.exists():
                continue
            ch = md_metrics(md)
            ch["images"] = image_breakdown(chap)
            out["chapters"][chap.name] = ch

    chs = out["chapters"]
    if chs:
        agg_latex = Counter()
        agg_format = Counter()
        agg_format_bytes: dict[str, int] = {}
        for c in chs.values():
            agg_latex.update(c["math"].get("latex_cmd_top10", {}))
            for fmt, n in c["images"].get("by_format", {}).items():
                agg_format[fmt] += n
            # Bytes por formato exigem walking the files de novo? Não — agregamos por count*avg seria errado.
            # Recoletamos do filesystem para precisão (T136).
        # T136: breakdown bytes por formato lendo o filesystem novamente
        for c_id, c in chs.items():
            ch_folder = Path(c["images"].get("_folder", "")) if isinstance(c["images"].get("_folder"), str) else None
            # Fallback: derivar do path do MD
            md_path = Path(c["path"])
            for candidate_dir in [md_path.parent, md_path.parent / "images"]:
                if not candidate_dir.is_dir():
                    continue
                for f in candidate_dir.iterdir():
                    suf = f.suffix.lower().lstrip(".")
                    if suf in ("jpeg", "jpg", "png", "svg") and f.is_file():
                        agg_format_bytes[suf] = agg_format_bytes.get(suf, 0) + f.stat().st_size
        out["totals"] = {
            "chapter_count": len(chs),
            "lines": sum(c["lines"] for c in chs.values()),
            "tokens": sum(c["tokens"] for c in chs.values()),
            "words": sum(c["words"] for c in chs.values()),
            "sentences_estimated": sum(c["sentences_estimated"] for c in chs.values()),
            "size_bytes": sum(c["size_bytes"] for c in chs.values()),
            "math_display": sum(c["math"]["display"] for c in chs.values()),
            "math_inline": sum(c["math"]["inline_markers"] for c in chs.values()),
            "headers_total": sum(sum(c["headers"].values()) for c in chs.values()),
            "ligature_artifacts": sum(c["ligature_artifacts"] for c in chs.values()),
            "images_count": sum(c["images"]["count"] for c in chs.values()),
            "images_total_bytes": sum(c["images"]["total_bytes"] for c in chs.values()),
            "images_by_format": dict(agg_format),           # T136: count por formato (agregado)
            "images_bytes_by_format": agg_format_bytes,     # T136: bytes por formato (agregado)
            "code_blocks": sum(c["code_blocks"] for c in chs.values()),
            "tables_rough": sum(c["tables_rough"] for c in chs.values()),
            "latex_cmd_top20_aggregated": dict(agg_latex.most_common(20)),
        }
    return out


# ============================================================================
# Round-trip + categorized divergences
# ============================================================================

def normalize_md(text: str) -> str:
    text = re.sub(r"\{\d+\}", "", text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
                  lambda m: f"![{m.group(1)}]({Path(m.group(2)).name})", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


_LATEX_CMD_RE = re.compile(r"\\[a-zA-Z]+")
_HEADING_RE = re.compile(r"(?:^|\n)#+ ")
_URL_RE = re.compile(r"https?://|ftp://")


def categorize_divergence(a_str: str, b_str: str) -> str:
    """Classifica um delta entre tokens.

    Math é detectado de forma estrita: tem `$` (dollar) OU comando LaTeX
    `\\<letras>` real (não escapes como `\\*` ou `\\_`). URLs e footnote
    markers (`<sup>\\*</sup>https://...`) não são mais classificados como
    math (regressão observada no e02 em CDC MMWR — 65% "math" com 0 fórmulas).
    """
    s = a_str + " " + b_str
    if not s.strip():
        return "whitespace"
    # URLs primeiro: links de footnote estavam virando "math" via backslash em <sup>\*</sup>
    if _URL_RE.search(s):
        return "other"
    if "$" in s or _LATEX_CMD_RE.search(s):
        return "math"
    if _HEADING_RE.search(s):
        return "heading"
    if "**" in s or "_" in s:
        return "emphasis"
    if "![" in s or ".jpeg" in s or ".png" in s or ".svg" in s:
        return "image_ref"
    if "|" in s:
        return "table"
    if "---" in s:
        return "separator"
    return "other"


def roundtrip_metrics(md1: Path, md2: Path) -> dict:
    t1 = normalize_md(md1.read_text(encoding="utf-8"))
    t2 = normalize_md(md2.read_text(encoding="utf-8"))
    tokens1 = re.findall(r"\S+", t1)
    tokens2 = re.findall(r"\S+", t2)
    matcher = SequenceMatcher(None, tokens1, tokens2)
    similarity = matcher.ratio()

    # T071: bloat_ratio detecta padrão de alucinação no re-OCR do PDF
    # intermediário. Quando MD₁ é esparso (poucos tokens por página) e o
    # roundtrip gera muito mais conteúdo no MD₂, é sinal de que o marker
    # alucinou. Observado em IBM lesson 1 (3.4× → rt 28.9%) e Wilson 1800
    # (7.7× → rt 13.62%). Casos normais ficam em ~1.0×.
    bloat_ratio = len(tokens2) / len(tokens1) if tokens1 else None

    cats = Counter()
    examples = {}
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        a_str = " ".join(tokens1[i1:i2])
        b_str = " ".join(tokens2[j1:j2])
        cat = categorize_divergence(a_str, b_str)
        n = max(i2 - i1, j2 - j1)
        cats[cat] += n
        if cat not in examples and (i2 - i1 > 0 or j2 - j1 > 0):
            # Mantém apenas SAMPLE curto (primeiras palavras) por categoria
            examples[cat] = {
                "tag": tag,
                "from": " ".join(tokens1[i1:i2][:6]),
                "to": " ".join(tokens2[j1:j2][:6]),
            }

    return {
        "md1_path": str(md1),
        "md2_path": str(md2),
        "md1_tokens": len(tokens1),
        "md2_tokens": len(tokens2),
        "similarity": similarity,
        "bloat_ratio": bloat_ratio,
        "divergence_categories": dict(cats),
        "divergence_examples": examples,
    }


# ============================================================================
# Render markdown report
# ============================================================================

def fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} TB"


def render_md(stats: dict) -> str:
    out = stats["output"]
    tot = out.get("totals", {})
    src = stats.get("source", {})
    rt = stats.get("roundtrip")
    tools = stats.get("tools", {})

    # ============== Resumo executivo ==============
    pages = src.get("pages")
    tokens = tot.get("tokens", 0)
    formulas = tot.get("math_display", 0) + tot.get("math_inline", 0)
    sim_label = "—"
    bloat_summary = None
    if rt:
        sim_pct = rt["similarity"] * 100
        sim_label = f"{sim_pct:.2f}%"
        verdict = (
            "✓ pipeline estável" if sim_pct >= 90
            else "⚠️ avaliar Fase 2" if sim_pct >= 80
            else "❌ investigar"
        )
        sim_label += f" — {verdict}"
        # T071: bloat flag no resumo (heurística de alucinação)
        bloat = rt.get("bloat_ratio")
        md1_tokens = rt.get("md1_tokens", 0)
        density = (md1_tokens / pages) if pages else None
        if bloat is not None:
            # Forte: bloat > 3.0 sempre, OU bloat > 2.0 com densidade pobre
            strong_alucinacao = (
                bloat > 3.0
                or (bloat > 2.0 and density is not None and density < 200)
            )
            if strong_alucinacao:
                bloat_summary = f"{bloat:.2f}× 🚨 padrão de alucinação"
            elif bloat > 1.5:
                bloat_summary = f"{bloat:.2f}× ⚠️ anormal"
            else:
                bloat_summary = f"{bloat:.2f}× ✓"

    lines = [
        "# Relatório de extração",
        "",
        f"*Gerado em: {stats['generated_at']}*",
        "",
        "## Resumo executivo",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Seções | {tot.get('chapter_count', 0)} |",
        f"| Páginas (PDF original) | {pages or '?'} |",
        f"| Tokens | {tokens:,} |",
        f"| Palavras | {tot.get('words', 0):,} |",
        f"| Fórmulas (display + inline) | {formulas:,} |",
        f"| Imagens | {tot.get('images_count', 0)} ({fmt_bytes(tot.get('images_total_bytes', 0))}) |",
        f"| Ligaduras quebradas | {tot.get('ligature_artifacts', 0)} {'✓' if tot.get('ligature_artifacts', 0) == 0 else '⚠️'} |",
        f"| Round-trip similaridade | {sim_label} |",
    ]
    if bloat_summary:
        lines.append(f"| Bloat ratio MD₂/MD₁ | {bloat_summary} |")
    lines.append("")

    # ============== Método / Tooling ==============
    lines += [
        "## Método de conversão",
        "",
        "| Componente | Versão / Valor |",
        "|---|---|",
        f"| Python | `{tools.get('python', '?')}` |",
        f"| marker-pdf | `{tools.get('marker', '?')}` |",
        f"| torch | `{tools.get('torch', '?')}` |",
        f"| CUDA | `{tools.get('cuda_device', 'CPU only') if tools.get('cuda_available') else 'CPU only'}` |",
        f"| pandoc | `{tools.get('pandoc', '?')}` |",
        f"| PyMuPDF | `{tools.get('pymupdf', '?')}` |",
        "",
    ]

    if "extraction_time_seconds" in stats:
        et = stats["extraction_time_seconds"]
        lines += [
            f"**Tempo de extração:** {et:.0f} s (~{et/60:.1f} min)",
            "",
        ]

    # ============== Fonte ==============
    if src:
        meta = src.get("pdf_metadata", {})
        lines += [
            "## Fonte (PDF original)",
            "",
            f"- **Arquivo:** `{src.get('path', '?')}`",
            f"- **Tamanho:** {fmt_bytes(src.get('size_bytes', 0))}",
            f"- **Páginas:** {pages or '?'}",
            f"- **SHA-256:** `{src.get('sha256', '?')[:32]}...`",
        ]
        if meta.get("title"):
            lines.append(f"- **Título (PDF metadata):** {meta['title']}")
        if meta.get("author"):
            lines.append(f"- **Autor:** {meta['author']}")
        lines.append("")

    # ============== Output overall ==============
    lines += [
        "## Output — métricas globais",
        "",
        "### Texto",
        "",
        f"- Linhas: **{tot.get('lines', 0):,}**",
        f"- Tokens (não-espaço): **{tot.get('tokens', 0):,}**",
        f"- Palavras: **{tot.get('words', 0):,}**",
        f"- Frases (estimado): **{tot.get('sentences_estimated', 0):,}**",
        f"- Tamanho MD total: **{fmt_bytes(tot.get('size_bytes', 0))}**",
        "",
        "### Estrutura",
        "",
        f"- Headers totais: **{tot.get('headers_total', 0)}**",
        f"- Code blocks: **{tot.get('code_blocks', 0)}**",
        f"- Tabelas (estimado): **{tot.get('tables_rough', 0)}**",
        "",
        "### Matemática",
        "",
        f"- Fórmulas display ($$..$$): **{tot.get('math_display', 0):,}**",
        f"- Math inline ($..$): **{tot.get('math_inline', 0):,}**",
    ]
    if pages:
        lines.append(f"- **Densidade:** {tot.get('math_display', 0) / pages:.1f} display/página, "
                     f"{(tot.get('math_display', 0) + tot.get('math_inline', 0)) / max(tot.get('tokens', 1), 1) * 1000:.1f} fórmulas/1k tokens")
    lines.append("")

    # ============== Top LaTeX commands ==============
    top_latex = tot.get("latex_cmd_top20_aggregated", {})
    if top_latex:
        lines += [
            "### Top 15 LaTeX commands (em todo o doc)",
            "",
            "| # | Comando | Ocorrências |",
            "|---:|---|---:|",
        ]
        for i, (cmd, count) in enumerate(list(top_latex.items())[:15], 1):
            lines.append(f"| {i} | `\\{cmd}` | {count:,} |")
        lines.append("")

    # ============== Imagens ==============
    img_total_bytes = tot.get("images_total_bytes", 0)
    img_count = tot.get("images_count", 0)
    if img_count:
        lines += [
            "## Imagens",
            "",
            f"- Total: **{img_count}** imagens, **{fmt_bytes(img_total_bytes)}**",
            f"- Tamanho médio: {fmt_bytes(img_total_bytes // max(img_count, 1))}",
            "",
        ]

        # T136: breakdown por formato (count, bytes, % bytes)
        formats_count = tot.get("images_by_format", {})
        formats_bytes = tot.get("images_bytes_by_format", {})
        if not formats_count:
            # Fallback (caso totals não tenha sido populado): re-agregar dos chapters
            formats_count = Counter()
            for c in out["chapters"].values():
                formats_count.update(c.get("images", {}).get("by_format", {}))
            formats_count = dict(formats_count)

        if formats_count:
            lines += [
                "### Breakdown por formato",
                "",
                "| Formato | Count | Bytes | % bytes |",
                "|---|---:|---:|---:|",
            ]
            sorted_formats = sorted(formats_count.items(), key=lambda x: -x[1])
            for fmt, count in sorted_formats:
                fmt_b = formats_bytes.get(fmt, 0)
                pct = (fmt_b / img_total_bytes * 100) if img_total_bytes else 0
                bytes_str = fmt_bytes(fmt_b) if fmt_b else "—"
                pct_str = f"{pct:.1f}%" if fmt_b else "—"
                lines.append(f"| `{fmt}` | {count:,} | {bytes_str} | {pct_str} |")
            lines.append("")

    # ============== Por seção ==============
    chs = out.get("chapters", {})
    if len(chs) > 1:
        lines += [
            "## Por seção",
            "",
            "| Seção | Linhas | Tokens | Palavras | Headers | $$ | Math inline | Imgs |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for cid, c in chs.items():
            lines.append(
                f"| {cid} | {c['lines']:,} | {c['tokens']:,} | {c['words']:,} | "
                f"{sum(c['headers'].values())} | {c['math']['display']} | "
                f"{c['math']['inline_markers']} | {c.get('images', {}).get('count', 0)} |"
            )
        lines.append("")

    # ============== Round-trip detalhado ==============
    if rt:
        sim_pct = rt["similarity"] * 100
        bloat = rt.get("bloat_ratio")
        # T071: heurística de alucinação — bloat alto OU (bloat médio + densidade pobre)
        md1_tokens = rt.get("md1_tokens", 0)
        density = (md1_tokens / pages) if pages else None  # tokens MD₁ por página
        strong_alucinacao = bloat is not None and (
            bloat > 3.0
            or (bloat > 2.0 and density is not None and density < 200)
        )
        if strong_alucinacao:
            bloat_flag = " 🚨 **PADRÃO DE ALUCINAÇÃO**"
        elif bloat is not None and bloat > 1.5:
            bloat_flag = " ⚠️ bloat anormal"
        else:
            bloat_flag = " ✓"
        bloat_str = f"{bloat:.2f}×{bloat_flag}" if bloat is not None else "—"

        lines += [
            "## Round-trip MD₁ → PDF → MD₂",
            "",
            "### Visão geral",
            "",
            f"- Tokens MD₁: **{rt['md1_tokens']:,}**",
            f"- Tokens MD₂: **{rt['md2_tokens']:,}**",
            f"- **Bloat ratio (MD₂/MD₁): {bloat_str}**",
            f"- **Similaridade: {sim_pct:.2f}%**",
            "",
        ]
        if "🚨" in bloat_flag:
            lines += [
                "> 🚨 **Bloat ≥ 2.0× com densidade < 200 tokens/página**: padrão "
                "característico de **alucinação** do re-OCR no PDF intermediário. "
                "MD₁ tem pouco conteúdo → marker re-OCR-iza o PDF reconstruído e "
                "inventa fórmulas/texto. Observado em IBM lesson 1 (3.4×, rt 28.9%) "
                "e Wilson 1800 (7.7×, rt 13.6%). Não é mau extract — é descompasso "
                "entre input pobre e re-OCR sem âncora. Ver `lab/e03_atkins_wilson_scan/`.",
                "",
            ]
        cats = rt.get("divergence_categories", {})
        if cats:
            total_div = sum(cats.values())
            lines += [
                "### Divergências por categoria",
                "",
                "| Categoria | Tokens divergentes | % do delta |",
                "|---|---:|---:|",
            ]
            for cat, n in sorted(cats.items(), key=lambda x: -x[1]):
                pct = n / max(total_div, 1) * 100
                lines.append(f"| `{cat}` | {n:,} | {pct:.1f}% |")
            lines.append("")

        examples = rt.get("divergence_examples", {})
        if examples:
            lines += [
                "### Exemplos por categoria (truncados, 6 tokens cada lado)",
                "",
                "| Categoria | MD₁ → MD₂ |",
                "|---|---|",
            ]
            for cat, ex in examples.items():
                a = ex["from"][:60] + ("..." if len(ex["from"]) > 60 else "")
                b = ex["to"][:60] + ("..." if len(ex["to"]) > 60 else "")
                lines.append(f"| `{cat}` ({ex['tag']}) | `{a}` → `{b}` |")
            lines.append("")

    # ============== Reprodutibilidade ==============
    lines += [
        "## Reprodutibilidade",
        "",
        f"- Pasta de output: `{out.get('folder', '?')}`",
        f"- SHA-256 do PDF: `{src.get('sha256', '?')[:32]}...`",
        f"- Comando para re-extrair (template):",
        "",
        "  ```",
        f"  marker_single \"{src.get('path', '<pdf>')}\" \\",
        f"    --output_dir <temp_dir> --output_format markdown",
        "  ```",
        "",
        "Após extrair, rodar `tools/pdf_md_converter/restructure.py` (livro) ou mover MD direto (paper).",
        "",
    ]

    return "\n".join(lines)


# ============================================================================
# Main
# ============================================================================

def main():
    p = argparse.ArgumentParser(description="Relatório de telemetria do conversor")
    p.add_argument("md_folder", type=Path)
    p.add_argument("--source-pdf", type=Path, default=None)
    p.add_argument("--roundtrip-md1", type=Path, default=None)
    p.add_argument("--roundtrip-md2", type=Path, default=None)
    p.add_argument("--extraction-time", type=float, default=None,
                   help="Tempo de extração em segundos (opcional)")
    args = p.parse_args()

    if not args.md_folder.is_dir():
        print(f"[ERRO] Pasta não encontrada: {args.md_folder}", file=sys.stderr)
        sys.exit(1)

    stats = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "tools": detect_tools(),
        "source": pdf_metrics(args.source_pdf) if args.source_pdf else {},
        "output": folder_metrics(args.md_folder),
    }
    if args.extraction_time:
        stats["extraction_time_seconds"] = args.extraction_time
    if args.roundtrip_md1 and args.roundtrip_md2:
        stats["roundtrip"] = roundtrip_metrics(args.roundtrip_md1, args.roundtrip_md2)

    json_path = args.md_folder / "_stats.json"
    md_path = args.md_folder / "_stats.md"
    json_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_md(stats), encoding="utf-8")

    print(f"[OK] {json_path}")
    print(f"[OK] {md_path}")
    tot = stats["output"]["totals"]
    print(f"  Tokens: {tot.get('tokens', 0):,} | Palavras: {tot.get('words', 0):,}")
    print(f"  Fórmulas display: {tot.get('math_display', 0):,} | Imagens: {tot.get('images_count', 0)}")
    if stats.get("roundtrip"):
        print(f"  Round-trip: {stats['roundtrip']['similarity']*100:.2f}%")


if __name__ == "__main__":
    main()
