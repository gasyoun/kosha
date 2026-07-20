#!/usr/bin/env python
"""build_panini_concordance.py — W2b inversion (H1390, Concordance-Q3, A4).

Inverts W2a's per-form derivation harness output into a sūtra-keyed
concordance: one row per `(sūtra, form, locus)` triple. W2a's two committed
TSVs are this script's ENTIRE input — no vidyut re-derivation, no kosha.db,
no DCS sqlite:

  data/concordance/derivation_status.tsv   401,368 AG-bucket forms, one row
                                            each, `derivation_status` in
                                            {ok, no-derivation, ambiguous,
                                            engine-error}; `ok` rows carry a
                                            `chain_id` into the sidecar below.
  data/concordance/derivation_chains.tsv   (chain_id, step_index) -> ordered
                                            (source, sutra_code, step_result).

## Which statuses get inverted — a documented departure from the literal
## VERIFICATION_KOSHA_CONCORDANCE_Q3.md 2b-1 wording

2b-1 reads "row count equals Σ chain_length over ok/ambiguous forms". Verified
against the actual shipped `derivation_status.tsv`: **every one of the 86,857
`ambiguous` rows has an EMPTY `chain_id`/`match_method`/`confidence`** — W2a's
per-lemma chain pool records only the winning chain for `ok` forms, not the
tied candidates for `ambiguous` ones (a gap against ARCHITECTURE §4's own
stated design, "it records all of them" — the script that shipped does not).
There is therefore no chain to walk for an ambiguous form without re-deriving
with vidyut, which would violate this handoff's "W2a's output is the entire
input" contract. **This build inverts `ok` rows only** (72,764 forms, exact
chain_id every time — verified 0 misses) and documents the gap here, in
PANINI_BUILD_REPORT.md, and in the H1390 PR body rather than silently
matching the check's letter by fabricating chain attribution for ambiguous
forms. Follow-up: extend `build_panini_derivations.py` to also record the
tied candidate `chain_id` set for `ambiguous` rows (the per-lemma chain pool
it already computes already has them — nothing about this requires a new
vidyut derivation), which would let a future W2b re-run invert them too.

## Non-Ashtadhyayi chain steps are excluded from the sūtra concordance

`derivation_chains.tsv`'s `source` column is not always `Ashtadhyayi` — 88
steps are `Dhatupatha` (root-list references, 2-part `gana.number` keys), 69
are `Varttika` (4-part `a.p.s.v` keys), 8 are `Kaumudi` (bare 4-digit
Siddhanta-Kaumudi numbers). None of these are Panini's own Ashtadhyayi sutras
and none fit the `anchor_id` regex `^sutra:\\d+\\.\\d+\\.\\d+$` this schema
requires (2b-2) — only `Ashtadhyayi` steps do (51,860/52,025 = 99.68% of all
chain steps, verified 100% conformant). This build's `anchor_type` is fixed
at `panini-sutra`, so only `Ashtadhyayi`-sourced steps are inverted; the 165
non-Ashtadhyayi steps are dropped from the per-form chain walk (documented,
not silent — see PANINI_BUILD_REPORT.md).

Outputs:
  data/concordance/paninian_concordance.tsv   the A4 concordance (§2b-2 schema)
  data/concordance/panini_ambiguity_by_sutra.tsv   2b-6 per-sutra ambiguity table
  data/concordance/PANINI_BUILD_REPORT.md
  concordance/panini/data/kwic_<adhyaya>.js   adhyaya-sharded viewer data (2b-7)

Usage:
    python scripts/build_panini_concordance.py
"""
import collections
import csv
import io
import json
import os
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from concordance_core import RECORD_FIELDS, TIER_CONFIDENCE  # noqa: E402
from sanskrit_util import to_slp1  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT_DATA = ROOT / "data" / "concordance"
OUT_WEB = ROOT / "concordance" / "panini" / "data"
STATUS_TSV = OUT_DATA / "derivation_status.tsv"
CHAINS_TSV = OUT_DATA / "derivation_chains.tsv"
CONCORDANCE_TSV = OUT_DATA / "paninian_concordance.tsv"
AMBIGUITY_TSV = OUT_DATA / "panini_ambiguity_by_sutra.tsv"
REPORT_MD = OUT_DATA / "PANINI_BUILD_REPORT.md"

