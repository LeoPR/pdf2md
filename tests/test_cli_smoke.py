"""Smoke tests do CLI: subcomandos meta (sem invocar marker/pandoc/Chrome)."""
import subprocess
import sys
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PDF2MD = REPO / ".venv" / "Scripts" / "pdf2md.exe"
if not PDF2MD.exists():
    PDF2MD = "pdf2md"  # fallback: PATH


def _run(args: list[str]) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    # encoding="utf-8" + errors="replace": evita UnicodeDecodeError no Windows
    # (default tenta cp1252 e quebra com caracteres ↔/ç do Rich help).
    return subprocess.run(
        [str(PDF2MD), *args],
        capture_output=True, text=True, timeout=30, env=env,
        encoding="utf-8", errors="replace",
    )


def test_version_runs():
    r = _run(["version"])
    assert r.returncode == 0
    assert "pdf2md" in r.stdout
    assert "commit" in r.stdout


def test_doctor_runs():
    r = _run(["doctor"])
    assert r.returncode == 0
    out = r.stdout
    # 6 checks pelo menos
    for tool in ("marker_single", "pandoc", "chrome", "PyMuPDF", "Pillow"):
        assert tool in out, f"doctor não mostra {tool!r}\n{out}"


def test_help_lists_macro_and_subcommands():
    r = _run(["--help"])
    assert r.returncode == 0
    out = r.stdout
    # Macro
    assert "convert" in out
    # Subcomandos finos
    for cmd in ("extract", "restruct", "optimize", "stats", "rt", "rt-multi",
                "aggr", "prov", "norm", "pdfs"):
        assert cmd in out, f"--help não lista subcomando {cmd!r}"
    # Meta
    for cmd in ("doctor", "version"):
        assert cmd in out


def test_convert_help_describes_presets():
    r = _run(["convert", "--help"])
    assert r.returncode == 0
    out = r.stdout
    for flag in ("--book", "--paper", "--quick", "--best", "--intent"):
        assert flag in out, f"convert --help não menciona {flag}"


# --- T090: roteamento por intent (in-process via exe editável) ---
ARXIV = REPO / "corpus" / "examples" / "arxiv_1706_03762_excerpt.pdf"


def test_route_command_dryrun():
    if not ARXIV.exists():
        return
    r = _run(["route", str(ARXIV), "-i", "rapido"])
    assert r.returncode == 0
    assert "host:" in r.stdout and "rapido" in r.stdout and "pdftotext" in r.stdout


def test_convert_intent_rapido_produces_md(tmp_path):
    if not ARXIV.exists():
        return
    out = tmp_path / "conv_rapido"
    r = _run(["convert", str(ARXIV), "-i", "rapido", "-o", str(out)])
    assert r.returncode == 0, r.stderr
    assert (out / "arxiv_1706_03762_excerpt.md").exists()


def test_convert_intent_excludes_legacy_presets(tmp_path):
    if not ARXIV.exists():
        return
    r = _run(["convert", str(ARXIV), "-i", "rapido", "--quick", "-o", str(tmp_path / "x")])
    assert r.returncode != 0   # --intent é exclusivo com --quick/--best
