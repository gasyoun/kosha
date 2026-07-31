"""kosha — the rendered-HTML trust boundary (W0C item 6, H1945).

`app/render.py` is a faithful port of Cologne's `basicdisplay.php`, and that
faithfulness is the problem: the PHP's default branch passes *any* unrecognised
element straight through with its attributes, and several handlers interpolate
source-XML attribute values (`n=`) into `title='…'` without escaping. Cologne
markup is trusted upstream text, but "trusted" is not "verified" — an entry
body is 19th-century typesetting run through a century of OCR, hand-correction
and conversion, and the renderer will happily emit whatever it finds. The
served surface must not depend on that.

So the entry HTML crosses exactly one boundary before it reaches a client, and
this module is it: an **allowlist** built with
[nh3](https://pypi.org/project/nh3/) — the maintained Python binding to Rust's
`ammonia`, which `bleach` itself now redirects users to. Allowlist, never
denylist: an element the renderer has never been taught to emit is dropped
rather than trusted, so a new tag appearing in a corrected upstream file cannot
widen the served surface without a deliberate change here.

**What this is not.** It is not a markup fixer and not an upstream edit. The
raw Cologne body is stored and served unchanged (`?raw=1`, `kosha.raw`,
`csl.xmlCsl`); only the *rendered* HTML is sanitized. The two stay separable on
purpose — a scholar auditing what Cologne actually prints reads the raw field,
not our render of it.

**Protecting legitimate display markup.** The allowlist is derived from what
`render.py` actually emits, and `tests/test_sanitizer.py` proves it against the
committed golden corpus: every golden fixture must survive sanitization
unchanged except for one documented removal (`<pb n='…'>`, an unclosed
page-break *metadata* element the PHP routes to its `row1` line and kosha
surfaces structurally as `page`/`scan_url`). Any future removal needs the same
treatment — a fixture and a line in that test, not a silent drop.
"""

from __future__ import annotations

import re

import nh3

#: Elements `app/render.py` emits. Anything else is unwrapped (content kept)
#: or, for the content-bearing dangerous set below, dropped whole.
ALLOWED_TAGS: frozenset[str] = frozenset(
    {
        # inline emphasis / structure the PHP emits
        "strong", "b", "i", "em", "sup", "sub", "span", "br", "div", "p",
        # tables: basicdisplay passes table/tr/td/th through with attributes
        "table", "thead", "tbody", "tr", "td", "th", "hr",
        # anchors: `<ls>` citation links are the documented D3 follow-on; the
        # allowlist is ready for them so shipping that layer is not also a
        # security change.
        "a",
    }
)

#: Per-tag attribute allowlist. `style`/`class`/`title` carry the renderer's
#: own presentation; every value is still checked by `_filter_attribute`.
ALLOWED_ATTRIBUTES: dict[str, set[str]] = {
    "span": {"class", "style", "title"},
    "div": {"class", "style"},
    "p": {"class", "style"},
    # `rel` is deliberately absent: `link_rel` below stamps
    # `noopener noreferrer` on every anchor, and nh3 refuses to let the
    # allowlist and that setting both own the attribute.
    "a": {"href", "title", "target", "class"},
    "table": {"class", "style"},
    "tr": {"class", "style"},
    "td": {"class", "style", "colspan", "rowspan"},
    "th": {"class", "style", "colspan", "rowspan"},
    "strong": {"class"},
    "b": {"class"},
    "i": {"class"},
    "em": {"class"},
    "sup": {"class"},
    "sub": {"class"},
}

#: Tags whose *content* is dropped with them. ammonia's default already covers
#: script/style; naming them here keeps the policy readable rather than
#: implied.
CLEAN_CONTENT_TAGS: frozenset[str] = frozenset(
    {"script", "style", "iframe", "object", "embed", "noscript", "template"}
)

#: URL schemes an `href` may use. No `javascript:`, no `data:` — the two that
#: turn a link into script execution.
ALLOWED_URL_SCHEMES: frozenset[str] = frozenset({"http", "https", "mailto"})

#: CSS properties the renderer emits (`_div`, the `is`/`bot`/`zoo`/`ab`
#: handlers, `alt`, `lshead`). `style` is an attribute nh3 does not parse, so
#: it is validated here declaration by declaration instead of trusted.
ALLOWED_CSS_PROPERTIES: frozenset[str] = frozenset(
    {
        "color", "padding-left", "margin-top", "margin-bottom", "font-size",
        "font-weight", "font-style", "letter-spacing", "text-decoration",
        "border-bottom", "text-align", "vertical-align",
    }
)

#: A CSS value may only be words, numbers, units, hashes and commas — enough
#: for `1px dotted #000` or `smaller`, not enough for `url(...)`,
#: `expression(...)`, or an escaped-hex payload.
_CSS_VALUE_RE = re.compile(r"^[A-Za-z0-9 ,.%#()/_-]+$")
_CSS_FORBIDDEN_RE = re.compile(r"(?i)(url\s*\(|expression\s*\(|@import|/\*|\\)")

#: `class` is presentational and comes from the renderer's own fixed strings;
#: a token that is not a plain identifier is not one of ours.
_CLASS_RE = re.compile(r"^[A-Za-z0-9 _-]+$")


def _safe_style(value: str) -> str | None:
    """Keep only declarations whose property is allowlisted and whose value is
    inert. Returns None when nothing survives, so the attribute is dropped
    rather than emitted empty."""
    if _CSS_FORBIDDEN_RE.search(value):
        return None
    kept = []
    for declaration in value.split(";"):
        if not declaration.strip():
            continue
        prop, sep, val = declaration.partition(":")
        if not sep:
            return None
        prop = prop.strip().lower()
        val = val.strip()
        if prop not in ALLOWED_CSS_PROPERTIES:
            return None
        if not val or not _CSS_VALUE_RE.match(val):
            return None
        kept.append(f"{prop}: {val}")
    return "; ".join(kept) or None


def _filter_attribute(tag: str, attribute: str, value: str) -> str | None:
    """nh3 attribute filter: the value-level half of the policy.

    nh3 decides *whether* an attribute may appear; this decides whether the
    value it carries is acceptable. Returning None drops the attribute.
    """
    if attribute == "style":
        return _safe_style(value)
    if attribute == "class":
        return value if _CLASS_RE.match(value) else None
    if attribute == "target":
        # A renderer-emitted target is always _blank; anything else is not ours.
        return "_blank" if value == "_blank" else None
    if attribute in {"colspan", "rowspan"}:
        return value if value.isdigit() and len(value) <= 3 else None
    # `title`/`href`/`rel` — href scheme is enforced by nh3's url_schemes; the
    # remaining risk in `title` is only text, which nh3 escapes.
    return value


def sanitize_html(html: str) -> str:
    """Apply the allowlist to one block of rendered entry HTML.

    Idempotent: sanitizing already-sanitized output returns it unchanged, which
    `tests/test_sanitizer.py` pins — a sanitizer that is not idempotent silently
    corrupts anything that passes through it twice.
    """
    if not html:
        return html
    return nh3.clean(
        html,
        tags=set(ALLOWED_TAGS),
        clean_content_tags=set(CLEAN_CONTENT_TAGS),
        attributes={tag: set(attrs) for tag, attrs in ALLOWED_ATTRIBUTES.items()},
        url_schemes=set(ALLOWED_URL_SCHEMES),
        attribute_filter=_filter_attribute,
        strip_comments=True,
        link_rel="noopener noreferrer",
    )
