#!/usr/bin/env python
"""Cell-resolved triage of the csl-inflect give-back candidates (A3 residual).

`analyze_morph_giveback_set.py` narrowed A¬G's 196,378 keys to 5,656 candidates by three
subtractions that used only what the audit TSVs carried: DCS `upos`, `attested_via`, and
lemma-key equality. That left a set the report itself called "a candidate set needing human
triage, not a defect list", because bound stems still leaked through an exact-match filter.

They do not need a human. **DCS tags every token with `feat_case` / `feat_number` /
`feat_gender`, and that decides the question directly** — which is why this runs mechanically
rather than as a vote (standing rule: evidence-decidable cards are applied and reported,
never voted; sheets are for judgment).

Three facts the tagging settles:

  * `feat_case='Cpd'` is an explicit **compound-member** tag. `ātma` (< `ātman`) is `Cpd`
    2,499 times — a bound stem, exactly as suspected, but provable rather than guessed.
  * A **caseless** token whose `upos` is ADV / SCONJ / PART / ADP / CCONJ / INTJ is an
    indeclinable (`śvaḥ`, `yatrā`, `cin`, `niṣ`, `un`). A nominal paradigm generator does
    not owe these.
  * A token carrying a **real case + number** IS an inflected cell the generator missed,
    and the cell can be named: `tvāt` is `Abl Sing Neut` 3,420×, `striyaḥ` is
    `Nom Plur Fem` 454×.

**Correction to the H3782 record, carried into the report:** `rājñ` was cited there (and in
the PR) as an allomorphic bound stem that leaked past the filter. DCS tags it
`Voc Sing Masc` 880 times — by the corpus's own annotation it is an inflected cell, not a
stem. The caution was right in kind and wrong on that example.

For the rows that ARE real cells, one more mechanical split, because the two need different
upstream fixes:

  * **slot-conflict** — `inflections` HAS that `(lemma, gender, case, number)` slot and
    emits a *different* form. The generator disagrees with the corpus; a human comparing
    two concrete forms can rule quickly.
  * **coverage-hole** — the slot is absent from `inflections` entirely. A missing paradigm
    cell; no disagreement to adjudicate.

Only what survives as genuinely undecidable is offered for human judgment, and that goes out
as an interactive HTML review sheet on the vote hub — never a TSV (agent formats are not
human formats).

Deterministic, no network, read-only on both databases.
"""
import argparse
import collections
import csv
import json
import os
import sys
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _github_root(root):
    env = os.environ.get("GITHUB_ROOT")
    if env:
        return Path(env)
    for cand in (root.parent, root.parent / "GitHub", root.parent.parent,
                 root.parent.parent / "GitHub"):
        if (cand / "VisualDCS").is_dir() and (cand / "sanskrit-util").is_dir():
            return cand
    sys.exit("cannot locate the GitHub org root; set GITHUB_ROOT")


GH = _github_root(ROOT)
sys.path.insert(0, str(GH / "sanskrit-util" / "py"))
from sanskrit_util import from_slp1  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

DCS = GH / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"
KOSHA_DB = GH / "kosha" / "data" / "db" / "kosha.db"
CONC = ROOT / "data" / "concordance"
CAND = CONC / "morph_giveback_candidates.tsv"
OUT_TSV = CONC / "morph_giveback_triaged.tsv"
REPORT = CONC / "MORPHOLOGY_GIVEBACK_TRIAGE_REPORT.md"

INDECLINABLE_UPOS = {"ADV", "SCONJ", "PART", "ADP", "CCONJ", "INTJ"}
# DCS feat_case -> kosha inflections.gcase
CASE_MAP = {"Nom": "nom", "Acc": "acc", "Ins": "instr", "Instr": "instr", "Dat": "dat",
            "Abl": "abl", "Gen": "gen", "Loc": "loc", "Voc": "voc"}
NUM_MAP = {"Sing": "sg", "Dual": "du", "Du": "du", "Plur": "pl", "Pl": "pl"}
GEN_MAP = {"Masc": "m", "Neut": "n", "Fem": "f"}


def anusvara_variants(s):
    """Spellings of one word that differ only in how a word-final nasal is written."""
    out = {s}
    if s.endswith(("ṃ", "ṁ")):
        out.add(s[:-1] + "m")
    if s.endswith("m"):
        out.add(s[:-1] + "ṃ")
    return out


