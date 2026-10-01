"""W4a polish — XSS-hardening regression gate for the panini concordance page.

Mirrors the H5545 colocation battery (tests/test_colocation_page_security.py)
for the hand-authored concordance/panini/index.html (W2b/H1585 vintage, polished
in the W4a drain pass). The page's data sinks are fed by build-generated shards
(concordance/panini/data/*.js), so the pins are:

  1. hardened esc() — quote-escaping (&#39;/&quot;), so attribute-context
     interpolations cannot break out of double quotes;
  2. static sink coverage — every data-bearing attribute interpolation in the
     render paths passes through esc(); no data-first href concatenation;
  3. JS syntax gate — the embedded <script> must parse (node --check);
  4. behavioral eval — esc() neutralizes markup/attr breakouts in node;
  5. polish affordances — coverage show-all button present.

Local-only (matches this suite's convention); node parts skip if node absent.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PAGE = REPO / "concordance" / "panini" / "index.html"

HAS_NODE = shutil.which("node") is not None


def _page_src() -> str:
    assert PAGE.exists(), f"page missing: {PAGE}"
    return PAGE.read_text(encoding="utf-8")


# ---------------------------------------------------------------- 1. esc()

def test_esc_covers_single_and_double_quote():
    src = _page_src()
    m = re.search(r"^function esc\(.*$", src, re.M)
    assert m, "esc() not found"
    body = m.group(0)
    assert "/[&<>\"']/" in body, "esc() must escape both quote flavors"
    assert "&#39;" in body, "esc() must map ' to &#39;"
    assert "&quot;" in body, "esc() must map \" to &quot;"
    # the old DOM-based esc did not escape quotes — it must be gone
    assert "createElement" not in body, "esc() must be the replace-based form"


# --------------------------------------------------------- 2. static sinks

def test_attribute_sinks_pass_through_esc():
    src = _page_src()
    for marker in (
        'href="#\'+esc(c)+\'"',
        '" data-c="\'+esc(c)+\'"',
        'data-id="\'+esc(r.id)+\'"',
        'data-status="\'+esc(r.status)+\'"',
        '\' + esc(fm.chain_id) + \'" data-target',
        'esc(shard[c].n_forms)',
        'esc(r.forms||0)',
        'esc(e.n_forms)',
    ):
        assert marker in src, f"attribute/data sink missing esc(): {marker}"


def test_no_data_first_href_concatenation():
    """Every href must start from a literal fragment (#) — never raw data."""
    src = _page_src()
    assert re.search(r"href=\"'\+", src) is None, \
        "data-first href concatenation found (href=\"'+...)"


# ------------------------------------------------------- 3. JS syntax gate

def _embedded_script(src: str) -> str:
    m = re.search(r"<script>(.*)</script>", src, re.S)
    assert m, "embedded <script> block not found"
    return m.group(1)


@pytest.mark.skipif(not HAS_NODE, reason="node not available")
def test_embedded_script_parses():
    script = _embedded_script(_page_src())
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8") as f:
        f.write(script)
        path = f.name
    r = subprocess.run(["node", "--check", path], capture_output=True, text=True)
    assert r.returncode == 0, f"page script has a JS syntax error:\n{r.stderr}"


# --------------------------------------------------------- 4. behavior eval

@pytest.mark.skipif(not HAS_NODE, reason="node not available")
def test_esc_behavior():
    src = _page_src()
    m = re.search(r"^function esc\(.*$", src, re.M)
    assert m, "esc() not found in page"
    harness = (
        m.group(0)
        + "\nconst cases=" + json.dumps({
            "esc_script": "<script>alert(1)</script>",
            "esc_attr_breakout": '" onmouseover="alert(1)',
            "esc_single_quote": "it's",
            "esc_amp": "a&b",
            "esc_sutra_code": '1.2.45"><script>alert(1)</script>',
        }) + """
const out={};
for (const [k,arg] of Object.entries(cases)) out[k]=esc(arg);
process.stdout.write(JSON.stringify(out));
"""
    )
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8") as f:
        f.write(harness)
        path = f.name
    r = subprocess.run(["node", path], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, f"node harness failed:\n{r.stderr}"
    out = json.loads(r.stdout)

    assert "<script>" not in out["esc_script"]
    assert "&lt;script&gt;" in out["esc_script"]
    assert '"' not in out["esc_attr_breakout"]
    assert "&quot;" in out["esc_attr_breakout"]
    assert out["esc_single_quote"] == "it&#39;s"
    assert out["esc_amp"] == "a&amp;b"
    # a shard value crafted to escape a double-quoted attribute stays inert
    assert out["esc_sutra_code"] == "1.2.45&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;"


# ------------------------------------------------------- 5. polish affordances

def test_polish_affordances_present():
    src = _page_src()
    # coverage table show-all beyond the 500-row cutoff
    assert "cov-more" in src
    # trust block carries CSV fallback for both data TSVs (house /viz-page)
    for tsv in ("paninian_concordance.tsv", "derivation_status.tsv"):
        assert re.search(
            rf'raw\.githubusercontent\.com/gasyoun/kosha/main/data/concordance/{re.escape(tsv)}"[^>]*download=',
            src,
        ), f"CSV download affordance missing for {tsv}"
    # KWIC adhyāya buttons carry honest lit counts from the coverage map
    assert "LIT_BY_ADHY" in src


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
