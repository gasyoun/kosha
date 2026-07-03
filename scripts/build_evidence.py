"""kosha P3 -- evidence layer: frequency band + one corpus example per lemma.

IMPLEMENTATION_PLAN.md P3 originally specced a new `evidence` table, but by
03-07-2026 the frequency signal it needed (count_all, grammar_all, rank_all,
periods, periods_sum, coverage_pct, core_rank) was already LEFT-JOINed onto
`lemmas` by build_db.py's build_lemmas(). This module builds on those existing
columns instead of duplicating them, and adds only the two things that were
genuinely missing:

  1. `band` (1-5) -- a coarse, display-facing bucket over `rank_all`, answering
     "what should a second-year student memorise vs. look up and forget".
  2. one corpus example per LEMMA (not per sense -- see "Scope note" below):
     a Sanskrit citation + aligned Russian translation, sourced from
     SanskritLexicography/RussianTranslation/src/corpus_lexicon.jsonl (the
     sibling repo's pwg_ru Phase 4 aligned corpus, 1,091,528 rows).

Run standalone or via build_db.py --stage evidence:

    python scripts/build_evidence.py

Additive-only: adds nullable columns to `lemmas` via ALTER TABLE (migrated
in build_db.py's connect(), mirroring the H111 forms.category migration), and
UPDATEs them. Never touches entries/senses/forms.

## Band thresholds (design decision, reasoned here)

Sanskrit corpus frequency is sharply Zipfian: D5's static-cache measurement
(D5_MEASUREMENTS.md, KOSHA_DECISIONS_NEEDED.md D5-3) found the top 10,000
count_all-ranked lemmas already cover 95.4% of all corpus token mass out of
323,425 spine lemmas. So a small number of high-rank lemmas dominates real
reading; the tail is enormous but individually rare. Bands are drawn on
`rank_all` (dense rank over count_all desc, falling back to periods_sum rank
for lemmas without a count_all row per data/frequency/README.md) with cut
points chosen to track that curve, not evenly-spaced buckets over rank number:

  Band 1 "core -- memorise"       rank_all <= 500     (493 lemmas measured)
      The absolute high-frequency core: pronouns, particles, the handful of
      constant nouns/verbs a reader meets in the first paragraph of anything.
  Band 2 "frequent -- learn early" 500 < rank_all <= 2,000 (+1,441 lemmas)
      Still near-guaranteed to recur within a page or two of intermediate
      reading.
  Band 3 "common -- recognise"    2,000 < rank_all <= 10,000 (+7,484 lemmas)
      Together bands 1-3 close out at rank 10,000, i.e. the D5-measured
      95.4%-of-token-mass cutoff: past this point a lemma stops being
      "recognise on sight" and becomes "look up, but it's attested".
  Band 4 "attested -- look up"    rank_all > 10,000 (any rank; ~51,341 lemmas)
      Real corpus attestation exists (DCS saw it), but it is long-tail rare;
      not worth active memorisation.
  Band 5 "unattested -- dictionary-only" rank_all IS NULL (~262,085 lemmas)
      No DCS corpus signal at all under the current archive.sqlite M9 import
      (data/frequency/README.md: 73.7% overlap by key). This is NOT "rank
      zero" or "never occurs in Sanskrit" -- it means this specific DCS
      snapshot never attested it; fail-closed per EVAL_PLAN.md rule 4 (no
      fabricated numeric placeholder).

These thresholds are a judgment call, not derived from an external gold
standard; they are recorded here (not in a tunable config) so a future
session changing them does so visibly, per EVAL_PLAN.md rule 3's spirit.

## Scope note: per-lemma, not per-sense

corpus_lexicon.jsonl is a word-aligned corpus feed keyed by SLP1 **surface
form** (`slp1` field, e.g. "hvayatAm", an inflected form of "hvA"), not by
lemma and not by dictionary sense. There is no sense-level tagging in the
feed at all -- P3's "one corpus example per sense" is infeasible within this
sidecar's scope; examples are attached per LEMMA via the existing `forms`
table's form_slp1 -> lemma_slp1 join (same join pattern build_forms.py uses),
picking the first `kind='translation'` row encountered in file order for a
form that maps to that lemma, falling back to `kind='commentary'` if no
translation-kind row exists. This is stated explicitly rather than silently
downgrading the P3 bullet: examples ship per-lemma.

Ambiguous forms (a form_slp1 with >1 candidate lemma_slp1 in `forms`, e.g.
"Darma" -> {Darma, Darman}) attach the same example row to every candidate
lemma -- correct with respect to "this token is textual evidence this word
is used", not a claim the alignment disambiguated the specific lemma.
"""
import csv
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SIBLING = ROOT.parent
CORPUS_LEXICON = (
    SIBLING / "SanskritLexicography" / "RussianTranslation" / "src" / "corpus_lexicon.jsonl"
)
EVIDENCE_DIR = ROOT / "data" / "evidence"
EXAMPLES_TSV = EVIDENCE_DIR / "lemma_examples.tsv"

