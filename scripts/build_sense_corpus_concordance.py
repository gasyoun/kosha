#!/usr/bin/env python
"""Build the per-SENSE corpus-attestation layer (H1455 / PLAN_KOSHA_SENSE_
RECONCILIATION_2026H2). The middle arrow of

    (headword) -> (numbered PWG sense) -> (DCS/Samudra attestation)

where today only (headword)->(attestation) exists (build_dict_corpus_
concordance.py, REUSED here). A SIDECAR: it never mutates MW/kosha `senses`.

Origin: the नागदन्त translator-split — PWG keeps ONE homonym with senses
a) Elephantenzahn (tusk) / b) Pflock in der Wand (peg), each with its own
<ls> loci; thin bilingual glossaries drop the per-sense locus and translators
split. This layer restores it.

Tiers (hybrid aligner, ARCHITECTURE step B/C):
  * ls      PWG's OWN <ls> citation placed under the sense — the load-bearing,
            guaranteed-correct sense<->passage witness (conf 0.99).
  * locus   a DCS attestation whose (text, ref) matches a sense's resolved
            <ls> locus set (conf 0.90). Rare: DCS uses critical-edition
            numbering, PWG cites Böhtlingk-Roth editions (VERIFICATION risk 1)
            — the honest yield is reported, never faked.
  * overlap high-precision shared tokens (proper names, Latin binomials,
            digits) between the DCS `meanings` gloss and a PWG sense gloss
            (conf 0.5-0.7). Same-language on the shared tokens across the
            DE/EN gap (VERIFICATION risk 2).
  * llm     residue (no/ambiguous candidate) -> a gloss-grounded adjudicator
            Workflow (wf/sense_adjudicate.js). BOUNDED + logged; deferred in
            an unattended run (parked to the review queue) so the deterministic
            tiers stay byte-reproducible (A8). See --run-llm.

confidence<tau  -> sense_review_queue.tsv (kept, never dropped, A5).

Outputs (data/concordance/):
  sense_corpus_concordance.tsv   headword, sense_id, lemma, locus, conf, method, rights (+ context)
  sense_corpus_coverage.tsv      per (headword,sense): #ls, #dcs, resolution, variant_of
  sense_review_queue.tsv         confidence<tau rows for the deferred human pass
  SENSE_CONCORDANCE_BUILD_REPORT.md
  concordance/senses/data/kwic_<a>.js  sense-sharded KWIC for the static viewer

Inputs (consume, never re-derive):
  data/concordance/pwg_sense_loci.tsv        H1456 export (regenerable)
  data/concordance/sense_pilot_headwords.tsv Step 0 (select_sense_pilot.py)
  data/concordance/dict_corpus_concordance.tsv  headword<->DCS-lemma (H380)
  VisualDCS .../dcs_full.sqlite               DCS 2026 (CC BY 4.0)
  RussianTranslation/src/pwg_sources.py       <ls> abbrev resolver (pwgbib)

H1670 — SCALE (--pilot / --out-dir / --locus-scan full). Two independent limits
capped wave-1's reach, and they must be kept apart:

  * FRAME WIDTH — the build only ever ran over its own 500-headword frame, so
    every other PWG headword is `grounding_not_computed`, not ungrounded.
    `--pilot PATH` runs the identical build over a wider frame.
  * PASSAGE DEPTH — `dcs_kwic()` samples `--kwic-per` (3) passages per DCS lemma
    for the VIEWER, and the locus tier then tested each sense's <ls> against only
    those 3. On the wave-1 frame that is 3,435 of 1,148,630 available passages:
    the exact-verse test ran through a 0.299% keyhole, so its yield measured the
    sample, not the corpus. `--locus-scan full` pre-computes the addresses the
    frame's senses actually cite, pulls exactly the DCS passages sitting at those
    addresses, and feeds them to the SAME verse_equal()/MBh-adhyāya predicates.
    No criterion is relaxed, no tier added, no heuristic substituted — the
    matcher is unchanged and merely stops being blindfolded. `kwic` (the default)
    keeps wave-1's output byte-identical.
"""
import argparse
import collections
import io
import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sense_loci_core as slc  # noqa: E402
from concordance_core import citable_locus  # noqa: E402  (REUSE the host-independent DCS cite)
from mbh_vulgate import MBhVulgate  # noqa: E402  (REUSE csl-atlas f8 PWG→vulgate crosswalk)

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent if (ROOT.parent / "VisualDCS").exists() else ROOT.parent.parent
DCS = GH / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"
DICT_CONC = ROOT / "data" / "concordance" / "dict_corpus_concordance.tsv"
PILOT = ROOT / "data" / "concordance" / "sense_pilot_headwords.tsv"

OUT_DATA = ROOT / "data" / "concordance"
OUT_WEB = ROOT / "concordance" / "senses" / "data"

TAU = 0.60           # marked default (IMPLEMENTATION step 5); logged in the report
KWIC_PER = 3         # samples per DCS attestation shown per sense (stated cap)
SENT_TRUNC = 160
CONF = {"ls": 0.99, "locus": 0.90, "overlap_strong": 0.70, "overlap_weak": 0.50, "llm": 0.0,
        # H1670: the DCS passage's address stops at the chapter/hymn (no
        # sent_counter), so the match is hymn-level corroboration — reported as
        # its own tier so no headline reads it as exact-verse identity.
        "locus_chapter": 0.70,
        # MBh via the csl-atlas f8 vulgate crosswalk (PWG→Nīlakaṇṭha-vulgate is
        # SOLVED; the DCS side is BORI-critical, so matching is adhyāya-level
        # corroboration with ~±1 vulgate↔critical drift — never exact identity).
        "locus_mbh_exact": 0.80, "locus_mbh_adj": 0.65}

