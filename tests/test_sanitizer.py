"""W0C — the rendered-HTML trust boundary (H1945, item 6).

Two obligations, and they pull against each other:

1. **Nothing executable survives.** `app/render.py` is a faithful port of
   Cologne's `basicdisplay.php`, including its default branch, which passes any
   unrecognised element through with its attributes — and its `title='{n}'`
   interpolations, which never escaped the source value. Entry HTML is
   interpolated unescaped into the SSR page and `{@html}`-bound in the Svelte
   UI, so anything the renderer emits, a browser runs.
2. **Everything legitimate survives.** Cologne display markup is the product;
   a sanitizer that quietly eats `<span class='sdata'>` would be a data-loss
   bug wearing a security badge. Every removal needs a fixture and a reason.

The adversarial cases below feed hostile *Cologne markup* through the real
`render()` → `sanitize_html()` path, not hand-written HTML, because the
question is what the pipeline emits, not what nh3 does in isolation.
"""

import html as html_lib
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
for extra in (ROOT, ROOT / "src", ROOT / "app"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from kosha.api.sanitize import sanitize_html  # noqa: E402
from kosha.render import render  # noqa: E402

GOLDEN = ROOT / "tests" / "golden"

#: Elements the renderer's passthrough branch would otherwise emit verbatim and
#: that must not reach a page. `pb` is the one *known* real-corpus case (see
#: `test_the_only_loss_on_the_golden_corpus_is_the_page_break_marker`); the rest
#: are what a corrupted or malicious body could carry down the same branch.
ACTIVE_CONTENT = [
    "<script>alert(1)</script>",
    "<script src='//evil.example/x.js'></script>",
    "<iframe src='//evil.example'></iframe>",
    "<object data='x.swf'></object>",
    "<embed src='x.swf'>",
    "<style>body{display:none}</style>",
    "<form action='//evil.example'><input name='p'></form>",
    "<svg><animate onbegin='alert(1)'/></svg>",
    "<math><mtext></mtext></math>",
    "<base href='//evil.example/'>",
    "<meta http-equiv='refresh' content='0;url=//evil.example'>",
]


def _sanitized(markup: str, dict_code: str = "mw") -> str:
    return sanitize_html(render(dict_code, f"<body>{markup}</body>"))


@pytest.mark.parametrize("payload", ACTIVE_CONTENT)
def test_active_content_never_survives(payload):
    out = _sanitized(payload)
    lowered = out.lower()
    for dead in ("<script", "<iframe", "<object", "<embed", "<style",
                 "<form", "<input", "<base", "<meta", "<svg", "onbegin"):
        assert dead not in lowered, f"{dead!r} survived in {out!r}"


def test_script_body_is_dropped_with_its_tag():
    """Unwrapping `<script>` and keeping its text would move the payload into
    the page as content — the classic half-fix."""
    out = _sanitized("<script>alert('pwned')</script>")
    assert "alert" not in out
    assert "pwned" not in out


@pytest.mark.parametrize(
    "payload",
    [
        "<b onclick='alert(1)'>x</b>",
        "<b onmouseover='alert(1)'>x</b>",
        "<div onload='alert(1)'>x</div>",
        "<span onerror='alert(1)'>x</span>",
    ],
)
def test_event_handlers_are_dropped(payload):
    out = _sanitized(payload).lower()
    assert "onclick" not in out and "onmouseover" not in out
    assert "onload" not in out and "onerror" not in out
    assert "alert" not in out


@pytest.mark.parametrize(
    "href",
    [
        "javascript:alert(1)",
        "JaVaScRiPt:alert(1)",
        "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
        "vbscript:msgbox(1)",
        "file:///etc/passwd",
    ],
)
def test_dangerous_url_schemes_are_dropped(href):
    out = _sanitized(f"<a href=\"{href}\">x</a>").lower()
    assert "javascript:" not in out
    assert "vbscript:" not in out
    assert "data:text/html" not in out
    assert "file://" not in out


def test_safe_links_survive_and_are_rel_hardened():
    out = _sanitized("<a href='https://sanskrit-lexicon.uni-koeln.de/x'>scan</a>")
    assert "https://sanskrit-lexicon.uni-koeln.de/x" in out
    # An allowlisted anchor still gets `noopener noreferrer` stamped on it, so a
    # future `<ls>` link layer cannot ship a tabnabbing vector by omission.
    assert "noopener" in out


@pytest.mark.parametrize(
    "style",
    [
        "background:url(javascript:alert(1))",
        "background-image:url('//evil.example/x.png')",
        "width:expression(alert(1))",
        "color:red;behavior:url(#default#time2)",
        "position:fixed;top:0;left:0;width:100%;height:100%",
    ],
)
def test_hostile_css_is_dropped(style):
    """`style` is an attribute nh3 does not parse, so the policy validates it
    declaration by declaration; a value carrying `url(`, `expression(`, or a
    property outside the renderer's own set takes the whole attribute with it."""
    out = _sanitized(f"<span style=\"{style}\">x</span>").lower()
    assert "url(" not in out
    assert "expression(" not in out
    assert "behavior" not in out
    assert "position" not in out
    assert ">x<" in out or "x" in out  # the text itself is never lost


def test_legitimate_renderer_css_survives():
    """The flip side: the styles `render()` actually emits must live."""
    out = sanitize_html("<div style='padding-left:2.0em;'>x</div>")
    assert "padding-left" in out
    out = sanitize_html(
        "<span style='letter-spacing:2px; text-decoration: none; "
        "border-bottom: 1px dotted #000;'>x</span>"
    )
    assert "letter-spacing" in out and "border-bottom" in out


def test_attribute_injection_through_a_source_title_is_escaped():
    """`basicdisplay` interpolates the source's `n=` into `title='…'` with no
    escaping. A body carrying a quote in that attribute could therefore close
    it and open another — the injection this boundary exists to stop."""
    out = _sanitized("<ab n=\"x' onmouseover='alert(1)\">abbr</ab>").lower()
    assert "onmouseover" not in out
    assert "alert(1)" not in out or "title=" in out and "onmouseover" not in out


def test_unknown_tags_are_unwrapped_but_their_text_is_kept():
    """Allowlist, not denylist — an element the renderer was never taught to
    emit is dropped. Its *text* is Cologne's content and must survive."""
    out = _sanitized("<madeup>meaningful text</madeup>")
    assert "meaningful text" in out
    assert "<madeup" not in out


def test_sanitizing_is_idempotent():
    """Cards are sanitized at build time and can be re-serialized later; a
    non-idempotent sanitizer would corrupt anything passing through twice."""
    for case in ACTIVE_CONTENT + ["<b>x</b>", "<span class='sdata'>agni</span>"]:
        once = _sanitized(case)
        assert sanitize_html(once) == once


def test_empty_input_is_preserved():
    assert sanitize_html("") == ""


# --------------------------------------------------------------------------- #
# Protecting legitimate Cologne display markup
# --------------------------------------------------------------------------- #

_TAG_RE = re.compile(r"<\s*([A-Za-z][A-Za-z0-9]*)")
_TEXT_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _golden_files():
    manifest = json.loads((GOLDEN / "manifest.json").read_text(encoding="utf-8"))
    return [(e["dict"], e["L"], GOLDEN / e["file"]) for e in manifest["entries"]]


def _text_of(markup: str) -> str:
    """Reader-facing text, entity-decoded.

    Decoded rather than compared raw because sanitization legitimately
    *normalizes* entities: Cologne bodies carry bare ampersands (`&c.`, the
    printed abbreviation for "etcetera"), which are invalid HTML, and nh3
    escapes them to `&amp;c.`. Both render as `&c.` on screen, so treating that
    as text loss would be wrong — the check is that the reader sees the same
    characters, not that the bytes are identical.
    """
    return _WS_RE.sub(" ", html_lib.unescape(_TEXT_RE.sub("", markup))).strip()


@pytest.mark.parametrize("dict_code,lnum,path", _golden_files())
def test_golden_corpus_keeps_all_of_its_text(dict_code, lnum, path):
    """No reader-facing character may be lost. Text is the dictionary."""
    original = path.read_text(encoding="utf-8")
    assert _text_of(sanitize_html(original)) == _text_of(original)


@pytest.mark.parametrize("dict_code,lnum,path", _golden_files())
def test_the_only_loss_on_the_golden_corpus_is_the_page_break_marker(
    dict_code, lnum, path
):
    """The documented-removal gate.

    Every element in the real rendered corpus must survive sanitization except
    `pb` — Cologne's page-break *metadata*, which `basicdisplay.php` routes to
    its `row1` line and which only reaches `row` at all through the renderer's
    passthrough branch. It is emitted unclosed (`<pb n='720,2'>`), so it is
    also invalid HTML. kosha surfaces the same fact structurally as
    `csl.page`/`csl.scanUrl`, so dropping it loses no information.

    If this test fails for a *new* tag, that tag needs a decision recorded here
    — either it belongs in `ALLOWED_TAGS` or its removal gets a line in this
    docstring. It must never be made to pass by widening the allowlist silently.
    """
    original = path.read_text(encoding="utf-8")
    before = {t.lower() for t in _TAG_RE.findall(original)}
    after = {t.lower() for t in _TAG_RE.findall(sanitize_html(original))}
    assert before - after <= {"pb"}, f"unexpected tag loss: {before - after}"


def test_the_golden_corpus_carries_no_active_content():
    """A sanity check on the corpus itself: if a golden fixture already
    contained a script tag, the tests above would be proving nothing."""
    for _dict_code, _lnum, path in _golden_files():
        lowered = path.read_text(encoding="utf-8").lower()
        assert "<script" not in lowered and "javascript:" not in lowered


def test_served_html_is_sanitized_end_to_end(fixture_client, fixture_lemma):
    """The boundary is only real if no surface can bypass it."""
    response = fixture_client.get(
        f"/api/v1/lemma/{fixture_lemma}", params={"in": "slp1"}
    )
    assert response.status_code == 200
    for entry in response.json()["results"]:
        html = entry["kosha"]["rendered_html"]
        assert sanitize_html(html) == html
