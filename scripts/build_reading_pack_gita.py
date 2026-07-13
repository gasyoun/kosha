#!/usr/bin/env python
"""kosha Gītā reading-pack builder (H848 Task B — GOLD, hand-curated).

Supersedes the earlier experimental (GRETIL + vidyut-cheda machine) build. The
lemmas, roots, morphology and English/Russian glosses now come from the
hand-curated word-by-word Bhagavadgītā in SanskritGrammar/Concordance/Gita.xlsm,
vendored as reading/data/sources/gita-1_gold_sanskritgrammar.tsv
(regenerate with scripts/extract_gita_gold.py). This is a GOLD pack — the same
quality class as the DCS-lemmatised Nala pack.

Resolution to a kosha /w/ card: the curated lemma (√/hyphens stripped) → SLP1 →
kosha.db lemmas.slp1; falls back to the root, then to the surface form via the
`forms` table. Emits the same payload schema as build_reading_pack.py so
reading/index.html renders it; carries the English gloss + Devanagari per verse.

Usage: python scripts/build_reading_pack_gita.py --built 2026-07-13
"""
import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "sanskrit-util" / "py"))
from sanskrit_util import to_slp1  # noqa: E402

SRC = ROOT / "reading" / "data" / "sources" / "gita-1_gold_sanskritgrammar.tsv"
KOSHA_DB = ROOT / "data" / "db" / "kosha.db"
if not KOSHA_DB.exists():
    GH = ROOT.parent if (ROOT.parent / "SanskritGrammar").exists() else ROOT.parent.parent
    KOSHA_DB = GH / "kosha" / "data" / "db" / "kosha.db"

COLS = ["vref", "widx", "form", "deva", "lemma", "root", "morph",
        "gloss_en", "gloss_ru", "verse_iast", "verse_deva"]


def card_token(slp1):  # twin of app/word_page.py:49
    return "".join(chr(b) if (97 <= b <= 122) or (48 <= b <= 57) else "_%02x" % b
                   for b in slp1.encode("utf-8"))


def clean_lemma(s):
    return re.sub(r"[√\-\s]", "", s) if s else ""


