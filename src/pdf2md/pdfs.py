"""MD → PDF por capítulo, via pandoc + Chrome headless + KaTeX.

Para cada `<base>/<chapter>/<chapter>.md`, produz `<chapter>.pdf` ao lado.

Pode ser usado como módulo (`from pdf2md.pdfs import md_to_pdf`) ou
script standalone (compat com docs históricos: `python src/gen_pdfs.py DIR`).
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

DEFAULT_PANDOC = os.environ.get("PDF2MD_PANDOC") or "pandoc"
DEFAULT_CHROME = os.environ.get("PDF2MD_CHROME") or r"C:/Program Files/Google/Chrome/Application/chrome.exe"

# CSS embutido — print-friendly: KaTeX legível, code blocks, tabelas, page breaks.
CSS_INLINE = """
@page { size: A4; margin: 2cm 2cm 2cm 2cm;
  @bottom-right { content: "p. " counter(page) " / " counter(pages); font-size: 9pt; color: #888; }
}
body { font-family: 'Segoe UI', sans-serif; font-size: 10.5pt; line-height: 1.55; color: #1a1a1a; max-width: none; margin: 0; padding: 0; background: #fafafa; }
h1 { color: #1a3a52; border-bottom: 2px solid #1a3a52; padding-bottom: 0.3em; font-size: 1.6em; }
h2 { color: #2a5a82; border-bottom: 1px solid #5e8bb0; padding-bottom: 0.2em; margin-top: 1.5em; font-size: 1.3em; page-break-after: avoid; }
h3 { color: #3a7aa5; margin-top: 1.4em; font-size: 1.12em; page-break-after: avoid; }
p { margin: 0.55em 0; text-align: left; }
strong { color: #1a3a52; }
code { background: #eef1f4; padding: 1px 5px; border-radius: 3px; font-family: 'Consolas', monospace; font-size: 0.92em; color: #b03050; }
pre { background: #f4f4f4; padding: 0.8em 1em; border-left: 3px solid #2a5a82; border-radius: 3px; font-size: 0.88em; line-height: 1.35; page-break-inside: avoid; }
blockquote { border-left: 3px solid #b8a050; background: #fffbe6; padding: 0.6em 1em; margin: 1em 0; color: #5a4a1a; border-radius: 3px; font-style: italic; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; page-break-inside: avoid; font-size: 0.95em; }
th, td { border: 1px solid #c8d2dc; padding: 0.5em 0.8em; text-align: left; vertical-align: top; }
th { background: #dbe5ef; color: #1a3a52; font-weight: 600; }
tr:nth-child(even) td { background: #f0f4f8; }
.katex-display { background: #ebf2f9; padding: 0.7em 1em; border-radius: 4px; border-left: 3px solid #2a5a82; margin: 0.9em 0 !important; page-break-inside: avoid; overflow-x: auto; }
.katex { font-size: 1em !important; }
img { max-width: 90%; height: auto; display: block; margin: 0.8em auto; border: 1px solid #d0d8e0; border-radius: 4px; background: white; padding: 4px; page-break-inside: avoid; }
hr { border: 0; border-top: 1px solid #c8d2dc; margin: 1.5em 0; }
"""


def md_to_pdf(
    md_path: Path,
    *,
    pandoc: str = DEFAULT_PANDOC,
    chrome: str = DEFAULT_CHROME,
    css: str = CSS_INLINE,
) -> Path:
    """Converte um MD em PDF, salvando ao lado. Retorna path do PDF gerado."""
    md_path = md_path.resolve()
    pdf_path = md_path.with_suffix(".pdf")
    chapter_dir = md_path.parent

    with tempfile.TemporaryDirectory(prefix="md2pdf_") as tmp_dir:
        tmp = Path(tmp_dir)
        css_path = tmp / "style.css"
        css_path.write_text(css, encoding="utf-8")
        html_path = tmp / "out.html"

        subprocess.run([
            pandoc, str(md_path),
            "-o", str(html_path),
            "--standalone", "--embed-resources",
            "--katex",
            "--css", str(css_path),
            "--resource-path", str(chapter_dir),
            "--metadata", f"title={md_path.stem}",
        ], check=True, capture_output=True)

        url = "file:///" + html_path.absolute().as_posix().replace(" ", "%20")
        subprocess.run([
            chrome,
            "--headless", "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path.absolute()}",
            "--virtual-time-budget=20000",
            url,
        ], check=True, capture_output=True)

    if not pdf_path.exists():
        raise RuntimeError(f"Chrome não criou o PDF em {pdf_path}")
    return pdf_path


def find_chapter_mds(base: Path) -> list[Path]:
    """Localiza `<base>/<chapter>/<chapter>.md` (livro restructure-output)."""
    targets: list[Path] = []
    for chapter_dir in sorted(base.iterdir()):
        if not chapter_dir.is_dir():
            continue
        md = chapter_dir / f"{chapter_dir.name}.md"
        if md.exists():
            targets.append(md)
    return targets


def generate_all(base: Path, *, on_progress=None) -> tuple[int, int]:
    """Gera PDF para todos os capítulos. Retorna (sucessos, falhas)."""
    targets = find_chapter_mds(base)
    ok = 0
    fail = 0
    for md in targets:
        try:
            pdf = md_to_pdf(md)
            kb = pdf.stat().st_size / 1024
            if on_progress:
                on_progress(md, pdf, kb, None)
            ok += 1
        except Exception as e:
            if on_progress:
                on_progress(md, None, 0, e)
            fail += 1
    return ok, fail


def _cli() -> int:
    """CLI standalone (compat com `python src/gen_pdfs.py DIR`)."""
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    base = Path(sys.argv[1])
    if not base.is_dir():
        print(f"[ERRO] {base} não é diretório")
        return 1
    targets = find_chapter_mds(base)
    print(f"[INFO] {len(targets)} capítulos para converter")

    def _report(md: Path, pdf: Path | None, kb: float, err: Exception | None) -> None:
        if err:
            print(f"  {md.parent.name}/ ... FALHOU ({type(err).__name__}: {err})")
        else:
            print(f"  {md.parent.name}/ ... {kb:>6.0f} KB ✓")

    ok, fail = generate_all(base, on_progress=_report)
    print(f"\n[OK] {ok}/{len(targets)} PDFs gerados em {base}/" + (f" — {fail} falhas" if fail else ""))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(_cli())
