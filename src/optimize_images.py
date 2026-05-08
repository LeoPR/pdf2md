"""
Otimização adaptativa de imagens extraídas (T131 — sub-ticket de T130).

Para cada imagem em `<root>/**/images/*.{jpeg,jpg,png}`:
- conta cores únicas
- ≤2 cores → PNG 1-bit (B&W puro, line art)
- ≤16 cores → PNG indexado (paleta)
- >16 cores → mantém JPEG original (continuous tone; re-encode só piora)

Para cada formato candidato (PNG vs JPEG original), escolhe o **menor**.
Se decidiu mudar formato, atualiza referências `.jpeg` → `.png` nos MDs
relevantes do mesmo capítulo.

Output:
- Imagens otimizadas in-place (originais substituídas)
- `_image_optimization.md` no `<root>/` com tabela antes/depois
- `_image_optimization.json` com dados detalhados

Uso:
  python optimize_images.py <root> [--dry-run] [--out <dir>]

Exemplo:
  python optimize_images.py pesquisa_geral/livros/Quantum_Computation_and_Quantum_Information

Implementa nível 1 e 2 da decisão tree de T130 (PHILOSOPHY.md prioridade 3).
SVG vetorizado (potrace) e fórmula→LaTeX (pix2tex) ficam para tickets
posteriores (T132/T134).
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

# Garantir UTF-8 no stdout
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# ============================================================================
# Classificação
# ============================================================================

def count_colors(img: Image.Image, max_check: int = 17) -> int | None:
    """
    Retorna número de cores únicas, ou None se exceder max_check.
    Usa getcolors() que é eficiente para imagens com paleta limitada.
    """
    rgb = img.convert("RGB")
    colors = rgb.getcolors(maxcolors=max_check)
    return len(colors) if colors is not None else None


def palette_quality(img: Image.Image, n_colors: int) -> float:
    """
    Quantiza para n_colors e mede diferença média de pixel (0-255).
    Mais baixo = melhor preservação visual.
    """
    rgb = img.convert("RGB")
    quant = rgb.quantize(colors=n_colors, method=Image.Quantize.MAXCOVERAGE).convert("RGB")
    diff = ImageChops.difference(rgb, quant)
    stat = ImageStat.Stat(diff)
    return sum(stat.mean) / len(stat.mean)  # média dos canais R/G/B


def classify_image(img: Image.Image, lossy_threshold: float = 5.0) -> tuple[str, int | None]:
    """
    Retorna ('bw' | 'palette' | 'palette_lossy' | 'continuous', n_colors).

    - bw / palette → lossless (poucas cores reais)
    - palette_lossy → quantizar para 16 cores preserva qualidade visual
      (diferença média de pixel < lossy_threshold em escala 0-255)
    - continuous → foto/diagrama complexo, manter JPEG

    O caminho `palette_lossy` é necessário porque JPEGs de diagramas B&W
    sempre acabam com >16 cores únicas (anti-aliasing + ruído JPEG),
    mas re-quantizam perfeitamente.
    """
    n = count_colors(img, max_check=17)
    if n is not None:
        if n <= 2:
            return ("bw", n)
        if n <= 16:
            return ("palette", n)

    # Mais de 16 cores exatas — testar se quantiza bem
    diff = palette_quality(img, n_colors=16)
    if diff < lossy_threshold:
        return ("palette_lossy", 16)
    return ("continuous", None)


# ============================================================================
# Conversão
# ============================================================================

def to_png_bw(img: Image.Image, out_path: Path):
    """PNG 1-bit (modo '1' do PIL)."""
    img.convert("1").save(out_path, format="PNG", optimize=True)


def to_png_palette(img: Image.Image, out_path: Path, n_colors: int):
    """PNG com paleta indexada (modo 'P')."""
    # Quantize com colors <= 16 (PIL precisa potência de 2 às vezes; usamos n_colors)
    n = max(2, min(n_colors, 16))
    palette = img.convert("RGB").quantize(colors=n, method=Image.Quantize.MAXCOVERAGE)
    palette.save(out_path, format="PNG", optimize=True)


# ============================================================================
# Per-image
# ============================================================================

def optimize_one(src: Path, dry_run: bool = False) -> dict:
    """
    Otimiza uma imagem. Retorna dict com decisão e tamanhos.
    Se decidir mudar formato, faz a troca in-place (deleta original).
    """
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
                # Mantém JPEG; nada a fazer no nível 1
                record["decision"] = "keep_jpeg"
                return record

            # Tenta PNG correspondente
            candidate = src.with_suffix(".png")
            if candidate.exists() and candidate.resolve() != src.resolve():
                # Já existe PNG com mesmo nome; só medir e comparar
                pass

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
                # PNG ficou menor — usar
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
                # PNG não ajudou; manter original
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
    """
    Substitui referências de imagem no MD baseado no mapa {old_basename: new_basename}.
    Retorna número de substituições.
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


