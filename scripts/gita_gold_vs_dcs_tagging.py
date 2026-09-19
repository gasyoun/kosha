#!/usr/bin/env python
"""H4799 — Gītā gold master lemma/POS vs DCS's own tagging of MBh 6 BhaGī 1–18.

The third Gītā QA leg, distinct from gita_inflection_qa.py (gold case/number/
gender vs kosha's OWN inflection engine, H874/W4): here the counterpart is
DCS's OWN hand tagging (dcs_full.sqlite, chapters 'MBh, 6, BhaGī N') compared
against the gold master's lemma and coarse POS. Word-level alignment is
compound-aware — the gold master treats compounds as one word ("dharma-kṣetra")
while DCS tokenises them apart ("dharma" + "kṣetra") — and sandhi-neutral
(final ḥ/ṃ/s deleted symmetrically on both streams) so surface sandhi never
breaks the join. Writes the full divergence map + a printed summary. Nothing
is auto-applied — divergences are a candidate feed, not corrections.

Usage: python scripts/gita_gold_vs_dcs_tagging.py
"""
import csv
import re
import sqlite3
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent

GOLD = ROOT / "data" / "gita" / "gita_gold_master.tsv"
OUT = ROOT / "data" / "gita" / "gita_gold_vs_dcs_tagging.tsv"
DCS_DB = ROOT.parent / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"

# window caps for the group search: 1 gold word may span several DCS tokens
# (compound split) and, rarely, 2 gold words merge into 1 DCS token
MAX_G, MAX_D = 3, 6

AVAGRAHA = {"'", "‘", "’", "’"}
SANDHI_CHARS = set("ḥṃs")  # deleted symmetrically for the alignment join only
VOWELS = set("aāiīuūṛṝḷeo")  # for the sandhi-tolerant consonant-skeleton key


def norm(s: str) -> str:
    """Lowercase IAST word, punctuation/ZWSP/avagraha stripped, hyphens removed."""
    out = []
    for ch in s.strip():
        if ch in AVAGRAHA:
            out.append("a")
        elif ch == "ṁ":  # niggahita dot-above ≡ dot-below variant
            out.append("ṃ")
        elif ch.isspace() or not ch.isalpha():
            continue
        else:
            out.append(ch.lower())
    return "".join(out)


def join_key(parts) -> str:
    return "".join(ch for ch in "".join(norm(p) for p in parts) if ch not in SANDHI_CHARS)


def skeleton(key: str) -> str:
    """Consonant skeleton — equal under vowel sandhi (guṇa/vṛddhi/a+i→e …)."""
    return "".join(ch for ch in key if ch not in VOWELS)


def gold_pos(row) -> str:
    """Coarse POS from the master's form_type/code/tense columns."""
    ft, code, tense = row["form_type"], row["code"], row["tense"]
    if ft == "verb":
        return "verb"
    m = re.match(r"\d+([nv])", code.strip())
    if m:
        return "verb" if m.group(1) == "v" else "nominal"
    if tense.strip() == "av." or ft in ("indecl", "partcpl"):
        return "indecl"
    if ft in ("nam", "adj", "pronoun"):
        return "nominal"
    return "unknown"


def dcs_pos(upos: str) -> str:
    return {"NOUN": "nominal", "PROPN": "nominal", "PRON": "nominal",
            "VERB": "verb", "AUX": "verb"}.get(upos, "indecl")


def gold_lemma_key(lemma: str) -> str:
    return norm(lemma).lstrip("√") if lemma.startswith("√") else norm(lemma)


# systematic lemmatization-convention families: gold and DCS disagree on the
# STRING but agree on the lexeme — these are not tagging errors
PRONOUN_MAP = {"asmat": "mad", "yuṣmat": "tvad", "tat": "tad", "yat": "yad",
               "etat": "etad", "kim": "ka"}
NASALS = "mṃṅn"


def _strip_final(s: str, chars: str) -> str:
    while s and s[-1] in chars:
        s = s[:-1]
    return s


def lemma_convention(gkey: str, dkey: str) -> str:
    """Name of the convention family making gkey≠dkey, or '' if genuine."""
    if PRONOUN_MAP.get(gkey) == dkey or gkey == PRONOUN_MAP.get(dkey, ""):
        return "pronoun-stem"
    if gkey.translate(str.maketrans(NASALS, "N" * 4)) == \
            dkey.translate(str.maketrans(NASALS, "N" * 4)):
        return "nasal-class"  # sam-jaya/saṃjaya, puṁgava/puṅgava
    for chars_a, chars_b, name in ((  # jagat/jagant, mahant/mahat
            "td", "ṅṃnm", "final-t/d+n"), ("sḥ", "", "adverb--tas/-taḥ")):
        if _strip_final(_strip_final(gkey, chars_a), chars_b) == \
                _strip_final(_strip_final(dkey, chars_a), chars_b):
            return name
    if skeleton(gkey) == skeleton(dkey):
        return "vowel-sandhi/contraction"  # ava-√āp/avāp, cet/ced
    return ""


