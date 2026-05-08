"""
Agrega todos os _stats.json de um diretório-raiz num único _OVERVIEW.md.

Varre recursivamente em busca de `_stats.json` e produz:
- `_OVERVIEW.md` — relatório consolidado (humano)
- `_OVERVIEW.json` — dump agregado (máquina)

Uso:
  python aggregate_stats.py <root_dir> [--out <dir>]

Exemplo:
  python aggregate_stats.py pesquisa_geral
"""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


def fmt_bytes(n: int) -> str:
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024
    return f"{n:.1f} TB"


def classify_doc(stats: dict, path: Path) -> str:
    """Heurística: livro / paper / material."""
    parts = [p.lower() for p in path.parts]
    if "livros" in parts:
        return "livro"
    if "papers" in parts:
        return "paper"
    if "material_aulas" in parts:
        return "material"
    return "outro"


def load_multi_roundtrip(folder: Path) -> dict | None:
    """Carrega _multi_roundtrip.json se existir."""
    f = folder / "_multi_roundtrip.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return None


def collect_docs(root: Path) -> list[dict]:
    docs = []
    for stats_path in sorted(root.rglob("_stats.json")):
        try:
            data = json.loads(stats_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARN] {stats_path}: {e}", file=sys.stderr)
            continue
        rel = stats_path.parent.relative_to(root)
        kind = classify_doc(data, stats_path)
        out = data.get("output", {})
        tot = out.get("totals", {}) or {}
        src = data.get("source", {}) or {}
        rt = data.get("roundtrip") or {}
        mrt = load_multi_roundtrip(stats_path.parent)
        docs.append({
            "kind": kind,
            "name": rel.name or str(rel),
            "rel_path": str(rel).replace("\\", "/"),
            "stats_path": str(stats_path),
            "pages": src.get("pages"),
            "pdf_size": src.get("size_bytes", 0),
            "chapter_count": tot.get("chapter_count", 0),
            "tokens": tot.get("tokens", 0),
            "words": tot.get("words", 0),
            "size_bytes": tot.get("size_bytes", 0),
            "math_display": tot.get("math_display", 0),
            "math_inline": tot.get("math_inline", 0),
            "headers_total": tot.get("headers_total", 0),
            "tables_rough": tot.get("tables_rough", 0),
            "images_count": tot.get("images_count", 0),
            "images_total_bytes": tot.get("images_total_bytes", 0),
            "ligature_artifacts": tot.get("ligature_artifacts", 0),
            "extraction_seconds": data.get("extraction_time_seconds"),
            "similarity": rt.get("similarity"),
            "divergences": rt.get("divergence_categories", {}),
            "tools": data.get("tools", {}),
            "generated_at": data.get("generated_at", "?"),
            "multi_roundtrip": mrt,
        })
    return docs


