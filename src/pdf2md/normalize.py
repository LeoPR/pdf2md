"""Normalização canônica de MD para round-trip e similarity metrics.

Consolida três cópias historicamente duplicadas em `roundtrip.py`,
`stats.py` e `multi_roundtrip.py`. Versão unificada com flag
`strip_md_escapes` para opt-in em remoção de markdown escapes —
descoberta em e05 (AcroForm gate, Q11.b): marker escapa automaticamente
`_`, `*`, etc., penalizando token similarity em ~71pp para markup denso
sem afetar conteúdo.

Default `strip_md_escapes=False` preserva comportamento histórico
(reprodutibilidade contra baseline T050 N&C 95.09%).
"""
from __future__ import annotations

import re
from pathlib import Path

# Page markers do marker (e.g. "{17}") + HTML comments de página
_PAGE_MARKER_RE = re.compile(r"\{\d+\}")
_PAGE_HTML_COMMENT_RE = re.compile(
    r"<!--\s*page\s*\d+\s*-->", flags=re.IGNORECASE
)

# Imagens — preserva alt mas reduz path para basename
_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

# Markdown escapes — `\_`, `\*`, `\(`, etc. Quando opt-in, remove o `\`
# para que a comparação não penalize escapes cosméticos do reconstrutor.
_MD_ESCAPE_RE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!])")


def normalize_md(text: str, *, strip_md_escapes: bool = False) -> str:
    """Normaliza MD para comparação semântica de tokens.

    Remove diferenças que não impactam fidelidade de conteúdo:
    - Marcadores de página (`{N}` do marker, `<!-- page N -->` de pandoc)
    - Caminhos de imagem (mantém só basename — paths variam entre runs)
    - Whitespace múltiplo (tabs/espaços, blank lines extras)
    - Opcional: escapes markdown (`\\_` → `_`, etc.)

    Args:
        text: conteúdo MD bruto.
        strip_md_escapes: se True, remove escapes `\\X` para X em
            `` \\`*_{}[]()#+-.! ``. Use quando comparar contra MD₂ produzido
            por marker que escapa automaticamente caracteres em listas/forms
            densos. Default False mantém o comportamento histórico.

    Returns:
        Texto normalizado, leading/trailing whitespace removido.
    """
    text = _PAGE_MARKER_RE.sub("", text)
    text = _PAGE_HTML_COMMENT_RE.sub("", text)

    text = _IMG_RE.sub(
        lambda m: f"![{m.group(1)}]({Path(m.group(2)).name})", text
    )

    if strip_md_escapes:
        text = _MD_ESCAPE_RE.sub(r"\1", text)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
