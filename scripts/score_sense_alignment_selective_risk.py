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
eligible population of stratum s — the GOLD-EXCLUDED eligible rows, not every
aligned row. Intervals are a HEURISTIC envelope: the wider of a plug-in
stratified normal interval (variance sum_s (N_s/N)^2 * p_s(1-p_s)/n_s) and an
unweighted Wilson interval on the pooled counts. Pure-outcome strata contribute
zero estimated variance and the Wilson half targets the unweighted mixture, so
the envelope is NOT shown to reach nominal 95 % coverage (H5070 Astra review,
22-09-2026). A stratum with no adjudicated card contributes its weight but no
information and is reported as such.

Two rates are printed for every scope, never one:

  strict  — every `different` verdict counts as a wrong match;
  lenient — `different` verdicts flagged `near_miss` (metonymy, POS variant,
            sibling referent) are excluded.

These are two rubric readings, not bounds on the truth. A third sensitivity,
`unsure` counted as wrong, is reported beside them.

The synthetic positive control is EXCLUDED from every rate and reported
separately as a pipeline check.

Reads  data/concordance/selective_risk/review_deck.tsv
       data/concordance/selective_risk/adjudication_h5070.tsv
       data/concordance/selective_risk/population_freeze.json
       data/concordance/selective_risk/canary_key.json
       data/concordance/selective_risk/adjudication_h5070_blind2.tsv  (optional)
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
SCOPES = [("all eligible (gold-excluded)", BANDS, 0.0),
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


def agreement(a_rows, b_rows):
    """Raw agreement and Cohen's kappa over same/different/unsure on shared cards."""
    b = {r["card"]: r["verdict"] for r in b_rows}
    pairs = [(r["verdict"], b[r["card"]]) for r in a_rows if r["card"] in b]
    n = len(pairs)
    if not n:
        return None
    labels = sorted({x for p in pairs for x in p})
    po = sum(1 for x, y in pairs if x == y) / n
    pe = sum((sum(1 for x, _ in pairs if x == l) / n) * (sum(1 for _, y in pairs if y == l) / n)
             for l in labels)
    kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
    confusion = {}
    for x, y in pairs:
        confusion[f"{x}->{y}"] = confusion.get(f"{x}->{y}", 0) + 1
    return {"cards": n, "raw_agreement": round(po, 4), "cohen_kappa": round(kappa, 4),
            "confusion_adj1_to_adj2": dict(sorted(confusion.items()))}


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
    L.append("_Created: 20-09-2026 · Last updated: 22-09-2026_")
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
    L.append("(metonymy, POS variant, sibling referent); `unsure→wrong` additionally counts every")
    L.append("`unsure` verdict as wrong. These are rubric readings, not bounds on the truth.")
    L.append(f"Rates are stratified estimates re-weighted to the **{r[0]['eligible_population']:,} gold-excluded eligible rows**,")
    L.append(f"not to all {payload['population_aligned']:,} aligned rows, and never raw deck fractions.")
    L.append("Intervals are a heuristic envelope (wider of a plug-in stratified normal and an unweighted")
    L.append("pooled Wilson interval); they are **not** shown to reach nominal 95 % coverage.")
    L.append("")
    L.append("| scope | eligible rows | coverage | cards | strict wrong-match | ~95 % CI | lenient | ~95 % CI | unsure→wrong |")
    L.append("|---|---:|---:|---:|---:|---|---:|---|---:|")
    for x in r:
        L.append(f"| {x['scope']} | {x['eligible_population']:,} | {x['coverage_of_all_groups']*100:.2f} % | "
                 f"{x['cards_adjudicated']} | {x['strict_wrong_rate']*100:.1f} % | "
                 f"{x['strict_ci95'][0]*100:.1f}–{x['strict_ci95'][1]*100:.1f} % | "
                 f"{x['lenient_wrong_rate']*100:.1f} % | "
                 f"{x['lenient_ci95'][0]*100:.1f}–{x['lenient_ci95'][1]*100:.1f} % | "
                 f"{x['unsure_as_wrong_rate']*100:.1f} % |")
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
        L.append(f"   Adjudicator 1 labelled it `{pc['observed']}`. **Blindness for adjudicator 1 is not provable from")
        L.append("   the artifacts:** the frozen deck TSV gave the canary `stratum_eligible=0` and")
        L.append("   `population_share=0`, which no real card carries (caught by the Astra review, 22-09-2026).")
        L.append("   The rendered cards hide those columns, but nothing records that only the rendering was read.")
        b2 = pc.get("blind_adjudicator_2")
        if b2:
            L.append(f"   **Blind re-test:** {b2['adjudicator']} labelled the rendered cards only, never told a")
            L.append(f"   control existed, and returned `{b2['observed']}` on the canary — **{b2['verdict']}**.")
        L.append("   The sampler now dresses the canary in its stratum's metadata; the frozen deck reproduces")
        L.append("   only with `--legacy-canary-metadata`. The control is excluded from every rate above.")
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
    ag = payload.get("inter_adjudicator_agreement")
    if ag:
        L.append(f"1. **Rates rest on adjudicator 1.** Opus 5 labelled all 60 cards; a blind second pass")
        L.append(f"   ({payload['positive_control']['blind_adjudicator_2']['adjudicator']}) agrees on {ag['raw_agreement']*100:.0f} % of them,")
        L.append(f"   Cohen's κ = {ag['cohen_kappa']:.2f} over same/different/unsure (confusion in the JSON). Both are")
        L.append("   agents; neither is the human acceptance vote. The reused H3910 judge kappa (0.9022)")
        L.append("   belongs to a different judge on a different population and does not transfer.")
    else:
        L.append("1. **Single adjudicator.** One agent (Opus 5) labelled all 60 cards; there is no second")
        L.append("   adjudicator and therefore no inter-annotator agreement for this deck.")
    L.append("2. **Evidence is the card, not the source.** Verdicts rest on the glosses carried in the")
    L.append("   table. A truncated gloss can make a correct alignment look wrong and vice versa;")
    L.append("   `C011` and `C014` are explicit instances of contentless glosses; both are `unsure`")
    L.append("   (`C014` was relabelled from `different` after the Astra review).")
    L.append("3. **Band resolution only.** Equal-per-band allocation resolves the curve at the band")
    L.append("   boundaries (0.40, 0.70) and nowhere else; a finer threshold sweep needs a larger deck.")
    L.append("4. **Selection limits.** Cards are drawn only from rows the aligner already aligned and")
    L.append("   only from the gold-excluded remainder, so this measures precision, never recall.")
    L.append("5. **Strata without cards contribute weight but no information** where listed in the JSON.")
    L.append("")
    L.append("_Гасунс_")
    (d / "SELECTIVE_RISK_REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- H5252 channel mode
#
# A deck frozen with `--stratify-channel <dict>` (H5252) is scored here instead of
# by the H5070 path above, which stays byte-for-byte what it was. Strata are score
# band x (carries the channel / does not); verdict files carry only
# card/verdict/near_miss/failure_shape/note and are joined to the deck by card, so
# the adjudicator never needed a single metadata column.

import re as _re

DHATU_MARKERS = _re.compile(
    r"kavikalpa|\((?:adanta-?\s*)?(?:bhvā|curā|adā|divā|tudā|rudhā|tanā|kryā|svā|juhotyā)"
    r"|\b(?:seṭ|aniṭ|veṭ)\b")


def dhatu_marked(gloss):
    """Mechanical second lens: does the SKD text read as a dhātupāṭha entry?
    Line-break hyphens are closed first (`kavi- kalpadrumaḥ`)."""
    return bool(DHATU_MARKERS.search(_re.sub(r"-\s+", "", gloss or "")))


# Post-review reclassification of the rubric's failure-shape LABEL (never the verdict).
# The frozen verdict files stay as written; the report counts both readings.
# C019 — Astra review of H5252 (22-09-2026): both adjudicators labelled it
# dhatu-vs-noun, but its PWG side is the preverb *ava* ('herab; weg'), not a noun.
SHAPE_RECLASSIFIED = {"C019": "dhatu-vs-indeclinable"}


def _channel_eligible(freeze, name):
    """Re-derive the channel's eligible rows from the primary table, guarded by
    the frozen hash, with the same group_id exclusions the sampler applied."""
    src = ROOT / freeze["source"]
    import hashlib
    if hashlib.sha256(src.read_bytes()).hexdigest() != freeze["source_sha256"]:
        return None, None
    rows = [r for r in load(src) if r["method"] != "singleton"]
    excluded = set()
    for g in freeze["gold_files"]:
        excluded |= {r["group_id"] for r in load(ROOT / "data/concordance" / g)}
    for p, meta in freeze.get("prior_decks_excluded", {}).items():
        ids = {r["group_id"] for r in load(ROOT / p)}
        ids.discard(meta.get("canary_skipped"))
        excluded |= ids
    chan = [r for r in rows if (r.get(f"{name}_gloss") or "").strip()]
    return chan, [r for r in chan if r["group_id"] not in excluded]


def _rate_block(label, weights, by_stratum, rules):
    strict, lenient, unsure_wrong = rules
    n_pop = sum(weights.values())
    sp, slo, shi, n_used, empty = stratified(by_stratum, weights, strict)
    lp, llo, lhi, _, _ = stratified(by_stratum, weights, lenient)
    up, ulo, uhi, _, _ = stratified(by_stratum, weights, unsure_wrong)
    return {"scope": label, "eligible_population": n_pop, "cards_adjudicated": n_used,
            "strict_wrong_rate": round(sp, 4), "strict_ci95": [round(slo, 4), round(shi, 4)],
            "lenient_wrong_rate": round(lp, 4), "lenient_ci95": [round(llo, 4), round(lhi, 4)],
            "unsure_as_wrong_rate": round(up, 4), "unsure_as_wrong_ci95": [round(ulo, 4), round(uhi, 4)],
            "strict_half_width_points": round((shi - slo) * 50, 1),
            "interval_method": "heuristic envelope, nominal coverage not established; "
                               "no finite-population correction (conservative)",
            "strata_without_cards": empty}


def score_channel(d, freeze, adj_path, blind2_path):
    name = freeze["stratify_channel"]
    canary = (json.loads((d / "canary_key.json").read_text(encoding="utf-8"))
              if (d / "canary_key.json").exists() else None)
    deck = {r["card"]: r for r in load(d / "review_deck.tsv")}
    verdicts = load(adj_path)
    assert {r["card"] for r in verdicts} == set(deck), "verdicts must cover the deck exactly"
    for r in verdicts:
        r.update({k: deck[r["card"]][k] for k in ("group_id", "stratum", "lemma_slp1", "skd_gloss")
                  if k in deck[r["card"]]})
    is_canary = lambda r: canary is not None and r["group_id"] == canary["canary_group_id"]
    real = [r for r in verdicts if not is_canary(r)]
    canary_rows = [r for r in verdicts if is_canary(r)]

    rules = (lambda r: r["verdict"] == "different",
             lambda r: r["verdict"] == "different" and r["near_miss"] != "yes",
             lambda r: r["verdict"] in ("different", "unsure"))
    weights_all = {m["stratum"]: m["eligible"] for m in freeze["strata"]}
    by_stratum = defaultdict(list)
    for r in real:
        by_stratum[r["stratum"]].append(r)

    own = {s: n for s, n in weights_all.items() if s.split("|")[1] == name}
    rest = {s: n for s, n in weights_all.items() if s.split("|")[1] != name}
    scopes = [_rate_block(f"{name} channel, all bands", own, by_stratum, rules)]
    for b in BANDS:
        scopes.append(_rate_block(f"{name} | {b}", {s: n for s, n in own.items() if s.startswith(b)},
                                  by_stratum, rules))
    scopes.append(_rate_block(f"non-{name} comparison, all bands", rest, by_stratum, rules))
    scopes.append(_rate_block("all eligible (pooled, re-weighted)", weights_all, by_stratum, rules))

    # failure shapes among the channel's strict wrong matches
    chan_cards = [r for r in real if r["stratum"].split("|")[1] == name]
    wrong = [r for r in chan_cards if r["verdict"] == "different"]
    shapes = defaultdict(int)
    for r in wrong:
        shapes[r.get("failure_shape") or "n/a"] += 1
    k = shapes.get("dhatu-vs-noun", 0)
    lo, hi = wilson(k, len(wrong))
    dhatu_rate = _rate_block(f"{name} rows that are dhatu-vs-noun wrong matches", own, by_stratum,
                             (lambda r: r["verdict"] == "different" and r.get("failure_shape") == "dhatu-vs-noun",) * 3)

    # mechanical second lens over the population and against the verdicts
    chan_all, chan_elig = _channel_eligible(freeze, name)
    marker = None
    if chan_all is not None:
        conf = defaultdict(int)
        for r in chan_cards:
            conf[f"{'marked' if dhatu_marked(r.get('skd_gloss')) else 'unmarked'}->{r['verdict']}"] += 1
        marker = {"pattern": DHATU_MARKERS.pattern,
                  "channel_rows_all": len(chan_all),
                  "channel_rows_marked_all": sum(dhatu_marked(r[f"{name}_gloss"]) for r in chan_all),
                  "channel_rows_eligible": len(chan_elig),
                  "channel_rows_marked_eligible": sum(dhatu_marked(r[f"{name}_gloss"]) for r in chan_elig),
                  "deck_marker_vs_verdict": dict(sorted(conf.items()))}

    blind2 = load(blind2_path) if blind2_path and blind2_path.exists() else None
    agree = agree_chan = shape_agree = None
    if blind2 is not None:
        agree = agreement(real, blind2)
        agree_chan = agreement(chan_cards, blind2)
        b2 = {r["card"]: r for r in blind2}
        both = [r for r in wrong if b2.get(r["card"], {}).get("verdict") == "different"]
        shape_agree = {"cards_both_different": len(both),
                       "same_failure_shape": sum(1 for r in both
                                                 if r.get("failure_shape") == b2[r["card"]].get("failure_shape"))}
    b2_by_card = {r["card"]: r for r in blind2} if blind2 else {}
    sens2 = None
    if blind2:
        # sensitivity: the same estimator over adjudicator 2's verdicts
        by2 = defaultdict(list)
        for r in real:
            v = b2_by_card[r["card"]]
            by2[r["stratum"]].append({"verdict": v["verdict"], "near_miss": v["near_miss"]})
        sens2 = _rate_block(f"{name} channel, all bands (adjudicator 2 verdicts)", own, by2, rules)
    pc = None
    if canary:
        obs1 = canary_rows[0]["verdict"] if canary_rows else None
        obs2 = b2_by_card.get(canary_rows[0]["card"], {}).get("verdict") if canary_rows and blind2 else None
        pc = {"group_id": canary["canary_group_id"], "card": canary_rows[0]["card"] if canary_rows else None,
              "construction": canary["construction"], "declared_score": canary["declared_score"],
              "expected": canary["expected_verdict"],
              "adjudicator_1": {"observed": obs1, "verdict": "PASS" if obs1 == canary["expected_verdict"] else "FAIL"},
              "adjudicator_2": ({"observed": obs2, "verdict": "PASS" if obs2 == canary["expected_verdict"] else "FAIL"}
                                if blind2 else None)}

    payload = {
        "handoff": freeze["handoff"],
        "source_sha256": freeze["source_sha256"],
        "seed": freeze["seed"],
        "stratify_channel": name,
        "population_aligned": freeze["population_aligned"],
        "eligible_after_exclusions": freeze["eligible_after_gold_exclusion"],
        "prior_decks_excluded": freeze.get("prior_decks_excluded"),
        "newly_adjudicated_cards": len(real),
        "channel_cards": len(chan_cards),
        "unsure_cards": sum(1 for r in real if r["verdict"] == "unsure"),
        "rates": scopes,
        "failure_shapes_among_channel_wrong": dict(sorted(shapes.items())),
        "dhatu_vs_noun_share_of_channel_wrong": {"k": k, "n": len(wrong),
                                                 "share": round(k / len(wrong), 4) if wrong else None,
                                                 "wilson95": [round(lo, 4), round(hi, 4)]},
        "dhatu_vs_noun_rate_of_channel_rows": dhatu_rate,
        "shape_reclassified_after_review": {c: SHAPE_RECLASSIFIED[c] for c in SHAPE_RECLASSIFIED
                                            if any(r["card"] == c for r in wrong)},
        "dhatu_vs_noun_strict_count": sum(1 for r in wrong if r.get("failure_shape") == "dhatu-vs-noun"
                                          and r["card"] not in SHAPE_RECLASSIFIED),
        "dhatu_marker_lens": marker,
        "adjudicator_2_sensitivity": sens2,
        "inter_adjudicator_agreement_all": agree,
        "inter_adjudicator_agreement_channel": agree_chan,
        "failure_shape_agreement": shape_agree,
        "positive_control": pc,
        "cards": [{k2: r.get(k2) for k2 in ("card", "group_id", "stratum", "verdict", "near_miss",
                                             "failure_shape")} for r in real],
    }
    (d / "channel_risk.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
    for x in scopes + [dhatu_rate]:
        print(f"{x['scope']:44s} N={x['eligible_population']:5d} n={x['cards_adjudicated']:3d} "
              f"strict {x['strict_wrong_rate']*100:5.1f}% [{x['strict_ci95'][0]*100:5.1f},{x['strict_ci95'][1]*100:5.1f}] "
              f"lenient {x['lenient_wrong_rate']*100:5.1f}% unsure->wrong {x['unsure_as_wrong_rate']*100:5.1f}%")
    print("shapes", dict(shapes), "marker", marker and {k2: v for k2, v in marker.items() if k2 != "pattern"})
    print("agreement", agree, agree_chan, shape_agree)
    print("control", pc)
    return payload


ADJ1 = "Claude Opus 5.5 (claude-opus-5-5), executor"
ADJ2 = "Claude Fable 5.1 (claude-fable-5-1), fresh context, rendered cards only"


def _pct(x):
    return f"{x*100:.1f} %"


def _ci(c):
    return f"{c[0]*100:.1f}–{c[1]*100:.1f} %"


def _cell(t):
    return str(t).replace("|", "\\|")


def write_channel_report(d, p, freeze):
    """Human-readable twin of channel_risk.json (H5252 channel mode)."""
    name = p["stratify_channel"]
    N = name.upper()
    rates = {x["scope"]: x for x in p["rates"]}
    ch = rates[f"{name} channel, all bands"]
    comp = rates[f"non-{name} comparison, all bands"]
    pooled = rates["all eligible (pooled, re-weighted)"]
    dv = p["dhatu_vs_noun_share_of_channel_wrong"]
    dr = p["dhatu_vs_noun_rate_of_channel_rows"]
    mk = p["dhatu_marker_lens"]
    pc = p["positive_control"]
    ag, agc, sa = (p["inter_adjudicator_agreement_all"], p["inter_adjudicator_agreement_channel"],
                   p["failure_shape_agreement"])
    prior = next(iter((p.get("prior_decks_excluded") or {}).values()), None)
    L = []
    L += ["# ŚKDR (skd) channel wrong-match rate — SKD-stratified sense-alignment deck", "",
          "_Created: 22-09-2026 · Last updated: 22-09-2026_", "",
          f"Generated by `scripts/score_sense_alignment_selective_risk.py` ({p['handoff']}, channel mode). "
          "Do not hand-edit: re-run the script. Machine twin: `channel_risk.json`.", "",
          "## What this is, and what it is not", "",
          "An **agent-adjudicated** size of one known defect: the ŚKDR (Śabdakalpadruma) channel of the",
          "aligned-sense table, where the H5070 deck found 3 of 3 cards wrong. It is **not** the family's",
          "acceptance precision (that stays behind the human-vote fence in `SENSE_ALIGNMENT_BUILD_REPORT.md`),",
          "and it changes no serving threshold and no aligner constant.", "",
          f"- population hash `{p['source_sha256']}` (same table as H5070), seed {p['seed']}",
          f"- {N} channel: {mk['channel_rows_all'] if mk else '—'} aligned rows carry an {N} gloss; "
          f"**{ch['eligible_population']}** remain after excluding the H3910/W2 gold cards"
          + (f" and the {prior['cards_excluded']} real H5070 deck cards" if prior else "")
          + ". Every one is a PWG + ŚKDR pair joined by `attrib` (PWG cites *skdr*).",
          f"- {p['newly_adjudicated_cards']} newly adjudicated cards: {p['channel_cards']} {N} "
          f"+ {p['newly_adjudicated_cards'] - p['channel_cards']} non-{N} comparison, plus one blind canary",
          f"- adjudicators: {ADJ1}; {ADJ2}", "",
          "## Design, frozen before any card was read", "",
          f"Strata = score band × (carries an {N} gloss / does not). The {N} stratum got a fixed budget",
          f"of {freeze['channel_budget']} cards spread over bands in proportion to size; the remaining",
          f"{freeze['target'] - freeze['channel_budget']} went to the complement, also proportionally. The freeze (population hash, seed,",
          "allocation, deck, sealed canary key) was committed before rendering; the verdicts of adjudicator 1",
          "were committed before the canary key was opened. Adjudicators saw only",
          "`render_selective_risk_deck.py --width 400` output — no score, stratum, method or group id.",
          f"The {N} channel is visible on the card by construction (an `SKD (sa)` line); that cannot be",
          "blinded and is why the canary and the second adjudicator matter.", "",
          "| stratum | eligible rows | cards |", "|---|---:|---:|"]
    for m in sorted(freeze["strata"], key=lambda m: (m["channel"] != name, BANDS.index(m["score_band"]))):
        L.append(f"| {_cell(m['stratum'])} | {m['eligible']:,} | {m['sampled']} |")
    L += ["", f"## {N} channel wrong-match rate", "",
          "`strict` counts every `different`; `lenient` drops `near_miss` ones (POS variant, sibling sense);",
          "`unsure→wrong` also counts every `unsure`. Stratified estimates re-weighted to eligible rows.",
          "Intervals are the H5070 heuristic envelope (wider of a plug-in stratified normal and a pooled",
          "Wilson); they ignore the finite-population correction, which here (45 of 90 rows read) would",
          "narrow them — so they are conservative, and still **not** shown to reach nominal 95 % coverage.", "",
          "| scope | eligible rows | cards | strict | ~95 % CI | lenient | ~95 % CI | unsure→wrong | ~95 % CI |",
          "|---|---:|---:|---:|---|---:|---|---:|---|"]
    for key in [f"{name} channel, all bands"] + [f"{name} | {b}" for b in BANDS] + \
               [f"non-{name} comparison, all bands", "all eligible (pooled, re-weighted)"]:
        x = rates[key]
        L.append(f"| {_cell(key)} | {x['eligible_population']:,} | {x['cards_adjudicated']} | "
                 f"{_pct(x['strict_wrong_rate'])} | {_ci(x['strict_ci95'])} | "
                 f"{_pct(x['lenient_wrong_rate'])} | {_ci(x['lenient_ci95'])} | "
                 f"{_pct(x['unsure_as_wrong_rate'])} | {_ci(x['unsure_as_wrong_ci95'])} |")
    hw = ch["strict_half_width_points"]
    s2 = p.get("adjudicator_2_sensitivity")
    if s2:
        L.append(f"| *sensitivity: {name} channel on adjudicator 2's verdicts* | {s2['eligible_population']:,} | "
                 f"{s2['cards_adjudicated']} | {_pct(s2['strict_wrong_rate'])} | {_ci(s2['strict_ci95'])} | "
                 f"{_pct(s2['lenient_wrong_rate'])} | {_ci(s2['lenient_ci95'])} | "
                 f"{_pct(s2['unsure_as_wrong_rate'])} | {_ci(s2['unsure_as_wrong_ci95'])} |")
    L += ["", f"**The {N} channel is wrong about {_pct(ch['strict_wrong_rate'])} of the time** (strict; "
          f"{_ci(ch['strict_ci95'])}), against {_pct(comp['strict_wrong_rate'])} for the rest of the table in this deck "
          f"and 18.4 % pooled in H5070. The strict interval is ±{hw} points — "
          + ("inside" if hw < 15 else "**outside**") + " the ±15-point target.", "",
          "Within the channel the score does not help: "
          + ", ".join(f"{b.split()[0]} band {_pct(rates[f'{name} | {b}']['strict_wrong_rate'])}" for b in BANDS)
          + ". The attribution score measures the witness, not whether the ŚKDR entry is the right lexeme.", "",
          f"The pooled row is reported for continuity with H5070 only: the deck spends 3/4 of its cards on 1.3 % of",
          "the population, so the pooled Wilson half of the envelope describes the deck, not the table, and is",
          f"uninformative ({_ci(pooled['strict_ci95'])}). Its point estimate ({_pct(pooled['strict_wrong_rate'])}) agrees with H5070.", "",
          "## What shape the wrong matches take", ""]
    L.append("| failure shape | cards |")
    L.append("|---|---:|")
    for k2, v in p["failure_shapes_among_channel_wrong"].items():
        L.append(f"| {k2} | {v} |")
    strict_k = p["dhatu_vs_noun_strict_count"]
    slo, shi = wilson(strict_k, dv["n"])
    recl = p["shape_reclassified_after_review"]
    L += ["", f"**{dv['k']} of {dv['n']} {N} wrong matches ({_pct(dv['share'])}, Wilson {_ci(dv['wilson95'])}) set a "
          "ŚKDR root (dhātu) entry against a non-verbal PWG sense** — the Kavikalpadruma root entry for the same",
          "letter string (*kūṭa ... aprasāde*, *puṭa ... saṃsarge*). "
          f"**{strict_k} of the {dv['n']} ({_pct(strict_k / dv['n'])}, Wilson {_ci([slo, shi])}) are strictly root-vs-nominal** "
          "(a noun or an adjective: a plant, a stone, a house, *weiss*)"
          + (f"; {', '.join(recl)} carries the rubric's `dhatu-vs-noun` label from both adjudicators, but its PWG "
             "side is the preverb *ava* ('herab; weg'), not a noun (Astra review, 22-09-2026 — the verdict files "
             "are left as frozen, the label is re-read here)." if recl else "."),
          f"Re-weighted, root-vs-non-verbal wrong matches are {_pct(dr['strict_wrong_rate'])} ({_ci(dr['strict_ci95'])}) of "
          f"all eligible {N} rows. The other wrong matches sit on indeclinables: a sibling sense of *antareṇa*,",
          "and a compound's gloss (*one who loathes study*) set against the prefix entry *pari*.", "",
          "Not every dhātu card is wrong: where the PWG sense is itself the root's verbal meaning",
          "(*dhvaj* 'hin und her bewegen' ↔ *dhvaja gatau*) the pair is a true match.", "",
          f"{sum(1 for c in p['cards'] if c['verdict'] == 'unsure' and c['stratum'].endswith('|' + name))} of the "
          f"{p['unsure_cards']} `unsure` verdicts sit in the {N} channel: letter entries (*ā*, *sa*, *u*),",
          "the indeclinable *saha* (two rows with identical text), and *sudhā*, where the PWG gloss is contentless",
          "or the ŚKDR text is cut before the claimed sense. They are counted in `unsure→wrong` only.", ""]
    if mk:
        c = mk["deck_marker_vs_verdict"]
        L += ["## Mechanical second lens: the dhātu marker", "",
              "A regular expression over the ŚKDR text (Kavikalpadruma citation, a gaṇa tag such as `(bhvā`/`(curā`,",
              "or `seṭ`/`aniṭ`/`veṭ`; line-break hyphens closed) flags a dhātupāṭha entry without reading the",
              "PWG side. It is a lens, not a verdict, and feeds no rate. **It was written after adjudicator 1 had",
              "read this deck** (the closed line-break hyphen comes from one of its cards), so its deck figures below",
              "are in-sample; only the population counts are an out-of-deck reading.", "",
              "| | rows | marked as dhātu entry |", "|---|---:|---:|",
              f"| all aligned {N} rows | {mk['channel_rows_all']} | {mk['channel_rows_marked_all']} |",
              f"| eligible {N} rows | {mk['channel_rows_eligible']} | {mk['channel_rows_marked_eligible']} |", "",
              "On the deck, marker × adjudicator-1 verdict: "
              + ", ".join(f"{k2.replace('->', ' → ')} {v}" for k2, v in c.items()) + ".", ""]
    L += ["## Controls and agreement", ""]
    if pc:
        L.append(f"1. **Seeded confident wrong match (blind) — adjudicator 1 {pc['adjudicator_1']['verdict']}"
                 + (f", adjudicator 2 {pc['adjudicator_2']['verdict']}" if pc.get("adjudicator_2") else "")
                 + f".** `{pc['group_id']}` ({pc['card']}): {pc['construction'].lower()}, dressed at score "
                 f"{pc['declared_score']} in the metadata of the stratum it imitates (the H5070 fix). Its id is chosen "
                 "so it names no real row — H5070's `rajas#9` did, which the sampler now guards against. "
                 "Excluded from every rate.")
    L.append("2. **H5070 reproduction.** The H5070 deck, canary key and freeze reproduce byte-for-byte with "
             "`--legacy-canary-metadata`, and its report regenerates unchanged — the new options are additive.")
    L.append(f"3. **No double reading.** The {prior['cards_excluded'] if prior else 0} real H5070 cards are excluded by "
             "group_id (as the gold fence is); `group_id` is not unique in the table, so "
             f"{prior['aligned_rows_removed'] - prior['cards_excluded'] if prior else 0} sibling rows sharing a judged id left too, "
             "and the H5070 canary id was skipped so the real row it collides with stays eligible.")
    if ag:
        L.append(f"4. **Two blind adjudicators.** Over all {ag['cards']} real cards: raw agreement "
                 f"{ag['raw_agreement']*100:.0f} %, Cohen's κ = {ag['cohen_kappa']:.2f} (the whole deck); over the {agc['cards']} {N} cards alone: "
                 f"{agc['raw_agreement']*100:.0f} %, κ = {agc['cohen_kappa']:.2f} (confusion in the JSON). "
                 f"Where both said `different` on an {N} card ({sa['cards_both_different']}), they named the same "
                 f"failure shape on {sa['same_failure_shape']}. Rates above rest on adjudicator 1.")
    else:
        L.append("4. **Second adjudicator: PENDING** — no blind second verdict file yet.")
    L += ["", "## Recommendation (not applied)", "",
          f"The evidence supports one remedy, **recommended, not applied**: at alignment time, do not attach an",
          f"{N} sense whose text is a dhātupāṭha root entry to a PWG sense that is not itself verbal. On this deck the",
          "marker alone would have removed "
          + (f"{mk['deck_marker_vs_verdict'].get('marked->different', 0)} wrong matches and "
             f"{mk['deck_marker_vs_verdict'].get('marked->same', 0)} right one" if mk else "the dhātu wrong matches")
          + ". The one right match it would remove (*dhvaj*) has a PWG sense that is itself a root meaning, so the "
          "rule should fire only when the PWG side is nominal — a test this handoff does not build. "
          + (f"It would touch {mk['channel_rows_marked_all']} of {mk['channel_rows_all']} {N} rows, including gold-sample rows, "
             "so it needs the human acceptance vote's eyes before it changes the table." if mk else ""), "",
          "## Limitations", "",
          "1. **Agents, not the human vote.** Both adjudicators are models; neither is acceptance precision.",
          "2. **Evidence is the card.** Glosses are truncated at 400 characters; letter and indeclinable",
          "   entries are cut before the claimed sense and stay `unsure`.",
          f"3. **The channel is visible.** Adjudicators knew which cards were {N} cards; blindness covers score,",
          "   stratum and the canary, not the channel.",
          f"4. **The canary tests a non-{N} mismatch.** It shows the adjudicators do not wave through a confident",
          f"   wrong PWG/MW/Apte card; it does not test their {N} judgments. Adjudicator 1 is also the executor and",
          "   knew how the canary is built — its blindness is procedural (verdicts committed before the key was",
          "   opened), not provable. Adjudicator 2's is: it saw only the rubric and the rendered cards.",
          "5. **Heuristic intervals.** See above; no finite-population correction, nominal coverage unproven.",
          "6. **Precision only.** Cards come from rows the aligner aligned; nothing here measures recall.", "",
          "_Гасунс_"]
    (d / f"{N}_CHANNEL_RISK_REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", type=Path, default=SR)
    ap.add_argument("--adjudication", type=Path, default=None,
                    help="H5252 channel mode: verdict TSV (default adjudication_<handoff>.tsv)")
    ap.add_argument("--blind2", type=Path, default=None,
                    help="H5252 channel mode: second-adjudicator TSV (default adjudication_<handoff>_blind2.tsv)")
    a = ap.parse_args()
    d = a.dir
    freeze = json.loads((d / "population_freeze.json").read_text(encoding="utf-8"))
    if freeze.get("stratify_channel"):
        tag = freeze["handoff"].lower()
        payload = score_channel(d, freeze, a.adjudication or d / f"adjudication_{tag}.tsv",
                                a.blind2 or d / f"adjudication_{tag}_blind2.tsv")
        write_channel_report(d, payload, freeze)
        return
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
    unsure_wrong = lambda r: r["verdict"] in ("different", "unsure")

    total_groups = freeze["source_rows"]
    aligned = freeze["population_aligned"]
    results = []
    for label, bands, thr in SCOPES:
        w = {s: n for s, n in weights_all.items() if s.split("|")[0] in bands}
        n_pop = sum(w.values())
        cov = n_pop / total_groups
        sp, slo, shi, n_used, empty = stratified(by_stratum, w, strict)
        lp, llo, lhi, _, _ = stratified(by_stratum, w, lenient)
        up, _, _, _, _ = stratified(by_stratum, w, unsure_wrong)
        results.append({
            "scope": label, "threshold": thr,
            "eligible_population": n_pop,
            "coverage_of_all_groups": round(cov, 6),
            "abstention_of_all_groups": round(1 - cov, 6),
            "cards_adjudicated": n_used,
            "strict_wrong_rate": round(sp, 4), "strict_ci95": [round(slo, 4), round(shi, 4)],
            "lenient_wrong_rate": round(lp, 4), "lenient_ci95": [round(llo, 4), round(lhi, 4)],
            "unsure_as_wrong_rate": round(up, 4),
            "interval_method": "heuristic envelope, nominal coverage not established",
            "strata_without_cards": empty,
        })

    deck_by_card = {r["card"]: r for r in load(d / "review_deck.tsv")}
    conc = concentration(deck_by_card, real, freeze)
    unsure = sum(1 for r in real if r["verdict"] == "unsure")
    b2_path = d / "adjudication_h5070_blind2.tsv"
    blind2 = load(b2_path) if b2_path.exists() else None
    b2_meta = None
    if blind2 is not None and canary:
        canary_cards = {r["card"] for r in canary_rows}
        obs = next((r["verdict"] for r in blind2 if r["card"] in canary_cards), None)
        b2_meta = {"adjudicator": "Claude Sonnet 5 (claude-sonnet-5), fresh context, rendered cards only",
                   "observed": obs,
                   "verdict": "PASS" if obs == canary["expected_verdict"] else "FAIL"}
    agree = agreement(real, blind2) if blind2 is not None else None
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
        "inter_adjudicator_agreement": agree,
        "risk_coverage": results,
        "error_concentration_by_channel": conc,
        "positive_control": ({
            "group_id": canary["canary_group_id"],
            "construction": canary["construction"],
            "declared_score": canary["declared_score"],
            "expected": canary["expected_verdict"],
            "observed": canary_rows[0]["verdict"] if canary_rows else None,
            "verdict": "PASS" if canary_rows and canary_rows[0]["verdict"] == canary["expected_verdict"] else "FAIL",
            "blind_adjudicator_1": "not provable: frozen deck TSV carried zero stratum metadata on the canary",
            "blind_adjudicator_2": b2_meta,
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
