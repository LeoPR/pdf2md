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
        )

    def marker_available(self) -> bool:
        """Conveniência (CLI/doctor). route() usa a versão profile-driven `_available`."""
        return self.has_marker and self.gpu_vram_mb >= MARKER_VRAM_MIN_MB


@dataclass
class DocInfo:
    n_pages: int = 1
    has_text_layer: bool = True
    math_density: float = 0.0     # regiões equation-like / página (heurística)
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
        doc = fitz.open(str(pdf_path))
        n = len(doc)
        if n == 0:
            doc.close()
            raise ValueError(f"PDF sem páginas: {pdf_path}")
        idxs = list(range(min(sample, n)))
        if n > sample:
            idxs += [n // 2, n - 1]
        text_chars = 0
        math_hits = 0
        has_logos = False
        seen = 0
        for i in sorted(set(idxs)):
            page = doc[i]
            t = page.get_text()
            text_chars += len(t.strip())
            math_hits += len(re.findall(r"[=∑∫√≤≥≠αβγδλΣΦΨΩ]|\b\d+/\d+\b|\^|\\[a-zA-Z]+", t))
            for img in page.get_images(full=True):
                w = img[2] if len(img) > 2 else 0
                if 0 < w < 200:        # imagem raster pequena = candidata a logo
                    has_logos = True
            seen += 1
        doc.close()
        seen = max(seen, 1)
        return cls(
            n_pages=n,
            has_text_layer=(text_chars / seen) > 30,   # >30 chars/pg amostrado = tem text-layer
            math_density=round(math_hits / seen, 2),
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

def _available(algo: str, host: HostInfo, profiles: dict, primary: str | None = None) -> bool:
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
        if need == "formula_cropper" and primary != "marker":
            return False   # BURACO #3: único cropper de fórmula é o Marker (GPU)
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
                    f"--qualidade pediu marker mas indisponível ({cause}); "
                    f"degradando p/ pdftotext (prose). Math fica cru — falta cropper CPU (BURACO #3)."
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
    # math: pix2tex (recorte) precisa de cropper de fórmula — _available checa o need
    # 'formula_cropper', que só é satisfeito com primary==marker (BURACO #3).
    if doc.math_density > 0:
        if _available("pix2tex", host, profiles, primary):
            pipe.steps.append(Step("pix2tex", REFINER, "refina fórmulas (marker já faz math nativo)"))
        else:
            pipe.rationale.append(
                "math presente mas sem cropper de fórmula (PRIMARY não-marker; BURACO #3) → math fica cru."
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
    p2.steps.append(Step("marker", PRIMARY, "reprocessa docs math-heavy / baixa qualidade"))
    if doc.math_density > 0 and _available("pix2tex", host, profiles, "marker"):
        p2.steps.append(Step("pix2tex", REFINER, "refina fórmulas"))
    p2.steps.append(Step("pdf2md-optimize", OPTIMIZER, "otimização"))
    return p2


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


def _detect_ollama() -> bool:
    """has_ollama = DAEMON alcançável (gemma/qwen são server-externo). O binário no
    PATH NÃO garante daemon rodando, então o socket na porta padrão (11434) é a
    única verdade — evita rotear um refiner VLM que falharia em runtime."""
    try:
        with socket.create_connection(("127.0.0.1", 11434), timeout=0.5):
            return True
    except Exception:
        return False
