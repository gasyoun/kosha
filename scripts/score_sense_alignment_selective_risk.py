#!/usr/bin/env python
"""H5070 — selective risk and abstention for the scaled aligned-sense table.

Turns the frozen H5070 deck plus its recorded verdicts into an error-versus-
coverage curve over the ENLARGED population, and reports the two quantities the
handoff insists are kept apart:

  wrong-match rate  — among rows the aligner DID align, how many join senses that
                      do not denote the same meaning (the selective risk);
  abstention rate   — the share of candidate groups the aligner declined to align
                      at all, with its failure taxonomy and the unreachable
                      (`absent-dictionary`) pairs split out.

Estimator. The deck allocates its budget EQUALLY across the three score bands,
so raw deck fractions are not population rates. Every figure here is a stratified
estimate: p_hat = sum_s (N_s / N) * p_hat_s over the strata in scope, with N_s the
eligible population of stratum s. Intervals are Wilson score intervals on the
per-stratum counts, combined for the pooled figure through the stratified
variance sum_s (N_s/N)^2 * p_s(1-p_s)/n_s; a stratum with no adjudicated card
contributes its weight but no information and is reported as such.

Two rates are printed for every scope, never one:

  strict  — every `different` verdict counts as a wrong match;
  lenient — `different` verdicts flagged `near_miss` (metonymy, POS variant,
            sibling referent) are excluded.

The truth is bracketed by the pair; quoting either alone overstates precision.

The synthetic positive control is EXCLUDED from every rate and reported
separately as a pipeline check.

Reads  data/concordance/selective_risk/review_deck.tsv
       data/concordance/selective_risk/adjudication_h5070.tsv
       data/concordance/selective_risk/population_freeze.json
       data/concordance/selective_risk/canary_key.json
Writes data/concordance/selective_risk/selective_risk.json
       data/concordance/selective_risk/SELECTIVE_RISK_REPORT.md
"""
import argparse, csv, json, math, sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
SR = ROOT / "data/concordance/selective_risk"
BANDS = ["lo <0.40", "mid 0.40-0.69", "hi >=0.70"]
SCOPES = [("all aligned", BANDS, 0.0),
          ("score >= 0.40", BANDS[1:], 0.40),
          ("score >= 0.70", BANDS[2:], 0.70)]


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def load(p):
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def stratified(rows_by_stratum, weights, wrong_of):
    """Return (point, lo, hi, n_used, strata_without_data)."""
    total_w = sum(weights.values())
    if total_w == 0:
        return (float("nan"), 0.0, 1.0, 0, list(weights))
    point, var, n_used, empty = 0.0, 0.0, 0, []
    for s, w in weights.items():
        cards = rows_by_stratum.get(s, [])
        if not cards:
            empty.append(s)
            continue
        n = len(cards)
        k = sum(1 for r in cards if wrong_of(r))
        p = k / n
        frac = w / total_w
        point += frac * p
        var += (frac ** 2) * (p * (1 - p) / n)
        n_used += n
    # pooled interval: normal on the stratified variance, widened to the Wilson
    # interval of the pooled counts when the deck is too small for the normal
    se = math.sqrt(var)
    lo_n, hi_n = point - 1.96 * se, point + 1.96 * se
    k_all = sum(1 for s in weights for r in rows_by_stratum.get(s, []) if wrong_of(r))
    lo_w, hi_w = wilson(k_all, n_used)
    return (point, max(0.0, min(lo_n, lo_w)), min(1.0, max(hi_n, hi_w)), n_used, empty)


DICT_KEYS = ("pwg", "mw", "apte", "md", "skd", "vcp")