def norm_ref(vref):  # '1.01' -> '1.1'
    a, b = vref.split(".")
    return "%d.%d" % (int(a), int(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="gita-1")
    ap.add_argument("--title", default="Gītā 1 — Arjunaviṣāda (Bhagavadgītā, adhyāya 1)")
    ap.add_argument("--built", default="2026-07-13")
    args = ap.parse_args()

    kc = sqlite3.connect(str(KOSHA_DB)).cursor()

    def in_kosha(slp1):
        return bool(slp1 and kc.execute(
            "SELECT 1 FROM lemmas WHERE slp1=? LIMIT 1", (slp1,)).fetchone())

    def form_lemma(form_slp1):
        r = kc.execute(
            "SELECT f.lemma_slp1 FROM forms f JOIN lemmas l ON l.slp1=f.lemma_slp1 "
            "WHERE f.form_slp1=? ORDER BY l.count_all DESC LIMIT 1", (form_slp1,)).fetchone()
        return r[0] if r else None

    def resolve(lemma_raw, root_raw, form):
        """Curated lemma → root → surface-form(forms table). Returns
        (slp1_key, tier) or (fallback_key, None)."""
        cl = to_slp1(clean_lemma(lemma_raw))
        if in_kosha(cl):
            return cl, "lemma"
        cr = to_slp1(clean_lemma(root_raw))
        if cr and in_kosha(cr):
            return cr, "root"
        fk = form_lemma(to_slp1(clean_lemma(form)))
        if fk:
            return fk, "form"
        return (cl or None), None

    verses, order = {}, []
    for line in SRC.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        r = dict(zip(COLS, (line.split("\t") + [""] * len(COLS))[:len(COLS)]))
        v = r["vref"]
        if v not in verses:
            verses[v] = {"iast": r["verse_iast"], "deva": r["verse_deva"], "rows": []}
            order.append(v)
        verses[v]["rows"].append(r)

    out_sents, n_tok, n_link = [], 0, 0
    tier_counts = {"lemma": 0, "root": 0, "form": 0, "none": 0}
    unresolved = {}
    for v in order:
        vd = verses[v]
        toks = []
        for r in vd["rows"]:
            n_tok += 1
            key, tier = resolve(r["lemma"], r["root"], r["form"])
            linked = tier is not None and in_kosha(key)
            lemdisp = r["lemma"] or r["root"]
            tok = {"form": r["form"], "lemma": lemdisp, "upos": "",
                   "morph": r["morph"], "gloss": r["gloss_en"], "deva": r["deva"]}
            if linked:
                n_link += 1
                tier_counts[tier] += 1
                tok["slp1"] = key
                tok["href"] = "../w/%s.html" % card_token(key)
                tok["tier"] = tier
            else:
                tier_counts["none"] += 1
                tok["resolved"] = False
                unresolved[lemdisp or r["form"]] = unresolved.get(lemdisp or r["form"], 0) + 1
            toks.append(tok)
        out_sents.append({
            "n": norm_ref(v), "locus": "Bhagavadgītā %s" % norm_ref(v),
            "dcs": None, "text": vd["iast"], "deva": vd["deva"], "tokens": toks})

    rate = round(100.0 * n_link / n_tok, 1) if n_tok else 0.0
    payload = {
        "slug": args.slug, "title": args.title, "ref": "BhG 1",
        "text_name": "Bhagavadgītā", "built": args.built,
        "source": "Word-by-word gold analysis: SanskritGrammar/Concordance/Gita.xlsm "
                  "(hand-curated lemma·root·morphology·English gloss).",
        "stats": {"sentences": len(out_sents), "tokens": n_tok,
                  "linked_tokens": n_link, "link_rate_pct": rate,
                  "tier_counts": tier_counts},
        "sentences": out_sents,
    }
    ddir = ROOT / "reading" / "data"
    body = json.dumps(payload, ensure_ascii=False, indent=1)
    with open(ddir / ("%s.js" % args.slug), "w", encoding="utf-8", newline="\n") as f:
        f.write("window.READING_DATA = window.READING_DATA || {};\n")
        f.write('window.READING_DATA["%s"] = %s;\n' % (args.slug, body))
    with open(ddir / ("%s.json" % args.slug), "w", encoding="utf-8", newline="\n") as f:
        f.write(body + "\n")

    rep = ["# Reading pack — Gītā 1 (GOLD, hand-curated)\n",
           "_Auto-generated by scripts/build_reading_pack_gita.py (H848)._\n",
           f"- Source: SanskritGrammar/Concordance/Gita.xlsm (hand-curated word-by-word), "
           f"vendored {SRC.name}, {len(out_sents)} verses.",
           f"- Tokens: {n_tok} · **linked to a /w/ card: {n_link} ({rate}%)** "
           f"(lemma {tier_counts['lemma']} · root {tier_counts['root']} · form {tier_counts['form']} · "
           f"unresolved {tier_counts['none']}).",
           "- Lemmas, roots, morphology and English/Russian glosses are hand-curated — "
           "GOLD, the same quality class as the DCS-lemmatised Nala pack (supersedes the "
           "earlier GRETIL + vidyut-cheda experimental build).\n",
           f"### Unresolved lemmas ({len(unresolved)} distinct)",
           "Compound headwords not held as single kosha lemmas (the gloss still shows):\n"]
    for k, c in sorted(unresolved.items(), key=lambda x: (-x[1], x[0])):
        rep.append(f"- `{k}` ×{c}")
    (ROOT / "reading" / "BUILD_REPORT_GITA.md").write_text(
        "\n".join(rep) + "\n", encoding="utf-8", newline="\n")

    print(f"built {args.slug} GOLD: {len(out_sents)} verses, {n_tok} tokens, "
          f"{n_link} linked ({rate}%) tiers={tier_counts}")


if __name__ == "__main__":
    main()
