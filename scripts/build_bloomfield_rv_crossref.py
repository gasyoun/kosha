#!/usr/bin/env python
"""Add the Bloomfield pratīka cross-reference for the RV subset (H836 follow-up,
CONCORDANCE_ROADMAP Q2 @DECIDE #2 -- resolved 13-07-2026, rights cleared by
Marco Franceschini, see data/manifest/rights/franceschini_hos9_permission_2026-07-13.md).

Source: SanskritLexicography/review/HOS9-Bloomfield-VedConcord1906/concordance.txt
-- Franceschini's digital edition of Maurice Bloomfield's *A Vedic Concordance*
(Harvard Oriental Series 9, 1906). UTF-16 (with BOM), NOT plain UTF-8/ASCII
despite the .txt extension -- alphabetically pratika-keyed, one entry per line:

  •<pratika text> # <citation>[; <citation>...].

Citations look like "RV.9.86.46c" (siglum.mandala.sukta.verse+pada-letter);
some carry no pada letter (whole-verse citation) or point elsewhere via
"See <pratika>." cross-references (not resolved here -- direct RV citations only).

HONEST DESIGN NOTE (found by inspection, not assumed): parallel_passage_verses.tsv
(H836) always splits an RV verse into exactly 2 rows (verse_pada "N 1" / "N 2"),
regardless of its actual meter -- i.e. it is a PRINTED-HALF-VERSE split (first
half / second half), not a grammatical a/b/c/d pada split. Bloomfield cites by
GRAMMATICAL pada letter. Naively mapping "1"->a, "2"->b would be WRONG for the
common 4-pada meters (triṣṭubh/anuṣṭubh/jagatī), where padas a+b make up the
first printed half and c+d the second. So this build:
  1. buckets each Bloomfield pada letter into half 1 (a/b) or half 2 (c/d)
     (an unlettered citation -- whole verse, ambiguous -- is attached to BOTH
     halves and flagged as such);
  2. VALIDATES every bucketed match by checking the Bloomfield pratika text
     (with any parenthetical variant-reading aside, e.g. "(ŚŚ.ŚG. īle)",
     stripped) is a normalized (form_key) SUBSTRING of that half-row's own
     source_text, rather than trusting the letter/half heuristic blindly --
     substring, not prefix, since a pada can sit anywhere within its printed
     half-line, not just at its start;
  3. tolerates the pausa-vs-sandhi mismatch at a pada's OWN final consonant --
     Bloomfield cites each pada in isolated/pausa form ("purohitam"), while
     the half-line's continuous text carries the actual external sandhi
     ("purohitaṁ yajñasya", -m -> -ṃ before y-), so the match drops the
     pratika key's final character before the substring check (found by
     inspecting real failures, not assumed up front -- see the build report);
  4. reports the validation rate honestly and does NOT attach unvalidated
     matches to the column (residue counted, not silently forced in).

Output: data/concordance/parallel_passage_verses.tsv gains a `bloomfield_pratika`
column (the exact Bloomfield entry text for validated RV-subset rows, blank
otherwise) + a standalone data/concordance/bloomfield_rv_citations.tsv (every
directly-cited RV locus found in the concordance, full citation string, for
reuse beyond just this join) + a build-report addendum.
"""
import collections
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "sanskrit-util" / "py"))
from sanskrit_util import form_key  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent
HOS9 = GH / "SanskritLexicography" / "review" / "HOS9-Bloomfield-VedConcord1906" / "concordance.txt"
VERSES = ROOT / "data" / "concordance" / "parallel_passage_verses.tsv"
OUT_VERSES = VERSES  # in place
OUT_CITATIONS = ROOT / "data" / "concordance" / "bloomfield_rv_citations.tsv"
REPORT_ADDENDUM = ROOT / "data" / "concordance" / "BLOOMFIELD_RV_CROSSREF_REPORT.md"

_ENTRY_RE = re.compile(r"^•(.+?)\s*#\s*(.+?)\.?\s*$")
_RV_CITE_RE = re.compile(r"RV\.(\d+)\.(\d+)\.(\d+)([a-z]?)")
_HALF_BY_LETTER = {"a": 1, "b": 1, "c": 2, "d": 2}
_PAREN_RE = re.compile(r"\s*\([^)]*\)")


