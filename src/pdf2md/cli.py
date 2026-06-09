"""CLI unificado do pdf2md.

Filosofia:
- **Macro** (`pdf2md FILE.pdf`): one-shot inteligente — extrai, organiza,
  otimiza, gera stats e marca proveniência. Decide via auto-detect (TOC do PDF).
- **Subcomandos finos** (`pdf2md extract`, `restruct`, `optimize`, ...): cada
  etapa isolada, para controle granular ou recuperar de pipeline parcial.
- **Meta** (`doctor`, `version`): diagnóstico do ambiente.

Ferramentas externas (marker, pandoc, chrome) **não** são instaladas pelo pip
deste pacote — conflito histórico de `pillow<11` (marker-pdf 1.10) vs `pillow>=11`
(otimização adaptativa). Cada uma vive no seu venv/PATH; `pdf2md doctor` valida.

Para uso, ver `pdf2md --help` ou `pdf2md help <subcmd>`.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

# Reconfigurar stdout/stderr para UTF-8 em Windows (default cp1252 quebra com
# acentos e setas no Rich/Typer help). Idempotente — se já estiver em utf-8, no-op.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass

import typer

from pdf2md.normalize import normalize_md
from pdf2md.provenance import (
    Provenance,
    apply_to_dir as _apply_provenance_dir,
    detect_current_commit,
)
from pdf2md.discovery import available, find_chrome, find_marker, find_pandoc

# ---------------------------------------------------------------------------
# Defaults e descoberta de ferramentas externas
# ---------------------------------------------------------------------------

# Ferramentas externas: descoberta portável (env PDF2MD_* → PATH multi-SO → local do SO).
# Ver pdf2md/discovery.py; `pdf2md doctor` reporta o que falta (nunca aponta p/ drive do autor).
DEFAULT_MARKER = find_marker()
DEFAULT_PANDOC = find_pandoc()
DEFAULT_CHROME = find_chrome()

# Path do diretório `src/` para invocar scripts standalone via subprocess.
# Quando `pdf2md` for instalado via `pip`, esses scripts serão movidos para
# módulos importáveis em v0.4. Por enquanto delegamos.
_SRC_DIR = Path(__file__).resolve().parent.parent  # src/
_REPO_ROOT = _SRC_DIR.parent

# ---------------------------------------------------------------------------
# App typer
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="pdf2md",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    help="Conversor PDF↔MD com round-trip mensurável.",
    rich_markup_mode="rich",
)


def _run(
    cmd: list[str],
    *,
    check: bool = True,
    cwd: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Roda comando externo e ecoa stderr. `extra_env` é mesclado em os.environ."""
    typer.echo(f"$ {' '.join(str(c) for c in cmd)}", err=True)
    env = None
    if extra_env:
        env = {**os.environ, **extra_env}
    return subprocess.run([str(c) for c in cmd], check=check, cwd=cwd, env=env)


def _python() -> str:
    return sys.executable


def _detect_marker_version() -> str | None:
    """Lê versão do marker-pdf no venv de DEFAULT_MARKER (via dist-info)."""
    try:
        marker_exe = Path(DEFAULT_MARKER)
        if not marker_exe.exists():
            return None
        # venv: <root>/Scripts/marker_single.exe (Win) ou <root>/bin/marker_single (POSIX).
        # site-packages: Lib/site-packages (Win) ou lib/pythonX.Y/site-packages (POSIX).
        venv = marker_exe.parent.parent
        for site_pkgs in [venv / "Lib" / "site-packages", *venv.glob("lib/python*/site-packages")]:
            for d in site_pkgs.glob("marker_pdf-*.dist-info"):
                return d.name.replace("marker_pdf-", "").replace(".dist-info", "")
    except Exception:
        pass
    return None


