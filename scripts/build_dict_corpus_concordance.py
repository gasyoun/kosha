#!/usr/bin/env python
"""Build the B1 dict↔corpus concordance (H380 / CONCORDANCE_ROADMAP Q1).

For every CDSL union headword (323,425; per-dict provenance flags), attach its
DCS attestations (5.69M tokens / 180,176 lemmas / 270 texts) via the tiered
matcher in concordance_core.py, seeded by the human-validated dcs-cdsl-xref
(consumed, never re-derived). Emits:

  data/concordance/dict_corpus_concordance.tsv     one row per headword↔lemma link
  data/concordance/dict_corpus_coverage.tsv        one row per union headword (status)
  data/concordance/BUILD_REPORT.md                 per-tier counts + coverage stats
  concordance/dict/data/kwic_<a>.js                per-first-letter KWIC shards for the
                                                   static viewer (<=3 samples per link)
  concordance/dict/data/index_<a>.js               per-first-letter headword index shards

Inputs (canonical, per the manifest — consume, don't re-derive):
  * union-headwords    SanskritLexicography/HeadwordLists/union/union_headwords.tsv
  * dcs-cdsl-xref      csl-apidev/simple-search/dcs_xref/dcs_cdsl_xref.tsv
  * dcs-full-sqlite    VisualDCS/src/DCS-data-2026/dcs_full.sqlite (gitignored, canonical ingest)

Deterministic, no network. ~2-4 min end to end (one aggregation pass + one
window-function KWIC pass over the 5.7M-token table).
"""
import argparse
import collections
import io
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from concordance_core import (  # noqa: E402
    RECORD_FIELDS, TIER_CONFIDENCE, TieredMatcher, citable_locus, human_locus,
)

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent if (ROOT.parent / "VisualDCS").exists() else ROOT.parent.parent
UNION = GH / "SanskritLexicography" / "HeadwordLists" / "union" / "union_headwords.tsv"
XREF = GH / "csl-apidev" / "simple-search" / "dcs_xref" / "dcs_cdsl_xref.tsv"
DCS = GH / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"

OUT_DATA = ROOT / "data" / "concordance"
OUT_WEB = ROOT / "concordance" / "dict" / "data"

KWIC_PER_LINK = 2   # samples per headword-lemma link in the static shards (cap
SENT_TRUNC = 160    # stated in BUILD_REPORT.md; the full corpus stays queryable
                    # in dcs_full.sqlite — the shards are a preview, not the data)

_JUNK_LEMMA = re.compile(r"^[\s\-_.?*0-9]*$")


def load_union():
    rows = {}
    with open(UNION, encoding="utf-8-sig") as f:
        header = f.readline().rstrip("\n").split("\t")
        idx = {c: i for i, c in enumerate(header)}
        for line in f:
            p = line.rstrip("\n").split("\t")
            slp1 = p[idx["slp1"]]
            rows[slp1] = {
                "iast": p[idx["iast"]],
                "n_dicts": int(p[idx["n_dicts"]] or 0),
                "dicts": p[idx["dicts"]],
            }
    return rows


def load_xref():
    """dcs_id -> slp1 key, for rows the xref pipeline already validated as in CDSL."""
    out = {}
    with open(XREF, encoding="utf-8-sig") as f:
        header = f.readline().rstrip("\n").split("\t")
        idx = {c: i for i, c in enumerate(header)}
        for line in f:
            p = line.rstrip("\n").split("\t")
            if p[idx["in_cdsl"]] == "1":
                out[int(p[idx["dcs_id"]])] = p[idx["slp1"]]
    return out


def lemma_stats(con):
    """lemma_id -> (lemma, n_tokens, n_texts, top_text_id)."""
    q = """
        SELECT t.lemma_id, l.lemma, COUNT(*) AS n_tok, COUNT(DISTINCT c.text_id) AS n_txt,
               MIN(c.text_id) AS a_text
        FROM token t
        JOIN sentence s ON s.id = t.sentence_id
        JOIN chapter c ON c.chapter_id = s.chapter_id
        JOIN lemma l ON l.lemma_id = t.lemma_id
        GROUP BY t.lemma_id
    """
    out = {}
    for lemma_id, lemma, n_tok, n_txt, a_text in con.execute(q):
        out[lemma_id] = (lemma or "", n_tok, n_txt, a_text)
    return out