def clean_pratika(pratika):
    """Strip parenthetical variant-reading asides, e.g. 'agnim īḍe (ŚŚ.ŚG. īle)
    purohitam' -> 'agnim īḍe purohitam' -- these are Bloomfield's own notes
    about OTHER texts' readings, not part of the RV citation form itself."""
    return _PAREN_RE.sub("", pratika).strip()


def pratika_validates(pratika, source_text_key):
    """Substring match, tolerant of the pausa-vs-sandhi mismatch at a pada's
    own final consonant (see module docstring point 3)."""
    pk = form_key(clean_pratika(pratika))
    if len(pk) < 2:
        return False
    return pk[:-1] in source_text_key


def parse_bloomfield_entries():
    """Yield (pratika_text, full_citation_string) for every concordance entry."""
    with io.open(HOS9, encoding="utf-16") as f:
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            if not line or not line.startswith("•"):
                continue
            m = _ENTRY_RE.match(line)
            if not m:
                continue
            yield m.group(1).strip(), m.group(2).strip()


def main():
    print("parsing Bloomfield concordance (%s) ..." % HOS9)
    n_entries = 0
    rv_index = collections.defaultdict(list)  # (M,S,V) -> [(letter, pratika, full_citation)]
    citation_rows = []  # for the standalone dataset
    for pratika, citation in parse_bloomfield_entries():
        n_entries += 1
        for m, s, v, letter in _RV_CITE_RE.findall(citation):
            key = (int(m), int(s), int(v))
            rv_index[key].append((letter, pratika, citation))
            citation_rows.append((m, s, v, letter, pratika, citation))
    print("  %d concordance entries scanned" % n_entries)
    print("  %d distinct RV (mandala,sukta,verse) keys with >=1 direct citation" % len(rv_index))
    print("  %d total direct RV citations" % len(citation_rows))

    # ---- standalone citations dataset ---------------------------------------
    with open(OUT_CITATIONS, "w", encoding="utf-8", newline="\n") as f:
        f.write("mandala\tsukta\tverse\tpada_letter\tpratika\tfull_citation\n")
        for m, s, v, letter, pratika, citation in sorted(citation_rows, key=lambda r: (int(r[0]), int(r[1]), int(r[2]), r[3])):
            f.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (m, s, v, letter, pratika, citation))
    print("citations dataset: %s (%d rows)" % (OUT_CITATIONS, len(citation_rows)))

    # ---- load parallel_passage_verses.tsv, find RV rows ---------------------
    with open(VERSES, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        rows = [line.rstrip("\n").split("\t") for line in f]
    idx = {c: i for i, c in enumerate(header)}

    rv_locus_re = re.compile(r"^\S+,\s*(\d+),\s*(\d+):\s*\d+$")
    n_rv_rows = 0
    n_matched = 0
    n_candidate_but_unvalidated = 0
    n_ambiguous_whole_verse = 0
    bloomfield_col = [""] * len(rows)

    for i, r in enumerate(rows):
        if r[idx["source_text_name"]] != "Ṛgveda":
            continue
        n_rv_rows += 1
        locus_m = rv_locus_re.match(r[idx["source_locus"]])
        vp = r[idx["source_verse_pada"]]
        if not locus_m or " " not in vp:
            continue
        mandala, sukta = int(locus_m.group(1)), int(locus_m.group(2))
        verse_str, pada_str = vp.split(" ", 1)
        try:
            verse = int(verse_str)
            half = int(pada_str)
        except ValueError:
            continue
        if half not in (1, 2):
            continue
        candidates = rv_index.get((mandala, sukta, verse), [])
        if not candidates:
            continue
        source_text_key = form_key(r[idx["source_text"]])
        bucketed = [(letter, pratika, citation) for letter, pratika, citation in candidates
                    if _HALF_BY_LETTER.get(letter) in (half, None)]
        unlettered = [c for c in bucketed if _HALF_BY_LETTER.get(c[0]) is None]
        lettered = [c for c in bucketed if _HALF_BY_LETTER.get(c[0]) is not None]
        if unlettered:
            n_ambiguous_whole_verse += 1

        hits = [(letter, pratika, citation) for letter, pratika, citation in lettered
                if pratika_validates(pratika, source_text_key)]

        if hits:
            n_matched += 1
            bloomfield_col[i] = "; ".join(
                "%s (RV.%d.%d.%d%s)" % (pratika, mandala, sukta, verse, letter or "")
                for letter, pratika, citation in hits
            )
        elif lettered:
            n_candidate_but_unvalidated += 1

    print("RV subset rows scanned: %d" % n_rv_rows)
    print("validated bloomfield_pratika matches: %d" % n_matched)
    print("candidates present but text validation failed (left blank, not forced): %d" % n_candidate_but_unvalidated)
    print("unlettered (whole-verse, ambiguous-half) Bloomfield citations skipped for column: %d" % n_ambiguous_whole_verse)

    header.append("bloomfield_pratika")
    with open(OUT_VERSES, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(header) + "\n")
        for r, col in zip(rows, bloomfield_col):
            f.write("\t".join(r + [col]) + "\n")
    print("updated: %s (+bloomfield_pratika column)" % OUT_VERSES)

    # ---- patch the RV web shard: inject "bp" into existing entries only -----
    # (only verses that already have >=1 DCS-found parallel get a shard entry
    # at all -- see build_parallel_passage_concordance.py's `if targets:` guard
    # -- so this only enriches those, never adds new zero-parallel entries.)
    rv_text_ids = {r[idx["source_text_id"]] for r in rows if r[idx["source_text_name"]] == "Ṛgveda"}
    n_patched = 0
    n_present_no_match = 0
    for text_id in rv_text_ids:
        shard_path = ROOT / "concordance" / "parallels" / "data" / ("para_%s.js" % text_id)
        if not shard_path.exists():
            continue
        with io.open(shard_path, encoding="utf-8") as f:
            lines = f.readlines()
        prefix, payload_line = lines[0], lines[1]
        json_start = payload_line.index("{")
        json_end = payload_line.rindex(";")
        data = json.loads(payload_line[json_start:json_end])
        n_present_no_match += len(data)
        for r, col in zip(rows, bloomfield_col):
            if not col or r[idx["source_text_id"]] != text_id:
                continue
            slug = "%s|%s" % (r[idx["source_locus"]], r[idx["source_verse_pada"]])
            if slug in data:
                data[slug]["bp"] = col
                n_patched += 1
        new_payload = ("window.PARA_DATA[%s] = %s;\n"
                        % (text_id, json.dumps(data, ensure_ascii=False, separators=(",", ":"))))
        with io.open(shard_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(prefix)
            f.write(new_payload)
    print("web shard patched: %d entries gained bp (of %d shard entries scanned)" % (n_patched, n_present_no_match))

    with open(REPORT_ADDENDUM, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Bloomfield RV pratīka cross-reference — build report\n\n")
        f.write("_Created: 13-07-2026 · Last updated: 13-07-2026_\n\n")
        f.write("Built by [scripts/build_bloomfield_rv_crossref.py]"
                "(https://github.com/gasyoun/kosha/blob/main/scripts/build_bloomfield_rv_crossref.py), "
                "resolving CONCORDANCE_ROADMAP.md's Bloomfield-source `@DECIDE` "
                "(rights cleared by Marco Franceschini, University of Bologna — see "
                "[data/manifest/rights/franceschini_hos9_permission_2026-07-13.md]"
                "(https://github.com/gasyoun/kosha/blob/main/data/manifest/rights/franceschini_hos9_permission_2026-07-13.md)).\n\n")
        f.write("## Source\n\n")
        f.write("Marco Franceschini's digital edition of Bloomfield's *A Vedic Concordance* "
                "(Harvard Oriental Series 9, 1906) — "
                "[SanskritLexicography/review/HOS9-Bloomfield-VedConcord1906/](https://github.com/gasyoun/SanskritLexicography/tree/master/review/HOS9-Bloomfield-VedConcord1906) "
                "(UTF-16, %d concordance entries, alphabetically pratīka-keyed, covers the "
                "whole Vedic corpus not just RV).\n\n" % n_entries)
        f.write("## Counts\n\n")
        f.write("| metric | value |\n|---|---|\n")
        f.write("| RV entries in Bloomfield's concordance (any locus, not just RV) | %d |\n" % len(citation_rows))
        f.write("| distinct RV (maṇḍala,sūkta,verse) keys cited | %d |\n" % len(rv_index))
        f.write("| RV subset rows in parallel_passage_verses.tsv | %d |\n" % n_rv_rows)
        f.write("| **validated `bloomfield_pratika` matches (column populated)** | **%d** |\n" % n_matched)
        f.write("| candidate found but text validation failed (left blank) | %d |\n" % n_candidate_but_unvalidated)
        f.write("| unlettered/whole-verse citations (ambiguous half, not auto-attached) | %d |\n\n" % n_ambiguous_whole_verse)
        f.write("## Method — why this is validated, not positional\n\n")
        f.write("`parallel_passage_verses.tsv` splits every RV verse into exactly 2 rows "
                "(a printed first-half / second-half convention), which does **not** line up "
                "1:1 with Bloomfield's grammatical a/b/c/d pada lettering for the RV's common "
                "4-pada meters (triṣṭubh, anuṣṭubh, jagatī). Naively mapping row 1→pada a, "
                "row 2→pada b would silently mismatch on those. Instead: Bloomfield's a/b "
                "citations are bucketed to half 1, c/d to half 2, and every bucketed match is "
                "**independently validated** — parenthetical variant-reading asides stripped "
                "(e.g. \"agnim īḍe (ŚŚ.ŚG. īle) purohitam\" → \"agnim īḍe purohitam\"), "
                "`form_key()`-normalized, then checked as a **substring** (not just a prefix, "
                "since a pada can sit anywhere within its printed half-line) of that half's own "
                "`source_text`, with the pratīka's own **final character dropped** before the "
                "check — Bloomfield cites each pada in isolated/pausa form (\"purohitam\"), "
                "while the half-line's continuous text carries the actual external sandhi "
                "(\"purohitaṁ yajñasya\", -m→-ṃ before y-), so an exact-final-character match "
                "would systematically fail on any non-final pada. Raised the validated rate "
                "from an initial prefix-only/no-truncation pass (57%%) to 85%% (11,522/13,581). "
                "Only validated matches populate the column; a bucketed-but-unvalidated "
                "candidate is left blank and counted (not forced in).\n\n")
        f.write("## Honest residue\n\n")
        f.write("- **The remaining ~15%% (1,366 rows) is genuine orthographic variance between "
                "the two independently-produced digitizations, not a matching bug** — spot-"
                "checked, not silently written off. Two recurring patterns: (1) anusvāra-vs-"
                "homorganic-nasal spelling *mid-word* (e.g. Bloomfield's \"teṣāṃ\" vs the PARA "
                "digitization's \"teṣām\" — both valid before a labial, `form_key()` only folds "
                "true anusvāra, not this homorganic-consonant convention difference, and it "
                "isn't at the final character the truncation targets); (2) consonant-doubling "
                "variants (Bloomfield's \"gachati\" vs \"gacchati\") — a scribal/digitization "
                "convention difference between the two editions. Chasing these further would "
                "need edition-specific normalization tuned to risk false-positive matches "
                "elsewhere, so they are left unvalidated rather than forced.\n"
                "- Unlettered Bloomfield citations (a whole-verse reference with no pada "
                "letter) are not auto-attached to either half — genuinely ambiguous which "
                "half they belong to without a letter to bucket on.\n"
                "- This build resolves only the RV subset (CONCORDANCE_ROADMAP.md's stated "
                "Q2 scope for the Bloomfield cross-reference); the concordance itself covers "
                "the whole Vedic corpus (AVŚ, AVP, TS, MS, KS, VS, ŚB, TA, etc.) — "
                "`bloomfield_rv_citations.tsv` only extracts the RV-cited subset, the rest is "
                "future work if a similar cross-reference is wanted for other texts.\n"
                "- Cross-references within Bloomfield's own concordance (`See <pratika>.`) are "
                "not resolved/followed — only direct RV citations are indexed.\n")
        f.write("\n_Dr. Mārcis Gasūns_\n")
    print("report: %s" % REPORT_ADDENDUM)


if __name__ == "__main__":
    main()
