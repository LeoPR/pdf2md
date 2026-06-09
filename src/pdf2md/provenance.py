"""Marcador de proveniência idempotente para MDs convertidos.

Insere um bloco curto logo após o primeiro heading do arquivo, identificando
versão do conversor, commit, data e fonte. Reaplica sem duplicar: se já existe
um bloco `<!-- pdf2md-provenance v1 ... -->`, substitui em vez de adicionar.

Formato resultante:

    # 4. Quantum circuits

    <!-- pdf2md-provenance v1 version=v0.2 commit=abc1234 date=2026-05-11 -->
    > *Convertido por **pdf2md** `v0.2` (commit `abc1234`) em 2026-05-11 ...*

    {resto do conteúdo}
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

_MARKER_RE = re.compile(
    r"<!--\s*pdf2md-provenance\s+v\d+[^>]*-->\s*\n(?:>\s*[^\n]*\n)+\s*",
    flags=re.MULTILINE,
)

_HEADING_RE = re.compile(r"^(#+\s+[^\n]+)\n", flags=re.MULTILINE)


@dataclass(frozen=True)
class Provenance:
    """Metadados de uma conversão. Todos os campos são opcionais exceto version+date."""
    version: str
    date: str
    commit: str | None = None
    source: str | None = None
    source_sha256: str | None = None
    extractor: str | None = None  # ex.: "marker-pdf 1.10.2"

    def html_comment(self) -> str:
        parts = [f"pdf2md-provenance v1 version={self.version} date={self.date}"]
        if self.commit:
            parts.append(f"commit={self.commit}")
        if self.source:
            parts.append(f"source={self.source}")
        return f"<!-- {' '.join(parts)} -->"

    def human_block(self) -> str:
        bits = [f"Convertido por **pdf2md** `{self.version}`"]
        if self.commit:
            bits.append(f"(commit `{self.commit}`)")
        bits.append(f"em {self.date}")
        if self.source:
            tail = f"fonte: `{self.source}`"
            if self.source_sha256:
                tail += f" (sha256 `{self.source_sha256[:8]}…`"
                if self.extractor:
                    tail += f", {self.extractor}"
                tail += ")"
            elif self.extractor:
                tail += f" — {self.extractor}"
            bits.append(f"— {tail}")
        return f"> *{' '.join(bits)}.*"

    def render(self) -> str:
        return f"{self.html_comment()}\n{self.human_block()}\n"


def detect_current_commit() -> str | None:
    """Retorna git short-sha do repo atual ou None se falhar."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True, timeout=5,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None


def pkg_version() -> str:
    """Versão do pdf2md: metadata do install (dist `pdf2md-tool`) > `__version__`.

    NÃO usa `git describe` do diretório atual — isso vazaria o estado do repo
    onde o usuário roda o comando, não a versão do conversor que gerou o MD.
    """
    try:
        from importlib.metadata import version as _v
        return _v("pdf2md-tool")
    except Exception:
        from pdf2md import __version__
        return __version__


def apply_to_text(text: str, prov: Provenance) -> str:
    """Insere/substitui o bloco de proveniência logo após o primeiro heading.

    Idempotente: bloco existente é substituído pelo novo. Se não houver
    heading, retorna texto inalterado (não inventamos onde colocar).
    """
    block = prov.render()

    if _MARKER_RE.search(text):
        return _MARKER_RE.sub(block + "\n", text, count=1)

    m = _HEADING_RE.search(text)
    if not m:
        # Sem heading explícito (ex.: MD começa com imagem ou prosa): prepend no topo.
        return block + "\n" + text
    head_end = m.end()
    return text[:head_end] + "\n" + block + text[head_end:]


def apply_to_file(path: Path, prov: Provenance) -> bool:
    """Aplica em um arquivo. Retorna True se conteúdo mudou."""
    original = path.read_text(encoding="utf-8")
    updated = apply_to_text(original, prov)
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def apply_to_dir(
    root: Path,
    prov: Provenance,
    *,
    skip_underscore: bool = True,
) -> list[tuple[Path, bool]]:
    """Aplica recursivamente em todos os .md sob `root`.

    `skip_underscore=True` ignora `_stats.md`, `_image_optimization.md`, etc.
    (arquivos de telemetria, não de conteúdo).
    """
    results: list[tuple[Path, bool]] = []
    for md in sorted(root.rglob("*.md")):
        if skip_underscore and md.name.startswith("_"):
            continue
        changed = apply_to_file(md, prov)
        results.append((md, changed))
    return results


def _cli() -> int:
    """Uso: python -m pdf2md.provenance <dir> [--source NAME] [--sha256 HEX] [--extractor 'marker-pdf 1.10.2']."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Diretório com .md a marcar")
    parser.add_argument("--version", default=None, help="Versão do conversor (default: git describe)")
    parser.add_argument("--date", default=None, help="Data YYYY-MM-DD (default: hoje)")
    parser.add_argument("--source", default=None, help="Nome do PDF fonte")
    parser.add_argument("--sha256", default=None, help="SHA-256 do PDF fonte")
    parser.add_argument("--extractor", default=None, help="Ex: 'marker-pdf 1.10.2'")
    args = parser.parse_args()

    version = args.version or pkg_version()

    prov = Provenance(
        version=version,
        date=args.date or date.today().isoformat(),
        commit=detect_current_commit(),
        source=args.source,
        source_sha256=args.sha256,
        extractor=args.extractor,
    )

    results = apply_to_dir(args.path, prov)
    changed = sum(1 for _, c in results if c)
    print(f"[pdf2md.provenance] {len(results)} arquivos visitados, {changed} alterados")
    for md, c in results:
        flag = "M" if c else "."
        print(f"  {flag} {md.relative_to(args.path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
