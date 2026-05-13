"""Shim de compatibilidade — lógica migrou para `pdf2md.roundtrip` (v0.4).

Preservado para que `python src/roundtrip.py <md> <work>` continue funcionando
como sempre fez nos labs e docs históricos.
"""
import sys
from pathlib import Path

# Adiciona src/ ao path quando script é executado standalone
sys.path.insert(0, str(Path(__file__).parent))
from pdf2md.roundtrip import _cli  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(_cli())