# PWG <ls> source abbrev -> DCS text name, for the (rare, honest) locus tier.
# Only the texts DCS actually carries AND whose reference scheme could align.
PWG_TO_DCS_TEXT = {
    # ⚠️ Keys are the abbrev as `sense_loci_core.split_ls()` yields it, upper-cased
    # and stripped of a trailing '.' — so they carry PWG's DIACRITICS. "RV" (ASCII)
    # never matched anything: PWG's Ṛgveda abbrev is "ṚV", and that one dead key
    # made the single most canonically-numbered text in the corpus — 32,075 <ls>
    # citations, 6.78% of the frame's total, more than any source but MBh —
    # permanently invisible to the locus tier. Fixed in H1670; keep the ASCII form
    # as an alias so an ASCII-folded input still resolves.
    "ṚV": "Ṛgveda", "RV": "Ṛgveda",
    "AV": "Atharvaveda (Śaunaka)", "ŚAT. BR": "Śatapathabrāhmaṇa",
    "AIT. BR": "Aitareyabrāhmaṇa", "TS": "Taittirīyasaṃhitā", "R": "Rāmāyaṇa",
    "MBH": "Mahābhārata", "SUŚR": "Suśrutasaṃhitā", "HARIV": "Harivaṃśa",
    "CHĀND. UP": "Chāndogyopaniṣad", "NIR": "Nirukta",
    # H1670 additions — texts DCS carries whose PWG citation scheme is verse-
    # structural and provably parallel to DCS's chapter/counter address. Each was
    # checked against its pwgbib entry, NOT against a name resemblance:
    "VS": "Vājasaneyisaṃhitā (Mādhyandina)",   # adhyāya, mantra
    "YĀJÑ": "Yājñavalkyasmṛti",                # adhyāya, śloka
    "KUMĀRAS": "Kumārasaṃbhava",               # sarga, śloka
    "BHĀG. P": "Bhāgavatapurāṇa",              # skandha, adhyāya, śloka
    # H1691 additions — every DCS-HAS-UNMAPPED abbrev above 0.05% citation mass
    # was adjudicated against BOTH its pwgbib entry and its real <ls> strings,
    # then screened on whether PWG's tuples land on that text's addresses at all
    # and, decisively, on whether the candidate OUTRANKS the other 269 DCS texts
    # on those same tuples (a plain hit rate is confounded by address-space size:
    # a 2-tuple exists in almost any large text). Verified band 25-98%; rejected
    # band 0.0-1.4%. Per-abbrev verdicts, evidence and reasons:
    # SanskritLexicography/RussianTranslation/research/pwg_ls_dcs_scheme_verdicts.tsv
    #
    # ⚠️ Two of these were classed DCS-LACKS — "a genuine corpus gap no crosswalk
    # can close" — by the H1670 backlog. That class is NOT trustworthy: its
    # candidate generator matches on the GERMAN pwgbib prose, and PWG names
    # Pāṇini and Manu by author and language ("PĀṆINI'S acht Bücher
    # grammatischer Regeln"), never by Sanskrit title. The two largest crosswalk
    # wins in the dictionary were hiding in the class labelled untouchable.
    "P": "Aṣṭādhyāyī",                         # adhyāya, pāda, sūtra
    "M": "Manusmṛti",                          # adhyāya, śloka
    "KĀTY. ŚR": "Kātyāyanaśrautasūtra",        # adhyāya, kaṇḍikā, sūtra
    "ŚĀṄKH. ŚR": "Śāṅkhāyanaśrautasūtra",      # adhyāya, kaṇḍikā, sūtra
    "PAÑCAV. BR": "Pañcaviṃśabrāhmaṇa",        # prapāṭhaka, khaṇḍa, verse
    "ĀŚV. GṚHY": "Āśvalāyanagṛhyasūtra",       # adhyāya, kaṇḍikā, sūtra
    "GOBH": "Gobhilagṛhyasūtra",               # prapāṭhaka, khaṇḍa, sūtra
    "BṚH. ĀR. UP": "Bṛhadāraṇyakopaniṣad",     # adhyāya, brāhmaṇa, verse
    "KIR": "Kirātārjunīya",                    # sarga, śloka
    "GĪT": "Gītagovinda",                      # sarga, verse
    "KAṬHOP": "Kaṭhopaniṣad",                  # vallī, verse
    "BHARTṚ": "Śatakatraya",                   # śataka, verse
    # DELIBERATELY NOT MAPPED although DCS carries a same-sounding text — the
    # citation schemes do not correspond, and a name match is not a crosswalk:
    #   VP        PWG cites WILSON'S TRANSLATION by page, not the Sanskrit verse
    #   KAUŚ      PWG numbers the kaṇḍikās continuously; DCS numbers per adhyāya
    #   KATHĀS    Brockhaus numbers 124 taraṅgas; DCS's KSS has 44 chapters
    #   AK/TRIK   kośa numbering (kāṇḍa, varga, śloka) vs DCS's single counter
    #   HIT/DAŚAK pwgbib says the two numbers are PAGE and LINE, not book and verse
    #   KĀṬH      right work, but PWG stops at the anuvāka where DCS reaches the
    #             mantra — a 2-tuple can never equal a 3-tuple. Same for PĀR. GṚHY
    #   TBR       right work (NOT the Taittirīya*saṃhitā* the backlog offered),
    #             but the Yajurveda prose texts cross-hit: Maitrāyaṇīsaṃhitā
    #             scores 43% against TB's 15.4%, so the pairing is unverifiable
    #   ŚĀṄKH. BR / ŚĀṄKH. GṚHY / ĀŚV. ŚR / TAITT. ĀR / TAITT. UP
    #             all five are the WRONG work in the backlog's candidate column;
    #             DCS carries the right one in every case, and none corresponds
    #   AMAR/CAURAP/SĀṂKHYAK/MEGH  1-component loci; verse_equal() needs >=2
    #   KĀŚ/NIGH. PR/BHĀVAPR       the citations carry no address at all
    # These stay in the residue and are listed as a ranked crosswalk backlog.
}

# Modern-copyright sources whose gloss text may NOT be published in bulk
# (corpus_gate.RIGHTS intent). None are consumed in wave-1 — PWG <ls> sources
# are pre-1900 editions and DCS is CC BY 4.0 — but the classifier is wired so
# any future modern gloss is stamped evidence-only, never leaked to the viewer.
MODERN_SOURCES = {"KOCHERGINA", "SMIRNOV"}


def rights_for(source_abbrev):
    key = (source_abbrev or "").upper().strip().rstrip(".")
    return "evidence-only" if key in MODERN_SOURCES else "public"


def load_pilot(path=None):
    """-> ordered list of (slp1, hom) in the pilot, plus the raw set."""
    order, seen = [], set()
    path = Path(path) if path else PILOT
    if not path.exists():
        return order, seen
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        idx = {c: i for i, c in enumerate(header)}
        for line in f:
            p = line.rstrip("\n").split("\t")
            key = (p[idx["slp1"]], p[idx["hom"]])
            if key not in seen:
                seen.add(key)
                order.append(key)
    return order, seen


def load_dict_links(pilot_slp1):
    """slp1 -> [(dcs_lemma_iast, lemma_id, evidence_count, tier, n_texts)] for
    pilot headwords only (REUSE build_dict_corpus_concordance output)."""
    out = collections.defaultdict(list)
    with open(DICT_CONC, encoding="utf-8-sig") as f:
        header = f.readline().rstrip("\n").split("\t")
        idx = {c: i for i, c in enumerate(header)}
        # header uses the pre-H539 names corpus_locus/corpus_text_id in this file
        loc_col = "corpus_locus" if "corpus_locus" in idx else "target_locus"
        for line in f:
            p = line.rstrip("\n").split("\t")
            slp1 = p[idx["anchor_key_slp1"]]
            if slp1 not in pilot_slp1:
                continue
            locus = p[idx[loc_col]]
            if not locus.startswith("lemma:"):
                continue
            lemma_id = int(locus.split(":", 1)[1])
            out[slp1].append((
                p[idx["dcs_lemma_iast"]], lemma_id,
                int(p[idx["evidence_count"]]), p[idx["match_method"]],
                int(p[idx["n_texts"]]),
            ))
    return out


