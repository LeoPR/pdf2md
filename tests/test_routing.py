"""Tests para pdf2md.routing — gates de roteamento macro-intent (T090).

route() é puro: testamos cada intent × {host, doc} com HostInfo/DocInfo mockados.
Cobre as tabelas de gate do spec + degradação + guarda de scan + low-resource.
"""
import pytest

from pdf2md.routing import (
    AUTO, BALANCEADO, INDEXACAO, INTENTS, LOW_RESOURCE, QUALIDADE, RAPIDO,
    DocInfo, HostInfo, Pipeline, RoutingError, ScanNoOCR, route,
)
from pdf2md._profiles import PRIMARY, REFINER, OPTIMIZER


# ---- fixtures de host ----
def host_gpu_full():   # GPU + marker + ollama
    return HostInfo(cpu_cores=8, ram_gb=32, gpu_vram_mb=12000,
                    has_ollama=True, has_marker=True, has_tesseract=True)

def host_gpu_no_marker():  # GPU presente mas marker_single ausente
    return HostInfo(cpu_cores=8, ram_gb=32, gpu_vram_mb=12000,
                    has_ollama=False, has_marker=False, has_tesseract=True)

def host_cpu():  # sem GPU
    return HostInfo(cpu_cores=4, ram_gb=8, gpu_vram_mb=0,
                    has_ollama=False, has_marker=False, has_tesseract=True)

def host_cpu_no_ocr():  # sem GPU e sem tesseract
    return HostInfo(cpu_cores=2, ram_gb=4, gpu_vram_mb=0,
                    has_ollama=False, has_marker=False, has_tesseract=False)

def host_small_gpu():  # marker instalado MAS VRAM insuficiente (<4096)
    return HostInfo(cpu_cores=8, ram_gb=16, gpu_vram_mb=2048,
                    has_ollama=False, has_marker=True, has_tesseract=True)

def host_cpu_pix2tex():  # CPU + runtime pix2tex (cropper é built-in)
    return HostInfo(cpu_cores=4, ram_gb=8, gpu_vram_mb=0,
                    has_marker=False, has_tesseract=True, has_pix2tex=True)


# ---- fixtures de doc ----
def doc_text():       return DocInfo(n_pages=50, has_text_layer=True, math_density=0.0)
def doc_math():       return DocInfo(n_pages=50, has_text_layer=True, math_density=3.0)
def doc_matrix():     return DocInfo(n_pages=50, has_text_layer=True, math_density=3.0, matrix_density=1.5)
def doc_logos():      return DocInfo(n_pages=10, has_text_layer=True, has_raster_logos=True)
def doc_math_logos(): return DocInfo(n_pages=50, has_text_layer=True, math_density=3.0, has_raster_logos=True)
def doc_scan():       return DocInfo(n_pages=30, has_text_layer=False)


def _primaries(p: Pipeline):
    return [s.algo for s in p.steps if s.role == PRIMARY]

def _algos(p: Pipeline):
    return [s.algo for s in p.steps]


# ---------------------------------------------------------------------------
# PRIMARY por intent × host (doc text-layer)
# ---------------------------------------------------------------------------

def test_rapido_uses_pdftotext_even_with_gpu():
    p = route(RAPIDO, host_gpu_full(), doc_text())
    assert p.primary == "pdftotext"
    assert not p.degraded

def test_low_resource_uses_pdftotext():
    p = route(LOW_RESOURCE, host_gpu_full(), doc_text())
    assert p.primary == "pdftotext"
    # optimize OFF em low-resource (teto RAM)
    assert "pdf2md-optimize" not in _algos(p)

def test_qualidade_uses_marker_with_gpu():
    p = route(QUALIDADE, host_gpu_full(), doc_text())
    assert p.primary == "marker"
    assert "pdf2md-optimize" in _algos(p)
    assert not p.degraded

def test_balanceado_marker_with_gpu_else_pdftotext():
    assert route(BALANCEADO, host_gpu_full(), doc_text()).primary == "marker"
    p = route(BALANCEADO, host_cpu(), doc_text())
    assert p.primary == "pdftotext"
    assert not p.degraded   # balanceado adapta, não degrada


# ---------------------------------------------------------------------------
# Degradação honesta
# ---------------------------------------------------------------------------

def test_qualidade_no_gpu_degrades_with_cause():
    p = route(QUALIDADE, host_cpu(), doc_text())
    assert p.primary == "pdftotext"
    assert p.degraded is True
    assert any("sem GPU" in r for r in p.rationale)

def test_qualidade_gpu_but_marker_not_installed_degrades():
    # buraco que a revisão adversarial pegou: GPU presente mas marker ausente
    p = route(QUALIDADE, host_gpu_no_marker(), doc_text())
    assert p.primary == "pdftotext"
    assert p.degraded is True
    assert any("marker_single" in r for r in p.rationale)


# ---------------------------------------------------------------------------
# Guarda de scan (precede gates de intent)
# ---------------------------------------------------------------------------

def test_scan_with_gpu_routes_marker():
    p = route(RAPIDO, host_gpu_full(), doc_scan())
    assert p.primary == "marker"   # scan sobrepõe a regra "rapido força pdftotext"

def test_scan_no_gpu_routes_tesseract():
    p = route(RAPIDO, host_cpu(), doc_scan())
    assert p.primary == "tesseract"

def test_scan_no_ocr_raises_for_all_intents():
    # a revisão pegou: silent-failure em scan; agora ERRO p/ qualquer intent
    for intent in INTENTS:
        with pytest.raises(ScanNoOCR):
            route(intent, host_cpu_no_ocr(), doc_scan())


