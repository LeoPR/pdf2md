"""Executor de pipeline do roteador (T090 marco 2).

`run_pipeline(pipeline, pdf, out_dir)` recebe o `Pipeline` que `route()` decidiu e
EXECUTA os steps implementados, devolvendo o md produzido + o que rodou/pulou.

Steps implementados:
  - PRIMARY: pdftotext, tesseract (CPU, em pdf2md.extractors) e marker (subprocess externo)
  - OPTIMIZER: pdf2md-optimize (só faz sentido quando há imagens — i.e. saída do marker)

Steps AINDA não implementados (pulam com nota honesta):
  - REFINER pix2tex (BURACO #3: falta cropper de fórmula CPU)
  - REFINER gemma3/qwen (T180: pipeline small-image decompose não promovido)

O marker_runner é injetável → as paths CPU (pdftotext/tesseract) são testáveis sem GPU.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from pdf2md._profiles import OPTIMIZER, PRIMARY, REFINER
from pdf2md.extractors import extract_pdftotext, extract_tesseract
from pdf2md.routing import Pipeline

MarkerRunner = Callable[[Path, Path], Path]   # (pdf, out_dir) -> caminho do .md gerado


@dataclass
class ExecResult:
    output_md: Path | None
    primary: str | None
    ran: list[str] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)
    degraded: bool = False
    rationale: list[str] = field(default_factory=list)

    def summary(self) -> str:
        chain = " + ".join(self.ran) or "(nada)"
        tag = " [DEGRADADO]" if self.degraded else ""
        skip = f" · pulou: {', '.join(a for a, _ in self.skipped)}" if self.skipped else ""
        return f"executou{tag}: {chain}{skip} → {self.output_md}"


def run_pipeline(pipeline: Pipeline, pdf_path: str | Path, out_dir: str | Path,
                 *, marker_runner: MarkerRunner | None = None) -> ExecResult:
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    res = ExecResult(output_md=None, primary=None,
                     degraded=pipeline.degraded, rationale=list(pipeline.rationale))
    md_text: str | None = None

    for step in pipeline.steps:
        if step.role == PRIMARY:
            res.primary = step.algo
            if step.algo == "pdftotext":
                md_text = extract_pdftotext(pdf_path).markdown
                res.output_md = _write_md(out_dir, pdf_path, md_text)
            elif step.algo == "tesseract":
                md_text = extract_tesseract(pdf_path).markdown
                res.output_md = _write_md(out_dir, pdf_path, md_text)
            elif step.algo == "marker":
                runner = marker_runner or _default_marker_runner
                res.output_md = runner(pdf_path, out_dir)
            else:
                res.skipped.append((step.algo, "PRIMARY desconhecido — sem executor"))
                continue
            res.ran.append(step.algo)

        elif step.role == REFINER:
            why = ("pix2tex: falta cropper de fórmula CPU (BURACO #3)"
                   if step.algo == "pix2tex"
                   else "VLM small-image decompose não promovido (T180)")
            res.skipped.append((step.algo, why))

        elif step.role == OPTIMIZER:
            # optimize opera sobre imagens extraídas. Só o marker (único PRIMARY que
            # emite imagens) gera material; extratores texto-puro (pdftotext/tesseract)
            # não → no-op explícito. Gate no primary evita re-otimizar imagens stale
            # de um out_dir reusado.
            if res.primary == "marker" and _list_images(out_dir):
                from pdf2md.optimize import optimize_dir
                optimize_dir(out_dir)
                res.ran.append(step.algo)
            else:
                res.skipped.append((step.algo, "sem imagens extraídas (extrator texto-puro)"))

    # pass2 (--indexacao) é um artefato ENFILEIRÁVEL, não executado agora — o spec
    # define pass2 como passada diferida (worker/cron). Surfaçamos em vez de dropar.
    if pipeline.pass2 is not None:
        res.rationale.append(
            f"pass2 enfileirável (deferido p/ worker, NÃO executado agora): {pipeline.pass2.summary()}"
        )

    return res


def _write_md(out_dir: Path, pdf_path: Path, md: str) -> Path:
    p = out_dir / f"{pdf_path.stem}.md"
    p.write_text(md, encoding="utf-8")
    return p


def _list_images(out_dir: Path) -> list[Path]:
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    return [p for p in out_dir.rglob("*") if p.suffix.lower() in exts]


def _discover_marker() -> str | None:
    if os.environ.get("PDF2MD_MARKER"):
        return os.environ["PDF2MD_MARKER"]
    if shutil.which("marker_single"):
        return "marker_single"
    win = Path(r"Z:\venvs\marker\Scripts\marker_single.exe")
    return str(win) if win.exists() else None


def _default_marker_runner(pdf_path: Path, out_dir: Path) -> Path:
    """Roda marker_single (subprocess, com timeout) e localiza o .md correto."""
    marker = _discover_marker()
    if marker is None:
        raise RuntimeError("marker_single não encontrado (rode `pdf2md doctor`).")
    # timeout generoso escalado por páginas (marker mediu ~12.9s/pg; 30s/pg = folga ~2.3×).
    try:
        import fitz
        d = fitz.open(str(pdf_path)); n = len(d); d.close()
    except Exception:
        n = 50
    timeout_s = 60 + n * 30
    try:
        subprocess.run(
            [marker, str(pdf_path), "--output_dir", str(out_dir), "--output_format", "markdown"],
            check=True, timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"marker excedeu timeout de {timeout_s}s em {pdf_path.name} ({n}pg).")
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"marker falhou (exit {exc.returncode}) em {pdf_path.name}.")
    # marker_single escreve <out_dir>/<stem>/<stem>.md. Casar pelo stem e EXCLUIR
    # relatórios próprios do pdf2md (prefixo '_', ex. _image_optimization.md) que
    # ordenariam antes do md real num out_dir reusado.
    stem = pdf_path.stem
    exact = [p for p in out_dir.rglob(f"{stem}.md") if not p.name.startswith("_")]
    if exact:
        return sorted(exact)[0]
    others = [p for p in out_dir.rglob("*.md") if not p.name.startswith("_")]
    if others:
        return sorted(others)[0]
    raise RuntimeError(f"marker não produziu .md em {out_dir}")