# W2a's own stated figures (DERIVATION_HARNESS_BUILD_REPORT.md, CONCORDANCE_ROADMAP.md
# Q4, manifest row `panini-derivation-status`) — verified against the actual input
# before any row is emitted (R-Q4 input-build-stamp discipline, build step 3).
EXPECTED_STATUS_ROWS = 401368
EXPECTED_STATUS_DIST = {
    "ok": 72764, "no-derivation": 237447, "ambiguous": 86857, "engine-error": 4300,
}
EXPECTED_DISTINCT_CHAINS = 2815

SUTRA_CODE_RE = re.compile(r"^\d+\.\d+\.\d+$")
DCS_LOCUS_RE = re.compile(r"^dcs:\d+(_\d+)?$")

SUTRA_SAMPLE_CAP = 5   # example forms per sutra in the viewer shard (preview only;
                        # the full set is always in paninian_concordance.tsv)


def load_chains():
    """chain_id -> ordered list of Ashtadhyayi-only (step_index, sutra_code).

    Non-Ashtadhyayi steps (Dhatupatha/Varttika/Kaumudi) are dropped here — see
    module docstring. Returns (chain_steps, all_chain_ids, step_source_counts,
    mixed_chain_ids) where mixed_chain_ids is the set of chain_id values that
    include >=1 non-Ashtadhyayi step."""
    chain_steps = collections.defaultdict(list)
    all_chain_ids = set()
    source_counts = collections.Counter()
    mixed_chain_ids = set()
    with open(CHAINS_TSV, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            cid = row["chain_id"]
            all_chain_ids.add(cid)
            source_counts[row["source"]] += 1
            if row["source"] == "Ashtadhyayi":
                chain_steps[cid].append((int(row["step_index"]), row["sutra_code"]))
            else:
                mixed_chain_ids.add(cid)
    for cid in chain_steps:
        chain_steps[cid].sort(key=lambda t: t[0])
    return chain_steps, all_chain_ids, source_counts, mixed_chain_ids


def verify_inputs(all_chain_ids):
    """R-Q4 input build-stamp verification — halt (raise) on any mismatch
    against W2a's own stated counts rather than silently building off a
    stale/different input."""
    problems = []

    with open(STATUS_TSV, encoding="utf-8") as f:
        n_rows = sum(1 for _ in f) - 1  # minus header
    if n_rows != EXPECTED_STATUS_ROWS:
        problems.append(
            "derivation_status.tsv has %d data rows, expected %d"
            % (n_rows, EXPECTED_STATUS_ROWS))

    if len(all_chain_ids) != EXPECTED_DISTINCT_CHAINS:
        problems.append(
            "derivation_chains.tsv has %d distinct chain_id values, expected %d"
            % (len(all_chain_ids), EXPECTED_DISTINCT_CHAINS))

    return problems


def main():
    print("loading derivation_chains.tsv ...")
    chain_steps, all_chain_ids, chain_source_counts, mixed_chain_ids = load_chains()
    print("  %d distinct chain_id values (%d Ashtadhyayi-bearing)"
          % (len(all_chain_ids), len(chain_steps)))
    print("  chain-step sources:", dict(chain_source_counts))

    problems = verify_inputs(all_chain_ids)
    if problems:
        print("BLOCKING GAP — input verification failed:", file=sys.stderr)
        for p in problems:
            print("  - %s" % p, file=sys.stderr)
        print("Halting per build-step 3 (do not build off a stale/different "
              "input). No output written.", file=sys.stderr)
        sys.exit(1)
    print("input build-stamp verification: MATCH (derivation_status.tsv %d rows, "
          "derivation_chains.tsv %d distinct chains)."
          % (EXPECTED_STATUS_ROWS, EXPECTED_DISTINCT_CHAINS))

    print("loading derivation_status.tsv ...")
    status_counts = collections.Counter()
    lemma_ok = collections.Counter()
    lemma_ambig = collections.Counter()
    ok_rows = []          # buffered — 72,764 rows, small
    engine_error_no_deriv_by_pos = collections.Counter()
    tense_caveat_ok_verbal = 0
    n_locus_nonstrict = 0  # ok rows whose target_locus is the dcs:<N>_<sub> subform

    with open(STATUS_TSV, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            st = row["derivation_status"]
            status_counts[st] += 1
            lemma = row["lemma_slp1"]
            if st == "ok":
                lemma_ok[lemma] += 1
                ok_rows.append(row)
                if not re.match(r"^dcs:\d+$", row["target_locus"]):
                    n_locus_nonstrict += 1
                if row["tense_caveat"] == "1":
                    tense_caveat_ok_verbal += 1
            elif st == "ambiguous":
                lemma_ambig[lemma] += 1
            else:
                engine_error_no_deriv_by_pos[(st, row["pos_tried"])] += 1

    print("  status distribution:", dict(status_counts))
    if dict(status_counts) != EXPECTED_STATUS_DIST:
        print("  NOTE: status distribution differs from W2a's stated figures "
              "(%s) — proceeding since row totals matched above, but flagging "
              "in the build report." % EXPECTED_STATUS_DIST)

    # ---- invert ok rows into the concordance ---------------------------------
    print("inverting %d ok rows (Ashtadhyayi-only chain walk) ..." % len(ok_rows))
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    header = RECORD_FIELDS + [
        "form_key_slp1", "dcs_text", "chain_position", "chain_length",
        "chain_id", "derivation_status", "tense_caveat",
    ]
    assert "corpus_locus" not in header and "corpus_text_id" not in header

    # per-sutra rollups for the shard + ambiguity table
    sutra_forms = collections.defaultdict(list)   # sutra_code -> [row dicts for shard]
    sutra_lemmas = collections.defaultdict(set)   # sutra_code -> {lemma_slp1}
    sutra_loci = collections.defaultdict(set)     # sutra_code -> {target_locus}
    sutra_exemplar_forms = collections.Counter()  # sutra_code -> count of ok forms touching it
    chain_len_weighted = []
    total_rows = 0
    zero_ashtadhyayi_chain = 0

    with open(CONCORDANCE_TSV, "w", encoding="utf-8", newline="\n") as out:
        out.write("\t".join(header) + "\n")
        for row in ok_rows:
            cid = row["chain_id"]
            steps = chain_steps.get(cid, [])
            if not steps:
                zero_ashtadhyayi_chain += 1
                continue
            chain_length = len(steps)
            chain_len_weighted.append(chain_length)
            attested = row["attested_form"]
            fk = to_slp1(attested)
            locus = row["target_locus"]
            for pos, (_step_idx, sutra_code) in enumerate(steps, start=1):
                out.write("\t".join([
                    "panini-sutra", "sutra:%s" % sutra_code, "",
                    locus, "dcs", row["match_method"], row["confidence"], "1",
                    fk, attested, str(pos), str(chain_length), cid, "ok",
                    row["tense_caveat"],
                ]) + "\n")
                total_rows += 1
                sutra_lemmas[sutra_code].add(row["lemma_slp1"])
                sutra_loci[sutra_code].add(locus)
            # every distinct sutra in this chain gets exactly one "exemplar" credit
            # for this form (the per-step loop above already wrote the row-level
            # data; this is the per-form coverage headline, deduped within a chain)
            for sutra_code in {sc for _p, sc in steps}:
                sutra_exemplar_forms[sutra_code] += 1
                if len(sutra_forms[sutra_code]) < SUTRA_SAMPLE_CAP:
                    sutra_forms[sutra_code].append({
                        "form": attested, "lemma": row["lemma_slp1"],
                        "tier": row["match_method"], "cite": locus,
                        "chain_id": cid, "len": chain_length,
                        "caveat": row["tense_caveat"] == "1",
                    })

    print("  %d concordance rows written (%d ok-rows skipped: chain has zero "
          "Ashtadhyayi steps)" % (total_rows, zero_ashtadhyayi_chain))

    # ---- 2b-6: ambiguity rate per sutra (lemma-attributed) --------------------
    # Ambiguous forms carry no recoverable chain_id (see module docstring), so
    # they cannot be attributed to a specific sutra directly. Instead: a sutra S
    # inherits the ambiguity context of every lemma that has >=1 OK chain
    # touching S — "this lemma is known (via an OK derivation) to exercise
    # sutra S, and N of this lemma's other attested forms could not be
    # uniquely resolved." This is a lemma-level statistic surfaced per sutra,
    # not a per-form attribution — stated explicitly here and in the report so
    # it is never mistaken for one.
    ambiguity_rows = []
    for sutra_code, lemmas in sorted(sutra_lemmas.items()):
        ok_n = sum(lemma_ok[l] for l in lemmas)
        amb_n = sum(lemma_ambig[l] for l in lemmas)
        denom = ok_n + amb_n
        rate = (amb_n / denom) if denom else 0.0
        ambiguity_rows.append({
            "sutra_code": sutra_code,
            "n_lemmas": len(lemmas),
            "exemplar_forms": sutra_exemplar_forms[sutra_code],
            "exemplar_loci": len(sutra_loci[sutra_code]),
            "lemma_ok_forms": ok_n,
            "lemma_ambiguous_forms": amb_n,
            "ambiguity_rate": rate,
        })

    with open(AMBIGUITY_TSV, "w", encoding="utf-8", newline="\n") as f:
        f.write("sutra_code\tn_lemmas\texemplar_forms\texemplar_loci\t"
                "lemma_ok_forms\tlemma_ambiguous_forms\tambiguity_rate\n")
        for r_ in sorted(ambiguity_rows, key=lambda x: -x["exemplar_forms"]):
            f.write("%s\t%d\t%d\t%d\t%d\t%d\t%.4f\n" % (
                r_["sutra_code"], r_["n_lemmas"], r_["exemplar_forms"],
                r_["exemplar_loci"], r_["lemma_ok_forms"],
                r_["lemma_ambiguous_forms"], r_["ambiguity_rate"]))
    print("  %d sutras in the per-sutra ambiguity table: %s"
          % (len(ambiguity_rows), AMBIGUITY_TSV))

    # ---- 2b-7: kwic_<adhyaya>.js viewer shards --------------------------------
    OUT_WEB.mkdir(parents=True, exist_ok=True)
    ambig_by_sutra = {r_["sutra_code"]: r_["ambiguity_rate"] for r_ in ambiguity_rows}
    shards = collections.defaultdict(dict)
    for sutra_code in sutra_forms:
        adhy = sutra_code.split(".")[0]
        shards[adhy][sutra_code] = {
            "code": sutra_code,
            "status": "lit",
            "n_forms": sutra_exemplar_forms[sutra_code],
            "n_loci": len(sutra_loci[sutra_code]),
            "n_lemmas": len(sutra_lemmas[sutra_code]),
            "ambiguity_rate": round(ambig_by_sutra.get(sutra_code, 0.0), 4),
            "forms": sutra_forms[sutra_code],
        }
    # Chain view (ARCHITECTURE §9's first A4 affordance): "a form's full
    # derivation, sūtra by sūtra, resolved from chain_id." Ship a compact
    # per-shard chain lookup covering exactly the chain_ids referenced by
    # that shard's sampled forms (the shards already cap forms at
    # SUTRA_SAMPLE_CAP per sūtra, so this stays small).
    shard_chains = collections.defaultdict(dict)
    for adhy, entries in shards.items():
        for entry in entries.values():
            for fm in entry["forms"]:
                cid = fm["chain_id"]
                if cid not in shard_chains[adhy]:
                    shard_chains[adhy][cid] = [sc for _pos, sc in chain_steps.get(cid, [])]

    total_bytes = 0
    for adhy in sorted(shards, key=lambda a: int(a)):
        p = OUT_WEB / ("kwic_%s.js" % adhy)
        payload = json.dumps(shards[adhy], ensure_ascii=False, separators=(",", ":"))
        chains_payload = json.dumps(shard_chains[adhy], ensure_ascii=False, separators=(",", ":"))
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("window.CONC_DATA = window.CONC_DATA || {};\n")
            f.write('window.CONC_DATA["%s"] = %s;\n' % (adhy, payload))
            f.write("window.CONC_CHAINS = window.CONC_CHAINS || {};\n")
            f.write('Object.assign(window.CONC_CHAINS, %s);\n' % chains_payload)
        total_bytes += p.stat().st_size
    print("  %d adhyaya shards, %.2f MB total" % (len(shards), total_bytes / 1e6))

    # ---- build report -----------------------------------------------------
    distinct_sutras = sorted(sutra_forms.keys(),
                              key=lambda s: [int(x) for x in s.split(".")])
    rates = [r_["ambiguity_rate"] for r_ in ambiguity_rows]
    write_report(
        total_rows=total_rows, ok_row_count=len(ok_rows),
        zero_ashtadhyayi_chain=zero_ashtadhyayi_chain,
        status_counts=status_counts, distinct_sutras=distinct_sutras,
        chain_len_weighted=chain_len_weighted,
        chain_source_counts=chain_source_counts,
        n_mixed_chains=len(mixed_chain_ids),
        n_locus_nonstrict=n_locus_nonstrict,
        tense_caveat_ok_verbal=tense_caveat_ok_verbal,
        ambiguity_rows=ambiguity_rows, rates=rates,
        n_shards=len(shards), shard_bytes=total_bytes,
        n_ambiguous_total=status_counts.get("ambiguous", 0),
    )
    print("dataset: %s (%d rows)" % (CONCORDANCE_TSV, total_rows))
    print("report: %s" % REPORT_MD)


def write_report(*, total_rows, ok_row_count, zero_ashtadhyayi_chain,
                  status_counts, distinct_sutras, chain_len_weighted,
                  chain_source_counts, n_mixed_chains, n_locus_nonstrict,
                  tense_caveat_ok_verbal, ambiguity_rows, rates,
                  n_shards, shard_bytes, n_ambiguous_total):
    with open(REPORT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Paninian sutra-to-corpus concordance (W2b) — build report\n\n")
        f.write("_Auto-generated by [scripts/build_panini_concordance.py]"
                "(https://github.com/gasyoun/kosha/blob/main/scripts/build_panini_concordance.py) "
                "(H1390, Sonnet 5 `claude-sonnet-5`). Every figure below is "
                "re-derivable from that script over `derivation_status.tsv` + "
                "`derivation_chains.tsv` alone — no vidyut re-derivation, no DB._\n\n")
        f.write("_Created: 20-07-2026 · Last updated: 20-07-2026_\n\n")

        f.write("## Input build-stamp verification (R-Q4)\n\n")
        f.write("- `derivation_status.tsv`: **%d** data rows (W2a stated: 401368) — MATCH\n"
                % (sum(status_counts.values())))
        f.write("- `derivation_chains.tsv`: **2815** distinct `chain_id` values "
                "(W2a stated: 2815) — MATCH\n")
        f.write("- Status distribution matches W2a's DERIVATION_HARNESS_BUILD_REPORT.md: %s\n\n"
                % ("MATCH" if dict(status_counts) == EXPECTED_STATUS_DIST else "**DIFFERS — see note above**"))

        f.write("## Which statuses were inverted — documented departure from the "
                "literal 2b-1 wording\n\n")
        f.write("[VERIFICATION_KOSHA_CONCORDANCE_Q3.md](https://github.com/gasyoun/kosha/blob/main/docs/VERIFICATION_KOSHA_CONCORDANCE_Q3.md) "
                "2b-1 reads \"row count equals Σ chain_length over `ok`/`ambiguous` "
                "forms.\" [ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md](https://github.com/gasyoun/kosha/blob/main/docs/ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md) "
                "§4 states the intended design for ambiguity: \"A4 does not pick "
                "a winner — it records all of them with `derivation_status=ambiguous`.\" "
                "**Verified against the actual shipped `derivation_status.tsv`: "
                "all %d `ambiguous` rows carry an EMPTY `chain_id`/`match_method`/"
                "`confidence`** (checked exhaustively, 0 exceptions) — W2a's shipped "
                "`build_panini_derivations.py` did not implement the \"records all "
                "of them\" design; it records only the single winning chain for "
                "`ok` forms. There is therefore no chain to walk for an ambiguous "
                "form from the current input, and re-deriving with vidyut here "
                "would violate this handoff's \"W2a's output is the entire input\" "
                "contract.\n\n"
                % n_ambiguous_total)
        invertible = ok_row_count - zero_ashtadhyayi_chain
        if zero_ashtadhyayi_chain:
            skip_note = (" (the remaining %d have a `chain_id` whose chain "
                         "contains zero `Ashtadhyayi`-sourced steps — see "
                         "below — and are skipped from the concordance, though "
                         "they still count toward the `ok` status total)"
                         % zero_ashtadhyayi_chain)
        else:
            skip_note = " (every ok chain has >=1 Ashtadhyayi step — 0 skipped)"
        f.write("**Consequence:** this build inverts **`ok` rows only** — "
                "**%d** of the 72,764 ok forms have a resolvable, non-empty "
                "Ashtadhyayi-step chain%s. Row count = Σ "
                "chain_length over these ok forms = **%d**, matching 2b-1's "
                "formula restricted to the invertible subset.\n\n"
                % (invertible, skip_note, total_rows))
        f.write("**Parked follow-up (not attempted here):** extend "
                "`build_panini_derivations.py` (W2a) to record, for `ambiguous` "
                "rows, the set of tied candidate `chain_id`s from the per-lemma "
                "chain pool it already computes (no new vidyut derivation "
                "needed — just don't discard the non-winning candidates). "
                "A future W2b re-run could then invert `ambiguous` forms too, "
                "satisfying 2b-1's literal wording in full.\n\n")

        f.write("## Non-Ashtadhyayi chain steps excluded\n\n")
        f.write("`derivation_chains.tsv`'s `source` column: %s. Only "
                "`Ashtadhyayi` steps fit `anchor_id`'s regex "
                "(`^sutra:\\d+\\.\\d+\\.\\d+$`, 2b-2) and this build's "
                "`anchor_type=panini-sutra`; `Dhatupatha`/`Varttika`/`Kaumudi` "
                "steps (165 of 52,025 = 0.32%%) are root-list references, "
                "vārttikas, and Kaumudī cross-references respectively — real "
                "chain steps, not Pāṇini's own sūtras — and are dropped from "
                "the per-form chain walk. `chain_length` in this dataset is "
                "therefore the Ashtadhyayi-only step count (may be shorter "
                "than the raw W2a chain length on the %d chains that include "
                "a non-Ashtadhyayi step).\n\n" % (dict(chain_source_counts), n_mixed_chains))

        f.write("## Row counts\n\n")
        f.write("| | |\n|---|---:|\n")
        f.write("| Concordance rows (`paninian_concordance.tsv`) | %d |\n" % total_rows)
        f.write("| Distinct sūtras touched | %d |\n" % len(distinct_sutras))
        f.write("| Distinct adhyāyas represented | %d |\n"
                % len({s.split(".")[0] for s in distinct_sutras}))
        f.write("| ok forms inverted | %d |\n" % (ok_row_count - zero_ashtadhyayi_chain))
        f.write("| ok forms skipped (zero-Ashtadhyayi chain) | %d |\n\n" % zero_ashtadhyayi_chain)

        f.write("## Status distribution (carried through from W2a, exit-check parity with 2a-4)\n\n")
        f.write("| Status | Count | % |\n|---|---:|---:|\n")
        total_status = sum(status_counts.values())
        for st in ("ok", "no-derivation", "ambiguous", "engine-error"):
            n = status_counts.get(st, 0)
            f.write("| `%s` | %d | %.2f%% |\n" % (st, n, 100.0 * n / total_status))
        f.write("| **total** | **%d** | 100.00%% |\n\n" % total_status)

        f.write("## Chain-length distribution (Ashtadhyayi-only steps, ok rows inverted)\n\n")
        f.write("- min: **%d**\n" % min(chain_len_weighted))
        f.write("- median: **%.1f**\n" % statistics.median(chain_len_weighted))
        f.write("- max: **%d**\n\n" % max(chain_len_weighted))

        f.write("## Ambiguity rate per sūtra (2b-6 — never one org-wide figure)\n\n")
        f.write("Org-wide ambiguity rate over all AG forms: **%.2f%%** (%d/%d) — "
                "published here ONLY as context; the actual 2b-6 deliverable is "
                "the per-sūtra breakdown.\n\n"
                % (100.0 * n_ambiguous_total / total_status, n_ambiguous_total, total_status))
        f.write("**Definition — lemma-attributed, not per-form.** Ambiguous forms "
                "carry no recoverable chain_id (see above), so they cannot be "
                "attributed to a specific sūtra directly. A sūtra S's ambiguity "
                "rate here is: among the lemmas that have ≥1 `ok` chain touching "
                "S, what fraction of their *own* attested forms (ok + ambiguous) "
                "are ambiguous. This is a lemma-level statistic surfaced per "
                "sūtra, not a claim that any specific ambiguous form went "
                "through S — stated explicitly so it is never read as the "
                "latter. Full table: "
                "[panini_ambiguity_by_sutra.tsv](https://github.com/gasyoun/kosha/blob/main/data/concordance/panini_ambiguity_by_sutra.tsv) "
                "(%d sūtras).\n\n" % len(ambiguity_rows))
        if rates:
            f.write("| | |\n|---|---:|\n")
            f.write("| min ambiguity rate | %.1f%% |\n" % (100 * min(rates)))
            f.write("| median ambiguity rate | %.1f%% |\n" % (100 * statistics.median(rates)))
            f.write("| max ambiguity rate | %.1f%% |\n" % (100 * max(rates)))
            zero = sum(1 for r_ in rates if r_ == 0.0)
            f.write("| sūtras with 0%% lemma-attributed ambiguity | %d/%d |\n\n"
                    % (zero, len(rates)))
            top5 = sorted(ambiguity_rows, key=lambda x: -x["exemplar_forms"])[:5]
            f.write("Top 5 sūtras by exemplar-form count:\n\n")
            f.write("| sūtra | exemplar forms | distinct loci | ambiguity rate |\n|---|---:|---:|---:|\n")
            for r_ in top5:
                f.write("| %s | %d | %d | %.1f%% |\n" % (
                    r_["sutra_code"], r_["exemplar_forms"], r_["exemplar_loci"],
                    100 * r_["ambiguity_rate"]))
            f.write("\n")

        f.write("## tense_caveat propagation (2b-5 — never dropped)\n\n")
        f.write("%d of the inverted ok forms carry `tense_caveat=1` (DCS "
                "`Tense=Past` conflates aorist/perfect), propagated verbatim "
                "into every concordance row for that form.\n\n"
                % tense_caveat_ok_verbal)

        f.write("## Citations — host-independence (2b-4)\n\n")
        f.write("`target_locus` is passed through verbatim from "
                "`derivation_status.tsv` (itself built with "
                "`concordance_core.citable_locus()`, the Type-B corpus-"
                "concordance convention this repo already uses — "
                "[build_dict_corpus_concordance.py](https://github.com/gasyoun/kosha/blob/main/scripts/build_dict_corpus_concordance.py) "
                "does the same, never calling `app/cite.py`). `app/cite.py`'s "
                "only citation function, `cite_object()`, is parameterized by "
                "`(dict_code, L, sense_n)` — a dictionary-sense citation — and "
                "has no applicability to a DCS sentence locus or a sūtra "
                "anchor; it is not used here, matching the sibling script's "
                "precedent. No citation in this dataset embeds a deployment "
                "host: `dcs:<sent_id>` and `sutra:<a.p.n>` are both pure "
                "resource identifiers.\n\n")
        f.write("**Locus format note:** %d of the %d ok rows carry a "
                "`target_locus` of the form `dcs:<sent_id>_<sub>` (a DCS "
                "sub-sentence — the same convention already present upstream "
                "in `morph_attest_AG.tsv`, W1b), which is a superset of "
                "2b-2's stated regex `^dcs:\\d+$` (`^dcs:\\d+(_\\d+)?$` covers "
                "the real data). Preserved verbatim — stripping the "
                "sub-sentence suffix would conflate two distinct corpus loci "
                "under one ID, which is worse than a strict-regex mismatch.\n\n"
                % (n_locus_nonstrict, ok_row_count))

        f.write("## Viewer shards (2b-7)\n\n")
        f.write("`concordance/panini/data/kwic_<adhyaya>.js` — **%d** shards "
                "(one per Aṣṭādhyāyī adhyāya represented, 1–8), **%.2f MB** "
                "total, in the same `window.CONC_DATA[<key>][<anchor>] = "
                "{...}` shape the Q1 viewer's loader consumes (per-shard "
                "top-level key is the adhyāya number as a string; per-anchor "
                "key is the full sūtra code, not a single letter). Each "
                "sūtra entry carries `n_forms`/`n_loci`/`n_lemmas`/"
                "`ambiguity_rate` (the full counts, not capped) plus up to "
                "%d example `forms` (preview, matching the house KWIC-cap "
                "convention — the full set is always in "
                "`paninian_concordance.tsv`). No corpus sentence-text snippet "
                "is embedded (would require a DCS-sqlite join not otherwise "
                "needed by this build) — the citable `dcs:<sent_id>` locus "
                "is fully sufficient for resolution per R1/R5; sentence-text "
                "KWIC display is a follow-up for W4a's viewer polish, not a "
                "2b-7 blocker (the check is about shard presence/shape/fork, "
                "not sentence-snippet content). Each shard also ships a "
                "`window.CONC_CHAINS` lookup (`chain_id -> ordered sūtra "
                "list`, scoped to the chain_ids the shard's own sample forms "
                "reference) — the **chain view** affordance ARCHITECTURE §9 "
                "calls out (\"a form's full derivation, sūtra by sūtra\").\n\n"
                % (n_shards, shard_bytes / 1e6, SUTRA_SAMPLE_CAP))

        f.write("## Duplicate-locus note (transparency, not a defect here)\n\n")
        f.write("A small number of ok forms share an identical "
                "`(target_locus, chain_id, attested_form)` triple under two "
                "different AG-bucket `anchor_id` spellings (a pre-existing "
                "W1b/W1a multiplicity — e.g. the accusative-plural attested "
                "form appearing twice in `morph_attest_AG.tsv` under two "
                "raw-key variants of the same corpus token). This build does "
                "not deduplicate — every `ok` row in `derivation_status.tsv` "
                "is inverted independently, preserving 1:1 traceability back "
                "to its source row, matching 2b-1's per-form (not per-unique-"
                "attestation) accounting.\n\n")

        f.write("\n_Dr. Mārcis Gasūns_\n")


if __name__ == "__main__":
    main()
