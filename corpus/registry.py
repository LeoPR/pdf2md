"""corpus/registry.py — fonte-de-verdade legível por código para os documentos do corpus.

Pensa nos PDFs como fontes de dados (dataset) com 3 tiers de armazenamento:

  inrepo   : excerto livre commitado em corpus/examples/ — "prova pronta", outros
             verificam sem baixar nada. Pequeno (poucos MB).
  zcache   : recuperável/baixável; bytes em Z:/caches/corpus/pdf2md/ (NÃO versionado).
             O registry só aponta (path + url + sha256).
  private  : proprietary; source read-only FORA do repo (ex. N&C no AulaQuantum).
             Nunca vai pro git/público. Resultados derivados podem ser públicos COM
             declaração de direito (ver corpus/RIGHTS.md).

`resolve(doc_id)` devolve o Path local utilizável, tentando in-repo → zcache → private,
e levanta erro com instrução se a fonte não estiver disponível. Substitui os paths
hardcoded que estavam espalhados em corpus/_gt/_prefill.py e nos labs.

Sem dependência externa (pyproject zerado; pyyaml ausente) — dict Python puro.
Os manifests humanos (docs/reference/corpus/manifest_*.md) seguem como referência
cruzada de schema/proveniência; ESTE arquivo é o canônico para código.
"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORPUS = PROJECT_ROOT / "corpus"
EXAMPLES = CORPUS / "examples"

# Drives externos (não versionados) — configuráveis por env p/ portabilidade.
# O default é o setup do autor; outra máquina aponta via PDF2MD_ZCACHE / PDF2MD_AULAQUANTUM
# (ou simplesmente não tem o tier, e resolve() cai no excerto in-repo / instrui o download).
ZCACHE = Path(os.environ.get("PDF2MD_ZCACHE") or "Z:/caches/corpus/pdf2md")
AULAQUANTUM = Path(
    os.environ.get("PDF2MD_AULAQUANTUM")
    or "C:/Users/leona/OneDrive/Documents/Projects/Acadêmicos/AulaQuantum/pesquisa_geral/_sources"
)

# doc_id -> entrada. Chaves batem com os doc_ids já usados em labs e em corpus/_gt/.
REGISTRY: dict[str, dict] = {
    # ---- PRIVATE (proprietary; nunca no git) -------------------------------
    "nielsen_chuang_cap4": {
        "tier": "private",
        "path": AULAQUANTUM / "livros" / "Nielsen_Chuang_QCQI.pdf",
        "license": "proprietary",            # copyright Cambridge University Press
        "sha256": "4090c88c294fbe428114256185118b6862d8716a14f9ebf2c7df258f28eb640e",
        "title": "Nielsen & Chuang, Quantum Computation and Quantum Information (cap4)",
        "results_publishable": "with-declaration",  # só resultados DERIVADOS (RIGHTS.md)
        "note": "Source E destiny no AulaQuantum (output de uso volta pra lá). "
                "GT verbatim (corpus/_gt/nielsen_chuang_cap4/) é PRIVADO desde 2026-06-09 "
                "(fora do repo público e do histórico; vive só no disco do autor).",
    },

    # ---- ZCACHE (livre/recuperável; bytes em Z:, só ref aqui) --------------
    "preskill_ph219_ch5": {
        "tier": "zcache",
        "path": ZCACHE / "preskill_ph219_ch5.pdf",
        "url": "http://theory.caltech.edu/~preskill/ph219/",
        "license": "read-only-online",       # NÃO redistribuir o PDF (só referenciar)
        "title": "Preskill, PH219/CS219 Lecture Notes ch5",
        "note": "GT + rasters (corpus/_gt/preskill_ph219_ch5/) privados desde 2026-06-09, "
                "alinhando o repo à própria política read-only-online.",
    },
    "arxiv_1706_03762": {
        "tier": "zcache",
        "path": ZCACHE / "arxiv_1706_03762.pdf",
        "url": "https://arxiv.org/abs/1706.03762",
        "license": "arxiv-non-exclusive",
        "title": "Vaswani et al., Attention Is All You Need",
        "inrepo_excerpt": "examples/arxiv_1706_03762_excerpt.pdf",  # 2pg p/ demo
    },
    "arxiv_2106_05919v2": {
        "tier": "zcache",
        "path": ZCACHE / "arxiv_2106_05919v2.pdf",
        "url": "https://arxiv.org/abs/2106.05919",
        "license": "arxiv-non-exclusive",
        "title": "arXiv 2106.05919v2 (math-heavy)",
    },
    "cdc_mmwr_73_35_a1": {
        "tier": "zcache",
        "path": ZCACHE / "cdc_mmwr_73_35_a1.pdf",
        "url": "https://www.cdc.gov/mmwr/",
        "license": "us-gov-public-domain",
        "title": "CDC MMWR 73(35) (gov multi-col)",
        "inrepo_excerpt": "examples/cdc_mmwr_73_35_a1.pdf",  # gov PD, pode commitar inteiro (~0.3MB)
    },
    "ia_mathematics00wils": {
        "tier": "zcache",
        "path": ZCACHE / "ia_mathematics00wils.pdf",
        "url": "https://archive.org/details/mathematics00wils",
        "license": "public-domain",          # pré-1928
        "title": "Wilson, Mathematics (1800s, scan MANUSCRITO PD)",
        "inrepo_excerpt": "examples/wilson_mathematics_excerpt.pdf",  # 2pg PD
        "note": "scan manuscrito cursivo — limite de CPU-OCR (e20).",
    },
    "ia_atkins_pure_mathematics_1874": {
        "tier": "zcache",
        "path": ZCACHE / "ia_atkins_pure_mathematics_1874.pdf",
        "url": "https://archive.org/details/...atkins",
        "license": "public-domain",          # 1874
        "title": "Atkins, Pure Mathematics (1874, scan IMPRESSO PD)",
        "note": "scan impresso — CPU-OCR Tesseract WER 0.052 em p80 (e20).",
    },
    "irs_f1040_2025": {
        "tier": "zcache",
        "path": ZCACHE / "irs_f1040_2025.pdf",
        "url": "https://www.irs.gov/forms-pubs/about-form-1040",
        "license": "us-gov-public-domain",
        "title": "IRS Form 1040 (AcroForm, gov PD)",
        "inrepo_excerpt": "examples/irs_f1040_2025.pdf",  # gov PD, ~0.2MB
    },
}


class SourceUnavailable(FileNotFoundError):
    """Source registrada mas ausente no disco (tier zcache/private não montado)."""


def entry(doc_id: str) -> dict:
    e = REGISTRY.get(doc_id)
    if e is None:
        raise KeyError(
            f"doc_id '{doc_id}' não está no registry. "
            f"Conhecidos: {sorted(REGISTRY)}"
        )
    return e


def resolve(doc_id: str, *, prefer_excerpt: bool = False) -> Path:
    """Devolve o Path local utilizável para doc_id.

    Ordem: excerto in-repo (se prefer_excerpt ou tier=inrepo) → path do tier.
    Levanta SourceUnavailable com instrução se o source do tier não existir.
    """
    e = entry(doc_id)

    exc = e.get("inrepo_excerpt")
    if exc:
        p = (CORPUS / exc).resolve()
        if (prefer_excerpt or e["tier"] == "inrepo") and p.exists():
            return p

    path = Path(e["path"])
    if path.exists():
        return path

    if exc and (CORPUS / exc).resolve().exists():
        # fallback: tier indisponível, mas temos o excerto in-repo
        return (CORPUS / exc).resolve()

    hint = e.get("url", "(sem url no registry)")
    raise SourceUnavailable(
        f"'{doc_id}' (tier={e['tier']}) não encontrado em {path}.\n"
        f"  - zcache: montar Z: / baixar de {hint}\n"
        f"  - private: source proprietary read-only (ex. AulaQuantum)\n"
        f"  - excerto in-repo: {exc or '(nenhum)'}"
    )


def has_excerpt(doc_id: str) -> bool:
    e = entry(doc_id)
    exc = e.get("inrepo_excerpt")
    return bool(exc and (CORPUS / exc).resolve().exists())


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("doc_id".ljust(24), "tier".ljust(9), "disponível", "license")
    for did, e in REGISTRY.items():
        try:
            p = resolve(did)
            avail = "in-repo" if has_excerpt(did) and e["tier"] != "private" else "OK"
            avail = "OK" if p.exists() else "—"
        except SourceUnavailable:
            avail = "ausente"
        except Exception:
            avail = "erro"
        print(did.ljust(24), str(e["tier"]).ljust(9), avail.ljust(10), e.get("license", "?"))