SOURCE_BAND = "kosha frequency layer, rank_all (DCS archive.sqlite M9 via VisualDCS)"
SOURCE_FREQ = "DCS archive.sqlite M9 (VisualDCS)"
SOURCE_EXAMPLE = "corpus_lexicon.jsonl (pwg_ru Phase 4, SanskritLexicography/RussianTranslation)"

BAND_LABELS = {
    1: "core -- memorise",
    2: "frequent -- learn early",
    3: "common -- recognise",
    4: "attested -- look up",
    5: "unattested -- dictionary-only (no DCS corpus signal)",
}

_ERA_PREFIX = re.compile(r"^\s*\d+\s*")


def frequency_band(rank_all) -> int:
    """Map rank_all (int or None) to a 1-5 display band. See module docstring
    "Band thresholds" for the reasoning behind these cut points."""
    if rank_all is None:
        return 5
    if rank_all <= 500:
        return 1
    if rank_all <= 2000:
        return 2
    if rank_all <= 10000:
        return 3
    return 4


def first_era(periods: str):
    """`periods` is a pipe-joined, chronological `N label=count` vector
    (data/frequency/README.md). The first segment is the earliest era with a
    nonzero attestation count. Returns None if `periods` is empty/None --
    never fabricates an era for a lemma with no period data."""
    if not periods:
        return None
    first_segment = periods.split("|", 1)[0]
    label = first_segment.split("=", 1)[0]
    return _ERA_PREFIX.sub("", label).strip() or None


def ensure_columns(con):
    cols = {row[1] for row in con.execute("PRAGMA table_info(lemmas)")}
    add = []
    if "band" not in cols:
        add.append("ALTER TABLE lemmas ADD COLUMN band INTEGER")
    if "first_era" not in cols:
        add.append("ALTER TABLE lemmas ADD COLUMN first_era TEXT")
    if "example_slp1" not in cols:
        add.append("ALTER TABLE lemmas ADD COLUMN example_slp1 TEXT")
    if "example_sa" not in cols:
        add.append("ALTER TABLE lemmas ADD COLUMN example_sa TEXT")
    if "example_ru" not in cols:
        add.append("ALTER TABLE lemmas ADD COLUMN example_ru TEXT")
    if "example_work" not in cols:
        add.append("ALTER TABLE lemmas ADD COLUMN example_work TEXT")
    if "example_passage" not in cols:
        add.append("ALTER TABLE lemmas ADD COLUMN example_passage TEXT")
    if "example_kind" not in cols:
        add.append("ALTER TABLE lemmas ADD COLUMN example_kind TEXT")
    for stmt in add:
        con.execute(stmt)
    if add:
        con.commit()


