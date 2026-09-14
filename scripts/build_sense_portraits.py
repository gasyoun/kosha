#!/usr/bin/env python3
"""Diachronic sense portraits — join kosha-sense-frequency x sense-dating (H4735).

Joins per-sense DCS frequency counts (data/frequency/sense_frequency.tsv, MW
layer) with per-sense first-attestation era buckets (data/dating/
sense_dating.tsv, PWG v1 500-headword sample) through the H3744 crossdict
pilot's MW inventory column (the only existing bridge between PWG concordance
sense ids and MW sense numbers).

Output: data/dating/sense_portraits.tsv — one row per dated sense (lossless
LEFT JOIN; era buckets are never altered or dropped), plus a dated report.

--check: parity gate — recomputes the join from inputs, requires byte-equality
with the stored TSV, and independently recounts era buckets + join coverage
("era-bucket recount", the H4735 verify step).

Honesty stamps carried in output/report:
- sense-dating first_era = first attestation among works PWG cites, NOT the
  origin of the meaning (H4019 preface caveat).
- The bridge is the pilot's MW *inventory* column, not a sense alignment
  (H3744 note) — bridge_status column keeps every row's provenance.
"""

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATING_TSV = REPO / "data/dating/sense_dating.tsv"
PILOT_TSV = REPO / "data/concordance/sense_crossdict_pilot.tsv"
FREQ_TSV = REPO / "data/frequency/sense_frequency.tsv"
OUT_TSV = REPO / "data/dating/sense_portraits.tsv"
REPORT_MD = REPO / "data/dating/SENSE_PORTRAITS_REPORT.md"

ERA_RANK = {
    "vedic": 1,
    "epic-sutra": 2,
    "classical": 3,
    "early-medieval": 4,
    "late-medieval": 5,
}

OUT_HEADER = [
    "slp1", "hom", "sense_id",
    "first_era", "era_rank", "bucket_via", "class", "n_cites", "n_dateable",
    "bridge_status", "bridge_mw_sense",
    "count_all", "sense_rank", "lemma_share", "n_texts", "top_genre",
    "top_genre_share", "provenance", "confidence",
]


def read_tsv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def build_bridge():
    """(slp1, hom, pwg_sense_id) -> mw sense number string, from pilot inventory."""
    bridge = {}
    for row in read_tsv(PILOT_TSV):
        mw = (row.get("mw_sense_id") or "").strip()
        key = (row["lemma_slp1"], row["hom"], row["pwg_sense_id"])
        if mw.startswith("mw:") and len(mw.split(":")) == 3:
            bridge[key] = mw  # keep store id verbatim for traceability
        else:
            bridge[key] = ""  # pilot row exists, MW inventory column empty
    return bridge


def build_freq_mw():
    """(lemma_slp1, mw sense number) -> freq row (MW layer only)."""
    freq = {}
    for row in read_tsv(FREQ_TSV):
        if row["layer"] != "mw":
            continue
        n = row["sense_id"].rsplit("#", 1)[1]
        freq[(row["lemma_slp1"], n)] = row
    return freq


