"""kosha D2 — per-dict sense segmentation.

ARCHITECTURE.md A2 mints sense IDs `{dict}.{L}.{senseN}` where senseN is a
"sense counter minted within the entry". This module derives that counter
from the `<div>` division markers that `make_xml.py` / basicadjust.php insert
into every csl-orig body and that basicdisplay.php renders as separate visual
divisions — the same boundaries a reader sees:

    MW    <div n="to"/> / <div n="vp"/>  meaning + verb-paradigm breaks
    PWG   <div n="1|2|3">…</div>          numbered senses (1〉) and sub-senses (a〉)
    AP90  <div n="1"/> before <b>1</b>…   numbered senses / compound dividers

Rule (uniform, per-dict `<div>` shapes above all reduce to the same boundary
signal): within the `<body>…</body>` region, sense 1 spans from the region
start to the first top-level `<div>`; each subsequent `<div>` opens a new
sense. An entry with no `<div>` gets a single sense spanning the whole body
(ARCHITECTURE's sanctioned fallback — "an entry-level citation is always
mintable"). Candidate spans with no visible (non-whitespace, tag-stripped)
text are dropped and the survivors renumbered 1..N, so every minted senseN
resolves to real text.

senseN is a *stable within-entry division counter*, per A2 — NOT necessarily
the dictionary's printed sense number (e.g. sense 1 is usually the headword +
grammar head that precedes the first printed meaning). It is deterministic and
byte-anchored, which is what the `@version` citation contract (A2, RISKS.md R1)
requires.

Spans are byte offsets into the FULL record string (the `entries.body` column,
which is the whole `<H1>…</H1>` record), because `/api/v1/sense/{id}` slices
`row["body"][span_start:span_end]`.
"""
import re

_RE_BODY_OPEN = re.compile(r"<body\b[^>]*>")
_RE_BODY_CLOSE = re.compile(r"</body>")
_RE_DIV_OPEN = re.compile(r"<div\b[^>]*>")
_RE_TAG = re.compile(r"<[^>]+>")


def _body_region(record: str):
    """(start, end) offsets of the meaning region inside the full record —
    just past `<body>` to just before the last `</body>`. Falls back to the
    whole record when the tags are absent (defensive; all csl-sqlite records
    carry a <body>)."""
    m_open = _RE_BODY_OPEN.search(record)
    if not m_open:
        return 0, len(record)
    start = m_open.end()
    closes = list(_RE_BODY_CLOSE.finditer(record, start))
    end = closes[-1].start() if closes else len(record)
    return start, end


def _has_visible_text(fragment: str) -> bool:
    return bool(_RE_TAG.sub("", fragment).strip())


def segment(dict_code: str, record: str):
    """Return a list of (span_start, span_end) offsets into `record`, one per
    sense, in order. Always returns at least one span. `dict_code` is accepted
    for interface stability and future per-dict divergence; the current rule is
    uniform across mw/pwg/ap90 because their `<div>` markers share one boundary
    semantics (see module docstring)."""
    start, end = _body_region(record)
    region = record[start:end]

    # Boundaries: region start + each top-level <div> open, as absolute offsets.
    boundaries = [start]
    for m in _RE_DIV_OPEN.finditer(region):
        pos = start + m.start()
        if pos != boundaries[-1]:
            boundaries.append(pos)

    # Candidate spans between consecutive boundaries; last runs to region end.
    candidates = []
    for i, b in enumerate(boundaries):
        s_end = boundaries[i + 1] if i + 1 < len(boundaries) else end
        candidates.append((b, s_end))

    # Keep only spans with visible text; if that leaves nothing (all-whitespace
    # body), fall back to the whole region so a sense is always mintable.
    spans = [(s, e) for (s, e) in candidates if _has_visible_text(record[s:e])]
    if not spans:
        spans = [(start, end)]
    return spans


def sense_text(record: str, span_start: int, span_end: int) -> str:
    """Tag-stripped, whitespace-collapsed visible text of a sense span — the
    similarity key the sense_crosswalk uses to match old→new senses across a
    rebuild (RISKS.md R1 Commitment 2)."""
    return re.sub(r"\s+", " ", _RE_TAG.sub(" ", record[span_start:span_end])).strip()
