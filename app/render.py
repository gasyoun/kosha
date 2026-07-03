"""kosha D4/A1 — render(dict, body) -> html.

A **code-level faithful port** of the mw/pwg/ap90 display path of
csl-websanlexicon's canonical template
(`v02/makotemplates/web/webtc/basicadjust.php` + `basicdisplay.php`,
SHARED_CODE.md family #5 — ported from the makotemplates *template*, never a
drifted per-dict copy). basicdisplay.php is a SAX (`xml_parse`) engine whose
`sthndl`/`chrhndl`/`endhndl` build an HTML string; this module reimplements it
with Python's expat parser, branch-for-branch for the tags that occur in
mw/pwg/ap90 bodies.

**Scope of the port — what render() returns.** basicdisplay builds two pieces:
`row` (the entry prose HTML) and `row1`/`row1x` (a metadata line: Cologne
record ID, "Printed book page" link, MW Whitney/Westergaard links).
`render()` returns **`row`** — the reader-facing entry text. The `row1`
metadata is intentionally excluded: kosha surfaces the record ID, scan link,
and cross-reference targets as *structured* fields (`L`, `scan_url`,
`sense_ids`, the Salt `csl` block), not baked into `rendered_html`. This is the
same row/row1 split the PHP makes, drawn at kosha's API boundary.

**Two documented deviations from the live PHP** (grounded, not silent):

1. **`<s>` transliteration is server-side (sanskrit-util), not client-JS.**
   The PHP emits `<span class='sdata'><SA>slp1</SA></span>` and a browser font
   + JS transcoder renders it; kosha (ARCHITECTURE.md A1 "Transliteration of
   `<s>` spans via sanskrit-util") emits `<span class='sdata'>IAST</span>`
   directly. SLP1 pitch accents (`/ ^ \\`) are stripped first, matching the
   PHP display default (`accent != "yes"`, basicadjust `remove_slp1_accent`).

2. **DB-backed tooltips and external `<ls>` hyperlinks are not resolved here.**
   basicadjust's `abbrv_callback`/`add_lex_markup` add abbreviation tooltips
   from per-dict `Xab.sqlite`, and `ls_callback_mw`/`ls_callback_pwg` wrap
   `<ls>` citations in `<gralink>` links to external scan viewers via hundreds
   of per-text URL builders + the `authtooltips` DB. kosha has neither DB
   locally (builds never call live services, RISKS.md R12), and the `<ls>`
   citation-link resolution is the separately-owned ls_resolver.py D3 follow-on
   (data/SOURCES.md D3). So `<ab>`/`<lex>` render as their text without a
   tooltip and `<ls>` renders as `<span class='ls'>text</span>` without an
   href — structurally faithful, minus the enrichment those DBs provide.

These are the honest boundaries; everything else mirrors the PHP emissions.
"""
import re
import sys
from pathlib import Path
from xml.parsers import expat

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "sanskrit-util" / "py"))
from sanskrit_util import from_slp1  # noqa: E402

# SLP1 pitch-accent marks stripped before transliteration (basicadjust
# remove_slp1_accent, display default accent != "yes").
_RE_ACCENT = re.compile(r"[/^\\]")


def _translit_s(slp1_text: str) -> str:
    return from_slp1(_RE_ACCENT.sub("", slp1_text))


# ---------------------------------------------------------------------------
# adjust() — the pre-display markup passes from basicadjust.php that apply to
# mw/pwg/ap90 and shape the *structure* of the display (not the DB tooltips or
# external ls-hrefs, which are documented deferrals above).
# ---------------------------------------------------------------------------

_RE_BAR = re.compile("¦")
_RE_HOM_IN_HEAD = re.compile(r"<key2>(.*?)<hom>.*?</hom>(.*?<body>)", re.S)
_RE_MW_LANG = re.compile(r"<lang(.*?)>(.*?)</lang>", re.S)
_RE_MW_S1N = re.compile(r'<s1( n=".*?")>(.*?)</s1>', re.S)
_RE_PWG_LANG = re.compile(r"<lang>(.*?)</lang>", re.S)
_RE_MW_VP_BOLD = re.compile(r'(<div n="vp"/> *)(<ab.*?</ab>)', re.S)
_RE_MW_SQRT = re.compile("√ ")


