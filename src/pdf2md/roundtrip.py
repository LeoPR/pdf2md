"""Round-trip test: MD₁ → PDF → MD₂, comparado por tokens.

Mede a fidelidade do toolchain `marker` (PDF→MD) + `pandoc` (MD→HTML+KaTeX) +
Chrome headless (HTML→PDF) + marker novamente (PDF→MD).

Não testa fidelidade ao **original**; testa estabilidade/consistência das
transformações. Bate ~95% em PDFs LaTeX nativos como N&C cap. 4.

Pode ser usado tanto como módulo (`from pdf2md.roundtrip import run_roundtrip`)
quanto como script standalone (compat com docs históricos).
"""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from pdf2md.normalize import normalize_md

# Defaults configuráveis via env vars (mesmo padrão do cli.py)
DEFAULT_PANDOC = os.environ.get("PDF2MD_PANDOC") or "pandoc"
DEFAULT_CHROME = os.environ.get("PDF2MD_CHROME") or r"C:/Program Files/Google/Chrome/Application/chrome.exe"
DEFAULT_MARKER = os.environ.get("PDF2MD_MARKER") or r"Z:/venvs/marker/Scripts/marker_single.exe"


@dataclass(frozen=True)
class RoundtripResult:
    """Resultado de um round-trip único."""
    tokens_md1: int
    tokens_md2: int
    similarity: float  # ratio em [0, 1]
    divergences: list[tuple[str, str, str]]  # (tag, md1_sample, md2_sample) — top N

    def render_text(self) -> str:
        """Formato human-readable (compat com saída histórica do script)."""
        lines = [
            f"MD_1: {self.tokens_md1:,} tokens",
            f"MD_2: {self.tokens_md2:,} tokens",
            f"Similaridade tokens: {self.similarity:.2%}",
            "",
            "Primeiras divergências:",
        ]
        for tag, a, b in self.divergences:
            lines.append(f"  [{tag}] MD_1: {a!r}")
            lines.append(f"           MD_2: {b!r}")
        return "\n".join(lines)


def extract_tokens(text: str) -> list[str]:
    """Tokens significativos do MD para SequenceMatcher (após normalize_md)."""
    text = normalize_md(text)
    return re.findall(r"\S+", text)


def md_to_pdf(
    md_path: Path,
    pdf_path: Path,
    *,
    pandoc: str = DEFAULT_PANDOC,
    chrome: str = DEFAULT_CHROME,
) -> None:
    """Gera PDF a partir do MD via pandoc + Chrome headless.

    Passa `--resource-path` para o pandoc resolver imagens relativas ao MD,
    e valida que o Chrome efetivamente criou o PDF (Chrome às vezes retorna
    exit 0 sem produzir arquivo — bug pego em e02 Atkins).
    """
    html_path = pdf_path.with_suffix(".html")
    chapter_dir = md_path.parent
    subprocess.run([
        pandoc, str(md_path),
        "-o", str(html_path),
        "--standalone", "--embed-resources",
        "--katex",
        "--resource-path", str(chapter_dir),
    ], check=True)
    subprocess.run([
        chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path.absolute()}",
        "--virtual-time-budget=30000",
        f"file:///{html_path.absolute().as_posix().replace(' ', '%20')}",
    ], check=True)
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        state = "inexistente" if not pdf_path.exists() else "vazio"
        raise RuntimeError(
            f"Chrome não criou PDF em {pdf_path} (exit 0 mas arquivo {state}). "
            f"HTML preservado em {html_path} para inspeção."
        )


def pdf_to_md(
    pdf_path: Path,
    output_dir: Path,
    *,
    marker: str = DEFAULT_MARKER,
) -> Path:
    """Extrai MD do PDF via marker_single. Retorna path do primeiro .md achado."""
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        marker, str(pdf_path),
        "--output_dir", str(output_dir),
        "--output_format", "markdown",
    ], check=True)
    md_files = list(output_dir.rglob("*.md"))
    if not md_files:
        raise RuntimeError(f"Marker não produziu MD em {output_dir}")
    return md_files[0]


def compare(md1: Path, md2: Path, *, max_divergences: int = 5) -> RoundtripResult:
    """Compara dois MDs e retorna métricas + amostras de divergência."""
    text1 = md1.read_text(encoding="utf-8")
    text2 = md2.read_text(encoding="utf-8")
    tokens1 = extract_tokens(text1)
    tokens2 = extract_tokens(text2)

    matcher = SequenceMatcher(None, tokens1, tokens2)
    ratio = matcher.ratio()

    divergences: list[tuple[str, str, str]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal" and len(divergences) < max_divergences:
            a = " ".join(tokens1[i1:i2][:8])
            b = " ".join(tokens2[j1:j2][:8])
            divergences.append((tag, a, b))

    return RoundtripResult(
        tokens_md1=len(tokens1),
        tokens_md2=len(tokens2),
        similarity=ratio,
        divergences=divergences,
    )


def run_roundtrip(
    md_path: Path,
    work_dir: Path,
    *,
    pandoc: str = DEFAULT_PANDOC,
    chrome: str = DEFAULT_CHROME,
    marker: str = DEFAULT_MARKER,
) -> RoundtripResult:
    """Pipeline completo: MD → PDF → MD' e compara.

    Args:
        md_path: MD inicial.
        work_dir: diretório onde caem PDF e MD₂ intermediários.
        pandoc, chrome, marker: paths das ferramentas (defaults via env var).

    Returns:
        RoundtripResult com tokens + similaridade + amostras de divergência.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = work_dir / "roundtrip.pdf"
    md2_dir = work_dir / "md2"

    md_to_pdf(md_path, pdf_path, pandoc=pandoc, chrome=chrome)
    md2_path = pdf_to_md(pdf_path, md2_dir, marker=marker)
    return compare(md_path, md2_path)


def _cli() -> int:
    """CLI standalone (compat com `python src/roundtrip.py md work`)."""
    import sys
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    md1 = Path(sys.argv[1])
    work = Path(sys.argv[2])
    print(f"[INFO] Round-trip test: {md1.name}")
    print(f"[INFO] Work dir: {work}")
    print("\n[1/3] MD_1 -> PDF...")
    work.mkdir(parents=True, exist_ok=True)
    pdf_path = work / "roundtrip.pdf"
    md_to_pdf(md1, pdf_path)
    print(f"  PDF gerado: {pdf_path} ({pdf_path.stat().st_size / 1024:.0f} KB)")
    print("\n[2/3] PDF -> MD_2...")
    md2 = pdf_to_md(pdf_path, work / "md2")
    print(f"  MD_2: {md2}")
    print("\n[3/3] Comparando MD_1 e MD_2...")
    result = compare(md1, md2)
    print(result.render_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