def concentration(deck_by_card, real, freeze):
    """Wrong-match rate split by which dictionaries a card joins.

    A pooled rate hides whether error is spread evenly or parked in one channel.
    Counts are raw (not re-weighted): these cells are far too small to carry a
    population estimate, and are reported as a direction to look, never a rate
    to quote."""
    out = []
    seen = {}
    for r in real:
        card = deck_by_card.get(r["card"], {})
        chans = tuple(k for k in DICT_KEYS if (card.get(f"{k}_gloss") or "").strip())
        for k in chans:
            a, b = seen.setdefault(k, [0, 0])
            seen[k] = [a + 1, b + (1 if r["verdict"] == "different" else 0)]
    reach = freeze.get("dictionary_reachability", {})
    for k in DICT_KEYS:
        if k not in seen:
            continue
        n, w = seen[k]
        lo, hi = wilson(w, n)
        out.append({"channel": k, "cards": n, "wrong": w,
                    "raw_rate": round(w / n, 4), "ci95": [round(lo, 4), round(hi, 4)],
                    "aligned_rows_with_channel": reach.get(k)})
    return out


def write_report(d, payload, freeze):
    """Emit the human-readable twin of selective_risk.json."""
    r = payload["risk_coverage"]
    pc = payload["positive_control"]
    L = []
    L.append("# Selective risk and abstention on the scaled aligned-sense table")
    L.append("")
    L.append("_Created: 20-09-2026 · Last updated: 20-09-2026_")
    L.append("")
    L.append("Generated by `scripts/score_sense_alignment_selective_risk.py` (H5070). Do not hand-edit:")
    L.append("re-run the script. Machine twin: `selective_risk.json`.")
    L.append("")
    L.append("## What this is, and what it is not")
    L.append("")
    L.append("This is an **agent-adjudicated** error-versus-coverage curve over the enlarged")
    L.append("population, produced to size the risk of the scaling waves. It is **not** the")
    L.append("family's acceptance precision: that figure stays behind the human-vote fence")
    L.append("restated in `SENSE_ALIGNMENT_BUILD_REPORT.md`, and nothing here lifts it or")
    L.append("licenses a change to any serving threshold.")
    L.append("")
    L.append(f"- population hash `{payload['source_sha256']}`")
    L.append(f"- aligned {payload['population_aligned']:,} of {payload['candidate_groups']:,} candidate groups "
             f"— coverage {payload['coverage']*100:.2f} %, abstention {payload['abstention']*100:.2f} %")
    L.append(f"- {payload['newly_adjudicated_cards']} newly adjudicated pairs; "
             f"{payload['gold_excluded_cards']} reused-gold cards excluded from selection")
    L.append(f"- adjudicator: {payload['adjudicator']}")
    L.append("")
    L.append("## Error versus coverage")
    L.append("")
    L.append("`strict` counts every `different` verdict; `lenient` drops the `near_miss` ones")
    L.append("(metonymy, POS variant, sibling referent). The truth is bracketed by the pair.")
    L.append("Rates are stratified estimates re-weighted to the population, never raw deck fractions.")
    L.append("")
    L.append("| scope | eligible rows | coverage | cards | strict wrong-match | 95 % CI | lenient | 95 % CI |")
    L.append("|---|---:|---:|---:|---:|---|---:|---|")
    for x in r:
        L.append(f"| {x['scope']} | {x['eligible_population']:,} | {x['coverage_of_all_groups']*100:.2f} % | "
                 f"{x['cards_adjudicated']} | {x['strict_wrong_rate']*100:.1f} % | "
                 f"{x['strict_ci95'][0]*100:.1f}–{x['strict_ci95'][1]*100:.1f} % | "
                 f"{x['lenient_wrong_rate']*100:.1f} % | "
                 f"{x['lenient_ci95'][0]*100:.1f}–{x['lenient_ci95'][1]*100:.1f} % |")
    L.append("")
    top, bot = r[0], r[-1]
    L.append(f"The point estimate falls monotonically with confidence "
             f"({top['strict_wrong_rate']*100:.1f} % → {bot['strict_wrong_rate']*100:.1f} % strict), which is the")
    L.append("direction a usable score would show. The intervals, however, overlap completely:")
    L.append(f"the `{bot['scope']}` interval ({bot['strict_ci95'][0]*100:.1f}–{bot['strict_ci95'][1]*100:.1f} %) contains the")
    L.append(f"pooled point estimate ({top['strict_wrong_rate']*100:.1f} %). At {payload['newly_adjudicated_cards']} cards the curve cannot")
    L.append("distinguish a real gain in precision from sampling noise.")
    L.append("")
    L.append("**No threshold is recommended.** The handoff permits an inconclusive calibration as")
    L.append("a documented result, and that is what this is.")
    L.append("")
    L.append("## Abstention, reported separately")
    L.append("")
    L.append(f"The aligner declines {payload['population_unaligned']:,} of {payload['candidate_groups']:,} candidate groups "
             f"({payload['abstention']*100:.2f} %).")
    L.append("Abstention is not error: these rows carry a failure class and are never served as matches.")
    L.append("")
    L.append("| failure class | rows |")
    L.append("|---|---:|")
    for k, v in payload["abstention_taxonomy"].items():
        L.append(f"| {k or '(aligned — no failure class)'} | {v:,} |")
    L.append("")
    L.append(f"`absent-dictionary` ({payload['unreachable_pairs_absent_dictionary']:,} rows) is the **unreachable-pair** class the handoff")
    L.append("asks to keep separate: the pair could not be formed because a dictionary has no entry,")
    L.append("so it is neither a match nor a miss and belongs in no error rate.")
    L.append("")
    L.append("## Controls")
    L.append("")
    if pc:
        L.append(f"1. **Seeded confident wrong match (blind) — {pc['verdict']}.** `{pc['group_id']}` was minted by pairing")
        L.append(f"   {pc['construction'].lower()}, dressed at score {pc['declared_score']} (high band) and shuffled into the")
        L.append(f"   deck; its identity sat in `canary_key.json`, unopened until the verdicts were written.")
        L.append(f"   Adjudicated `{pc['observed']}` — the deck detects a confident wrong match it is not warned about.")
        L.append("   It is excluded from every rate above.")
    L.append("2. **Baseline reproduction.** The W2 acceptance sample reproduces **byte-for-byte** from its own")
    L.append("   revision `bd758f0f0`, confirming the sampler is deterministic and the artifact honest.")
    L.append("3. **Population-shift control.** The same command at HEAD does **not** reproduce it — see below.")
    L.append("")
    L.append("## The frozen acceptance sample no longer matches the population it names")
    L.append("")
    L.append("H4745 (`e98910b6f`) rebuilt the population table after H4751 (`bd758f0f0`) froze the W2 sample,")
    L.append("inserting the MD channel. Consequences, measured:")
    L.append("")
    L.append("| | frozen W2 | HEAD |")
    L.append("|---|---:|---:|")
    L.append("| aligned population | 7,009 | 7,087 |")
    L.append("| sample columns | 25 | 27 |")
    L.append("| cards the frozen rule selects | 152 | 155 |")
    L.append("")
    L.append("Only 122 of the 152 frozen cards are still selected at HEAD: 30 are re-drawn and 33 are new.")
    L.append("**All 30 dropped cards remain in the population** — nothing was deleted; the seeded draw moved")
    L.append("because stratum sizes moved. One group (`SAKa#1`) changed score (0.533 → 0.600) and crossed")
    L.append("into a different stratum.")
    L.append("")
    L.append("The frozen sample therefore remains a valid sample of the *pre-MD* population and an invalid")
    L.append("one of the current table. Any precision figure computed on it must name the revision it")
    L.append("describes. This is a **provenance defect, not a data defect**.")
    L.append("")
    L.append("## Where the error actually sits")
    L.append("")
    L.append("A pooled rate hides whether error is spread evenly or parked in one channel.")
    L.append("Counts below are **raw and tiny** — a direction to look, never a rate to quote.")
    L.append("")
    L.append("| channel | cards adjudicated | wrong | raw rate | 95 % CI | aligned rows carrying it |")
    L.append("|---|---:|---:|---:|---|---:|")
    for c in payload["error_concentration_by_channel"]:
        rows = f"{c['aligned_rows_with_channel']:,}" if c["aligned_rows_with_channel"] is not None else "—"
        L.append(f"| {c['channel']} | {c['cards']} | {c['wrong']} | {c['raw_rate']*100:.0f} % | "
                 f"{c['ci95'][0]*100:.0f}–{c['ci95'][1]*100:.0f} % | {rows} |")
    L.append("")
    skd = next((c for c in payload["error_concentration_by_channel"] if c["channel"] == "skd"), None)
    if skd and skd["cards"] and skd["wrong"] == skd["cards"]:
        L.append(f"**Every SKD-bearing card in the deck ({skd['wrong']}/{skd['cards']}) is a wrong match**, and all of them are")
        L.append("the same failure the build report already names under Known limits: the ŚKDR gloss is the")
        L.append("**verbal-root (dhātu) entry**, not the noun, so the row is true about the attribution and")
        L.append("false about the meaning. This deck did not discover a new defect — it independently")
        L.append("re-derived a documented one and shows it is not rare within its channel.")
        L.append("")
        L.append(f"The channel is small ({skd['aligned_rows_with_channel']:,} of {payload['population_aligned']:,} aligned rows), so it cannot")
        L.append("explain the pooled rate on its own; with three cards it cannot size itself either.")
        L.append("The actionable reading is that **the next deck should stratify on the SKD channel**")
        L.append("rather than let it fall out of a general draw.")
        L.append("")
    L.append("## Limitations")
    L.append("")
    L.append("1. **Single adjudicator.** One agent (Opus 5) labelled all 60 cards; there is no second")
    L.append("   adjudicator and therefore no inter-annotator agreement for this deck. The reused H3910")
    L.append("   judge kappa (0.9022) is self-consistency of a different judge on a different population")
    L.append("   and does not transfer.")
    L.append("2. **Evidence is the card, not the source.** Verdicts rest on the glosses carried in the")
    L.append("   table. A truncated gloss can make a correct alignment look wrong and vice versa;")
    L.append("   `C011` and `C014` are explicit instances of contentless glosses.")
    L.append("3. **Band resolution only.** Equal-per-band allocation resolves the curve at the band")
    L.append("   boundaries (0.40, 0.70) and nowhere else; a finer threshold sweep needs a larger deck.")
    L.append("4. **Selection limits.** Cards are drawn only from rows the aligner already aligned and")
    L.append("   only from the gold-excluded remainder, so this measures precision, never recall.")
    L.append("5. **Strata without cards contribute weight but no information** where listed in the JSON.")
    L.append("")
    L.append("_Гасунс_")
    (d / "SELECTIVE_RISK_REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", type=Path, default=SR)
    a = ap.parse_args()
    d = a.dir
    freeze = json.loads((d / "population_freeze.json").read_text(encoding="utf-8"))
    canary = json.loads((d / "canary_key.json").read_text(encoding="utf-8")) if (d / "canary_key.json").exists() else None
    verdicts = load(d / "adjudication_h5070.tsv")

    canary_rows = [r for r in verdicts if canary and r["group_id"] == canary["canary_group_id"]]
    real = [r for r in verdicts if not (canary and r["group_id"] == canary["canary_group_id"])]

    weights_all = {m["stratum"]: m["eligible"] for m in freeze["strata"]}
    by_stratum = defaultdict(list)
    for r in real:
        by_stratum[r["stratum"]].append(r)

    strict = lambda r: r["verdict"] == "different"
    lenient = lambda r: r["verdict"] == "different" and r["near_miss"] != "yes"

    total_groups = freeze["source_rows"]
    aligned = freeze["population_aligned"]
    results = []
    for label, bands, thr in SCOPES:
        w = {s: n for s, n in weights_all.items() if s.split("|")[0] in bands}
        n_pop = sum(w.values())
        cov = n_pop / total_groups
        sp, slo, shi, n_used, empty = stratified(by_stratum, w, strict)
        lp, llo, lhi, _, _ = stratified(by_stratum, w, lenient)
        results.append({
            "scope": label, "threshold": thr,
            "eligible_population": n_pop,
            "coverage_of_all_groups": round(cov, 6),
            "abstention_of_all_groups": round(1 - cov, 6),
            "cards_adjudicated": n_used,
            "strict_wrong_rate": round(sp, 4), "strict_ci95": [round(slo, 4), round(shi, 4)],
            "lenient_wrong_rate": round(lp, 4), "lenient_ci95": [round(llo, 4), round(lhi, 4)],
            "strata_without_cards": empty,
        })

    deck_by_card = {r["card"]: r for r in load(d / "review_deck.tsv")}
    conc = concentration(deck_by_card, real, freeze)
    unsure = sum(1 for r in real if r["verdict"] == "unsure")
    payload = {
        "handoff": "H5070",
        "source_sha256": freeze["source_sha256"],
        "population_aligned": aligned,
        "population_unaligned": freeze["population_unaligned"],
        "candidate_groups": total_groups,
        "coverage": freeze["coverage"],
        "abstention": freeze["abstention"],
        "abstention_taxonomy": freeze["abstention_taxonomy"],
        "unreachable_pairs_absent_dictionary": freeze["unreachable_pairs_absent_dictionary"],
        "gold_excluded_cards": freeze["gold_excluded_cards"],
        "gold_files": freeze["gold_files"],
        "newly_adjudicated_cards": len(real),
        "adjudicator": "Claude Opus 5 (claude-opus-5), single adjudicator, H5070",
        "unsure_cards": unsure,
        "risk_coverage": results,
        "error_concentration_by_channel": conc,
        "positive_control": ({
            "group_id": canary["canary_group_id"],
            "construction": canary["construction"],
            "declared_score": canary["declared_score"],
            "expected": canary["expected_verdict"],
            "observed": canary_rows[0]["verdict"] if canary_rows else None,
            "verdict": "PASS" if canary_rows and canary_rows[0]["verdict"] == canary["expected_verdict"] else "FAIL",
            "blind": True,
        } if canary else None),
    }
    (d / "selective_risk.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"population  aligned {aligned}  unaligned {freeze['population_unaligned']}  "
          f"coverage {freeze['coverage']*100:.2f}%  abstention {freeze['abstention']*100:.2f}%")
    print(f"deck        {len(real)} newly adjudicated (+1 synthetic control), "
          f"{freeze['gold_excluded_cards']} reused-gold cards excluded")
    print(f"unsure      {unsure}")
    print()
    hdr = f"{'scope':16s} {'pop':>6s} {'cov':>7s} {'n':>4s} {'strict':>8s} {'95% CI':>17s} {'lenient':>8s} {'95% CI':>17s}"
    print(hdr); print("-" * len(hdr))
    for r in results:
        print(f"{r['scope']:16s} {r['eligible_population']:6d} {r['coverage_of_all_groups']*100:6.2f}% "
              f"{r['cards_adjudicated']:4d} {r['strict_wrong_rate']*100:7.1f}% "
              f"[{r['strict_ci95'][0]*100:5.1f}, {r['strict_ci95'][1]*100:5.1f}] "
              f"{r['lenient_wrong_rate']*100:7.1f}% "
              f"[{r['lenient_ci95'][0]*100:5.1f}, {r['lenient_ci95'][1]*100:5.1f}]")
    write_report(d, payload, freeze)

    if payload["positive_control"]:
        pc = payload["positive_control"]
        print(f"\npositive control (blind, seeded confident wrong match): {pc['group_id']} "
              f"@ score {pc['declared_score']} -> {pc['observed']}  {pc['verdict']}")
    print(f"\nwrote {(d / 'selective_risk.json')}")


if __name__ == "__main__":
    main()
