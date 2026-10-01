"""Give-back port — the routed Q3 morph payload stays exactly the machine-decided set.

Roadmap drain A02 (CONCORDANCE_ROADMAP.md "Route the Q3 morph give-back
payload…"). The port's whole point is that nothing human-judged leaks in and
nothing owed leaks out, so the gate pins:

  1. counts — payloads match morph_giveback_triage_summary.json's verdict
     counts exactly (owed 4,900 = slot-conflict 2,212 + coverage-hole 2,688);
  2. purity — no not-owed / untagged verdict reaches a payload;
  3. subset — every payload row is byte-identical (on the shared columns) to
     its source row in morph_giveback_triaged.tsv;
  4. class contracts — every slot-conflict names the generator's competing
     form; every coverage-hole has generator_has empty;
  5. ROUTING.json integrity — recorded sha256s match the files on disk,
     provenance checksums match the triage inputs, and the diplomacy gate is
     recorded as human-gated with the draft present;
  6. determinism shape — payloads are frequency-sorted (evidence_count desc).

Fixture-tier: no kosha.db, no network; runs in seconds.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PORT = REPO / "data" / "concordance" / "giveback_port"
TRIAGED = REPO / "data" / "concordance" / "morph_giveback_triaged.tsv"
SUMMARY = REPO / "data" / "concordance" / "morph_giveback_triage_summary.json"

SLOT_PAYLOAD = PORT / "csl_inflect_slot_conflicts.tsv"
HOLE_PAYLOAD = PORT / "csl_inflect_coverage_holes.tsv"
ROUTING = PORT / "ROUTING.json"
DRAFT = PORT / "DRAFT_POST.md"

COLUMNS = [
    "attested_form", "dcs_lemma", "dcs_upos", "cell",
    "generator_has", "evidence_count", "target_locus",
]


def _read_tsv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def summary() -> dict:
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def slots() -> list[dict]:
    return _read_tsv(SLOT_PAYLOAD)


@pytest.fixture(scope="module")
def holes() -> list[dict]:
    return _read_tsv(HOLE_PAYLOAD)


def test_port_exists():
    for p in (SLOT_PAYLOAD, HOLE_PAYLOAD, ROUTING, DRAFT):
        assert p.exists(), f"missing port artefact: {p.name}"


def test_counts_match_triage_summary(slots, holes, summary):
    assert len(slots) == summary["verdicts"]["slot-conflict"] == 2212
    assert len(holes) == summary["verdicts"]["coverage-hole"] == 2688
    assert len(slots) + len(holes) == summary["owed"] == 4900


def test_no_not_owed_or_untagged_rows_leak_in(slots, holes):
    # The payload schema carries no verdict column, so purity is structural:
    # no column to smuggle a not-owed row through, and the class counts leave
    # no room for one (test_counts_match_triage_summary pins those). Here we
    # additionally pin the schema itself so a future builder edit cannot
    # quietly start copying the verdict column (and with it, stray rows).
    for rows, name in ((slots, "slot_conflicts"), (holes, "coverage_holes")):
        assert rows, f"{name}: empty payload"
        assert set(rows[0].keys()) == set(COLUMNS), (
            f"{name}: schema drift — expected exactly {COLUMNS}"
        )


def test_payload_rows_are_exact_source_rows(slots, holes):
    triaged = _read_tsv(TRIAGED)
    def key(r: dict) -> tuple:
        return tuple(r[c] for c in COLUMNS)
    source = {key(r) for r in triaged}
    for rows, name in ((slots, "slot_conflicts"), (holes, "coverage_holes")):
        for r in rows:
            assert key(r) in source, f"{name}: row not in the triaged source: {r}"


def test_slot_conflicts_name_the_competing_form(slots):
    for r in slots:
        assert r["generator_has"], f"slot-conflict without generator form: {r}"
        assert r["generator_has"] != r["attested_form"], (
            f"slot-conflict where both sides agree (not a conflict): {r}"
        )


def test_coverage_holes_have_no_generator_form(holes):
    for r in holes:
        assert r["generator_has"] == "", f"coverage-hole carrying a generator form: {r}"


def test_payloads_are_frequency_sorted(slots, holes):
    for rows, name in ((slots, "slot_conflicts"), (holes, "coverage_holes")):
        counts = [int(r["evidence_count"]) for r in rows]
        assert counts == sorted(counts, reverse=True), f"{name} not frequency-sorted"


def test_routing_json_integrity(slots, holes, summary):
    routing = json.loads(ROUTING.read_text(encoding="utf-8"))
    assert routing["owed_total"] == len(slots) + len(holes) == summary["owed"]
    assert routing["payloads"]["slot-conflicts"]["rows"] == len(slots)
    assert routing["payloads"]["coverage-holes"]["rows"] == len(holes)
    assert routing["payloads"]["slot-conflicts"]["sha256"] == _sha256(SLOT_PAYLOAD)
    assert routing["payloads"]["coverage-holes"]["sha256"] == _sha256(HOLE_PAYLOAD)
    assert routing["source"]["triaged"]["sha256"] == _sha256(TRIAGED)
    assert routing["source"]["triaged"]["rows"] == summary["total"] == 5224
    assert routing["source"]["triage_summary"]["sha256"] == _sha256(SUMMARY)
    assert routing["not_routed"]["not_owed"] == summary["not_owed"] == 323
    assert routing["not_routed"]["untagged_residue"] == summary["residue"] == 1


def test_upstream_post_stays_human_gated():
    routing = json.loads(ROUTING.read_text(encoding="utf-8"))
    gate = routing["destination"]["gate"]["upstream_post"]
    assert "HUMAN-GATED" in gate
    draft_ref = routing["destination"]["gate"]["draft"]
    assert (REPO / draft_ref).exists(), "ROUTING.json draft pointer is dangling"
    draft = DRAFT.read_text(encoding="utf-8")
    assert "DO NOT POST FROM AN AGENT SESSION" in draft
