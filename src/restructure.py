"""Shim de compatibilidade — lógica migrou para `pdf2md.restructure` (v0.4).

Preservado para `python src/restructure.py PDF MARKER TARGET`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pdf2md.restructure import _cli  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(_cli())
