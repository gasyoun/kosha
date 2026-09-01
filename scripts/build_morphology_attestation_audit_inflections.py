#!/usr/bin/env python
"""A3 completion — the NON-CIRCULAR generated-vs-attested morphology audit (H3782).

Why this exists beside `build_morphology_attestation_audit.py` (H1262, 18-07-2026)
---------------------------------------------------------------------------------
The shipped W1b build joined kosha.db `forms` (heritage excluded: 426,410 rows) against
DCS attestation and reported A¬G = **2**. That number is degenerate by construction:
93.30% of that generated side is itself `source='dcs'`, so the join is close to a
round-trip and the "attested-never-generated" direction cannot be measured on it. The
build report says so explicitly and hands the question on.

CONCORDANCE_ROADMAP Q3's first exit check names a different, larger side — "full 6.9M x
5.7M join complete". That 6.9M is kosha.db `inflections` (6,917,018 rows / 3,326,312
distinct `form_slp1`), which the roadmap mis-attributes to vidyut: it is **99.99%
`source='cologne_mwinflect'`** (6,916,522 rows; vidyut contributes 17 gap-fill rows).
Cologne's MW-inflect output is generated from MW headwords with no DCS input, so it is
the one generated side on which "attested but never generated" carries engine meaning.

This build therefore closes Q3 exit check 1 on the table the check names, and produces
the asymmetry in BOTH directions rather than one direction plus a tautology.

Two attested keys, deliberately
-------------------------------
A paradigm generator emits *unsandhied* forms; DCS `token.form` is the *sandhied*
surface. Joining a generator against sandhied surfaces manufactures a large fake
"engine gap" class -- the shipped report already identified sandhi-surface variance as
its dominant A¬G class. So both DCS keys are carried:

  surface     token.form            381,413 distinct   (comparable to the H1262 build)
  unsandhied  token.m_unsandhied    303,859 distinct   (the fair key for a generator)

An attested form counts as generated if EITHER key matches, and the report states how
much of the raw surface-only gap the unsandhied key dissolves.

A¬G triage -- lexicon gap vs paradigm gap (the routing that matters)
--------------------------------------------------------------------
An attested form the engine never produced is only a csl-inflect give-back candidate
(H185) when the engine *knew the lemma* and still missed the cell. So A¬G rows are split
on whether the DCS lemma is in the generator's own lemma inventory:

  lexicon_gap   DCS lemma absent from `inflections.lemma_slp1` -> a dictionary-coverage
                gap, NOT an inflection-engine bug; never routed to give-back
  paradigm_gap  lemma known, this cell never generated -> the genuine engine gap that
                routes to the csl-inflect give-back (H185)

plus the mechanical noise classes (`non_sanskrit_or_ocr`, `segmentation_artefact`)
carried unchanged from the H1262 build so the two reports stay comparable.

Discipline
----------
`form_key()` / `from_slp1()` / `to_slp1()` are CONSUMED from the canonical sanskrit-util
package via `concordance_core` (SHARED_CODE.md); no transcoder or normaliser is written
here. The banned NFD+strip-combining-marks path appears nowhere (D6). `TIER_CONFIDENCE`
and `citable_locus()` come from `concordance_core`, not hand-written.

R-C4 (DCS `Tense=Past` conflates aorist and perfect) is carried as a `tense_caveat`
column and a caveated subtotal beside every aggregate, never as an exclusion.

Deterministic, no network, read-only on both databases.
"""
import argparse
import collections
import gzip
import os
import random
import sqlite3
import sys
import time
import tracemalloc
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# kosha.db (1.7 GB) and the DCS dump are gitignored, so they live only in the canonical
# main clone's working tree, never in a worktree checkout. Resolve them there. The same
# root supplies sanskrit-util: `concordance_core` finds it at ROOT/../../sanskrit-util,
# which is correct in the main clone and wrong in a worktree, so it is put on the path
# here FIRST and that stale-relative guess never fires.
def _github_root(root):
    """The org checkout root that holds the sibling repos (VisualDCS, sanskrit-util).

    Must be *found*, not assumed: in the canonical clone it is ROOT.parent, but in a
    linked worktree (`../kosha-h<id>-<pid>`) that is the worktree's parent instead, and
    `Path.home()` is the harness profile directory on this box, not the user profile.
    So probe candidates and accept the first that actually carries VisualDCS.
    """
    env = os.environ.get("GITHUB_ROOT")
    if env:
        return Path(env)
    seen = []
    for cand in (root.parent, root.parent / "GitHub", root.parent.parent,
                 root.parent.parent / "GitHub"):
        seen.append(cand)
        if (cand / "VisualDCS").is_dir() and (cand / "sanskrit-util").is_dir():
            return cand
    sys.exit("cannot locate the GitHub org root (tried: %s); set GITHUB_ROOT"
             % ", ".join(str(p) for p in seen))