def adjust(dict_code: str, line: str) -> str:
    """Ported basicadjust.line_adjust, restricted to the passes that affect
    mw/pwg/ap90 display structure. Order follows the PHP."""
    line = _RE_BAR.sub(" ", line)  # all dicts
    if dict_code == "mw":
        # <lang ...>X</lang> -> <ab ...>X</ab> (04-08-2024)
        line = _RE_MW_LANG.sub(r"<ab\1>\2</ab>", line)
        # <s1 n="X">Y</s1> -> <ab n="X">Y</ab> (08-21-2024, tooltip)
        line = _RE_MW_S1N.sub(r"<ab\1>\2</ab>", line)
    elif dict_code == "pwg":
        # <lang>X</lang> -> <ab>X</ab> (06-14-2026)
        line = _RE_PWG_LANG.sub(r"<ab>\1</ab>", line)
    # remove <hom>X</hom> within the head portion, all dicts with <h> metaline
    line = _RE_HOM_IN_HEAD.sub(r"<key2>\1\2", line)
    if dict_code == "mw":
        # bold the abbreviation after <div n="vp"/> (verb-paradigm header)
        line = _RE_MW_VP_BOLD.sub(r"\1<b>\2</b>", line)
        line = _RE_MW_SQRT.sub("√", line)
    return line


# ---------------------------------------------------------------------------
# display() — expat SAX port of basicdisplay.php, producing `row`.
# ---------------------------------------------------------------------------

# Tags whose character data is suppressed from `row` (head/metadata: key1/key2
# never print; L/pc/pb data go to row1, which render() omits).
_SUPPRESS_TEXT = {"key1", "key2", "L", "pc", "pb", "hom_head"}