def build_bands(con):
    rows = con.execute("SELECT slp1, rank_all FROM lemmas").fetchall()
    updates = [(frequency_band(r["rank_all"]), r["slp1"]) for r in rows]
    con.executemany("UPDATE lemmas SET band=? WHERE slp1=?", updates)
    con.commit()

    era_rows = con.execute("SELECT slp1, periods FROM lemmas WHERE periods IS NOT NULL").fetchall()
    era_updates = [(first_era(r["periods"]), r["slp1"]) for r in era_rows]
    con.executemany("UPDATE lemmas SET first_era=? WHERE slp1=?", era_updates)
    con.commit()

    band_counts = {n: 0 for n in range(1, 6)}
    for r in con.execute("SELECT band, COUNT(*) c FROM lemmas GROUP BY band"):
        band_counts[r["band"]] = r["c"]
    print(f"[P3] band distribution: {band_counts}")
    return band_counts


def _load_form_to_lemmas(con):
    """form_slp1 -> set(lemma_slp1), from the existing `forms` table (H111's
    dcs/vidyut/heritage witnesses). Union of all sources -- for "does this
    token belong to lemma X", source trust ordering doesn't matter (it only
    matters for authoritativeness of the grammatical claim itself)."""
    idx = {}
    for r in con.execute("SELECT DISTINCT form_slp1, lemma_slp1 FROM forms"):
        idx.setdefault(r["form_slp1"], set()).add(r["lemma_slp1"])
    return idx


def build_examples(con):
    if not CORPUS_LEXICON.exists():
        print(f"[P3] WARNING: corpus feed missing at {CORPUS_LEXICON} -- skipping examples")
        return {}

    form_to_lemmas = _load_form_to_lemmas(con)
    known_lemmas = {r["slp1"] for r in con.execute("SELECT slp1 FROM lemmas")}

    # lemma_slp1 -> best example row found so far. Priority: kind='translation'
    # beats 'commentary'; within the same kind, first occurrence in file order
    # wins (deterministic given a fixed input file).
    best = {}  # lemma_slp1 -> (priority, dict)

    n_rows = 0
    with open(CORPUS_LEXICON, encoding="utf-8") as f:
        for line in f:
            n_rows += 1
            row = json.loads(line)
            form = row.get("slp1")
            if not form:
                continue
            lemmas = form_to_lemmas.get(form)
            if not lemmas:
                continue
            priority = 1 if row.get("kind") == "translation" else 0
            for lemma in lemmas:
                if lemma not in known_lemmas:
                    continue
                cur = best.get(lemma)
                if cur is not None and cur[0] >= priority:
                    continue
                best[lemma] = (priority, {
                    "example_slp1": form,
                    "example_sa": row.get("sa"),
                    "example_ru": row.get("ru"),
                    "example_work": row.get("work"),
                    "example_passage": row.get("passage"),
                    "example_kind": row.get("kind"),
                })

    print(f"[P3] scanned {n_rows} corpus_lexicon.jsonl rows, "
          f"found examples for {len(best)} lemmas")

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    with open(EXAMPLES_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["lemma_slp1", "example_slp1", "example_sa", "example_ru",
                    "example_work", "example_passage", "example_kind"])
        for lemma in sorted(best):
            e = best[lemma][1]
            w.writerow([lemma, e["example_slp1"], e["example_sa"], e["example_ru"],
                        e["example_work"], e["example_passage"], e["example_kind"]])

    updates = []
    for lemma, (_, e) in best.items():
        updates.append((e["example_slp1"], e["example_sa"], e["example_ru"],
                         e["example_work"], e["example_passage"], e["example_kind"], lemma))
    con.executemany(
        "UPDATE lemmas SET example_slp1=?, example_sa=?, example_ru=?, "
        "example_work=?, example_passage=?, example_kind=? WHERE slp1=?",
        updates,
    )
    con.commit()
    return best


def build_evidence(con):
    ensure_columns(con)
    band_counts = build_bands(con)
    examples = build_examples(con)
    return band_counts, examples


if __name__ == "__main__":
    db_path = ROOT / "data" / "db" / "kosha.db"
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    build_evidence(con)
    con.close()
