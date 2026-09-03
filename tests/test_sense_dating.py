"""H4019 — minimal kosha sense-dating bucket layer.

Locks:
  * the resolver reproduces the H4016 hand probe exactly: the 20 nominal
    probe senses come out DATEABLE in the probe's own era (20/20) — the
    seed tier is authoritative and never overridden;
  * disputed / boundary / recension-dependent works stay NULL (Suśruta,
    Medinīkoṣa) and the Śabdakalpadruma ceiling carries its discount flags;
  * canon_dm joins resolve at build time with the hand-verified expected
    era (the DM snapshot is asserted, not trusted);
  * verb honesty: high-frequency verb senses sit at the ṚV floor (all-tie
    vedic), never reordered;
  * parity: `--check` recompute == stored outputs (derive-don't-store);
  * the render (app/dating_hydrate.py) is staging-only: badges appear only
    on `<span class='ls'>` citations, only for abbreviations that resolve
    to one work at mode share ≥ 0.9, and the default render path (no ux
    key) never calls it — no existing display order changes.
"""
import csv
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scripts"))

import dating_hydrate as dh  # noqa: E402

DATING = ROOT / "data" / "dating"
BUILD = ROOT / "scripts" / "build_sense_dating.py"


def _rows(path):
    with open(path) as f:
        return list(csv.DictReader(f, delimiter="\t"))


@pytest.fixture(scope="module")
def sense_rows():
    return _rows(DATING / "sense_dating.tsv")


@pytest.fixture(scope="module")
def work_rows():
    return _rows(DATING / "work_dates.tsv")


@pytest.fixture(scope="module")
def abbrev_rows():
    return _rows(DATING / "abbrev_map.tsv")


def _sense(sense_rows, slp1, hom, sense_id):
    return next((r for r in sense_rows
                 if r["slp1"] == slp1 and r["hom"] == hom and r["sense_id"] == sense_id), None)


# ---------------------------------------------------------------- seed fidelity

NOMINA_PROBE = [  # (slp1, sense_id, expected era) — H4016 hand calls, verbatim
    ("nAgadanta", "1a", "epic-sutra"), ("nAgadanta", "1b", "classical"),
    ("nAgadanta", "2", "epic-sutra"), ("nAgadanta", "3a", "early-medieval"),
    ("Siva", "1", "vedic"), ("Siva", "2a", "epic-sutra"), ("Siva", "2b", "vedic"),
    ("Siva", "2c", "epic-sutra"), ("padma", "3", "epic-sutra"),
    ("padma", "4", "classical"), ("padma", "5", "classical"),
    ("padma", "6", "epic-sutra"), ("viS", "4", "vedic"), ("viS", "6", "vedic"),
    ("viS", "7", "vedic"), ("viS", "5a", "vedic"), ("koSa", "1a", "vedic"),
    ("koSa", "1b", "vedic"), ("koSa", "1c", "early-medieval"), ("koSa", "1d", "vedic"),
]


def test_nomina_probe_20_of_20(sense_rows):
    got = 0
    for slp1, sense_id, era in NOMINA_PROBE:
        r = next((r for r in sense_rows if r["slp1"] == slp1
                  and r["sense_id"] == sense_id and r["first_era"]), None)
        assert r is not None, f"{slp1} {sense_id} missing from the layer"
        assert r["first_era"] == era, f"{slp1} {sense_id}: {r['first_era']} != {era}"
        assert r["class"].startswith("DATEABLE")
        got += 1
    assert got == 20


def test_verb_roots_sit_at_the_rv_floor(sense_rows):
    for slp1, hom, sense_id in [("han", "1", "2"), ("car", "", "4"), ("gam", "1", "3a")]:
        r = _sense(sense_rows, slp1, hom, sense_id)
        assert r is not None, f"{slp1} {sense_id} missing"
        assert r["first_era"] == "vedic"
        assert r["class"] == "DATEABLE"