def _detect_torch_cuda_in_marker_venv() -> tuple[str | None, str | None, float | None]:
    """Inspeciona torch+cuda no venv do marker (sem importar — só metadata)."""
    try:
        marker_exe = Path(DEFAULT_MARKER)
        if not marker_exe.exists():
            return None, None, None
        venv_python = marker_exe.parent / "python.exe"
        if not venv_python.exists():
            return None, None, None
        # Pergunta direto ao Python do venv do marker
        result = subprocess.run(
            [str(venv_python), "-c",
             "import torch,json; "
             "d=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None; "
             "m=round(torch.cuda.get_device_properties(0).total_memory/(1024**3),1) if torch.cuda.is_available() else None; "
             "print(json.dumps({'torch':torch.__version__,'cuda':d,'mem':m}))"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            import json as _json
            data = _json.loads(result.stdout.strip())
            return data.get("torch"), data.get("cuda"), data.get("mem")
    except Exception:
        pass
    return None, None, None


def _detect_pandoc_version() -> str | None:
    """Versão do pandoc disponível no PATH."""
    try:
        result = subprocess.run(
            [DEFAULT_PANDOC, "--version"], capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout:
            line = result.stdout.splitlines()[0]
            return line.replace("pandoc ", "").replace("pandoc.exe ", "").strip()
    except Exception:
        pass
    return None


def _detect_external_tools() -> dict[str, str | float]:
    """Monta dict de versões reais das ferramentas externas (kwargs para `pdf2md.stats`).

    Necessário porque pdf2md roda num venv distinto do marker (conflito histórico
    pillow<11 vs pillow>=11). Detectamos versões inspecionando metadata do venv
    do marker em vez de importar — assim stats reporta versões reais em vez de
    `n/a`/`CPU only` (regressão pegada em 2026-05-12).
    """
    overrides: dict[str, str | float] = {}
    mv = _detect_marker_version()
    if mv:
        overrides["marker_version"] = mv
    tv, cuda, mem = _detect_torch_cuda_in_marker_venv()
    if tv:
        overrides["torch_version"] = tv
    if cuda:
        overrides["cuda_device"] = cuda
    if mem is not None:
        overrides["cuda_memory_gb"] = mem
    pv = _detect_pandoc_version()
    if pv:
        overrides["pandoc_version"] = pv
    return overrides


def _detect_book(pdf_path: Path) -> bool:
    """True se PDF tem TOC nivel >= 2 (sugere livro com capítulos)."""
    try:
        import fitz
        toc = fitz.open(pdf_path).get_toc()
        return any(level >= 2 for level, _, _ in toc) and len(toc) >= 3
    except Exception:
        return False


def _sha256_short(path: Path) -> str | None:
    try:
        import hashlib
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 16), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Meta: doctor e version
# ---------------------------------------------------------------------------

@app.command()
def doctor(intent: str = typer.Option(
        None, "--intent", "-i",
        help="mostra o pipeline que o roteador (T090) escolheria p/ ESTE intent neste host")):
    """Diagnostica o ambiente: core, extras pip e capabilities externas. Não modifica nada.

    Core (PyMuPDF/Pillow) e extras pip ([rtpixel]/[ocr]) são do pacote; marker/pix2tex/
    ollama/pandoc/chrome são EXTERNOS (venv/binário/server) — opcionais. Com `--intent`,
    mostra o que aquele intent usaria aqui (com a degradação honesta se faltar algo).
    """
    import importlib.util as _ilu

    from pdf2md.extractors import tesseract_cmd
    from pdf2md.routing import MARKER_VRAM_MIN_MB, HostInfo

    typer.secho("pdf2md doctor — diagnóstico do ambiente", bold=True)
    typer.echo("")
    host = HostInfo.detect()
    rows: list[tuple[str, str, str]] = []

    # --- core (sempre instalado: é o pacote base) ---
    try:
        import fitz  # noqa: F401
        rows.append(("PyMuPDF (core)", "OK", "extração CPU pdftotext / probe"))
    except ImportError:
        rows.append(("PyMuPDF (core)", "MISSING", "pip install pymupdf"))
    try:
        from PIL import Image as _img  # noqa: F401
        rows.append(("Pillow (core)", "OK", f"v{__import__('PIL').__version__} — optimize de imagens"))
    except ImportError:
        rows.append(("Pillow (core)", "MISSING", "pip install pillow"))

    # --- extras pip (opcionais, deste pacote) ---
    rt_ok = all(_ilu.find_spec(m) is not None for m in ("numpy", "scipy", "skimage"))
    rows.append(("[rtpixel] visual", "OK" if rt_ok else "—",
                 "validador SSIM/align" if rt_ok else "pip install 'pdf2md-tool[rtpixel]'"))
    twrap = _ilu.find_spec("pytesseract") is not None

    # --- capabilities EXTERNAS (venv/binário/server; nunca pip deste pacote) ---
    marker_ok = host.has_marker and host.gpu_vram_mb >= MARKER_VRAM_MIN_MB
    rows.append(("marker_single (GPU)", "OK" if marker_ok else "—",
                 f"VRAM {host.gpu_vram_mb}MB ok ({DEFAULT_MARKER})" if marker_ok
                 else "venv próprio + GPU≥4GB — math/layout nativo (https://github.com/datalab-to/marker)"))
    tbin = tesseract_cmd()
    if tbin and twrap:
        rows.append(("tesseract (OCR)", "OK", f"{tbin} + pytesseract"))
    elif tbin or twrap:
        rows.append(("tesseract (OCR)", "PARCIAL",
                     f"engine {'OK' if tbin else 'FALTA'} / wrapper [ocr] {'OK' if twrap else 'FALTA'}"))
    else:
        rows.append(("tesseract (OCR)", "—", "engine UB-Mannheim + pip install 'pdf2md-tool[ocr]'"))
    rows.append(("pix2tex (math)", "OK" if host.has_pix2tex else "—",
                 "runtime torch" if host.has_pix2tex else "set PDF2MD_PIX2TEX_PYTHON (venv com pix2tex)"))
    rows.append(("ollama (VLM logos)", "OK" if host.has_ollama else "—",
                 "daemon :11434" if host.has_ollama else "(opcional) ollama daemon + pull gemma3/qwen"))
    if shutil.which(DEFAULT_PANDOC):
        try:
            v = subprocess.run([DEFAULT_PANDOC, "--version"], capture_output=True, text=True, timeout=5)
            rows.append(("pandoc", "OK", v.stdout.splitlines()[0] if v.stdout else DEFAULT_PANDOC))
        except Exception:
            rows.append(("pandoc", "OK", DEFAULT_PANDOC))
    else:
        rows.append(("pandoc", "—", "MD→HTML — https://pandoc.org/installing.html"))
    if available(DEFAULT_CHROME):
        rows.append(("chrome (headless)", "OK", DEFAULT_CHROME))
    else:
        rows.append(("chrome (headless)", "—", "HTML→PDF (KaTeX) — chrome/chromium no PATH ou PDF2MD_CHROME"))

    # --- Print table ---
    w = max(len(r[0]) for r in rows)
    for name, status, detail in rows:
        color = (typer.colors.GREEN if status == "OK"
                 else typer.colors.RED if status == "MISSING"
                 else typer.colors.YELLOW)
        typer.echo(f"  {name:<{w}}  ", nl=False)
        typer.secho(f"{status:<8}", fg=color, nl=False)
        typer.echo(f"  {detail}")

    # --- --intent: o que o roteador faria NESTE host (ponte capabilities↔intent) ---
    if intent:
        from pdf2md.routing import INTENTS, DocInfo, RoutingError, route
        typer.echo("")
        if intent not in INTENTS:
            typer.secho(f"intent inválido: {intent!r}. Válidos: {', '.join(INTENTS)}", fg=typer.colors.RED)
            raise typer.Exit(1)
        # doc genérico (text-layer, com math e logos) p/ revelar os refiners possíveis
        doc = DocInfo(n_pages=10, has_text_layer=True, math_density=1.0,
                      matrix_density=0.0, has_raster_logos=True)
        typer.secho(f"Para --intent {intent} neste host:", bold=True)
        try:
            pipe = route(intent, host, doc)
            typer.echo(f"  pipeline: {pipe.summary()}")   # summary() já inclui [DEGRADADO]
            for r in pipe.rationale:
                typer.echo(f"    · {r}")
            if pipe.pass2:
                typer.echo(f"  pass2 (enfileirável): {pipe.pass2.summary()}")
        except RoutingError as exc:
            typer.secho(f"  sem caminho viável: {exc}", fg=typer.colors.RED)


@app.command()
def version():
    """Versão do pacote + commit git (se aplicável)."""
    try:
        from importlib.metadata import version as _v
        pkg_ver = _v("pdf2md")
    except Exception:
        pkg_ver = "0.7.0 (uninstalled)"

    commit = detect_current_commit() or "—"
    typer.echo(f"pdf2md {pkg_ver}  (commit {commit})")


@app.command()
def route(
    pdf: Path = typer.Argument(..., help="PDF a rotear"),
    intent: str = typer.Option("auto", "--intent", "-i",
                               help="rapido|qualidade|balanceado|auto|indexacao|low-resource"),
    execute: bool = typer.Option(False, "--execute", "-x",
                                 help="Executa o pipeline decidido (default: só dry-run)"),
    out: Path = typer.Option(None, "--out", "-o", help="Diretório de saída (com --execute)"),
):
    """Decide (e opcionalmente executa) o pipeline de conversão por intent (T090).

    Sem --execute: dry-run — detecta host, caracteriza o PDF e imprime o pipeline
    que `route()` escolheria + o porquê. Com --execute: roda os steps implementados
    (pdftotext/tesseract/marker + optimize); refiners não-implementados pulam com nota.
    """
    from pdf2md.routing import DocInfo, HostInfo, RoutingError, ScanNoOCR
    from pdf2md.routing import route as _route

    host = HostInfo.detect()
    typer.secho("host:", bold=True)
    typer.echo(f"  CPU {host.cpu_cores} cores · RAM {host.ram_gb}GB · "
               f"GPU {host.gpu_vram_mb}MB · marker={host.has_marker} · "
               f"ollama={host.has_ollama} · tesseract={host.has_tesseract}")
    try:
        doc = DocInfo.probe(pdf)
    except Exception as exc:
        typer.secho(f"falha ao ler {pdf}: {exc}", fg=typer.colors.RED)
        raise typer.Exit(1)
    typer.secho("doc:", bold=True)
    typer.echo(f"  {doc.n_pages}pg · text-layer={doc.has_text_layer} · "
               f"math_density={doc.math_density} · logos={doc.has_raster_logos}")
    try:
        pipe = _route(intent, host, doc)
    except (RoutingError, ScanNoOCR) as exc:
        typer.secho(f"\n[ERRO] {exc}", fg=typer.colors.RED)
        raise typer.Exit(2)
    typer.secho(f"\n{pipe.summary()}", fg=typer.colors.GREEN, bold=True)
    for s in pipe.steps:
        typer.echo(f"  · {s.role:<9} {s.algo:<24} {s.reason}")
    if pipe.pass2:
        typer.echo(f"  pass2 (enfileirável): {pipe.pass2.summary()}")
    for r in pipe.rationale:
        typer.echo(f"  ℹ {r}")

    if not execute:
        return
    if out is None:
        typer.secho("\n--execute requer --out DIR", fg=typer.colors.RED)
        raise typer.Exit(1)
    from pdf2md.executor import run_pipeline
    typer.secho(f"\n[executando] → {out}", bold=True)
    try:
        res = run_pipeline(pipe, pdf, out)
    except Exception as exc:
        typer.secho(f"[ERRO execução] {exc}", fg=typer.colors.RED)
        raise typer.Exit(3)
    typer.secho(res.summary(), fg=typer.colors.GREEN)
    for algo, why in res.skipped:
        typer.echo(f"  ⊘ pulou {algo}: {why}")


# ---------------------------------------------------------------------------
# Subcomandos: utilitários puros (não precisam de tools externas)
# ---------------------------------------------------------------------------

@app.command("norm")
def norm(
    md_path: Path = typer.Argument(..., exists=True, dir_okay=False, help="Arquivo MD a normalizar"),
    strip_escapes: bool = typer.Option(False, "--strip-escapes/--keep-escapes", help="Remove \\X markdown escapes (Q11.b)"),
    in_place: bool = typer.Option(False, "-i", "--in-place", help="Sobrescreve o arquivo"),
):
    """Normalização canônica do MD (page markers, image paths, escapes).

    Mesma função usada internamente pelo `roundtrip` para comparação semântica.
    Sem `-i`, imprime para stdout.
    """
    text = md_path.read_text(encoding="utf-8")
    out = normalize_md(text, strip_md_escapes=strip_escapes)
    if in_place:
        md_path.write_text(out, encoding="utf-8")
        typer.echo(f"[OK] {md_path}", err=True)
    else:
        typer.echo(out)


@app.command("prov")
def prov(
    target_dir: Path = typer.Argument(..., exists=True, file_okay=False, help="Diretório com MDs a marcar"),
    pkg_version: str = typer.Option(None, "--version", help="Versão do conversor (default: git describe)"),
    source: str = typer.Option(None, "--source", help="Nome do PDF fonte"),
    sha256: str = typer.Option(None, "--sha256", help="SHA-256 do PDF fonte (ou caminho — auto-calcula)"),
    extractor: str = typer.Option(None, "--extractor", help="Ex: 'marker-pdf 1.10.2'"),
    when: str = typer.Option(None, "--date", help="Data ISO (default: hoje)"),
):
    """Aplica marcador de proveniência idempotente em cada MD do diretório.

    Insere após primeiro heading. Re-aplicar substitui em vez de duplicar.
    """
    if not pkg_version:
        try:
            v = subprocess.run(["git", "describe", "--tags", "--always"],
                               capture_output=True, text=True, check=True, timeout=5)
            pkg_version = v.stdout.strip() or "unknown"
        except Exception:
            pkg_version = "unknown"

    # Se --sha256 for caminho, calcula
    if sha256 and Path(sha256).exists():
        sha256 = _sha256_short(Path(sha256))

    prov_obj = Provenance(
        version=pkg_version,
        date=when or date.today().isoformat(),
        commit=detect_current_commit(),
        source=source,
        source_sha256=sha256,
        extractor=extractor,
    )
    results = _apply_provenance_dir(target_dir, prov_obj)
    changed = sum(1 for _, c in results if c)
    typer.echo(f"{len(results)} arquivos visitados, {changed} alterados")


# ---------------------------------------------------------------------------
# Subcomandos: pipeline (delegam para scripts em src/ via subprocess)
# ---------------------------------------------------------------------------

@app.command()
def extract(
    pdf: Path = typer.Argument(..., exists=True, dir_okay=False, help="PDF a extrair"),
    out: Path = typer.Option(..., "--out", "-o", help="Diretório de saída"),
    page_range: str = typer.Option(None, "--pages", help="Faixa de páginas (ex: '0-29' ou '0,5,10')"),
):
    """Extração base: marker_single PDF → MD.

    Wrapper sobre `marker_single` (datalab-to/marker). Para flags avançadas
    (--use_llm, --llm_service, etc.) chame marker_single direto.
    """
    if not (Path(DEFAULT_MARKER).exists() or shutil.which(DEFAULT_MARKER)):
        typer.secho(f"marker_single não encontrado em {DEFAULT_MARKER}. Rode `pdf2md doctor`.", fg=typer.colors.RED)
        raise typer.Exit(1)

    cmd = [DEFAULT_MARKER, str(pdf), "--output_dir", str(out), "--output_format", "markdown"]
    if page_range:
        cmd.extend(["--page_range", page_range])
    _run(cmd)


@app.command("restruct")
def restruct(
    target_dir: Path = typer.Argument(..., help="Diretório final (será criado)"),
    pdf: Path = typer.Option(..., "--pdf", exists=True, dir_okay=False, help="PDF original (para extrair TOC)"),
    marker_out: Path = typer.Option(..., "--marker-out", exists=True, file_okay=False, help="Saída do marker_single"),
):
    """Reorganiza saída do marker em capítulos via TOC do PDF.

    Cria estrutura: target/01_titulo/01_titulo.md + images/ + index.md.
    Usa pdf2md.restructure (importação direta, sem subprocess).
    """
    from pdf2md.restructure import restructure as _restructure

    typer.echo(f"[pdf2md restruct] {pdf.name} + {marker_out} → {target_dir}")

    def _report(cid: str, chars: int, imgs: int, error: str | None) -> None:
        if error:
            typer.echo(f"  [pulo] {cid}: {error}")
        else:
            typer.echo(f"  [{cid}] {chars:,} chars, {imgs} imagens")

    try:
        counts = _restructure(pdf, marker_out, target_dir, on_chapter=_report)
    except (ValueError, RuntimeError) as e:
        typer.secho(f"[ERRO] {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

    typer.echo(f"\n[OK] {len(counts)} capítulos em {target_dir}")


@app.command()
def optimize(
    target_dir: Path = typer.Argument(..., exists=True, file_okay=False, help="Diretório com MDs e imagens"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Não modifica, só relata"),
):
    """Otimização adaptativa de imagens (PNG paleta lossy / JPEG / B&W 1-bit).

    Classificador defensivo: continuous tone fica como JPEG, line art vira PNG paleta.
    Gera `_image_optimization.{md,json}` na raiz.
    Usa pdf2md.optimize (importação direta, sem subprocess).
    """
    from pdf2md.optimize import fmt_bytes, optimize_dir
    typer.echo(f"[pdf2md optimize] {target_dir}" + (" (dry-run)" if dry_run else ""))

    def _progress(i: int, total: int, rec: dict) -> None:
        if i % 20 == 0 or i == total:
            typer.echo(f"  [{i}/{total}]")

    json_path, md_path, summary = optimize_dir(
        target_dir, dry_run=dry_run, on_progress=_progress,
    )
    typer.echo(f"[OK] {json_path}")
    typer.echo(f"[OK] {md_path}")
    typer.echo(
        f"[RESUMO] {summary['changed']}/{summary['total_images']} convertidas, "
        f"{fmt_bytes(summary['bytes_saved'])} ({summary['savings_pct']:.1f}%)"
    )


@app.command()
def stats(
    target_dir: Path = typer.Argument(..., exists=True, file_okay=False, help="Diretório de MDs"),
    source_pdf: Path = typer.Option(None, "--source-pdf", exists=True, dir_okay=False, help="PDF original para métricas extras"),
    roundtrip_md1: Path = typer.Option(None, "--rt-md1", help="MD inicial para round-trip"),
    roundtrip_md2: Path = typer.Option(None, "--rt-md2", help="MD pós-roundtrip"),
):
    """Telemetria: tokens, fórmulas, imagens, headers + round-trip categorizado.

    Gera `_stats.{md,json}` no diretório. As versões marker/torch/CUDA/pandoc
    são auto-detectadas (do venv do marker via inspect, do pandoc no PATH) e
    passadas como kwargs para `pdf2md.stats.compute_stats` — assim o relatório
    mostra versões reais em vez de "n/a"/"CPU only" (regressão de 2026-05-12).
    """
    from pdf2md.stats import compute_stats
    typer.echo(f"[pdf2md stats] {target_dir}")
    json_path, md_path = compute_stats(
        target_dir,
        source_pdf=source_pdf,
        roundtrip_md1=roundtrip_md1,
        roundtrip_md2=roundtrip_md2,
        tool_overrides=_detect_external_tools(),
    )
    typer.echo(f"[OK] {json_path}")
    typer.echo(f"[OK] {md_path}")


@app.command("rt")
def rt(
    md_path: Path = typer.Argument(..., exists=True, dir_okay=False, help="MD inicial"),
    work_dir: Path = typer.Option(..., "--work", "-w", help="Diretório de trabalho (pdf, md2 temporários)"),
):
    """Round-trip single: MD → PDF → MD'. Mede similaridade de tokens.

    Reporta similaridade total + primeiras 5 divergências.
    Usa o módulo pdf2md.roundtrip (importação direta, sem subprocess).
    """
    from pdf2md.roundtrip import run_roundtrip
    typer.echo(f"[pdf2md rt] {md_path.name} → {work_dir}")
    result = run_roundtrip(
        md_path, work_dir,
        pandoc=DEFAULT_PANDOC, chrome=DEFAULT_CHROME, marker=DEFAULT_MARKER,
    )
    typer.echo(result.render_text())


@app.command("rt-pixel")
def rt_pixel(
    pdf_orig: Path = typer.Argument(..., exists=True, dir_okay=False, help="PDF original (source)"),
    pdf_render: Path = typer.Argument(..., exists=True, dir_okay=False, help="PDF reconstruído (render do pdf2md)"),
    align: str = typer.Option("hungarian", "--align", help="Alinhamento: hungarian | dtw"),
    dpi: int = typer.Option(150, "--dpi", help="Resolução do render para SSIM"),
    skip_ssim: bool = typer.Option(False, "--skip-ssim", help="Pula SSIM (modo rápido — só WER textual)"),
    out: Path = typer.Option(None, "--out", help="Salvar JSON em path (default: stdout-only)"),
):
    """Pixel-roundtrip visual L0.5: alinha páginas + macro SSIM + médio WER.

    Compara PDF original vs PDF reconstruído. Saída inclui mediana SSIM/WER,
    flags de páginas problemáticas. Skip-SSIM ~7× mais rápido (só textual).
    """
    from pdf2md.pixel_roundtrip import run_pixel_roundtrip
    typer.echo(f"[pdf2md rt-pixel] {pdf_orig.name} ↔ {pdf_render.name}")

    def _progress(cur: int, total: int) -> None:
        if cur == 1 or cur % 10 == 0 or cur == total:
            typer.echo(f"  SSIM {cur}/{total}")

    result = run_pixel_roundtrip(
        pdf_orig, pdf_render,
        align_method=align, dpi=dpi, skip_ssim=skip_ssim,
        on_progress=None if skip_ssim else _progress,
    )
    typer.echo("")
    typer.echo(result.render_text())
    if out:
        result.save_json(out)
        typer.echo(f"\n[OK] {out}")


@app.command("rt-multi")
def rt_multi(
    md_path: Path = typer.Argument(..., exists=True, dir_okay=False, help="MD inicial"),
    work_dir: Path = typer.Option(..., "--work", "-w", help="Diretório de trabalho"),
    iterations: int = typer.Option(3, "-n", "--iterations", help="Quantas iterações"),
):
    """Round-trip iterativo (N×): detecta convergência / drift / blow-up.

    Usa pdf2md.multi_roundtrip (importação direta, sem subprocess).
    """
    from pdf2md.multi_roundtrip import (
        IterationResult,
        run_multi_roundtrip,
        write_report,
    )
    typer.echo(f"[pdf2md rt-multi] {md_path.name}, {iterations} iter → {work_dir}")

    def _end(r: IterationResult) -> None:
        if r.error:
            typer.echo(f"  iter {r.i}: FALHA — {r.error}")
        else:
            typer.echo(f"  iter {r.i}: sim(MD₀) {r.sim_to_md0*100:.2f}%, {r.seconds:.0f}s")

    report = run_multi_roundtrip(
        md_path, work_dir,
        iterations=iterations,
        pandoc=DEFAULT_PANDOC, chrome=DEFAULT_CHROME, marker=DEFAULT_MARKER,
        on_iter_end=_end,
    )
    json_path, md_out = write_report(report, work_dir)
    typer.echo(f"\n[OK] {json_path}")
    typer.echo(f"[OK] {md_out}")


@app.command()
def aggr(
    root_dir: Path = typer.Argument(..., exists=True, file_okay=False, help="Raiz com vários _stats.json recursivos"),
    out: Path = typer.Option(None, "--out", help="Diretório do OVERVIEW (default: <root>)"),
):
    """Agrega múltiplos `_stats.json` em OVERVIEW consolidado.

    Detecta distribuição de round-trip, outliers, comparativo entre extrações.
    Usa pdf2md.aggregate (importação direta, sem subprocess).
    """
    from pdf2md.aggregate import aggregate, collect_docs
    docs = collect_docs(root_dir)
    typer.echo(f"[pdf2md aggr] {len(docs)} doc(s) com _stats.json em {root_dir}")
    md_path, json_path = aggregate(root_dir, out)
    typer.echo(f"[OK] {md_path}")
    typer.echo(f"[OK] {json_path}")


@app.command()
def pdfs(
    target_dir: Path = typer.Argument(..., exists=True, file_okay=False, help="Diretório com capítulos MD"),
):
    """Renderiza cada capítulo MD em PDF via pandoc + Chrome + KaTeX.

    Útil para validar visualmente o resultado antes de distribuir.
    Usa pdf2md.pdfs (importação direta, sem subprocess).
    """
    from pdf2md.pdfs import find_chapter_mds, generate_all
    targets = find_chapter_mds(target_dir)
    typer.echo(f"[pdf2md pdfs] {len(targets)} capítulos em {target_dir}")

    def _report(md: Path, pdf: Path | None, kb: float, err: Exception | None) -> None:
        if err:
            typer.echo(f"  {md.parent.name}/ FALHOU ({type(err).__name__}: {err})")
        else:
            typer.echo(f"  {md.parent.name}/ {kb:>6.0f} KB ✓")

    ok, fail = generate_all(target_dir, on_progress=_report)
    typer.echo(f"\n[OK] {ok}/{len(targets)}" + (f" — {fail} falhas" if fail else ""))
    if fail:
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Macro: convert (one-shot inteligente)
# ---------------------------------------------------------------------------

@app.command()
def convert(
    pdf: Path = typer.Argument(..., exists=True, dir_okay=False, help="PDF a converter"),
    out: Path = typer.Option(None, "--out", "-o", help="Diretório de saída (default: ./<pdf-basename>/)"),
    book: bool = typer.Option(False, "--book", help="Força split por capítulo (default: auto via TOC)"),
    paper: bool = typer.Option(False, "--paper", help="Força flat (sem restructure)"),
    intent: str = typer.Option(None, "--intent", "-i",
        help="Roteamento profile-aware (T090): rapido|qualidade|balanceado|auto|indexacao|low-resource. "
             "Escolhe a stack por host+doc. Substitui --quick/--best."),
    quick: bool = typer.Option(False, "--quick", "-q", help="[legado] Pula otimização + round-trip"),
    best: bool = typer.Option(False, "--best", help="[legado] Otimização total + multi-roundtrip 3 iter + rt-pixel"),
    no_optimize: bool = typer.Option(False, "--no-optimize", help="Não otimiza imagens"),
    no_stats: bool = typer.Option(False, "--no-stats", help="Não gera _stats.md"),
    no_provenance: bool = typer.Option(False, "--no-provenance", help="Não marca proveniência"),
    rt_pixel: bool = typer.Option(False, "--rt-pixel", help="Roda pixel-roundtrip visual L0.5 (~30-60s extra/cap)"),
    rt_pixel_skip_ssim: bool = typer.Option(False, "--rt-pixel-skip-ssim", help="Modo rápido do pixel-roundtrip (só WER textual)"),
):
    """[MACRO] Pipeline completo: extract + restructure + optimize + stats + provenance.

    Decide via auto-detect:
    - Se PDF tem TOC nivel >= 2 ⇒ livro (restructure por capítulo)
    - Senão ⇒ paper (flat)
    Use --book / --paper para forçar.

    Presets:
    - --quick: pula otimize + skip rt
    - --best: --no-optimize=false + rt-multi 3 iter

    Cada etapa pode ser desligada com --no-*.
    """
    if book and paper:
        typer.secho("--book e --paper são exclusivos", fg=typer.colors.RED)
        raise typer.Exit(2)
    if quick and best:
        typer.secho("--quick e --best são exclusivos", fg=typer.colors.RED)
        raise typer.Exit(2)

    out = out or Path.cwd() / pdf.stem
    out.mkdir(parents=True, exist_ok=True)

    # T090: roteamento por intent (profile-aware). Decide a stack por host+doc.
    if intent:
        if quick or best:
            typer.secho("--intent é exclusivo com --quick/--best (legado)", fg=typer.colors.RED)
            raise typer.Exit(2)
        from pdf2md.routing import DocInfo, HostInfo, RoutingError, ScanNoOCR
        from pdf2md.routing import route as _route
        host = HostInfo.detect()
        try:
            doc = DocInfo.probe(pdf)
            pipe = _route(intent, host, doc)
        except (RoutingError, ScanNoOCR) as exc:
            typer.secho(f"[ERRO roteamento] {exc}", fg=typer.colors.RED)
            raise typer.Exit(2)
        typer.secho(f"[pdf2md] convert {pdf.name} → {out}", bold=True)
        typer.secho(f"  {pipe.summary()}", fg=typer.colors.GREEN)
        for r in pipe.rationale:
            typer.echo(f"  ℹ {r}")

        if pipe.primary in ("pdftotext", "tesseract"):
            # caminho CPU: extrai → escreve md → stats + provenance (sem restructure/optimize)
            from pdf2md.executor import run_pipeline
            res = run_pipeline(pipe, pdf, out)
            for algo, why in res.skipped:
                typer.echo(f"  ⊘ {algo}: {why}")
            if not no_stats:
                typer.secho("\n[stats]", bold=True)
                stats(out, source_pdf=pdf, roundtrip_md1=None, roundtrip_md2=None)  # type: ignore
            if not no_provenance:
                typer.secho("[provenance]", bold=True)
                prov(out, pkg_version=None, source=pdf.name, sha256=str(pdf),  # type: ignore
                     extractor=pipe.primary, when=None)
            typer.secho(f"\n[OK] {res.output_md}", fg=typer.colors.GREEN)
            raise typer.Exit(0)

        # primary == marker → segue o fluxo marker legado (com restructure/stats/prov).
        if pipe.degraded:
            typer.secho("  [aviso] pipeline degradado — ver rationale acima", fg=typer.colors.YELLOW)

    is_book = book or (not paper and _detect_book(pdf))
    if not intent:
        typer.secho(f"[pdf2md] convert {pdf.name} → {out}", bold=True)
        typer.echo(f"  Preset: {'quick' if quick else ('best' if best else 'default')}")
    typer.echo(f"  Layout: {'book (restructure por TOC)' if is_book else 'paper (flat)'}")

    # 1. Extract
    # IMPORTANTE: marker_raw fica em pasta IRMÃ do out/, não dentro. Porque
    # restructure.py faz rmtree(target_dir) e apagaria o _marker_raw junto.
    marker_raw_root = out.with_name(out.name + "_marker_raw")
    if marker_raw_root.exists():
        shutil.rmtree(marker_raw_root)
    typer.secho("\n[1/5] extract (marker_single)...", bold=True)
    typer.echo(f"  marker_raw → {marker_raw_root}")
    extract(pdf, marker_raw_root, page_range=None)  # type: ignore

    # Marker cria subpasta com nome do PDF (sem extensão). Localiza-a robustamente.
    marker_out = marker_raw_root / pdf.stem
    if not marker_out.exists() or not list(marker_out.glob("*.md")):
        md_files = list(marker_raw_root.rglob("*.md"))
        if not md_files:
            typer.secho(f"Marker não produziu MD em {marker_raw_root}", fg=typer.colors.RED)
            raise typer.Exit(1)
        marker_out = md_files[0].parent

    # 2. Restructure (só se book)
    if is_book:
        typer.secho("\n[2/5] restruct...", bold=True)
        restruct(out, pdf=pdf, marker_out=marker_out)  # type: ignore
    else:
        typer.echo("\n[2/5] restruct ⏭ (paper layout)")
        # Move marker output direto para out/
        for f in marker_out.rglob("*"):
            if f.is_file():
                tgt = out / f.relative_to(marker_out)
                tgt.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, tgt)

    # 3. Optimize
    if not no_optimize and not quick:
        typer.secho("\n[3/5] optimize (imagens)...", bold=True)
        optimize(out, dry_run=False)  # type: ignore
    else:
        typer.echo("\n[3/5] optimize ⏭")

    # 4. Stats
    if not no_stats:
        typer.secho("\n[4/5] stats...", bold=True)
        stats(out, source_pdf=pdf, roundtrip_md1=None, roundtrip_md2=None)  # type: ignore
    else:
        typer.echo("\n[4/5] stats ⏭")

    # 5. Provenance
    if not no_provenance:
        typer.secho("\n[5/5] provenance...", bold=True)
        prov(
            out,
            pkg_version=None,
            source=pdf.name,
            sha256=str(pdf),  # calcula automaticamente via prov()
            extractor="marker-pdf 1.10.2",
            when=None,
        )
    else:
        typer.echo("\n[5/5] provenance ⏭")

    # Best mode: multi-roundtrip extra
    if best:
        typer.secho("\n[+] rt-multi (best mode, 3 iter)...", bold=True)
        # Roda no primeiro MD encontrado (chapter 1 ou paper único)
        first_md = next(out.rglob("*.md"), None)
        if first_md:
            work = out / "_roundtrip_work"
            rt_multi(first_md, work_dir=work, iterations=3)  # type: ignore

    # rt-pixel: validador visual L0.5 (T070, v0.6.0). Opt-in via --rt-pixel ou --best.
    if rt_pixel or best:
        typer.secho("\n[+] rt-pixel (validador visual L0.5)...", bold=True)
        _run_rt_pixel_on_out(pdf, out, skip_ssim=rt_pixel_skip_ssim or quick)

    typer.secho(f"\n✓ Pronto. Saída em {out}", bold=True, fg=typer.colors.GREEN)


def _run_rt_pixel_on_out(pdf_orig: Path, out: Path, *, skip_ssim: bool = False) -> None:
    """Gera PDF render do MD canônico e roda pixel_roundtrip vs PDF original.

    Para layouts book/paper, usa o primeiro MD (paper) ou TODOS (book) e gera
    `_pixel_roundtrip.json` na raiz com agregados por capítulo.
    """
    from pdf2md.pixel_roundtrip import run_pixel_roundtrip
    from pdf2md.pdfs import md_to_pdf
    import tempfile

    # Acha MDs principais (igual ao pdfs.find_chapter_mds, mas tolera paper layout)
    md_targets = []
    for chap_dir in sorted(out.iterdir()):
        if not chap_dir.is_dir():
            continue
        md = chap_dir / f"{chap_dir.name}.md"
        if md.exists():
            md_targets.append(md)
    # Paper layout: MD direto na raiz
    if not md_targets:
        md_targets = [m for m in out.glob("*.md") if not m.name.startswith("_")]

    if not md_targets:
        typer.secho("  [SKIP] nenhum MD encontrado para rt-pixel", fg=typer.colors.YELLOW)
        return

    results = []
    for md in md_targets:
        typer.echo(f"  {md.parent.name}/...")
        with tempfile.TemporaryDirectory(prefix="rt_pixel_") as tmp:
            tmp_dir = Path(tmp)
            tmp_md = tmp_dir / "source.md"
            tmp_md.write_text(md.read_text(encoding="utf-8"), encoding="utf-8")
            # Copia images/ se existir (md_to_pdf precisa pra resolve image paths)
            images_src = md.parent / "images"
            if images_src.is_dir():
                tmp_imgs = tmp_dir / "images"
                tmp_imgs.mkdir()
                for img in images_src.iterdir():
                    if img.is_file():
                        shutil.copy2(img, tmp_imgs / img.name)
            pdf_render = tmp_dir / "render.pdf"
            md_to_pdf(tmp_md, out_pdf=pdf_render, overwrite=True)
            result = run_pixel_roundtrip(pdf_orig, pdf_render, skip_ssim=skip_ssim)

        agg = result.agg
        typer.echo(f"    WER med={agg['wer_median']:.3f} %<0.60={agg['pct_wer_tol']:.1%}"
                   + (f" SSIM={agg.get('ssim_median', 0):.3f}" if not skip_ssim else ""))
        results.append({
            "chapter": md.parent.name,
            "md": str(md.relative_to(out)),
            "n_orig_pages": result.n_orig_pages,
            "n_render_pages": result.n_render_pages,
            "monotonic": result.monotonic,
            "agg": agg,
        })

    # Salva agregado consolidado
    import json
    rt_pixel_path = out / "_pixel_roundtrip.json"
    rt_pixel_path.write_text(
        json.dumps({"pdf_orig": str(pdf_orig), "chapters": results}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    typer.echo(f"  [OK] {rt_pixel_path}")


# ---------------------------------------------------------------------------
# Help longo
# ---------------------------------------------------------------------------

@app.command("help")
def help_cmd(
    subcommand: str = typer.Argument(None, help="Nome do subcomando (omita para listar todos)"),
):
    """Mostra ajuda detalhada de um subcomando.

    Exemplo: `pdf2md help convert`
    """
    if not subcommand:
        # Mostra help geral
        os.execvp(sys.argv[0], [sys.argv[0], "--help"])
    else:
        os.execvp(sys.argv[0], [sys.argv[0], subcommand, "--help"])


if __name__ == "__main__":
    app()
