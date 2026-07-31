"""kosha fixture profile — the compact committed source pack (W0B item 6).

The full build reads five sibling repos and a ~GB csl-sqlite extract, so until
now nothing could prove the graph end to end without a workstation that had
every feed on disk. That is why #210 survived so long: no cheap build existed
to notice that five stages never ran.

The pack under
[`tests/fixtures/build/sources/`](https://github.com/gasyoun/kosha/tree/main/tests/fixtures/build/sources)
is seven lemmas' worth of plain text — headwords, a frequency sidecar, a
Heritage crosswalk, form→lemma feeds, hand-written paradigm tables, a corpus
snippet, and three layer feeds. Every byte is written for this fixture, not
copied from a restricted upstream, so the pack carries no rights question
(D18) and can live in a public repo.

Only the csl-sqlite *cache* has to be materialized: `build_entries` reads a
per-dict SQLite file that the real build downloads from a GitHub release. This
module writes that cache from the committed `entries_<dict>.tsv` files into a
gitignored scratch directory, pinned to a `fixture-<digest>` release tag so
the source lock records something immutable rather than `latest`.
"""

from __future__ import annotations

import csv
import hashlib
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "tests" / "fixtures" / "build" / "sources"
#: Gitignored scratch: regenerable, never committed (like `data/raw_sqlite/`).
CACHE = ROOT / "data" / ".fixture-cache"

DICTS = ("mw", "pwg", "ap90")


def _pack_digest() -> str:
    """Short digest over the committed pack, used as the pinned release tag."""
    roll = hashlib.sha256()
    for path in sorted(PACK.glob("*")):
        roll.update(path.name.encode())
        roll.update(path.read_bytes())
    return roll.hexdigest()[:12]


def materialize(cache: Path | None = None) -> Path:
    """Write the csl-sqlite-shaped cache from the committed entry TSVs.

    Returns the cache root. Idempotent and deterministic: the same pack always
    produces the same rows and the same pinned tag.
    """
    cache = CACHE if cache is None else cache
    tag = f"fixture-{_pack_digest()}"
    for dict_code in DICTS:
        source = PACK / f"entries_{dict_code}.tsv"
        if not source.is_file():
            continue
        out_dir = cache / dict_code
        out_dir.mkdir(parents=True, exist_ok=True)
        db_path = out_dir / f"{dict_code}.sqlite"
        if db_path.exists():
            db_path.unlink()
        con = sqlite3.connect(db_path)
        con.execute(
            f"CREATE TABLE {dict_code} (key TEXT, lnum INTEGER, data TEXT)"
        )
        with open(source, encoding="utf-8", newline="") as handle:
            rows = [
                (row["key"], int(row["lnum"]), row["data"])
                for row in csv.DictReader(handle, delimiter="\t")
            ]
        con.executemany(f"INSERT INTO {dict_code} VALUES (?,?,?)", rows)
        con.commit()
        con.close()
        (out_dir / "RELEASE_TAG.txt").write_text(tag, encoding="utf-8")
    return cache


def fixture_env(cache: Path | None = None) -> dict[str, str]:
    """Environment overrides pointing every declared source at the pack."""
    cache = CACHE if cache is None else cache
    return {
        "KOSHA_SRC_UNION_HEADWORDS": str(PACK / "union_headwords.tsv"),
        "KOSHA_SRC_LEMMA_FREQUENCY": str(PACK / "lemma_frequency.tsv"),
        "KOSHA_SRC_HERITAGE_CROSSWALK": str(PACK / "mw_heritage_crosswalk.tsv"),
        "KOSHA_SRC_CSL_SQLITE": str(cache),
        "KOSHA_SRC_DCS_FORM2LEMMA": str(PACK / "dcs_form2lemma.tsv"),
        "KOSHA_SRC_VIDYUT_FORM2LEMMA": str(PACK / "vidyut_form2lemma.tsv"),
        "KOSHA_SRC_HERITAGE_FORMS": str(PACK / "heritage_only_forms.tsv"),
        "KOSHA_SRC_MWINFLECT_NOMINALS": str(PACK / "mwinflect_nominals.txt"),
        "KOSHA_SRC_MWINFLECT_VERBS": str(PACK / "mwinflect_verbs.txt"),
        "KOSHA_SRC_CORPUS_LEXICON": str(PACK / "corpus_lexicon.jsonl"),
        "KOSHA_SRC_SENSE_FREQUENCY": str(PACK / "sense_frequency.tsv"),
        "KOSHA_SRC_ROOTS_FREQUENCY": str(PACK / "roots_frequency.tsv"),
        "KOSHA_SRC_DICT_CORPUS_COVERAGE": str(PACK / "dict_corpus_coverage.tsv"),
        "KOSHA_SRC_MW_ROOTS": str(PACK / "mw_roots.tsv"),
        "KOSHA_SRC_MW_ETYMOLOGY": str(PACK / "mw_etymology.tsv"),
        "KOSHA_SRC_GITA_GOLD": str(ROOT / "data" / "gita" / "gita_morphology_gold.tsv"),
    }


def release_tag() -> str:
    """The pinned pseudo-release tag for the current pack contents."""
    return f"fixture-{_pack_digest()}"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    print(f"materialized fixture csl-sqlite cache at {materialize()} ({release_tag()})")