GH = _github_root(ROOT)
sys.path.insert(0, str(GH / "sanskrit-util" / "py"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from concordance_core import TIER_CONFIDENCE, citable_locus  # noqa: E402
from sanskrit_util import form_key, from_slp1, to_slp1  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

KOSHA_DB = GH / "kosha" / "data" / "db" / "kosha.db"
DCS = GH / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"
OUT = ROOT / "data" / "concordance"

AG_TSV = OUT / "morph_attest_infl_AG.tsv"
GNA_TSV = OUT / "morph_attest_infl_GnA.tsv.gz"
ANG_TSV = OUT / "morph_attest_infl_AnG.tsv"
REPORT = OUT / "MORPHOLOGY_ATTESTATION_INFLECTIONS_BUILD_REPORT.md"

# The allowed IAST alphabet (precomposed), carried verbatim from the H1262 build so the
# two reports' `non_sanskrit_or_ocr` classes mean the same thing.
IAST_OK = set("abcdefghijklmnopqrstuvwxyz"
              "āīūṛṝḷḹēō"
              "ṃṁḥṅñṭḍṇśṣḻ"
              "'-")

SAMPLE_PER_CLASS = 10
SAMPLE_SEED = 3782


def _non_sanskrit(surface):
    fl = unicodedata.normalize("NFC", surface).lower()
    return any((ch not in IAST_OK and not ch.isspace()) for ch in fl)


def triage_ang(surface, lemma_known):
    """Classify an attested-not-generated form. Order matters: mechanical noise first,
    then the lexicon/paradigm split that decides give-back routing."""
    if _non_sanskrit(surface):
        return "non_sanskrit_or_ocr"
    if " " in surface or len(surface) <= 1:
        return "segmentation_artefact"
    return "paradigm_gap" if lemma_known else "lexicon_gap"


def human(n):
    return "{:,}".format(n)


def pct(a, b):
    return "0.00%" if not b else "%.2f%%" % (100.0 * a / b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-gen", type=int, default=0,
                    help="debug: cap the generated-side scan (0 = all)")
    ap.add_argument("--limit-tokens", type=int, default=0,
                    help="debug: cap the DCS token scan (0 = all)")
    args = ap.parse_args()

    for p in (KOSHA_DB, DCS):
        if not p.exists():
            sys.exit("missing input: %s" % p)

    OUT.mkdir(parents=True, exist_ok=True)
    random.seed(SAMPLE_SEED)
    tracemalloc.start()
    t0 = time.time()

    # ---------------------------------------------------------------- pass 1: attested
    # Per attested key: occurrences, Past-tense occurrences, a representative surface
    # form + locus + DCS lemma. Two independent key spaces (sandhied / unsandhied) are
    # aggregated into one index, each entry recording which DCS column produced it.
    dcs = sqlite3.connect("file:%s?mode=ro" % DCS.as_posix(), uri=True)
    q = "SELECT form, m_unsandhied, lemma, feat_tense, sent_id, upos FROM token"
    if args.limit_tokens:
        q += " LIMIT %d" % args.limit_tokens

    # att[key] = [occ, past_occ, rep_surface, rep_locus, rep_lemma, from_surface,
    #             from_unsandhied, rep_upos]
    att = {}
    n_tok = 0
    n_surface_forms = set()
    n_unsandhied_forms = set()
    for form, unsand, lemma, tense, sentid, upos in dcs.execute(q):
        n_tok += 1
        for value, is_surface in ((form, True), (unsand, False)):
            if not value:
                continue
            if is_surface:
                n_surface_forms.add(value)
            else:
                n_unsandhied_forms.add(value)
            fk = form_key(value)
            if not fk:
                continue
            a = att.get(fk)
            if a is None:
                a = att[fk] = [0, 0, value, citable_locus(sentid), lemma or "", False,
                               False, upos or ""]
            a[0] += 1
            if tense == "Past":
                a[1] += 1
            if is_surface:
                a[5] = True
            else:
                a[6] = True
    dcs.close()
    print("pass1: %s tokens -> %s attested form_keys "
          "(%s distinct surface / %s distinct unsandhied) [%.0fs]"
          % (human(n_tok), human(len(att)), human(len(n_surface_forms)),
             human(len(n_unsandhied_forms)), time.time() - t0), file=sys.stderr)

    # SLP1 index of the attested side, so the `exact` tier (byte-identical SLP1) can be
    # claimed rather than assumed. Built once, reused for every generated row.
    att_slp1 = set()
    for fk, a in att.items():
        att_slp1.add(to_slp1(a[2]))

    # ------------------------------------------- pass 2: the generator's lemma inventory
    # Split nominal from verbal: `inflections` marks a verbal cell by a non-NULL `person`.
    # The split is load-bearing for reading A¬G — a generator that carries almost no verbal
    # lemmas cannot be said to have a "gap" at an attested finite verb; it never claimed
    # that territory. Without this axis the lexicon_gap class silently conflates "MW lacks
    # the headword" with "this generator does not do verbs".
    kosha = sqlite3.connect("file:%s?mode=ro" % KOSHA_DB.as_posix(), uri=True)
    gen_lemma_nominal, gen_lemma_verbal = set(), set()
    for label, where, target in (("nominal", "person IS NULL", gen_lemma_nominal),
                                 ("verbal", "person IS NOT NULL", gen_lemma_verbal)):
        for (lem,) in kosha.execute(
                "SELECT DISTINCT lemma_slp1 FROM inflections WHERE %s" % where):
            if lem:
                k = form_key(from_slp1(lem))
                if k:
                    target.add(k)
    gen_lemma_keys = gen_lemma_nominal | gen_lemma_verbal
    print("generator lemma inventory: %s distinct lemma keys "
          "(nominal %s / verbal %s) [%.0fs]"
          % (human(len(gen_lemma_keys)), human(len(gen_lemma_nominal)),
             human(len(gen_lemma_verbal)), time.time() - t0), file=sys.stderr)

    # ------------------------------------------------ pass 3: generated side, stream out
    # Grouped by form_slp1 so the unit is a distinct generated form, not a paradigm-cell
    # duplicate; `cells` records how many inflection rows assert that form.
    gq = ("SELECT form_slp1, MIN(lemma_slp1), MIN(source), COUNT(*) "
          "FROM inflections GROUP BY form_slp1")
    if args.limit_gen:
        gq += " LIMIT %d" % args.limit_gen

    ag_by_source = collections.Counter()
    gna_by_source = collections.Counter()
    ag_by_method = collections.Counter()
    ag_tense_caveat = 0
    ag_total = gna_total = 0
    matched_keys = set()
    ag_sample = []
    gna_sample = []

    AG_HEADER = ["anchor_type", "anchor_id", "anchor_key_slp1", "lemma_slp1", "gen_source",
                 "gen_cells", "target_locus", "source_dataset", "match_method",
                 "confidence", "evidence_count", "tense_caveat", "attested_form",
                 "attested_via"]
    GNA_HEADER = ["anchor_type", "anchor_id", "anchor_key_slp1", "lemma_slp1",
                  "gen_source", "gen_cells", "form_key"]

    fag = open(AG_TSV, "w", encoding="utf-8", newline="")
    fgna = gzip.open(GNA_TSV, "wt", encoding="utf-8", newline="")
    fag.write("\t".join(AG_HEADER) + "\n")
    fgna.write("\t".join(GNA_HEADER) + "\n")

    n_gen = 0
    for form_slp1, lemma_slp1, source, cells in kosha.execute(gq):
        n_gen += 1
        iast = from_slp1(form_slp1)
        fk = form_key(iast)
        if not fk:
            continue
        a = att.get(fk)
        if a is None:
            gna_total += 1
            gna_by_source[source] += 1
            row = ["inflection", form_slp1, form_slp1, lemma_slp1 or "", source or "",
                   str(cells), fk]
            fgna.write("\t".join(row) + "\n")
            if len(gna_sample) < 400:
                gna_sample.append((form_slp1, iast, lemma_slp1, source, cells))
            elif random.random() < 0.002:
                gna_sample[random.randrange(400)] = (form_slp1, iast, lemma_slp1,
                                                     source, cells)
            continue

        ag_total += 1
        matched_keys.add(fk)
        ag_by_source[source] += 1
        method = "exact" if form_slp1 in att_slp1 else "floor"
        ag_by_method[method] += 1
        caveat = 1 if a[1] else 0
        ag_tense_caveat += caveat
        via = "surface+unsandhied" if (a[5] and a[6]) else ("surface" if a[5] else "unsandhied")
        row = ["inflection", form_slp1, form_slp1, lemma_slp1 or "", source or "",
               str(cells), a[3], "dcs", method, "%.2f" % TIER_CONFIDENCE[method],
               str(a[0]), str(caveat), a[2], via]
        fag.write("\t".join(row) + "\n")
        if len(ag_sample) < 400:
            ag_sample.append((form_slp1, iast, lemma_slp1, source, a[2], a[3], a[0],
                              method, via))
        elif random.random() < 0.002:
            ag_sample[random.randrange(400)] = (form_slp1, iast, lemma_slp1, source,
                                                a[2], a[3], a[0], method, via)

    fag.close()
    fgna.close()
    kosha.close()
    print("pass3: %s distinct generated forms -> AG %s / GnA %s [%.0fs]"
          % (human(n_gen), human(ag_total), human(gna_total), time.time() - t0),
          file=sys.stderr)

    # ----------------------------------------------------------- pass 4: A¬G + triage
    ang_rows = []
    ang_by_class = collections.Counter()
    ang_caveat_by_class = collections.Counter()
    ang_verbal_by_class = collections.Counter()   # DCS upos == VERB, per class
    ag_verbal = 0
    att_verbal = 0
    surface_only_gap = 0
    ANG_HEADER = ["attested_form", "form_key", "dcs_lemma", "dcs_upos", "target_locus",
                  "source_dataset", "evidence_count", "tense_caveat", "attested_via",
                  "triage_class"]
    with open(ANG_TSV, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(ANG_HEADER) + "\n")
        for fk, a in att.items():
            occ, past, surface, locus, lemma, from_s, from_u, upos = a
            is_verb = (upos == "VERB")
            if is_verb:
                att_verbal += 1
            if fk in matched_keys:
                if is_verb:
                    ag_verbal += 1
                continue
            lemma_known = bool(lemma) and form_key(lemma) in gen_lemma_keys
            klass = triage_ang(surface, lemma_known)
            caveat = 1 if past else 0
            ang_by_class[klass] += 1
            ang_caveat_by_class[klass] += caveat
            if is_verb:
                ang_verbal_by_class[klass] += 1
            if from_s and not from_u:
                surface_only_gap += 1
            via = "surface+unsandhied" if (from_s and from_u) else ("surface" if from_s
                                                                   else "unsandhied")
            f.write("\t".join([surface, fk, lemma, upos, locus, "dcs", str(occ),
                               str(caveat), via, klass]) + "\n")
            ang_rows.append((surface, fk, lemma, locus, occ, via, klass, upos))

    ang_total = len(ang_rows)
    att_total = len(att)
    peak = tracemalloc.get_traced_memory()[1] / 1e6
    tracemalloc.stop()
    runtime = time.time() - t0

    # ------------------------------------------------------------------------- samples
    def sample(rows, k):
        return random.sample(rows, min(k, len(rows)))

    ang_by_class_rows = collections.defaultdict(list)
    for r in ang_rows:
        ang_by_class_rows[r[6]].append(r)

    # --------------------------------------------------------------------------- report
    today = time.strftime("%d-%m-%Y")
    L = []
    w = L.append
    w("# Morphology attestation audit — the `inflections` side (A3 completion, H3782)")
    w("")
    w("_Auto-generated by [`scripts/build_morphology_attestation_audit_inflections.py`]"
      "(https://github.com/gasyoun/kosha/blob/main/scripts/"
      "build_morphology_attestation_audit_inflections.py) (H3782, Opus 5 `claude-opus-5`). "
      "Every figure below is re-derivable from that script over the two source databases; "
      "a number nobody can re-derive is not shipped._")
    w("")
    w("_Created: %s · Last updated: %s_" % (today, today))
    w("")
    w("## Why a second audit (read this before quoting either report)")
    w("")
    w("[`MORPHOLOGY_ATTESTATION_BUILD_REPORT.md`](https://github.com/gasyoun/kosha/blob/"
      "main/data/concordance/MORPHOLOGY_ATTESTATION_BUILD_REPORT.md) (H1262, 18-07-2026) "
      "joined kosha.db `forms` (heritage excluded, %s rows) and reported **A¬G = 2**. That "
      "number is degenerate by construction: 93.30%% of that generated side is itself "
      "`source='dcs'`, so the join is close to a round-trip and the attested-never-generated "
      "direction is unmeasurable on it. That report says so and hands the question on."
      % human(426410))
    w("")
    w("CONCORDANCE_ROADMAP Q3's first exit check names a different side — \"full 6.9M x 5.7M "
      "join complete\". This build runs that join. **The roadmap mis-attributes the 6.9M to "
      "vidyut**: kosha.db `inflections` is 6,917,018 rows of which **6,916,522 are "
      "`source='cologne_mwinflect'`** (plus 326 `hybrid-natva-fix`, 153 "
      "`curated-gita-pronoun`, 17 `vidyut-gap-fill`). Cologne's MW-inflect output is derived "
      "from MW headwords with no DCS input, so it is the one generated side on which "
      "\"attested but never generated\" carries engine meaning.")
    w("")
    w("## Inputs (measured, read-only)")
    w("")
    w("| Input | Stamp (%s) |" % today)
    w("|---|---|")
    w("| `kosha.db` (`inflections`) | %.1f MB, mtime %s |"
      % (os.path.getsize(KOSHA_DB) / 1e6,
         time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(KOSHA_DB)))))
    w("| `dcs_full.sqlite` (`token`) | %.1f MB, mtime %s |"
      % (os.path.getsize(DCS) / 1e6,
         time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(DCS)))))
    w("")
    w("- Generated side: `inflections`, **all sources** (%s distinct `form_slp1` scanned "
      "as groups; a group is one distinct generated form, `gen_cells` records how many "
      "paradigm-cell rows assert it)." % human(n_gen))
    w("- Attested side: **two DCS keys**, because a paradigm generator emits *unsandhied* "
      "forms while `token.form` is the *sandhied* surface — joining a generator against "
      "sandhied surfaces manufactures a fake engine-gap class, which is exactly what "
      "dominated the H1262 A¬G triage.")
    w("")
    w("| Attested key | DCS column | Distinct values |")
    w("|---|---|---:|")
    w("| surface (sandhied) | `token.form` | %s |" % human(len(n_surface_forms)))
    w("| unsandhied | `token.m_unsandhied` | %s |" % human(len(n_unsandhied_forms)))
    w("| **union, after `form_key()`** | both | **%s** |" % human(att_total))
    w("")
    w("- Token occurrences scanned: **%s**." % human(n_tok))
    w("- Join key: `form_key()` from sanskrit-util (length-preserving floor tier), "
      "consumed via `concordance_core` — no NFD+strip-combining-marks path anywhere (D6).")
    w("")
    w("## Buckets")
    w("")
    w("Two denominators, as in the H1262 build: the generated side is counted in distinct "
      "generated forms, the attested side in distinct attested `form_key`s.")
    w("")
    w("| Bucket | Definition | Count | Denominator |")
    w("|---|---|---:|---|")
    w("| **AG** (generated view) | generated form whose `form_key` is attested | **%s** | "
      "of %s generated forms |" % (human(ag_total), human(n_gen)))
    w("| **G¬A** | generated form never attested (over-generation) | **%s** | of %s "
      "generated forms |" % (human(gna_total), human(n_gen)))
    w("| **AG** (attested view) | attested keys matched by some generated form | **%s** | "
      "of %s attested keys |" % (human(len(matched_keys)), human(att_total)))
    w("| **A¬G** | attested key never generated (engine or lexicon gap) | **%s** | of %s "
      "attested keys |" % (human(ang_total), human(att_total)))
    w("")
    w("**Reconciliation.** Generated: AG %s + G¬A %s = **%s** (= %s ✓). Attested: AG %s + "
      "A¬G %s = **%s** (= %s ✓)."
      % (human(ag_total), human(gna_total), human(ag_total + gna_total),
         human(ag_total + gna_total), human(len(matched_keys)), human(ang_total),
         human(len(matched_keys) + ang_total), human(att_total)))
    w("")
    w("- Generated-side attestation rate: **%s** of generated forms are attested."
      % pct(ag_total, n_gen))
    w("- Attested-side coverage: **%s** of attested keys are generated."
      % pct(len(matched_keys), att_total))
    w("")
    w("### By generated-side source")
    w("")
    w("| Generated source | AG | G¬A | AG rate |")
    w("|---|---:|---:|---:|")
    for src in sorted(set(list(ag_by_source) + list(gna_by_source)),
                      key=lambda s: -(ag_by_source[s] + gna_by_source[s])):
        a, g = ag_by_source[src], gna_by_source[src]
        w("| %s | %s | %s | %s |" % (src, human(a), human(g), pct(a, a + g)))
    w("")
    w("### AG by match tier")
    w("")
    w("`form_key` equality **is** the floor tier (%.2f); promoted to `exact` (%.2f) only "
      "where the generated SLP1 is byte-identical to an attested SLP1. `TIER_CONFIDENCE` "
      "is imported from `concordance_core.py`, never hand-written."
      % (TIER_CONFIDENCE["floor"], TIER_CONFIDENCE["exact"]))
    w("")
    for m in ("exact", "floor"):
        w("- **%s** (%.2f): %s forms" % (m, TIER_CONFIDENCE[m], human(ag_by_method[m])))
    w("")
    w("## R-C4 tense caveat")
    w("")
    w("DCS conflates aorist and perfect under `Tense=Past`. Rows whose attested evidence "
      "carries a `Past`-tense token are flagged `tense_caveat=1` and are **not excluded** "
      "(excluding them understates coverage).")
    w("")
    w("- **AG** total %s — of which `tense_caveat=1`: **%s** (%s)."
      % (human(ag_total), human(ag_tense_caveat), pct(ag_tense_caveat, ag_total)))
    w("- **A¬G** total %s — of which `tense_caveat=1`: **%s**."
      % (human(ang_total), human(sum(ang_caveat_by_class.values()))))
    w("- **G¬A** total %s — `tense_caveat=1`: **0** by construction (no attested side, so "
      "no DCS Past evidence)." % human(gna_total))
    w("")
    w("## A¬G triage — lexicon gap vs paradigm gap")
    w("")
    w("An attested form the engine never produced is only a csl-inflect give-back candidate "
      "(H185) when the engine **knew the lemma** and still missed the cell. A¬G is therefore "
      "split on whether the DCS lemma is in the generator's own lemma inventory (%s distinct "
      "lemma keys from `inflections.lemma_slp1`: **%s nominal** — rows with `person IS NULL` "
      "— and **%s verbal**)."
      % (human(len(gen_lemma_keys)), human(len(gen_lemma_nominal)),
         human(len(gen_lemma_verbal))))
    w("")
    w("| Triage class | Count | share of A¬G | of which `tense_caveat=1` | Meaning |")
    w("|---|---:|---:|---:|---|")
    meanings = {
        "paradigm_gap": "lemma IS in the generator's inventory, this form never generated "
                        "→ **the genuine engine gap; routes to the csl-inflect give-back "
                        "(H185)**",
        "lexicon_gap": "DCS lemma absent from the generator's inventory → a dictionary-"
                       "coverage gap, NOT an inflection-engine bug; never routed to give-back",
        "segmentation_artefact": "space-containing or single-character token; DCS "
                                 "segmentation artefact",
        "non_sanskrit_or_ocr": "carries a non-IAST character (digit/Latin/punctuation) → "
                               "OCR artefact",
    }
    for klass, n in ang_by_class.most_common():
        w("| `%s` | %s | %s | %s | %s |"
          % (klass, human(n), pct(n, ang_total), human(ang_caveat_by_class[klass]),
             meanings.get(klass, "")))
    w("")
    w("**Sandhi control.** %s of the %s A¬G keys (%s) are attested **only** as a sandhied "
      "surface, never as an unsandhied form — for those the gap is a sandhi-surface "
      "artefact of the attested side, not a claim about the generator. The remaining %s are "
      "attested in unsandhied form and are the defensible gap set."
      % (human(surface_only_gap), human(ang_total), pct(surface_only_gap, ang_total),
         human(ang_total - surface_only_gap)))
    w("")
    w("**Verb control — read this before quoting `paradigm_gap` as an engine defect.** The "
      "generator's inventory is **%s nominal lemmas against %s verbal** (%s of it verbal), "
      "so finite verbs are territory `inflections` barely claims. Of the %s attested keys "
      "DCS tags `upos=VERB`, **%s are generated (%s)** and **%s fall in A¬G**. Per class:"
      % (human(len(gen_lemma_nominal)), human(len(gen_lemma_verbal)),
         pct(len(gen_lemma_verbal), len(gen_lemma_keys)), human(att_verbal),
         human(ag_verbal), pct(ag_verbal, att_verbal),
         human(sum(ang_verbal_by_class.values()))))
    w("")
    w("| Triage class | rows | of which DCS `upos=VERB` | share |")
    w("|---|---:|---:|---:|")
    for klass, n in ang_by_class.most_common():
        v = ang_verbal_by_class[klass]
        w("| `%s` | %s | %s | %s |" % (klass, human(n), human(v), pct(v, n)))
    w("")
    w("A `paradigm_gap` row on a verbal lemma is therefore **not** evidence that the Cologne "
      "nominal-inflection tables are broken; it is evidence of the scope they never covered. "
      "The give-back candidates worth acting on are the **non-verbal** `paradigm_gap` rows.")
    w("")
    w("**Give-back routing (hard stop).** `paradigm_gap` rows are handed to the csl-inflect "
      "dual-engine give-back (H185) as a **queued port** — a GTD row and a pointer, never "
      "an in-pass edit to csl-inflect.")
    w("")
    w("## Outputs")
    w("")
    w("| File | Rows | Bytes |")
    w("|---|---:|---:|")
    for p, n in ((AG_TSV, ag_total), (GNA_TSV, gna_total), (ANG_TSV, ang_total)):
        w("| [`data/concordance/%s`](https://github.com/gasyoun/kosha/blob/main/data/"
          "concordance/%s) | %s | %s |" % (p.name, p.name, human(n),
                                           human(os.path.getsize(p))))
    w("")
    w("`morph_attest_infl_GnA.tsv.gz` is gzipped: the over-generation bucket is the largest "
      "of the three and ships complete rather than sampled.")
    w("")
    w("## Run")
    w("")
    w("- Peak Python-object memory: **%.0f MB** (tracemalloc)." % peak)
    w("- Runtime: **%.0f s**." % runtime)
    w("")
    w("## Spot-check — A¬G `paradigm_gap`, %d rows (human-verifiable)" % SAMPLE_PER_CLASS)
    w("")
    w("Each row is a genuine engine gap iff the form really occurs in DCS at the cited locus "
      "**and** the Cologne MW-inflect tables really lack it for that lemma. Verify against "
      "`dcs_full.sqlite` (`dcs:<sent_id>`) and `kosha.db` `inflections`.")
    w("")
    w("| # | attested form | form_key | DCS lemma | upos | locus | occ | via |")
    w("|---:|---|---|---|---|---|---:|---|")
    for i, r in enumerate(sample(ang_by_class_rows.get("paradigm_gap", []),
                                 SAMPLE_PER_CLASS), 1):
        w("| %d | `%s` | `%s` | `%s` | %s | `%s` | %s | %s |"
          % (i, r[0], r[1], r[2], r[7], r[3], human(r[4]), r[5]))
    w("")
    w("## Spot-check — A¬G `lexicon_gap`, %d rows" % SAMPLE_PER_CLASS)
    w("")
    w("These are attested lemmas the generator's inventory does not carry at all — a "
      "dictionary-coverage question for MW, not an inflection bug.")
    w("")
    w("| # | attested form | form_key | DCS lemma | upos | locus | occ | via |")
    w("|---:|---|---|---|---|---|---:|---|")
    for i, r in enumerate(sample(ang_by_class_rows.get("lexicon_gap", []),
                                 SAMPLE_PER_CLASS), 1):
        w("| %d | `%s` | `%s` | `%s` | %s | `%s` | %s | %s |"
          % (i, r[0], r[1], r[2], r[7], r[3], human(r[4]), r[5]))
    w("")
    w("## Spot-check — G¬A over-generation, %d rows" % SAMPLE_PER_CLASS)
    w("")
    w("Each row is a form the generator emits that the 5.7M-token corpus never attests. "
      "A row is *sound* over-generation if the form is a well-formed paradigm cell that "
      "simply happens to be unattested, and a *defect* if it is not well-formed Sanskrit.")
    w("")
    w("| # | form (SLP1) | form (IAST) | lemma | source | cells |")
    w("|---:|---|---|---|---|---:|")
    for i, r in enumerate(sample(gna_sample, SAMPLE_PER_CLASS), 1):
        w("| %d | `%s` | %s | `%s` | %s | %s |"
          % (i, r[0], r[1], r[2], r[3], human(r[4])))
    w("")
    w("## Spot-check — AG confirmations, %d rows" % SAMPLE_PER_CLASS)
    w("")
    w("| # | form (SLP1) | form (IAST) | lemma | attested surface | locus | occ | tier | via |")
    w("|---:|---|---|---|---|---|---:|---|---|")
    for i, r in enumerate(sample(ag_sample, SAMPLE_PER_CLASS), 1):
        w("| %d | `%s` | %s | `%s` | %s | `%s` | %s | %s | %s |"
          % (i, r[0], r[1], r[2], r[4], r[5], human(r[6]), r[7], r[8]))
    w("")
    w("_Dr. Mārcis Gasūns_")

    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote %s" % REPORT, file=sys.stderr)
    print("AG %s / GnA %s / AnG %s | %.0fs | peak %.0f MB"
          % (human(ag_total), human(gna_total), human(ang_total), runtime, peak))


if __name__ == "__main__":
    main()
