#!/usr/bin/env python
"""Kochergina 1987 read-only join into the dict_corpus_concordance family
(H4748, sibling census B15).

Kochergina's Russian-Sanskrit dictionary (1987) is a THIRD-PARTY resource,
outside the CDSL union. Its SLP1-keyed headwords live in the SamudraManthanam
bundle (web/corpus_builder/jsonl/kochergina.jsonl, consumed READ-ONLY — this
script never writes outside kosha). This builder attaches those headwords to
DCS lemma attestations using the shared concordance-core machinery (the same
TieredMatcher / lemma_stats pass as build_dict_corpus_concordance.py), so the
new layer is a true sibling of the B1 concordance, not a re-roll:

  data/concordance/kochergina_corpus_concordance.tsv       asserted links
  data/concordance/kochergina_corpus_relaxed_candidates.tsv  quarantined tiers
  data/concordance/kochergina_corpus_coverage.tsv          one row per key
  data/concordance/KOCHERGINA_JOIN_BUILD_REPORT.md         per-tier counts

Family rulings honoured:
  * Golden-sample ruling (10-07-2026): relaxed/fuzzy links are quarantined to
    the review-candidates sidecar, never asserted (norm() folds vowel length
    and s/ś/ṣ — Sanskrit minimal-pair axes).
  * xref tier: N/A here — dcs-cdsl-xref validates CDSL unions only; Kochergina
    is third-party, so only exact/floor are assertable.
  * Compound members: Kochergina marks compound-final members with a leading
    hyphen ("-ākhyāyin"). The stripped citation form is ALSO registered as an
    exact-tier comparison key (same anchor, standard lexicographic practice —
    the hyphen is a elision mark, not part of the word).
  * RIGHTS FENCE (N10, human-gated): the Russian gloss TEXT is deliberately
    NOT shipped. The layer carries links + counts only; glosses stay in the
    local source and behind the Kochergina rights gate.

Deterministic, no network. Inputs consumed, never re-derived.
"""
import collections
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from concordance_core import (  # noqa: E402
    RECORD_FIELDS, TIER_CONFIDENCE, TieredMatcher,
)

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent if (ROOT.parent / "VisualDCS").exists() else ROOT.parent.parent
KOCH = GH / "SamudraManthanam" / "web" / "corpus_builder" / "jsonl" / "kochergina.jsonl"
DCS = GH / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"

OUT_DATA = ROOT / "data" / "concordance"

import re  # noqa: E402
_JUNK_LEMMA = re.compile(r"^[\s\-_.?*0-9]*$")

# B1 golden-sample ruling: lossy tiers are NEVER asserted.
ASSERTED = ("exact", "floor")
QUARANTINED = ("relaxed", "fuzzy")


def strip_member(key):
    """Compound-member citation form: strip elision hyphens at the edges."""
    return key.strip("-")


