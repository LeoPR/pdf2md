"""Round-trip iterativo: MD₀ → PDF → MD₁ → PDF → MD₂ → … (N iterações).

Mede similaridade a cada iteração para detectar:
- **Convergência**: similaridade estabiliza num "ponto fixo" (~97% no paper de teste)
- **Drift**: similaridade decai a cada iteração
- **Drift logarítmico**: cai rápido nas primeiras, depois estabiliza

Reusa `pdf2md.roundtrip.md_to_pdf` + `pdf_to_md` para evitar duplicar lógica.
Gera `_multi_roundtrip.{md,json}` no work_dir.
"""
from __future__ import annotations

import json
import re
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from pdf2md.normalize import normalize_md
from pdf2md.roundtrip import (
    DEFAULT_CHROME,
    DEFAULT_MARKER,
    DEFAULT_PANDOC,
    md_to_pdf,
    pdf_to_md,
)


@dataclass
class IterationResult:
    """Uma iteração do multi-roundtrip."""
    i: int
    tokens: int = 0
    sim_to_md0: float | None = None
    sim_to_prev: float | None = None
    seconds: float = 0.0
    md_path: str = ""
    error: str | None = None


@dataclass
class MultiRoundtripReport:
    md0: str
    iterations: list[IterationResult] = field(default_factory=list)
    total_seconds: float = 0.0
    generated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "md0": self.md0,
            "iterations": [vars(it) for it in self.iterations],
            "total_seconds": self.total_seconds,
        }


def similarity(md_a: Path, md_b: Path) -> tuple[float, int, int]:
    """Token similarity entre dois MDs após normalize_md. Retorna (sim, ta, tb)."""
    a = normalize_md(md_a.read_text(encoding="utf-8"))
    b = normalize_md(md_b.read_text(encoding="utf-8"))
    ta = re.findall(r"\S+", a)
    tb = re.findall(r"\S+", b)
    return SequenceMatcher(None, ta, tb).ratio(), len(ta), len(tb)


def render_report(report: MultiRoundtripReport) -> str:
    """Formata report como MD humano-legível, com curva e veredito."""
    iters = report.iterations
    if not iters:
        return "# Multi-roundtrip — sem iterações\n"

    lines = [
        "# Relatório multi-iteration round-trip",
        "",
        f"*Gerado em: {report.generated_at}*",
        "",
        f"- **Doc inicial:** `{report.md0}`",
        f"- **Iterações:** {len(iters)}",
        f"- **Tempo total:** {report.total_seconds:.0f} s",
        "",
        "## Curva de similaridade",
        "",
        "Similaridade entre cada MDᵢ e MD₀. Se o pipeline é idempotente/estável,",
        "a curva achata depois de 1-2 iterações.",
        "",
        "| i | Tokens MDᵢ | Sim(MDᵢ, MD₀) | Sim(MDᵢ, MDᵢ₋₁) | Tempo (s) |",
        "|---:|---:|---:|---:|---:|",
    ]
    for it in iters:
        if it.error:
            lines.append(f"| {it.i} | — | — | — | falha: {it.error[:60]} |")
            continue
        sim0 = f"{it.sim_to_md0*100:.2f}%" if it.sim_to_md0 is not None else "—"
        simp = f"{it.sim_to_prev*100:.2f}%" if it.sim_to_prev is not None else "—"
        lines.append(f"| {it.i} | {it.tokens:,} | {sim0} | {simp} | {it.seconds:.0f} |")

    # Veredito
    sims = [it.sim_to_md0 for it in iters if it.sim_to_md0 is not None]
    if len(sims) >= 2:
        first, last = sims[0], sims[-1]
        diff = (first - last) * 100
        last_two_diff = abs(sims[-1] - sims[-2]) * 100
        lines += ["", "## Veredito", ""]
        if abs(diff) < 1.0:
            lines.append("**Pipeline estável (idempotente)** — drift < 1% entre 1ª e última iteração.")
        elif diff > 0 and last_two_diff < 0.5:
            lines.append(f"**Convergência logarítmica** — perdeu {diff:.1f}% no total mas estabilizou (Δ últimas duas: {last_two_diff:.2f}%).")
        elif diff > 0:
            lines.append(f"**Drift contínuo** — perdeu {diff:.1f}% e ainda variando.")
        else:
            lines.append("**Comportamento inesperado** — similaridade aumentou (improvável; revisar).")

    return "\n".join(lines) + "\n"


def _safe_rmtree(work: Path) -> None:
    """Remove work_dir resilientemente (Windows às vezes trava em handles abertos)."""
    if not work.exists():
        return
    def _retry(func, path, exc_info):
        import os, stat
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass
    shutil.rmtree(work, onerror=_retry)
    if work.exists():
        work.rename(work.with_name(work.name + f"_old_{int(time.time())}"))


