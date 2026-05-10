"""
Round-trip test: MD_1 -> PDF -> MD_2, compare semantically.

Mede a fidelidade do toolchain marker (PDF->MD) + pandoc (MD->PDF) + marker (PDF->MD).
Não testa fidelidade ao original; testa estabilidade/consistência das transformações.

Uso:
  python roundtrip_test.py <md_inicial> <work_dir>
"""

import sys
import re
import subprocess
from pathlib import Path
from difflib import SequenceMatcher

PANDOC = "pandoc"
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
MARKER = r"Z:/venvs/marker/Scripts/marker_single.exe"


def normalize_md(text: str) -> str:
    """Normaliza MD para comparação semântica.

    Remove diferenças que não importam para fidelidade de conteúdo:
    - Marcadores de página
    - Whitespace múltiplo
    - Caminhos de imagem (mantém só o filename)
    - Quebras de linha dentro de parágrafos
    """
    # Remove page markers (formato {N} do marker, ou <!-- page N -->)
    text = re.sub(r"\{\d+\}", "", text)
    text = re.sub(r"<!--\s*page\s*\d+\s*-->", "", text, flags=re.IGNORECASE)

    # Normaliza paths de imagem (só basename)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
                  lambda m: f"![{m.group(1)}]({Path(m.group(2)).name})", text)

    # Colapsa whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove leading/trailing
    text = text.strip()
    return text


def extract_tokens(text: str) -> list:
    """Extrai tokens significativos para comparação."""
    text = normalize_md(text)
    # Quebra por whitespace, mantém pontuação
    tokens = re.findall(r"\S+", text)
    return tokens


def md_to_pdf(md_path: Path, pdf_path: Path):
    """Gera PDF a partir do MD via pandoc + chrome.

    Passa --resource-path para o pandoc resolver imagens relativas ao MD,
    e valida que o Chrome efetivamente gerou o PDF (Chrome às vezes
    retorna exit 0 sem criar o arquivo).
    """
    html_path = pdf_path.with_suffix(".html")
    chapter_dir = md_path.parent
    subprocess.run([
        PANDOC, str(md_path),
        "-o", str(html_path),
        "--standalone", "--embed-resources",
        "--katex",
        "--resource-path", str(chapter_dir),
    ], check=True)
    subprocess.run([
        CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path.absolute()}",
        "--virtual-time-budget=30000",
        f"file:///{html_path.absolute().as_posix().replace(' ', '%20')}",
    ], check=True)
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError(
            f"Chrome não criou PDF em {pdf_path} (exit code foi 0 mas "
            f"arquivo {'inexistente' if not pdf_path.exists() else 'vazio'}). "
            f"HTML preservado em {html_path} para inspeção."
        )


def pdf_to_md(pdf_path: Path, output_dir: Path) -> Path:
    """Extrai MD do PDF via marker."""
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        MARKER, str(pdf_path),
        "--output_dir", str(output_dir),
        "--output_format", "markdown",
    ], check=True)
    md_files = list(output_dir.rglob("*.md"))
    if not md_files:
        raise RuntimeError("Marker did not produce any MD")
    return md_files[0]


def compare(md1: Path, md2: Path):
    """Compara dois MDs e reporta similaridade."""
    text1 = md1.read_text(encoding="utf-8")
    text2 = md2.read_text(encoding="utf-8")

    tokens1 = extract_tokens(text1)
    tokens2 = extract_tokens(text2)

    matcher = SequenceMatcher(None, tokens1, tokens2)
    ratio = matcher.ratio()

    print(f"MD_1: {len(tokens1):,} tokens")
    print(f"MD_2: {len(tokens2):,} tokens")
    print(f"Similaridade tokens: {ratio:.2%}")

    # Mostra primeiras divergências
    print("\nPrimeiras divergências:")
    n_diffs = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal" and n_diffs < 5:
            a = " ".join(tokens1[i1:i2][:8])
            b = " ".join(tokens2[j1:j2][:8])
            print(f"  [{tag}] MD_1: {a!r}")
            print(f"           MD_2: {b!r}")
            n_diffs += 1


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    md1 = Path(sys.argv[1])
    work = Path(sys.argv[2])
    work.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Round-trip test: {md1.name}")
    print(f"[INFO] Work dir: {work}")

    pdf_path = work / "roundtrip.pdf"
    md2_dir = work / "md2"

    print("\n[1/3] MD_1 -> PDF...")
    md_to_pdf(md1, pdf_path)
    print(f"  PDF gerado: {pdf_path} ({pdf_path.stat().st_size / 1024:.0f} KB)")

    print("\n[2/3] PDF -> MD_2...")
    md2 = pdf_to_md(pdf_path, md2_dir)
    print(f"  MD_2: {md2}")

    print("\n[3/3] Comparando MD_1 e MD_2...")
    compare(md1, md2)


if __name__ == "__main__":
    main()
