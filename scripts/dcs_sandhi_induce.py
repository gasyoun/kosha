#!/usr/bin/env python
"""H882 / Phase 0 — DCS sandhi-junction inducer.

Generalises the Bhagavadgītā sandhi layer (scripts/build_gita_sandhi.py) from a
single *hand-curated* `sandhi` column to any text in the Digital Corpus of
Sanskrit (DCS). The Gītā table read a human-annotated rule (e.g. `aḥ a → o '`)
straight off the gold master; a DCS text has no such column — but it DOES carry,
per token, both the **sandhied surface** (CoNLL-U FORM, col 2) and the
**pre-sandhi form** (MISC `Unsandhied=…`). This script *induces* the same rule
notation by diffing those two across every adjacent token pair, then reuses the
Gītā `categorise()` classifier verbatim so the output is schema-compatible with
`data/gita/gita_sandhi.tsv`.

This is **method A** of the roadmap's A/B/C split-method bake-off (A = DCS gold
splits; B = Vidyut cheda; C = neural). It is the ceiling: every other method
must match the rules A induces from human-verified DCS splits.

Output (per text): data/sandhi/<text_slug>_sandhi.tsv
  columns: rule · category · count · pct · examples   (== gita_sandhi.tsv schema)
Also prints a coverage report: junctions seen · rules induced · flagged-complex.

Public/MIT, credit Dr. Mārcis Gasūns.

Usage:
  python scripts/dcs_sandhi_induce.py --text "Aṣṭāvakragīta"
  python scripts/dcs_sandhi_induce.py --dcs-root /path/to/dcs-conllu/files --text Aṣṭāvakragīta
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


# --- the inducer ------------------------------------------------------------
def induce_rule(left_uns, left_surf, right_uns, right_surf):
    """Return (rule_string, flag) for the junction between two adjacent words.

    rule_string mirrors the Gītā notation: `IN_LEFT IN_RIGHT → OUT_LEFT OUT_RIGHT`
    e.g. `ḥ u → Ø u`, `a a → ā`, `m c → ṃ c`, `t b → d b`.
    flag is None for a clean induction, else a short reason a Phase-1 pass should
    revisit (both-sided change, deletion-only, etc.)."""
    lu, ls = nfc(left_uns), nfc(left_surf)
    ru, rs = nfc(right_uns), nfc(right_surf)

    if lu == ls and ru == rs:
        return None, "no-sandhi"  # nothing changed at this boundary

    # A junction rule may only be read off the FACING edges — the left token's
    # END and the right token's START. A token's FORM can also differ from its
    # Unsandhied at its *far* edge (sandhi with the OTHER neighbour, or DCS
    # lemma-normalisation like me→mama). Guard against attributing that far-edge
    # change to this junction: the change must touch the facing edge.
    #  - left token: change touches END  ⇔ common_suffix_len(lu, ls) == 0
    #  - right token: change touches START ⇔ common_prefix_len(ru, rs) == 0
    if lu != ls and common_suffix_len(lu, ls) == 0:
        p = common_prefix_len(lu, ls)
        Lu, Ls = lu[p:], ls[p:]
    else:
        Lu, Ls = "", ""  # left token's right edge unchanged
    if ru != rs and common_prefix_len(ru, rs) == 0:
        s = common_suffix_len(ru, rs)
        Ru, Rs = ru[: len(ru) - s], rs[: len(rs) - s]
    else:
        Ru, Rs = "", ""  # right token's left edge unchanged

    left_changed = bool(Lu or Ls)
    right_changed = bool(Ru or Rs)
    if not left_changed and not right_changed:
        # the FORM≠Unsandhied difference is entirely on the far edges — this
        # junction itself has no sandhi to record (e.g. me/mama, idam/idaṃ)
        return None, "far-edge"

    # input phonemes that meet at the junction
    in_left = Lu if Lu else last_phoneme(lu)
    in_right = Ru if Ru else first_phoneme(ru)
    # surface realisation on each side of the boundary
    out_left = Ls if left_changed else last_phoneme(lu)
    if right_changed:
        out_right = Rs
    else:
        out_right = first_phoneme(rs)

    rule = "%s %s → %s %s" % (in_left, in_right, out_left or "Ø", out_right or "Ø")
    rule = re.sub(r"\s+", " ", rule).strip()

    flag = None
    if left_changed and right_changed:
        flag = "two-sided"  # genuine coalescence w/ both tokens reshaped — verify
    elif not in_left or not in_right:
        flag = "empty-side"
    return rule, flag


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


# --- CoNLL-U reading --------------------------------------------------------
UNS_RE = re.compile(r"Unsandhied=([^|\s]+)")


def read_sentences(conllu_path):
    """Yield lists of (form, unsandhied|None) token tuples, one list per sentence."""
    sent = []
    ref = None
    for raw in conllu_path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("#") or raw.startswith("##"):
            if raw.startswith("# text ="):
                ref = raw.split("=", 1)[1].strip()
            continue
        if not raw.strip():
            if sent:
                yield ref, sent
                sent = []
            continue
        cols = raw.split("\t")
        if len(cols) < 10:
            continue
        form = cols[1]
        m = UNS_RE.search(cols[9])
        uns = m.group(1) if m else None
        sent.append((form, uns))
    if sent:
        yield ref, sent


def slug(name):
    # fold IAST diacritics to base letters (ā→a, ṣ→s, ṃ→m, ḥ→h …) then asciify
    folded = "".join(c for c in unicodedata.normalize("NFD", name)
                     if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-z0-9]+", "_", folded).strip("_").lower() or "text"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True, help="DCS text directory name, e.g. Aṣṭāvakragīta")
    ap.add_argument("--dcs-root", default=str(DEFAULT_DCS))
    ap.add_argument("--out-dir", default=str(ROOT / "data" / "sandhi"))
    ap.add_argument("--debug", action="store_true", help="print flagged/complex junctions")
    args = ap.parse_args()

    text_dir = Path(args.dcs_root) / args.text
    if not text_dir.is_dir():
        sys.exit("text dir not found: %s" % text_dir)

    files = sorted(text_dir.glob("*.conllu"))
    counts = Counter()
    examples = defaultdict(list)
    flagged = Counter()
    debug_rows = []
    junctions = 0
    no_gold = 0
    no_sandhi = 0  # facing edges unchanged (or far-edge-only diff) — no rule owed

    for f in files:
        for ref, sent in read_sentences(f):
            for i in range(len(sent) - 1):
                (lf, lu), (rf, ru) = sent[i], sent[i + 1]
                junctions += 1
                if lu is None or ru is None:
                    no_gold += 1
                    continue
                rule, flag = induce_rule(lu, lf, ru, rf)
                if rule is None:
                    no_sandhi += 1  # "no-sandhi" or "far-edge": no event at this junction
                    continue
                if flag == "empty-side":
                    flagged[flag] += 1  # a genuine sandhi event we could NOT rule-tag
                    if args.debug:
                        debug_rows.append((flag, lu, lf, ru, rf, rule))
                    continue
                if flag:
                    flagged[flag] += 1
                    if args.debug:
                        debug_rows.append((flag, lu, lf, ru, rf, rule))
                counts[rule] += 1
                if len(examples[rule]) < 4:
                    examples[rule].append("%s %s+%s" % (ref or "", lf, rf))

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

    gold = junctions - no_gold
    unruled = flagged.get("empty-side", 0)      # sandhi events we could NOT rule-tag
    review = flagged.get("two-sided", 0)        # ruled, but flagged for verification
    sandhi_events = total + unruled             # total already includes `review`
    print("=== %s ===" % args.text)
    print("files:               %d" % len(files))
    print("adjacent junctions:  %d" % junctions)
    print("  no gold split:     %d  (%.0f%% — token lacks Unsandhied=)"
          % (no_gold, 100.0 * no_gold / junctions if junctions else 0))
    print("  no sandhi at edge:  %d  (%.0f%% of gold — FORM==Unsandhied facing)"
          % (no_sandhi, 100.0 * no_sandhi / gold if gold else 0))
    print("  sandhi events:      %d  (%.0f%% of gold)"
          % (sandhi_events, 100.0 * sandhi_events / gold if gold else 0))
    print("    ruled:            %d events → %d distinct rules (%.1f%% of events)"
          % (total, len(counts), 100.0 * total / sandhi_events if sandhi_events else 0))
    print("      of which flagged for review (two-sided): %d" % review)
    print("    unruled:          %d  (empty-side)" % unruled)
    print("categories:", dict(cat.most_common()))
    print("wrote", out_tsv)
    print("\ntop 12 rules:")
    for rule, n in counts.most_common(12):
        print("  %-18s %-18s %4d  %5.1f%%" % (rule, categorise(rule), n,
                                              100.0 * n / total if total else 0))
    if args.debug and debug_rows:
        print("\nflagged junctions (first 25):")
        for flag, lu, lf, ru, rf, rule in debug_rows[:25]:
            print("  [%s] %s/%s + %s/%s => %s" % (flag, lu, lf, ru, rf, rule))


if __name__ == "__main__":
    main()
