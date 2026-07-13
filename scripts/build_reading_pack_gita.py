#!/usr/bin/env python
"""kosha Gītā reading-pack builder — all 18 adhyāyas (H871 / roadmap W1).

Builds one gold reading pack per Gītā chapter straight off the W0 master
[`data/gita/gita_gold_master.tsv`] (9,092 words · 18 adhyāyas). Supersedes the
chapter-1-only build (which read a separate ch-1 TSV): the master is now the
single source. Each word links to its kosha /w/ card; the viewer carries
Devanagari + IAST + English gloss per verse.

Resolution: curated lemma (√/hyphens stripped) → SLP1 → kosha.db lemmas.slp1,
falling back to the root, then to the surface form via the `forms` table.

Usage: python scripts/build_reading_pack_gita.py --built 2026-07-13
"""
import argparse
import csv
import json
import re
import sqlite3
import sys
from collections import OrderedDict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "sanskrit-util" / "py"))
from sanskrit_util import to_slp1  # noqa: E402

MASTER = ROOT / "data" / "gita" / "gita_gold_master.tsv"
KOSHA_DB = ROOT / "data" / "db" / "kosha.db"
if not KOSHA_DB.exists():
    GH = ROOT.parent if (ROOT.parent / "SanskritGrammar").exists() else ROOT.parent.parent
    KOSHA_DB = GH / "kosha" / "data" / "db" / "kosha.db"

CHAPTER_NAMES = {
    1: "Arjunaviṣāda", 2: "Sāṅkhyayoga", 3: "Karmayoga", 4: "Jñānakarmasaṃnyāsa",
    5: "Karmasaṃnyāsa", 6: "Dhyāna", 7: "Jñānavijñāna", 8: "Akṣarabrahma",
    9: "Rājavidyārājaguhya", 10: "Vibhūti", 11: "Viśvarūpadarśana", 12: "Bhakti",
    13: "Kṣetrakṣetrajñavibhāga", 14: "Guṇatrayavibhāga", 15: "Puruṣottama",
    16: "Daivāsurasaṃpadvibhāga", 17: "Śraddhātrayavibhāga", 18: "Mokṣasaṃnyāsa",
}


def card_token(slp1):
    return "".join(chr(b) if (97 <= b <= 122) or (48 <= b <= 57) else "_%02x" % b
                   for b in slp1.encode("utf-8"))


def clean_lemma(s):
    return re.sub(r"[√\-\s]", "", s) if s else ""


def norm_ref(v):
    a, b = v.split(".")
    return "%d.%d" % (int(a), int(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--built", default="2026-07-13")
    args = ap.parse_args()
    kc = sqlite3.connect(str(KOSHA_DB)).cursor()

    def in_kosha(s):
        return bool(s and kc.execute("SELECT 1 FROM lemmas WHERE slp1=? LIMIT 1", (s,)).fetchone())

    def form_lemma(fs):
        r = kc.execute("SELECT f.lemma_slp1 FROM forms f JOIN lemmas l ON l.slp1=f.lemma_slp1 "
                       "WHERE f.form_slp1=? ORDER BY l.count_all DESC LIMIT 1", (fs,)).fetchone()
        return r[0] if r else None

    def resolve(lemma, root, form):
        cl = to_slp1(clean_lemma(lemma))
        if in_kosha(cl):
            return cl, "lemma"
        cr = to_slp1(clean_lemma(root))
        if cr and in_kosha(cr):
            return cr, "root"
        fk = form_lemma(to_slp1(clean_lemma(form)))
        if fk:
            return fk, "form"
        return (cl or None), None

    # group master rows by chapter -> verse
    chapters = OrderedDict()
    for r in csv.DictReader(open(MASTER, encoding="utf-8"), delimiter="\t"):
        ch = int(r["verse"].split(".")[0])
        chapters.setdefault(ch, OrderedDict()).setdefault(r["verse"], []).append(r)

    ddir = ROOT / "reading" / "data"
    ddir.mkdir(parents=True, exist_ok=True)
    summary = []
    for ch, verses in chapters.items():
        sents, n_tok, n_link = [], 0, 0
        for vref, words in verses.items():
            toks = []
            for r in words:
                n_tok += 1
                key, tier = resolve(r["lemma"], r["root"], r["iast"])
                linked = tier is not None and in_kosha(key)
                tok = {"form": r["iast"], "lemma": r["lemma"] or r["root"], "upos": "",
                       "morph": "", "gloss": r["gloss_en"], "gloss_ru": r["gloss_ru"],
                       "deva": r["devanagari"], "sandhi": r["sandhi"]}
                if linked:
                    n_link += 1
                    tok["slp1"] = key
                    tok["href"] = "../w/%s.html" % card_token(key)
                else:
                    tok["resolved"] = False
                toks.append(tok)
            deva = " ".join(w["devanagari"] for w in words if w["devanagari"])
            sents.append({"n": norm_ref(vref), "locus": "Bhagavadgītā %s" % norm_ref(vref),
                          "dcs": None, "text": words[0]["verse_iast"], "deva": deva, "tokens": toks})
        rate = round(100.0 * n_link / n_tok, 1) if n_tok else 0.0
        payload = {"slug": "gita-%d" % ch, "chapter": ch,
                   "title": "Gītā %d — %s (Bhagavadgītā)" % (ch, CHAPTER_NAMES.get(ch, "")),
                   "ref": "BhG %d" % ch, "text_name": "Bhagavadgītā", "built": args.built,
                   "source": "Word-by-word gold analysis: SanskritGrammar/Concordance/Gita.xlsm "
                             "(hand-curated), via data/gita/gita_gold_master.tsv.",
                   "stats": {"sentences": len(sents), "tokens": n_tok,
                             "linked_tokens": n_link, "link_rate_pct": rate},
                   "sentences": sents}
        body = json.dumps(payload, ensure_ascii=False, indent=1)
        with open(ddir / ("gita-%d.js" % ch), "w", encoding="utf-8", newline="\n") as f:
            f.write("window.READING_DATA = window.READING_DATA || {};\n")
            f.write('window.READING_DATA["gita-%d"] = %s;\n' % (ch, body))
        summary.append((ch, len(sents), n_tok, rate))

    tot_v = sum(s[1] for s in summary); tot_t = sum(s[2] for s in summary)
    tot_l = sum(round(s[2] * s[3] / 100.0) for s in summary)
    print("built %d chapters: %d verses, %d tokens, ~%.1f%% linked" %
          (len(summary), tot_v, tot_t, 100.0 * tot_l / tot_t))
    for ch, v, t, r in summary:
        print("  gita-%-2d: %3d verses, %4d tokens, %.1f%%" % (ch, v, t, r))


if __name__ == "__main__":
    main()