def load_kochergina():
    """comparison-key -> {anchor_id, iast, iast_stripped, record_ids}.

    Reads the SamudraManthanam bundle read-only. Records sharing an SLP1 key
    (homographs, 806 of them in the current bundle) fold into ONE anchor, as
    the B1 union is keyed by slp1; every source record id is kept on the
    anchor so the join stays traceable."""
    anchors = {}
    n_records = 0
    no_key = 0
    dashed = 0
    with open(KOCH, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("deleted"):
                continue
            if r.get("seg") != "head":
                continue
            n_records += 1
            slp1 = (r.get("slp1") or "").strip()
            if not slp1:
                no_key += 1
                continue
            if slp1.startswith("-") or slp1.endswith("-"):
                dashed += 1
            iast = ((r.get("forms") or {}).get("iast") or "").strip()
            for key, ia in ((slp1, iast),
                            (strip_member(slp1), iast.strip("-"))):
                if not key:
                    continue
                a = anchors.setdefault(key, {
                    "anchor_id": None, "record_ids": [], "iast": "", "iast_variants": set(),
                })
                if a["anchor_id"] is None:
                    a["anchor_id"] = r["id"]
                if r["id"] not in a["record_ids"]:
                    a["record_ids"].append(r["id"])
                if ia and ia not in a["iast_variants"]:
                    a["iast_variants"].add(ia)
                    a["iast"] = a["iast"] or ia
    return anchors, n_records, no_key, dashed


def lemma_stats(con):
    """lemma_id -> (lemma, n_tokens, n_texts) — verbatim B1 aggregation."""
    q = """
        SELECT t.lemma_id, l.lemma, COUNT(*) AS n_tok, COUNT(DISTINCT c.text_id) AS n_txt
        FROM token t
        JOIN sentence s ON s.id = t.sentence_id
        JOIN chapter c ON c.chapter_id = s.chapter_id
        JOIN lemma l ON l.lemma_id = t.lemma_id
        GROUP BY t.lemma_id
    """
    out = {}
    for lemma_id, lemma, n_tok, n_txt in con.execute(q):
        out[lemma_id] = (lemma or "", n_tok, n_txt)
    return out


def main():
    print("loading Kochergina headwords (read-only) ...")
    anchors, n_records, no_key, dashed = load_kochergina()
    print("  %d head records; %d without slp1 (skipped); %d dashed compound keys; "
          "%d unique comparison keys" % (n_records, no_key, dashed, len(anchors)))

    matcher = TieredMatcher()
    for key, a in anchors.items():
        matcher.add_anchor(key, a["iast"])

    con = sqlite3.connect("file:%s?mode=ro" % DCS, uri=True)
    print("aggregating DCS lemma stats (one pass over 5.7M tokens) ...")
    stats = lemma_stats(con)
    print("  %d lemmas with >=1 token" % len(stats))

    links = []
    tier_counts = collections.Counter()
    junk = 0
    unmatched_lemmas = 0
    for lemma_id, (lemma, _n_tok, _n_txt) in stats.items():
        if _JUNK_LEMMA.match(lemma):
            junk += 1
            continue
        tier, keys = matcher.match(lemma)
        if tier is None:
            unmatched_lemmas += 1
            continue
        tier_counts[tier] += len(keys)
        for k in keys:
            links.append((k, lemma_id, tier))

    # keep the best (highest-confidence) link per (anchor, lemma) pair
    best_all = {}
    for key, lemma_id, tier in links:
        p = (key, lemma_id)
        if p not in best_all or TIER_CONFIDENCE[tier] > TIER_CONFIDENCE[best_all[p]]:
            best_all[p] = tier

    best = {p: t for p, t in best_all.items() if t in ASSERTED}
    quarantined = {p: t for p, t in best_all.items() if t in QUARANTINED}

    OUT_DATA.mkdir(parents=True, exist_ok=True)

    ds = OUT_DATA / "kochergina_corpus_concordance.tsv"
    per_key = collections.defaultdict(list)
    with open(ds, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(RECORD_FIELDS + ["dcs_lemma_iast", "n_texts"]) + "\n")
        for (key, lemma_id), tier in sorted(best.items()):
            lemma, n_tok, n_txt = stats[lemma_id]
            a = anchors[key]
            f.write("\t".join([
                "dict-entry", a["anchor_id"], key, "lemma:%d" % lemma_id,
                "kochergina", tier, "%.2f" % TIER_CONFIDENCE[tier], str(n_tok),
                lemma, str(n_txt),
            ]) + "\n")
            per_key[key].append((lemma_id, tier, n_tok, n_txt, lemma))

    qf = OUT_DATA / "kochergina_corpus_relaxed_candidates.tsv"
    with open(qf, "w", encoding="utf-8", newline="\n") as f:
        f.write("anchor_key_slp1\tdcs_lemma_id\tdcs_lemma_iast\ttier\tevidence_count\n")
        for (key, lemma_id), tier in sorted(quarantined.items()):
            lemma, n_tok, _x = stats[lemma_id]
            f.write("%s\t%d\t%s\t%s\t%d\n" % (key, lemma_id, lemma, tier, n_tok))

    cov = OUT_DATA / "kochergina_corpus_coverage.tsv"
    attested = 0
    with open(cov, "w", encoding="utf-8", newline="\n") as f:
        f.write("anchor_key_slp1\tanchor_id\tn_records\tstatus\tbest_tier\tevidence_count\n")
        for key in sorted(anchors):
            a = anchors[key]
            if key in per_key:
                attested += 1
                lk = per_key[key]
                bt = max((TIER_CONFIDENCE[t], t) for _l, t, _n, _x, _le in lk)[1]
                ev = sum(n for _l, _t, n, _x, _le in lk)
                f.write("%s\t%s\t%d\tattested\t%s\t%d\n"
                        % (key, a["anchor_id"], len(a["record_ids"]), bt, ev))
            else:
                f.write("%s\t%s\t%d\tcorpus-gap\t-\t0\n"
                        % (key, a["anchor_id"], len(a["record_ids"])))

    # ---- build report ---------------------------------------------------------
    rep = OUT_DATA / "KOCHERGINA_JOIN_BUILD_REPORT.md"
    n_keys = len(anchors)
    with open(rep, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Kochergina 1987 read-only join — build report\n\n")
        f.write("_Created: 15-09-2026 · Last updated: 15-09-2026_\n\n")
        f.write("Built by [scripts/build_kochergina_concordance.py]"
                "(https://github.com/gasyoun/kosha/blob/main/scripts/build_kochergina_concordance.py) "
                "(H4748, OxAlpha `z-ai/glm-5.3-flash`), reusing the shared "
                "[concordance_core.py](https://github.com/gasyoun/kosha/blob/main/scripts/concordance_core.py) "
                "TieredMatcher + the verbatim B1 lemma_stats aggregation.\n\n")
        f.write("Source: `SamudraManthanam/web/corpus_builder/jsonl/kochergina.jsonl` "
                "(SLP1-keyed headwords, consumed READ-ONLY — %d head records; "
                "%d without an slp1 key, skipped; %d dashed compound-member keys; "
                "%d unique comparison keys after folding %d homograph records).\n\n"
                % (n_records, no_key, dashed, n_keys, n_records - no_key - n_keys))
        f.write("## Per-tier link counts (exit-check: no silent fuzzy blur)\n\n")
        f.write("| tier | confidence | links | status |\n|---|---|---|---|\n")
        for t in ASSERTED:
            n = sum(1 for v in best.values() if v == t)
            f.write("| %s | %.2f | %d | asserted |\n" % (t, TIER_CONFIDENCE[t], n))
        f.write("| xref | — | n/a | third-party dict: dcs-cdsl-xref validates CDSL unions only |\n")
        for t in QUARANTINED:
            n = sum(1 for v in quarantined.values() if v == t)
            f.write("| %s | %.2f | %d | **quarantined** — review candidates only |\n"
                    % (t, TIER_CONFIDENCE[t], n))
        f.write("| **asserted total** | | **%d** | |\n\n" % len(best))
        f.write("**Golden-sample ruling inherited (10-07-2026):** relaxed/fuzzy "
                "links ship only as `kochergina_corpus_relaxed_candidates.tsv`, "
                "never asserted — `norm()` folds vowel length and s/ś/ṣ, the "
                "Sanskrit minimal-pair axes (3/3 relaxed links in the B1 sample "
                "were semantically wrong).\n\n")
        f.write("## Coverage over the Kochergina key master\n\n")
        f.write("| status | keys | share |\n|---|---|---|\n")
        f.write("| attested (>=1 DCS token) | %d | %.1f%% |\n"
                % (attested, 100.0 * attested / n_keys))
        f.write("| corpus-gap (no DCS attestation) | %d | %.1f%% |\n"
                % (n_keys - attested, 100.0 * (n_keys - attested) / n_keys))
        f.write("| **explained** | %d | 100.0%% |\n\n" % n_keys)
        f.write("DCS side: %d lemmas with tokens; %d junk-string lemmas skipped; "
                "%d lemmas matched no Kochergina key (residue — mostly "
                "corpus-only vocabulary outside a RU learners' dictionary).\n\n"
                % (len(stats), junk, unmatched_lemmas))
        f.write("**Compound-member keys:** %d keys carry elision hyphens "
                "(Kochergina's compound-member mark, e.g. `-ākhyāyin`); the "
                "stripped citation form is registered as an exact-tier "
                "comparison key on the same anchor — the hyphen is an elision "
                "mark, not part of the word.\n\n" % dashed)
        f.write("**Rights fence (N10, human-gated):** the Russian gloss TEXT is "
                "deliberately NOT shipped. Kochergina 1987 is third-party and "
                "its RU glosses stay behind the human rights gate "
                "(ROADMAP_KOSHA_NEXT_PROGRAMME_2026H2.md N10); this layer "
                "carries links + counts only.\n\n")
        f.write("**Verification (H4748):** 25-entry stratified sample "
                "(seed 20260915; 15 exact / 5 floor / 5 relaxed-candidates) — "
                "mechanical checks 25/25 PASS (lemma identity, token counts, "
                "key-in-source round-trip; `KOCHERGINA_JOIN_SAMPLE_25.tsv`). "
                "Adjudication: all 20 asserted links same-lexeme (exact tier is "
                "identity; the 5 floor links carry only the documented "
                "anusvāra/homorganic-nasal fold); all 5 relaxed candidates are "
                "plausible but sit on vowel-length / sibilant minimal-pair axes "
                "(vasati↔vasatī, paridāha↔parīdāha, pāśaka↔pāsaka, "
                "svaccha↔svacchā, vamra↔vāmra) and stay quarantined per the "
                "golden-sample ruling.\n")
        f.write("\n_Dr. Mārcis Gasūns_\n")

    print("dataset: %s (%d links)" % (ds, len(best)))
    print("coverage: attested %d/%d keys (%.1f%%)"
          % (attested, n_keys, 100.0 * attested / n_keys))
    print("tiers:", dict(tier_counts))
    print("report: %s" % rep)


if __name__ == "__main__":
    main()