def dcs_meanings(con, lemma_ids):
    out = {}
    if not lemma_ids:
        return out
    ids = list(lemma_ids)
    for i in range(0, len(ids), 900):
        chunk = ids[i:i + 900]
        q = "SELECT lemma_id, meanings FROM lemma WHERE lemma_id IN (%s)" % \
            ",".join("?" * len(chunk))
        for lid, m in con.execute(q, chunk):
            out[lid] = m or ""
    return out


def dcs_kwic(con, lemma_ids, per):
    """lemma_id -> [ {form, cite, locus, source_text, ref, sent} ] (<=per)."""
    out = collections.defaultdict(list)
    if not lemma_ids:
        return out
    ids = list(lemma_ids)
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        q = """
        SELECT lemma_id, form, sent_id, text_name, ref, cnt, sub, sent FROM (
            SELECT t.lemma_id lemma_id, t.form form, s.sent_id sent_id,
                   x.name text_name, c.ref ref, s.sent_counter cnt,
                   s.sent_subcounter sub, s.text_sandhied sent,
                   ROW_NUMBER() OVER (PARTITION BY t.lemma_id ORDER BY s.sent_id) rn
            FROM token t JOIN sentence s ON s.id=t.sentence_id
            JOIN chapter c ON c.chapter_id=s.chapter_id
            JOIN text x ON x.text_id=c.text_id
            WHERE t.lemma_id IN (%s)
        ) WHERE rn <= %d
        """ % (",".join("?" * len(chunk)), per)
        for lid, form, sid, text, ref, cnt, sub, sent in con.execute(q, chunk):
            sent = (sent or "").strip()
            if len(sent) > SENT_TRUNC:
                sent = sent[:SENT_TRUNC] + "…"
            out[lid].append({
                "form": form or "",
                "cite": citable_locus(sid),
                "locus": "%s, %s, %s" % (text, ref, cnt),
                "source_text": text, "ref": ref, "cnt": cnt, "sent": sent,
            })
    return out


def parse_ref_nums(s):
    """Extract the comparable numeric tuple from a DCS ref/counter or a PWG
    <ls> locus: 'MBh, 12, 99' -> (12,99); '12,3630' -> (12,3630)."""
    import re
    return tuple(int(x) for x in re.findall(r"\d+", s or ""))


def numeric_address(ref, cnt):
    """-> (numeric_tuple, level) for a DCS passage, or None if its address is NOT
    tuple-comparable and the locus tiers must therefore ABSTAIN.

    H1670. `parse_ref_nums` keeps only the digits, so a DCS ref that encodes a
    book/section as a NAME had that name silently dropped — collapsing distinct
    passages into one numbering space:

      'Rām, Bā, 6'  and  'Rām, Utt, 6'   both -> (6, …)
      'Su, Cik., 29' and 'Su, Sū., 29'   both -> (29, …)
      'MBh, 6, BhaGī 1'                       -> (6, 1), i.e. read as parvan 6
                                                 adhyāya 1, which is NOT where
                                                 the Bhagavadgītā sits (6.25 ff.)

    A shared (sarga, verse) pair then "matched" in up to 7 different Rāmāyaṇa
    books at once — a false positive that the wave-1 3-passage sample was simply
    too thin to expose. The rule: every component after the siglum must be a
    plain integer, else the address carries information the tuple cannot, and we
    abstain rather than guess. Same discipline as verse_equal() abstaining for
    edition-numbered texts.

    `level` distinguishes an address that reaches the verse (`sent_counter`
    present) from one that stops at the chapter/hymn — 20.9% of DCS's Ṛgveda and
    24.1% of its Atharvaveda sentences carry no counter, so a match there is
    hymn-level corroboration and must not be reported as exact-verse identity.
    """
    parts = [p.strip() for p in (ref or "").split(",")]
    for p in parts[1:]:                       # parts[0] is the text siglum
        if not p.isdigit():
            return None
    nums = [int(p) for p in parts[1:]]
    c = str(cnt).strip() if cnt is not None else ""
    if c.isdigit():
        return tuple(nums + [int(c)]), "verse"
    return tuple(nums), "chapter"


def verse_equal(pwg_nums, dcs_nums):
    """A real verse-level locus match: the full numeric tuples are EQUAL and
    carry >=2 components (so a shared book/page number alone never matches).
    Fires for canonically-numbered texts (Ṛgveda/Atharvaveda — maṇḍala.hymn.
    verse stable across editions); abstains for edition-numbered texts whose
    Böhtlingk-Roth numbering differs from DCS's critical edition."""
    return len(pwg_nums) >= 2 and tuple(pwg_nums) == tuple(dcs_nums)


# --------------------------------------------------------------------------- #
# H1670 — targeted locus scan (--locus-scan full)                             #
# --------------------------------------------------------------------------- #
def wanted_addresses(pilot_order, groups, mbh):
    """Pre-pass: every DCS address the FRAME's senses actually cite.

    Uses `slc.split_ls` only — the cheap string split that yields (abbrev,
    locus). The expensive `pwg_sources.resolve()` bibliography lookup is NOT
    needed to know which address a citation points at, and is left to the main
    pass, so this costs one extra string split per <ls>, not a second resolve.

    -> (addr, mbh_adh)
       addr    : {(dcs_text_name, numeric_tuple)}    for the exact-verse tier
       mbh_adh : {(parvan, adhyaya)}                  for the MBh corroboration
                 tier, ALREADY EXPANDED by the ±1 vulgate↔critical drift the
                 tier tolerates, so lookup is a plain set membership test.
    """
    addr, mbh_adh = set(), set()
    for key in pilot_order:
        for s in slc.leaves(groups.get(key, [])):
            for raw in s.ls_raw:
                abbrev, locus = slc.split_ls(raw)
                ab = (abbrev or "").upper().strip().rstrip(".")
                dcs_text = PWG_TO_DCS_TEXT.get(ab)
                if dcs_text:
                    addr.add((dcs_text, parse_ref_nums(locus)))
                if mbh.ok and ab == "MBH":
                    nums = parse_ref_nums(locus)
                    if len(nums) >= 2:
                        vulg = mbh.resolve(nums[0], nums[1])
                        if vulg:
                            for d in (-1, 0, 1):
                                mbh_adh.add((nums[0], vulg["adhyaya"] + d))
    return addr, mbh_adh


