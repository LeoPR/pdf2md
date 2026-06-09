"""Pixel-roundtrip — validador visual L0.5 do T070.

Compara `PDF_orig ↔ PDF_render` (textual + visual) via:

1. **Alinhamento de páginas** — Hungarian (default) ou DTW sobre WER per-page.
   Necessário porque reflow do reconstrutor pode adicionar/remover páginas
   relativo ao original (lab/e12 → lab/e13).
2. **Macro SSIM** — Structural Similarity em pixels para cada par alinhado.
   Captura layout + tipografia agregados.
3. **Médio WER** — Word Error Rate sobre texto agregado da página, com
   normalização forte (NFC, lowercase, strip markdown escapes).

Validado em `lab/e09_*` … `lab/e13_*` (Nielsen & Chuang cap 4, 45×49 pgs).
Block-a-block (lab/e10, e11) foi descartado: fragmentação incompatível com
reflow torna pareamento local não-confiável.

Uso típico:

    from pdf2md.pixel_roundtrip import run_pixel_roundtrip

    result = run_pixel_roundtrip(pdf_orig, pdf_render)
    print(result.render_text())
    result.save_json(out_dir / "_pixel_roundtrip.json")
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Callable

import fitz
from PIL import Image

# numpy/scipy/scikit-image vivem no extra [rtpixel] — o validador visual é OPCIONAL e não
# deve inflar o core de quem só quer pdf->md. cli importa este módulo lazy (só nos comandos
# rt-pixel), então um base-install funciona; este guard dá erro CLARO se o extra faltar.
try:
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    from skimage.metrics import structural_similarity as _ssim
except ModuleNotFoundError as _e:  # pragma: no cover
    raise ModuleNotFoundError(
        f"pixel-roundtrip (validador visual L0.5) requer o extra [rtpixel]: "
        f"pip install 'pdftomd[rtpixel]' (faltou: {_e.name})"
    ) from _e


DEFAULT_DPI = 150
WER_OK = 0.30   # par "ótimo"
WER_TOL = 0.60  # par "tolerável" (limite acima do qual é problemático)
SSIM_OK = 0.95
SSIM_TOL = 0.50

_MD_ESCAPE_RE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!])")
_WS_RE = re.compile(r"\s+")


# ============================================================================
# Normalização + WER per-página
# ============================================================================

def normalize_text(text: str) -> str:
    """NFC unicode + lowercase + strip MD escapes + collapse whitespace.

    Padrão validado em lab/e11 — desambigua diferenças tipográficas residuais
    entre PDF source (Times serif) e PDF render (Segoe sans, KaTeX).
    """
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    text = _MD_ESCAPE_RE.sub(r"\1", text)
    text = _WS_RE.sub(" ", text).strip()
    return text


def page_wer(text_a: str, text_b: str) -> float:
    """Word Error Rate aproximado via SequenceMatcher.ratio.

    Range 0.0 (idêntico) .. 1.0 (completamente diferente).
    """
    a = normalize_text(text_a).split()
    b = normalize_text(text_b).split()
    if not a and not b:
        return 0.0
    if not a or not b:
        return 1.0
    return 1.0 - difflib.SequenceMatcher(None, a, b).ratio()


# ============================================================================
# Render PDF → numpy grayscale
# ============================================================================

def render_pages_to_arrays(pdf_path: Path, dpi: int = DEFAULT_DPI) -> list[np.ndarray]:
    """Renderiza cada página em array grayscale uint8 (H, W). Não toca disco."""
    doc = fitz.open(pdf_path)
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    arrays: list[np.ndarray] = []
    for page in doc:
        pix = page.get_pixmap(matrix=mat, alpha=False)
        # PyMuPDF Pixmap → PIL → numpy grayscale
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).convert("L")
        arrays.append(np.array(img))
    doc.close()
    return arrays


def page_ssim(arr_a: np.ndarray, arr_b: np.ndarray) -> float:
    """SSIM macro global entre duas imagens grayscale.

    Resize automático para shape de `arr_a` se diferirem (PDFs com page size
    distinto, raro mas possível). Range [0, 1] tipicamente; pode ser negativo.
    """
    if arr_a.shape != arr_b.shape:
        b_img = Image.fromarray(arr_b).resize((arr_a.shape[1], arr_a.shape[0]))
        arr_b = np.array(b_img)
    return float(_ssim(arr_a, arr_b, data_range=255))


# ============================================================================
# Alinhamento de páginas
# ============================================================================

def _wer_matrix(texts_a: list[str], texts_b: list[str]) -> np.ndarray:
    """N×M matriz de WER entre todos pares (a, b)."""
    n, m = len(texts_a), len(texts_b)
    cost = np.ones((n, m))
    for i in range(n):
        for j in range(m):
            cost[i, j] = page_wer(texts_a[i], texts_b[j])
    return cost


def align_hungarian(texts_a: list[str], texts_b: list[str]) -> list[tuple[int, int]]:
    """Hungarian assignment 1-para-1 minimizando soma WER.

    Quando m > n (render tem páginas extras), pares com dummies são filtrados —
    retorna n pares válidos. Não-monotônico em geral (faz trocas globais para
    minimizar custo total).
    """
    n, m = len(texts_a), len(texts_b)
    if n == 0 or m == 0:
        return []
    # Padding com dummies (WER=1.0) quando m > n
    cost = np.ones((n, max(m, n)))
    for i in range(n):
        for j in range(m):
            cost[i, j] = page_wer(texts_a[i], texts_b[j])

    row_idx, col_idx = linear_sum_assignment(cost)
    pairs = []
    for ri, ci in zip(row_idx, col_idx):
        if ci < m:
            pairs.append((int(ri), int(ci)))
    return pairs


def align_dtw(texts_a: list[str], texts_b: list[str]) -> list[tuple[int, int]]:
    """DTW sobre WER per-page. Monotônico por construção; permite many-to-one.

    Útil quando reflow espalha 1 pg orig em várias render (1→2).
    """
    n, m = len(texts_a), len(texts_b)
    if n == 0 or m == 0:
        return []
    local = _wer_matrix(texts_a, texts_b)

    dp = np.full((n + 1, m + 1), np.inf)
    dp[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i, j] = local[i - 1, j - 1] + min(
                dp[i - 1, j - 1], dp[i - 1, j], dp[i, j - 1]
            )

    # Backtrack
    path: list[tuple[int, int]] = []
    i, j = n, m
    while i > 0 and j > 0:
        path.append((i - 1, j - 1))
        diag, up, left = dp[i - 1, j - 1], dp[i - 1, j], dp[i, j - 1]
        m_val = min(diag, up, left)
        if diag == m_val:
            i, j = i - 1, j - 1
        elif up == m_val:
            i -= 1
        else:
            j -= 1
    path.reverse()
    return path


def is_monotonic(pairs: list[tuple[int, int]]) -> bool:
    """Path é monotônico (sem inversões em b) quando reflow é "estender", não embaralhar."""
    for k in range(len(pairs) - 1):
        if pairs[k][1] > pairs[k + 1][1]:
            return False
    return True


# ============================================================================
# Resultado estruturado
# ============================================================================

@dataclass
class PageMetrics:
    orig_page: int
    render_page: int
    wer: float
    ssim_macro: float | None = None
    flags: list[str] = field(default_factory=list)


@dataclass
class PixelRoundtripResult:
    pdf_orig: str
    pdf_render: str
    n_orig_pages: int
    n_render_pages: int
    alignment: str  # "hungarian" | "dtw"
    monotonic: bool
    dpi: int
    pages: list[PageMetrics]
    agg: dict
    skipped_ssim: bool = False

    def render_text(self) -> str:
        lines = [
            f"# Pixel-roundtrip",
            "",
            f"- orig: `{self.pdf_orig}` ({self.n_orig_pages} pgs)",
            f"- render: `{self.pdf_render}` ({self.n_render_pages} pgs)",
            f"- alignment: **{self.alignment}** (monotonic={self.monotonic})",
            f"- dpi: {self.dpi}{' (SSIM skipped)' if self.skipped_ssim else ''}",
            "",
            "## Agregados",
            "",
            f"| Métrica | Valor |",
            f"|---|---|",
            f"| Pares alinhados | {self.agg.get('n_pairs', 0)} |",
            f"| WER mediana | {self.agg.get('wer_median', 0):.3f} |",
            f"| WER média | {self.agg.get('wer_mean', 0):.3f} |",
            f"| % pares WER < {WER_OK} (ótimo) | {self.agg.get('pct_wer_ok', 0):.1%} |",
            f"| % pares WER < {WER_TOL} (tolerável) | {self.agg.get('pct_wer_tol', 0):.1%} |",
        ]
        if not self.skipped_ssim:
            lines += [
                f"| SSIM mediana | {self.agg.get('ssim_median', 0):.3f} |",
                f"| SSIM média | {self.agg.get('ssim_mean', 0):.3f} |",
                f"| % pares SSIM > {SSIM_OK} | {self.agg.get('pct_ssim_ok', 0):.1%} |",
            ]
        lines += [
            "",
            "## Páginas problemáticas",
            "",
        ]
        problematic = [p for p in self.pages if p.flags]
        if problematic:
            lines += ["| orig | render | WER | SSIM | flags |", "|---:|---:|---:|---:|---|"]
            for p in problematic[:20]:  # top 20
                ssim_str = f"{p.ssim_macro:.3f}" if p.ssim_macro is not None else "—"
                lines.append(f"| {p.orig_page} | {p.render_page} | {p.wer:.3f} | {ssim_str} | {', '.join(p.flags)} |")
            if len(problematic) > 20:
                lines.append(f"| ... | ... | ... | ... | (+{len(problematic) - 20} mais) |")
        else:
            lines.append("(nenhuma)")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "pdf_orig": self.pdf_orig,
            "pdf_render": self.pdf_render,
            "n_orig_pages": self.n_orig_pages,
            "n_render_pages": self.n_render_pages,
            "alignment": self.alignment,
            "monotonic": self.monotonic,
            "dpi": self.dpi,
            "skipped_ssim": self.skipped_ssim,
            "agg": self.agg,
            "pages": [asdict(p) for p in self.pages],
        }

    def save_json(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path


# ============================================================================
# Pipeline principal
# ============================================================================

def _flag_page(wer: float, ssim_val: float | None) -> list[str]:
    flags = []
    if wer >= WER_TOL:
        flags.append("high_wer")
    elif wer >= WER_OK:
        flags.append("medium_wer")
    if ssim_val is not None:
        if ssim_val < SSIM_TOL:
            flags.append("low_ssim")
        elif ssim_val < SSIM_OK:
            flags.append("medium_ssim")
    return flags


def run_pixel_roundtrip(
    pdf_orig: Path,
    pdf_render: Path,
    *,
    align_method: str = "hungarian",
    dpi: int = DEFAULT_DPI,
    skip_ssim: bool = False,
    on_progress: Callable[[int, int], None] | None = None,
) -> PixelRoundtripResult:
    """Pipeline completo do pixel-roundtrip.

    Args:
        pdf_orig: PDF source (livro original, paper, etc.).
        pdf_render: PDF reconstruído via `pdf2md.pdfs.md_to_pdf` (ou outro).
        align_method: `"hungarian"` (default — melhor mediana WER) ou `"dtw"`
            (monotônico, many-to-one para reflow).
        dpi: resolução do render para SSIM (default 150).
        skip_ssim: pula cálculo de SSIM (preset "rápido" — texto-only é
            ~7× mais rápido).
        on_progress: callback `(current, total)` chamado por página
            durante o SSIM.

    Returns:
        `PixelRoundtripResult` com per-page + agregados + flags.
    """
    pdf_orig = Path(pdf_orig).resolve()
    pdf_render = Path(pdf_render).resolve()

    # 1. Texto por página
    doc_a = fitz.open(pdf_orig)
    doc_b = fitz.open(pdf_render)
    n_a, n_b = len(doc_a), len(doc_b)
    texts_a = [doc_a[i].get_text() for i in range(n_a)]
    texts_b = [doc_b[i].get_text() for i in range(n_b)]
    doc_a.close()
    doc_b.close()

    # 2. Alinhamento
    if align_method == "hungarian":
        pairs = align_hungarian(texts_a, texts_b)
    elif align_method == "dtw":
        pairs = align_dtw(texts_a, texts_b)
    else:
        raise ValueError(f"align_method deve ser 'hungarian' ou 'dtw', recebeu {align_method!r}")
    monotonic = is_monotonic(pairs)

    # 3. SSIM (opcional, mais caro)
    ssim_by_pair: dict[tuple[int, int], float] = {}
    if not skip_ssim and pairs:
        imgs_a = render_pages_to_arrays(pdf_orig, dpi=dpi)
        imgs_b = render_pages_to_arrays(pdf_render, dpi=dpi)
        for k, (i, j) in enumerate(pairs):
            ssim_by_pair[(i, j)] = page_ssim(imgs_a[i], imgs_b[j])
            if on_progress:
                on_progress(k + 1, len(pairs))

    # 4. Per-page + agregados
    pages: list[PageMetrics] = []
    for i, j in pairs:
        w = page_wer(texts_a[i], texts_b[j])
        s = ssim_by_pair.get((i, j))
        pages.append(PageMetrics(orig_page=i, render_page=j, wer=w, ssim_macro=s,
                                  flags=_flag_page(w, s)))

    wers = [p.wer for p in pages]
    agg = {
        "n_pairs": len(pages),
        "wer_median": float(np.median(wers)) if wers else 0.0,
        "wer_mean": float(np.mean(wers)) if wers else 0.0,
        "wer_min": float(min(wers)) if wers else 0.0,
        "wer_max": float(max(wers)) if wers else 0.0,
        "pct_wer_ok": sum(1 for w in wers if w < WER_OK) / len(wers) if wers else 0.0,
        "pct_wer_tol": sum(1 for w in wers if w < WER_TOL) / len(wers) if wers else 0.0,
    }
    if not skip_ssim:
        ssims = [p.ssim_macro for p in pages if p.ssim_macro is not None]
        agg.update({
            "ssim_median": float(np.median(ssims)) if ssims else 0.0,
            "ssim_mean": float(np.mean(ssims)) if ssims else 0.0,
            "ssim_min": float(min(ssims)) if ssims else 0.0,
            "ssim_max": float(max(ssims)) if ssims else 0.0,
            "pct_ssim_ok": sum(1 for s in ssims if s > SSIM_OK) / len(ssims) if ssims else 0.0,
        })

    return PixelRoundtripResult(
        pdf_orig=str(pdf_orig),
        pdf_render=str(pdf_render),
        n_orig_pages=n_a,
        n_render_pages=n_b,
        alignment=align_method,
        monotonic=monotonic,
        dpi=dpi,
        pages=pages,
        agg=agg,
        skipped_ssim=skip_ssim,
    )
