#!/usr/bin/env python
"""DCS sandhi-junction inducer (method A) — H882 Phase 0 + H888 Phase 1.

Generalises the Bhagavadgītā sandhi layer (scripts/build_gita_sandhi.py) from a
single *hand-curated* `sandhi` column to any text in the Digital Corpus of
Sanskrit (DCS). A DCS text has no such column, but every token carries both its
**sandhied surface** (CoNLL-U FORM) and its **pre-sandhi form** (MISC
`Unsandhied=…`). This script *induces* the same `X Y → Z` rule notation and reuses
the Gītā `categorise()` classifier verbatim, so the output is schema-compatible
with `data/gita/gita_sandhi.tsv`.

Two induction modes (H888 finding — DCS splits vowel coalescence differently
from cross-word sandhi):

  mode 1 — EDGE sandhi (visarga / anusvāra / consonant). Between two adjacent
           *syntactic words* whose FORM differs from Unsandhied at the facing
           edge. E.g. `janakaḥ`/`janaka` + `uvāca` → `ḥ u → Ø u`.

  mode 2 — VOWEL COALESCENCE inside a CoNLL-U **multi-word token** (MWT). DCS
           records a coalesced surface span (`5-6  nāgnir`) as an MWT range line
           over its component words (`5 na`, `6 agniḥ`), whose own FORM stays
           un-coalesced — so mode 1 never sees the merge. Mode 2 aligns the MWT
           surface against the concatenated component Unsandhied and reads the
           rule off each internal word boundary → `na agniḥ` in `nāgnir` yields
           `a a → ā`. (Phase 0 wrongly counted MWT range lines as tokens; fixed.)

This is **method A** of the roadmap's A/B/C split-method bake-off — the ceiling,
since it uses human-verified DCS splits.

Output (per text): data/sandhi/<slug>_sandhi.tsv
  columns: rule · category · count · pct · examples   (== gita_sandhi.tsv schema)

Public/MIT, credit Dr. Mārcis Gasūns.

Usage:
  python scripts/dcs_sandhi_induce.py --text "Aṣṭāvakragīta"
  python scripts/dcs_sandhi_induce.py --text Aṣṭāvakragīta --debug   # dump flagged cases
"""
import argparse
import csv
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DCS = Path("C:/Users/user/Documents/GitHub/dcs-conllu/files")

# --- phoneme helpers (IAST) -------------------------------------------------
VOWELS = set("aāiīuūṛṝḷḹeaioauē")
# aspirated stops are digraphs (kh gh ch jh ṭh ḍh th dh ph bh) — one phoneme
ASPIRABLE = set("kgcjṭḍtdpb")


def nfc(s):
    return unicodedata.normalize("NFC", s)


def first_phoneme(s):
    """Leading phoneme of an IAST string: an aspirate digraph counts as one,
    a consonant cluster (br, kr, …) returns only its first consonant."""
    if not s:
        return ""
    if len(s) >= 2 and s[0] in ASPIRABLE and s[1] == "h":
        return s[:2]
    return s[0]


def last_phoneme(s):
    if not s:
        return ""
    if len(s) >= 2 and s[-2] in ASPIRABLE and s[-1] == "h":
        return s[-2:]
    return s[-1]


