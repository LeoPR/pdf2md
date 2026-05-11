"""
Multi-iteration round-trip: MD₀ → PDF → MD₁ → PDF → MD₂ → PDF → ...

Mede similaridade a cada iteração para detectar:
- Convergência (similaridade estabiliza num "ponto fixo")
- Drift (similaridade decai a cada iteração)
- Drift logarítmico (cai rápido nas primeiras iterações, depois estabiliza)

Gera relatório com curva de similaridade ao longo das iterações.

Uso:
  python multi_roundtrip.py <md_inicial> <work_dir> [--iterations N]

Exemplo:
  python multi_roundtrip.py pesquisa_geral/papers/2106_05919v2/2106_05919v2.md \\
                            /tmp/multi_rt_paper1 --iterations 5
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

# Garantir UTF-8 no stdout (Windows default cp1252 quebra com setas/acentos)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

PANDOC = "pandoc"
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
MARKER = r"Z:/venvs/marker/Scripts/marker_single.exe"


def md_to_pdf(md_path: Path, pdf_path: Path):
    """MD → PDF via pandoc + Chrome headless + KaTeX."""
    html_path = pdf_path.with_suffix(".html")
    chapter_dir = md_path.parent
    subprocess.run([
        PANDOC, str(md_path),
        "-o", str(html_path),
        "--standalone", "--embed-resources", "--katex",
        "--resource-path", str(chapter_dir),
        "--metadata", f"title={md_path.stem}",
    ], check=True, capture_output=True)
    url = "file:///" + html_path.absolute().as_posix().replace(" ", "%20")
    subprocess.run([
        CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path.absolute()}",
        "--virtual-time-budget=20000",
        url,
    ], check=True, capture_output=True)
    if not pdf_path.exists():
        raise RuntimeError(f"Chrome não criou PDF em {pdf_path}")


def pdf_to_md(pdf_path: Path, output_dir: Path) -> Path:
    """PDF → MD via marker (GPU)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        MARKER, str(pdf_path),
        "--output_dir", str(output_dir),
        "--output_format", "markdown",
    ], check=True, capture_output=True, text=True,
       encoding="utf-8", errors="replace", timeout=2400)
    md_files = list(output_dir.rglob("*.md"))
    if not md_files:
        raise RuntimeError("Marker não produziu MD")
    return md_files[0]


sys.path.insert(0, str(Path(__file__).parent))
from pdf2md.normalize import normalize_md  # noqa: E402


def similarity(md_a: Path, md_b: Path) -> tuple[float, int, int]:
    """Token similarity entre dois MDs. Retorna (sim, tokens_a, tokens_b)."""
    a = normalize_md(md_a.read_text(encoding="utf-8"))
    b = normalize_md(md_b.read_text(encoding="utf-8"))
    ta = re.findall(r"\S+", a)
    tb = re.findall(r"\S+", b)
    return SequenceMatcher(None, ta, tb).ratio(), len(ta), len(tb)