def join():
    bridge = build_bridge()
    freq = build_freq_mw()
    out_rows = []
    for d in read_tsv(DATING_TSV):
        key = (d["slp1"], d["hom"], d["sense_id"])
        mw_id = bridge.get(key)
        if mw_id is None:
            status, mw_id = "no_pilot_row", ""
        elif not mw_id:
            status = "bridge_unaligned"
        else:
            n = mw_id.rsplit(":", 1)[1]
            f = freq.get((d["slp1"], n))
            if f is None:
                status = "bridge_no_freq"
            else:
                status = "joined"
        era = d["first_era"].strip()
        f = None
        if mw_id is None:
            status, mw_id = "no_pilot_row", ""
        elif not mw_id:
            status = "bridge_unaligned"
        else:
            n = mw_id.rsplit(":", 1)[1]
            f = freq.get((d["slp1"], n))
            status = "joined" if f is not None else "bridge_no_freq"

        def fv(field, f=f):
            return f[field] if f is not None else ""
        out_rows.append({
            "slp1": d["slp1"],
            "hom": d["hom"],
            "sense_id": d["sense_id"],
            "first_era": era,
            "era_rank": str(ERA_RANK.get(era, "")),
            "bucket_via": d["bucket_via"],
            "class": d["class"],
            "n_cites": d["n_cites"],
            "n_dateable": d["n_dateable"],
            "bridge_status": status,
            "bridge_mw_sense": mw_id if status in ("joined", "bridge_no_freq") else "",
            "count_all": fv("count_all"),
            "sense_rank": fv("sense_rank"),
            "lemma_share": fv("lemma_share"),
            "n_texts": fv("n_texts"),
            "top_genre": fv("top_genre"),
            "top_genre_share": fv("top_genre_share"),
            "provenance": fv("provenance"),
            "confidence": fv("confidence"),
        })
    out_rows.sort(key=lambda r: (
        r["slp1"], r["hom"],
        int(r["era_rank"]) if r["era_rank"] else 99,
        r["sense_id"],
    ))
    return out_rows


def write_tsv(rows, path):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_HEADER, delimiter="\t",
                           lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def median(vals):
    vals = sorted(vals)
    n = len(vals)
    if not n:
        return ""
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2


def era_key(era: str) -> int:
    r = ERA_RANK.get(era)
    return r if r is not None else 99


def build_report(rows):
    era_census = Counter(r["first_era"] or "null-undateable" for r in rows)
    status_census = Counter(r["bridge_status"] for r in rows)
    joined = [r for r in rows if r["bridge_status"] == "joined"]
    dating_lemmas = {r["slp1"] for r in rows}
    joined_by_era = {}
    for r in joined:
        joined_by_era.setdefault(r["first_era"], []).append(int(r["count_all"]))
    era_lines = []
    for era in sorted(ERA_RANK, key=era_key):
        if era in era_census:
            cnts = joined_by_era.get(era, [])
            med = median(cnts)
            era_lines.append(
                f"| {era} | {era_census[era]} | {len(cnts)} | "
                f"{med if med != '' else '—'} | {sum(cnts)} |")
    top = sorted(joined, key=lambda r: -int(r["count_all"]))[:10]
    top_lines = [
        f"| {r['slp1']} | {r['sense_id']} | {r['first_era']} | "
        f"{r['count_all']} | {r['sense_rank']} | {r['bridge_mw_sense']} |"
        for r in top]
    lemma_rollup = Counter()
    per_lemma_min = {}
    for r in rows:
        k = (r["slp1"], r["hom"])
        if r["era_rank"]:
            per_lemma_min[k] = min(int(r["era_rank"]),
                                   per_lemma_min.get(k, 99))
    for k, rank in per_lemma_min.items():
        era = next(e for e, v in ERA_RANK.items() if v == rank)
        lemma_rollup[era] += 1
    lemma_lines = [f"| {e} | {c} |" for e, c in sorted(
        lemma_rollup.items(), key=lambda kv: ERA_RANK[kv[0]])]
    n_lemmas_dated = len(per_lemma_min)

    return f"""_Created: 15-09-2026 · Last updated: 15-09-2026_

# Diachronic sense portraits — sense-frequency × sense-dating (H4735)

Join of `data/frequency/sense_frequency.tsv` (DCS per-sense counts, MW layer)
with `data/dating/sense_dating.tsv` (first-attestation
era buckets, PWG v1 500-headword sample, H4019), bridged through the H3744
crossdict pilot's MW inventory column. Output: `sense_portraits.tsv` —
{len(rows)} rows, one per dated sense, lossless LEFT JOIN.

## Preface caveats (carried from both inputs)

> **first_era = first attestation among the works PWG itself cites — NOT the
> origin of the meaning** (H4019). The printed PWG sense order is never
> reordered.

> **The bridge is the pilot's MW *inventory* column, not a sense alignment**
> (H3744 note verbatim: "MW/Apte columns are inventory not sense-aligned").
> A joined row means "this PWG concordance sense's inventory MW sense has a
> DCS frequency row", nothing stronger.

## Era-bucket census (recount = verify target)

| era | dated senses | of which freq-joined |
|---|---|---|
""" + "\n".join(
        f"| {e} | {era_census[e]} | "
        f"{sum(1 for r in joined if r['first_era'] == e)} |"
        for e in sorted(era_census, key=era_key)
    ) + f"""

## Join coverage (bridge provenance)

| bridge_status | rows |
|---|---|
""" + "\n".join(f"| {s} | {c} |" for s, c in
                status_census.most_common()) + f"""

- `joined` — pilot inventory MW sense has a frequency row; freq payload filled.
- `bridge_no_freq` — pilot carries an MW inventory id but the frequency sidecar
  has no matching (lemma, sense) row (sense unattested / numbering drift).
- `bridge_unaligned` — pilot row exists, MW inventory column empty.
- `no_pilot_row` — no pilot row for the key.

## Era × frequency (joined rows only)

| era | dated senses | freq-joined | median count_all | total count_all |
|---|---|---|---|---|
""" + ("\n".join(era_lines) or "| (none) | | | | |") + f"""

## Lemma rollup — earliest dated sense per lemma ({n_lemmas_dated} lemmas with ≥1 dateable sense; sample = 500)

| earliest era | lemmas |
|---|---|
""" + ("\n".join(lemma_lines) or "| (none) | |") + f"""

## Top joined portraits (by DCS count_all)

| lemma | sense | first_era | count_all | sense_rank | bridge_mw_sense |
|---|---|---|---|---|---|
""" + ("\n".join(top_lines) or "| (none) | | | | | |") + f"""

## Feeds

Sense-resolved LSC (A57 next): era buckets give the diachronic axis, joined
count_all the frequency weight per sense. Per-sense frequency coverage is
bounded by the pilot inventory fill ({status_census.get('joined', 0)}/{len(rows)}
= {status_census.get('joined', 0) / len(rows):.1%}); widening it is the
concordance→MW alignment programme, not this join.

Rebuild + parity gate:

```bash
python scripts/build_sense_portraits.py           # rebuild
python scripts/build_sense_portraits.py --check   # era-bucket recount, exit 0
```

_Гасунс_
"""