def render_overview(root: Path, docs: list[dict]) -> str:
    if not docs:
        return f"# OVERVIEW — {root}\n\nNenhum `_stats.json` encontrado.\n"

    by_kind = {"livro": [], "paper": [], "material": [], "outro": []}
    for d in docs:
        by_kind[d["kind"]].append(d)

    lines = [
        f"# OVERVIEW — `{root}`",
        "",
        f"*Gerado em: {datetime.now().isoformat(timespec='seconds')}*",
        "",
        "Visão consolidada de todas as extrações do conversor neste diretório.",
        "Cada linha vem de um `_stats.json` produzido por `tools/pdf_md_converter/stats.py`.",
        "",
    ]

    # --- Resumo executivo agregado ---
    total_pages = sum(d["pages"] or 0 for d in docs)
    total_tokens = sum(d["tokens"] for d in docs)
    total_words = sum(d["words"] for d in docs)
    total_math = sum(d["math_display"] + d["math_inline"] for d in docs)
    total_imgs = sum(d["images_count"] for d in docs)
    total_md_bytes = sum(d["size_bytes"] for d in docs)
    total_pdf_bytes = sum(d["pdf_size"] for d in docs)
    total_img_bytes = sum(d["images_total_bytes"] for d in docs)

    sims = [d["similarity"] for d in docs if d["similarity"] is not None]
    sim_avg = sum(sims) / len(sims) if sims else None
    sim_min = min(sims) if sims else None
    sim_max = max(sims) if sims else None

    agg_div: Counter = Counter()
    for d in docs:
        agg_div.update(d["divergences"])

    lines += [
        "## Resumo executivo",
        "",
        "| Métrica | Total |",
        "|---|---:|",
        f"| Documentos extraídos | **{len(docs)}** |",
        f"| Livros | {len(by_kind['livro'])} |",
        f"| Papers | {len(by_kind['paper'])} |",
        f"| Materiais de aula | {len(by_kind['material'])} |",
        f"| Páginas (PDF originais) | {total_pages:,} |",
        f"| Tokens (MD output) | {total_tokens:,} |",
        f"| Palavras | {total_words:,} |",
        f"| Fórmulas | {total_math:,} |",
        f"| Imagens | {total_imgs:,} |",
        f"| Tamanho dos PDFs | {fmt_bytes(total_pdf_bytes)} |",
        f"| Tamanho dos MDs | {fmt_bytes(total_md_bytes)} |",
        f"| Tamanho das imagens | {fmt_bytes(total_img_bytes)} |",
    ]
    if total_pdf_bytes:
        ratio_md = total_md_bytes / total_pdf_bytes * 100
        ratio_full = (total_md_bytes + total_img_bytes) / total_pdf_bytes * 100
        lines += [
            f"| MD/PDF (apenas texto) | {ratio_md:.1f}% |",
            f"| (MD+img)/PDF (transporte) | {ratio_full:.1f}% |",
        ]
    if sim_avg is not None:
        lines += [
            f"| Round-trip — média | **{sim_avg*100:.2f}%** |",
            f"| Round-trip — min | {sim_min*100:.2f}% |",
            f"| Round-trip — max | {sim_max*100:.2f}% |",
        ]
    lines.append("")

    # --- Tabela por kind ---
    for kind, label in [("livro", "Livros"), ("paper", "Papers"), ("material", "Materiais de aula")]:
        items = by_kind[kind]
        if not items:
            continue
        lines += [
            f"## {label}",
            "",
            "| Doc | Pgs | Seções | Tokens | Palavras | Fórmulas | Imgs | MD | Round-trip | Tempo |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for d in sorted(items, key=lambda x: x["rel_path"]):
            sim_str = f"{d['similarity']*100:.1f}%" if d["similarity"] is not None else "—"
            t_str = f"{d['extraction_seconds']:.0f}s" if d["extraction_seconds"] else "—"
            formula_total = d["math_display"] + d["math_inline"]
            lines.append(
                f"| [{d['rel_path']}](./{d['rel_path']}/_stats.md) "
                f"| {d['pages'] or '?'} "
                f"| {d['chapter_count']} "
                f"| {d['tokens']:,} "
                f"| {d['words']:,} "
                f"| {formula_total} "
                f"| {d['images_count']} "
                f"| {fmt_bytes(d['size_bytes'])} "
                f"| {sim_str} "
                f"| {t_str} |"
            )
        lines.append("")

    # --- Análise de round-trip ---
    if sims:
        lines += [
            "## Análise round-trip",
            "",
            f"Documentos com medição de round-trip: **{len(sims)}/{len(docs)}**.",
            "",
        ]
        # Bucket por similaridade
        buckets = {"≥95%": 0, "90-95%": 0, "80-90%": 0, "<80%": 0}
        for s in sims:
            p = s * 100
            if p >= 95:
                buckets["≥95%"] += 1
            elif p >= 90:
                buckets["90-95%"] += 1
            elif p >= 80:
                buckets["80-90%"] += 1
            else:
                buckets["<80%"] += 1
        lines += [
            "### Distribuição",
            "",
            "| Faixa | Documentos |",
            "|---|---:|",
        ]
        for k, v in buckets.items():
            lines.append(f"| {k} | {v} |")
        lines.append("")

        # Categorias agregadas de divergência (já calculadas no topo)
        if agg_div:
            total_div = sum(agg_div.values())
            lines += [
                "### Divergências (agregadas em todos os docs com round-trip)",
                "",
                "| Categoria | Tokens divergentes | % |",
                "|---|---:|---:|",
            ]
            for cat, n in agg_div.most_common():
                pct = n / max(total_div, 1) * 100
                lines.append(f"| `{cat}` | {n:,} | {pct:.1f}% |")
            lines.append("")

    # --- Análise por prioridade (ver tools/pdf_md_converter/PHILOSOPHY.md) ---
    if agg_div:
        math_pct = agg_div.get("math", 0) / max(sum(agg_div.values()), 1) * 100
        lines += [
            "### Interpretação à luz da hierarquia de prioridades",
            "",
            f"`math` representa **{math_pct:.1f}%** das divergências agregadas. Isso é",
            "consistente com **drift de notação LaTeX** (4ª prioridade — formatação),",
            "não perda de conteúdo (1ª prioridade). O round-trip mede similaridade",
            "byte-a-byte; uma fórmula re-renderizada com `\\rm` em vez de `\\mathrm`",
            "conta como divergência mas preserva o conteúdo matemático.",
            "",
            "Para validar **preservação de conteúdo** (1ª prioridade), seria preciso",
            "comparar AST math e contagem de fórmulas em vez de tokens — ver T410.",
            "",
        ]

    # --- Multi-iteration round-trip ---
    multi_docs = [d for d in docs if d.get("multi_roundtrip")]
    if multi_docs:
        lines += [
            "## Multi-iteration round-trip",
            "",
            "Documentos com teste de iteração MD → PDF → MD' → PDF → ... medindo",
            "convergência ou drift do pipeline. Curva achatada = pipeline idempotente.",
            "",
        ]
        for d in multi_docs:
            mrt = d["multi_roundtrip"]
            iters = mrt.get("iterations", [])
            if not iters:
                continue
            lines += [
                f"### `{d['rel_path']}` — {len(iters)} iterações",
                "",
                "| i | Tokens | Sim(MDᵢ, MD₀) | Sim(MDᵢ, MDᵢ₋₁) | Tempo |",
                "|---:|---:|---:|---:|---:|",
            ]
            for it in iters:
                if it.get("error"):
                    lines.append(f"| {it['i']} | — | — | — | falha |")
                    continue
                sim_to_0 = f"{it['sim_to_md0']*100:.2f}%" if it.get("sim_to_md0") is not None else "—"
                sim_to_prev = f"{it['sim_to_prev']*100:.2f}%" if it.get("sim_to_prev") is not None else "—"
                lines.append(
                    f"| {it['i']} | {it.get('tokens', 0):,} | "
                    f"{sim_to_0} | {sim_to_prev} | {it.get('seconds', 0):.0f}s |"
                )
            sims_to_0 = [it["sim_to_md0"] for it in iters if it.get("sim_to_md0") is not None]
            if len(sims_to_0) >= 2:
                first, last = sims_to_0[0], sims_to_0[-1]
                drift = (first - last) * 100
                last_two_diff = abs(sims_to_0[-1] - sims_to_0[-2]) * 100
                lines.append("")
                if abs(drift) < 1.0:
                    lines.append(f"**Veredito:** pipeline estável (drift {drift:.2f}% < 1%).")
                elif drift > 0 and last_two_diff < 0.5:
                    lines.append(f"**Veredito:** convergência logarítmica — perdeu {drift:.1f}% mas estabilizou (Δ últimas duas iterações: {last_two_diff:.2f}%).")
                else:
                    lines.append(f"**Veredito:** drift contínuo — perdeu {drift:.1f}% e ainda variando.")
            lines.append("")
            lines.append(f"Detalhes: [`{d['rel_path']}/_multi_roundtrip.md`](./{d['rel_path']}/_multi_roundtrip.md)")
            lines.append("")

    # --- Outliers ---
    lines += ["## Outliers e atenção", ""]
    critical = []  # round-trip < 50% ou ligaduras ou zero tokens
    notable = []   # round-trip 50-70%
    for d in docs:
        notes = []
        bucket = None
        if d["similarity"] is not None:
            sim_pct = d["similarity"] * 100
            if sim_pct < 50:
                notes.append(f"round-trip crítico ({sim_pct:.1f}%)")
                bucket = "critical"
            elif sim_pct < 70:
                notes.append(f"round-trip moderado ({sim_pct:.1f}%) — provavelmente drift LaTeX")
                bucket = "notable"
        if d["ligature_artifacts"] > 0:
            notes.append(f"{d['ligature_artifacts']} ligaduras quebradas")
            bucket = bucket or "critical"
        if d["tokens"] == 0:
            notes.append("zero tokens (extração falhou?)")
            bucket = "critical"
        if not notes:
            continue
        if bucket == "critical":
            critical.append((d["rel_path"], notes))
        else:
            notable.append((d["rel_path"], notes))

    if critical:
        lines += ["### Crítico (investigar)", ""]
        for path, notes in critical:
            lines.append(f"- `{path}` — {'; '.join(notes)}")
        lines.append("")
    if notable:
        lines += ["### Notável (drift esperado, monitorar)", ""]
        for path, notes in notable:
            lines.append(f"- `{path}` — {'; '.join(notes)}")
        lines.append("")
    if not critical and not notable:
        lines.append("Nenhum documento com flags de atenção.")
        lines.append("")

    # --- Tooling ---
    tool_versions = Counter()
    for d in docs:
        t = d["tools"]
        sig = (
            t.get("marker", "?"),
            t.get("torch", "?"),
            t.get("cuda_device", "CPU"),
        )
        tool_versions[sig] += 1
    if tool_versions:
        lines += [
            "## Pipeline / versões",
            "",
            "| marker-pdf | torch | device | docs |",
            "|---|---|---|---:|",
        ]
        for (mk, tc, dev), n in tool_versions.most_common():
            lines.append(f"| `{mk}` | `{tc}` | `{dev}` | {n} |")
        lines.append("")

    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description="Agrega _stats.json em _OVERVIEW.md")
    p.add_argument("root", type=Path)
    p.add_argument("--out", type=Path, default=None,
                   help="Diretório de saída (default: <root>)")
    args = p.parse_args()

    if not args.root.is_dir():
        print(f"[ERRO] Diretório não encontrado: {args.root}", file=sys.stderr)
        sys.exit(1)

    out_dir = args.out or args.root
    out_dir.mkdir(parents=True, exist_ok=True)

    docs = collect_docs(args.root)
    print(f"[INFO] {len(docs)} doc(s) com _stats.json em {args.root}")

    overview_md = out_dir / "_OVERVIEW.md"
    overview_json = out_dir / "_OVERVIEW.json"

    overview_md.write_text(render_overview(args.root, docs), encoding="utf-8")
    overview_json.write_text(
        json.dumps({
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "root": str(args.root),
            "docs": docs,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"[OK] {overview_md}")
    print(f"[OK] {overview_json}")


if __name__ == "__main__":
    main()