def load_gold():
    by_adj = {}
    with open(GOLD, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            adj = int(row["verse"].split(".")[0])
            by_adj.setdefault(adj, []).append(row)
    return by_adj


def load_dcs():
    db = sqlite3.connect(f"file:{DCS_DB}?mode=ro", uri=True)
    cur = db.cursor()
    rows = cur.execute(
        """
        select cast(substr(c.ref, 14) as int) as adj,
               t.form, t.lemma, t.upos
        from chapter c
        join sentence s on s.chapter_id = c.chapter_id
        join token t on t.sentence_id = s.id
        where c.ref like 'MBh, 6, BhaGī%'
        order by adj, s.id, t.idx
        """
    ).fetchall()
    db.close()
    by_adj = {}
    for adj, form, lemma, upos in rows:
        by_adj.setdefault(adj, []).append((form, lemma, upos))
    return by_adj


def _find_group(g, d, gold_rows, dcs_rows):
    """Smallest (m, n) whose sanitized concatenations match at (g, d), or None.

    Tier 1: exact join-key equality. Tier 2 (vowel sandhi, e.g. gold
    'maheṣv-āsāḥ' vs DCS 'mahā'+'iṣvāsāḥ'): equal consonant skeletons AND
    difflib ratio ≥ 0.55 so short skeletons never mis-join.
    """
    cands = sorted(
        ((m, n) for m in range(1, MAX_G + 1) for n in range(1, MAX_D + 1)),
        key=lambda mn: (mn[0] + mn[1], abs(mn[0] - mn[1]), mn[0]),
    )
    for tier in ("exact", "skeleton"):
        for m, n in cands:
            if g + m > len(gold_rows) or d + n > len(dcs_rows):
                continue
            gk = join_key(r["iast"] for r in gold_rows[g:g + m])
            dk = join_key(f for f, _, _ in dcs_rows[d:d + n])
            if gk == dk:
                return m, n
            if tier == "skeleton" and skeleton(gk) == skeleton(dk) and \
                    SequenceMatcher(None, gk, dk).ratio() >= 0.55:
                return m, n
    return None


def align(adhyaya, gold_rows, dcs_rows):
    """Greedy smallest-window group join on sanitized concatenated streams.

    Word-count mismatches (one stream has an extra word) are recovered by
    dropping the MINIMAL side and verifying a real group matches right after
    — a blind drop-both would freeze the offset for the rest of the adhyāya.
    """
    groups = []
    g = d = 0
    while g < len(gold_rows) or d < len(dcs_rows):
        if g >= len(gold_rows):  # gold exhausted: DCS-only tail
            groups.append((adhyaya, [], dcs_rows[d:]))
            break
        if d >= len(dcs_rows):  # DCS exhausted: gold-only tail
            groups.append((adhyaya, gold_rows[g:], []))
            break
        found = _find_group(g, d, gold_rows, dcs_rows)
        if found:
            m, n = found
            groups.append((adhyaya, gold_rows[g:g + m], dcs_rows[d:d + n]))
            g += m
            d += n
            continue
        # drift recovery: single-side drop that provably realigns, else drop both
        for dm, dn in ((0, 1), (1, 0)):
            if g + dm < len(gold_rows) or d + dn < len(dcs_rows):
                if _find_group(g + dm, d + dn, gold_rows, dcs_rows) is not None:
                    groups.append((adhyaya, gold_rows[g:g + dm], dcs_rows[d:d + dn]))
                    g += dm
                    d += dn
                    break
        else:
            groups.append((adhyaya, gold_rows[g:g + 1], dcs_rows[d:d + 1]))
            g += 1
            d += 1
    return groups


def classify(gold_rows, dcs_rows):
    m, n = len(gold_rows), len(dcs_rows)
    gold_lemmas = "|".join(r["lemma"] for r in gold_rows)
    gold_forms = "|".join(r["iast"] for r in gold_rows)
    dcs_forms = "|".join(f for f, _, _ in dcs_rows)
    dcs_lemmas = "|".join(l for _, l, _ in dcs_rows)
    dcs_upos = "|".join(u for _, _, u in dcs_rows)
    gpos = gold_pos(gold_rows[0]) if m == 1 else "|".join(gold_pos(r) for r in gold_rows)
    dpos = dcs_pos(dcs_rows[0][2]) if n == 1 else "|".join(dcs_pos(u) for _, _, u in dcs_rows)
    if not dcs_rows or not gold_rows:
        cls = "DCS_ONLY" if gold_rows else "GOLD_ONLY"
        lemma_match = pos_match = conv = ""
    elif m == 1 and n == 1:
        gk, dk = gold_lemma_key(gold_rows[0]["lemma"]), norm(dcs_rows[0][1])
        lemma_match = gk == dk
        pos_match = gpos == dpos
        convention = lemma_convention(gk, dk) if not lemma_match else ""
        if lemma_match and pos_match:
            cls = "MATCH"
        elif lemma_match:
            cls = "POS_DIVERGE"
        elif pos_match and convention:
            cls = "LEMMA_CONVENTION"
        elif convention:
            cls = "LEMMA_CONVENTION+POS_DIVERGE"
        elif pos_match:
            cls = "LEMMA_DIVERGE"
        else:
            cls = "LEMMA+POS_DIVERGE"
        lemma_match = "yes" if lemma_match else "no"
        pos_match = "yes" if pos_match else "no"
        conv = convention
    else:
        cls = "COMPOUND_SPLIT" if m == 1 else ("MERGE" if n == 1 else "RESEGMENTED")
        lemma_match = pos_match = "n/a"
        conv = ""
    return {
        "adhyaya": "", "verse": gold_rows[0]["verse"] if gold_rows else "",
        "gold_form": gold_forms, "gold_lemma": gold_lemmas, "gold_pos": gpos,
        "dcs_form": dcs_forms, "dcs_lemma": dcs_lemmas, "dcs_upos": dpos,
        "class": cls, "lemma_match": lemma_match, "pos_match": pos_match,
        "convention": conv,
        "n_gold": m, "n_dcs": n,
    }


def main():
    gold, dcs = load_gold(), load_dcs()
    assert set(gold) == set(dcs), f"adhyaya mismatch: gold={sorted(gold)} dcs={sorted(dcs)}"
    records, cls_counter, pos_confusion = [], Counter(), Counter()
    for adj in sorted(gold):
        groups = align(adj, gold[adj], dcs[adj])
        for _, grows, drows in groups:
            rec = classify(grows, drows)
            rec["adhyaya"] = adj
            records.append(rec)
            cls_counter[rec["class"]] += 1
            if rec["lemma_match"] in ("yes", "no"):
                for gp, dp in zip(rec["gold_pos"].split("|"), rec["dcs_upos"].split("|")):
                    pos_confusion[(gp, dp)] += 1

    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0].keys()), delimiter="\t",
                           lineterminator="\n")
        w.writeheader()
        w.writerows(records)

    total = len(records)
    conv_counter = Counter(r["convention"] for r in records if r["convention"])
    print(f"H4799 gita gold vs DCS tagging — {total} aligned groups over 18 adhyāyas")
    for cls, n in cls_counter.most_common():
        print(f"  {cls:30s} {n:5d}  ({n / total:.1%})")
    one2one = cls_counter["MATCH"] + cls_counter["LEMMA_DIVERGE"] + \
        cls_counter["POS_DIVERGE"] + cls_counter["LEMMA+POS_DIVERGE"] + \
        cls_counter["LEMMA_CONVENTION"] + cls_counter["LEMMA_CONVENTION+POS_DIVERGE"]
    lemma_ok = cls_counter["MATCH"] + cls_counter["POS_DIVERGE"]
    lemma_conv = lemma_ok + cls_counter["LEMMA_CONVENTION"] + \
        cls_counter["LEMMA_CONVENTION+POS_DIVERGE"]
    pos_ok = cls_counter["MATCH"] + cls_counter["LEMMA_DIVERGE"] + \
        cls_counter["LEMMA_CONVENTION"]
    print(f"  1:1 groups: {one2one} — lemma string agreement {lemma_ok} "
          f"({lemma_ok / max(one2one, 1):.1%}), +conventions {lemma_conv} "
          f"({lemma_conv / max(one2one, 1):.1%}), POS agreement {pos_ok} "
          f"({pos_ok / max(one2one, 1):.1%})")
    print("  convention families:")
    for fam, n in conv_counter.most_common():
        print(f"    {fam:28s} {n:5d}")
    print("  POS confusion (gold -> dcs, top):")
    for (gp, dp), n in pos_confusion.most_common(12):
        print(f"    {gp:8s} -> {dp:8s} {n:5d}")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