# ---------------------------------------------------------------------------
# REFINERs (math precisa cropper; logo precisa ollama)
# ---------------------------------------------------------------------------

def test_qualidade_marker_math_no_pix2tex():
    # marker é PRIMARY → math nativo (Texify); pix2tex seria redundante → não entra
    p = route(QUALIDADE, host_gpu_full(), doc_math())
    assert p.primary == "marker"
    assert "pix2tex" not in _algos(p)

def test_qualidade_cpu_math_no_runtime_keeps_math_cru():
    # CPU sem runtime pix2tex (cropper é built-in, mas falta o torch) → math cru
    p = route(QUALIDADE, host_cpu(), doc_math())
    assert "pix2tex" not in _algos(p)
    assert any("cru" in r or "runtime pix2tex ausente" in r for r in p.rationale)

def test_qualidade_cpu_math_with_runtime_adds_pix2tex():
    # gate VIRADO (e21): CPU + runtime pix2tex + math → pix2tex entra (primary=pdftotext)
    p = route(QUALIDADE, host_cpu_pix2tex(), doc_math())
    assert p.primary == "pdftotext"
    assert "pix2tex" in _algos(p)

def test_qualidade_cpu_matrix_flags_low_confidence():
    # fronteira medida: matriz presente → pix2tex entra MAS rationale rebaixa confiança
    p = route(QUALIDADE, host_cpu_pix2tex(), doc_matrix())
    assert "pix2tex" in _algos(p)
    assert any("matriz" in r and "0.50" in r for r in p.rationale)

def test_qualidade_logos_with_ollama_adds_gemma3():
    p = route(QUALIDADE, host_gpu_full(), doc_logos())
    assert "gemma3-4b-small-image" in _algos(p)

def test_qualidade_logos_no_ollama_skips_refiner():
    p = route(QUALIDADE, host_cpu(), doc_logos())
    assert "gemma3-4b-small-image" not in _algos(p)
    assert any("Ollama" in r for r in p.rationale)

def test_rapido_never_adds_refiners():
    p = route(RAPIDO, host_gpu_full(), doc_math_logos())
    assert not any(s.role == REFINER for s in p.steps)


# ---------------------------------------------------------------------------
# --auto converge para --qualidade quando o host comporta
# ---------------------------------------------------------------------------

def test_auto_with_full_host_matches_qualidade():
    h, d = host_gpu_full(), doc_math_logos()
    auto = set(_algos(route(AUTO, h, d)))
    qual = set(_algos(route(QUALIDADE, h, d)))
    assert auto == qual

def test_auto_no_gpu_is_adaptive_not_degraded():
    p = route(AUTO, host_cpu(), doc_text())
    assert p.primary == "pdftotext"
    assert p.degraded is False   # auto adapta; qualidade degradaria


# ---------------------------------------------------------------------------
# --indexacao: 2 passes
# ---------------------------------------------------------------------------

def test_indexacao_pass1_pdftotext_pass2_marker_when_gpu():
    p = route(INDEXACAO, host_gpu_full(), doc_math())
    assert p.primary == "pdftotext"
    assert p.pass2 is not None
    assert p.pass2.primary == "marker"

def test_indexacao_no_gpu_has_no_pass2():
    p = route(INDEXACAO, host_cpu(), doc_math())
    assert p.primary == "pdftotext"
    assert p.pass2 is None


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------

def test_invalid_intent_raises():
    with pytest.raises(RoutingError):
        route("turbo", host_gpu_full(), doc_text())

def test_summary_runs():
    assert "pdftotext" in route(RAPIDO, host_cpu(), doc_text()).summary()


# ---------------------------------------------------------------------------
# Correções da revisão adversarial do código (impl-review)
# ---------------------------------------------------------------------------

def test_small_gpu_marker_installed_degrades_on_vram():
    # marker instalado mas VRAM<4096: qualidade degrada por VRAM; balanceado/auto adaptam
    h = host_small_gpu()
    q = route(QUALIDADE, h, doc_text())
    assert q.primary == "pdftotext" and q.degraded is True
    assert any("VRAM<4096" in r for r in q.rationale)
    assert route(BALANCEADO, h, doc_text()).degraded is False
    assert route(AUTO, h, doc_text()).degraded is False

def test_indexacao_scan_no_optimize_and_has_rationale():
    # optimizer consistente entre scan e text-layer; colapso 2-pass documentado
    p = route(INDEXACAO, host_gpu_full(), doc_scan())
    assert "pdf2md-optimize" not in _algos(p)
    assert p.pass2 is None
    assert any("2-pass" in r or "colapsa" in r for r in p.rationale)

def test_low_resource_optimize_off_by_ram_ceiling():
    # optimize off é DERIVADO do teto + ram dos perfis, não hardcoded
    p = route(LOW_RESOURCE, host_cpu(), doc_text())
    assert "pdf2md-optimize" not in _algos(p)
    assert any("teto" in r and "160" in r for r in p.rationale)

def test_profiles_param_actually_drives_routing():
    # override do mapa muda o resultado → profiles não é decorativo
    from pdf2md._profiles import load_active_profiles
    import copy
    prof = copy.deepcopy(load_active_profiles())
    # remover marker do mapa → _available("marker") = False (profile None)
    del prof["marker"]
    p = route(QUALIDADE, host_gpu_full(), doc_text(), profiles=prof)
    assert p.primary == "pdftotext"   # marker bloqueado via profile override
    assert p.degraded is True
