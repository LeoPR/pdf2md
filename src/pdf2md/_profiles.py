"""Índice machine-readable dos perfis ativos — subconjunto *route-relevant*.

Espelha o padrão de `corpus/registry.py` (dict Python puro, sem dependência):
a fonte-de-verdade HUMANA são os YAML em `docs/profiles/ativo/`; este módulo é o
recorte que o roteador (`pdf2md/routing.py`) consulta. Decisão registrada em
T090 (decisão #1) — pyyaml não é dependência declarada, então não parseamos YAML
em runtime.

Campos por perfil:
- role:        PRIMARY (extrator full-doc) | REFINER (recorte) | OPTIMIZER
- hardware:    "cpu" | "gpu-required" | "gpu-optional"
- needs:       requisitos externos além de hardware (ex. "marker_bin", "ollama")
- granularity: "documento" | "recorte"
- unit_speed_s + unit: custo medido por unidade (pg / formula / img)
- vram_mb:     pico de VRAM medido (0 = CPU)
- scan:        capacidade em scan — "none" | "printed" (Tesseract CPU) | "ocr-gpu" (Surya)
- wins:        dimensões vencidas (do perfil)
- measured_in: labs de origem

Mantido em sincronia manual com docs/profiles/ativo/*.yaml. Se divergir, o YAML
manda (é a fonte humana); atualizar aqui ao promover/remensurar um perfil.
"""
from __future__ import annotations

PRIMARY = "PRIMARY"
REFINER = "REFINER"
OPTIMIZER = "OPTIMIZER"

PROFILES: dict[str, dict] = {
    # ---- PRIMARY (extrator full-doc; escolher 1) --------------------------
    "marker": {
        "role": PRIMARY,
        "hardware": "gpu-required",
        "needs": ["marker_bin"],
        "granularity": "documento",
        "unit_speed_s": 12.9, "unit": "pg",
        "vram_mb": 3400, "ram_mb": 1500, "cold_s": 30,
        "scan": "ocr-gpu",          # Surya OCR (único OCR full-doc; GPU)
        "math": "nativo",           # Texify: math_display/inline forte
        "wins": ["prose", "math", "livro", "paper", "riqueza", "estabilidade"],
        "measured_in": ["e00", "e14"],
    },
    "pdftotext": {
        "role": PRIMARY,
        "hardware": "cpu",
        "needs": [],
        "granularity": "documento",
        "unit_speed_s": 0.0205, "unit": "pg",
        "vram_mb": 0, "ram_mb": 63, "cold_s": 0.1,
        "scan": "none",             # text-layer only; scan vai p/ tesseract
        "math": "cru",              # Unicode cru, sem LaTeX
        "wins": ["velocidade", "ram", "offline", "alucinacao", "determinismo", "estabilidade"],
        "measured_in": ["e19"],
    },
    "tesseract": {
        "role": PRIMARY,
        "hardware": "cpu",
        "needs": ["tesseract_bin"],
        "granularity": "documento",
        "unit_speed_s": 2.74, "unit": "pg",  # @300dpi, e20
        "vram_mb": 0, "ram_mb": 124, "cold_s": 0.5,
        "scan": "printed",          # OCR CPU p/ scan impresso (e20 WER 0.052)
        "math": "cru",
        "wins": ["scan_cpu", "alucinacao", "determinismo", "offline"],
        "measured_in": ["e20"],
        "note": "scan impresso forte; manuscrito falha (honesto, sem alucinar).",
    },

    # ---- REFINER (recorte, componível) ------------------------------------
    "pix2tex": {
        "role": REFINER,
        "hardware": "cpu",
        "needs": ["formula_cropper"],   # BURACO #3: cropper CPU não existe; só via marker
        "granularity": "recorte",
        "unit_speed_s": 6.5, "unit": "formula",
        "vram_mb": 0, "ram_mb": 800, "cold_s": 11.9,
        "refines": "math_display",
        "wins": ["math_semantico", "alucinacao", "offline", "cpu"],
        "measured_in": ["e18"],
        "note": "granularidade=recorte; precisa de cropper de fórmula (só marker hoje).",
    },
    "gemma3-4b-small-image": {
        "role": REFINER,
        "hardware": "gpu-optional",
        "needs": ["ollama"],
        "granularity": "recorte",
        "unit_speed_s": 45.9, "unit": "img",
        "vram_mb": 3500, "ram_mb": 600, "cold_s": 5,
        "refines": "logo",
        "wins": ["logo"],
        "measured_in": ["e16"],
    },
    "qwen3-vl-8b-small-image": {
        "role": REFINER,
        "hardware": "gpu-optional",
        "needs": ["ollama"],
        "granularity": "recorte",
        "unit_speed_s": 112.0, "unit": "img",
        "vram_mb": 5500, "ram_mb": 700, "cold_s": 5,
        "refines": "logo",
        "wins": ["logo"],
        "measured_in": ["e16"],
        "note": "fallback Apache-2.0 do gemma3-4b p/ logo.",
    },

    # ---- OPTIMIZER (pós-extração, universal) ------------------------------
    "pdf2md-optimize": {
        "role": OPTIMIZER,
        "hardware": "cpu",
        "needs": [],
        "granularity": "recorte",
        "unit_speed_s": 0.12, "unit": "img",
        "vram_mb": 0, "ram_mb": 100, "cold_s": 0.1,
        "wins": ["bytes", "determinismo", "universal"],
        "measured_in": ["e04"],
    },
}


def load_active_profiles() -> dict[str, dict]:
    """Devolve os perfis ativos (route-relevant). Função p/ paridade com a API
    do T090 e p/ permitir injeção/override em testes."""
    return PROFILES


def by_role(role: str, profiles: dict | None = None) -> dict[str, dict]:
    p = profiles or PROFILES
    return {k: v for k, v in p.items() if v["role"] == role}