def dcs_passages_at(con, lemma_ids, addr, mbh_adh, per):
    """The DCS passages that sit at an address the frame cites — lemma_id ->
    [passage dict], same shape `dcs_kwic` returns so the matcher is untouched.

    One streaming pass over the mapped texts only (~2.15 M of DCS's tokens).
    Rows are kept ONLY when the passage's address is one the frame's <ls> point
    at, so memory stays proportional to the CANDIDATE set, not to the corpus.
    This is a retrieval change; the accept/reject decision remains entirely in
    verse_equal() and the MBh ±1 test downstream.
    """
    out = collections.defaultdict(list)
    seen = collections.Counter()
    texts = sorted(set(PWG_TO_DCS_TEXT.values()) | {"Mahābhārata"})
    q = """
    SELECT x.name, c.ref, s.sent_counter, s.sent_subcounter, s.sent_id,
           s.text_sandhied, t.lemma_id, t.form
    FROM token t
    JOIN sentence s ON s.id = t.sentence_id
    JOIN chapter  c ON c.chapter_id = s.chapter_id
    JOIN text     x ON x.text_id = c.text_id
    WHERE x.name IN (%s)
    """ % ",".join("?" * len(texts))
    n_scanned = n_kept = 0
    for (name, ref, cnt, sub, sid, sent, lid, form) in con.execute(q, texts):
        n_scanned += 1
        if lid not in lemma_ids:
            continue
        a = numeric_address(ref, cnt)
        if a is None:                    # not tuple-comparable → never a candidate
            continue
        nums = a[0]
        hit = (name, nums) in addr
        if not hit and name.startswith("Mahābhārata"):
            pn = numeric_address(ref, None)[0]
            hit = len(pn) >= 2 and (pn[0], pn[1]) in mbh_adh
        if not hit:
            continue
        k = (lid, name, nums)
        if seen[k] >= per:
            continue
        seen[k] += 1
        n_kept += 1
        stext = (sent or "").strip()
        if len(stext) > SENT_TRUNC:
            stext = stext[:SENT_TRUNC] + "…"
        out[lid].append({
            "form": form or "", "cite": citable_locus(sid),
            "locus": "%s, %s, %s" % (name, ref, cnt),
            "source_text": name, "ref": ref, "cnt": cnt, "sent": stext,
        })
    print("  locus-scan full: %s token rows scanned in the mapped texts, "
          "%s kept as address candidates (%d lemmas)"
          % (format(n_scanned, ","), format(n_kept, ","), len(out)), file=sys.stderr)
    return out


def overlap_assign(dcs_meaning, sense_tokens_list):
    """-> (best_index, strength, shared) or (None, 0, set()).
    sense_tokens_list: [set(content_tokens per leaf sense)]. Match the DCS
    lemma meaning tokens against each sense; a shared proper-noun/binomial/
    digit is worth more than a generic word."""
    mtok = slc.content_tokens(dcs_meaning)
    if not mtok:
        return None, 0, set()
    best_i, best_shared = None, set()
    for i, stok in enumerate(sense_tokens_list):
        shared = mtok & stok
        if len(shared) > len(best_shared):
            best_shared, best_i = shared, i
    if best_i is None or not best_shared:
        return None, 0, set()
    # strength: proper/binomial/digit token present, or >=3 shared -> strong
    strong = any(any(ord(c) > 127 for c in t) or t.isdigit() or len(t) >= 6
                 for t in best_shared) or len(best_shared) >= 3
    return best_i, (2 if strong else 1), best_shared