def check(rows):
    """Era-bucket recount + join-coverage recount + byte parity."""
    # 1. Recount era buckets independently from the INPUT dating table.
    input_era = Counter(
        (d["first_era"].strip() or "null-undateable")
        for d in read_tsv(DATING_TSV))
    output_era = Counter(
        (r["first_era"] or "null-undateable") for r in rows)
    assert input_era == output_era, (
        f"era-bucket recount mismatch: input={dict(input_era)} "
        f"output={dict(output_era)}")
    # 2. Lossless: output row count == dating row count.
    n_dating = sum(1 for _ in open(DATING_TSV)) - 1
    assert len(rows) == n_dating, f"row loss: {len(rows)} != {n_dating}"
    # 3. Joined payload recount: every joined row's count_all must exist in
    #    the freq sidecar at the bridged MW sense number.
    freq = build_freq_mw()
    for r in rows:
        if r["bridge_status"] == "joined":
            n = r["bridge_mw_sense"].rsplit(":", 1)[1]
            f = freq.get((r["slp1"], n))
            assert f is not None and f["count_all"] == r["count_all"], (
                f"freq payload mismatch at {r['slp1']}#{r['sense_id']}")
        else:
            assert r["count_all"] == "", "freq payload on non-joined row"
    # 4. Byte parity with the stored file.
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=OUT_HEADER, delimiter="\t",
                       lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    stored = OUT_TSV.read_text()
    assert stored == buf.getvalue(), "stored TSV drifted from recompute"
    print(f"CHECK PASS: {len(rows)} rows, era recount ok "
          f"({dict(output_era)}), joined={sum(1 for r in rows if r['bridge_status'] == 'joined')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    rows = join()
    if args.check:
        check(rows)
        return 0
    write_tsv(rows, OUT_TSV)
    REPORT_MD.write_text(build_report(rows))
    check(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
