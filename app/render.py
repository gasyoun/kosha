"""kosha D4 — render(dict, body) -> html.

**Partial port, not the full ARCHITECTURE.md A1 port.** basicadjust.php +
basicdisplay.php (csl-websanlexicon v02/makotemplates/web/webtc/) total 5,516
lines of PHP implementing per-tag display rules, cross-reference resolution,
and per-dict quirks accumulated over years of Cologne corrections. A faithful
byte-for-byte port with golden HTML snapshots (ARCHITECTURE.md's stated bar:
"the renderer cannot merge without them") is D4-scoped follow-on work, not
completed in this pass — flagged in data/SOURCES.md, not silently claimed.

What ships now: a small, honest subset covering the tags actually observed
across mw/pwg/ap90 raw bodies (<s> Sanskrit spans via sanskrit-util, <ab>
abbreviations, <ls> cross-references, <pc>/<L>/<head> stripped from display,
paragraph breaks). Good enough for `?raw=1` callers and for the API to return
*something* renderable; NOT a claim of parity with the PHP display engine.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "sanskrit-util" / "py"))
from sanskrit_util import from_slp1  # noqa: E402

_RE_S = re.compile(r"<s>(.*?)</s>", re.S)
_RE_AB = re.compile(r"<ab>(.*?)</ab>", re.S)
_RE_LS = re.compile(r"<ls>(.*?)</ls>", re.S)
# Metadata elements: drop TAG + CONTENT entirely (headword/pagination/provenance,
# not display text). Wrapper elements (H1, body, h): drop only the tags,
# keep the inner display text.
_RE_DROP_WHOLE = re.compile(r"<(key1|key2|pc|L|tail|info)\b[^>]*>.*?</\1>|<(?:pc|L|info)[^>]*/>", re.S)
_RE_STRIP_WRAPPER_TAGS = re.compile(r"</?(?:H1|h|body|div)\b[^>]*>", re.S)
_RE_ANY_TAG = re.compile(r"<[^>]+>")


def render(dict_code: str, body: str) -> str:
    """Minimal display render — see module docstring for scope."""
    html = body
    html = _RE_DROP_WHOLE.sub("", html)
    html = _RE_STRIP_WRAPPER_TAGS.sub("", html)
    html = _RE_S.sub(lambda m: f"<span class='sa'>{from_slp1(re.sub('<[^>]+>', '', m.group(1)))}</span>", html)
    html = _RE_AB.sub(lambda m: f"<abbr>{m.group(1)}</abbr>", html)
    html = _RE_LS.sub(lambda m: f"<cite>{re.sub('<[^>]+>', '', m.group(1))}</cite>", html)
    html = _RE_ANY_TAG.sub("", html)  # any remaining unhandled tag: strip, keep text
    return re.sub(r"\s+", " ", html).strip()
