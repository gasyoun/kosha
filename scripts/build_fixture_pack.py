"""Derive the committed fixture pack from the real source feeds.

The pack exists so the full build DAG can be run end to end — every declared
stage, from an empty database — on a machine that has none of the sibling
checkouts and none of the multi-gigabyte dumps. That is what turns "did every
stage run?" from a claim into a test
([issue #210](https://github.com/gasyoun/kosha/issues/210)).

**Derived, never hand-written.** Every row in the pack is copied verbatim out
of the real feed it stands for, so the fixtures cannot drift into a format the
builders do not actually parse — the classic way a green fixture suite stops
saying anything about production. Regenerating requires the full local source
tree; the output is committed so nobody else needs it.

    python scripts/build_fixture_pack.py            # regenerate the pack
    python scripts/build_fixture_pack.py --seeds 40 # wider slice

Seeds are chosen *from the real build's own output*: lemmas that actually
produced a natva fix, a vidyut gap-fill, a stem-bridge pair, a Heritage anchor
and entries in all three dictionaries. Picking them from the result rather than
by intuition is what makes every stage's postcondition reachable on 40 lemmas.

Licensing: the slice carries Cologne dictionary text (CC BY-SA 4.0, as the rest
of the data releases) and DCS-derived counts (CC BY). No rights-restricted feed
is sampled — `data/frequency/.cache/` (SCL, ruling N4) is not read here, and the
pack contains no SCL body text, gloss dumps or HTML.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

PACK = ROOT / "tests" / "fixtures" / "pack"
DICTS = ("mw", "pwg", "ap90")
MAX_CORPUS_LINES_PER_LEMMA = 3


def _seed_lemmas(db_path: Path, target: int) -> list[str]:
    """Pick seeds from the real database, biased to what each stage needs."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    seeds: list[str] = []

    def take(sql, params=(), limit=6):
        for row in con.execute(sql, params).fetchmany(limit):
            for value in row:
                if value and value not in seeds:
                    seeds.append(value)

    try:
        # hybrid: stems the real run actually corrected / gap-filled
        take("SELECT DISTINCT lemma_slp1 FROM inflections "
             "WHERE source='hybrid-natva-fix'", limit=5)
        take("SELECT DISTINCT lemma_slp1 FROM inflections "
             "WHERE source='vidyut-gap-fill'", limit=5)
        # stem_bridge: both spellings of a real strong/weak pair
        take("SELECT variant_slp1, canonical_slp1 FROM stem_bridge "
             "WHERE rule <> 'identity'", limit=3)
        # entries: headwords present in all three dictionaries
        take("SELECT slp1_key FROM entries GROUP BY slp1_key "
             "HAVING COUNT(DISTINCT dict) = 3 ORDER BY slp1_key", limit=8)
        # heritage: anchored, covered MW keys
        take("SELECT mw_key1 FROM heritage_anchor "
             "WHERE covered=1 AND anchor IS NOT NULL", limit=5)
        # verbs, so the verb half of the inflections ingest is exercised
        take("SELECT DISTINCT lemma_slp1 FROM inflections "
             "WHERE model LIKE 'v\\_%' ESCAPE '\\'", limit=5)
        # evidence: frequent lemmas certainly carrying a band + corpus example
        take("SELECT slp1 FROM lemmas WHERE rank_all IS NOT NULL "
             "ORDER BY rank_all LIMIT 200", limit=target)
    finally:
        con.close()
    return seeds[:target]