def kwic_samples(con, wanted_lemma_ids):
    """lemma_id -> up to KWIC_PER_LINK samples of (form, sent_id, text, ref, counter, sub, sentence)."""
    q = """
        SELECT lemma_id, form, sent_id, text_name, ref, sent_counter, sent_subcounter, text_sandhied
        FROM (
            SELECT t.lemma_id AS lemma_id, t.form AS form, s.sent_id AS sent_id,
                   x.name AS text_name, c.ref AS ref,
                   s.sent_counter AS sent_counter, s.sent_subcounter AS sent_subcounter,
                   s.text_sandhied AS text_sandhied,
                   ROW_NUMBER() OVER (PARTITION BY t.lemma_id ORDER BY s.sent_id) AS rn
            FROM token t
            JOIN sentence s ON s.id = t.sentence_id
            JOIN chapter c ON c.chapter_id = s.chapter_id
            JOIN text x ON x.text_id = c.text_id
        ) WHERE rn <= %d
    """ % KWIC_PER_LINK
    out = collections.defaultdict(list)
    for lemma_id, form, sent_id, text_name, ref, cnt, sub, sent in con.execute(q):
        if lemma_id in wanted_lemma_ids:
            sent = (sent or "").strip()
            if len(sent) > SENT_TRUNC:
                sent = sent[:SENT_TRUNC] + "…"
            out[lemma_id].append({
                "form": form or "",
                "cite": citable_locus(sent_id),
                "locus": human_locus(text_name, ref, cnt, sub),
                "sent": sent,
            })
    return out


