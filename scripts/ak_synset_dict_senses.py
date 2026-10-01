#!/usr/bin/env python3
"""H4806 — Amarakosha synsets x MW/PWG sense-unit inventories (kosha).

Shortlist cand.6 (CROSSWALK_CANDIDATES_SHORTLIST_14-09-2026): join the AK
varga/synset layer (H4746 ak_lemma_cdsl_crosswalk.tsv, 14,036
(varga,eid,lemma) instances) against dictionary sense units — one Cologne
<L> record per unit — from MW (v02/mw/mw.txt) and PWG (v02/pwg/pwg.txt).
Measures how classical semantic clusters (AK synsets) split across modern
sense inventories.

LANGUAGE FENCE (sense-alignment-pilot trap): structural join on exact SLP1
lemma keys ONLY. No cross-language gloss-Jaccard; no gloss text is read,
joined, or emitted. Outputs carry keys + counts only.

Inputs are external read-only sources; nothing from csl-orig is committed.

Usage:
    python scripts/ak_synset_dict_senses.py            # build outputs
    python scripts/ak_synset_dict_senses.py --selftest # 30-synset sample
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import random
import re
import sys
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# External read-only sources (sibling clones; never committed here).
SL_TSV_DEFAULT = os.path.expanduser(
    "~/Documents/GitHub/SanskritLexicography/data/ak_lemma_cdsl_crosswalk.tsv")
MW_TXT_DEFAULT = os.path.expanduser("~/Documents/GitHub/csl-orig/v02/mw/mw.txt")
PWG_TXT_DEFAULT = os.path.expanduser("~/Documents/GitHub/csl-orig/v02/pwg/pwg.txt")

OUT_DIR = os.path.join(REPO, "data", "xwalk")
SYNSET_TSV = os.path.join(OUT_DIR, "ak_synset_mw_pwg_senses.tsv")
LEMMA_TSV = os.path.join(OUT_DIR, "ak_lemma_mw_pwg_senses.tsv")
STATS_JSON = os.path.join(OUT_DIR, "ak_synset_dict_senses_stats.json")

K1_RE = re.compile(r"<k1>([^<]*)")
SELFTEST_N = 30
CANARIES = ("deva", "svarga", "nara")


def count_sense_units_stream(path: str) -> dict:
    """Builder-side parse: stream records split on '<L>', take k1 of each."""
    units = collections.Counter()
    with open(path, encoding="utf-8") as f:
        for rec in f.read().split("<L>")[1:]:
            m = K1_RE.search(rec)
            if m:
                units[m.group(1)] += 1
    return units


def count_sense_units_linescan(path: str, keys: set) -> dict:
    """Independent re-scan (selftest): per-line state machine. A '<L>' line
    opens a new record; a '<k1>' seen while inside a record attributes the
    unit. Different code path from count_sense_units_stream on purpose."""
    counts = collections.Counter()
    inside = False
    with open(path, encoding="utf-8") as f:
        for line in f:
            if "<L>" in line:
                inside = True
            if inside and "<k1>" in line:
                m = K1_RE.search(line)
                if m and m.group(1) in keys:
                    counts[m.group(1)] += 1
                inside = False
    return counts


def load_ak_instances(path: str):
    rows = []
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        idx = {name: i for i, name in enumerate(header)}
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < len(header):
                continue
            rows.append((p[idx["lemma_slp1"]], p[idx["varga"]], p[idx["eid"]],
                         p[idx["match_type"]]))
    return rows


def bucket(n: int) -> str:
    if n == 0:
        return "0"
    if n == 1:
        return "1"
    if n <= 3:
        return "2-3"
    if n <= 10:
        return "4-10"
    return "11+"


def build(sl_tsv=MW_TXT_DEFAULT, mw_txt=MW_TXT_DEFAULT, pwg_txt=PWG_TXT_DEFAULT,
          write=True):
    sl_tsv = SL_TSV_DEFAULT if sl_tsv == MW_TXT_DEFAULT else sl_tsv
    instances = load_ak_instances(sl_tsv)
    mw_units = count_sense_units_stream(mw_txt)
    pwg_units = count_sense_units_stream(pwg_txt)

    # Lemma-level detail: one row per (varga,eid,lemma) instance.
    lemma_rows = []
    for lemma, varga, eid, _mt in instances:
        lemma_rows.append((lemma, varga, eid, mw_units.get(lemma, 0),
                           pwg_units.get(lemma, 0)))

    # Synset-level aggregation: (varga,eid) is the AK synset key.
    syn = {}
    for lemma, varga, eid, mu, pu in lemma_rows:
        s = syn.setdefault((varga, eid), dict(
            n_members=0, n_lemmas=0, mw_covered=0, mw_units=0,
            pwg_covered=0, pwg_units=0, _lemmas=set(), _top=None))
        s["n_members"] += 1
        if lemma not in s["_lemmas"]:
            s["_lemmas"].add(lemma)
            s["n_lemmas"] += 1
            if mu:
                s["mw_covered"] += 1
                s["mw_units"] += mu
            if pu:
                s["pwg_covered"] += 1
                s["pwg_units"] += pu
            tot = mu + pu
            if tot and (s["_top"] is None or tot > s["_top"][1]):
                s["_top"] = (lemma, tot)

    BUCKET_ORDER = ["0", "1", "2-3", "4-10", "11+"]
    dist = {b: 0 for b in BUCKET_ORDER}
    covered_mw = covered_pwg = covered_any = 0
    total_units = total_mw = total_pwg = 0
    synset_rows = []
    for (varga, eid) in sorted(syn, key=lambda k: (k[0], int(k[1]))):
        s = syn[(varga, eid)]
        tot = s["mw_units"] + s["pwg_units"]
        dist[bucket(tot)] += 1
        if s["mw_units"]:
            covered_mw += 1
        if s["pwg_units"]:
            covered_pwg += 1
        if tot:
            covered_any += 1
        total_units += tot
        total_mw += s["mw_units"]
        total_pwg += s["pwg_units"]
        synset_rows.append((varga, eid, s["n_members"], s["n_lemmas"],
                            s["mw_covered"], s["mw_units"],
                            s["pwg_covered"], s["pwg_units"], tot))

    n_syn = len(synset_rows)
    stats = {
        "generated": date.today().isoformat(),
        "handoff": "H4806",
        "ak_side": {"source": SL_TSV_DEFAULT, "instances": len(instances)},
        "sense_unit_def": "one Cologne <L> record (k1) in csl-orig v02 dict headword list",
        "mw_sense_units_total": sum(mw_units.values()),
        "pwg_sense_units_total": sum(pwg_units.values()),
        "mw_keys_total": len(mw_units),
        "pwg_keys_total": len(pwg_units),
        "ak_synsets": n_syn,
        "ak_synsets_with_mw_units": covered_mw,
        "ak_synsets_with_pwg_units": covered_pwg,
        "ak_synsets_with_any_units": covered_any,
        "coverage_mw_pct": round(100.0 * covered_mw / n_syn, 2),
        "coverage_pwg_pct": round(100.0 * covered_pwg / n_syn, 2),
        "coverage_any_pct": round(100.0 * covered_any / n_syn, 2),
        "sense_units_on_ak_synsets_mw": total_mw,
        "sense_units_on_ak_synsets_pwg": total_pwg,
        "sense_units_on_ak_synsets_total": total_units,
        "units_per_covered_synset_mean": round(total_units / covered_any, 2)
        if covered_any else 0.0,
        "split_distribution_units_per_synset": dist,
        "top10_most_split_synsets": [
            {"varga": v, "eid": e, "units": t,
             "lemma": syn[(v, e)]["_top"][0]}
            for (v, e), t in sorted(
                (((v, e), syn[(v, e)]["mw_units"] + syn[(v, e)]["pwg_units"])
                 for (v, e) in syn), key=lambda x: -x[1])[:10]],
        "fence": "structural lemma-key join only; no gloss text read or emitted",
    }

    if write:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(LEMMA_TSV, "w", encoding="utf-8") as f:
            f.write("lemma_slp1\tvarga\teid\tmw_sense_units\tpwg_sense_units\n")
            for r in lemma_rows:
                f.write("\t".join(str(x) for x in r) + "\n")
        with open(SYNSET_TSV, "w", encoding="utf-8") as f:
            f.write("varga\teid\tn_members\tn_lemmas_distinct\t"
                    "mw_lemmas_covered\tmw_sense_units\t"
                    "pwg_lemmas_covered\tpwg_sense_units\ttotal_sense_units\n")
            for r in synset_rows:
                f.write("\t".join(str(x) for x in r) + "\n")
        with open(STATS_JSON, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=1)
    return instances, lemma_rows, synset_rows, stats, mw_units, pwg_units


def selftest(mw_txt=MW_TXT_DEFAULT, pwg_txt=PWG_TXT_DEFAULT):
    instances, lemma_rows, synset_rows, stats, mw_units, pwg_units = build(
        write=False)
    failures = []

    # 30-synset sample: independent line-scan re-verification.
    rng = random.Random(42)
    sample = rng.sample(synset_rows, min(SELFTEST_N, len(synset_rows)))
    sample_pairs = {(r[0], r[1]) for r in sample}
    sample_keys = {lemma for lemma, varga, eid, _, _ in lemma_rows
                   if (varga, eid) in sample_pairs}
    sample_keys.update(CANARIES)  # canaries verified on the same scan

    mw_re = count_sense_units_linescan(mw_txt, sample_keys)
    pwg_re = count_sense_units_linescan(pwg_txt, sample_keys)
    checked = 0
    for varga, eid, *_ in sample:
        want_mw = want_pwg = 0
        for lemma, v, e, mu, pu in lemma_rows:
            if (v, e) == (varga, eid):
                want_mw += mw_units.get(lemma, 0)
                want_pwg += pwg_units.get(lemma, 0)
        got_mw = sum(mw_re[l] for l in (x[0] for x in lemma_rows
                                        if (x[1], x[2]) == (varga, eid)))
        got_pwg = sum(pwg_re[l] for l in (x[0] for x in lemma_rows
                                          if (x[1], x[2]) == (varga, eid)))
        checked += 1
        if (got_mw, got_pwg) != (want_mw, want_pwg):
            failures.append(f"synset {varga}/{eid}: stream="
                            f"({want_mw},{want_pwg}) linescan=({got_mw},{got_pwg})")

    # Own-data canaries.
    for c in CANARIES:
        w = (mw_units.get(c, 0), pwg_units.get(c, 0))
        g = (mw_re.get(c, 0), pwg_re.get(c, 0))
        if w != g:
            failures.append(f"canary {c}: stream={w} linescan={g}")
        print(f"canary {c}: mw={w[0]} pwg={w[1]}")

    print(f"selftest: {checked}/{len(sample)} sampled synsets re-verified "
          f"via independent line-scan; {len(sample_keys)} distinct lemmas")
    if failures:
        for f_ in failures:
            print("FAIL:", f_, file=sys.stderr)
        return 1
    print("PASS 30-synset sample + 3 canaries" if checked == SELFTEST_N
          else f"PASS {checked}-synset sample + 3 canaries")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--sl-tsv", default=SL_TSV_DEFAULT)
    ap.add_argument("--mw-txt", default=MW_TXT_DEFAULT)
    ap.add_argument("--pwg-txt", default=PWG_TXT_DEFAULT)
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest(args.mw_txt, args.pwg_txt))
    instances, lemma_rows, synset_rows, stats, _, _ = build(
        args.sl_tsv, args.mw_txt, args.pwg_txt, write=True)
    print(json.dumps({k: stats[k] for k in (
        "ak_synsets", "coverage_mw_pct", "coverage_pwg_pct",
        "coverage_any_pct", "sense_units_on_ak_synsets_total",
        "units_per_covered_synset_mean")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
