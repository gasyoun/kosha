"""Rung B1 demo — one-rung proof of the kosha->Systema last-mile pipeline.

Emits `kosha-srs-deck-b1-demo`: a frequency-ordered SRS deck of the CONTENT
words in the existing Nala-1 reading pack (reading/data/nala-1.json), per
LAST_MILE_PIPELINE_SPEC.md Hop B + section 4 (demo path). Function words
(grammar_all in {ind, pron}) are stripped per the wave-1a finding
(DIFFICULTY_ORDERING_RESULT.md); deck is core_rank-ordered.

Scope note: this is a ONE-VERSE-SET demo artifact, not the general-purpose
vocabulary curriculum (that is H947's scope, kosha-side, fenced off in its
own handoff). Deliberately narrow so it does not duplicate that in-flight work.
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "sanskrit-util" / "py"))
from sanskrit_util import from_slp1, slp1_to_devanagari  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
READING_PACK = ROOT / "reading" / "data" / "nala-1.json"
FREQUENCY_TSV = ROOT / "data" / "frequency" / "lemma_frequency.tsv"
OUT_DIR = ROOT / "data" / "srs"
OUT_PATH = OUT_DIR / "srs-deck-b1-demo.json"

FUNCTION_WORD_GRAMMAR = {"ind", "pron"}


def load_frequency() -> dict[str, dict]:
    table: dict[str, dict] = {}
    with FREQUENCY_TSV.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            slp1 = row.get("lemma_slp1", "")
            if slp1:
                table[slp1] = row
    return table


def load_reading_pack() -> dict:
    return json.loads(READING_PACK.read_text(encoding="utf-8"))


def first_gloss(gloss_field: str) -> str:
    # gloss field is a "; "-joined sense list; the first sense is the display gloss.
    return gloss_field.split(";")[0].strip() if gloss_field else ""


def build() -> dict:
    freq = load_frequency()
    pack = load_reading_pack()

    seen_slp1: set[str] = set()
    rows: list[dict] = []
    total_tokens = 0
    skipped_no_slp1 = 0
    skipped_duplicate = 0
    skipped_function_words = 0
    skipped_no_frequency = 0
    skipped_no_core_rank = 0

    for sentence in pack["sentences"]:
        for token in sentence["tokens"]:
            total_tokens += 1
            slp1 = token.get("slp1", "")
            if not slp1:
                skipped_no_slp1 += 1
                continue
            if slp1 in seen_slp1:
                skipped_duplicate += 1
                continue
            freq_row = freq.get(slp1)
            if freq_row is None:
                skipped_no_frequency += 1
                continue
            if freq_row.get("grammar_all", "") in FUNCTION_WORD_GRAMMAR:
                skipped_function_words += 1
                continue
            core_rank_raw = freq_row.get("core_rank", "")
            if not core_rank_raw:
                # not in the core vocabulary spine (wave-1a: core_rank already
                # excludes function words + long-tail rarities) — skip for the
                # demo deck, matches the W1b fence (core_rank-spined only).
                skipped_no_core_rank += 1
                continue
            seen_slp1.add(slp1)
            rows.append(
                {
                    "rank": int(core_rank_raw),
                    "slp1": slp1,
                    "deva": slp1_to_devanagari(slp1),
                    "iast": from_slp1(slp1),
                    "gloss": first_gloss(token.get("gloss", "")),
                }
            )

    rows.sort(key=lambda r: r["rank"])

    return {
        "id": "kosha-srs-deck-b1-demo",
        "source_reading_pack": "nala-1",
        "method": "core_rank-ordered, function words (grammar_all in ind/pron) stripped — wave-1a method",
        "stats": {
            "total_tokens": total_tokens,
            "cards": len(rows),
            "skipped_no_slp1": skipped_no_slp1,
            "skipped_duplicate": skipped_duplicate,
            "skipped_function_words": skipped_function_words,
            "skipped_no_frequency": skipped_no_frequency,
            "skipped_no_core_rank": skipped_no_core_rank,
        },
        "cards": rows,
    }


def main() -> None:
    deck = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(deck, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH} — {deck['stats']}")


if __name__ == "__main__":
    main()