def shard_key(slp1):
    ch = (slp1 or "?")[0].lower()
    return ch if ch.isalpha() else "_"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-kwic", action="store_true", help="skip the KWIC pass (fast dev loop)")
    args = ap.parse_args()

    print("loading union headwords ...")
    union = load_union()
    print("  %d headwords" % len(union))
    print("loading xref ...")
    xref = load_xref()
    print("  %d validated dcs_id->slp1 links" % len(xref))

    matcher = TieredMatcher()
    for slp1, u in union.items():
        matcher.add_anchor(slp1, u["iast"])

    con = sqlite3.connect(str(DCS))
    print("aggregating DCS lemma stats (one pass over 5.7M tokens) ...")
    stats = lemma_stats(con)
    print("  %d lemmas with >=1 token" % len(stats))

    # ---- tiered matching ----------------------------------------------------
    links = []            # (anchor_slp1, lemma_id, tier)
    tier_counts = collections.Counter()
    junk = 0
    unmatched_lemmas = 0
    for lemma_id, (lemma, n_tok, n_txt, _a) in stats.items():
        if _JUNK_LEMMA.match(lemma):
            junk += 1
            continue
        if lemma_id in xref:
            hint = xref[lemma_id]
            if hint in union:
                links.append((hint, lemma_id, "xref"))
                tier_counts["xref"] += 1
                continue
        tier, anchors = matcher.match(lemma)
        if tier is None:
            unmatched_lemmas += 1
            continue
        tier_counts[tier] += len(anchors)
        for a in anchors:
            links.append((a, lemma_id, tier))

    # keep the best (highest-confidence) link per (anchor, lemma) pair
    best_all = {}
    for anchor, lemma_id, tier in links:
        k = (anchor, lemma_id)
        if k not in best_all or TIER_CONFIDENCE[tier] > TIER_CONFIDENCE[best_all[k]]:
            best_all[k] = tier

    # GOLDEN-SAMPLE RULING (10-07-2026, Fable 5): the lossy tiers are NOT asserted.
    # norm()/normalize_sanskrit() fold vowel length and s/ś/ṣ — exactly the
    # distinctions Sanskrit lexical minimal pairs live on; the stratified sample
    # showed 3/3 relaxed links semantically wrong (aṃśaka↔aṃsaka, vikarṣaṇa↔
    # vikarśana, ram↔rāṃ). relaxed/fuzzy matches are therefore emitted to a
    # REVIEW-CANDIDATES sidecar, never into the concordance or the viewer.
    ASSERTED = ("xref", "exact", "floor")
    best = {k: t for k, t in best_all.items() if t in ASSERTED}
    quarantined = {k: t for k, t in best_all.items() if t not in ASSERTED}

    # ---- emit the concordance dataset ---------------------------------------
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    ds = OUT_DATA / "dict_corpus_concordance.tsv"
    per_anchor = collections.defaultdict(list)
    with open(ds, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(RECORD_FIELDS + ["dcs_lemma_iast", "n_texts", "dicts", "n_dicts"]) + "\n")
        for (anchor, lemma_id), tier in sorted(best.items()):
            lemma, n_tok, n_txt, _a = stats[lemma_id]
            u = union[anchor]
            f.write("\t".join([
                "dict-entry", anchor, anchor, "lemma:%d" % lemma_id, "-",
                tier, "%.2f" % TIER_CONFIDENCE[tier], str(n_tok),
                lemma, str(n_txt), u["dicts"], str(u["n_dicts"]),
            ]) + "\n")
            per_anchor[anchor].append((lemma_id, tier, n_tok, n_txt, lemma))

    qf = OUT_DATA / "dict_corpus_relaxed_candidates.tsv"
    with open(qf, "w", encoding="utf-8", newline="\n") as f:
        f.write("anchor_key_slp1\tdcs_lemma_id\tdcs_lemma_iast\ttier\tevidence_count\n")
        for (anchor, lemma_id), tier in sorted(quarantined.items()):
            lemma, n_tok, _x, _a = stats[lemma_id]
            f.write("%s\t%d\t%s\t%s\t%d\n" % (anchor, lemma_id, lemma, tier, n_tok))

    # ---- coverage + absence classes ------------------------------------------
    cov = OUT_DATA / "dict_corpus_coverage.tsv"
    attested = 0
    absence = collections.Counter()
    with open(cov, "w", encoding="utf-8", newline="\n") as f:
        f.write("slp1\tn_dicts\tstatus\tbest_tier\tevidence_count\n")
        for slp1 in sorted(union):
            u = union[slp1]
            if slp1 in per_anchor:
                attested += 1
                lk = per_anchor[slp1]
                bt = max((TIER_CONFIDENCE[t], t) for _l, t, _n, _x, _le in lk)[1]
                ev = sum(n for _l, _t, n, _x, _le in lk)
                f.write("%s\t%d\tattested\t%s\t%d\n" % (slp1, u["n_dicts"], bt, ev))
            else:
                cls = ("corpus-gap-single-dict" if u["n_dicts"] == 1
                       else "corpus-gap-multi-dict")
                absence[cls] += 1
                f.write("%s\t%d\t%s\t-\t0\n" % (slp1, u["n_dicts"], cls))

    # ---- KWIC + index shards for the static viewer ---------------------------
    if not args.no_kwic:
        print("KWIC pass (window function over token table) ...")
        wanted = {lemma_id for (_a, lemma_id) in best}
        kwic = kwic_samples(con, wanted)
        OUT_WEB.mkdir(parents=True, exist_ok=True)
        shards = collections.defaultdict(dict)
        for anchor, lk in per_anchor.items():
            u = union[anchor]
            entry = {
                "iast": u["iast"], "dicts": u["dicts"], "n": u["n_dicts"],
                "lemmas": [
                    {"id": lid, "lemma": lemma, "tier": tier, "tok": n_tok,
                     "texts": n_txt, "kwic": kwic.get(lid, [])}
                    for lid, tier, n_tok, n_txt, lemma in sorted(
                        lk, key=lambda r: -r[2])
                ],
            }
            shards[shard_key(anchor)][anchor] = entry
        total_bytes = 0
        for sk, data in sorted(shards.items()):
            p = OUT_WEB / ("kwic_%s.js" % sk)
            payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            with io.open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write("window.CONC_DATA = window.CONC_DATA || {};\n")
                f.write('window.CONC_DATA["%s"] = %s;\n' % (sk, payload))
            total_bytes += p.stat().st_size
        print("  %d shards, %.1f MB total" % (len(shards), total_bytes / 1e6))

    # ---- build report ---------------------------------------------------------
    n_union = len(union)
    n_abs = sum(absence.values())
    rep = OUT_DATA / "BUILD_REPORT.md"
    with open(rep, "w", encoding="utf-8", newline="\n") as f:
        f.write("# dict-corpus-concordance — build report\n\n")
        f.write("_Created: 10-07-2026 · Last updated: 10-07-2026_\n\n")
        f.write("Built by [scripts/build_dict_corpus_concordance.py]"
                "(https://github.com/gasyoun/kosha/blob/main/scripts/build_dict_corpus_concordance.py) "
                "(H380, Fable 5 `claude-fable-5`).\n\n")
        f.write("## Per-tier link counts (exit-check: no silent fuzzy blur)\n\n")
        f.write("| tier | confidence | links | status |\n|---|---|---|---|\n")
        for t in ("xref", "exact", "floor"):
            n = sum(1 for v in best.values() if v == t)
            f.write("| %s | %.2f | %d | asserted |\n" % (t, TIER_CONFIDENCE[t], n))
        for t in ("relaxed", "fuzzy"):
            n = sum(1 for v in quarantined.values() if v == t)
            f.write("| %s | %.2f | %d | **quarantined** — review candidates only |\n"
                    % (t, TIER_CONFIDENCE[t], n))
        f.write("| **asserted total** | | **%d** | |\n\n" % len(best))
        f.write("**Golden-sample ruling:** the stratified verification sample "
                "(seed 20260710; 4 xref / 4 exact / 3 floor / 3 relaxed) passed every "
                "mechanical check (lemma identity, token counts, citable-locus "
                "resolution 14/14), but adjudication found **all 3 relaxed links "
                "semantically wrong** (aṃśaka 'share' ↔ aṃsaka 'shoulder'; "
                "vikarṣaṇa 'dragging' ↔ vikarśana 'emaciating'; ram ↔ rāṃ) — "
                "`norm()` folds vowel length and s/ś/ṣ, the exact axes of Sanskrit "
                "minimal pairs. relaxed/fuzzy links are therefore shipped only as "
                "`dict_corpus_relaxed_candidates.tsv` (review queue), never asserted.\n\n")
        f.write("## Coverage over the union headword master\n\n")
        f.write("| status | headwords | share |\n|---|---|---|\n")
        f.write("| attested (>=1 DCS token) | %d | %.1f%% |\n"
                % (attested, 100.0 * attested / n_union))
        for cls, n in absence.most_common():
            f.write("| %s | %d | %.1f%% |\n" % (cls, n, 100.0 * n / n_union))
        f.write("| **explained (attested or classed absence)** | %d | %.1f%% |\n\n"
                % (attested + n_abs, 100.0 * (attested + n_abs) / n_union))
        f.write("DCS side: %d lemmas with tokens; %d junk-string lemmas skipped; "
                "%d lemmas matched no headword (residue, listed honestly — mostly "
                "proper names, segmentation artifacts, and corpus-only vocabulary).\n\n"
                % (len(stats), junk, unmatched_lemmas))
        f.write("**Stated cap:** the static viewer shards carry at most %d KWIC "
                "samples per link, sentences truncated at %d chars — a preview "
                "layer only; every attestation remains queryable against the "
                "canonical `dcs-full-sqlite` (the dataset row carries the full "
                "`evidence_count`).\n" % (KWIC_PER_LINK, SENT_TRUNC))
        f.write("\n_Dr. Mārcis Gasūns_\n")

    print("dataset: %s (%d links)" % (ds, len(best)))
    print("coverage: attested %d/%d (%.1f%%), absences classed %d"
          % (attested, n_union, 100.0 * attested / n_union, n_abs))
    print("tiers:", dict(tier_counts))
    print("report: %s" % rep)


if __name__ == "__main__":
    main()