def is_ka_variant(slp1, pilot_slp1_set):
    """nAgadantaka -> nAgadanta (record variant_of edge, ARCHITECTURE)."""
    for suf in ("ka", "aka"):
        if slp1.endswith(suf):
            base = slp1[: -len(suf)]
            if base in pilot_slp1_set:
                return base
            if base + "a" in pilot_slp1_set:
                return base + "a"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=None, help="pwg_sense_loci.tsv (default: data/concordance or sample)")
    ap.add_argument("--tau", type=float, default=TAU)
    ap.add_argument("--kwic-per", type=int, default=KWIC_PER)
    ap.add_argument("--viewer", action="store_true", help="also (re)build concordance/senses/ shards")
    ap.add_argument("--run-llm", action="store_true", help="dispatch the residue Workflow (bounded, paid) — off by default")
    # --- H1670 scale knobs (all default to wave-1 behaviour) ------------------
    ap.add_argument("--pilot", default=None, help="frame file (default: the frozen 500)")
    ap.add_argument("--out-dir", default=None, help="output dir (default: data/concordance)")
    ap.add_argument("--locus-scan", choices=("kwic", "full"), default="kwic",
                    help="kwic = test <ls> against the --kwic-per viewer sample "
                         "(wave-1, byte-identical); full = against every DCS "
                         "passage at an address the frame cites (same predicate)")
    ap.add_argument("--no-ls-rows", action="store_true",
                    help="omit the method=ls self-witness rows from the bulk TSV. "
                         "They are PWG citing itself, are excluded from every "
                         "headline, and at scale are ~99.9%% of the file; the "
                         "per-sense n_ls/n_ls_resolved counts are unaffected.")
    args = ap.parse_args()
    tau = args.tau
    out_data = Path(args.out_dir) if args.out_dir else OUT_DATA

    print("loading pilot headwords ...", file=sys.stderr)
    pilot_order, pilot_set = load_pilot(args.pilot)
    pilot_slp1 = {s for s, _h in pilot_set}
    print("  %d pilot (slp1,hom) groups, %d distinct slp1" % (len(pilot_set), len(pilot_slp1)), file=sys.stderr)

    groups = slc.load_pwg_senses(args.input)
    print("  %d PWG (slp1,hom) groups loaded" % len(groups), file=sys.stderr)

    mbh = MBhVulgate()   # REUSE csl-atlas f8 PWG→vulgate crosswalk (may be absent → tier off)
    print("  MBh vulgate crosswalk: %s (%d parvans)" % (mbh.ok, len(mbh._by_parvan)), file=sys.stderr)

    dict_links = load_dict_links(pilot_slp1)
    all_lemma_ids = {lid for v in dict_links.values() for _i, lid, _e, _t, _n in v}
    print("  %d pilot headwords DCS-attested, %d distinct DCS lemmas" % (len(dict_links), len(all_lemma_ids)), file=sys.stderr)

    con = sqlite3.connect(str(DCS))
    meanings = dcs_meanings(con, all_lemma_ids)
    kwic = dcs_kwic(con, all_lemma_ids, args.kwic_per)
    # H1670: candidates for the locus tiers. In `kwic` mode this stays empty and
    # the tiers see only the viewer sample, exactly as in wave-1.
    cand = {}
    if args.locus_scan == "full":
        w_addr, w_mbh = wanted_addresses(pilot_order, groups, mbh)
        print("  frame cites %s distinct DCS-mappable addresses, %s MBh adhyāyas (±1)"
              % (format(len(w_addr), ","), format(len(w_mbh), ",")), file=sys.stderr)
        cand = dcs_passages_at(con, all_lemma_ids, w_addr, w_mbh, args.kwic_per)
    con.close()

    # ---- per-pilot-group build ------------------------------------------------
    conc_rows = []        # concordance rows (dicts)
    review_rows = []      # confidence<tau OR unassigned residue
    coverage_rows = []    # per (slp1,hom,sense) coverage
    viewer = collections.OrderedDict()   # slp1 -> entry for the viewer

    ls_total = ls_resolved = 0           # A2 metric accumulators (pilot leaf senses)
    mbh_ls_total = mbh_ls_resolved = 0   # MBh <ls> resolved to a vulgate address (wave-1.5)
    method_counts = collections.Counter()
    n_dcs_links = n_dcs_assigned = n_locus_hits = 0

    for (slp1, hom) in pilot_order:
        senses = slc.leaves(groups.get((slp1, hom), []))
        if not senses:
            continue
        # display iast (first sense's group), from union not available here -> derive from slp1 via kwic? keep slp1.
        variant_of = is_ka_variant(slp1, pilot_slp1)

        # Step 2 — resolve each leaf sense's <ls>, emit method=ls witness rows.
        sense_view = []
        sense_tokens = []
        sense_resolved_loci = []   # per sense: set of (dcs_text_name, numeric_tuple) from resolved <ls>
        sense_mbh_adh = []         # per sense: set of (parvan, adhyaya) resolved via the MBh vulgate crosswalk
        for s in senses:
            gloss = s.gloss_clean()
            # overlap keys on the GLOSS only — proper names / Latin binomials /
            # digits shared across DE↔EN. <ls> loci are excluded (their source
            # abbrevs + verse numbers would spuriously overlap the DCS meaning).
            sense_tokens.append(slc.content_tokens(gloss))
            ls_items = []
            rloci = set()
            madh = set()
            for raw in s.ls_raw:
                r = slc.resolve_ls(raw)
                ls_total += 1
                if r["resolved"]:
                    ls_resolved += 1
                rights = rights_for(r["source_abbrev"])
                locus_disp = (r["source_name"].split(",")[0][:40] if r["source_name"] else r["source_abbrev"])
                if r["locus"]:
                    locus_disp = (locus_disp + " " + r["locus"]).strip()
                # MBh: resolve PWG continuous verse -> Nīlakaṇṭha vulgate (csl-atlas f8).
                vulg = None
                if mbh.ok and (r["source_abbrev"] or "").upper().strip().rstrip(".") == "MBH":
                    nums = parse_ref_nums(r["locus"])
                    if len(nums) >= 2:
                        mbh_ls_total += 1
                        vulg = mbh.resolve(nums[0], nums[1])
                        if vulg:
                            mbh_ls_resolved += 1
                            madh.add((nums[0], vulg["adhyaya"]))
                            locus_disp += " → vulg %s" % vulg["vulgate"]
                if not args.no_ls_rows:
                    conc_rows.append({
                        "slp1": slp1, "hom": hom, "sense_id": s.sense_id, "lemma": slp1,
                        "locus": locus_disp, "cite": "pwgls:%s|%s" % (r["source_abbrev"], r["locus"]),
                        "conf": CONF["ls"], "method": "ls", "rights": rights,
                        "source": r["source_abbrev"], "gloss": gloss[:80], "sent": "",
                    })
                method_counts["ls"] += 1
                # short source name for the viewer (pwgbib expansions are full
                # German bibliography paragraphs — keep only the leading title,
                # else every <ls> item bloats the shard by hundreds of chars).
                short_src = None
                if r["source_name"]:
                    short_src = r["source_name"].split("(")[0].split(",")[0].strip()[:48]
                ls_items.append({"raw": raw, "abbrev": r["source_abbrev"], "locus": r["locus"],
                                 "source": short_src, "resolved": r["resolved"], "rights": rights,
                                 "vulgate": vulg["vulgate"] if vulg else None})
                # for the locus tier: map resolved abbrev -> DCS text + numeric
                dcs_text = PWG_TO_DCS_TEXT.get((r["source_abbrev"] or "").upper().strip().rstrip("."))
                if dcs_text:
                    rloci.add((dcs_text, parse_ref_nums(r["locus"])))
            sense_resolved_loci.append(rloci)
            sense_mbh_adh.append(madh)
            sense_view.append({
                "sense_id": s.sense_id, "gloss": gloss[:200],
                "ls": ls_items, "dcs": [],
            })

        # Step 3 — DCS attestation -> sense candidates.
        unassigned = []
        for (lemma_iast, lemma_id, ev, tier, n_txt) in dict_links.get(slp1, []):
            n_dcs_links += 1
            # Address-targeted candidates FIRST (H1670 --locus-scan full), then
            # the viewer sample. The sample stays in the list so an unmatched
            # link still has passages to display and the overlap tier is
            # unaffected; ordering only decides which equal-scoring passage is
            # shown, never whether a match is accepted.
            passages = cand.get(lemma_id, []) + kwic.get(lemma_id, [])
            # (i) locus-match — REAL verse-level equality only. The DCS passage
            # tuple is (text, ref-nums + sent-counter); it must equal a sense's
            # resolved <ls> numeric tuple for the same text. This fires for
            # canonically-numbered texts (Ṛgveda/Atharvaveda: maṇḍala,hymn,verse
            # stable across editions) and correctly ABSTAINS for edition-numbered
            # texts (MBH/Rām/Suśruta — Böhtlingk-Roth continuous verse ≠ DCS
            # critical-edition adhyāya.śloka), per the spike. A shared book number
            # is NOT a match (a book has thousands of verses).
            matched_i = None
            matched_level = None
            matched_passages = []
            for pi, sr in enumerate(sense_resolved_loci):
                for kw in passages:
                    # ABSTAIN when the DCS address is not tuple-comparable (a
                    # named book/section the tuple would silently drop) — H1670.
                    addr = numeric_address(kw["ref"], kw.get("cnt"))
                    if addr is None:
                        continue
                    kwtuple, level = addr
                    for (dt, nums) in sr:
                        if not nums or kw["source_text"] != dt:
                            continue
                        if verse_equal(nums, kwtuple):
                            matched_i = pi
                            matched_level = level
                            # H1691: keep each passage's OWN level. A sense can
                            # match several passages at once whose addresses
                            # bottom out differently — one at the verse, another
                            # only at the chapter — and stamping them all with a
                            # single sense-level label put 507 of H1670's 12,280
                            # `locus` rows (4.13%, 504 of them Aitareyabrāhmaṇa)
                            # in the exact-verse tier at conf 0.90 on a
                            # chapter-level address. That is defect 2 of the
                            # H1670 report reappearing one level down: the fix
                            # separated the TIERS but still chose the tier once
                            # per sense. Level travels with the row now.
                            matched_passages.append((kw, level))
                            break
                if matched_i is not None:
                    break
            method = conf = None
            si = None
            samples = passages[: args.kwic_per]
            sample_levels = []          # H1691: per-row locus level, when known
            if matched_i is not None:
                si = matched_i
                # the sense-level tier is the STRONGEST level it achieved, so the
                # LOG counters keep meaning "this sense is grounded at a verse";
                # individual rows are stamped from their own level below.
                if any(lv == "verse" for _kw, lv in matched_passages):
                    matched_level = "verse"
                if matched_level == "verse":
                    method, conf = "locus", CONF["locus"]
                else:
                    method, conf = "locus-chapter", CONF["locus_chapter"]
                n_locus_hits += 1
                if matched_passages:
                    chosen = matched_passages[: args.kwic_per]
                    samples = [kw for kw, _lv in chosen]
                    sample_levels = [lv for _kw, lv in chosen]
            else:
                # (ii) MBh via the csl-atlas f8 vulgate crosswalk. DCS Mahābhārata
                # is the BORI critical edition, so a DCS (parvan, adhyāya) matches
                # a sense's <ls>-resolved vulgate adhyāya at ±1 (the vulgate↔critical
                # drift) — an adhyāya-level CORROBORATION, never exact identity.
                mbh_hits = {}   # sense_i -> (min_delta, [matching passages])
                for kw in passages:
                    if not (kw["source_text"] or "").startswith("Mahābhārata"):
                        continue
                    # (parvan, adhyāya) — abstain on 'MBh, 6, BhaGī n', whose
                    # digits would otherwise read as parvan 6 adhyāya n (H1670).
                    a_mbh = numeric_address(kw["ref"], None)
                    if a_mbh is None:
                        continue
                    pn = a_mbh[0]
                    if len(pn) < 2:
                        continue
                    for pi, madh in enumerate(sense_mbh_adh):
                        for (p_v, a_v) in madh:
                            if p_v == pn[0] and abs(a_v - pn[1]) <= 1:
                                d = abs(a_v - pn[1])
                                cur = mbh_hits.get(pi)
                                if cur is None or d < cur[0]:
                                    mbh_hits[pi] = (d, [kw])
                                elif d == cur[0]:
                                    cur[1].append(kw)
                if mbh_hits:
                    si = min(mbh_hits, key=lambda k: mbh_hits[k][0])
                    d, hitpass = mbh_hits[si]
                    method = "locus-mbh"
                    conf = CONF["locus_mbh_exact"] if d == 0 else CONF["locus_mbh_adj"]
                    samples = hitpass[: args.kwic_per]
                    n_locus_hits += 1
                else:
                    # (iii) gloss-overlap (proper-noun / binomial / digit tokens)
                    bi, strength, shared = overlap_assign(meanings.get(lemma_id, ""), sense_tokens)
                    if bi is not None:
                        si = bi
                        method = "overlap"
                        conf = CONF["overlap_strong"] if strength == 2 else CONF["overlap_weak"]
            if si is None:
                unassigned.append((lemma_iast, lemma_id, ev, n_txt))
                continue
            n_dcs_assigned += 1
            method_counts[method] += 1
            s = senses[si]
            sense_view[si]["dcs"].append({
                "lemma": lemma_iast, "conf": conf, "method": method,
                "tok": ev, "texts": n_txt, "kwic": samples,
            })
            for ri, kw in enumerate(samples):
                # H1691 — a row is stamped from ITS OWN address level, not from
                # the tier the sense as a whole reached. Only the locus tier
                # carries per-row levels; every other method is uniform.
                r_method, r_conf = method, conf
                if ri < len(sample_levels) and method in ("locus", "locus-chapter"):
                    if sample_levels[ri] == "verse":
                        r_method, r_conf = "locus", CONF["locus"]
                    else:
                        r_method, r_conf = "locus-chapter", CONF["locus_chapter"]
                row = {
                    "slp1": slp1, "hom": hom, "sense_id": s.sense_id, "lemma": lemma_iast,
                    "locus": kw["locus"], "cite": kw["cite"], "conf": r_conf,
                    "method": r_method, "rights": "public", "source": "DCS",
                    "gloss": (meanings.get(lemma_id, "") or "")[:80], "sent": kw["sent"],
                }
                conc_rows.append(row)
                if r_conf < tau:
                    review_rows.append({**row, "reason": "confidence<tau"})

        # residue -> review queue (never dropped, A5)
        for (lemma_iast, lemma_id, ev, n_txt) in unassigned:
            review_rows.append({
                "slp1": slp1, "hom": hom, "sense_id": "?", "lemma": lemma_iast,
                "locus": "lemma:%d" % lemma_id, "cite": "", "conf": 0.0,
                "method": "unassigned", "rights": "public", "source": "DCS",
                "gloss": (meanings.get(lemma_id, "") or "")[:80], "sent": "",
                "reason": "no locus/overlap candidate — residue for LLM/human pass",
            })

        # coverage rows
        for si, s in enumerate(senses):
            coverage_rows.append({
                "slp1": slp1, "hom": hom, "sense_id": s.sense_id,
                "n_ls": len(sense_view[si]["ls"]),
                "n_ls_resolved": sum(1 for x in sense_view[si]["ls"] if x["resolved"]),
                "n_dcs_assigned": len(sense_view[si]["dcs"]),
                "variant_of": variant_of or "",
                "gloss": s.gloss_clean()[:120],
            })

        # At scale the viewer payload (every <ls> item of every sense) is the
        # dominant memory cost and is only ever consumed by --viewer / the
        # nāgadanta worked example, so keep it only when it is wanted.
        if args.viewer or slp1 == "nAgadanta":
            viewer[slp1] = {
                "slp1": slp1, "hom": hom, "variant_of": variant_of or "",
                "senses": sense_view, "n_unassigned": len(unassigned),
            }

    # ---- write datasets -------------------------------------------------------
    OUT_DATA = out_data          # local rebind; --out-dir defaults to the global
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    conc_cols = ["slp1", "hom", "sense_id", "lemma", "locus", "cite", "conf", "method", "rights", "source", "gloss", "sent"]
    ds = OUT_DATA / "sense_corpus_concordance.tsv"
    with open(ds, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(conc_cols) + "\n")
        for r in conc_rows:
            f.write("\t".join(str(r[c]).replace("\t", " ").replace("\n", " ") for c in conc_cols) + "\n")

    cov = OUT_DATA / "sense_corpus_coverage.tsv"
    cov_cols = ["slp1", "hom", "sense_id", "n_ls", "n_ls_resolved", "n_dcs_assigned", "variant_of", "gloss"]
    with open(cov, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(cov_cols) + "\n")
        for r in coverage_rows:
            f.write("\t".join(str(r[c]).replace("\t", " ") for c in cov_cols) + "\n")

    rq = OUT_DATA / "sense_review_queue.tsv"
    rq_cols = ["slp1", "hom", "sense_id", "lemma", "locus", "cite", "conf", "method", "rights", "source", "gloss", "reason"]
    with open(rq, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(rq_cols) + "\n")
        for r in review_rows:
            f.write("\t".join(str(r.get(c, "")).replace("\t", " ").replace("\n", " ") for c in rq_cols) + "\n")

    # ---- viewer shards (Step 6) ----------------------------------------------
    n_public_rows = sum(1 for r in conc_rows if r["rights"] == "public")
    n_evidence_only = sum(1 for r in conc_rows if r["rights"] != "public")
    if args.viewer:
        OUT_WEB.mkdir(parents=True, exist_ok=True)
        shards = collections.defaultdict(dict)
        for slp1, entry in viewer.items():
            # filter each sense's rows to rights=public for the public viewer (A7)
            pub = {"slp1": slp1, "hom": entry["hom"], "variant_of": entry["variant_of"],
                   "n_unassigned": entry["n_unassigned"], "senses": []}
            for s in entry["senses"]:
                pub["senses"].append({
                    "sense_id": s["sense_id"], "gloss": s["gloss"],
                    "ls": [x for x in s["ls"] if x["rights"] == "public"],
                    "dcs": s["dcs"],
                })
            ch = (slp1 or "?")[0].lower()
            shards[ch if ch.isalpha() else "_"][slp1] = pub
        total = 0
        for sk, data in sorted(shards.items()):
            p = OUT_WEB / ("kwic_%s.js" % sk)
            payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            with io.open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write("window.SENSE_DATA = window.SENSE_DATA || {};\n")
                f.write('window.SENSE_DATA["%s"] = %s;\n' % (sk, payload))
            total += p.stat().st_size
        print("  viewer: %d shards, %.2f MB" % (len(shards), total / 1e6), file=sys.stderr)

    # ---- build report (Step 7) ------------------------------------------------
    rate = (100.0 * ls_resolved / ls_total) if ls_total else 0.0
    write_report(OUT_DATA / "SENSE_CONCORDANCE_BUILD_REPORT.md", dict(
        n_pilot=len(pilot_set), n_pilot_slp1=len(pilot_slp1),
        ls_total=ls_total, ls_resolved=ls_resolved, rate=rate,
        method_counts=method_counts, n_dcs_links=n_dcs_links,
        n_dcs_assigned=n_dcs_assigned, n_locus_hits=n_locus_hits,
        n_conc=len(conc_rows), n_review=len(review_rows), tau=tau,
        n_public=n_public_rows, n_evidence_only=n_evidence_only,
        mbh_ls_total=mbh_ls_total, mbh_ls_resolved=mbh_ls_resolved, mbh_ok=mbh.ok,
        viewer=args.viewer,
        locus_scan=args.locus_scan, no_ls_rows=args.no_ls_rows,
        pilot_path=str(Path(args.pilot) if args.pilot else PILOT),
        n_grounded_senses=len({(r["slp1"], r["hom"], r["sense_id"]) for r in conc_rows
                               if r["method"] in ("locus", "locus-mbh", "locus-chapter")}),
        n_grounded_senses_verse=len({(r["slp1"], r["hom"], r["sense_id"]) for r in conc_rows
                                     if r["method"] == "locus"}),
    ), viewer)

    print("LOG: ls_total=%d ls_resolved=%d rate=%.1f%% (A2 floor 60%%) tau=%.2f" % (ls_total, ls_resolved, rate, tau), file=sys.stderr)
    print("LOG: MBh <ls> resolved to vulgate: %d/%d (csl-atlas f8 crosswalk, ok=%s)" % (
        mbh_ls_resolved, mbh_ls_total, mbh.ok), file=sys.stderr)
    print("LOG: dcs_links=%d assigned=%d (locus=%d locus-chapter=%d locus-mbh=%d overlap=%d) review=%d" % (
        n_dcs_links, n_dcs_assigned, method_counts["locus"], method_counts["locus-chapter"],
        method_counts["locus-mbh"], method_counts["overlap"], len(review_rows)), file=sys.stderr)
    print("dataset: %s (%d rows)" % (ds, len(conc_rows)), file=sys.stderr)