class _Display:
    def __init__(self, dict_code: str):
        self.dict = dict_code
        self.row = []
        self.parent = ""
        self.sdata = "sdata"

    # -- start tag --------------------------------------------------------
    def start(self, el, attribs):
        self.parent = el
        d = self.dict
        row = self.row
        if re.match(r"^H.+$", el):
            # Hn markers go to row1 for MW (record head); row gets nothing.
            return
        if el == "s":
            return  # transliteration happens in char data
        if el in ("key1", "key2", "h", "body", "tail", "L", "pc", "info",
                  "hom", "lbinfo", "s1", "symbol", "hwtype", "edit", "sic",
                  "vlex", "ns", "to", "shortlong", "srs", "pcol", "nsi"):
            # no start-tag emission (some carry char-data handled in chrhndl)
            return
        if el in ("b", "lex"):
            row.append("<strong>")
        elif el == "i":
            row.append("<i>")
        elif el == "br":
            row.append("<br/>")
        elif el == "etym":
            row.append("<i>")
        elif el == "div":
            row.append(self._div(attribs))
        elif el == "ls":
            n = attribs.get("n")
            if n is not None:
                row.append(f"<span class='ls' title='{n}'>")
            else:
                row.append("&nbsp;<span class='ls'>")
        elif el == "ab":
            n = attribs.get("n")
            if n is not None:
                style = "border-bottom: 1px dotted #000; text-decoration: none;"
                row.append(f"<span title='{n}' style='{style}'>")
            else:
                row.append("<span>")
        elif el == "sup":
            row.append("<sup>")
        elif el == "alt":
            row.append("<span style='font-size:smaller'>(")
        elif el == "lshead":
            row.append("<span style='color:blue;' class='ls'>")
        elif el == "is":
            n = attribs.get("n")
            if n is not None:
                style = "letter-spacing:2px; text-decoration: none; border-bottom: 1px dotted #000;"
                row.append(f"<span title='{n}' style='{style}'>")
            else:
                row.append("<span style='letter-spacing:2px;'>")
        elif el in ("bot", "zoo"):
            n = attribs.get("n")
            if n is not None:
                style = "color: brown; text-decoration: none; border-bottom: 1px dotted #000;"
                row.append(f"<span title='{n}' style='{style}'>")
            else:
                row.append("<span style='color: brown;'>")
        elif el == "bio":
            row.append("<span style='color: brown'>")
        elif el == "lb":
            row.append("<br/>")
        elif el == "F":
            row.append("<br/>[<span style='font-weight:bold;'>Footnote: </span><span>")
        elif el == "C":
            row.append(f"<strong>(C{attribs.get('n', '')})</strong>")
        elif el == "span":
            t = "<span"
            for a in ("class", "style", "title"):
                if a in attribs:
                    t += f" {a}='{attribs[a]}'"
            row.append(t + ">")
        elif el == "lang":
            pass  # char data handled in chrhndl (MW italic Greek)
        elif el in ("gk", "fr", "ger", "tib", "toch", "lat", "arab", "rus", "mong"):
            titles = {"gk": "Greek script" if d == "mw" else "Greek language",
                      "fr": "French language", "ger": "German language",
                      "tib": "Tibetan language", "toch": "Tocharian language",
                      "lat": "Latin language", "arab": "Arabic language",
                      "rus": "Russian language", "mong": "Mongolian language"}
            row.append(f"<span style='color: brown;' title='{titles[el]}'>")
        elif el in ("table", "tr", "td", "th", "hr"):
            a = "".join(f" {k}='{v}'" for k, v in attribs.items())
            row.append(f"<{el}{a}>")
        else:
            # unrecognized element: passthrough (basicdisplay default branch)
            a = " ".join(f"{k}='{v}'" for k, v in attribs.items())
            row.append(f"<{el} {a}>" if a else f"<{el}>")

    def _div(self, attribs):
        n = attribs.get("n")
        d = self.dict
        if d == "pwg":
            indent = {"1": "1.0em", "2": "2.0em", "3": "3.0em"}.get(n, "0.1em")
            return f"<div style='padding-left:{indent};'>"
        # mw and ap90 fall to basicdisplay's default div branch
        return "<div style='margin-top:0.6em;'></div>"

    # -- character data ---------------------------------------------------
    def char(self, data):
        p = self.parent
        row = self.row
        if p in ("key1", "key2"):
            return
        if p == "s":
            row.append(f"<span class='{self.sdata}'>{_translit_s(data)}</span>")
        elif p == "hom":
            row.append(f"<span class='hom' title='Homonym'>{data}</span>")
        elif p == "lang":
            row.append(f"<i>{data}</i>" if self.dict == "mw" else data)
        elif p in ("L", "pc", "pb", "pcol", "pref", "cref", "L1"):
            return  # metadata -> row1 in PHP; render() omits row1
        else:
            row.append(data)

    # -- end tag ----------------------------------------------------------
    def end(self, el):
        self.parent = ""
        row = self.row
        if el in ("b", "lex"):
            row.append("</strong>")
        elif el == "i":
            row.append("</i>")
        elif el == "etym":
            row.append("</i>")
        elif el == "div":
            row.append("</div>")
        elif el == "alt":
            row.append(")</span><br/>")
        elif el == "sup":
            row.append("</sup>")
        elif el == "ls":
            row.append("</span>&nbsp;")
        elif el == "F":
            row.append("]</span>&nbsp;<br/>")
        elif el in ("span", "is", "bot", "zoo", "bio", "ab", "lshead"):
            row.append("</span>")
        elif el in ("gk", "fr", "ger", "tib", "toch", "lat", "arab", "rus", "mong"):
            row.append("</span>")
        elif el == "table":
            row.append("</table>")
        elif el in ("tr", "td", "th"):
            row.append(f"</{el}>")
        elif el in ("br", "lb", "hr"):
            return
        elif el in ("s", "L", "key1", "key2", "h", "info", "tail", "pc", "body",
                    "hom", "pb", "lbinfo", "s1", "symbol", "hwtype", "edit",
                    "sic", "vlex", "ns", "to", "shortlong", "srs", "pcol", "nsi",
                    "lang", "C"):
            return
        elif re.match(r"^H.+$", el):
            return
        else:
            row.append(f"</{el}>")


def display(dict_code: str, record: str) -> str:
    d = _Display(dict_code)
    p = expat.ParserCreate("UTF-8")
    p.ordered_attributes = False
    p.StartElementHandler = d.start
    p.CharacterDataHandler = d.char
    p.EndElementHandler = d.end
    try:
        p.Parse(record, True)
    except expat.ExpatError:
        # basicdisplay's fallback: strip tags, degrade gracefully (never blank).
        text = re.sub(r"<[^>]+>", "", record)
        return re.sub(r"\s+", " ", text).strip()
    return re.sub(r"[ \t]+", " ", "".join(d.row)).strip()


def render(dict_code: str, body: str) -> str:
    """Render a csl-orig record (or a sense span of one) to entry-prose HTML.
    `body` is either a full `<H1>…</H1>` record (lemma/entry rendering) or a
    sense-span fragment of one (`/api/v1/sense`). A fragment is wrapped in a
    synthetic `<body>` root so expat has a single well-formed root; a full
    record (root `<H…>` or `<body…>`) is parsed as-is."""
    adjusted = adjust(dict_code, body)
    stripped = adjusted.lstrip()
    if not (stripped.startswith("<H") or stripped.startswith("<body")):
        adjusted = f"<body>{adjusted}</body>"
    return display(dict_code, adjusted)
