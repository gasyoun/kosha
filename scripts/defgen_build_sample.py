#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""defgen_build_sample.py — H730: build the frozen MW definition-generation
eval sample (>=500 headwords, stratified frequency x polysemy) + DCS
attestation sentences.

Inputs (all pre-existing org assets — nothing derived here is new data,
only a frozen JOIN of A3 x E26 x C15 x DCS):
  * A3  mw_en_tm.json          — SLP1-keyed MW English glosses, senses ' | '-separated
  * E26 lemma_frequency.tsv    — DCS whole-corpus lemma counts + rank (SLP1)
  * C15 dcs_cdsl_xref.tsv      — DCS lemma id <-> CDSL SLP1 headword crosswalk
  * DCS dcs_full.sqlite        — corpus sentences (VisualDCS local mirror)

Strata (3 x 3 = 9 cells, TARGET_PER_CELL each, seeded, deterministic):
  frequency by E26 rank_all : high <=2000 | mid 2001..20000 | low >20000
  polysemy by MW sense count: mono =1     | poly2_4 2..4    | poly5p >=5

A candidate must have >=MIN_ATTEST usable DCS sentences (4..40 whitespace
tokens, <=2 per work) or it is skipped (skips are logged, the cell refills
from its seeded oversample order — the freeze is the OUTPUT files, not the
candidate order).

Outputs (committed — this IS the frozen eval set):
  data/eval/defgen/frozen_sample.tsv
  data/eval/defgen/attestations.jsonl
  data/eval/defgen/frozen_sample.meta.json  (row counts, cell fill, skip log)

Usage:
  python scripts/defgen_build_sample.py [--gh-root C:/Users/user/Documents/GitHub]