def write_report(path, m, viewer):
    # nAgadanta worked example (A3)
    ex = viewer.get("nAgadanta")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("# sense-corpus-concordance — build report (H1455 wave-1)\n\n")
        f.write("_Created: 22-07-2026 · Last updated: 22-07-2026_\n\n")
        f.write("Built by [scripts/build_sense_corpus_concordance.py]"
                "(https://github.com/gasyoun/kosha/blob/main/scripts/build_sense_corpus_concordance.py) "
                "(H1455, Opus 4.8 `claude-opus-4-8`), consuming the H1456 PWG per-sense `<ls>` export.\n\n")
        f.write("## Run configuration (H1670)\n\n")
        f.write("| knob | value |\n|---|---|\n")
        f.write("| frame | `%s` (%d groups) |\n" % (m.get("pilot_path", ""), m["n_pilot"]))
        scan_gloss = ("every DCS passage at an address the frame cites"
                      if m.get("locus_scan") == "full"
                      else "the viewer sample per DCS lemma only (wave-1 default)")
        f.write("| `--locus-scan` | `%s` — %s |\n"
                % (m.get("locus_scan", "kwic"), scan_gloss))
        f.write("| `method=ls` rows in the bulk TSV | %s |\n"
                % ("omitted (`--no-ls-rows`); counts below are unaffected"
                   if m.get("no_ls_rows") else "included"))
        f.write("| PWG leaf senses grounded — exact verse only (`locus`) | **%d** |\n"
                % m.get("n_grounded_senses_verse", 0))
        f.write("| PWG leaf senses grounded — incl. adhyāya/hymn corroboration | **%d** |\n\n"
                % m.get("n_grounded_senses", 0))
        f.write("## A2 — `<ls>`-locus-resolution rate (THE wave-1 acceptance metric)\n\n")
        f.write("| metric | value |\n|---|---|\n")
        f.write("| pilot (slp1,hom) groups | %d |\n" % m["n_pilot"])
        f.write("| `<ls>` citations on pilot leaf senses | %d |\n" % m["ls_total"])
        f.write("| resolved to a bibliographic source (pwgbib) | %d |\n" % m["ls_resolved"])
        f.write("| **resolution rate** | **%.1f%%** (floor 60%%) |\n\n" % m["rate"])
        f.write("Resolution reuses the canonical `RussianTranslation/src/pwg_sources.py` "
                "(pwgbib.txt) — the abbrev table is consumed, never re-derived.\n\n")
        f.write("## MBh vulgate resolution (wave-1.5 — reused prior art)\n\n")
        f.write("PWG's continuous Böhtlingk–Roth Mahābhārata numbering IS resolvable to a Nīlakaṇṭha-vulgate "
                "address — the csl-atlas **f8 fitted-index crosswalk** (H610/H761, all 18 parvans, held-out MW "
                "55.2%% within ±3; [DEAD_ENDS §8b retracted](https://github.com/gasyoun/SanskritLexicography/blob/master/DEAD_ENDS.md)). "
                "This layer now **consumes** it (`mbh_vulgate.py` → `mbh_vulgate_concordance.csv`): **%d/%d** MBh "
                "`<ls>` loci on pilot senses resolved to a vulgate `parvan.adhyāya.śloka` (crosswalk present: %s). "
                "Example: `MBH. 12,3630` → **vulgate 12.98.19**.\n\n"
                % (m["mbh_ls_resolved"], m["mbh_ls_total"], m["mbh_ok"]))
        f.write("## Per-tier attestation rows\n\n")
        f.write("| tier | confidence | rows | meaning |\n|---|---|---|---|\n")
        f.write("| ls | 0.99 | %d | PWG's OWN `<ls>` under the sense — guaranteed-correct witness (MBh loci carry their resolved vulgate address) |\n" % m["method_counts"]["ls"])
        f.write("| locus | 0.90 | %d | DCS attestation verse-equal to a sense's `<ls>` (canonically-numbered Vedic texts) |\n" % m["method_counts"]["locus"])
        f.write("| locus-chapter | 0.70 | %d | verse-equal to a sense's `<ls>`, but the DCS address stops at the chapter/hymn (no `sent_counter`) — hymn-level corroboration, NOT exact-verse identity |\n" % m["method_counts"]["locus-chapter"])
        f.write("| locus-mbh | 0.65–0.80 | %d | DCS Mahābhārata attestation whose (parvan, adhyāya) matches a sense's `<ls>`-resolved vulgate adhyāya (±1, vulgate↔critical drift) |\n" % m["method_counts"]["locus-mbh"])
        f.write("| overlap | 0.50–0.70 | %d | shared proper-noun/binomial/digit gloss tokens |\n" % m["method_counts"]["overlap"])
        f.write("| **review queue** | <%.2f | %d | conf<τ + unassigned residue (kept, never dropped) |\n\n" % (m["tau"], m["n_review"]))
        f.write("DCS side: **%d** headword↔DCS-lemma links over the pilot; **%d** assigned to a sense "
                "(%d by verse-locus, %d by MBh-vulgate-adhyāya, %d by gloss-overlap); the rest parked to "
                "`sense_review_queue.tsv`.\n\n"
                % (m["n_dcs_links"], m["n_dcs_assigned"], m["method_counts"]["locus"],
                   m["method_counts"]["locus-mbh"], m["method_counts"]["overlap"]))
        f.write("**Honest note — corrected (wave-1.5).** An earlier draft of this report called PWG↔DCS "
                "Mahābhārata locus-matching *infeasible*. That over-claimed: PWG-continuous → **vulgate** is a "
                "SOLVED problem (csl-atlas f8), and it is now consumed. The residual is narrower and specific — "
                "DCS's Mahābhārata is the **BORI critical edition**, whose adhyāya/śloka numbering drifts ~±1 "
                "adhyāya from the vulgate — so a DCS match through the crosswalk is an adhyāya-level "
                "**corroboration** (`locus-mbh`, conf ≤ 0.80), not exact-verse identity. Texts DCS lacks entirely "
                "(Pañcatantra, Kathāsaritsāgara) still cannot be DCS-matched. The `ls` tier (PWG's own `<ls>`, "
                "now carrying resolved vulgate addresses) remains the load-bearing witness.\n\n")
        f.write("## Rights (A7)\n\n")
        f.write("Every row carries `rights ∈ {public, evidence-only}`; the public viewer filters to `public`. "
                "PWG `<ls>` sources are pre-1900 editions (public); DCS is CC BY 4.0 (public). "
                "**%d public rows, %d evidence-only** — no modern-copyright gloss (Kochergina/Smirnov) is "
                "consumed in wave-1, so 0 evidence-only rows arise; the classifier is wired for future modern glosses.\n\n"
                % (m["n_public"], m["n_evidence_only"]))
        f.write("## A3 — `nāgadanta` worked example (the translator-split, resolved)\n\n")
        if ex:
            f.write("PWG keeps one homonym; the sense-sharded layer restores the per-sense loci that the "
                    "thin bilingual glossaries dropped:\n\n")
            for s in ex["senses"]:
                lsrc = ", ".join("%s%s" % (x["abbrev"], (" " + x["locus"]) if x["locus"] else "")
                                 for x in s["ls"]) or "—"
                dcs = ", ".join("%s (%s)" % (d["lemma"], d["method"]) for d in s["dcs"]) or "—"
                f.write("- **sense %s** — %s\n  - `<ls>`: %s\n  - DCS: %s\n"
                        % (s["sense_id"], (s["gloss"][:70] or ""), lsrc, dcs))
            f.write("\nSense **1a** (Elephantenzahn / tusk) carries its **MBH** locus; sense **1b** (Pflock / "
                    "peg) carries its **PAÑCAT** loci — the exact split the "
                    "[नागदन्त thread](https://groups.google.com/g/nagari/c/NOWqiBQl1Xc/m/_R8O4-39CAAJ) "
                    "argued about. `nāgadantaka` `1b` (HIT 27,12) is recorded `variant_of nāgadanta`, "
                    "corroborating the peg sense (A4).\n\n")
        else:
            f.write("_(nāgadanta not in this pilot slice — force it via select_sense_pilot.py.)_\n\n")
        f.write("## Determinism (A8)\n\n")
        f.write("Steps 1–3 + 5 are deterministic (byte-identical on re-run); only the optional LLM residue "
                "tier (`--run-llm`, `wf/sense_adjudicate.js`) may vary and is bounded + logged. This run "
                "did **not** dispatch the LLM tier — residue is parked to the review queue (marked default, "
                "autonomy contract).\n\n")
        f.write("_Dr. Mārcis Gasūns_\n")


if __name__ == "__main__":
    main()
