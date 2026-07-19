#!/usr/bin/env python
"""kosha reading-pack builder (H848 / P5 UI step 6b, CONCORDANCE_ROADMAP sibling).

Builds a "reading pack" for one DCS chapter: the sandhied passage sentence by
sentence, every word linked to its kosha /w/ dictionary card. A reading aid,
not a concordance — but it CONSUMES the concordance core (H380) rather than
re-rolling the dict<->corpus join:

  * scripts/concordance_core.py :: TieredMatcher / to_slp1 / card-safe loci
    (form_key floor tier, ā-preserving). We accept only the high-confidence
    exact + floor tiers as a /w/ link; relaxed/fuzzy/no-match render as a
    plain (un-linked) word, flagged — a wrong link in a reading aid is worse
    than no link, so the two lossy tiers are NOT used here.
  * app/word_page.py :: card_token() twin — the /w/<card_token>.html URL key.

Inputs (consumed, never re-derived):
  * DCS full sqlite  ../VisualDCS/src/DCS-data-2026/dcs_full.sqlite
    (the real 920 MB DB; ../VisualDCS/src/dcs_full.sqlite is a 0-byte decoy).
  * kosha.db lemmas.slp1/.iast  data/db/kosha.db  (the anchor inventory).

Outputs:
  * reading/data/<slug>.js      window.READING_DATA = {...}  (viewer payload)
  * reading/data/<slug>.json    the same object as a plain dataset
  * reading/BUILD_REPORT.md     per-tier resolution table + unresolved residue

Determinism: pure read of two sqlite DBs + a transcode; no network, no clock
beyond the --built date stamp (passed in, default today via argparse default).

Usage:
  python scripts/build_reading_pack.py --ref "MBh, 3, 50" --slug nala-1 \
      --title "Nala 1 — Nalopākhyāna (Mahābhārata 3.50)" --built 2026-07-13
"""
import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from concordance_core import TieredMatcher, to_slp1, citable_locus, human_locus  # noqa: E402

# card_token twin (app/word_page.py:49 / build_static_cache.py / ui cardToken.js)
def card_token(slp1: str) -> str:
    out = []
    for b in slp1.encode("utf-8"):
        if (97 <= b <= 122) or (48 <= b <= 57):
            out.append(chr(b))
        else:
            out.append("_%02x" % b)
    return "".join(out)


# sibling-repo locator (same shape as build_dict_corpus_concordance.py)
GH = ROOT.parent if (ROOT.parent / "VisualDCS").exists() else ROOT.parent.parent
DCS = GH / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"
# kosha.db is a gitignored local-only giant — absent from a fresh worktree; fall
# back to the primary clone's copy (GH/kosha) when this checkout doesn't carry it.
KOSHA_DB = ROOT / "data" / "db" / "kosha.db"
if not KOSHA_DB.exists():
    KOSHA_DB = GH / "kosha" / "data" / "db" / "kosha.db"

# tiers we accept as a real /w/ link (high-confidence, ā-preserving)
LINK_TIERS = ("exact", "floor")

MORPH_FEATS = [
    ("feat_case", ""), ("feat_number", ""), ("feat_gender", ""),
    ("feat_person", "p"), ("feat_tense", ""), ("feat_mood", ""),
    ("feat_voice", ""),
]


def morph_str(tokrow):
    parts = []
    for col, pfx in MORPH_FEATS:
        v = tokrow[col]
        if v:
            parts.append((pfx + str(v)) if pfx else str(v))
    return " ".join(parts)


def gloss_of(meanings, limit=90):
    if not meanings:
        return ""
    g = meanings.strip()
    return g if len(g) <= limit else g[: limit - 1].rstrip() + "…"


