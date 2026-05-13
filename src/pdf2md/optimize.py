"""Otimização adaptativa de imagens (T131): classifica e recomprime.

Para cada imagem em `<root>/**/{*.jpeg,*.jpg,*.png}`:
- conta cores únicas
- <= 2 cores  -> PNG 1-bit (B&W puro, line art)
- <= 16 cores -> PNG indexado (paleta)
- > 16 cores  -> mantém JPEG (continuous tone)

Caminho `palette_lossy` para JPEGs de diagramas B&W (anti-aliasing + ruído
inflam contagem, mas quantizam perfeitamente).

Pode ser usado como módulo (`from pdf2md.optimize import optimize_dir`) ou
script standalone (compat com `python src/optimize_images.py ROOT [--dry-run]`).
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Callable

from PIL import Image, ImageChops, ImageStat


# ============================================================================
# Classificação
# ============================================================================

def count_colors(img: Image.Image, max_check: int = 17) -> int | None:
    """Conta cores únicas até max_check. None se exceder."""
    rgb = img.convert("RGB")
    colors = rgb.getcolors(maxcolors=max_check)
    return len(colors) if colors is not None else None


def palette_quality(img: Image.Image, n_colors: int) -> float:
    """Diferença média de pixel (0-255) após quantizar para n_colors. Menor = melhor."""
    rgb = img.convert("RGB")
    quant = rgb.quantize(colors=n_colors, method=Image.Quantize.MAXCOVERAGE).convert("RGB")
    diff = ImageChops.difference(rgb, quant)
    stat = ImageStat.Stat(diff)
    return sum(stat.mean) / len(stat.mean)


def classify_image(img: Image.Image, lossy_threshold: float = 5.0) -> tuple[str, int | None]:
    """Retorna `('bw' | 'palette' | 'palette_lossy' | 'continuous', n_colors)`.

    `palette_lossy` é necessário porque JPEGs de diagramas B&W sempre acabam
    com >16 cores únicas (anti-aliasing + ruído JPEG), mas re-quantizam bem.
    """
    n = count_colors(img, max_check=17)
    if n is not None:
        if n <= 2:
            return ("bw", n)
        if n <= 16:
            return ("palette", n)

    diff = palette_quality(img, n_colors=16)
    if diff < lossy_threshold:
        return ("palette_lossy", 16)
    return ("continuous", None)


# ============================================================================
# Conversão
# ============================================================================

def to_png_bw(img: Image.Image, out_path: Path) -> None:
    """PNG 1-bit (modo '1' do PIL)."""
    img.convert("1").save(out_path, format="PNG", optimize=True)


def to_png_palette(img: Image.Image, out_path: Path, n_colors: int) -> None:
    """PNG com paleta indexada (modo 'P')."""
    n = max(2, min(n_colors, 16))
    palette = img.convert("RGB").quantize(colors=n, method=Image.Quantize.MAXCOVERAGE)
    palette.save(out_path, format="PNG", optimize=True)


# ============================================================================
# Per-image
# ============================================================================

def optimize_one(src: Path, dry_run: bool = False) -> dict:
    """Otimiza uma imagem. Se trocar formato, faz in-place (deleta original)."""
    record = {
        "src": str(src),
        "src_format": src.suffix.lower().lstrip("."),
        "src_bytes": src.stat().st_size,
        "kind": None,
        "n_colors": None,
        "decision": "keep",
        "dst": str(src),
        "dst_format": src.suffix.lower().lstrip("."),
        "dst_bytes": src.stat().st_size,
        "saved_bytes": 0,
    }

    try:
        with Image.open(src) as img:
            img.load()
            kind, n = classify_image(img)
            record["kind"] = kind
            record["n_colors"] = n

            if kind == "continuous":
                record["decision"] = "keep_jpeg"
                return record

            tmp = src.with_suffix(".png.tmp")
            try:
                if kind == "bw":
                    to_png_bw(img, tmp)
                elif kind == "palette":
                    to_png_palette(img, tmp, n or 16)
                else:  # palette_lossy
                    to_png_palette(img, tmp, 16)
                new_bytes = tmp.stat().st_size
            except Exception as e:
                if tmp.exists():
                    tmp.unlink()
                record["decision"] = f"error: {e}"
                return record

            if new_bytes < record["src_bytes"]:
                record["decision"] = f"convert_to_png_{kind}"
                record["dst_bytes"] = new_bytes
                record["saved_bytes"] = record["src_bytes"] - new_bytes

                if not dry_run:
                    final = src.with_suffix(".png")
                    if final.exists() and final != src:
                        final.unlink()
                    tmp.rename(final)
                    record["dst"] = str(final)
                    record["dst_format"] = "png"
                    if src.suffix.lower() != ".png":
                        src.unlink()
                else:
                    tmp.unlink()
            else:
                tmp.unlink()
                record["decision"] = "keep_jpeg_smaller"

    except Exception as e:
        record["decision"] = f"open_error: {e}"

    return record


# ============================================================================
# MD reference rewrite
# ============================================================================

IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def rewrite_md_refs(md_path: Path, renames: dict[str, str], dry_run: bool = False) -> int:
    """Substitui referências `![alt](path)` no MD baseado em `{old_basename: new_basename}`.

    Retorna número de substituições aplicadas.
    """
    if not renames or not md_path.exists():
        return 0
    text = md_path.read_text(encoding="utf-8")
    n = [0]

    def sub(m: re.Match) -> str:
        alt, path = m.group(1), m.group(2)
        base = Path(path).name
        if base in renames:
            new_path = path.replace(base, renames[base])
            n[0] += 1
            return f"![{alt}]({new_path})"
        return m.group(0)

    new_text = IMG_RE.sub(sub, text)
    if new_text != text and not dry_run:
        md_path.write_text(new_text, encoding="utf-8")
    return n[0]


def fmt_bytes(n: int) -> str:
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024
    return f"{n:.1f} TB"


# ============================================================================
# Render relatório
# ============================================================================

def _render_md(summary: dict, root: Path) -> str:
    by_kind = Counter(summary["by_kind"])
    by_decision = Counter(summary["by_decision"])
    records = summary["records"]

    lines = [
        f"# Otimização de imagens — `{root.name}`",
        "",
        f"*Gerado em: {summary['generated_at']}*",
        f"{'**(dry-run — nada modificado)**' if summary['dry_run'] else ''}",
        "",
        "## Resumo",
        "",
        "| Métrica | Valor |",
        "|---|---:|",
        f"| Imagens analisadas | {summary['total_images']} |",
        f"| Convertidas para PNG | {summary['changed']} |",
        f"| Mantidas (JPEG ou já ótimas) | {summary['kept']} |",
        f"| Tamanho antes | {fmt_bytes(summary['bytes_before'])} |",
        f"| Tamanho depois | {fmt_bytes(summary['bytes_after'])} |",
        f"| **Economia** | **{fmt_bytes(summary['bytes_saved'])}** ({summary['savings_pct']:.1f}%) |",
        f"| Refs atualizadas em MDs | {summary['md_refs_updated']} |",
        "",
        "## Distribuição por tipo de conteúdo",
        "",
        "| Tipo | Imagens |",
        "|---|---:|",
    ]
    for kind, n in by_kind.most_common():
        lines.append(f"| `{kind}` | {n} |")
    lines += ["", "## Decisão final", "", "| Decisão | Imagens |", "|---|---:|"]
    for dec, n in by_decision.most_common():
        lines.append(f"| `{dec}` | {n} |")

    top = sorted(
        (r for r in records if r["saved_bytes"] > 0),
        key=lambda r: -r["saved_bytes"],
    )[:10]
    if top:
        lines += [
            "",
            "## Top 10 economias individuais",
            "",
            "| Imagem | Antes | Depois | Economia | Tipo |",
            "|---|---:|---:|---:|---|",
        ]
        for r in top:
            short = Path(r["src"]).name
            saved_pct = r["saved_bytes"] / r["src_bytes"] * 100
            lines.append(
                f"| `{short}` | {fmt_bytes(r['src_bytes'])} | "
                f"{fmt_bytes(r['dst_bytes'])} | "
                f"{fmt_bytes(r['saved_bytes'])} ({saved_pct:.0f}%) | "
                f"`{r['kind']}` |"
            )

    lines.append("")
    return "\n".join(lines)


# ============================================================================
# API top-level
# ============================================================================

ProgressCb = Callable[[int, int, dict], None]  # (i, total, record) -> None


def optimize_dir(
    root: Path,
    dry_run: bool = False,
    out_dir: Path | None = None,
    on_progress: ProgressCb | None = None,
) -> tuple[Path, Path, dict]:
    """Pipeline: descobre imagens, otimiza, reescreve MDs, salva relatórios.

    Args:
        root: raiz com `**/{*.jpeg,*.jpg,*.png}` (book ou paper layout).
        dry_run: se True, não modifica nada (só relata).
        out_dir: onde gravar relatórios (default: `root`).
        on_progress: callback `(i, total, record)` chamado por imagem.

    Retorna `(json_path, md_path, summary_dict)`.
    """
    out_dir = out_dir or root
    out_dir.mkdir(parents=True, exist_ok=True)

    images: list[Path] = []
    for ext in ("*.jpeg", "*.jpg", "*.png"):
        images += list(root.rglob(ext))
    images = sorted(set(p for p in images if p.is_file()))

    records: list[dict] = []
    renames_per_dir: dict[Path, dict[str, str]] = {}

    for i, img_path in enumerate(images, 1):
        rec = optimize_one(img_path, dry_run=dry_run)
        records.append(rec)
        if rec["decision"].startswith("convert_to_png"):
            old_name = Path(rec["src"]).name
            new_name = Path(rec["dst"]).name
            d = img_path.parent
            renames_per_dir.setdefault(d, {})[old_name] = new_name
        if on_progress:
            on_progress(i, len(images), rec)

    md_updates = 0
    for img_dir, renames in renames_per_dir.items():
        chapter_dir = img_dir.parent if img_dir.name == "images" else img_dir
        for md in chapter_dir.glob("*.md"):
            if md.name.startswith("_"):
                continue
            md_updates += rewrite_md_refs(md, renames, dry_run=dry_run)

    n_total = len(records)
    n_changed = sum(1 for r in records if r["decision"].startswith("convert_to_png"))
    n_kept = n_total - n_changed
    bytes_before = sum(r["src_bytes"] for r in records)
    bytes_after = sum(r["dst_bytes"] for r in records)
    saved = bytes_before - bytes_after

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "dry_run": dry_run,
        "total_images": n_total,
        "changed": n_changed,
        "kept": n_kept,
        "bytes_before": bytes_before,
        "bytes_after": bytes_after,
        "bytes_saved": saved,
        "savings_pct": (saved / bytes_before * 100) if bytes_before else 0,
        "by_kind": dict(Counter(r["kind"] for r in records)),
        "by_decision": dict(Counter(r["decision"].split(":")[0] for r in records)),
        "md_refs_updated": md_updates,
        "records": records,
    }

    json_path = out_dir / "_image_optimization.json"
    md_path = out_dir / "_image_optimization.md"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_render_md(summary, root), encoding="utf-8")
    return json_path, md_path, summary


# ============================================================================
# CLI standalone
# ============================================================================

def _cli() -> int:
    """CLI standalone (compat com `python src/optimize_images.py ROOT [--dry-run]`)."""
    import argparse
    p = argparse.ArgumentParser(description="Otimização adaptativa de imagens")
    p.add_argument("root", type=Path)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--out", type=Path, default=None,
                   help="Onde escrever o relatório (default: <root>)")
    args = p.parse_args()

    if not args.root.is_dir():
        print(f"[ERRO] {args.root} não é diretório", file=sys.stderr)
        return 1

    def _progress(i: int, total: int, rec: dict) -> None:
        if i % 20 == 0:
            print(f"  [{i}/{total}]")

    images_seen = 0

    def _count_progress(i, total, rec):
        nonlocal images_seen
        images_seen = total
        _progress(i, total, rec)

    json_path, md_path, summary = optimize_dir(
        args.root, dry_run=args.dry_run, out_dir=args.out, on_progress=_count_progress,
    )

    print(f"[INFO] {images_seen} imagens em {args.root}")
    if args.dry_run:
        print("[INFO] dry-run — nada foi modificado")
    if summary["md_refs_updated"]:
        print(f"  [MD] {summary['md_refs_updated']} refs atualizadas")
    print()
    print(f"[OK] {json_path}")
    print(f"[OK] {md_path}")
    print(
        f"[RESUMO] {summary['changed']}/{summary['total_images']} convertidas, "
        f"{fmt_bytes(summary['bytes_saved'])} economizados ({summary['savings_pct']:.1f}%)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
