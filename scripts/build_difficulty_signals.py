#!/usr/bin/env python
"""Derive the DCS-grounded signal table the difficulty scorer consumes (W2a /
H949). Split out from the scorer so the slow, heavy-DB derive runs once and
`build_difficulty_scorer.py` can then score any reading pack from small TSVs alone
(no 878 MB DCS at score time — the same source→derive→consume split the sandhi
programme uses).

  * morph-signature rarity — GROUP BY the UD morphology features over all ~5.7M DCS
    tokens → per-signature corpus frequency. A token's morphological FORM (e.g.
    "dual locative", "optative middle") is rarer, hence harder to parse, than
    "nom sing masc"; this table is the evidence for the morphology axis. Persisted
    as data/difficulty/morph_signature_freq.tsv.

The compound axis needs NO derived table: DCS marks every compound-internal member
with feat_case='Cpd' (841k tokens), which the reading pack already carries in its
`morph` field — so the scorer reads compound load straight off the pack. (An earlier
draft tried the VisualDCS Kompozity/cmps.csv headword set for this; rejected — its
headwords include bare particles like `ca`/`tu`/`na`, so a join flagged ~12 % of
Nala 1 as "compound" when the real Cpd share is ~11 %, mostly different tokens. The
in-corpus Cpd tag is both cleaner and self-contained.)

Determinism: pure read of the DCS sqlite; no network, no clock.

Usage:
  python scripts/build_difficulty_signals.py
"""
import csv
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
# Reuse the reading pack's OWN morph formatter + feature columns, so the signature
# this table is keyed by is byte-identical to the `upos` + `morph` a reading pack
# carries per token. Re-deriving them here would let the two silently drift, and the
# scorer's join would then miss on every token (the FINDINGS §82 class).
from build_reading_pack import MORPH_FEATS, morph_str  # noqa: E402

GH = ROOT.parent if (ROOT.parent / "VisualDCS").exists() else ROOT.parent.parent
DCS = GH / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"

OUT_DIR = ROOT / "data" / "difficulty"
MORPH_FREQ = OUT_DIR / "morph_signature_freq.tsv"

# The signature is exactly what the reading pack shows: "<upos>|<morph_str>". Grouping
# on the raw feature columns MORPH_FEATS uses (plus upos) yields one row per distinct
# displayed form, so the scorer can join on the pack's own (upos, morph) with no
# re-derivation and no heavy DB at score time.
GROUP_COLS = ["upos"] + [c for c, _ in MORPH_FEATS]


def signature(upos, tokrow):
    return f"{upos or '-'}|{morph_str(tokrow)}"


def derive_morph_freq(con):
    cur = con.execute(
        "SELECT " + ",".join(GROUP_COLS) + ", COUNT(*) AS n FROM token "
        "GROUP BY " + ",".join(GROUP_COLS)
    )
    counts = {}
    total = 0
    for row in cur:
        sig = signature(row["upos"], row)
        n = row["n"]
        counts[sig] = counts.get(sig, 0) + n
        total += n
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(MORPH_FREQ, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["signature", "count", "share_pct"])
        for sig, n in sorted(counts.items(), key=lambda kv: -kv[1]):
            w.writerow([sig, n, round(100.0 * n / total, 6)])
    print(f"morph_signature_freq: {len(counts)} distinct signatures over {total} tokens -> {MORPH_FREQ}")
    return len(counts), total


def main():
    if not DCS.exists():
        sys.exit(f"DCS DB not found at {DCS}")
    con = sqlite3.connect(f"file:{DCS}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    derive_morph_freq(con)
    con.close()


if __name__ == "__main__":
    main()
