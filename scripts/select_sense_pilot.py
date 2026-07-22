#!/usr/bin/env python
"""Step 0 — select the wave-1 polysemous-headword pilot for the H1455
sense-reconciliation layer (PLAN_KOSHA_SENSE_RECONCILIATION_2026H2).

Selection criteria (IMPLEMENTATION step 0):
  * >= 2 PWG leaf senses in the (slp1, hom) group,
  * >= 2 of those leaf senses carry >= 1 <ls> locus (the per-sense locus signal
    the whole layer demonstrates), and
  * a non-trivial DCS attestation count (headword present in the reused
    dict_corpus_concordance headword<->DCS-lemma table).

Ranks DCS-attested groups first, then by (n_leaf_senses, n_ls) desc, slp1 asc
for a fully deterministic order, and FORCES the nāgadanta/nāgadantaka smoke-test
pair to the head. Writes data/concordance/sense_pilot_headwords.tsv and prints
the selection query as a LOG: line (no silent cap — the pilot size is logged).

Deterministic, no network. REUSES sense_loci_core (leaf model) + the existing
dict_corpus_concordance output; builds nothing already owned elsewhere.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sense_loci_core as slc  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DICT_CONC = ROOT / "data" / "concordance" / "dict_corpus_concordance.tsv"
OUT = ROOT / "data" / "concordance" / "sense_pilot_headwords.tsv"

FORCE = [("nAgadanta", ""), ("nAgadantaka", "")]   # A3/A4 smoke-test pair


def load_attested():
    """slp1 -> total DCS evidence_count (reuse dict_corpus_concordance)."""
    ev = {}
    with open(DICT_CONC, encoding="utf-8-sig") as f:
        header = f.readline().rstrip("\n").split("\t")
        idx = {c: i for i, c in enumerate(header)}
        for line in f:
            p = line.rstrip("\n").split("\t")
            slp1 = p[idx["anchor_key_slp1"]]
            ev[slp1] = ev.get(slp1, 0) + int(p[idx["evidence_count"]] or 0)
    return ev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=None, help="pwg_sense_loci.tsv (default: data/concordance or sample)")
    ap.add_argument("--size", type=int, default=500, help="target pilot size (marked default 500)")
    ap.add_argument("--min-loci-senses", type=int, default=2, help="min leaf senses carrying >=1 <ls>")
    args = ap.parse_args()

    groups = slc.load_pwg_senses(args.input)
    attested = load_attested()
    print("LOG: loaded %d PWG (slp1,hom) groups; %d DCS-attested headwords"
          % (len(groups), len(attested)), file=sys.stderr)

    cands = []
    for (slp1, hom), senses in groups.items():
        leaf = slc.leaves(senses)
        if len(leaf) < 2:
            continue
        n_ls_senses = sum(1 for s in leaf if s.ls_raw)
        n_ls = sum(len(s.ls_raw) for s in leaf)
        if n_ls_senses < args.min_loci_senses:
            continue
        ev = attested.get(slp1, 0)
        cands.append((slp1, hom, len(leaf), n_ls_senses, n_ls, ev, ev > 0))

    # deterministic rank: attested first, then most senses, most loci, slp1 asc
    cands.sort(key=lambda r: (0 if r[6] else 1, -r[2], -r[4], r[0]))

    forced = {k: None for k in FORCE}
    chosen, seen = [], set()
    for k in FORCE:
        for c in cands:
            if (c[0], c[1]) == k:
                chosen.append(c)
                seen.add(k)
                break
    for c in cands:
        if len(chosen) >= args.size:
            break
        key = (c[0], c[1])
        if key in seen:
            continue
        seen.add(key)
        chosen.append(c)

    missing = [k for k in FORCE if k not in seen]
    if missing:
        print("LOG: WARNING forced smoke-test headwords not in candidate set: %s" % missing, file=sys.stderr)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    cols = ["slp1", "hom", "n_leaf_senses", "n_loci_senses", "n_ls", "dcs_evidence", "dcs_attested"]
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(cols) + "\n")
        for slp1, hom, nl, nls_s, nls, ev, att in chosen:
            f.write("%s\t%s\t%d\t%d\t%d\t%d\t%s\n" % (slp1, hom, nl, nls_s, nls, ev, "1" if att else "0"))

    n_att = sum(1 for c in chosen if c[6])
    print("LOG: selection query = {>=2 leaf senses} AND {>=%d leaf senses with >=1 <ls>} "
          "AND rank[DCS-attested, n_senses, n_ls]; size=%d" % (args.min_loci_senses, len(chosen)), file=sys.stderr)
    print("pilot: %d headwords (%d DCS-attested, %d unattested), smoke-pair forced=%s -> %s"
          % (len(chosen), n_att, len(chosen) - n_att, [k[0] for k in FORCE], OUT), file=sys.stderr)


if __name__ == "__main__":
    main()