# ============================================================================
# Main
# ============================================================================

def fmt_bytes(n: int) -> str:
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024
    return f"{n:.1f} TB"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--out", type=Path, default=None,
                   help="Onde escrever o relatório (default: <root>)")
    args = p.parse_args()

    if not args.root.is_dir():
        print(f"[ERRO] {args.root} não é diretório", file=sys.stderr)
        sys.exit(1)

    out_dir = args.out or args.root

    # Coletar imagens (em images/ ou raiz da pasta-doc)
    images = []
    for ext in ("*.jpeg", "*.jpg", "*.png"):
        images += list(args.root.rglob(ext))
    # Filtrar artefatos do próprio script
    images = sorted(set(p for p in images if p.is_file()))

    print(f"[INFO] {len(images)} imagens em {args.root}")
    if args.dry_run:
        print("[INFO] dry-run — nada será modificado")

    records = []
    renames_per_dir: dict[Path, dict[str, str]] = {}

    for i, img_path in enumerate(images, 1):
        rec = optimize_one(img_path, dry_run=args.dry_run)
        records.append(rec)

        if rec["decision"].startswith("convert_to_png"):
            old_name = Path(rec["src"]).name
            new_name = Path(rec["dst"]).name
            d = img_path.parent
            renames_per_dir.setdefault(d, {})[old_name] = new_name

        if i % 20 == 0:
            print(f"  [{i}/{len(images)}]")

    # Atualizar MDs (no diretório-doc, que é parent de images/)
    md_updates = 0
    for img_dir, renames in renames_per_dir.items():
        # MDs candidatos: capítulo é parent de images/
        chapter_dir = img_dir.parent if img_dir.name == "images" else img_dir
        for md in chapter_dir.glob("*.md"):
            if md.name.startswith("_"):
                continue
            n = rewrite_md_refs(md, renames, dry_run=args.dry_run)
            if n:
                md_updates += n
                print(f"  [MD] {md.name}: {n} refs atualizadas")

    # Relatório
    n_total = len(records)
    n_changed = sum(1 for r in records if r["decision"].startswith("convert_to_png"))
    n_kept = n_total - n_changed
    bytes_before = sum(r["src_bytes"] for r in records)
    bytes_after = sum(r["dst_bytes"] for r in records)
    saved = bytes_before - bytes_after

    by_kind = Counter(r["kind"] for r in records)
    by_decision = Counter(r["decision"].split(":")[0] for r in records)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(args.root),
        "dry_run": args.dry_run,
        "total_images": n_total,
        "changed": n_changed,
        "kept": n_kept,
        "bytes_before": bytes_before,
        "bytes_after": bytes_after,
        "bytes_saved": saved,
        "savings_pct": (saved / bytes_before * 100) if bytes_before else 0,
        "by_kind": dict(by_kind),
        "by_decision": dict(by_decision),
        "md_refs_updated": md_updates,
        "records": records,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "_image_optimization.json"
    md_path = out_dir / "_image_optimization.md"

    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    # Render MD
    lines = [
        f"# Otimização de imagens — `{args.root.name}`",
        "",
        f"*Gerado em: {summary['generated_at']}*",
        f"{'**(dry-run — nada modificado)**' if args.dry_run else ''}",
        "",
        "## Resumo",
        "",
        "| Métrica | Valor |",
        "|---|---:|",
        f"| Imagens analisadas | {n_total} |",
        f"| Convertidas para PNG | {n_changed} |",
        f"| Mantidas (JPEG ou já ótimas) | {n_kept} |",
        f"| Tamanho antes | {fmt_bytes(bytes_before)} |",
        f"| Tamanho depois | {fmt_bytes(bytes_after)} |",
        f"| **Economia** | **{fmt_bytes(saved)}** ({summary['savings_pct']:.1f}%) |",
        f"| Refs atualizadas em MDs | {md_updates} |",
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

    # Top 10 economias individuais
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
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print()
    print(f"[OK] {json_path}")
    print(f"[OK] {md_path}")
    print(f"[RESUMO] {n_changed}/{n_total} convertidas, {fmt_bytes(saved)} economizados ({summary['savings_pct']:.1f}%)")


if __name__ == "__main__":
    main()
