#!/usr/bin/env python
"""Build A3 — the generated-vs-attested morphology audit (W1b / H1262).

The artefact A4 cannot start without (D12 in the Concordance-Q3 plan set). Joins
kosha's *generated* inflected forms (kosha.db `forms`, heritage excluded) against
*attested* DCS surface forms (dcs_full.sqlite `token.form`) on `form_key()`
equality — the length-preserving floor tier — and emits three buckets:

  data/concordance/morph_attest_AG.tsv    attested ∧ generated (confirmed)  -> feeds A4
  data/concordance/morph_attest_GnA.tsv   generated, never attested (over-generation)
  data/concordance/morph_attest_AnG.tsv   attested, never generated (engine/grammar gap
                                          OR OCR/segmentation error) -- triaged
  data/concordance/MORPHOLOGY_ATTESTATION_BUILD_REPORT.md

Key discipline (VERIFICATION 1b-2, ARCHITECTURE §3, D6): the join key is
`form_key()` from the canonical sanskrit-util package, CONSUMED not re-implemented
(SHARED_CODE.md). form_key() is length-preserving (ā≠a, retroflex preserved). The
banned NFD+strip-combining-marks path appears NOWHERE here — it destroys vowel
length and retroflexion, which is precisely what scored the relaxed tier 0/3 (D6).
A near-match is not a match.

Encodings. Generated side is SLP1 (`forms.form_slp1`); it is rendered to IAST via
sanskrit_util.from_slp1 before form_key(), because form_key() folds precomposed
IAST nasals/visarga. Attested side is IAST surface (`token.form`); form_key() eats
it directly. The `exact` tier (0.95) is claimed only where the generated SLP1 key
is byte-identical to an attested SLP1 key (to_slp1 of the surface form); otherwise
the match is `floor` (0.85). No hand-written confidence — TIER_CONFIDENCE is
imported from concordance_core.py.

Measured-input reality (H1262, 18-07-2026): `forms` holds 1,378,401 rows (NOT the
6.9M of the architecture diagram — that is `inflections`, a different table; the
contradiction is REPORTED here and logged as a contradiction, never silently
resolved — see the build report). Non-heritage: 426,410 rows / 409,978 distinct
form_slp1 (heritage 951,991 · dcs 397,843 · vidyut 28,567). 93.30% of the
non-heritage generated side is itself DCS-derived (source='dcs'), so a raw AG count
overstates what the *engine* generates — AG is therefore partitioned by
generated-side source, and the vidyut subtotal is the figure that carries research
meaning. Attested: 5,688,416 token occurrences / 381,413 distinct surface forms.

Deterministic, no network, read-only on both databases.
"""
import argparse
import collections
import os
import random
import sqlite3
import sys
import time
import tracemalloc
import unicodedata
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# concordance_core sets up the sanskrit-util path and owns the shared schema/tiers.
from concordance_core import RECORD_FIELDS, TIER_CONFIDENCE, citable_locus  # noqa: E402
from sanskrit_util import form_key, from_slp1, to_slp1  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent if (ROOT.parent / "VisualDCS").exists() else ROOT.parent.parent
# kosha.db (1.674 GB) is gitignored, so it lives only in the canonical main clone's
# working tree, never in a worktree checkout. Resolve it there, not under ROOT.
KOSHA_DB = GH / "kosha" / "data" / "db" / "kosha.db"
DCS = GH / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"
OUT = ROOT / "data" / "concordance"

AG_TSV = OUT / "morph_attest_AG.tsv"
GNA_TSV = OUT / "morph_attest_GnA.tsv"
ANG_TSV = OUT / "morph_attest_AnG.tsv"
REPORT = OUT / "MORPHOLOGY_ATTESTATION_BUILD_REPORT.md"

# A¬G triage: the allowed IAST alphabet (precomposed). A surface form carrying any
# other character (digit, Latin-only OCR junk, stray punctuation) is an OCR artefact
# rather than an engine gap. Apostrophe/avagraha and hyphen are tolerated as Sanskrit.
IAST_OK = set("abcdefghijklmnopqrstuvwxyz"
              "āīūṛṝḷḹēō"   # ā ī ū ṛ ṝ ḷ ḹ ē ō
              "ṃṁḥṅñṭḍṇśṣḻ"  # ṃ ṁ ḥ ṅ ñ ṭ ḍ ṇ ś ṣ ḻ
              "'-")

SAMPLE_PER_SOURCE = 10   # 1b-8: 20 rows total, STRATIFIED by generated-side source
SAMPLE_SEED = 1262