def common_prefix_len(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def common_suffix_len(a, b):
    n = 0
    for x, y in zip(reversed(a), reversed(b)):
        if x != y:
            break
        n += 1
    return n


# --- mode 1: edge-sandhi inducer --------------------------------------------
def induce_rule(left_uns, left_surf, right_uns, right_surf):
    """Return (rule_string, flag) for the EDGE junction between two adjacent
    words. rule mirrors the Gītā notation `IN_LEFT IN_RIGHT → OUT_LEFT OUT_RIGHT`
    (`ḥ u → Ø u`, `m c → ṃ c`, `t b → d b`). flag is None for a clean induction,
    else a reason a Phase-1 pass should revisit."""
    lu, ls = nfc(left_uns), nfc(left_surf)
    ru, rs = nfc(right_uns), nfc(right_surf)

    if lu == ls and ru == rs:
        return None, "no-sandhi"

    # Only read the rule off the FACING edges — left token END, right token START.
    # A token's FORM can also differ at its *far* edge (sandhi with the OTHER
    # neighbour, or DCS lemma-normalisation like me→mama); the change must touch
    # the facing edge (left: common_suffix_len==0; right: common_prefix_len==0).
    if lu != ls and common_suffix_len(lu, ls) == 0:
        p = common_prefix_len(lu, ls)
        Lu, Ls = lu[p:], ls[p:]
    else:
        Lu, Ls = "", ""
    if ru != rs and common_prefix_len(ru, rs) == 0:
        s = common_suffix_len(ru, rs)
        Ru, Rs = ru[: len(ru) - s], rs[: len(rs) - s]
    else:
        Ru, Rs = "", ""

    left_changed = bool(Lu or Ls)
    right_changed = bool(Ru or Rs)
    if not left_changed and not right_changed:
        return None, "far-edge"

    in_left = Lu if Lu else last_phoneme(lu)
    in_right = Ru if Ru else first_phoneme(ru)
    out_left = Ls if left_changed else last_phoneme(lu)
    out_right = Rs if right_changed else first_phoneme(rs)

    rule = "%s %s → %s %s" % (in_left, in_right, out_left or "Ø", out_right or "Ø")
    rule = re.sub(r"\s+", " ", rule).strip()

    flag = None
    if left_changed and right_changed:
        flag = "two-sided"
    elif not in_left or not in_right:
        flag = "empty-side"
    return rule, flag


# --- mode 2: MWT-internal vowel-coalescence inducer -------------------------
def induce_coalescence(left_uns, right_uns, surface):
    """Given two component words' Unsandhied forms and the MWT surface that
    coalesces them, induce the rule at their internal boundary.

    Sandhi-aware, NOT a naïve char alignment: the last phoneme of `left` and the
    first phoneme of `right` merge into a short surface segment. We anchor on
    left's stable prefix (`left` minus its final phoneme) and locate where the
    stable head of right's remainder resumes in the surface; everything between
    is the merged output. This gets `na`+`eva`→`naiva` as `a e → ai` (a naïve
    alignment mis-reads it as `a e → i`), and `na`+`agniḥ`→`nāgnir` as `a a → ā`
    while ignoring agniḥ's separate right-edge visarga→r.

    Returns (rule, flag); flag None on a clean read, else a reason to revisit."""
    lu, ru, sf = nfc(left_uns), nfc(right_uns), nfc(surface)
    lp, rp = last_phoneme(lu), first_phoneme(ru)
    if not lp or not rp:
        return None, "empty-side"
    prefix = lu[: len(lu) - len(lp)]     # left minus its final phoneme
    if not sf.startswith(prefix):
        return None, "prefix-mismatch"    # left-edge of MWT changed — out of scope
    rest = sf[len(prefix):]               # = merged-output + tail-of-right
    right_rest = ru[len(rp):]             # what follows right's initial phoneme

    if right_rest:
        # right_rest's LAST phoneme may be edge-changed (MWT-final sandhi), so
        # search on its stable head; require ≥1 output char before it.
        key = right_rest[: len(right_rest) - len(last_phoneme(right_rest))] or right_rest
        idx = rest.find(key, 1) if key else -1
        if idx < 1:
            idx = rest.find(right_rest, 1)
        if idx < 1:
            return None, "align-fail"
        out = rest[:idx]
    else:
        out = rest  # single-phoneme right word fully merged (rare)

    if not out or len(out) > 3:
        return None, "align-fail"
    if out == lp + rp:
        return None, "no-sandhi"          # inputs pass through unchanged (a+v→av)
    rule = re.sub(r"\s+", " ", "%s %s → %s" % (lp, rp, out)).strip()
    return rule, None


# same 4-class scheme as scripts/build_gita_sandhi.py:categorise()
def categorise(rule):
    junction = rule.split("→")[0].strip()
    left = junction.replace(" ", "")
    if "ḥ" in junction:
        return "visarga"
    if "ṃ" in rule.split("→")[-1] or junction.startswith("m"):
        return "anusvāra / nasal"
    if left and all(ch in VOWELS for ch in left):
        return "vowel coalescence"
    return "consonant / other"


# --- CoNLL-U reading (MWT-aware) --------------------------------------------
UNS_RE = re.compile(r"Unsandhied=([^|\s]+)")


def read_sentences(conllu_path):
    """Yield (ref, words, mwts) per sentence.
      words: [{'id': int, 'form': str, 'uns': str|None}]  — syntactic words only
      mwts:  [{'start': int, 'end': int, 'surface': str}] — CoNLL-U range lines
    Empty/enhanced nodes (ids like `3.1`) are skipped."""
    words, mwts, ref = [], [], None
    for raw in conllu_path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("#"):
            if raw.startswith("# text ="):
                ref = raw.split("=", 1)[1].strip()
            continue
        if not raw.strip():
            if words:
                yield ref, words, mwts
            words, mwts, ref = [], [], None
            continue
        cols = raw.split("\t")
        if len(cols) < 10:
            continue
        idc = cols[0]
        if "-" in idc:
            a, b = idc.split("-", 1)
            if a.isdigit() and b.isdigit():
                mwts.append({"start": int(a), "end": int(b), "surface": cols[1]})
            continue
        if not idc.isdigit():  # enhanced/empty node
            continue
        m = UNS_RE.search(cols[9])
        words.append({"id": int(idc), "form": cols[1], "uns": m.group(1) if m else None})
    if words:
        yield ref, words, mwts


def induce_from_files(files, debug=False):
    """Run mode 1 + mode 2 over a list of .conllu paths.
    Returns (counts, examples, stats, debug_rows)."""
    counts = Counter()
    examples = defaultdict(list)
    flagged = Counter()
    debug_rows = []
    st = Counter()  # junctions, no_gold, no_sandhi, mwt_boundaries, mwt_no_gold

    for f in files:
        for ref, words, mwts in read_sentences(f):
            by_id = {w["id"]: w for w in words}
            # word-ids covered by some MWT → their internal edges are mode-2, not mode-1
            covered = set()
            for m in mwts:
                covered.update(range(m["start"], m["end"] + 1))

            # mode 1 — edge sandhi between adjacent syntactic words
            for i in range(len(words) - 1):
                w, x = words[i], words[i + 1]
                # skip a pair fully inside one MWT (its merge is mode-2 territory)
                if w["id"] in covered and x["id"] in covered \
                        and x["id"] - w["id"] == 1 and _same_mwt(w["id"], x["id"], mwts):
                    continue
                st["junctions"] += 1
                if w["uns"] is None or x["uns"] is None:
                    st["no_gold"] += 1
                    continue
                rule, flag = induce_rule(w["uns"], w["form"], x["uns"], x["form"])
                if rule is None:
                    st["no_sandhi"] += 1
                    continue
                if flag == "empty-side":
                    flagged["edge:empty-side"] += 1
                    if debug:
                        debug_rows.append(("edge:empty-side", w["uns"], w["form"], x["uns"], x["form"], rule))
                    continue
                if flag:
                    flagged["edge:" + flag] += 1
                counts[rule] += 1
                if len(examples[rule]) < 4:
                    examples[rule].append("%s %s+%s" % (ref or "", w["form"], x["form"]))

            # mode 2 — vowel coalescence inside each MWT
            for m in mwts:
                comps = [by_id[k] for k in range(m["start"], m["end"] + 1) if k in by_id]
                if len(comps) < 2:
                    continue
                for j in range(len(comps) - 1):
                    st["mwt_boundaries"] += 1
                    lc, rc = comps[j], comps[j + 1]
                    if lc["uns"] is None or rc["uns"] is None:
                        st["mwt_no_gold"] += 1
                        continue
                    rule, flag = induce_coalescence(lc["uns"], rc["uns"], m["surface"])
                    if rule is None:
                        st["mwt_no_sandhi"] += 1
                        continue
                    if flag:
                        flagged["coalesce:" + flag] += 1
                        if debug:
                            debug_rows.append(("coalesce:" + flag, lc["uns"], rc["uns"], m["surface"], "", rule))
                    counts[rule] += 1
                    if len(examples[rule]) < 4:
                        examples[rule].append("%s %s+%s→%s" % (ref or "", lc["uns"], rc["uns"], m["surface"]))

    return counts, examples, st, flagged, debug_rows


def _same_mwt(a, b, mwts):
    return any(m["start"] <= a and b <= m["end"] for m in mwts)


def slug(name):
    folded = "".join(c for c in unicodedata.normalize("NFD", name)
                     if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-z0-9]+", "_", folded).strip("_").lower() or "text"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True, help="DCS text directory name, e.g. Aṣṭāvakragīta")
    ap.add_argument("--dcs-root", default=str(DEFAULT_DCS))
    ap.add_argument("--out-dir", default=str(ROOT / "data" / "sandhi"))
    ap.add_argument("--debug", action="store_true", help="print flagged junctions")
    args = ap.parse_args()

    text_dir = Path(args.dcs_root) / args.text
    if not text_dir.is_dir():
        sys.exit("text dir not found: %s" % text_dir)
    files = sorted(text_dir.glob("*.conllu"))

    counts, examples, st, flagged, debug_rows = induce_from_files(files, debug=args.debug)
    total = sum(counts.values())

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_tsv = out_dir / ("%s_sandhi.tsv" % slug(args.text))
    with open(out_tsv, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["rule", "category", "count", "pct", "examples"])
        for rule, n in counts.most_common():
            w.writerow([rule, categorise(rule), n,
                        round(100.0 * n / total, 2) if total else 0,
                        " · ".join(examples[rule])])

    cat = Counter()
    for rule, n in counts.items():
        cat[categorise(rule)] += n

    print("=== %s ===" % args.text)
    print("files:               %d" % len(files))
    print("mode 1 (edge) junctions: %d  (no-gold %d · no-sandhi %d)"
          % (st["junctions"], st["no_gold"], st["no_sandhi"]))
    print("mode 2 (MWT) boundaries: %d  (no-gold %d · no-coalescence %d)"
          % (st["mwt_boundaries"], st["mwt_no_gold"], st["mwt_no_sandhi"]))
    print("rules: %d distinct over %d events" % (len(counts), total))
    print("flagged: %s" % (dict(flagged) or "none"))
    print("categories:", dict(cat.most_common()))
    print("wrote", out_tsv)
    print("\ntop 14 rules:")
    for rule, n in counts.most_common(14):
        print("  %-16s %-18s %4d  %5.1f%%" % (rule, categorise(rule), n,
                                              100.0 * n / total if total else 0))
    if args.debug and debug_rows:
        print("\nflagged (first 25):")
        for row in debug_rows[:25]:
            print("  [%s] %s | %s | %s => %s" % (row[0], row[1], row[2], row[3], row[5]))


if __name__ == "__main__":
    main()
