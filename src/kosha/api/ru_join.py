"""Read-only pwg_ru / mw_ru join for /w/ language groups (H2670).

Looks up a lemma in a sibling `SanskritLexicography/RussianTranslation`
tree, or in the committed CI fixture `tests/fixtures/ru_join/`. Never
writes the translation store and never flips `review_status`.
"""
from __future__ import annotations

import html
import re
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from kosha.api.sanitize import sanitize_html

# Repo root = parents[3] of src/kosha/api/ru_join.py
_KOSHA_ROOT = Path(__file__).resolve().parents[3]

_PWG_NAMES = (
    "pwg_ru.jsonl",
    "pwg_ru_translated.jsonl",
    "src/pwg_ru_translated.jsonl",
)
_MW_NAMES = (
    "mw_ru.jsonl",
    "mw_ru_translated.jsonl",
    "src/mw_ru.jsonl",
    "src/mw_ru_translated.jsonl",
)

REVIEWED = frozenset({"approved", "human_reviewed"})


def locale_from_accept_language(header: str | None) -> str:
    """EN unless an Accept-Language tag is `ru` / `ru-*` (vote R13)."""
    if not header:
        return "en"
    for part in header.split(","):
        tag = part.split(";", 1)[0].strip().lower().replace("_", "-")
        if tag == "ru" or tag.startswith("ru-"):
            return "ru"
    return "en"


def _sibling_roots() -> list[Path]:
    parent = _KOSHA_ROOT.parent
    return [
        parent / "SanskritLexicography" / "RussianTranslation",
        parent.parent / "SanskritLexicography" / "RussianTranslation",
        # .92: clone next to /opt/kosha/repo when missing (vote R14)
        _KOSHA_ROOT.parent / "SanskritLexicography" / "RussianTranslation",
    ]


def resolve_ru_root() -> Path | None:
    """Explicit `$KOSHA_RU_JOIN`, else the first sibling tree that exists."""
    env = (os.environ.get("KOSHA_RU_JOIN") or "").strip()
    if env:
        path = Path(env)
        return path if path.exists() else None
    for cand in _sibling_roots():
        if cand.is_dir():
            return cand
    return None


def _first_file(root: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        path = root / name
        if path.is_file():
            return path
    return None


def _index_jsonl(path: Path) -> dict[str, list[dict[str, Any]]]:
    idx: dict[str, list[dict[str, Any]]] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            key = rec.get("key1") or rec.get("slp1") or rec.get("key") or ""
            if key:
                idx.setdefault(str(key), []).append(rec)
    return idx


@lru_cache(maxsize=8)
def _store_index(path_str: str) -> dict[str, list[dict[str, Any]]]:
    return _index_jsonl(Path(path_str))


def clear_caches() -> None:
    """Test hook — drop the store index after an env change."""
    _store_index.cache_clear()


_RU_SLP1_RE = re.compile(r"\{#(.*?)#\}", re.S)
_RU_GLOSS_RE = re.compile(r"\{%(.*?)%\}", re.S)


def ru_markup_prepass(ru: str) -> str:
    """RU-pipeline wrappers -> Cologne markup the renderer already knows (H3480, R3).

    The pwg_ru / mw_ru stores carry two conventions of their own on top of
    Cologne markup: `{#slp1#}` for a Sanskrit word (the PWG `<s>` payload, SLP1,
    accents allowed) and `{%…%}` around a Russian gloss. `render()` is the
    basicdisplay port and knows neither, so before this pre-pass both leaked
    verbatim into the public RU tab (`{#gam#} (vgl. {#gA#}) образует …`).
    `<s>` goes through the renderer's server-side IAST transliteration
    (src/kosha/render.py, sdata span); the gloss becomes `<i>` like PWG's own
    German glosses. Nothing else is touched.
    """
    if not ru or ("{#" not in ru and "{%" not in ru):
        return ru
    ru = _RU_SLP1_RE.sub(lambda m: "<s>" + m.group(1) + "</s>", ru)
    ru = _RU_GLOSS_RE.sub(lambda m: "<i>" + m.group(1) + "</i>", ru)
    return ru


def _render_ru(dict_id: str, row: dict[str, Any]) -> str:
    ready = row.get("rendered_html")
    if isinstance(ready, str) and ready.strip():
        return sanitize_html(ru_markup_prepass(ready)) if ("{#" in ready or "{%" in ready) \
            else sanitize_html(ready)
    ru = row.get("ru") or row.get("russian") or ""
    if not isinstance(ru, str) or not ru.strip():
        return ""
    ru = ru_markup_prepass(ru)
    # Live store rows carry Cologne-style markup; never read the German `de`.
    if any(tok in ru for tok in ("<div", "{%", "{#", "<ls>", "<ab>", "<lex>")):
        try:
            from kosha.api.serializer import render_sanitized

            code = "pwg" if dict_id == "pwg_ru" else "mw"
            return render_sanitized(code, ru)
        except Exception:
            pass
    if ru.lstrip().startswith("<"):
        return sanitize_html(ru)
    return "<p>" + html.escape(ru) + "</p>"


def unreviewed(status: str | None) -> bool:
    return (status or "ai_translated").strip() not in REVIEWED


def rows_to_entries(dict_id: str, rows: list[dict[str, Any]], slp1: str) -> list[dict[str, Any]]:
    entries = []
    for row in rows:
        status = (row.get("review_status") or "ai_translated").strip()
        entries.append(
            {
                "dict": dict_id,
                "headword": row.get("iast") or row.get("headword") or slp1,
                "rendered_html": _render_ru(dict_id, row),
                "scan_url": None,
                "review_status": status,
            }
        )
    return entries


def join_ru(slp1: str) -> dict[str, list[dict[str, Any]]]:
    """Return `{pwg_ru: [entries], mw_ru: [entries]}`. Missing store → empty lists."""
    empty: dict[str, list[dict[str, Any]]] = {"pwg_ru": [], "mw_ru": []}
    root = resolve_ru_root()
    if root is None or not slp1:
        return empty
    mapping = (
        ("pwg_ru", _first_file(root, _PWG_NAMES)),
        ("mw_ru", _first_file(root, _MW_NAMES)),
    )
    out = dict(empty)
    for dict_id, path in mapping:
        if path is None:
            continue
        rows = _store_index(str(path.resolve())).get(slp1) or []
        out[dict_id] = rows_to_entries(dict_id, rows, slp1)
    return out