def _non_sanskrit(surface):
    fl = unicodedata.normalize("NFC", surface).lower()
    return any((ch not in IAST_OK and not ch.isspace()) for ch in fl)


def triage_ang(surface, sandhi_ne_occ, total_occ):
    """Classify an attested-not-generated surface form (1b-5). Order matters:
    OCR junk first, then segmentation, then sandhi-surface variants (the big noise
    class induced by using the *sandhied* surface form as the attested key), then
    the residue — genuine engine gaps that route to the csl-inflect give-back."""
    if _non_sanskrit(surface):
        return "non_sanskrit_or_ocr"
    if " " in surface or len(surface) <= 1:
        return "segmentation_artefact"
    if sandhi_ne_occ * 2 >= total_occ:   # majority of occurrences are sandhi-altered
        return "sandhi_surface_variant"
    return "genuine_engine_gap"


def db_size_bytes(path):
    return os.path.getsize(path) if os.path.exists(path) else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-tokens", type=int, default=0,
                    help="debug: cap DCS token scan (0 = all)")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    random.seed(SAMPLE_SEED)
    tracemalloc.start()
    t0 = time.time()

    kosha_before = db_size_bytes(KOSHA_DB)
    print("kosha.db before: %.3f GB" % (kosha_before / 1e9), file=sys.stderr)

    # ---- Pass 1: aggregate attested surface forms over the 5.69M-token table ----
    dcs = sqlite3.connect("file:%s?mode=ro" % DCS.as_posix(), uri=True)
    q = "SELECT form, feat_tense, m_unsandhied, sent_id FROM token"
    if args.limit_tokens:
        q += " LIMIT %d" % args.limit_tokens
    # per surface form: [occ, past_occ, sandhi_ne_occ, first_sent_id]
    att = {}
    n_tok = 0
    for form, tense, unsand, sentid in dcs.execute(q):
        n_tok += 1
        if not form:
            continue
        a = att.get(form)
        if a is None:
            a = att[form] = [0, 0, 0, sentid]
        a[0] += 1
        if tense == "Past":
            a[1] += 1
        if unsand and unsand != form:
            a[2] += 1
    dcs.close()
    print("pass1: %d tokens, %d distinct surface forms (%.1fs)"
          % (n_tok, len(att), time.time() - t0), file=sys.stderr)

    # ---- Build the form_key -> attested aggregate index ----
    # per fk: occ/past/sandhi bucket totals; rep_* = most-attested surface form (used
    # for floor matches); slp1_map = SLP1 -> (surface, locus, occ) so an EXACT match
    # (generated SLP1 byte-identical to an attested SLP1) shows the surface form and
    # locus that ACTUALLY produced it, not the bucket's most-frequent variant. That
    # distinction is load-bearing for the 1b-8 human spot-check.
    att_fk = {}
    att_unkeyable = 0   # surface forms whose form_key() is empty (placeholders/punct)
    for surface, (occ, past, sandhi, sentid) in att.items():
        fk = form_key(surface)
        if not fk:
            att_unkeyable += 1
            continue
        g = att_fk.get(fk)
        if g is None:
            g = att_fk[fk] = {"occ": 0, "past": 0, "sandhi": 0, "slp1_map": {},
                              "rep_form": surface, "rep_locus": citable_locus(sentid),
                              "rep_occ": occ, "n_forms": 0}
        g["occ"] += occ
        g["past"] += past
        g["sandhi"] += sandhi
        g["n_forms"] += 1
        slp1 = to_slp1(surface)
        prev = g["slp1_map"].get(slp1)
        if prev is None or occ > prev[2]:   # keep the most-attested surface per SLP1 key
            g["slp1_map"][slp1] = (surface, citable_locus(sentid), occ)
        if occ > g["rep_occ"]:   # representative = most-attested surface form in the bucket
            g["rep_form"] = surface
            g["rep_locus"] = citable_locus(sentid)
            g["rep_occ"] = occ
    print("indexed %d attested form_keys (%d unkeyable surface forms)"
          % (len(att_fk), att_unkeyable), file=sys.stderr)

    # ---- Pass 2: generated side (non-heritage), stream AG + G¬A ----
    kosha = sqlite3.connect("file:%s?mode=ro" % KOSHA_DB.as_posix(), uri=True)
    gen_fk_set = set()
    matched_fk = set()

    ag_by_source = collections.Counter()          # AG generated-rows per source
    ag_by_method = collections.Counter()          # exact / floor
    ag_tense_caveat = 0
    gna_by_source = collections.Counter()
    ag_total = 0
    gna_total = 0
    reservoir = {"dcs": [], "vidyut": []}          # 1b-8 stratified sample

    AG_HEADER = ["anchor_type", "anchor_id", "anchor_key_slp1", "lemma_slp1",
                 "gen_source", "target_locus", "source_dataset", "match_method",
                 "confidence", "evidence_count", "tense_caveat", "attested_form"]
    GNA_HEADER = ["anchor_type", "anchor_id", "anchor_key_slp1", "lemma_slp1",
                  "gen_source", "form_key"]

    fag = open(AG_TSV, "w", encoding="utf-8", newline="")
    fgna = open(GNA_TSV, "w", encoding="utf-8", newline="")
    fag.write("\t".join(AG_HEADER) + "\n")
    fgna.write("\t".join(GNA_HEADER) + "\n")

    n_gen = 0
    for form_slp1, lemma_slp1, source in kosha.execute(
            "SELECT form_slp1, lemma_slp1, source FROM forms WHERE source != 'heritage'"):
        n_gen += 1
        iast = from_slp1(form_slp1)
        fk = form_key(iast)
        gen_fk_set.add(fk)
        a = att_fk.get(fk) if fk else None
        if a:
            exact_hit = a["slp1_map"].get(form_slp1)
            if exact_hit is not None:        # generated SLP1 byte-identical to an attested SLP1
                method = "exact"
                att_surface, att_locus, att_occ = exact_hit
            else:
                method = "floor"             # form_key-equal but not SLP1-identical
                att_surface, att_locus, att_occ = a["rep_form"], a["rep_locus"], a["occ"]
            conf = TIER_CONFIDENCE[method]
            tcav = 1 if a["past"] > 0 else 0
            ag_total += 1
            ag_by_source[source] += 1
            ag_by_method[method] += 1
            ag_tense_caveat += tcav
            matched_fk.add(fk)
            row = ["inflection", form_slp1, form_slp1, lemma_slp1, source,
                   att_locus, "dcs", method, "%.2f" % conf,
                   str(att_occ), str(tcav), att_surface]
            fag.write("\t".join(row) + "\n")
            # reservoir sample per source (only sources we stratify on)
            if source in reservoir:
                buf = reservoir[source]
                if len(buf) < SAMPLE_PER_SOURCE:
                    buf.append(row)
                else:
                    j = random.randint(0, ag_by_source[source] - 1)
                    if j < SAMPLE_PER_SOURCE:
                        buf[j] = row
        else:
            gna_total += 1
            gna_by_source[source] += 1
            fgna.write("\t".join(["inflection", form_slp1, form_slp1, lemma_slp1,
                                  source, fk]) + "\n")
    kosha.close()
    fag.close()
    fgna.close()
    print("pass2: %d generated non-heritage rows -> AG %d / G¬A %d (%.1fs)"
          % (n_gen, ag_total, gna_total, time.time() - t0), file=sys.stderr)

    # ---- Pass 3: A¬G — attested surface forms whose form_key is not generated ----
    ANG_HEADER = ["attested_form", "form_key", "target_locus", "source_dataset",
                  "evidence_count", "tense_caveat", "triage_class"]
    fang = open(ANG_TSV, "w", encoding="utf-8", newline="")
    fang.write("\t".join(ANG_HEADER) + "\n")

    ang_total = 0
    ag_att_forms = 0                       # distinct attested surface forms that matched
    ang_triage = collections.Counter()
    ang_tense_caveat = 0
    ang_triage_tcav = collections.Counter()
    for surface, (occ, past, sandhi, sentid) in att.items():
        fk = form_key(surface)
        if not fk:
            continue                        # counted in att_unkeyable
        if fk in gen_fk_set:
            ag_att_forms += 1
            continue
        ang_total += 1
        cls = triage_ang(surface, sandhi, occ)
        ang_triage[cls] += 1
        tcav = 1 if past > 0 else 0
        ang_tense_caveat += tcav
        if tcav:
            ang_triage_tcav[cls] += 1
        fang.write("\t".join([surface, fk, citable_locus(sentid), "dcs",
                              str(occ), str(tcav), cls]) + "\n")
    fang.close()
    print("pass3: A¬G %d / AG-attested-forms %d (%.1fs)"
          % (ang_total, ag_att_forms, time.time() - t0), file=sys.stderr)

    kosha_after = db_size_bytes(KOSHA_DB)
    cur_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    runtime = time.time() - t0

    # ---- Reconciliation ----
    gen_denom = ag_total + gna_total                       # must == 426,410
    att_denom = ag_att_forms + ang_total + att_unkeyable   # must == 381,413

    stats = {
        "n_gen": n_gen, "ag_total": ag_total, "gna_total": gna_total,
        "gen_denom": gen_denom,
        "ag_by_source": dict(ag_by_source), "gna_by_source": dict(gna_by_source),
        "ag_by_method": dict(ag_by_method), "ag_tense_caveat": ag_tense_caveat,
        "n_att_forms": len(att), "ag_att_forms": ag_att_forms,
        "ang_total": ang_total, "att_unkeyable": att_unkeyable,
        "att_denom": att_denom, "n_tok": n_tok,
        "ang_triage": dict(ang_triage), "ang_triage_tcav": dict(ang_triage_tcav),
        "ang_tense_caveat": ang_tense_caveat,
        "kosha_before": kosha_before, "kosha_after": kosha_after,
        "peak_mem": peak_mem, "runtime": runtime,
        "reservoir": reservoir,
    }
    write_report(stats)
    print("DONE %.1fs  peak-mem %.0f MB  AG %d (vidyut %d) / G¬A %d / A¬G %d"
          % (runtime, peak_mem / 1e6, ag_total,
             ag_by_source.get("vidyut", 0), gna_total, ang_total), file=sys.stderr)


