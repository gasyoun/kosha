"""Public SanskritRussian glossary strip for /w/ (H2680 / W-RU-2).

Reuses `RuGlosser` from scripts/build_ru_gloss_layer.py — the same
surface / lemma / root join the reading packs already use. Never reads
`corpus_lexicon` or any restricted bulk layer. Never vendors the glossary.
"""
from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

# Repo root = parents[3] of src/kosha/api/sr_gloss.py
_KOSHA_ROOT = Path(__file__).resolve().parents[3]
_SCRIPTS = _KOSHA_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import build_ru_gloss_layer as rg  # noqa: E402

_PUBLIC_FILES = (
    "surface_glossary.tsv",
    "lemma_glossary.tsv",
    "root_glossary.tsv",
    "dcs_lemma2root.tsv",
)


def _sibling_roots() -> list[Path]:
    parent = _KOSHA_ROOT.parent
    return [
        parent / "SanskritRussian",
        parent.parent / "SanskritRussian",
        # .92: clone next to /opt/kosha/repo when missing
        _KOSHA_ROOT.parent / "SanskritRussian",
    ]


def _is_public_root(path: Path) -> bool:
    return (path / "lemma_glossary.tsv").is_file() or (
        path / "surface_glossary.tsv"
    ).is_file()


def resolve_sr_root() -> Path | None:
    """Explicit `$KOSHA_SR_GLOSS`, else the first sibling public checkout."""
    env = (os.environ.get("KOSHA_SR_GLOSS") or "").strip()
    if env:
        path = Path(env)
        return path if path.exists() else None
    for cand in _sibling_roots():
        if cand.is_dir() and _is_public_root(cand):
            return cand
    return None


@lru_cache(maxsize=4)
def _glosser(root_str: str) -> rg.RuGlosser:
    return rg.RuGlosser(root=Path(root_str), missing_ok=True)


def clear_caches() -> None:
    """Test hook — drop the loaded glosser after an env change."""
    _glosser.cache_clear()


def join_sr_strip(slp1: str) -> dict[str, Any]:
    """One public-tier gloss for a lemma key. Lemma wins, then surface.

    Returns `{hit, text, layer}`. Missing tree or key → hit False.
    Root layer is not the strip (handoff: lemma/surface only).
    """
    empty: dict[str, Any] = {"hit": False, "text": None, "layer": None}
    root = resolve_sr_root()
    if root is None or not slp1:
        return empty
    out = _glosser(str(root.resolve())).gloss(slp1, None, slp1)
    if out.get("lemma_ru"):
        return {"hit": True, "text": out["lemma_ru"], "layer": "lemma"}
    if out.get("surface_ru"):
        return {"hit": True, "text": out["surface_ru"], "layer": "surface"}
    return empty
