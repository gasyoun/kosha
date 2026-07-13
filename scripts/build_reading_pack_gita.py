#!/usr/bin/env python
"""kosha Gītā reading-pack builder (H848 Task B — EXPERIMENTAL, machine-segmented).

The Nala pack (scripts/build_reading_pack.py) rode DCS's own GOLD lemmatisation.
The Bhagavadgītā is ABSENT from the DCS corpus, so this pack instead:

  1. takes the mūla text from GRETIL (reading/data/sources/gita-1_mula_gretil.tsv,
     a vendored public-domain text — no live fetch at build time),
  2. segments + lemmatises each verse with **vidyut-cheda** via kosha's own
     production wrapper app/segmenter.py (H181/K2a) — a MACHINE segmenter, not a
     gold annotation: it mis-splits some sandhi and mis-lemmatises some proper
     names / participles, so "linked" ≠ "correct". The pack is flagged
     `experimental` and the viewer shows a "verify before citing" banner.
  3. resolves each lemma (SLP1) to a kosha /w/ card (lemma present in kosha.db
     lemmas.slp1), using the same card_token twin as the Nala builder.

Output schema is identical to build_reading_pack.py so reading/index.html renders
both packs unchanged (plus an `experimental`/`method` flag on this one).

Usage:  python scripts/build_reading_pack_gita.py --built 2026-07-13
"""
import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT.parent / "sanskrit-util" / "py"))
import segmenter  # noqa: E402  (kosha app/segmenter.py — vidyut-cheda wrapper)
from sanskrit_util import to_slp1, from_slp1  # noqa: E402


def card_token(slp1: str) -> str:  # twin of app/word_page.py:49
    out = []
    for b in slp1.encode("utf-8"):
        out.append(chr(b) if (97 <= b <= 122) or (48 <= b <= 57) else "_%02x" % b)
    return "".join(out)


KOSHA_DB = ROOT / "data" / "db" / "kosha.db"
if not KOSHA_DB.exists():
    GH = ROOT.parent if (ROOT.parent / "VisualDCS").exists() else ROOT.parent.parent
    KOSHA_DB = GH / "kosha" / "data" / "db" / "kosha.db"

SRC = ROOT / "reading" / "data" / "sources" / "gita-1_mula_gretil.tsv"

# a "word" = maximal run of IAST letters (+ internal avagraha/marks we clean below)
_DANDA = re.compile(r"[|॥।/\\]+")
_VNUM = re.compile(r"\|\|\d+\|\|\s*$")