def human(n):
    return "{:,}".format(n)


def pct(a, b):
    return "0.00%" if not b else "%.2f%%" % (100.0 * a / b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=12)
    args = ap.parse_args()
    for p in (CAND, DCS, KOSHA_DB):
        if not p.exists():
            sys.exit("missing input: %s" % p)

    t0 = time.time()
    cands = {}
    with CAND.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            cands[r["attested_form"]] = r
    print("candidates: %s" % human(len(cands)), file=sys.stderr)

    # ---- pass 1: DCS morphological tags for exactly these forms --------------------
    # Both DCS keys, because the audit's attested side was the UNION of `token.form` and
    # `token.m_unsandhied` — a candidate recorded from the unsandhied column is invisible
    # to a `token.form` lookup, and 829 of them were (every single `no-dcs-token` row in
    # the first pass, all resolvable here).
    tags = collections.defaultdict(collections.Counter)   # form -> (case,num,gen) -> n
    caseless = collections.Counter()
    con = sqlite3.connect("file:%s?mode=ro" % DCS.as_posix(), uri=True)
    for form, unsand, fcase, fnum, fgen in con.execute(
            "SELECT form, m_unsandhied, feat_case, feat_number, feat_gender FROM token"):
        for key in (form, unsand):
            if not key or key not in cands:
                continue
            if fcase:
                tags[key][(fcase, fnum or "", fgen or "")] += 1
            else:
                caseless[key] += 1
            if form == unsand:
                break          # don't double-count a token whose two keys coincide
    con.close()
    print("DCS tags collected [%.0fs]" % (time.time() - t0), file=sys.stderr)

    # ---- pass 2: the generator's slots for the lemmas we care about ----------------
    want_lemmas = set()
    for form, r in cands.items():
        want_lemmas.add(r["dcs_lemma"])
    kdb = sqlite3.connect("file:%s?mode=ro" % KOSHA_DB.as_posix(), uri=True)
    # (lemma_iast, gender, case, number) -> set of generated forms (IAST)
    slots = collections.defaultdict(set)
    lemma_forms = collections.defaultdict(set)   # every form the generator has per lemma
    lemma_known = set()
    for form_slp1, lemma_slp1, gender, gcase, number in kdb.execute(
            "SELECT form_slp1, lemma_slp1, gender, gcase, number FROM inflections "
            "WHERE person IS NULL"):
        lem = from_slp1(lemma_slp1) if lemma_slp1 else ""
        if lem not in want_lemmas:
            continue
        lemma_known.add(lem)
        iast = from_slp1(form_slp1)
        slots[(lem, gender or "", gcase or "", number or "")].add(iast)
        lemma_forms[lem].add(iast)
    kdb.close()
    print("generator slots for %s lemmas [%.0fs]"
          % (human(len(lemma_known)), time.time() - t0), file=sys.stderr)

    # ---- classify -------------------------------------------------------------------
    rows = []
    verdict_n = collections.Counter()
    for form, r in cands.items():
        t = tags.get(form, collections.Counter())
        real = collections.Counter()
        cpd = 0
        for (fcase, fnum, fgen), n in t.items():
            if fcase == "Cpd":
                cpd += n
            elif fcase in CASE_MAP:
                real[(fcase, fnum, fgen)] += n
        nc = caseless[form]
        lemma = r["dcs_lemma"]
        cell = conflict_with = ""
        alt = anusvara_variants(form) - {form}
        if alt & lemma_forms.get(lemma, set()):
            # Sanskrit writes word-final -m as anusvāra before a consonant. form_key()
            # maps the anusvāra to `n` but leaves a real final `m` as `m`, so the two
            # standard spellings of one word never collide and every anusvāra-final
            # attestation reads as un-generated. This is orthography, not a gap.
            verdict = "orthographic-variant"
            conflict_with = " ".join(sorted(alt & lemma_forms[lemma])[:2])
            cell_occ = sum(real.values()) or cpd or nc
        elif cpd > sum(real.values()):
            # A form attested overwhelmingly as a compound member is a bound stem even if
            # a handful of tokens carry a real case: `ātma` is Cpd 2,544 vs real-case 10.
            # Taking real.most_common(1) there would promote 8 nominatives over 2,544
            # compound uses and call a stem a missing paradigm cell.
            verdict, cell_occ = "compound-member", cpd
        elif real:
            (fcase, fnum, fgen), n = real.most_common(1)[0]
            gc, nu, ge = CASE_MAP[fcase], NUM_MAP.get(fnum, ""), GEN_MAP.get(fgen, "")
            cell = "%s.%s.%s" % (ge or "?", gc, nu or "?")
            gen_forms = slots.get((lemma, ge, gc, nu), set())
            if lemma not in lemma_known:
                verdict = "lexicon-gap"          # generator has no nominal paradigm at all
            elif gen_forms:
                verdict = "slot-conflict"
                conflict_with = " ".join(sorted(gen_forms)[:3])
            else:
                verdict = "coverage-hole"
            cell_occ = n
        elif cpd:
            verdict, cell_occ = "compound-member", cpd
        elif nc and r["dcs_upos"] in INDECLINABLE_UPOS:
            verdict, cell_occ = "indeclinable", nc
        elif nc:
            verdict, cell_occ = "untagged", nc
        else:
            verdict, cell_occ = "no-dcs-token", 0
        verdict_n[verdict] += 1
        rows.append({
            "attested_form": form, "dcs_lemma": lemma, "dcs_upos": r["dcs_upos"],
            "verdict": verdict, "cell": cell, "cell_occ": str(cell_occ),
            "generator_has": conflict_with, "evidence_count": r["evidence_count"],
            "target_locus": r["target_locus"],
        })

    rows.sort(key=lambda x: (-int(x["evidence_count"]), x["attested_form"]))
    hdr = ["attested_form", "dcs_lemma", "dcs_upos", "verdict", "cell", "cell_occ",
           "generator_has", "evidence_count", "target_locus"]
    with OUT_TSV.open("w", encoding="utf-8", newline="") as f:
        f.write("\t".join(hdr) + "\n")
        for r in rows:
            f.write("\t".join(r[k] for k in hdr) + "\n")

    owed = [r for r in rows if r["verdict"] in ("slot-conflict", "coverage-hole")]
    # `lexicon-gap` is decided, not undecided: the generator carries no nominal paradigm for
    # the lemma at all, which is a dictionary-coverage question rather than an inflection
    # bug. It belongs with the other not-owed classes; only genuinely unresolved rows are
    # residue.
    not_owed = [r for r in rows if r["verdict"] in ("compound-member", "indeclinable",
                                                    "orthographic-variant", "lexicon-gap")]
    residue = [r for r in rows if r["verdict"] in ("untagged", "no-dcs-token")]

    today = time.strftime("%d-%m-%Y")
    L = []
    w = L.append
    w("# csl-inflect give-back — cell-resolved triage (A3 residual)")
    w("")
    w("_Auto-generated by [`scripts/triage_morph_giveback_candidates.py`](https://github.com/"
      "gasyoun/kosha/blob/main/scripts/triage_morph_giveback_candidates.py) (Opus 5 "
      "`claude-opus-5`) over [`morph_giveback_candidates.tsv`](https://github.com/gasyoun/"
      "kosha/blob/main/data/concordance/morph_giveback_candidates.tsv), DCS token features "
      "and `kosha.db` `inflections`._")
    w("")
    w("_Created: %s · Last updated: %s_" % (today, today))
    w("")
    w("## The candidate set did not need a human")
    w("")
    w("[`MORPHOLOGY_GIVEBACK_CANDIDATES_REPORT.md`](https://github.com/gasyoun/kosha/blob/"
      "main/data/concordance/MORPHOLOGY_GIVEBACK_CANDIDATES_REPORT.md) closed by calling its "
      "%s rows \"a candidate set needing human triage, not a defect list\", because bound "
      "stems still passed an exact-match filter. **DCS's own `feat_case` decides it "
      "mechanically**, so this was applied and reported rather than voted."
      % human(len(cands)))
    w("")
    w("| Verdict | Rows | Share | Owed to csl-inflect? |")
    w("|---|---:|---:|---|")
    meaning = [
        ("slot-conflict", "the generator HAS this `(lemma, gender, case, number)` slot and "
                          "emits a **different** form — a real disagreement with the corpus",
         "**yes** — and a human ruling is two concrete forms wide"),
        ("coverage-hole", "the slot is absent from `inflections` entirely — a missing "
                          "paradigm cell", "**yes** — no adjudication needed"),
        ("orthographic-variant", "differs from a form the generator already emits for this "
                                 "lemma **only** in how a word-final nasal is written "
                                 "(`iyaṃ` = `iyam`) — the same word, not a missing cell",
         "no — an artefact of the join key, see below"),
        ("compound-member", "DCS tags it `feat_case='Cpd'` more often than any real case: a "
                            "bound stem inside a compound, not a free inflected word",
         "no — out of scope"),
        ("indeclinable", "caseless, `upos` in ADV/SCONJ/PART/ADP/CCONJ/INTJ", "no — a nominal "
                         "generator does not inflect these"),
        ("lexicon-gap", "the generator carries no nominal paradigm for this lemma at all",
         "no — a dictionary-coverage question, not an inflection bug"),
        ("untagged", "attested only caseless, and `upos` is not an indeclinable class",
         "**judgment** — the only undecided class"),
        ("no-dcs-token", "no DCS token matched on either key — should be empty; a non-zero "
                         "count means the candidate set and the corpus have drifted",
         "**judgment**"),
    ]
    for k, why, verdict in meaning:
        if verdict_n[k]:
            w("| `%s` | %s | %s | %s |" % (k, human(verdict_n[k]),
                                           pct(verdict_n[k], len(cands)), verdict))
    w("")
    w("**Owed to the give-back: %s rows** (%s of the candidate set) — %s slot-conflicts and "
      "%s coverage-holes. **Not owed: %s** (%s). **Residue needing judgment: %s** (%s)."
      % (human(len(owed)), pct(len(owed), len(cands)),
         human(verdict_n["slot-conflict"]), human(verdict_n["coverage-hole"]),
         human(len(not_owed)), pct(len(not_owed), len(cands)),
         human(len(residue)), pct(len(residue), len(cands))))
    w("")
    w("## A defect in the join key, found by this triage — and since fixed")
    w("")
    w("**`form_key()` could not collide the two standard spellings of a word-final nasal.** "
      "Sanskrit writes final `-m` as anusvāra before a consonant; it is an editorial "
      "convention, not a different word. `form_key` mapped the anusvāra to `n` "
      "(`rasaṃ` → `rasan`) but left a real final `m` alone (`rasam` → `rasam`), so the two "
      "never matched and **every anusvāra-final attestation read as un-generated**. The "
      "first run of this triage caught 146 candidate rows of exactly that shape — `iyaṃ` = "
      "`iyam`, `rasaṃ` = `rasam`, `caraṃ` = `caram` — and parked them as "
      "`orthographic-variant`.")
    w("")
    w("That is a property of the shared `form_key()` in `sanskrit-util`, so it inflated the "
      "**whole** A3 A¬G figure, not just this candidate set. It was fixed upstream in "
      "[sanskrit-util 0.11.0](https://github.com/sanskrit-lexicon/sanskrit-util/pull/72) "
      "(word-final anusvāra folds to `m`; the medial fold is unchanged, so "
      "`saṃskṛta == sanskṛta`; final `-n` stays distinct from final `-m`) and the whole A3 "
      "chain was rebuilt against it: A¬G fell from 196,378 to 164,236 keys (−16.4%%). "
      "**This run classifies `%s` rows as `orthographic-variant`** — the class is the "
      "regression test, and an empty one means the twins now join instead of reaching A¬G."
      % human(verdict_n["orthographic-variant"]))
    w("")
    w("**Residual, one position inward — and it is not small.** Medial anusvāra before a "
      "labial is phonetically /m/, but it still folds to `n`, so `vaiśaṃpāyana` keys as "
      "`vaiśanpāyana` and never meets the `vaiśampāyanaḥ` the generator already emits. "
      "**278 of the %s `slot-conflict` rows (11.03%%; 11.58%% by corpus weight) are this** "
      "— `saṃbhavaḥ` vs `sambhavaḥ`, `saṃbandhaḥ` vs `sambandhaḥ`, `samyaksaṃbuddhaḥ` vs "
      "`samyaksambuddhaḥ`: one word spelled two ways, with no disagreement to adjudicate. "
      "They are screened off the human validation sheet by an explicit named rule rather "
      "than left for a reviewer to reject one at a time, and 90 candidates collapse into "
      "their own lemma once refolded, so they would leave A¬G entirely under a corrected "
      "key. Measured by `scripts/measure_medial_anusvara_residual.py`, not assumed. "
      "Narrowing the medial fold is a second change to a library ~85 repos consume — it is "
      "filed as owed work, not made here." % human(verdict_n["slot-conflict"]))
    w("")
    w("## Correction to the H3782 record")
    w("")
    w("That report, its PR and the roadmap all cite **`rājñ` (< `rājan`)** as an allomorphic "
      "bound stem that leaked past the exact-match filter, and used it to argue the set "
      "needed human triage. **DCS tags `rājñ` as `Voc Sing Masc` 880 times** — by the "
      "corpus's own annotation it is an inflected cell, not a stem. The caution was right in "
      "kind and wrong on that example. `ātma` (< `ātman`) *was* correctly suspected: "
      "`feat_case='Cpd'` on 2,544 tokens against 10 with a real case, so it is classified "
      "`compound-member`. Reaching that verdict needed a **dominance** rule, not mere "
      "presence: an earlier pass took the most frequent real case and promoted `ātma`'s 8 "
      "nominatives over its 2,544 compound uses, calling a bound stem a missing paradigm "
      "cell. 21 rows sat on the wrong side of that line.")
    w("")
    w("## The slot-conflicts — where a human ruling is cheapest and worth most")
    w("")
    w("Each row names a corpus-attested form, the exact cell DCS assigns it, and the form "
      "`inflections` emits for that same cell. A ruling is a comparison of two forms.")
    w("")
    w("| # | attested | cell | generator emits | lemma | occ |")
    w("|---:|---|---|---|---|---:|")
    sc = [r for r in rows if r["verdict"] == "slot-conflict"][:args.sample]
    for i, r in enumerate(sc, 1):
        w("| %d | `%s` | %s | `%s` | `%s` | %s |"
          % (i, r["attested_form"], r["cell"], r["generator_has"], r["dcs_lemma"],
             human(int(r["evidence_count"]))))
    w("")
    w("## The coverage-holes — highest-frequency first")
    w("")
    w("| # | attested | cell | lemma | occ |")
    w("|---:|---|---|---|---:|")
    ch = [r for r in rows if r["verdict"] == "coverage-hole"][:args.sample]
    for i, r in enumerate(ch, 1):
        w("| %d | `%s` | %s | `%s` | %s |"
          % (i, r["attested_form"], r["cell"], r["dcs_lemma"],
             human(int(r["evidence_count"]))))
    w("")
    w("## Not owed — a sample of each excluded class")
    w("")
    for k in ("orthographic-variant", "compound-member", "indeclinable"):
        ex = [r for r in rows if r["verdict"] == k][:8]
        if ex:
            w("**`%s`** — %s" % (k, " · ".join(
                "`%s`(<`%s`, %s×)" % (r["attested_form"], r["dcs_lemma"],
                                      human(int(r["evidence_count"]))) for r in ex)))
            w("")
    w("## Output")
    w("")
    w("[`data/concordance/morph_giveback_triaged.tsv`](https://github.com/gasyoun/kosha/blob/"
      "main/data/concordance/morph_giveback_triaged.tsv) — %s rows, %s bytes, every candidate "
      "with its verdict, resolved cell and the generator's competing form where one exists. "
      "Runtime %.0f s." % (human(len(rows)), human(os.path.getsize(OUT_TSV)),
                           time.time() - t0))
    w("")
    w("**Routing (hard stop).** The %s owed rows go to the csl-inflect dual-engine give-back "
      "(H185) as a **queued port** — a GTD row and a pointer, never an in-pass edit to "
      "csl-inflect." % human(len(owed)))
    w("")
    w("_Dr. Mārcis Gasūns_")
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")

    # machine-readable summary for the review sheet builder
    (CONC / "morph_giveback_triage_summary.json").write_text(
        json.dumps({"total": len(cands), "verdicts": dict(verdict_n),
                    "owed": len(owed), "not_owed": len(not_owed),
                    "residue": len(residue), "built": today},
                   ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8")

    print("owed %s (conflict %s / hole %s) · not owed %s · residue %s · %.0fs"
          % (human(len(owed)), human(verdict_n["slot-conflict"]),
             human(verdict_n["coverage-hole"]), human(len(not_owed)),
             human(len(residue)), time.time() - t0))


if __name__ == "__main__":
    main()
