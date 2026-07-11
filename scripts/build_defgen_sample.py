"""Build the frozen H730 definition-generation / WSD eval sample.

Joins four canonical assets (never copied here, consumed in place):
  A3  mw_en_tm.json          MW English glosses, SLP1-keyed, senses '|'-separated
      (SanskritLexicography/RussianTranslation/src/)
  C15 dcs_cdsl_xref.tsv      DCS lemma id <-> CDSL/SLP1 crosswalk
      (csl-apidev/simple-search/dcs_xref/)
  E26 lemma_frequency.tsv    DCS-derived corpus frequency layer (kosha/data/frequency/)
  --  dcs_full.sqlite        DCS sentences + tokens (VisualDCS/src/DCS-data-2026/)

Sampling universe: SLP1 keys present in A3 AND C15(in_cdsl=1) AND E26, with >=3
attestation sentences in the DCS DB. Stratified 3 frequency terciles (E26 count_all)
x 4 polysemy bands (A3 sense count: 1 / 2-3 / 4-6 / 7+), equal quotas, seeded
random.Random(SEED), deterministic given the four inputs. Output is FROZEN: this
script exists for provenance/reproduction, not for re-runs that would shift the
sample under scored outputs (see docs/DEFGEN_WSD_EVAL_PROTOCOL_MW.md).

Usage: python scripts/build_defgen_sample.py [--out data/eval/defgen/frozen_sample_v1.jsonl]
"""
import argparse
import collections
import csv
import hashlib
import json
import random
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

GH = Path(__file__).resolve().parents[2]
A3_PATH = GH / "SanskritLexicography" / "RussianTranslation" / "src" / "mw_en_tm.json"
C15_PATH = GH / "csl-apidev" / "simple-search" / "dcs_xref" / "dcs_cdsl_xref.tsv"
E26_PATH = Path(__file__).resolve().parents[1] / "data" / "frequency" / "lemma_frequency.tsv"
DB_PATH = GH / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"

SEED = 730
TARGET = 520          # >=500 after any attrition
MIN_ATTEST = 3        # attestation sentences required per headword
N_ATTEST = 3          # attestations frozen per headword
SENT_MIN_WORDS = 4    # attestation sentence length filter (whitespace words)
SENT_MAX_WORDS = 60
POLY_BANDS = [(1, 1, "mono"), (2, 3, "low"), (4, 6, "mid"), (7, 10**9, "high")]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def poly_band(n: int) -> str:
    for lo, hi, name in POLY_BANDS:
        if lo <= n <= hi:
            return name
    raise ValueError(n)


