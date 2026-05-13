"""Shim de compatibilidade — lógica migrou para `pdf2md.multi_roundtrip` (v0.4).

Preservado para `python src/multi_roundtrip.py <md> <work> -n N`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pdf2md.multi_roundtrip import _cli  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(_cli())
