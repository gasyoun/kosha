#!/usr/bin/env python
"""kosha concordance core (H380 / CONCORDANCE_ROADMAP Q1) — shared by Q1–Q4.

One schema, four instantiations: every concordance in the program links a
lexicon/grammar ANCHOR to a corpus LOCUS with evidence. This module owns the
pieces all four quarters share, so Q2 (parallel-verse), Q3 (generated-vs-
attested) and Q4 (sūtra→form) import it instead of re-rolling:

  * RECORD_FIELDS — the canonical concordance record (CONCORDANCE_ROADMAP
    §"The core idea"): anchor_type · anchor_id · anchor_key_slp1 ·
    corpus_locus · corpus_text_id · match_method · confidence · evidence_count
  * the tiered matcher — exact SLP1 → form_key (length-preserving floor) →
    norm (relaxed) → normalize_sanskrit (fuzzy ASCII bucket), per-tier counts
    always surfaced, lossy tiers unique-match-only (never a silent blur)
  * corpus locus + citation helpers — a host-independent citable ID
    (`dcs:<sent_id>`) plus the human locus (text · chapter ref · sentence
    counter). RISKS R1/R5: the ID embeds only DCS's own stable sentence id,
    never a URL host; resolution instructions live in the dataset README.

Keys come from the canonical sanskrit-util package (sibling checkout, the
same path app/transliterate.py uses) — form_key()/norm()/normalize_sanskrit()
are CONSUMED, not re-implemented (SHARED_CODE.md discipline).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "sanskrit-util" / "py"))
from sanskrit_util import form_key, norm, normalize_sanskrit, to_slp1  # noqa: E402

RECORD_FIELDS = [
    "anchor_type",       # dict-entry | parallel-verse | inflection | panini-sutra
    "anchor_id",         # stable ID in the source resource (B1: SLP1 headword key)
    "anchor_key_slp1",   # the SLP1 comparison key
    "corpus_locus",      # human locus (B1 index rows: lemma-level -> 'lemma:<id>')
    "corpus_text_id",    # which DCS text (B1 index rows: n_texts spread instead)
    "match_method",      # xref | exact | floor | relaxed | fuzzy
    "confidence",        # tier-derived score
    "evidence_count",    # attestations backing the link
]

# Tier -> confidence. xref = the human-validated dcs-cdsl-xref pipeline;
# exact = byte-identical SLP1; floor = length-preserving form_key (anusvāra/
# homorganic-nasal fold + final-visarga strip — ā≠a is PRESERVED); relaxed =
# norm (accent/length-lossy); fuzzy = ASCII bucket. The two lossy tiers are
# only accepted when the bucket resolves to exactly ONE candidate.
TIER_CONFIDENCE = {
    "xref": 0.99,
    "exact": 0.95,
    "floor": 0.85,
    "relaxed": 0.60,
    "fuzzy": 0.40,
}


def citable_locus(sent_id):
    """Host-independent citable ID for a DCS sentence (RISKS R5: no URL host).

    `dcs:<sent_id>` — sent_id is DCS's own stable sentence identifier, carried
    verbatim in the CoNLL-U dump and every DCS release; resolvable offline
    against any copy of the corpus (VisualDCS dcs_full.sqlite `sentence.sent_id`)
    or online by DCS sentence lookup. Deliberately NOT a URL."""
    return "dcs:%s" % sent_id


def human_locus(text_name, chapter_ref, sent_counter, sent_subcounter=None):
    """Human-readable locus: 'Text, chapter-ref, sentence-counter[.sub]'."""
    loc = "%s, %s, %s" % (text_name, chapter_ref, sent_counter)
    if sent_subcounter not in (None, "", 0, "0"):
        loc += ".%s" % sent_subcounter
    return loc


class TieredMatcher:
    """Match corpus lemma strings (IAST) against an anchor inventory.

    Anchors are registered once (slp1 key + iast form); lemmas are then
    resolved tier by tier. Lossy tiers (relaxed / fuzzy) accept only
    single-candidate buckets. Every accept records its tier so per-tier
    counts can be reported (exit-check requirement: never a silent blur)."""

    def __init__(self):
        self.by_slp1 = {}
        self.by_floor = {}
        self.by_relaxed = {}
        self.by_fuzzy = {}

    def add_anchor(self, slp1_key, iast):
        self.by_slp1.setdefault(slp1_key, slp1_key)
        self.by_floor.setdefault(form_key(iast), []).append(slp1_key)
        self.by_relaxed.setdefault(norm(iast), []).append(slp1_key)
        self.by_fuzzy.setdefault(normalize_sanskrit(iast), []).append(slp1_key)

    def match(self, lemma_iast, slp1_hint=None):
        """-> (tier, [anchor slp1 keys]) or (None, []).

        slp1_hint: a pre-transcoded SLP1 form (e.g. from the xref) — checked
        as the 'exact' tier before transcoding lemma_iast ourselves."""
        s = slp1_hint if slp1_hint is not None else to_slp1(lemma_iast)
        if s in self.by_slp1:
            return "exact", [s]
        hits = self.by_floor.get(form_key(lemma_iast))
        if hits:
            return "floor", sorted(set(hits))
        hits = self.by_relaxed.get(norm(lemma_iast))
        if hits and len(set(hits)) == 1:
            return "relaxed", sorted(set(hits))
        hits = self.by_fuzzy.get(normalize_sanskrit(lemma_iast))
        if hits and len(set(hits)) == 1:
            return "fuzzy", sorted(set(hits))
        return None, []
