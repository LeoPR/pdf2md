"""Executor de pipeline do roteador (T090 marco 2).

`run_pipeline(pipeline, pdf, out_dir)` recebe o `Pipeline` que `route()` decidiu e
EXECUTA os steps implementados, devolvendo o md produzido + o que rodou/pulou.

Steps implementados:
  - PRIMARY: pdftotext, tesseract (CPU, em pdf2md.extractors) e marker (subprocess externo)
  - REFINER pix2tex: cropper de fórmula built-in (formula_cropper, CPU) + pix2tex externo
    (runtime torch via subprocess). Emite as fórmulas como LaTeX (matriz flagada baixa-conf).
  - OPTIMIZER: pdf2md-optimize (só faz sentido quando há imagens — i.e. saída do marker)

Steps AINDA não implementados (pulam com nota honesta):
  - REFINER gemma3/qwen (T180: pipeline small-image decompose não promovido)

marker_runner e pix2tex_runner são injetáveis → paths CPU testáveis sem GPU/torch.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from pdf2md._profiles import OPTIMIZER, PRIMARY, REFINER
from pdf2md.extractors import extract_pdftotext, extract_tesseract
from pdf2md.formula_cropper import crop_formulas
from pdf2md.routing import Pipeline

MarkerRunner = Callable[[Path, Path], Path]      # (pdf, out_dir) -> caminho do .md gerado
Pix2texRunner = Callable[[Path], dict]           # (crop_dir) -> {png_name: latex}


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
                 *, marker_runner: MarkerRunner | None = None,
                 pix2tex_runner: Pix2texRunner | None = None) -> ExecResult:
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

        elif step.role == REFINER and step.algo == "pix2tex":
            new_md, ran_ok, note = _run_pix2tex(
                pdf_path, out_dir, md_text, res.output_md, pix2tex_runner)
            if ran_ok:
                md_text = new_md
                res.output_md = _write_md(out_dir, pdf_path, md_text)
                res.ran.append("pix2tex")
            else:
                res.skipped.append(("pix2tex", note))

        elif step.role == REFINER:
            res.skipped.append((step.algo, "VLM small-image decompose não promovido (T180)"))

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
    # exclui dirs/arquivos com prefixo '_' (relatórios + _formula_crops do pix2tex) —
    # o OPTIMIZER não deve otimizar os crops de fórmula como se fossem imagens do doc.
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    return [p for p in out_dir.rglob("*")
            if p.suffix.lower() in exts
            and not any(part.startswith("_") for part in p.relative_to(out_dir).parts)]


def _run_pix2tex(pdf_path: Path, out_dir: Path, md_text: str | None,
                 output_md: Path | None, runner: Pix2texRunner | None):
    """Cropa as fórmulas display (built-in, CPU) e roda pix2tex (externo) sobre os
    crops, anexando o LaTeX ao md. Devolve (novo_md|None, rodou?, nota_de_skip)."""
    if md_text is None and output_md is not None:
        md_text = Path(output_md).read_text(encoding="utf-8")
    if md_text is None:
        return None, False, "sem markdown base p/ anexar fórmulas"

    crop_dir = Path(out_dir) / "_formula_crops"
    if crop_dir.exists():                       # limpa crops stale (out_dir reusado → evita re-OCR)
        for old in crop_dir.glob("*.png"):
            old.unlink()
    try:
        regions = crop_formulas(pdf_path, crop_dir)
    except Exception as exc:
        return None, False, f"cropper falhou: {exc}"
    if not regions:
        return None, False, "nenhuma fórmula display detectada"

    if runner is None and _discover_pix2tex_python() is None \
            and not (shutil.which("pix2tex") or shutil.which("latexocr")):
        return None, False, (f"{len(regions)} fórmulas cropadas mas runtime pix2tex ausente "
                             f"(set PDF2MD_PIX2TEX_PYTHON)")
    run = runner or _default_pix2tex_runner
    try:
        latex_by_crop = run(crop_dir)
    except Exception as exc:
        return None, False, f"runtime pix2tex falhou: {exc}"
    new_md, n_appended = _append_formulas(md_text, regions, latex_by_crop)
    if n_appended == 0:
        return None, False, f"{len(regions)} fórmulas cropadas mas 0 legíveis (pix2tex vazio)"
    return new_md, True, ""


def _append_formulas(md: str, regions, latex_by_crop: dict) -> tuple[str, int]:
    """Anexa seção de fórmulas (LaTeX). Matriz/multi-linha flagada baixa-confiança.
    Devolve (md, n_anexadas). Posição inline no corpo = futuro (exige alinhamento
    com a saída pdftotext)."""
    out = ["", "## Fórmulas extraídas (LaTeX)", "",
           "<!-- formula_cropper (CPU) + pix2tex. Posição inline no corpo = trabalho futuro. -->", ""]
    n = 0
    for r in regions:
        latex = (latex_by_crop.get(r.crop_path.name, "") if r.crop_path else "").strip()
        if not latex:
            continue
        tag = f"({r.label})" if r.label else f"pg{r.page_index}"
        warn = " ⚠️ matriz/multi-linha (baixa confiança CPU ~0.50; marker/GPU recomendado)" \
            if r.is_complex else ""
        out += [f"- **{tag}**{warn}", f"  $$ {latex} $$"]
        n += 1
    return (md.rstrip() + "\n" + "\n".join(out) + "\n", n) if n else (md, 0)


def _discover_pix2tex_python() -> str | None:
    env = os.environ.get("PDF2MD_PIX2TEX_PYTHON")
    return env if env and Path(env).exists() else None


def _default_pix2tex_runner(crop_dir: Path) -> dict:
    """Roda pix2tex no venv externo (torch). Preferência: python do venv + runner
    standalone; fallback: CLI pix2tex/latexocr por imagem."""
    crop_dir = Path(crop_dir)
    crops = sorted(crop_dir.glob("*.png"))
    py = _discover_pix2tex_python()
    if py:
        runner_script = Path(__file__).parent / "_pix2tex_runner.py"
        out_json = crop_dir / "_pix2tex.json"
        timeout_s = 120 + len(crops) * 30        # cold-start ~12s + ~6.5s/formula + folga
        subprocess.run([py, str(runner_script), str(crop_dir), str(out_json)],
                       check=True, timeout=timeout_s,
                       capture_output=True, text=True)   # não polui o stdout do CLI
        return json.loads(out_json.read_text(encoding="utf-8"))
    cli = shutil.which("pix2tex") or shutil.which("latexocr")
    if not cli:
        raise RuntimeError("runtime pix2tex não encontrado (set PDF2MD_PIX2TEX_PYTHON).")
    out = {}
    for png in crops:
        r = subprocess.run([cli, str(png)], capture_output=True, text=True, timeout=120)
        out[png.name] = r.stdout.strip()
    return out


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