def clean_word(w):
    """Drop verse punctuation; strip GRETIL compound hyphens and a leading
    avagraha (elided a-)."""
    w = w.strip().strip("|।॥/\\")
    w = w.replace("-", "")          # GRETIL marks compound seams with '-'
    if w.startswith("'") or w.startswith("’"):
        w = "a" + w[1:]             # avagraha => restore the elided a-
    w = w.strip("'’")
    return w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="gita-1")
    ap.add_argument("--title", default="Gītā 1 — Arjunaviṣāda (Bhagavadgītā, adhyāya 1)")
    ap.add_argument("--built", default="2026-07-13")
    args = ap.parse_args()

    if not segmenter.available():
        sys.exit("vidyut-cheda unavailable — vendor data/vidyut (kosha.download_data) first")
    kcon = sqlite3.connect(str(KOSHA_DB)); kc = kcon.cursor()

    def in_kosha(slp1):
        return bool(slp1 and kc.execute(
            "SELECT 1 FROM lemmas WHERE slp1=? LIMIT 1", (slp1,)).fetchone())

    def resolve_form(form_slp1):
        """kosha reverse-lookup stage 1/2: a surface form -> its most frequent
        kosha lemma via the `forms` table. Returns (lemma_slp1, 'forms') or None.
        Frequency-ranked so an ambiguous form (kiM -> ka/kim/…) picks the common
        one; this is what makes whole inflected words (saMjaya, mAmakAH, asmAkam)
        resolve correctly where raw cheda mis-lemmatises them."""
        rows = kc.execute(
            "SELECT f.lemma_slp1 FROM forms f JOIN lemmas l ON l.slp1=f.lemma_slp1 "
            "WHERE f.form_slp1=? ORDER BY l.count_all DESC LIMIT 1", (form_slp1,)).fetchone()
        return (rows[0], "forms") if rows else None

    out_sents, n_tok, n_link = [], 0, 0
    tier_counts = {"forms": 0, "cheda": 0, "none": 0}
    unresolved = {}

    def emit_token(toks, form_iast, lemma_slp1, tier):
        nonlocal n_tok, n_link
        n_tok += 1
        tok = {"form": form_iast, "lemma": from_slp1(lemma_slp1) if lemma_slp1 else "",
               "upos": "", "morph": "", "gloss": ""}
        if lemma_slp1 and in_kosha(lemma_slp1):
            n_link += 1
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            tok["slp1"] = lemma_slp1
            tok["href"] = "../w/%s.html" % card_token(lemma_slp1)
            tok["tier"] = tier
        else:
            tier_counts["none"] += 1
            tok["resolved"] = False
            key = from_slp1(lemma_slp1) if lemma_slp1 else form_iast
            unresolved[key] = unresolved.get(key, 0) + 1
        toks.append(tok)

    for line in SRC.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        ref, text = line.split("\t", 1)
        display = _VNUM.sub("", text).strip()
        raw_words = [w for w in _DANDA.sub(" ", display).split() if w]
        toks = []
        for rw in raw_words:
            w = clean_word(rw)
            if not w:
                continue
            slp1_word = to_slp1(w)
            # 1. whole-word forms-table lookup (best quality for inflected words)
            r = resolve_form(slp1_word)
            if r:
                emit_token(toks, w, r[0], "forms")
                continue
            # 2. sandhi-fused word -> cheda split; each pada re-checked vs forms
            segs = segmenter.segment(slp1_word) or [{"text": slp1_word, "lemma": None}]
            for s in segs:
                pada = s.get("text")
                r2 = resolve_form(pada) if pada else None
                lemma = r2[0] if r2 else s.get("lemma")
                emit_token(toks, from_slp1(pada) if pada else w, lemma,
                           "forms" if r2 else "cheda")
        out_sents.append({
            "n": ref,
            "locus": "Bhagavadgītā %s" % ref,
            "dcs": None,
            "text": display,
            "tokens": toks,
        })

    rate = round(100.0 * n_link / n_tok, 1) if n_tok else 0.0
    payload = {
        "slug": args.slug,
        "title": args.title,
        "ref": "BhG 1",
        "text_name": "Bhagavadgītā",
        "source": "Mūla: GRETIL (public domain). Segmentation: vidyut-cheda (machine).",
        "built": args.built,
        "experimental": True,
        "method": "MACHINE-SEGMENTED (vidyut-cheda) — the Bhagavadgītā is absent from "
                  "the DCS gold corpus, so lemmas are auto-segmented and may be wrong "
                  "(proper names, participles, some compounds). Verify before citing.",
        "stats": {"sentences": len(out_sents), "tokens": n_tok,
                  "linked_tokens": n_link, "link_rate_pct": rate,
                  "tier_counts": tier_counts},
        "sentences": out_sents,
    }

    ddir = ROOT / "reading" / "data"
    ddir.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, indent=1)
    with open(ddir / ("%s.js" % args.slug), "w", encoding="utf-8", newline="\n") as f:
        f.write("window.READING_DATA = window.READING_DATA || {};\n")
        f.write('window.READING_DATA["%s"] = %s;\n' % (args.slug, body))
    with open(ddir / ("%s.json" % args.slug), "w", encoding="utf-8", newline="\n") as f:
        f.write(body + "\n")

    rep = ["# Reading pack — Gītā 1 (EXPERIMENTAL, machine-segmented)\n",
           "_Auto-generated by scripts/build_reading_pack_gita.py (H848)._\n",
           f"- Mūla source: GRETIL (vendored, {SRC.name}), {len(out_sents)} verses.",
           f"- Segmentation: kosha reverse-lookup cascade — `forms` table first "
           f"({tier_counts['forms']} tokens), vidyut-cheda fallback for sandhi-fused "
           f"words ({tier_counts['cheda']}).",
           f"- Tokens: {n_tok} · **linked to a /w/ card: {n_link} ({rate}%)** · "
           f"unresolved: {tier_counts['none']}.",
           "",
           "> **Machine-segmented — not gold.** The Bhagavadgītā is absent from the DCS "
           "gold corpus (MBh book 6 omits adhyāyas 23–40), so lemmas here are auto-derived "
           "and some are wrong (long samāsa compounds not split; a few proper-name / "
           "participle mis-lemmatisations). Unlike the Nala pack (DCS gold), verify before "
           "citing.\n",
           f"### Unresolved forms ({len(unresolved)} distinct)",
           "Mostly long compounds neither the `forms` table nor cheda resolve to a single "
           "headword:\n"]
    for k, v in sorted(unresolved.items(), key=lambda x: (-x[1], x[0])):
        rep.append(f"- `{k}` ×{v}")
    (ROOT / "reading" / "BUILD_REPORT_GITA.md").write_text(
        "\n".join(rep) + "\n", encoding="utf-8", newline="\n")

    print(f"built {args.slug}: {len(out_sents)} verses, {n_tok} tokens, "
          f"{n_link} linked ({rate}%) — EXPERIMENTAL machine-segmented")
    print(f"unresolved distinct: {len(unresolved)} (top: "
          + ", ".join(f"{k}×{v}" for k, v in sorted(unresolved.items(), key=lambda x: -x[1])[:8]) + ")")


if __name__ == "__main__":
    main()
