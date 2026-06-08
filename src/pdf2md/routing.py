"""Roteador macro-intent profile-aware (T090).

`route(intent, host, doc)` é **puro** dado host+doc+profiles — não faz I/O —, o que
o torna trivialmente testável. A detecção de ambiente (`HostInfo.detect`) e a
caracterização do input (`DocInfo.probe`) fazem o I/O e ficam separadas.

Camadas de decisão (ver tickets/research/T090_macro_intent_routing.md):
  1. GUARDA DE SCAN (precede tudo): doc sem text-layer → marker(GPU) / tesseract(CPU) / ERRO.
  2. GATE DE INTENT: escolhe o PRIMARY por intent × host.
  3. REFINERs/OPTIMIZER: add-ons quando o intent paga e o host comporta.
  4. DEGRADAÇÃO HONESTA: registra `.degraded` + `.rationale` (vão pra provenance).

A **disponibilidade** de cada algoritmo (hardware + needs + capacidade de scan +
custo de RAM) é lida do MAPA medido (`pdf2md/_profiles.py`) — o `profiles` é
consultado de fato, não decorativo (T090 decisão #1). A POLÍTICA (qual algo para
qual intent) é a lógica deste módulo.
"""
from __future__ import annotations

import re
import shutil
import socket
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from pdf2md._profiles import OPTIMIZER, PRIMARY, REFINER, load_active_profiles

# Intents macro (mutuamente exclusivos no CLI)
RAPIDO = "rapido"
QUALIDADE = "qualidade"
BALANCEADO = "balanceado"
AUTO = "auto"
INDEXACAO = "indexacao"
LOW_RESOURCE = "low-resource"
INTENTS = (RAPIDO, QUALIDADE, BALANCEADO, AUTO, INDEXACAO, LOW_RESOURCE)

MARKER_VRAM_MIN_MB = 4096       # gate p/ hardware gpu-required (pico medido 3400 + folga)
LOW_RESOURCE_RAM_CEIL_MB = 160  # teto de RAM do pipeline em --low-resource


class RoutingError(Exception):
    """Erro de roteamento (intent inválido, sem caminho viável)."""


class ScanNoOCR(RoutingError):
    """Doc é scan (sem text-layer) e nenhum OCR está disponível (nem marker/GPU nem tesseract)."""


# ---------------------------------------------------------------------------
# Host + Doc
# ---------------------------------------------------------------------------

@dataclass
class HostInfo:
    cpu_cores: int = 1
    ram_gb: float = 0.0
    gpu_vram_mb: int = 0          # 0 = sem GPU detectada
    has_ollama: bool = False
    has_marker: bool = False
    has_tesseract: bool = False
    has_pix2tex: bool = False     # runtime torch externo (cropper é built-in)

    @classmethod
    def detect(cls) -> "HostInfo":
        import os
        try:
            import psutil
            ram_gb = round(psutil.virtual_memory().total / 1e9, 1)
        except Exception:
            ram_gb = 0.0
        return cls(
            cpu_cores=os.cpu_count() or 1,
            ram_gb=ram_gb,
            gpu_vram_mb=_detect_gpu_vram_mb(),
            has_ollama=_detect_ollama(),
            has_marker=_detect_marker(),
            has_tesseract=_detect_tesseract(),
            has_pix2tex=_detect_pix2tex(),
        )

    def marker_available(self) -> bool:
        """Conveniência (CLI/doctor). route() usa a versão profile-driven `_available`."""
        return self.has_marker and self.gpu_vram_mb >= MARKER_VRAM_MIN_MB