"""
import argparse
import collections
import io
import json
import os
import random
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SEED = 730
TARGET_PER_CELL = 56          # 9 * 56 = 504 >= 500
OVERSAMPLE_PER_CELL = 120
MIN_ATTEST = 3
MAX_ATTEST = 5
MIN_SENT_TOKENS = 4
MAX_SENT_TOKENS = 40
MAX_PER_WORK = 2

OUT_DIR = os.path.join(REPO, "data", "eval", "defgen")


def freq_band(rank):
    if rank <= 2000:
        return "high"
    if rank <= 20000:
        return "mid"
    return "low"


def poly_band(n):
    if n == 1:
        return "mono"
    if n <= 4:
        return "poly2_4"
    return "poly5p"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gh-root", default=os.path.dirname(REPO))
    args = ap.parse_args()
    gh = args.gh_root

    tm_path = os.path.join(gh, "SanskritLexicography", "RussianTranslation", "src", "mw_en_tm.json")
    freq_path = os.path.join(gh, "kosha", "data", "frequency", "lemma_frequency.tsv")
    if not os.path.exists(freq_path):
        freq_path = os.path.join(REPO, "data", "frequency", "lemma_frequency.tsv")
    xref_path = os.path.join(gh, "csl-apidev", "simple-search", "dcs_xref", "dcs_cdsl_xref.tsv")
    dcs_path = os.path.join(gh, "VisualDCS", "src", "DCS-data-2026", "dcs_full.sqlite")
    for p in (tm_path, freq_path, xref_path, dcs_path):
        if not os.path.exists(p):
            sys.exit("missing input: %s" % p)

    print("loading A3 TM ...")
    tm = json.load(io.open(tm_path, encoding="utf-8"))

    print("loading E26 frequency ...")
    freq = {}
    with io.open(freq_path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        col = {c: i for i, c in enumerate(header)}
        for line in f:
            parts = line.rstrip("\n").split("\t")
            slp1 = parts[col["lemma_slp1"]]
            try:
                freq[slp1] = (int(parts[col["count_all"]]), int(parts[col["rank_all"]]),
                              parts[col["grammar_all"]])
            except ValueError:
                continue

    print("loading C15 crosswalk ...")
    # slp1 -> (dcs_id, dcs_lemma_iast) with the highest token_count
    xref = {}
    with io.open(xref_path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        col = {c: i for i, c in enumerate(header)}
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if parts[col["in_cdsl"]] != "1":
                continue
            slp1 = parts[col["slp1"]]
            try:
                tc = int(parts[col["token_count"]])
            except ValueError:
                tc = 0
            if slp1 not in xref or tc > xref[slp1][2]:
                xref[slp1] = (int(parts[col["dcs_id"]]), parts[col["dcs_lemma_iast"]], tc)

    universe = sorted(k for k in tm if k in freq and k in xref)
    print("universe (TM x E26 x C15):", len(universe))

    cells = collections.defaultdict(list)
    for k in universe:
        gloss = tm[k]
        senses = [s.strip() for s in gloss.split(" | ") if s.strip()]
        if not senses:
            continue
        count_all, rank_all, grammar = freq[k]
        cells[(freq_band(rank_all), poly_band(len(senses)))].append(k)

    rng = random.Random(SEED)
    candidates = {}
    for cell, keys in sorted(cells.items()):
        keys = sorted(keys)
        rng.shuffle(keys)
        candidates[cell] = keys[:OVERSAMPLE_PER_CELL]
        print("cell %-14s universe=%6d oversample=%d" % ("/".join(cell), len(keys), len(candidates[cell])))

    con = sqlite3.connect(dcs_path)
    cur = con.cursor()

    def attestations(dcs_id):
        rows = cur.execute(
            "SELECT DISTINCT s.sent_id, s.text_sandhied, t.name "
            "FROM token tk JOIN sentence s ON tk.sentence_id = s.id "
            "JOIN chapter c ON s.chapter_id = c.chapter_id "
            "JOIN text t ON c.text_id = t.text_id "
            "WHERE tk.lemma_id = ? LIMIT 4000", (dcs_id,)).fetchall()
        usable = []
        for sent_id, text, work in rows:
            if not text:
                continue
            ntok = len(text.split())
            if MIN_SENT_TOKENS <= ntok <= MAX_SENT_TOKENS:
                usable.append((ntok, str(sent_id), text, work or ""))
        usable.sort(key=lambda r: (r[0], r[1]))  # shortest first, deterministic tiebreak
        picked, per_work = [], collections.Counter()
        for ntok, sent_id, text, work in usable:
            if per_work[work] >= MAX_PER_WORK:
                continue
            per_work[work] += 1
            picked.append({"sent_id": sent_id, "text": text, "work": work})
            if len(picked) >= MAX_ATTEST:
                break
        return picked

    sample, attest_rows, skipped = [], [], []
    for cell in sorted(candidates):
        fb, pb = cell
        kept = 0
        for k in candidates[cell]:
            if kept >= TARGET_PER_CELL:
                break
            dcs_id, iast, _tc = xref[k]
            att = attestations(dcs_id)
            if len(att) < MIN_ATTEST:
                skipped.append({"slp1": k, "cell": "/".join(cell), "n_attest": len(att)})
                continue
            gloss = tm[k]
            senses = [s.strip() for s in gloss.split(" | ") if s.strip()]
            count_all, rank_all, grammar = freq[k]
            sample.append({
                "slp1": k, "iast": iast, "grammar": grammar,
                "sense_count": len(senses), "poly_band": pb,
                "count_all": count_all, "rank_all": rank_all, "freq_band": fb,
                "dcs_lemma_id": dcs_id, "n_attest": len(att),
                "gold_gloss": gloss,
            })
            attest_rows.append({"slp1": k, "dcs_lemma_id": dcs_id, "sentences": att})
            kept += 1
        print("cell %-14s kept=%d" % ("/".join(cell), kept))

    os.makedirs(OUT_DIR, exist_ok=True)
    cols = ["slp1", "iast", "grammar", "sense_count", "poly_band", "count_all",
            "rank_all", "freq_band", "dcs_lemma_id", "n_attest", "gold_gloss"]
    with io.open(os.path.join(OUT_DIR, "frozen_sample.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(cols) + "\n")
        for r in sample:
            f.write("\t".join(str(r[c]).replace("\t", " ") for c in cols) + "\n")
    with io.open(os.path.join(OUT_DIR, "attestations.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for r in attest_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    cell_fill = collections.Counter((r["freq_band"], r["poly_band"]) for r in sample)
    meta = {
        "id": "mw-defgen-eval-sample",
        "seed": SEED,
        "n": len(sample),
        "target_per_cell": TARGET_PER_CELL,
        "cells": {"/".join(c): cell_fill[c] for c in sorted(cell_fill)},
        "skipped_lt_min_attest": len(skipped),
        "skip_log": skipped,
        "inputs": {
            "a3_mw_en_tm": "SanskritLexicography/RussianTranslation/src/mw_en_tm.json (187,506 glosses)",
            "e26_lemma_frequency": "kosha data-v0.1.0 release asset lemma_frequency.tsv (83,277 lemmas)",
            "c15_dcs_cdsl_xref": "csl-apidev/simple-search/dcs_xref/dcs_cdsl_xref.tsv (in_cdsl=1 only)",
            "dcs": "VisualDCS/src/DCS-data-2026/dcs_full.sqlite (DCS 2026, Hellwig, CC BY 4.0)",
        },
        "filters": {
            "sentence_tokens": [MIN_SENT_TOKENS, MAX_SENT_TOKENS],
            "max_per_work": MAX_PER_WORK,
            "min_attest": MIN_ATTEST, "max_attest": MAX_ATTEST,
        },
    }
    with io.open(os.path.join(OUT_DIR, "frozen_sample.meta.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("frozen: n=%d  skipped=%d  -> %s" % (len(sample), len(skipped), OUT_DIR))
    if len(sample) < 500:
        sys.exit("FROZEN SAMPLE UNDER 500 — raise OVERSAMPLE_PER_CELL or relax filters")


if __name__ == "__main__":
    main()
