#!/usr/bin/env python
"""kosha concordance core (H380 / CONCORDANCE_ROADMAP Q1) — shared by Q1–Q4
and by Type-D grammar<->non-grammar concordances (H539 /
TYPED_LINK_ID_GRAMMAR.md).

One schema, instantiated for both corpus concordances (Type-B: Q1-Q4) and
grammar<->non-grammar links (Type-D): every record links an ANCHOR to a
TARGET LOCUS with evidence. This module owns the pieces every consumer
shares, so no Type-D builder re-rolls a matcher or an ID scheme:

  * RECORD_FIELDS — the canonical concordance record (CONCORDANCE_ROADMAP
    §"The core idea"): anchor_type · anchor_id · anchor_key_slp1 ·
    target_locus · source_dataset · match_method · confidence ·
    evidence_count. (Renamed from corpus_locus/corpus_text_id per
    TYPED_LINK_ID_GRAMMAR.md §1 — the target is no longer always a corpus;
    field positions and semantics are unchanged.)
  * TYPE_D_RECORD_FIELDS — RECORD_FIELDS extended with the Type-D
    discriminator (`link_type`) and provenance `date`; normalize_record()
    maps either shape into one shared view (spec §1's stated goal).
  * the tiered matcher — exact SLP1 → form_key (length-preserving floor) →
    norm (relaxed) → normalize_sanskrit (fuzzy ASCII bucket), per-tier counts
    always surfaced, lossy tiers unique-match-only (never a silent blur).
    Type-D adds two non-fuzzy tiers ABOVE exact in trust: id-link (a pure
    join on a shared host-stable id) and curated (the source concordance's
    own authoritative assertion) — see TIER_CONFIDENCE.
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
    "target_locus",      # human/host-independent locus (B1 index rows: lemma-level -> 'lemma:<id>')
    "source_dataset",    # which dataset asserts the link (B1 index rows: n_texts spread instead)
    "match_method",      # id-link | curated | xref | exact | floor | relaxed | fuzzy
    "confidence",        # tier-derived score
    "evidence_count",    # attestations backing the link
]

# TYPED_LINK_ID_GRAMMAR.md §1: the Type-D record is a renamed superset of
# RECORD_FIELDS — same anchor/target/evidence shape, plus a subtype
# discriminator (link_type) and a provenance date. Field order here follows
# the spec's §1 table, not a straight append.
TYPE_D_RECORD_FIELDS = [
    "anchor_type",
    "anchor_id",
    "anchor_key_slp1",
    "target_locus",
    "link_type",
    "source_dataset",
    "match_method",
    "confidence",
    "evidence_count",
    "date",
]

# TYPED_LINK_ID_GRAMMAR.md §1: the three Type-D link subtypes.
TYPE_D_LINK_TYPES = ("translation-witness", "commentary-citation", "thematic")

# Tier -> confidence. id-link/curated (Type-D, TYPED_LINK_ID_GRAMMAR.md §1)
# sit above exact in trust: id-link = a pure join on a shared host-stable id
# (no matching at all, e.g. id_gra); curated = the source concordance's own
# authoritative assertion. xref = the human-validated dcs-cdsl-xref pipeline;
# exact = byte-identical SLP1; floor = length-preserving form_key (anusvāra/
# homorganic-nasal fold + final-visarga strip — ā≠a is PRESERVED); relaxed =
# norm (accent/length-lossy); fuzzy = ASCII bucket. The two lossy tiers are
# only accepted when the bucket resolves to exactly ONE candidate — Type-D
# keeps this same unique-match-only quarantine rule.
TIER_CONFIDENCE = {
    "id-link": 0.99,
    "xref": 0.99,
    "curated": 0.97,
    "exact": 0.95,
    "floor": 0.85,
    "relaxed": 0.60,
    "fuzzy": 0.40,
}


def normalize_record(row):
    """Map a Type-B or Type-D record (dict keyed by field name) into one
    shared view: RECORD_FIELDS' keys plus link_type/date (None for Type-B
    rows, which predate the discriminator). TYPED_LINK_ID_GRAMMAR.md §1:
    'a shared reader can normalize a Type-B and a Type-D row into one view.'

    Accepts either the current field names (target_locus/source_dataset) or
    the pre-H539 names (corpus_locus/corpus_text_id) so callers holding an
    older in-memory row don't need to migrate it first."""
    target_locus = row.get("target_locus", row.get("corpus_locus"))
    source_dataset = row.get("source_dataset", row.get("corpus_text_id"))
    return {
        "anchor_type": row.get("anchor_type"),
        "anchor_id": row.get("anchor_id"),
        "anchor_key_slp1": row.get("anchor_key_slp1"),
        "target_locus": target_locus,
        "link_type": row.get("link_type"),
        "source_dataset": source_dataset,
        "match_method": row.get("match_method"),
        "confidence": row.get("confidence"),
        "evidence_count": row.get("evidence_count"),
        "date": row.get("date"),
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
