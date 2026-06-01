"""Runner standalone de pix2tex — executado pelo python de um venv EXTERNO (torch).

NÃO importa pdf2md (o venv externo não tem o pacote). Só pix2tex + PIL + stdlib.
O executor (pdf2md.executor) cropa as fórmulas no venv geral e chama:

    <pix2tex_python> _pix2tex_runner.py <crop_dir> <out_json>

Lê todos os PNGs de <crop_dir>, roda LatexOCR e escreve {filename: latex} em
<out_json>. Mantém o torch fora do venv geral (ver feedback_venv_efemero_para_labs).
"""
import json
import sys
from pathlib import Path


def main(argv) -> int:
    if len(argv) != 2:
        print("uso: _pix2tex_runner.py <crop_dir> <out_json>", file=sys.stderr)
        return 2
    crop_dir, out_json = Path(argv[0]), Path(argv[1])
    crops = sorted(crop_dir.glob("*.png"))
    if not crops:
        out_json.write_text("{}", encoding="utf-8")
        return 0
    try:
        from PIL import Image
        from pix2tex.cli import LatexOCR
    except ImportError as e:
        print(f"[ERRO] runtime pix2tex ausente: {e}", file=sys.stderr)
        return 3

    model = LatexOCR()
    out = {}
    for png in crops:
        try:
            out[png.name] = model(Image.open(png))
        except Exception as e:                       # uma fórmula ruim não derruba o lote
            out[png.name] = ""
            print(f"[warn] {png.name}: {e}", file=sys.stderr)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
