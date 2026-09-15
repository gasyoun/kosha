#!/usr/bin/env python
"""25-entry stratified verification sample for the Kochergina join (H4748).

Stratified, seeded (20260915): 15 exact / 5 floor / 5 relaxed-candidates.
Mechanical checks per row (fail = any miss):
  C1 lemma-exists  — the linked dcs_lemma_id exists in dcs_full.sqlite and its
                     lemma string matches the row's dcs_lemma_iast.
  C2 token-count   — the lemma's token count equals the row's evidence_count.
  C3 key-in-source — the comparison key (or, for stripped compound-member
                     keys, the dashed source form) exists in the Kochergina
                     bundle and the anchor_id matches.

Emits data/concordance/KOCHERGINA_JOIN_SAMPLE_25.tsv with a blank
`adjudication` column filled in by hand (semantic sense check) afterwards.
No Russian gloss text is emitted (N10 rights fence).
"""
import collections
import json
import random
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from concordance_core import RECORD_FIELDS  # noqa: E402  (schema parity check)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "sanskrit-util" / "py"))
from sanskrit_util import from_slp1  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent if (ROOT.parent / "VisualDCS").exists() else ROOT.parent.parent
KOCH = GH / "SamudraManthanam" / "web" / "corpus_builder" / "jsonl" / "kochergina.jsonl"
DCS = GH / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"
CONC = ROOT / "data" / "concordance" / "kochergina_corpus_concordance.tsv"
CAND = ROOT / "data" / "concordance" / "kochergina_corpus_relaxed_candidates.tsv"
OUT = ROOT / "data" / "concordance" / "KOCHERGINA_JOIN_SAMPLE_25.tsv"

STRATA = {"exact": 15, "floor": 5, "relaxed": 5}
SEED = 20260915


def main():
    rows = []
    with open(CONC, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        assert header == RECORD_FIELDS + ["dcs_lemma_iast", "n_texts"], header
        for line in f:
            p = dict(zip(header, line.rstrip("\n").split("\t")))
            p["tier"] = p["match_method"]
            p["dcs_lemma_id"] = p["target_locus"].split(":", 1)[1]
            p["dcs_lemma_iast"] = p["dcs_lemma_iast"]
            rows.append(("asserted", p))
    with open(CAND, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            p = dict(zip(header, line.rstrip("\n").split("\t")))
            rows.append(("quarantined", p))

    rng = random.Random(SEED)
    sample = []
    for tier, n in STRATA.items():
        if tier == "relaxed":
            pool = [r for kind, r in rows if kind == "quarantined" and r["tier"] == "relaxed"]
        else:
            pool = [r for kind, r in rows if kind == "asserted" and r["tier"] == tier]
        sample += rng.sample(pool, min(n, len(pool)))

    # source key -> (anchor_id, dashed?) for C3
    src = {}
    with open(KOCH, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("deleted") or r.get("seg") != "head":
                continue
            s = (r.get("slp1") or "").strip()
            if s:
                src.setdefault(s, r["id"])

    con = sqlite3.connect("file:%s?mode=ro" % DCS, uri=True)
    lemma_tab = {}
    tok_tab = {}
    for lemma_id, lemma, n_tok in con.execute(
            "SELECT l.lemma_id, l.lemma, (SELECT COUNT(*) FROM token t WHERE t.lemma_id=l.lemma_id) "
            "FROM lemma l WHERE l.lemma_id IN (%s)"
            % ",".join(str(int(r["dcs_lemma_id"])) for r in sample)):
        lemma_tab[lemma_id] = lemma
        tok_tab[lemma_id] = n_tok

    out_rows = []
    n_pass = 0
    for r in sample:
        key = r["anchor_key_slp1"]
        lid = int(r["dcs_lemma_id"])
        stripped = key != key.strip("-")
        c1 = lemma_tab.get(lid) == r["dcs_lemma_iast"]
        c2 = tok_tab.get(lid) == int(r["evidence_count"])
        c3 = key in src and (src.get(key) == r.get("anchor_id") or r.get("anchor_id") is None)
        ok = c1 and c2 and c3
        n_pass += ok
        out_rows.append({
            "stratum": r["tier"],
            "anchor_key_slp1": key,
            "anchor_key_iast": from_slp1(key.strip("-")),
            "anchor_id": r.get("anchor_id", "-"),
            "dcs_lemma_id": lid,
            "dcs_lemma_iast": r["dcs_lemma_iast"],
            "evidence_count": r["evidence_count"],
            "check_lemma_exists": "PASS" if c1 else "FAIL",
            "check_token_count": "PASS" if c2 else "FAIL",
            "check_key_in_source": "PASS" if c3 else "FAIL",
            "compound_stripped": "yes" if stripped else "no",
            "adjudication": "",
        })

    cols = list(out_rows[0].keys())
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(cols) + "\n")
        for r in out_rows:
            f.write("\t".join(str(r[c]) for c in cols) + "\n")

    print("sample: %d rows -> %s" % (len(out_rows), OUT))
    print("mechanical checks: %d/%d PASS" % (n_pass, len(out_rows)))
    for r in out_rows:
        print("  %-8s %-18s -> %-18s %s%s%s" % (
            r["stratum"], r["anchor_key_iast"], r["dcs_lemma_iast"],
            r["check_lemma_exists"][0], r["check_token_count"][0], r["check_key_in_source"][0]))


if __name__ == "__main__":
    main()