def build_matcher(kcon):
    """Seed a TieredMatcher with every kosha lemma (slp1 + iast)."""
    m = TieredMatcher()
    for slp1, iast in kcon.execute("SELECT slp1, iast FROM lemmas"):
        m.add_anchor(slp1, iast or slp1)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="MBh, 3, 50", help="DCS chapter ref")
    ap.add_argument("--slug", default="nala-1")
    ap.add_argument("--title", default="Nala 1 — Nalopākhyāna (Mahābhārata 3.50)")
    ap.add_argument("--text-id", type=int, default=154)
    ap.add_argument("--built", default="2026-07-13", help="YYYY-MM-DD build stamp")
    ap.add_argument("--gloss-lang", choices=["none", "ru"], default="none",
                    help="ru = inline the additive Sa->Ru gloss layer (W-RU-a/H1278) into "
                         "each token's gloss_ru; English gloss is untouched")
    args = ap.parse_args()

    if not DCS.exists():
        sys.exit(f"DCS DB not found at {DCS} (real DB is DCS-data-2026/, not the 0-byte src/ decoy)")
    if not KOSHA_DB.exists():
        sys.exit(f"kosha.db not found at {KOSHA_DB}")

    dcon = sqlite3.connect(str(DCS)); dcon.row_factory = sqlite3.Row
    kcon = sqlite3.connect(str(KOSHA_DB))
    d = dcon.cursor()

    row = d.execute(
        "SELECT chapter_id FROM chapter WHERE text_id=? AND ref=?",
        (args.text_id, args.ref)).fetchone()
    if not row:
        sys.exit(f"ref {args.ref!r} not present in text_id {args.text_id}")
    cid = row["chapter_id"]
    text_name = krow = dcon.execute(
        "SELECT name FROM text WHERE text_id=?", (args.text_id,)).fetchone()[0]

    matcher = build_matcher(kcon)

    sents = d.execute(
        "SELECT id, sent_id, sent_counter, sent_subcounter, text_sandhied "
        "FROM sentence WHERE chapter_id=? ORDER BY sent_counter, sent_subcounter, id",
        (cid,)).fetchall()

    tier_counts = {}
    out_sents = []
    n_tok = 0
    n_link = 0
    # cache lemma->(tier, key) and lemma meanings
    lemma_meta = {}
    unresolved = {}  # lemma_iast -> count
    for s in sents:
        toks = d.execute(
            "SELECT idx, form, lemma, lemma_id, upos, feat_case, feat_gender, "
            "feat_number, feat_person, feat_tense, feat_mood, feat_voice "
            "FROM token WHERE sentence_id=? ORDER BY idx", (s["id"],)).fetchall()
        otoks = []
        for t in toks:
            n_tok += 1
            lemma = t["lemma"]
            if lemma not in lemma_meta:
                tier, keys = matcher.match(lemma)
                key = keys[0] if keys else None
                # DCS lemma gloss
                mrow = dcon.execute(
                    "SELECT meanings FROM lemma WHERE lemma_id=?", (t["lemma_id"],)).fetchone()
                lemma_meta[lemma] = (tier, key, gloss_of(mrow["meanings"] if mrow else ""))
            tier, key, gloss = lemma_meta[lemma]
            linked = tier in LINK_TIERS and key is not None
            tier_counts[tier or "none"] = tier_counts.get(tier or "none", 0) + 1
            tok = {
                "form": t["form"],
                "lemma": lemma,
                "upos": t["upos"],
                "morph": morph_str(t),
                "gloss": gloss,
            }
            if linked:
                n_link += 1
                slp1 = key
                tok["slp1"] = slp1
                tok["href"] = "../w/%s.html" % card_token(slp1)
                tok["tier"] = tier
            else:
                tok["resolved"] = False
                if lemma:
                    unresolved[lemma] = unresolved.get(lemma, 0) + 1
            otoks.append(tok)
        out_sents.append({
            "n": s["sent_counter"],
            "sub": s["sent_subcounter"] or None,
            "locus": human_locus(text_name, args.ref, s["sent_counter"], s["sent_subcounter"]),
            "dcs": citable_locus(s["sent_id"]),
            "text": s["text_sandhied"],
            "tokens": otoks,
        })

    rate = round(100.0 * n_link / n_tok, 1) if n_tok else 0.0
    payload = {
        "slug": args.slug,
        "title": args.title,
        "ref": args.ref,
        "text_name": text_name,
        "source": "DCS (Digital Corpus of Sanskrit) — CC BY 4.0",
        "built": args.built,
        "stats": {
            "sentences": len(out_sents), "tokens": n_tok,
            "linked_tokens": n_link, "link_rate_pct": rate,
            "tier_counts": tier_counts,
        },
        "sentences": out_sents,
    }

    # W-RU-a (H1278): optional additive Sa->Ru gloss layer. Runs BEFORE the write so the
    # pack is emitted once, with gloss_ru already inlined; the English gloss is untouched.
    if args.gloss_lang == "ru":
        from build_ru_gloss_layer import RuGlosser, inline_token_ru  # noqa: E402
        glosser = RuGlosser()
        for sent in payload["sentences"]:
            for tok in sent["tokens"]:
                inline_token_ru(tok, glosser)
        payload["gloss_langs"] = sorted(set((payload.get("gloss_langs") or []) + ["ru"]))

    read_dir = ROOT / "reading" / "data"
    read_dir.mkdir(parents=True, exist_ok=True)
    js = read_dir / ("%s.js" % args.slug)
    jsonf = read_dir / ("%s.json" % args.slug)
    body = json.dumps(payload, ensure_ascii=False, indent=1)
    with open(js, "w", encoding="utf-8", newline="\n") as f:
        f.write("window.READING_DATA = window.READING_DATA || {};\n")
        f.write('window.READING_DATA["%s"] = %s;\n' % (args.slug, body))
    with open(jsonf, "w", encoding="utf-8", newline="\n") as f:
        f.write(body + "\n")

    # build report
    rep = ROOT / "reading" / "BUILD_REPORT.md"
    lines = []
    lines.append("# Reading packs — build report\n")
    lines.append("_Auto-generated by scripts/build_reading_pack.py (H848)._\n")
    lines.append(f"## {args.slug} — {args.title}\n")
    lines.append(f"- Source ref: `{args.ref}` (DCS `{text_name}`, chapter_id {cid})")
    lines.append(f"- Sentences: {len(out_sents)} · tokens: {n_tok} · "
                 f"**linked to a /w/ card: {n_link} ({rate}%)**")
    lines.append(f"- Tiers (link tiers {LINK_TIERS} accepted; relaxed/fuzzy/none NOT linked):")
    for tier in ("exact", "floor", "relaxed", "fuzzy", "none"):
        if tier in tier_counts:
            lines.append(f"    - `{tier}`: {tier_counts[tier]}")
    lines.append("")
    lines.append(f"### Unresolved lemmas ({len(unresolved)} distinct) — honest residue")
    lines.append("DCS causative/denominative `-ay` stems and indeclinables that kosha "
                 "keys under the root; rendered as plain (un-linked) words.\n")
    for lem, cnt in sorted(unresolved.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{lem}` ×{cnt} (slp1 `{to_slp1(lem)}`)")
    lines.append("")
    lines.append("## Gītā 1 — PARKED (data gap)")
    lines.append("The Bhagavadgītā is **absent from the DCS full corpus**: Mahābhārata "
                 "book 6 (Bhīṣmaparvan) skips exactly adhyāyas 23–40 (the 18 Gītā "
                 "chapters), and no standalone Bhagavadgītā text exists in the DB. "
                 "Building a Gītā reading pack needs an external lemmatised BhG source "
                 "(GRETIL / DharmaMitra / a separate DCS export). Surfaced as `@DECIDE`.\n")
    with open(rep, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    dcon.close(); kcon.close()
    print(f"built {args.slug}: {len(out_sents)} sentences, {n_tok} tokens, "
          f"{n_link} linked ({rate}%)")
    print("tiers:", tier_counts)
    print("wrote:", js, jsonf, rep)


if __name__ == "__main__":
    main()
