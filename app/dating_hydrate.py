"""kosha word-page UX layer — sense-dating era badges (H4019, P3).

STAGING ONLY (03-09-2026), same contract as app/ls_hydrate.py and the
H3744 aligned-sense organ: only reached when `ux["sense_dating"]` is set,
so the default `render_word_page(card)` path is byte-identical (the H4019
assert gate: this layer changes no existing display order).

PWG only. This hydrates the ALREADY-RENDERED
`<span class='ls' title='N'>TEXT</span>` markup (app/render.py's `<ls>`
emission, exactly the span ls_hydrate matches) by appending a small era
badge span INSIDE the citation span:

    <span class='ls era-classical' ...>RAGH. 1,3
        <span class='ls-era' data-era='classical'
          title='...'>4th-5th c.</span></span>

The lookup is data/dating/abbrev_map.tsv (H4019, derived by
scripts/build_sense_dating.py): PWG citation abbreviation → work + era
bucket, kept only where the abbreviation resolves to ONE work at mode
share ≥ 0.9 — homonym-dense abbreviations get no badge, ever.

**What the badge claims** (the preface caveat, in every tooltip):
"first attestation in the cited corpus, not the origin of the meaning"
(«первое засвидетельствование в цитируемом корпусе, не происхождение
значения»). The printed PWG sense order is never reordered; the badge is
additive markup inside an existing span.

When the layer files are absent, `hydrate_dating` returns the input
unchanged — an honest no-op, never a crash (same DB-free posture as
ls_hydrate's sibling checkouts).
"""
import csv
import html
import os
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_ABBREV_TSV = _REPO / "data" / "dating" / "abbrev_map.tsv"

# Matches app/render.py's `<ls>` emission exactly — the same pattern
# app/ls_hydrate.py uses (deliberately does not match `<lshead>` spans).
_LS_SPAN_RE = re.compile(r"<span class='ls'(?: title='([^']*)')?>(.*?)</span>", re.S)
_STRIP_TAGS = re.compile(r"<[^>]+>")
# Trailing coordinate tokens in the citation text ("RAGH. 1,3", "MBH. 1,573")
_TRAILING_COORDS = re.compile(r"[\s,.;:]*\d[\d,.\-–()abxfg\s]*$")

#: era → short label shown in the badge (date_range strings live in the layer)
ERA_LABEL = {
    "vedic": "Vedic",
    "epic-sutra": "epic-sūtra",
    "classical": "classical",
    "early-medieval": "early medieval",
    "late-medieval": "late medieval",
}

_era_of: dict[str, dict] | None = None


def _era_map() -> dict[str, dict]:
    """abbrev → {era, via, mode_share}; loaded once, honest-miss on absence."""
    global _era_of
    if _era_of is not None:
        return _era_of
    _era_of = {}
    try:
        with open(_ABBREV_TSV) as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if r.get("era"):
                    _era_of[r["abbrev"]] = {"era": r["era"],
                                            "via": r.get("via", ""),
                                            "mode_share": r.get("mode_share", "")}
    except OSError:
        return {}
    return _era_of


def abbrev_of(citation_text: str) -> str:
    """The PWG abbreviation a hydrated `<ls>` span carries: leading
    non-digit run, coordinate suffix stripped ("RAGH. 1,3" → "RAGH.")."""
    txt = _STRIP_TAGS.sub("", citation_text)
    txt = _TRAILING_COORDS.sub("", txt).strip()
    return txt.strip()


def badge_html(era: str, via: str) -> str:
    label = ERA_LABEL.get(era, era)
    caveat = ("first attestation in the cited corpus, not the origin of the "
              "meaning (первое засвидетельствование в цитируемом корпусе)")
    if via:
        caveat += f" · via {via}"
    return (f"<span class='ls-era' data-era='{html.escape(era, quote=True)}' "
            f"title='{html.escape(caveat, quote=True)}'>{html.escape(label)}</span>")


def hydrate_dating(rendered: str) -> tuple[str, dict]:
    """Append era badges to PWG `<ls>` spans. Returns (html, stats)."""
    era_map = _era_map()
    stats = {"hits": 0, "misses": 0}

    def _sub(m: re.Match) -> str:
        title_attr, inner = m.group(1), m.group(2)
        if "ls-era" in inner:  # idempotent: never double-badge
            return m.group(0)
        info = era_map.get(abbrev_of(inner))
        if not info:
            stats["misses"] += 1
            return m.group(0)
        stats["hits"] += 1
        cls = f" era-{info['era']}"
        t = f" title='{title_attr}'" if title_attr else ""
        return f"<span class='ls{cls}'{t}>{inner}{badge_html(info['era'], info['via'])}</span>"

    return _LS_SPAN_RE.sub(_sub, rendered), stats
