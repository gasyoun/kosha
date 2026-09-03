"""kosha word-page UX layer — sense-dating era badges (H4019, P3).

**PUBLISHED 03-09-2026** (MG order on «показать бейджи на поверхности kośa»,
H4026): the badge render is live on the PWG panel of every word page rendered
with the `ux["sense_dating"]` key — set by the live build
(scripts/build_word_pages.py default `ux`), never reached without the key, so
the default `render_word_page(card)` path stays byte-identical (the H4019
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
share ≥ 0.9 — homonym-dense abbreviations get no badge, ever. Works the
layer refuses to date (Suśruta, disputed) carry no row → no badge.

**Runs AFTER app/ls_hydrate.py** (word_page.py order is fixed): on the live
path a resolvable citation has already been rewritten to
`<a class="ls ls-scan|ls-etext">…</a>`, so the badge pass matches BOTH forms
— the plain `<span class='ls'>` (unresolvable citations, badge appended
INSIDE the span) and the rewritten anchor (badge appended INSIDE the `<a>`,
after the citation text; the badge then rides the citation's own link, same
as the span form rides its span). Continuation citations — PWG prints
`<ls n="RAGH. 1,">12,6779</ls>` and app/render.py keeps that `n` in the
span/anchor `title` while the visible text is bare coordinates — look up
their abbreviation from the `title` attribute when the visible text alone
resolves to nothing (`title='7'`-style coordinate-only titles are skipped).

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
# What app/ls_hydrate.py rewrote that span INTO when the citation resolved
# (HIT_SCAN / HIT_ETEXT) — badge must cover these too or the live path would
# badge only the citations ls_hydrate could NOT link.
_LS_ANCHOR_RE = re.compile(
    r'(<a class="ls ls-(?:scan|etext)"[^>]*>)(.*?)(</a>)', re.S)
_STRIP_TAGS = re.compile(r"<[^>]+>")
# Trailing coordinate tokens in the citation text ("RAGH. 1,3", "MBH. 1,573")
_TRAILING_COORDS = re.compile(r"[\s,.;:]*\d[\d,.\-–()abxfg\s]*$")
# A continuation `title` that actually carries an abbreviation: "RAGH. 1,"
# qualifies ("RAGH."), the ls `n`-attribute form title='7' (bare coordinates
# or empty) does not.
_TITLE_HAS_ABBREV = re.compile(r"[^\s\d,.;:\-–()abxfg]")

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


def _title_abbrev(title: str | None) -> str:
    """Abbreviation carried by a continuation citation's `title` ("RAGH. 1,"
    → "RAGH."), or "" when the title is coordinate-only (the ls `n`-attribute
    form title='7') — never an abbreviation."""
    if not title or not _TITLE_HAS_ABBREV.search(title):
        return ""
    return _TRAILING_COORDS.sub("", title).strip()


def hydrate_dating(rendered: str) -> tuple[str, dict]:
    """Append era badges to PWG `<ls>` citations — both the plain spans
    app/render.py emits (badge appended INSIDE the span) and the
    `<a class="ls ls-scan|ls-etext">` anchors app/ls_hydrate.py rewrote the
    resolvable ones into (badge appended INSIDE the anchor, riding the
    citation's own link). Returns (html, stats).

    Never reverse-resolves a link URL: a continuation citation that ls_hydrate
    linked (abbreviation lives only in the URL after the rewrite) is an honest
    miss — the run's first citation still carries the visible abbreviation."""
    era_map = _era_map()
    stats = {"hits": 0, "misses": 0}

    def _lookup(inner: str, title: str | None):
        if "ls-era" in inner:  # idempotent: never double-badge
            return None
        info = era_map.get(abbrev_of(inner))
        if not info:
            info = era_map.get(_title_abbrev(title))
        return info

    def _sub_span(m: re.Match) -> str:
        title_attr, inner = m.group(1), m.group(2)
        info = _lookup(inner, title_attr)
        if not info:
            stats["misses"] += 1
            return m.group(0)
        stats["hits"] += 1
        cls = f" era-{info['era']}"
        t = f" title='{title_attr}'" if title_attr else ""
        return f"<span class='ls{cls}'{t}>{inner}{badge_html(info['era'], info['via'])}</span>"

    def _sub_anchor(m: re.Match) -> str:
        head, inner, tail = m.group(1), m.group(2), m.group(3)
        # anchors carry the scan tooltip in title=, not the ls n-attr —
        # no title fallback here (see docstring).
        info = _lookup(inner, None)
        if not info:
            stats["misses"] += 1
            return m.group(0)
        stats["hits"] += 1
        return f"{head}{inner}{badge_html(info['era'], info['via'])}{tail}"

    out = _LS_SPAN_RE.sub(_sub_span, rendered)
    out = _LS_ANCHOR_RE.sub(_sub_anchor, out)
    return out, stats
