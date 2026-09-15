#!/usr/bin/env python3
"""Build the zaliznyak-oddbank-drills dataset (H4730).

Consumes, at build time only (never vendored), the kosha-registered
dcs-nominal-class-split + dcs-nominal-class-split-adj verdict banks
(VisualDCS/visual/paradigm_nominal_class_split*.json, H3984/H4011) and turns
the -ant/-at pooled-class verdicts into an oddball/exception drill bank for
zaliznyak-drills: words that END like -ant/-at present participles but whose
dictionary verdict says something else.

Two item types (ARCHITECTURE shared item schema, verdict-traceable):

  odd-one-out       3 words whose -ant/-at pair is ONE lexeme with two stem
                    spellings (verdict one_lexeme_two_spellings) + 1 oddball
                    where the dictionaries do NOT unite the pair (at_only /
                    ant_only). Spot the word that does not alternate.
  classify-verdict  one item per dictionary-resolved verdict row: are the
                    -ant and -at spellings one lexeme, or only -at attested?

Every item carries `verdict_refs` — {source_dataset, lemma_id, lemma, verdict}
— and `--check` re-resolves every ref against the live source JSONs, so a
drill item that no longer traces to its verdict row is a build failure.

Deterministic: no RNG. Pools sorted by (tokens desc, lemma_id asc); oddball i
pairs with distractors [i, i+1, i+2] (mod pool, collisions skipped).

Read-only on the source repos; writes only inside kosha/data/zaliznyak/.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

KOSHA_ROOT = Path(__file__).resolve().parent.parent
GH = KOSHA_ROOT.parent if (KOSHA_ROOT.parent / "VisualDCS").exists() else KOSHA_ROOT.parent
VISUAL = GH / "VisualDCS" / "visual"

SOURCES = {
    "dcs-nominal-class-split": VISUAL / "paradigm_nominal_class_split.json",
    "dcs-nominal-class-split-adj": VISUAL / "paradigm_nominal_class_split_adj.json",
}

VERDICT_CHOICES = [
    "one_lexeme_two_spellings",
    "at_only",
    "ant_only",
    "two_headwords",
]

ODDBALL_VERDICTS = {"at_only", "ant_only"}  # pair NOT united as one lexeme
ALTERNANT_VERDICT = "one_lexeme_two_spellings"
UNRESOLVED = "unresolved"


def load_rows() -> dict[str, dict[int, dict]]:
    """Return {source_dataset: {lemma_id: normalized row}}."""
    out: dict[str, dict[int, dict]] = {}
    for ds, path in SOURCES.items():
        if not path.exists():
            sys.exit(f"FAIL: source not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        key = "perLemmaAnt" if "perLemmaAnt" in data else "perLemmaAntAdj"
        rows = {}
        for r in data[key]:
            tokens = r.get("tokens", r.get("adjTokens", 0))
            deva = r["at_devanagari"] if r.get("dcsSpelling") == "at" else r["ant_devanagari"]
            rows[r["lemma_id"]] = {
                "source_dataset": ds,
                "lemma_id": r["lemma_id"],
                "lemma": r["lemma"],
                "devanagari": deva,
                "ant_devanagari": r["ant_devanagari"],
                "at_devanagari": r["at_devanagari"],
                "ant_form": r["ant_form"],
                "at_form": r["at_form"],
                "verdict": r["verdict"],
                "tokens": tokens,
            }
        out[ds] = rows
    return out


def ref(row: dict) -> dict:
    return {
        "source_dataset": row["source_dataset"],
        "lemma_id": row["lemma_id"],
        "lemma": row["lemma"],
        "verdict": row["verdict"],
    }


def word(row: dict) -> str:
    return f"{row['devanagari']} ({row['lemma']})"


def build_items(rows_by_ds: dict[str, dict[int, dict]]):
    items, stats = [], Counter()

    # --- classify-verdict: 1 item per resolved verdict row -------------------
    for ds, rows in rows_by_ds.items():
        for row in sorted(rows.values(), key=lambda r: (-r["tokens"], r["lemma_id"])):
            if row["verdict"] == UNRESOLVED:
                continue
            q = (
                f"In the dictionaries, are {row['ant_devanagari']} ({row['ant_form']}) "
                f"and {row['at_devanagari']} ({row['at_form']}) treated as ONE lexeme "
                f"with two stem spellings, or not?"
            )
            items.append({
                "type": "classify-verdict",
                "question": q,
                "answer": row["verdict"],
                "choices": list(VERDICT_CHOICES),
                "verdict_refs": [ref(row)],
                "source_dataset": ds,
                "tags": ["classify-verdict", row["verdict"]],
            })
            stats[f"classify-verdict:{ds}:{row['verdict']}"] += 1

    # --- odd-one-out: 3 alternants + 1 non-alternating oddball ---------------
    for ds, rows in rows_by_ds.items():
        alternants = sorted(
            (r for r in rows.values() if r["verdict"] == ALTERNANT_VERDICT),
            key=lambda r: (-r["tokens"], r["lemma_id"]),
        )
        oddballs = sorted(
            (r for r in rows.values() if r["verdict"] in ODDBALL_VERDICTS),
            key=lambda r: (-r["tokens"], r["lemma_id"]),
        )
        if not alternants or not oddballs:
            continue
        for i, odd in enumerate(oddballs):
            picks, j = [], 0
            while len(picks) < 3 and j < len(alternants):
                cand = alternants[(i + j) % len(alternants)]
                if cand["lemma_id"] != odd["lemma_id"] and all(
                    c["lemma_id"] != cand["lemma_id"] for c in picks
                ):
                    picks.append(cand)
                j += 1
            if len(picks) < 3:
                continue  # not enough distractors in this universe: skip, don't fake
            members = picks + [odd]
            # deterministic shuffle-ish rotation so the answer position varies
            rot = i % 4
            ordered = members[rot:] + members[:rot]
            q = (
                "Three of these words inflect with ONE lexeme that alternates its "
                "stem spelling (-ant/-at, like bhagavant/bhagavat). Which one does "
                "NOT — its -ant/-at pair is not one lexeme with two spellings? "
                + ", ".join(word(m) for m in ordered)
            )
            items.append({
                "type": "odd-one-out",
                "question": q,
                "answer": word(odd),
                "choices": [word(m) for m in ordered],
                "verdict_refs": [ref(m) for m in ordered],
                "source_dataset": ds,
                "tags": ["odd-one-out", odd["verdict"]],
            })
            stats[f"odd-one-out:{ds}:{odd['verdict']}"] += 1

    for n, it in enumerate(items, 1):
        it["id"] = f"ZOD-{n:04d}"
    # hoist id first, drop builder-only helper keys
    for it in items:
        it.pop("ant_devanagari_q", None)
    items.sort(key=lambda x: x["id"])
    return items, stats


def check(items, rows_by_ds) -> None:
    """Every verdict_ref must re-resolve to a live source row (id + verdict)."""
    errors = []
    seen_ids = set()
    for it in items:
        if it["id"] in seen_ids:
            errors.append(f"{it['id']}: duplicate id")
        seen_ids.add(it["id"])
        if it["answer"] not in it["choices"]:
            errors.append(f"{it['id']}: answer not among choices")
        if len(set(it["choices"])) != len(it["choices"]):
            errors.append(f"{it['id']}: duplicate choices")
        if not it["verdict_refs"]:
            errors.append(f"{it['id']}: no verdict_refs")
        expected_refs = 4 if it["type"] == "odd-one-out" else 1
        if len(it["verdict_refs"]) != expected_refs:
            errors.append(f"{it['id']}: {len(it['verdict_refs'])} refs, want {expected_refs}")
        for r in it["verdict_refs"]:
            row = rows_by_ds.get(r["source_dataset"], {}).get(r["lemma_id"])
            if row is None:
                errors.append(f"{it['id']}: ref {r} not in source")
            elif row["verdict"] != r["verdict"] or row["lemma"] != r["lemma"]:
                errors.append(f"{it['id']}: ref {r} mismatched against source row")
            if it["type"] == "odd-one-out" and r["verdict"] in ODDBALL_VERDICTS:
                if it["answer"] != f"{row['devanagari']} ({row['lemma']})":
                    errors.append(f"{it['id']}: oddball ref is not the answer")
    if errors:
        for e in errors:
            print("CHECK FAIL:", e, file=sys.stderr)
        sys.exit(f"FAIL: {len(errors)} trace/validation errors")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="validate an existing bank instead of building")
    args = ap.parse_args()

    rows_by_ds = load_rows()
    out_json = KOSHA_ROOT / "data" / "zaliznyak" / "zaliznyak_oddbank_drills.json"
    out_tsv = KOSHA_ROOT / "data" / "zaliznyak" / "zaliznyak_oddbank_drills.tsv"

    if args.check:
        doc = json.loads(out_json.read_text(encoding="utf-8"))
        check(doc["items"], rows_by_ds)
        print(f"CHECK PASS: {len(doc['items'])} items, all verdict_refs re-resolve")
        return

    items, stats = build_items(rows_by_ds)
    check(items, rows_by_ds)

    doc = {
        "title": "Zaliznyak -ant/-at oddball drills — split-verdict exception bank",
        "description": (
            "Oddball/exception bank for zaliznyak-drills built from the "
            "dcs-nominal-class-split(-adj) pooled-class verdicts: words ending "
            "like -ant/-at participles whose MW+PWG verdict says the -ant/-at "
            "pair is (or is not) one lexeme with two stem spellings."
        ),
        "source": {
            "datasets": sorted(SOURCES),
            "paths": {ds: str(p.relative_to(GH)) for ds, p in SOURCES.items()},
            "provenance": "H3984/H4011 (VisualDCS) consumed at build time, never vendored; H4730 consumer",
        },
        "item_types": ["odd-one-out", "classify-verdict"],
        "traceability": "every item carries verdict_refs -> {source_dataset, lemma_id, lemma, verdict}; rebuild with --check to re-resolve",
        "items": items,
    }
    out_json.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    with out_tsv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["id", "type", "question", "answer", "choices", "verdict_refs", "source_dataset"])
        for it in items:
            w.writerow([
                it["id"], it["type"], it["question"], it["answer"],
                "|".join(it["choices"]),
                ";".join(f"{r['source_dataset']}:{r['lemma_id']}:{r['verdict']}" for r in it["verdict_refs"]),
                it["source_dataset"],
            ])

    total_rows = sum(len(r) for r in rows_by_ds.values())
    unresolved = sum(1 for r in rows_by_ds.values() for x in r.values() if x["verdict"] == UNRESOLVED)
    print(f"source rows: {total_rows} (unresolved excluded from drills: {unresolved})")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    print(f"items: {len(items)} -> {out_json.relative_to(KOSHA_ROOT)} + .tsv")


if __name__ == "__main__":
    main()
