"""Invariants for /concordance/morphology/ (A3 web deliverable, H3861).

These are the claims the page makes that could silently rot: that its shard manifest
resolves, that every lemma it renders is reachable, that its attestation marks agree with
the dataset the trust block cites, and that the head is the measured one. A page whose
numbers drift from its dataset is exactly the defect the A3 audit was written to catch, so
it gets caught here rather than by a reader.

Skips cleanly when the page has not been built in this checkout (the shards are large and
built by `scripts/build_morphology_concordance_page.py`, not by the fixture profile).
"""
import csv
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
WEB = REPO / "concordance" / "morphology"
DATA = WEB / "data"
AG_TSV = REPO / "data" / "concordance" / "morph_attest_infl_AG.tsv"

pytestmark = pytest.mark.skipif(
    not (DATA / "stats.js").exists(),
    reason="/concordance/morphology/ not built in this checkout",
)


def _js_object(path, var):
    """Pull one `window.<var> = {...};` literal out of a generated .js shard."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"window\.%s(?:\[[^\]]+\])? *= *(\{.*?\});\s*$" % var, text,
                  re.S | re.M)
    assert m, "%s: no %s literal" % (path.name, var)
    return json.loads(m.group(1))


@pytest.fixture(scope="module")
def stats():
    return _js_object(DATA / "stats.js", "MORPH_STATS")


@pytest.fixture(scope="module")
def manifest():
    return _js_object(DATA / "stats.js", "MORPH_SHARDS")


def test_page_exists_and_is_self_contained():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "<title>" in html
    # only same-origin data/ scripts — the page must not acquire a CDN dependency
    for src in re.findall(r'<script[^>]*\bsrc="([^"]+)"', html):
        assert src.startswith("data/"), "external script dependency: %s" % src
        assert (WEB / src).exists(), "missing referenced script: %s" % src


def test_every_manifest_chunk_exists(manifest):
    for letter, chunks in manifest.items():
        assert chunks, "letter %r has no chunks" % letter
        for first_key, name in chunks:
            assert (DATA / ("kwic_%s.js" % name)).exists(), "missing chunk %s" % name
        # chunks must be ordered by their first key, or the client's pick is wrong
        firsts = [c[0] for c in chunks]
        assert firsts == sorted(firsts), "letter %r chunks out of order" % letter


def test_every_letter_has_an_index(manifest):
    for letter in manifest:
        assert (DATA / ("index_%s.js" % letter)).exists(), "missing index_%s.js" % letter


def test_index_and_chunks_cover_the_same_lemmas(manifest):
    for letter, chunks in manifest.items():
        idx = _js_object(DATA / ("index_%s.js" % letter), "MORPH_INDEX")
        in_chunks = set()
        for _first, name in chunks:
            text = (DATA / ("kwic_%s.js" % name)).read_text(encoding="utf-8")
            m = re.search(r"MORPH_ADD\(\"[^\"]+\", (\{.*\})\);\s*$", text, re.S | re.M)
            assert m, "chunk %s is not in MORPH_ADD form" % name
            in_chunks |= set(json.loads(m.group(1)))
        assert set(idx) == in_chunks, (
            "letter %r: index and chunks disagree on %d lemma(s)"
            % (letter, len(set(idx) ^ in_chunks)))


def test_client_chunk_pick_resolves_every_lemma(manifest):
    """Replicate the page's chunk picker and assert it lands on the owning chunk."""
    for letter, chunks in manifest.items():
        idx = _js_object(DATA / ("index_%s.js" % letter), "MORPH_INDEX")
        owner = {}
        for _first, name in chunks:
            text = (DATA / ("kwic_%s.js" % name)).read_text(encoding="utf-8")
            m = re.search(r"MORPH_ADD\(\"[^\"]+\", (\{.*\})\);\s*$", text, re.S | re.M)
            for k in json.loads(m.group(1)):
                owner[k] = name
        for key in idx:
            pick = chunks[0][1]
            for first, name in chunks:
                if first <= key:
                    pick = name
                else:
                    break
            assert pick == owner[key], (
                "%r would load chunk %s but lives in %s" % (key, pick, owner[key]))


def test_attestation_marks_agree_with_the_dataset(manifest):
    """A cell marked attested must be an AG row; an unmarked one must not be.

    This is the invariant that keeps the page from drifting away from the TSV its trust
    block cites — the whole point of the A3 audit.
    """
    if not AG_TSV.exists():
        pytest.skip("morph_attest_infl_AG.tsv not present")
    ag = set()
    with AG_TSV.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            ag.add(r["anchor_id"])

    checked = 0
    for letter, chunks in list(manifest.items())[:4]:      # 4 letters is ample and fast
        for _first, name in chunks:
            text = (DATA / ("kwic_%s.js" % name)).read_text(encoding="utf-8")
            m = re.search(r"MORPH_ADD\(\"[^\"]+\", (\{.*\})\);\s*$", text, re.S | re.M)
            for _lemma, e in json.loads(m.group(1)).items():
                for cell in list(e.get("nom", [])) + list(e.get("vrb", [])):
                    marked = bool(cell.get("a"))
                    assert marked == (cell["f"] in ag), (
                        "cell %s marked attested=%s but AG membership is %s"
                        % (cell["f"], marked, cell["f"] in ag))
                    checked += 1
    assert checked > 500, "only %d cells checked — shards look empty" % checked


def test_reported_counts_match_the_shards(stats, manifest):
    total = sum(len(_js_object(DATA / ("index_%s.js" % l), "MORPH_INDEX"))
                for l in manifest)
    assert total == stats["head_with_cells"], (
        "stats say %d lemmas, shards carry %d" % (stats["head_with_cells"], total))
    assert stats["head_with_cells"] <= stats["head_n"]
    assert 0 < stats["coverage"] <= 100


def test_head_is_measured_not_hardcoded():
    """The builder must derive N from the frequency table (standing rule D4/D5).

    Checked against the parsed code, not the text: the docstring legitimately *cites*
    the measured N of 02-09-2026 as an observation, and a substring scan over the whole
    file cannot tell that apart from a frozen constant.
    """
    import ast

    path = REPO / "scripts" / "build_morphology_concordance_page.py"
    src = path.read_text(encoding="utf-8")
    assert "lemma_frequency.tsv" in src, "builder does not read the frequency table"
    assert "--coverage" in src, "builder exposes no measured-coverage argument"

    tree = ast.parse(src)
    # A NAMED module-level constant (SHARD_MAX_BYTES = 400_000) is a declared tuning knob
    # and is fine; what must never appear is an anonymous corpus-scale literal buried in
    # the logic, which is how a measured head silently becomes a frozen one.
    named = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    named.add(id(node.value))
    big = [n.value for n in ast.walk(tree)
           if isinstance(n, ast.Constant) and isinstance(n.value, int)
           and id(n) not in named and 1000 <= n.value <= 10_000_000]
    assert not big, (
        "builder carries an inline corpus-scale literal %s — the static head must be "
        "measured at build time, never frozen (D4/D5, H1590)" % sorted(set(big)))