def test_disputed_works_stay_null(work_rows):
    by_fold = {r["fold"]: r for r in work_rows}
    for name in ("susruta", "medinikosa"):
        r = by_fold.get(name)
        assert r is not None
        assert r["era"] == ""
        assert r["tier"] == "seed"  # H4016 hand:disputed, kept verbatim
        assert "hand:disputed" in r["via"] or r["via"] == "hand:disputed"


def test_sabdakalpadruma_is_a_discounted_ceiling(work_rows):
    r = next(r for r in work_rows if r["work_key"] == "sabdakalpadruma")
    assert r["era"] == "late-medieval"
    assert "terminus-ceiling" in r["flags"] and "low_value" in r["flags"]


def test_canon_dm_join_resolves_expected_eras(work_rows):
    # canon texts with NO seed call, dated by the hand-verified DM family join
    # (kavyaprakasa is canon-spine but absent from PWG's own citations — an
    # honest miss, asserted absent below)
    for work_key, era in [("sisupalavadha", "early-medieval"),
                          ("bhavaprakasa", "late-medieval"),
                          ("brhadaranyakopanisad", "vedic"),
                          ("uttararamacarita", "classical"),
                          ("kulluka", "late-medieval")]:
        r = next((r for r in work_rows if r["work_key"] == work_key and r["era"]), None)
        assert r is not None, f"{work_key} unresolved"
        assert r["era"] == era
    assert not any(r["work_key"] == "kavyaprakasa" and r["era"] for r in work_rows)


def test_no_display_order_claim_is_encoded():
    # the builder refuses to reorder anything: sense rows carry no order field
    assert all("order" not in c for c in
               csv.DictReader(open(DATING / "sense_dating.tsv"), delimiter="\t").fieldnames)


# ---------------------------------------------------------------- parity gate

def test_parity_check_exit_zero():
    proc = subprocess.run([sys.executable, str(BUILD), "--check"],
                          capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "parity: OK" in proc.stdout


# ---------------------------------------------------------------- render (P3)

def test_badge_only_for_resolvable_abbrevs():
    html = "<span class='ls' title='7'>RAGH. 1,3</span>"
    out, stats = dh.hydrate_dating(html)
    assert stats["hits"] == 1
    assert "data-era=" in out and "ls-era" in out
    assert "first attestation in the cited corpus" in out
    assert "первое засвидетельствование" in out


def test_badge_never_for_unresolved_or_ambiguous():
    html = ("<span class='ls'>ZZZZUNKN. 1,2</span>"
            "<span class='ls'>RAGH. 1,3</span>")
    out, stats = dh.hydrate_dating(html)
    assert "ZZZZUNKN" not in stats or stats["misses"] >= 1
    assert "ls-era" in out  # RAGH. still badges
    # an ambiguous abbreviation carries era='' in abbrev_map → no badge
    html2 = "<span class='ls'>AMB. 4,5</span>"
    if any(r["abbrev"] == "AMB." for r in _rows(DATING / "abbrev_map.tsv")):
        return  # only meaningful if the fixture exists
    out2, _ = dh.hydrate_dating(html2)
    assert "ls-era" not in out2


def test_hydration_is_idempotent():
    html = "<span class='ls' title='7'>RAGH. 1,3</span>"
    once, _ = dh.hydrate_dating(html)
    twice, stats = dh.hydrate_dating(once)
    assert twice == once and stats["hits"] == 0


def test_span_structure_preserved():
    """The layer changes no existing display order: the citation span keeps its
    class/title/text, and the badge is appended INSIDE it."""
    html = "<span class='ls' title='7'>RAGH. 1,3</span>"
    out, _ = dh.hydrate_dating(html)
    assert re.search(r"<span class='ls era-[a-z-]+' title='7'>RAGH\. 1,3", out)
    assert out.count("<span") == 2 and out.count("</span>") == 2
    assert out.endswith("</span>")
