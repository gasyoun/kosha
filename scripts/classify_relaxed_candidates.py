#!/usr/bin/env python
"""Pre-classify the 2,171 relaxed-tier candidates quarantined by H380/Q1
(data/concordance/dict_corpus_relaxed_candidates.tsv) for the H836 human-gated
review pass (CONCORDANCE_ROADMAP Q2 Task A).

Context: the Q1 golden sample found the relaxed tier (norm()-fold: collapses
vowel length, all retroflex/nasal/sibilant consonant distinctions, and
visarga -- confirmed empirically against Unicode NFD decomposition, see
H836 build notes) semantically WRONG in 3 of 3 checks (aṃśaka/aṃsaka,
vikarṣaṇa/vikarśana, ram/rāṃ). Because form_key() (the FLOOR tier, one level
more trusted, already ASSERTED) already folds anusvāra/homorganic-nasal and
strips final visarga, every row that fell through to "relaxed" necessarily
differs from its anchor ONLY on the golden-sample's proven-risky axes
(vowel length, sibilant, or a consonant/vocalic-liquid confusion e.g. r/ṛ) --
so the honest DEFAULT classification for this whole file is "likely-spurious"
(matching the established prior), not a fresh 50/50 guess per row.

This script computes a per-row diff signature (SLP1-space, so char comparison
avoids Unicode-NFD ambiguity) and applies ONE narrow, documented exception:
a row is flagged "worth-a-closer-look" (never "likely-good" -- no row here
has earned that without human confirmation) only when the ENTIRE difference
is a single vowel-length substitution in the word-FINAL position of a
reasonably long word (>=5 chars) -- the one pattern plausibly explained by a
dictionary-citation-form vs corpus-lemma stem convention, rather than two
distinct lexemes. Every other row keeps the default.

Emits data/concordance/relaxed_candidates_classified.tsv (adds diff_axis,
n_diff_positions, pre_classification, rationale columns) for the
/review-sheet HTML generator to consume.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from concordance_core import norm, to_slp1  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent if (ROOT.parent / "SanskritLexicography").exists() else ROOT.parent.parent
UNION = GH / "SanskritLexicography" / "HeadwordLists" / "union" / "union_headwords.tsv"
RELAXED = ROOT / "data" / "concordance" / "dict_corpus_relaxed_candidates.tsv"
OUT = ROOT / "data" / "concordance" / "relaxed_candidates_classified.tsv"

VOWEL_LEN_PAIRS = {frozenset(p) for p in (("a", "A"), ("i", "I"), ("u", "U"), ("f", "F"), ("x", "X"))}
SIBILANT_PAIRS = {frozenset(p) for p in (("s", "S"), ("s", "z"), ("S", "z"))}
RETROFLEX_DENTAL_PAIRS = {frozenset(p) for p in (("t", "T"), ("d", "D"))}
NASAL_PAIRS = {frozenset(p) for p in (("n", "N"), ("n", "R"), ("n", "G"), ("n", "Y"), ("n", "M"),
                                        ("N", "R"), ("N", "G"), ("N", "Y"), ("N", "M"),
                                        ("R", "G"), ("R", "Y"), ("R", "M"), ("G", "Y"), ("G", "M"), ("Y", "M"))}
LIQUID_PAIRS = {frozenset(p) for p in (("r", "f"), ("r", "F"), ("f", "F"), ("l", "x"), ("l", "X"), ("x", "X"))}
VISARGA_PAIRS = {frozenset(p) for p in (("H", ""),)}


def classify_axis(a_ch, b_ch):
    pair = frozenset((a_ch, b_ch))
    if pair in VOWEL_LEN_PAIRS:
        return "vowel-length"
    if pair in SIBILANT_PAIRS:
        return "sibilant"
    if pair in RETROFLEX_DENTAL_PAIRS:
        return "retroflex-dental"
    if pair in NASAL_PAIRS:
        return "nasal"
    if pair in LIQUID_PAIRS:
        return "liquid-vocalic"
    return "other"


def diff_signature(a, b):
    """Align two SLP1 strings (equal length expected -- norm() is length-preserving
    modulo the diacritic fold) and return (axes, positions, n_diff)."""
    if len(a) != len(b):
        return ("length-mismatch",), [], -1
    axes = []
    positions = []
    for i, (ca, cb) in enumerate(zip(a, b)):
        if ca != cb:
            axes.append(classify_axis(ca, cb))
            positions.append(i)
    return tuple(axes), positions, len(positions)


def main():
    union_iast = {}
    with open(UNION, encoding="utf-8-sig") as f:
        header = f.readline().rstrip("\n").split("\t")
        idx = {c: i for i, c in enumerate(header)}
        for line in f:
            p = line.rstrip("\n").split("\t")
            union_iast[p[idx["slp1"]]] = p[idx["iast"]]

    rows = []
    with open(RELAXED, encoding="utf-8-sig") as f:
        header = f.readline().rstrip("\n").split("\t")
        idx = {c: i for i, c in enumerate(header)}
        for line in f:
            p = line.rstrip("\n").split("\t")
            anchor_slp1 = p[idx["anchor_key_slp1"]]
            lemma_id = p[idx["dcs_lemma_id"]]
            lemma_iast = p[idx["dcs_lemma_iast"]]
            evidence = p[idx["evidence_count"]]
            rows.append((anchor_slp1, lemma_id, lemma_iast, evidence))

    print("relaxed candidates:", len(rows))
    print("union headwords loaded:", len(union_iast))

    out_rows = []
    n_len_mismatch = 0
    n_no_union = 0
    counts = {"likely-spurious": 0, "worth-a-closer-look": 0}
    axis_counts = {}

    for anchor_slp1, lemma_id, lemma_iast, evidence in rows:
        anchor_iast = union_iast.get(anchor_slp1)
        lemma_slp1 = to_slp1(lemma_iast)
        if anchor_iast is None:
            n_no_union += 1
            anchor_iast = "(not in union — stale?)"
        axes, positions, n_diff = diff_signature(anchor_slp1, lemma_slp1)
        if n_diff < 0:
            n_len_mismatch += 1
            cls = "likely-spurious"
            rationale = "SLP1 length mismatch (anchor %r vs lemma %r) -- unexpected for the relaxed tier, flag for manual check" % (anchor_slp1, lemma_slp1)
        else:
            axis_summary = "+".join(sorted(set(axes))) if axes else "none"
            axis_counts[axis_summary] = axis_counts.get(axis_summary, 0) + 1
            word_len = max(len(anchor_slp1), len(lemma_slp1))
            is_final_single_vowel_len = (
                n_diff == 1 and axes and axes[0] == "vowel-length"
                and positions and positions[0] >= word_len - 2  # last or second-to-last char
                and word_len >= 5
            )
            if is_final_single_vowel_len:
                cls = "worth-a-closer-look"
                rationale = ("Single word-final vowel-length difference on a %d-char word "
                             "(position %d) -- the one pattern plausibly explained by a "
                             "dictionary-citation-form vs corpus-lemma stem convention rather "
                             "than two distinct lexemes; still NOT pre-approved."
                             % (word_len, positions[0]))
            else:
                cls = "likely-spurious"
                if n_diff == 0:
                    rationale = "anchor and lemma keys are SLP1-identical after transcoding (unexpected) -- check to_slp1() edge case"
                elif word_len <= 4:
                    rationale = ("Short word (%d chars) with a %s difference -- high collision "
                                 "risk, per the Q1 golden sample's confirmed pattern "
                                 "(relaxed tier wrong 3/3)." % (word_len, axis_summary))
                elif n_diff > 1:
                    rationale = ("%d differing positions (%s) -- multiple diacritic axes "
                                 "differ, consistent with two distinct lexemes." % (n_diff, axis_summary))
                else:
                    rationale = ("Single mid-word %s difference (position %d of %d) -- the exact "
                                 "axis the golden sample found semantically wrong (e.g. "
                                 "vikarṣaṇa/vikarśana)." % (axis_summary, positions[0], word_len))
        counts[cls] = counts.get(cls, 0) + 1
        axis_out = "+".join(sorted(set(axes))) if (n_diff >= 0 and axes) else ("length-mismatch" if n_diff < 0 else "none")
        pos_out = positions[0] if (n_diff >= 0 and positions) else -1
        word_len_out = max(len(anchor_slp1), len(lemma_slp1)) if n_diff >= 0 else -1
        out_rows.append((anchor_slp1, anchor_iast, lemma_id, lemma_iast, evidence, cls, rationale,
                          axis_out, n_diff, pos_out, word_len_out))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("anchor_key_slp1\tanchor_iast\tdcs_lemma_id\tdcs_lemma_iast\tevidence_count\t"
                "pre_classification\trationale\taxis\tn_diff\tfirst_diff_pos\tword_len\n")
        for r in out_rows:
            f.write("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in r) + "\n")

    print("classified:", counts)
    print("no union match (anchor not found):", n_no_union)
    print("SLP1 length mismatches:", n_len_mismatch)
    print("axis distribution:", axis_counts)
    print("wrote:", OUT)


if __name__ == "__main__":
    main()