@dataclass
class DocInfo:
    n_pages: int = 1
    has_text_layer: bool = True
    math_density: float = 0.0     # regiões equation-like / página (heurística)
    matrix_density: float = 0.0   # regiões matriz/multi-linha / página (formula_cropper)
    has_raster_logos: bool = False

    @classmethod
    def probe(cls, pdf_path: str | Path, sample: int = 5) -> "DocInfo":
        """Caracteriza o PDF por amostragem barata de páginas.

        LIMITE CONHECIDO: `has_text_layer` detecta AUSÊNCIA de text-layer (scan
        verdadeiramente image-only, ~0 chars), não text-layer RUIM. Scans
        archive.org costumam ter um text-layer esparso/garbage (ex. Wilson,
        Atkins) que passa como text_layer=True — então iriam p/ pdftotext (que
        extrai o garbage) em vez do Tesseract. Detectar "text-layer ruim" barato
        e confiável é um refinamento aberto (proxy de garbage-ratio). Hoje o
        caminho de OCR (e20) dispara só p/ scan image-only puro.
        """
        import re
        import fitz
        from pdf2md.formula_cropper import detect_formula_regions
        doc = fitz.open(str(pdf_path))
        text_chars = 0
        math_hits = 0
        matrix_hits = 0
        has_logos = False
        seen = 0
        try:
            n = len(doc)
            if n == 0:
                raise ValueError(f"PDF sem páginas: {pdf_path}")
            idxs = list(range(min(sample, n)))
            if n > sample:
                idxs += [n // 2, n - 1]
            for i in sorted(set(idxs)):
                page = doc[i]
                t = page.get_text()
                text_chars += len(t.strip())
                math_hits += len(re.findall(r"[=∑∫√≤≥≠αβγδλΣΦΨΩ]|\b\d+/\d+\b|\^|\\[a-zA-Z]+", t))
                # matrix_density: regiões display que o cropper marca complexas (matriz/
                # multi-linha). Uma página patológica NÃO pode derrubar a caracterização.
                try:
                    matrix_hits += sum(1 for r in detect_formula_regions(page, i) if r.is_complex)
                except Exception:
                    pass
                for img in page.get_images(full=True):
                    w = img[2] if len(img) > 2 else 0
                    if 0 < w < 200:        # imagem raster pequena = candidata a logo
                        has_logos = True
                seen += 1
        finally:
            doc.close()
        seen = max(seen, 1)
        return cls(
            n_pages=n,
            has_text_layer=(text_chars / seen) > 30,   # >30 chars/pg amostrado = tem text-layer
            math_density=round(math_hits / seen, 2),
            matrix_density=round(matrix_hits / seen, 2),
            has_raster_logos=has_logos,
        )


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

@dataclass
class Step:
    algo: str
    role: str
    reason: str = ""


@dataclass
class Pipeline:
    intent: str
    steps: list[Step] = field(default_factory=list)
    degraded: bool = False
    rationale: list[str] = field(default_factory=list)
    pass2: "Pipeline | None" = None   # só --indexacao

    @property
    def primary(self) -> str | None:
        for s in self.steps:
            if s.role == PRIMARY:
                return s.algo
        return None

    def summary(self) -> str:
        chain = " + ".join(s.algo for s in self.steps) or "(vazio)"
        tag = " [DEGRADADO]" if self.degraded else ""
        return f"{self.intent}{tag}: {chain}"


# ---------------------------------------------------------------------------
# Disponibilidade PROFILE-DRIVEN (lê o mapa medido, não hardcode)
# ---------------------------------------------------------------------------

def _available(algo: str, host: HostInfo, profiles: dict) -> bool:
    """Algo roda neste host? Deriva de profile.hardware + profile.needs."""
    p = profiles.get(algo)
    if p is None:
        return False
    if p["hardware"] == "gpu-required" and host.gpu_vram_mb < MARKER_VRAM_MIN_MB:
        return False
    for need in p.get("needs", []):
        if need == "marker_bin" and not host.has_marker:
            return False
        if need == "tesseract_bin" and not host.has_tesseract:
            return False
        if need == "ollama" and not host.has_ollama:
            return False
        if need == "pix2tex_runtime" and not host.has_pix2tex:
            return False   # cropper é built-in (formula_cropper); falta só o runtime torch
    return True


def _scan_primary(host: HostInfo, profiles: dict) -> str | None:
    """Melhor PRIMARY capaz de OCR de scan, lido de profile.scan. None se nenhum."""
    # ordem de preferência: OCR de alta fidelidade (marker/GPU) → CPU impresso (tesseract)
    for algo in ("marker", "tesseract"):
        p = profiles.get(algo, {})
        if p.get("scan") in ("ocr-gpu", "printed") and _available(algo, host, profiles):
            return algo
    return None


def _ram_budget_mb(algos: list[str], profiles: dict) -> int:
    """Pico de RAM aproximado do pipeline (steps rodam em sequência → max, não soma)."""
    return max((profiles[a].get("ram_mb", 0) for a in algos if a in profiles), default=0)


# ---------------------------------------------------------------------------
# route() — puro
# ---------------------------------------------------------------------------

def route(intent: str, host: HostInfo, doc: DocInfo, profiles: dict | None = None) -> Pipeline:
    if intent not in INTENTS:
        raise RoutingError(f"intent inválido: {intent!r}. Válidos: {INTENTS}")
    profiles = profiles or load_active_profiles()
    pipe = Pipeline(intent=intent)

    # --- 1. GUARDA DE SCAN (precede gates de intent) ---
    if not doc.has_text_layer:
        return _route_scan(intent, host, doc, pipe, profiles)

    # --- 2. GATE DE INTENT: PRIMARY (doc com text-layer) ---
    marker_ok = _available("marker", host, profiles)
    if intent in (RAPIDO, LOW_RESOURCE, INDEXACAO):
        primary = "pdftotext"
        pipe.steps.append(Step("pdftotext", PRIMARY, "text-layer CPU (velocidade)"))
    else:  # QUALIDADE, BALANCEADO, AUTO
        if marker_ok:
            primary = "marker"
            pipe.steps.append(Step("marker", PRIMARY, "qualidade (math nativo, layout)"))
        else:
            primary = "pdftotext"
            cause = ("sem GPU (VRAM<4096)" if host.gpu_vram_mb < MARKER_VRAM_MIN_MB
                     else "marker_single não instalado")
            if intent == QUALIDADE:
                pipe.degraded = True
                pipe.rationale.append(
                    f"--qualidade pediu marker mas indisponível ({cause}); degradando p/ pdftotext "
                    f"(prose). Math display recuperado via cropper CPU + pix2tex se houver runtime "
                    f"(ver refiners); sem layout nativo do marker."
                )
            else:
                pipe.rationale.append(f"marker indisponível ({cause}); adaptando p/ pdftotext (CPU).")
            pipe.steps.append(Step("pdftotext", PRIMARY, "fallback CPU"))

    # --- 3. REFINERs (só qualidade/auto; disponibilidade lida do mapa) ---
    if intent in (QUALIDADE, AUTO):
        _add_refiners(pipe, host, doc, primary, profiles)

    # --- OPTIMIZER (pré-index/rapido/low-resource não otimizam) ---
    if intent in (BALANCEADO, QUALIDADE, AUTO):
        pipe.steps.append(Step("pdf2md-optimize", OPTIMIZER, "otimização de imagens"))
    elif intent == LOW_RESOURCE:
        opt_ram = profiles.get("pdf2md-optimize", {}).get("ram_mb", 0)
        prim_ram = profiles.get(primary, {}).get("ram_mb", 0)
        if prim_ram + opt_ram <= LOW_RESOURCE_RAM_CEIL_MB:
            pipe.steps.append(Step("pdf2md-optimize", OPTIMIZER, "otimização (dentro do teto)"))
        else:
            pipe.rationale.append(
                f"optimize off: {primary} {prim_ram}MB + optimize {opt_ram}MB "
                f"excederia o teto --low-resource de {LOW_RESOURCE_RAM_CEIL_MB}MB."
            )

    # --- 4. INDEXACAO: pass2 enfileirável ---
    if intent == INDEXACAO:
        pipe.pass2 = _indexacao_pass2(host, doc, profiles)
        pipe.rationale.append(
            "pass1 = índice imediato (pdftotext). pass2 (enfileirável) reprocessa docs com "
            "math_density alto ou anomalia de labels-soltos (proxy medível no output pdftotext)."
        )

    return pipe


def _add_refiners(pipe: Pipeline, host: HostInfo, doc: DocInfo, primary: str, profiles: dict) -> None:
    # math: cropper de fórmula é built-in (formula_cropper, CPU); pix2tex precisa só do
    # runtime torch (need 'pix2tex_runtime'). Com marker como PRIMARY o math já é nativo,
    # então pix2tex é redundante; faz diferença real quando PRIMARY=pdftotext (CPU).
    if doc.math_density > 0 and primary != "marker":
        if _available("pix2tex", host, profiles):
            reason = "extrai math display → LaTeX (cropper CPU + pix2tex)"
            if doc.matrix_density > 0:
                reason += " [matriz: baixa confiança ~0.50]"
                pipe.rationale.append(
                    f"matriz/multi-linha presente (matrix_density={doc.matrix_density}): pix2tex "
                    f"em matriz é fraco (e21: ~0.50, trunca/embaralha). marker/GPU recomendado p/ matriz."
                )
            pipe.steps.append(Step("pix2tex", REFINER, reason))
        else:
            pipe.rationale.append(
                "math presente mas runtime pix2tex ausente (set PDF2MD_PIX2TEX_PYTHON) → math fica cru."
            )
    # logo: gemma3 via Ollama
    if doc.has_raster_logos:
        if _available("gemma3-4b-small-image", host, profiles):
            pipe.steps.append(Step("gemma3-4b-small-image", REFINER, "transcreve logos (Ollama)"))
        else:
            pipe.rationale.append("logos presentes mas Ollama indisponível → sem refino de logo.")


def _route_scan(intent: str, host: HostInfo, doc: DocInfo, pipe: Pipeline, profiles: dict) -> Pipeline:
    """Doc sem text-layer. PRIMARY de scan lido do mapa (profile.scan)."""
    primary = _scan_primary(host, profiles)
    if primary is None:
        raise ScanNoOCR(
            "doc é scan (sem text-layer) e nenhum OCR disponível: "
            "marker exige GPU+marker_single; tesseract não encontrado. "
            "BURACO scan-sem-GPU (instalar Tesseract — Lab e20)."
        )
    if primary == "marker":
        pipe.steps.append(Step("marker", PRIMARY, "scan → Surya OCR (GPU)"))
        pipe.rationale.append("scan: marker(Surya/GPU) é o único OCR full-doc de alta fidelidade.")
    else:  # tesseract
        pipe.steps.append(Step("tesseract", PRIMARY, "scan → Tesseract CPU-OCR"))
        pipe.rationale.append(
            "scan sem GPU: Tesseract CPU-OCR (e20: impresso WER 0.052, zero alucinação; "
            "manuscrito falha de forma honesta)."
        )
        if intent == QUALIDADE:
            pipe.degraded = True

    if intent == INDEXACAO:
        # contrato 2-pipelines não se aplica: pdftotext não indexa scan, então pass1
        # já é a passada OCR (cara). Documenta o colapso explicitamente.
        pipe.rationale.append(
            "--indexacao em scan: modelo 2-pass colapsa — pdftotext não indexa scan, "
            "então pass1 já é a passada OCR. Sem pass2 enfileirável."
        )

    # optimize: pré-index/rapido/low-resource não otimizam (consistente com text-layer)
    if intent not in (RAPIDO, LOW_RESOURCE, INDEXACAO):
        pipe.steps.append(Step("pdf2md-optimize", OPTIMIZER, "otimização de imagens"))
    return pipe


def _indexacao_pass2(host: HostInfo, doc: DocInfo, profiles: dict) -> Pipeline | None:
    """pass2 enfileirável: marker (se disponível) p/ docs que valem reprocessar."""
    if not _available("marker", host, profiles):
        return None  # sem marker, sem ganho de math sem cropper
    p2 = Pipeline(intent="indexacao-pass2")
    # marker é PRIMARY no pass2 → math nativo (Texify); pix2tex seria redundante (e
    # conflitaria com o OPTIMIZER ao varrer crops). Consistente com _add_refiners.
    p2.steps.append(Step("marker", PRIMARY, "reprocessa docs math-heavy / baixa qualidade"))
    p2.steps.append(Step("pdf2md-optimize", OPTIMIZER, "otimização"))
    return p2


# ---------------------------------------------------------------------------
# Gatilho de pass2 (--indexacao) — SELETIVO, medido NO OUTPUT do pass1
# ---------------------------------------------------------------------------
# route() anexa o TEMPLATE do pass2 quando o host comporta marker (capacidade do host).
# pass2_warranted() é a outra metade: decide, POR DOC, se vale ENFILEIRAR o reprocessamento
# — medindo o markdown que o pass1 (pdftotext) já produziu, conforme o critério do spec
# (T090, "mensurável no output do pdftotext"). Dois sinais de PERDA recuperável pelo marker:
#   - math denso: pdftotext entrega math como Unicode cru; marker recupera LaTeX (Texify).
#   - densidade de texto anômala (chars/página baixíssima): text-layer esparso/garbage
#     (scan de OCR ruim que passou a guarda) — marker re-OCR/layout recupera estrutura.
# Thresholds calibrados no corpus livre in-repo (N=5): separam com folga ampla (math-arm
# arxiv-math 3.57 vs prosa ≤0.14; density-arm wilson 261 vs sãos ≥3079). HONESTO quanto ao
# escopo: N=5 não generaliza — revisitar num corpus maior (relacionado ao BURACO cross-doc).
PASS2_MATH_PER_KCHAR = 1.0       # ≥ ⇒ math-heavy (folga: arxiv-math 3.57; prosa ≤0.14)
PASS2_DENSITY_FLOOR_CPP = 800    # chars/pág < ⇒ text-layer esparso/garbage (wilson 261; sãos ≥3079)

# math no markdown cru (símbolos + frações + super/subscrito + comandos LaTeX-like).
# Mais amplo que o de DocInfo.probe de propósito: aqui medimos o OUTPUT, não amostra do PDF.
_PASS2_MATH_RE = re.compile(r"[=∑∫√≤≥≠αβγδλμνπσφψωΣΦΨΩ∇∂±×·→]|\b\d+/\d+\b|\^|_\{|\\[a-zA-Z]+")


@dataclass
class Pass2Signal:
    warranted: bool
    math_per_kchar: float
    chars_per_page: float
    reasons: list[str] = field(default_factory=list)

    def summary(self) -> str:
        verdict = "PASS2" if self.warranted else "ok-pass1"
        return (f"{verdict} (math={self.math_per_kchar}/kchar, dens={self.chars_per_page}c/pg)"
                + (f": {'; '.join(self.reasons)}" if self.reasons else ""))


def pass2_warranted(pass1_md: str, n_pages: int) -> Pass2Signal:
    """Decide se um doc indexado pelo pass1 (pdftotext) merece pass2 (marker, enfileirável).

    PURO e medido NO OUTPUT do pass1 (não re-proba o PDF). warranted = math denso OU
    densidade de texto anômala — os dois casos em que o pass1 perde algo que o marker
    recupera. Para o `--indexacao`: pass1 indexa TODOS; só estes vão pra fila do pass2."""
    chars = len(pass1_md)
    n_pages = max(n_pages, 1)
    math = len(_PASS2_MATH_RE.findall(pass1_md))
    math_per_kc = 1000 * math / max(chars, 1)
    cpp = chars / n_pages
    reasons: list[str] = []
    if math_per_kc >= PASS2_MATH_PER_KCHAR:
        reasons.append(
            f"math denso ({math_per_kc:.1f}/kchar ≥ {PASS2_MATH_PER_KCHAR}): "
            f"pdftotext entrega Unicode cru, marker recupera LaTeX"
        )
    if cpp < PASS2_DENSITY_FLOOR_CPP:
        reasons.append(
            f"densidade de texto anômala ({cpp:.0f} chars/pág < {PASS2_DENSITY_FLOOR_CPP}): "
            f"text-layer esparso/garbage, marker re-OCR/layout recupera estrutura"
        )
    return Pass2Signal(warranted=bool(reasons), math_per_kchar=round(math_per_kc, 2),
                       chars_per_page=round(cpp, 1), reasons=reasons)


# ---------------------------------------------------------------------------
# detecção (I/O) — fora de route()
# ---------------------------------------------------------------------------

def _detect_gpu_vram_mb() -> int:
    """VRAM total via nvidia-smi (torch não é dependência declarada)."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            return int(out.stdout.strip().splitlines()[0])
    except Exception:
        pass
    return 0


def _detect_marker() -> bool:
    import os
    if os.environ.get("PDF2MD_MARKER"):
        return Path(os.environ["PDF2MD_MARKER"]).exists()
    if shutil.which("marker_single"):
        return True
    return Path(r"Z:\venvs\marker\Scripts\marker_single.exe").exists()


def _detect_tesseract() -> bool:
    if shutil.which("tesseract"):
        return True
    return Path(r"C:/Program Files/Tesseract-OCR/tesseract.exe").exists()


def _detect_pix2tex() -> bool:
    """Runtime pix2tex (torch) — externo. O cropper é built-in; só o math-OCR é externo.
    PDF2MD_PIX2TEX_PYTHON = python de um venv com pix2tex (igual marker em venv próprio);
    fallback: CLI pix2tex/latexocr no PATH."""
    import os
    env = os.environ.get("PDF2MD_PIX2TEX_PYTHON")
    if env:
        return Path(env).exists()
    return bool(shutil.which("pix2tex") or shutil.which("latexocr"))


def _detect_ollama() -> bool:
    """has_ollama = DAEMON alcançável (gemma/qwen são server-externo). O binário no
    PATH NÃO garante daemon rodando, então o socket na porta padrão (11434) é a
    única verdade — evita rotear um refiner VLM que falharia em runtime."""
    try:
        with socket.create_connection(("127.0.0.1", 11434), timeout=0.5):
            return True
    except Exception:
        return False