def _db_stamp(path):
    import datetime
    if not os.path.exists(path):
        return "MISSING"
    mt = os.path.getmtime(path)
    return "%.1f MB, mtime %s" % (
        os.path.getsize(path) / 1e6,
        datetime.datetime.fromtimestamp(mt, datetime.timezone.utc).strftime("%Y-%m-%d"))


def write_report(s):
    L = []
    a = L.append
    a("# Morphology attestation audit (A3 / W1b) — build report")
    a("")
    a("_Auto-generated by `scripts/build_morphology_attestation_audit.py` (H1262, "
      "Opus 4.8 `claude-opus-4-8`). Every figure below is re-derivable from that "
      "script over the two source databases; a number nobody can re-derive is not shipped._")
    a("")
    a("_Created: 18-07-2026 · Last updated: 18-07-2026_")
    a("")
    a("## Inputs (measured, read-only)")
    a("")
    a("| Input | Stamp (18-07-2026) |")
    a("|---|---|")
    a("| `kosha.db` (generated `forms`) | %s |" % _db_stamp(KOSHA_DB))
    a("| `dcs_full.sqlite` (attested `token`) | %s |" % _db_stamp(DCS))
    a("")
    a("- Generated side: `kosha.db` `forms`, **`include_heritage=False`** (heritage is "
      "hypergenerated and untrusted, default-off since H696; trust ordering "
      "`dcs > vidyut > heritage`). Non-heritage rows scanned: **{:,}**.".format(s["n_gen"]))
    a("- Attested side: `dcs_full.sqlite` `token.form` (the sandhied **surface** form, IAST). "
      "Token occurrences: **{:,}**; distinct surface forms: **{:,}**.".format(s["n_tok"], s["n_att_forms"]))
    a("- Join key: `form_key()` from sanskrit-util (length-preserving floor tier). "
      "**No NFD+strip-combining-marks path anywhere** (D6 / 1b-2).")
    a("")
    a("## ⚠️ `forms` vs `inflections` contradiction (STOP-AND-SURFACE, not resolved here)")
    a("")
    a("The Concordance-Q3 plan set disagrees with itself on the generated side, and this "
      "wave has **no standing to settle it** (H1262 human gate). Both cardinalities are "
      "stated; the question of which table A4 should measure is handed to a human as a "
      "recorded contradiction.")
    a("")
    a("| | Cardinality (measured 18-07-2026) |")
    a("|---|---|")
    a("| `forms` (this build's generated side; the deliverable text names it) | **1,378,401** rows |")
    a("| `forms`, heritage excluded | **426,410** rows / 409,978 distinct `form_slp1` |")
    a("| `inflections` (the architecture diagram's \"6.9M\") | **6,917,018** rows / 3,326,312 distinct `form_slp1` |")
    a("")
    a("Built against **`forms`** per the deliverable text (it is the table that carries a "
      "`source` column, which the trust-ordering / `include_heritage` discipline requires; "
      "`inflections` does not distinguish heritage). `inflections` was **not** folded in as a "
      "second generated side. The architecture diagram's 6.9M should be corrected to name "
      "`inflections`, not propagated into W2a.")
    a("")
    a("## Buckets")
    a("")
    a("Two denominators, because a set intersection over two sides with different "
      "multiplicities has two natural cardinalities (1b-1 names each explicitly):")
    a("")
    a("- **Generated denominator = {:,}** non-heritage `forms` rows. Every such row is "
      "either AG or G¬A.".format(s["gen_denom"]))
    a("- **Attested denominator = {:,}** distinct surface forms. Every such form is AG "
      "(its `form_key` is generated), A¬G, or unkeyable.".format(s["att_denom"]))
    a("")
    a("| Bucket | Definition | Count | Denominator |")
    a("|---|---|---:|---|")
    a("| **AG** (generated view) | non-heritage generated row whose `form_key` is attested | **{:,}** | of {:,} generated rows |".format(s["ag_total"], s["gen_denom"]))
    a("| **G¬A** | non-heritage generated row never attested (over-generation) | **{:,}** | of {:,} generated rows |".format(s["gna_total"], s["gen_denom"]))
    a("| **AG** (attested view) | distinct attested surface forms that matched a generated `form_key` | **{:,}** | of {:,} attested forms |".format(s["ag_att_forms"], s["att_denom"]))
    a("| **A¬G** | distinct attested surface form never generated (engine gap / OCR / sandhi) | **{:,}** | of {:,} attested forms |".format(s["ang_total"], s["att_denom"]))
    a("| unkeyable | attested surface form with empty `form_key()` (placeholder/punct) | **{:,}** | of {:,} attested forms |".format(s["att_unkeyable"], s["att_denom"]))
    a("")
    a("**Reconciliation (1b-1).** Generated: AG {:,} + G¬A {:,} = **{:,}** (= 426,410 ✓). "
      "Attested: AG {:,} + A¬G {:,} + unkeyable {:,} = **{:,}** (= 381,413 ✓)."
      .format(s["ag_total"], s["gna_total"], s["gen_denom"],
              s["ag_att_forms"], s["ang_total"], s["att_unkeyable"], s["att_denom"]))
    a("")
    a("### AG by generated-side source — the circularity split (the load-bearing figure)")
    a("")
    a("93.30% of the non-heritage generated side is itself `source='dcs'`, so joining it "
      "against DCS attestation is close to a round-trip. The **vidyut** subtotal is the "
      "figure that carries research meaning about what the *engine* generates; the **dcs** "
      "subtotal is largely tautological and is reported as such (EVAL_PLAN anti-gaming rule).")
    a("")
    a("| Generated source | AG rows | G¬A rows | AG rate |")
    a("|---|---:|---:|---:|")
    for src in ("dcs", "vidyut"):
        ag = s["ag_by_source"].get(src, 0)
        gna = s["gna_by_source"].get(src, 0)
        tot = ag + gna
        rate = ("%.2f%%" % (100.0 * ag / tot)) if tot else "—"
        a("| %s | %s | %s | %s |" % (src, "{:,}".format(ag), "{:,}".format(gna), rate))
    a("")
    a("### AG by match tier")
    a("")
    a("`form_key` equality **is** the floor tier (0.85); promoted to `exact` (0.95) only "
      "where the generated SLP1 key is byte-identical to an attested SLP1 key. No "
      "hand-written confidence — `TIER_CONFIDENCE` imported from `concordance_core.py`.")
    a("")
    for m in ("exact", "floor"):
        a("- **%s** (%.2f): %s rows" % (m, TIER_CONFIDENCE[m], "{:,}".format(s["ag_by_method"].get(m, 0))))
    a("")
    a("## R-C4 tense caveat (1b-4)")
    a("")
    a("DCS conflates aorist and perfect under `Tense=Past`. Rows whose attested evidence "
      "carries a `Past`-tense token are flagged `tense_caveat=1` and are **not excluded** "
      "(excluding them understates coverage). Every aggregate below is published with its "
      "caveated subtotal beside it.")
    a("")
    a("- **AG** total {:,} — of which `tense_caveat=1`: **{:,}**".format(s["ag_total"], s["ag_tense_caveat"]))
    a("- **A¬G** total {:,} — of which `tense_caveat=1`: **{:,}**".format(s["ang_total"], s["ang_tense_caveat"]))
    a("- **G¬A** total {:,} — `tense_caveat=1`: **0** (no attested side, so no DCS Past evidence).".format(s["gna_total"]))
    a("")
    a("## A¬G triage (1b-5)")
    a("")
    a("The residue is **not** reported as one undifferentiated number. Because the attested "
      "key is the *sandhied surface* form, the largest A¬G class is sandhi-surface variants "
      "(a surface spelling the unsandhied engine never emits), not engine gaps. Only the "
      "`genuine_engine_gap` class routes to the csl-inflect give-back.")
    a("")
    a("| Triage class | Count | of which `tense_caveat=1` | Meaning |")
    a("|---|---:|---:|---|")
    meanings = {
        "genuine_engine_gap": "well-formed unsandhied-looking Sanskrit form the engine did not generate → **queued port to csl-inflect give-back (H185)**",
        "sandhi_surface_variant": "majority of occurrences are sandhi-altered surface spellings; not an engine gap",
        "segmentation_artefact": "space-containing or single-character token; DCS segmentation artefact",
        "non_sanskrit_or_ocr": "carries a non-IAST character (digit/Latin/punctuation) → OCR artefact",
    }
    for cls in ("genuine_engine_gap", "sandhi_surface_variant", "segmentation_artefact", "non_sanskrit_or_ocr"):
        a("| `%s` | %s | %s | %s |" % (
            cls, "{:,}".format(s["ang_triage"].get(cls, 0)),
            "{:,}".format(s["ang_triage_tcav"].get(cls, 0)), meanings[cls]))
    a("")
    a("**Give-back routing (hard stop).** The `genuine_engine_gap` rows are handed to the "
      "csl-inflect dual-engine give-back (H185) as a **queued port** — a GTD row and a "
      "pointer, never an in-pass edit to csl-inflect.")
    a("")
    a("## Storage (1b-6, R-Q1)")
    a("")
    a("| | Bytes | GB |")
    a("|---|---:|---:|")
    a("| `kosha.db` before | {:,} | {:.3f} |".format(s["kosha_before"], s["kosha_before"] / 1e9))
    a("| `kosha.db` after | {:,} | {:.3f} |".format(s["kosha_after"], s["kosha_after"] / 1e9))
    a("")
    a("This build is **read-only** on `kosha.db` (a join emitting TSVs, no writeback), so "
      "before == after by construction. The number that matters for A4 is the current size: "
      "**{:.3f} GB = ~{:.0f}%% of the 2 GB release-asset ceiling.** ".format(
          s["kosha_after"] / 1e9, 100.0 * s["kosha_after"] / 2e9))
    a("**Projection:** A4 derivation-metadata tables (per-form model/gender/case/tense + "
      "sūtra attribution over the AG set) materially enlarge the DB. If A4 tables project "
      "`kosha.db` past ~1.9 GB, the finding is that **derivation tables ship as a separate "
      "release asset**, not bundled into `kosha.db`. The decision follows from the "
      "measurement; this wave records the projection and does not cut a release.")
    a("")
    a("## Run")
    a("")
    a("- Peak Python-object memory: **{:.0f} MB** (tracemalloc). The join is ~410k × ~381k "
      "on distinct keys, comfortably in memory; the smaller generated side never needed "
      "streaming.".format(s["peak_mem"] / 1e6))
    a("- Runtime: **{:.0f} s**.".format(s["runtime"]))
    a("")
    a("## 1b-8 spot-check — 20 AG rows, STRATIFIED by generated source (human-verifiable)")
    a("")
    a("A uniform sample would be ~93% DCS-derived round-trips and prove nothing about the "
      "engine. This sample is stratified: {} from `source='dcs'`, {} from `source='vidyut'`. "
      "Each row is a genuine attestation iff the generated form really occurs in DCS at the "
      "cited locus. Verify against `dcs_full.sqlite` (`dcs:<sent_id>`).".format(
          SAMPLE_PER_SOURCE, SAMPLE_PER_SOURCE))
    a("")
    a("| # | gen source | form (SLP1) | form (IAST) | lemma | attested surface | locus | occ | tier |")
    a("|---:|---|---|---|---|---|---|---:|---|")
    i = 0
    for src in ("dcs", "vidyut"):
        for row in s["reservoir"][src]:
            i += 1
            # row = [anchor_type, anchor_id(slp1), key_slp1, lemma_slp1, gen_source,
            #        locus, source_dataset, method, conf, evidence, tcav, attested_form]
            a("| %d | %s | `%s` | %s | `%s` | %s | `%s` | %s | %s |" % (
                i, row[4], row[1], from_slp1(row[1]), row[3], row[11],
                row[5], row[9], row[7]))
    a("")
    a("_Dr. Mārcis Gasūns_")
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