def split_senses(gloss: str) -> list[str]:
    return [s.strip() for s in gloss.split("|") if s.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/eval/defgen/frozen_sample_v1.jsonl")
    args = ap.parse_args()

    with open(A3_PATH, encoding="utf-8") as f:
        tm = json.load(f)
    e26 = {}
    with open(E26_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            # rows without a whole-corpus count carry no usable frequency signal
            if row["count_all"].isdigit() and row["rank_all"].isdigit():
                e26[row["lemma_slp1"]] = row
    c15 = []
    with open(C15_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["in_cdsl"] == "1" and row["slp1"] in tm and row["slp1"] in e26:
                c15.append(row)
    # one row per slp1 key: keep the dcs_id with the most DCS tokens (dup keys exist)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT lemma_id, COUNT(DISTINCT sent_id) FROM token GROUP BY lemma_id")
    db_counts = dict(cur.fetchall())
    by_slp1: dict[str, dict] = {}
    for row in c15:
        n = db_counts.get(int(row["dcs_id"]), 0)
        row["_db_count"] = n
        prev = by_slp1.get(row["slp1"])
        if prev is None or n > prev["_db_count"]:
            by_slp1[row["slp1"]] = row
    universe = [r for r in by_slp1.values() if r["_db_count"] >= MIN_ATTEST]
    print(f"universe (A3 & C15 in_cdsl & E26 & >={MIN_ATTEST} DCS sents): {len(universe)}")

    counts = sorted(int(e26[r["slp1"]]["count_all"]) for r in universe)
    t1 = counts[len(counts) // 3]
    t2 = counts[2 * len(counts) // 3]
    print(f"frequency tercile cuts (count_all): low<={t1} < mid<={t2} < high")

    def freq_band(c: int) -> str:
        return "low" if c <= t1 else ("mid" if c <= t2 else "high")

    strata: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for r in universe:
        fb = freq_band(int(e26[r["slp1"]]["count_all"]))
        pb = poly_band(len(split_senses(tm[r["slp1"]])))
        strata[(fb, pb)].append(r)

    keys = sorted(strata)
    quota, extra = divmod(TARGET, len(keys))
    rng = random.Random(SEED)
    picked: list[tuple[str, str, dict]] = []
    short = 0
    for i, k in enumerate(keys):
        pool = sorted(strata[k], key=lambda r: r["slp1"])
        want = quota + (1 if i < extra else 0)
        if len(pool) < want:
            short += want - len(pool)
            sel = pool
        else:
            sel = rng.sample(pool, want)
        picked.extend((k[0], k[1], r) for r in sel)
        print(f"  stratum freq={k[0]:4s} poly={k[1]:4s}: pool={len(pool):5d} take={len(sel)}")
    # redistribute shortfall into the largest remaining pools, deterministically
    if short:
        taken = {r["slp1"] for _, _, r in picked}
        rest = sorted((r for k in keys for r in strata[k] if r["slp1"] not in taken),
                      key=lambda r: (-r["_db_count"], r["slp1"]))
        for r in rest[:short]:
            fb = freq_band(int(e26[r["slp1"]]["count_all"]))
            pb = poly_band(len(split_senses(tm[r["slp1"]])))
            picked.append((fb, pb, r))
        print(f"redistributed shortfall: {short}")

    # sentence.sent_id is unindexed (only chapter_id is); a per-lemma JOIN makes
    # SQLite build a transient auto-index per query. One pass + dict is ~500x faster.
    print("loading sentence table ...", flush=True)
    cur.execute("SELECT sent_id, text_sandhied FROM sentence")
    sent_text = dict(cur.fetchall())

    out_rows = []
    for fb, pb, r in sorted(picked, key=lambda t: t[2]["slp1"]):
        cur.execute(
            """SELECT sent_id, MIN(form) FROM token WHERE lemma_id = ?
               GROUP BY sent_id ORDER BY sent_id""",
            (int(r["dcs_id"]),),
        )
        rows = [(sid, form, sent_text.get(sid)) for sid, form in cur.fetchall()]
        good = [x for x in rows
                if x[2] and SENT_MIN_WORDS <= len(x[2].split()) <= SENT_MAX_WORDS]
        chosen = (good if len(good) >= N_ATTEST else rows)[:N_ATTEST]
        senses = split_senses(tm[r["slp1"]])
        out_rows.append({
            "slp1": r["slp1"],
            "iast": r["dcs_lemma_iast"],
            "dcs_id": int(r["dcs_id"]),
            "grammar": r["grammar"],
            "freq_count_all": int(e26[r["slp1"]]["count_all"]),
            "freq_rank_all": int(e26[r["slp1"]]["rank_all"]),
            "freq_band": fb,
            "sense_count": len(senses),
            "polysemy_band": pb,
            "gold_senses": senses,
            "attestations": [
                {"sent_id": sid, "form": form, "text": text}
                for sid, form, text in chosen
            ],
        })
    con.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for row in out_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    meta = {
        "sample": out.name,
        "n": len(out_rows),
        "seed": SEED,
        "target": TARGET,
        "min_attest": MIN_ATTEST,
        "freq_tercile_cuts": [t1, t2],
        "strata": {f"{fb}/{pb}": sum(1 for row in out_rows
                                     if row["freq_band"] == fb and row["polysemy_band"] == pb)
                   for fb in ("low", "mid", "high")
                   for pb in ("mono", "low", "mid", "high")},
        "inputs": {
            "A3_mw_en_tm.json": sha256(A3_PATH),
            "C15_dcs_cdsl_xref.tsv": sha256(C15_PATH),
            "E26_lemma_frequency.tsv": sha256(E26_PATH),
            "dcs_full.sqlite": sha256(DB_PATH),
        },
    }
    meta_path = out.with_suffix(".meta.json")
    with open(meta_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote {len(out_rows)} rows -> {out}")
    print(f"meta -> {meta_path}")


if __name__ == "__main__":
    main()