def render_report(report: dict) -> str:
    iters = report["iterations"]
    if not iters:
        return "# Multi-roundtrip — sem iterações"

    lines = ["# Relatório multi-iteration round-trip",
             "",
             f"*Gerado em: {report['generated_at']}*",
             "",
             f"- **Doc inicial:** `{report['md0']}`",
             f"- **Iterações:** {len(iters)}",
             f"- **Tempo total:** {report['total_seconds']:.0f} s",
             "",
             "## Curva de similaridade",
             "",
             "Similaridade entre cada MDᵢ e MD₀ (o MD inicial). Se o pipeline é",
             "idempotente/estável, a curva achata depois de 1-2 iterações.",
             "",
             "| i | Tokens MDᵢ | Sim(MDᵢ, MD₀) | Sim(MDᵢ, MDᵢ₋₁) | Tempo (s) |",
             "|---:|---:|---:|---:|---:|"]

    for it in iters:
        if it.get("error"):
            lines.append(f"| {it['i']} | — | — | — | falha: {it['error'][:60]} |")
            continue
        sim_to_0 = f"{it['sim_to_md0']*100:.2f}%" if it.get("sim_to_md0") is not None else "—"
        sim_to_prev = f"{it['sim_to_prev']*100:.2f}%" if it.get("sim_to_prev") is not None else "—"
        tokens = it.get("tokens", 0)
        seconds = it.get("seconds", 0)
        lines.append(f"| {it['i']} | {tokens:,} | {sim_to_0} | {sim_to_prev} | {seconds:.0f} |")

    # Veredito
    sims_to_0 = [it["sim_to_md0"] for it in iters if it.get("sim_to_md0") is not None]
    if len(sims_to_0) >= 2:
        first, last = sims_to_0[0], sims_to_0[-1]
        diff = (first - last) * 100
        last_two_diff = abs(sims_to_0[-1] - sims_to_0[-2]) * 100 if len(sims_to_0) >= 2 else None

        lines += ["",
                  "## Veredito",
                  ""]
        if abs(diff) < 1.0:
            lines.append("**Pipeline estável (idempotente)** — drift < 1% entre 1ª e última iteração.")
        elif diff > 0 and last_two_diff is not None and last_two_diff < 0.5:
            lines.append(f"**Convergência logarítmica** — perdeu {diff:.1f}% no total mas estabilizou (Δ últimas duas: {last_two_diff:.2f}%).")
        elif diff > 0:
            lines.append(f"**Drift contínuo** — perdeu {diff:.1f}% e ainda variando.")
        else:
            lines.append("**Comportamento inesperado** — similaridade aumentou (improvável; revisar).")

    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("md_initial", type=Path)
    p.add_argument("work_dir", type=Path)
    p.add_argument("--iterations", type=int, default=5)
    args = p.parse_args()

    if not args.md_initial.is_file():
        print(f"[ERRO] MD inicial não encontrado: {args.md_initial}", file=sys.stderr)
        sys.exit(1)

    work = args.work_dir
    if work.exists():
        def _retry(func, path, exc_info):
            import os, stat
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception:
                pass
        shutil.rmtree(work, onerror=_retry)
        if work.exists():
            # Última tentativa: renomear para um path morto e seguir
            work.rename(work.with_name(work.name + f"_old_{int(time.time())}"))
    work.mkdir(parents=True)

    # MD₀ = original (copiado para o work dir)
    md0 = work / "md0.md"
    shutil.copy(args.md_initial, md0)
    # Copiar também imagens se houver pasta images/
    src_imgs = args.md_initial.parent / "images"
    if src_imgs.is_dir():
        shutil.copytree(src_imgs, work / "images")

    print(f"[INFO] MD inicial: {md0}")
    print(f"[INFO] Work dir: {work}")
    print(f"[INFO] Iterações: {args.iterations}")

    iterations = []
    prev_md = md0
    t_total_start = time.time()

    for i in range(1, args.iterations + 1):
        print(f"\n=== Iteração {i} ===")
        t0 = time.time()
        try:
            pdf_i = work / f"iter_{i}.pdf"
            print("  MD → PDF...")
            md_to_pdf(prev_md, pdf_i)
            print(f"    PDF: {pdf_i.stat().st_size // 1024} KB")

            print("  PDF → MD...")
            md2_dir = work / f"md_{i}_dir"
            md_i_orig = pdf_to_md(pdf_i, md2_dir)
            md_i = work / f"md_{i}.md"
            shutil.copy(md_i_orig, md_i)

            sim_to_0, tokens_i, _ = similarity(md_i, md0)
            sim_to_prev, _, _ = similarity(md_i, prev_md) if i > 1 else (None, None, None)

            elapsed = time.time() - t0
            iterations.append({
                "i": i,
                "md_path": str(md_i),
                "tokens": tokens_i,
                "sim_to_md0": sim_to_0,
                "sim_to_prev": sim_to_prev,
                "seconds": elapsed,
            })
            print(f"  sim(MD₀): {sim_to_0*100:.2f}%, tempo: {elapsed:.0f}s")
            prev_md = md_i

        except Exception as e:
            print(f"  [FALHA] {type(e).__name__}: {str(e)[:150]}")
            iterations.append({"i": i, "error": str(e)[:200]})
            break

    t_total = time.time() - t_total_start

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "md0": str(args.md_initial),
        "iterations": iterations,
        "total_seconds": t_total,
    }

    json_path = work / "_multi_roundtrip.json"
    md_path = work / "_multi_roundtrip.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_report(report), encoding="utf-8")

    print(f"\n[OK] {json_path}")
    print(f"[OK] {md_path}")


if __name__ == "__main__":
    main()