def _slice_tsv(source: Path, out: Path, key_columns, seeds: set[str],
               limit_per_key: int | None = None) -> int:
    """Copy the header plus every row whose key column is a seed."""
    out.parent.mkdir(parents=True, exist_ok=True)
    per_key: dict[str, int] = {}
    written = 0
    with open(source, encoding="utf-8", newline="") as src, \
            open(out, "w", encoding="utf-8", newline="") as dst:
        reader = csv.DictReader(src, delimiter="\t")
        writer = csv.DictWriter(dst, fieldnames=reader.fieldnames, delimiter="\t",
                                lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in reader:
            key = next((row.get(c) for c in key_columns if row.get(c)), None)
            if key not in seeds:
                continue
            if limit_per_key is not None:
                if per_key.get(key, 0) >= limit_per_key:
                    continue
                per_key[key] = per_key.get(key, 0) + 1
            writer.writerow(row)
            written += 1
    return written


def _slice_calc_tables(source: Path, out: Path, seeds: set[str], stem_field: int) -> int:
    """MWinflect tables are raw TSV, not DictReader-shaped: keep whole lines
    whose stem/root column (de-hyphenated, exactly as build_inflections does)
    is a seed."""
    out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(source, encoding="utf-8") as src, open(out, "w", encoding="utf-8",
                                                      newline="\n") as dst:
        for line in src:
            parts = line.rstrip("\n\r").split("\t")
            if len(parts) <= stem_field:
                continue
            if parts[stem_field].replace("-", "") in seeds:
                dst.write(line)
                written += 1
    return written


def _slice_jsonl(source: Path, out: Path, field: str, seeds: set[str],
                 limit_per_key: int) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    per_key: dict[str, int] = {}
    written = 0
    with open(source, encoding="utf-8") as src, open(out, "w", encoding="utf-8",
                                                      newline="\n") as dst:
        for line in src:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = record.get(field)
            if key not in seeds or per_key.get(key, 0) >= limit_per_key:
                continue
            per_key[key] = per_key.get(key, 0) + 1
            dst.write(line)
            written += 1
            if len(per_key) == len(seeds) and all(
                    v >= limit_per_key for v in per_key.values()):
                break
    return written


def _slice_dict_sqlite(source: Path, out: Path, dict_code: str, seeds: set[str]) -> int:
    """Copy the seed rows of one csl-sqlite dump into a miniature of itself."""
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    dst = sqlite3.connect(out)
    try:
        ddl = src.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (dict_code,)
        ).fetchone()
        if ddl is None:
            raise SystemExit(f"{source} has no table named {dict_code!r}")
        dst.execute(ddl[0])
        placeholders = ",".join("?" * len(seeds))
        rows = src.execute(
            f"SELECT key, lnum, data FROM {dict_code} WHERE key IN ({placeholders})",
            tuple(seeds),
        ).fetchall()
        dst.executemany(
            f"INSERT INTO {dict_code} (key, lnum, data) VALUES (?,?,?)", rows)
        dst.commit()
        dst.execute("VACUUM")
        dst.commit()
    finally:
        src.close()
        dst.close()
    return len(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seeds", type=int, default=40, help="how many seed lemmas")
    ap.add_argument("--db", type=Path, default=ROOT / "data" / "db" / "kosha.db",
                    help="the real database the seeds are chosen from")
    ap.add_argument("--raw-sqlite", type=Path, default=None,
                    help="csl-sqlite cache to slice (default: this checkout's "
                         "data/raw_sqlite; pass the main checkout's when running "
                         "from a worktree, where the gitignored cache is absent)")
    args = ap.parse_args()

    if not args.db.exists():
        raise SystemExit(
            f"missing {args.db}. The pack is DERIVED from a real build; "
            f"regenerate it on a machine that has one."
        )

    import build_db
    import build_db_layers
    import build_entries
    import build_evidence
    import build_forms
    import build_inflections

    seeds = _seed_lemmas(args.db, args.seeds)
    seed_set = set(seeds)
    print(f"{len(seeds)} seed lemmas: {', '.join(seeds[:12])}"
          + (" ..." if len(seeds) > 12 else ""))

    if PACK.exists():
        shutil.rmtree(PACK)
    PACK.mkdir(parents=True)

    report: dict[str, int] = {}
    overrides: dict[str, str] = {}

    def emit(key: str, rel: str, count: int) -> None:
        overrides[key] = rel
        report[rel] = count
        print(f"  {rel}: {count} row(s)")

    emit("build_db.UNION_HEADWORDS", "union_headwords.tsv",
         _slice_tsv(build_db.UNION_HEADWORDS, PACK / "union_headwords.tsv",
                    ("slp1",), seed_set))
    emit("build_db.HERITAGE_CROSSWALK", "mw_heritage_crosswalk.tsv",
         _slice_tsv(build_db.HERITAGE_CROSSWALK, PACK / "mw_heritage_crosswalk.tsv",
                    ("mw_key1",), seed_set))
    emit("build_forms.DCS_F2L", "dcs_form2lemma.tsv",
         _slice_tsv(build_forms.DCS_F2L, PACK / "dcs_form2lemma.tsv",
                    ("lemma_slp1",), seed_set))
    emit("build_forms.VIDYUT_F2L", "vidyut_form2lemma.tsv",
         _slice_tsv(build_forms.VIDYUT_F2L, PACK / "vidyut_form2lemma.tsv",
                    ("lemma_slp1",), seed_set))
    emit("build_forms.HERITAGE_F2L", "heritage_only_forms.tsv",
         _slice_tsv(build_forms.HERITAGE_F2L, PACK / "heritage_only_forms.tsv",
                    ("lemma_slp1",), seed_set))
    emit("build_inflections.DEFAULT_CALC_TABLES", "mwinflect_nominals.txt",
         _slice_calc_tables(build_inflections.DEFAULT_CALC_TABLES,
                            PACK / "mwinflect_nominals.txt", seed_set, stem_field=1))
    emit("build_inflections.DEFAULT_VERB_TABLES", "mwinflect_verbs.txt",
         _slice_calc_tables(build_inflections.DEFAULT_VERB_TABLES,
                            PACK / "mwinflect_verbs.txt", seed_set, stem_field=1))
    emit("build_evidence.CORPUS_LEXICON", "corpus_lexicon.jsonl",
         _slice_jsonl(build_evidence.CORPUS_LEXICON, PACK / "corpus_lexicon.jsonl",
                      "slp1", seed_set, MAX_CORPUS_LINES_PER_LEMMA))

    for tsv_attr, name, key in (
        ("SENSE_FREQ_TSV", "sense_frequency.tsv", "lemma_slp1"),
        ("DICT_COVERAGE_TSV", "dict_corpus_coverage.tsv", "slp1"),
    ):
        source = getattr(build_db_layers, tsv_attr)
        emit(f"build_db_layers.{tsv_attr}", name,
             _slice_tsv(source, PACK / name, (key,), seed_set))
    for tsv_attr, name, key in (
        ("MW_ROOTS_TSV", "mw_roots.tsv", "k1_slp1"),
        ("MW_ETYMOLOGY_TSV", "mw_etymology.tsv", "headword_slp1"),
    ):
        source = getattr(build_db_layers, tsv_attr)
        if source.exists():
            emit(f"build_db_layers.{tsv_attr}", name,
                 _slice_tsv(source, PACK / name, (key,), seed_set))

    raw = PACK / "raw_sqlite"
    cache = args.raw_sqlite or build_entries.DL_DIR
    for dict_code in DICTS:
        real = cache / dict_code / f"{dict_code}.sqlite"
        if not real.exists():
            raise SystemExit(
                f"missing {real}; fetch the csl-sqlite cache first, or pass "
                f"--raw-sqlite pointing at a checkout that has it")
        count = _slice_dict_sqlite(real, raw / dict_code / f"{dict_code}.sqlite",
                                   dict_code, seed_set)
        tag_src = cache / dict_code / "RELEASE_TAG.txt"
        tag = tag_src.read_text(encoding="utf-8").strip() if tag_src.exists() else "unknown"
        (raw / dict_code / "RELEASE_TAG.txt").write_text(tag + "\n", encoding="utf-8")
        report[f"raw_sqlite/{dict_code}"] = count
        print(f"  raw_sqlite/{dict_code}: {count} entry row(s) (release {tag})")
    overrides["build_entries.DL_DIR"] = "raw_sqlite"

    # Stage outputs that would otherwise land on tracked repo files during a
    # fixture build. Redirected so a fixture run leaves the working tree clean.
    overrides["build_evidence.EXAMPLES_TSV"] = "out/lemma_examples.tsv"
    overrides["build_pronoun_corrections.OUT"] = "out/pronoun_corrections.tsv"
    overrides["build_hybrid_forms.DEFAULT_OUT"] = "out"
    (PACK / "out").mkdir(exist_ok=True)
    (PACK / "out" / ".gitignore").write_text("*\n!.gitignore\n", encoding="utf-8")

    manifest = {
        "name": "fixture-pack",
        "description": (
            "Compact slice of the real source feeds, derived by "
            "scripts/build_fixture_pack.py. Drives a full from-zero build of "
            "every declared stage without the sibling checkouts."
        ),
        "seeds": seeds,
        "rows": report,
        "overrides": overrides,
    }
    (PACK / "sources.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    total = sum(p.stat().st_size for p in PACK.rglob("*") if p.is_file())
    print(f"\npack written to {PACK} — {total:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
