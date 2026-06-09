"""Descoberta PORTÁVEL de ferramentas externas (marker / chrome / tesseract / pandoc).

Cada `find_*` segue a MESMA cadeia: env var `PDF2MD_*` → `shutil.which` (multi-nome,
multi-SO) → locais padrão por SO → o NOME do comando como fallback portável.

Princípio: NUNCA devolver um path absoluto preso à máquina do autor
(`Z:\\venvs\\marker`, `C:\\Program Files\\...`) como fallback universal. Quando a
ferramenta não é encontrada, devolve o nome do comando ("marker_single", "chrome", ...)
— que `available()` reconhece como ausente e o `pdf2md doctor` instrui a instalar.
Os locais `C:\\Program Files\\...` permanecem, mas SÓ como default do Windows
(gated por `sys.platform`), depois de env+PATH. Centraliza o que estava duplicado
em cli/pdfs/roundtrip/executor/routing com fallbacks de uma máquina só.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

# Nomes que o Chrome/Chromium headless assume por SO/distro (Linux/macOS não usam "chrome").
_CHROME_NAMES = ["chrome", "google-chrome", "google-chrome-stable",
                 "chromium", "chromium-browser", "msedge"]


def available(cmd: str | None) -> bool:
    """True se `cmd` é um arquivo existente OU resolve no PATH (nome de comando)."""
    if not cmd:
        return False
    return Path(cmd).exists() or shutil.which(cmd) is not None


def _first_existing(paths: list[str]) -> str | None:
    for p in paths:
        if p and Path(p).exists():
            return p
    return None


def _resolve(env_var: str, which_names: list[str], os_locations: list[str]) -> str | None:
    """env var (respeitada como-está) → PATH (qualquer um dos nomes) → locais do SO → None."""
    env = os.environ.get(env_var)
    if env:
        return env
    for name in which_names:
        hit = shutil.which(name)
        if hit:
            return hit
    return _first_existing(os_locations)


def find_marker() -> str:
    """marker_single: PDF2MD_MARKER → PATH → 'marker_single' (bare, portável)."""
    return _resolve("PDF2MD_MARKER", ["marker_single"], []) or "marker_single"


def find_pandoc() -> str:
    """pandoc: PDF2MD_PANDOC → PATH → 'pandoc' (bare; subprocess resolve em runtime)."""
    return _resolve("PDF2MD_PANDOC", ["pandoc"], []) or "pandoc"


def find_tesseract() -> str:
    """tesseract: PDF2MD_TESSERACT → PATH → local padrão do SO → 'tesseract'."""
    if sys.platform == "win32":
        locs = [r"C:/Program Files/Tesseract-OCR/tesseract.exe"]
    else:
        locs = ["/usr/bin/tesseract", "/usr/local/bin/tesseract", "/opt/homebrew/bin/tesseract"]
    return _resolve("PDF2MD_TESSERACT", ["tesseract"], locs) or "tesseract"


def find_chrome() -> str:
    """Chrome/Chromium headless: PDF2MD_CHROME → PATH (multi-nome) → local padrão do SO → 'chrome'."""
    if sys.platform == "win32":
        locs = [r"C:/Program Files/Google/Chrome/Application/chrome.exe",
                r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
                r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"]
    elif sys.platform == "darwin":
        locs = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    else:
        locs = ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium", "/usr/bin/chromium-browser", "/snap/bin/chromium"]
    return _resolve("PDF2MD_CHROME", _CHROME_NAMES, locs) or "chrome"
