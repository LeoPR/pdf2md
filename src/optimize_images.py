"""Shim de compatibilidade — lógica migrou para `pdf2md.optimize` (v0.4).

Preservado para `python src/optimize_images.py ROOT [--dry-run]`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pdf2md.optimize import _cli  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(_cli())