def run_multi_roundtrip(
    md_initial: Path,
    work_dir: Path,
    *,
    iterations: int = 5,
    pandoc: str = DEFAULT_PANDOC,
    chrome: str = DEFAULT_CHROME,
    marker: str = DEFAULT_MARKER,
    on_iter_start=None,
    on_iter_end=None,
) -> MultiRoundtripReport:
    """Pipeline iterativo. Para na primeira falha (preserva resultados até então).

    Args:
        md_initial: MD inicial (será copiado como md0.md no work_dir).
        work_dir: limpo+recriado. Recebe md0.md, iter_N.pdf, md_N.md por iteração.
        iterations: quantas iterações tentar.
        on_iter_start / on_iter_end: callbacks opcionais para progresso.

    Returns:
        MultiRoundtripReport com todas iterações (sucesso ou falha).
    """
    _safe_rmtree(work_dir)
    work_dir.mkdir(parents=True)

    # Setup: md0 + imagens
    md0 = work_dir / "md0.md"
    shutil.copy(md_initial, md0)
    src_imgs = md_initial.parent / "images"
    if src_imgs.is_dir():
        shutil.copytree(src_imgs, work_dir / "images")

    report = MultiRoundtripReport(
        md0=str(md_initial),
        generated_at=datetime.now().isoformat(timespec="seconds"),
    )
    t_total_start = time.time()
    prev_md = md0

    for i in range(1, iterations + 1):
        if on_iter_start:
            on_iter_start(i)
        t0 = time.time()
        result = IterationResult(i=i)
        try:
            pdf_i = work_dir / f"iter_{i}.pdf"
            md_to_pdf(prev_md, pdf_i, pandoc=pandoc, chrome=chrome)
            md2_dir = work_dir / f"md_{i}_dir"
            md_i_orig = pdf_to_md(pdf_i, md2_dir, marker=marker)
            md_i = work_dir / f"md_{i}.md"
            shutil.copy(md_i_orig, md_i)

            sim_to_0, tokens_i, _ = similarity(md_i, md0)
            sim_to_prev = None
            if i > 1:
                sim_to_prev, _, _ = similarity(md_i, prev_md)

            result.tokens = tokens_i
            result.sim_to_md0 = sim_to_0
            result.sim_to_prev = sim_to_prev
            result.seconds = time.time() - t0
            result.md_path = str(md_i)
            prev_md = md_i
        except Exception as e:
            result.error = f"{type(e).__name__}: {str(e)[:150]}"
            result.seconds = time.time() - t0
            report.iterations.append(result)
            if on_iter_end:
                on_iter_end(result)
            break

        report.iterations.append(result)
        if on_iter_end:
            on_iter_end(result)

    report.total_seconds = time.time() - t_total_start
    return report


def write_report(report: MultiRoundtripReport, work_dir: Path) -> tuple[Path, Path]:
    """Salva report como JSON + MD. Retorna paths."""
    json_path = work_dir / "_multi_roundtrip.json"
    md_path = work_dir / "_multi_roundtrip.md"
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    md_path.write_text(render_report(report), encoding="utf-8")
    return json_path, md_path


def _cli() -> int:
    """CLI standalone (compat com `python src/multi_roundtrip.py md work -n N`)."""
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    p = argparse.ArgumentParser()
    p.add_argument("md_initial", type=Path)
    p.add_argument("work_dir", type=Path)
    p.add_argument("--iterations", type=int, default=5)
    args = p.parse_args()

    if not args.md_initial.is_file():
        print(f"[ERRO] MD inicial não encontrado: {args.md_initial}", file=sys.stderr)
        return 1

    print(f"[INFO] MD inicial: {args.md_initial}")
    print(f"[INFO] Work dir: {args.work_dir}")
    print(f"[INFO] Iterações: {args.iterations}")

    def _start(i: int) -> None:
        print(f"\n=== Iteração {i} ===")
        print("  MD → PDF...")
        print("  PDF → MD...")

    def _end(r: IterationResult) -> None:
        if r.error:
            print(f"  [FALHA] {r.error}")
        else:
            print(f"  sim(MD₀): {r.sim_to_md0*100:.2f}%, tempo: {r.seconds:.0f}s")

    report = run_multi_roundtrip(
        args.md_initial, args.work_dir,
        iterations=args.iterations,
        on_iter_end=_end,
    )
    json_path, md_path = write_report(report, args.work_dir)
    print(f"\n[OK] {json_path}")
    print(f"[OK] {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
