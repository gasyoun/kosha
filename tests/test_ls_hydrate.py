"""H3479 — literary-source `<ls>` citation links (H3457 wave 2), PWG only.

Locks:
  * `<span class='ls'>` (with or without a `title`) is hydrated into a link
    exactly when the resolver + registry can place it; `<lshead>`'s identically
    -classed span (different attribute order, no title) is never touched;
  * a resolvable citation is `ls-scan` when its host is `scan_wired` in the
    csl-observatory campaign registry, `ls-etext` otherwise;
  * an unresolvable citation (bare abbreviation or unknown-pattern locus) is
    left byte-identical;
  * absent either sibling checkout, hydration is a no-op — never a crash, never
    an invented link;
  * the default `render_word_page(card)` path (no `ux`) never calls this module
    at all (covered by test_word_page_ux_staging.py's byte-identical lock).
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import ls_hydrate as lh  # noqa: E402

SIBLINGS_PRESENT = (
    (ROOT.parent / "SanskritLexicography" / "RussianTranslation" / "src" / "ls_resolver.py").exists()
    and (ROOT.parent / "csl-observatory" / "data" / "pwg_scan_index_tracker" / "pwg_scan_index.tsv").exists()
)


def test_lshead_span_never_matched():
    """<lshead>'s span (style before class, no title) is a different element —
    the org-wide render.py <ls>/<lshead> distinction must survive hydration."""
    html = "<span style='color:blue;' class='ls'>headword</span>"
    out, stats = lh.hydrate_pwg_ls(html)
    assert out == html
    assert sum(stats.values()) == 0


def test_no_op_when_siblings_absent(monkeypatch):
    monkeypatch.setattr(lh, "_SANSKRIT_LEXICOGRAPHY_SRC", Path("does/not/exist"))
    monkeypatch.setattr(lh, "_SCAN_INDEX_TSV", Path("does/not/exist.tsv"))
    monkeypatch.setattr(lh, "_lsr", None)
    monkeypatch.setattr(lh, "_lsr_load_failed", False)
    monkeypatch.setattr(lh, "_wired_titles", None)
    html = "<span class='ls'>MBH. 12,8081</span> and <span class='ls'>GORR.</span>"
    out, stats = lh.hydrate_pwg_ls(html)
    assert out == html, "no resolver on disk -> untouched, never invented"
    assert stats[lh.MINTABLE] == 1  # has a digit, no resolver to try it against
    assert stats[lh.NO_LOCUS] == 1  # bare abbreviation


@pytest.mark.skipif(not SIBLINGS_PRESENT,
                     reason="SanskritLexicography / csl-observatory siblings not checked out")
def test_bare_abbreviation_is_no_locus_not_mintable():
    html = "<span class='ls'>GORR.</span>"
    out, stats = lh.hydrate_pwg_ls(html)
    assert out == html
    assert stats == {lh.NO_LOCUS: 1}


@pytest.mark.skipif(not SIBLINGS_PRESENT,
                     reason="SanskritLexicography / csl-observatory siblings not checked out")
def test_resolved_citation_gets_a_link_classed_scan_or_etext():
    # YĀJÑ. is a scan_wired campaign row (pwg_scan_index.tsv); resolves to a
    # sanskrit-lexicon-scans.github.io host either way, so this only needs to
    # land in HIT territory with the right visible text preserved.
    html = "<span class='ls'>YĀJÑ. 2,115</span>"
    out, stats = lh.hydrate_pwg_ls(html)
    assert sum(stats.values()) == 1
    assert stats[lh.HIT_SCAN] == 1 or stats[lh.HIT_ETEXT] == 1
    assert '<a class="ls ls-' in out
    assert "YĀJÑ. 2,115" in out
    assert 'href="https://' in out


@pytest.mark.skipif(not SIBLINGS_PRESENT,
                     reason="SanskritLexicography / csl-observatory siblings not checked out")
def test_continuation_citation_with_title_attribute_resolves():
    # render.py emits `<span class='ls' title='N'>` for the n="..." continuation
    # form (LsLinks selftest's own motivating case: n="ṚV." 5,15,4).
    html = "<span class='ls' title='ṚV.'>5,15,4</span>"
    out, stats = lh.hydrate_pwg_ls(html)
    assert stats[lh.HIT_SCAN] + stats[lh.HIT_ETEXT] == 1
    assert "rv05.015" in out
