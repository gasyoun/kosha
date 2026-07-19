"""H1264 W1c one-shot migration: in_release closed vocabulary + release_asset backfill.

Run once from the repo root: python scripts/migrate_manifest_schema.py
Idempotent: re-running after the migration is a no-op diff.
"""
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

MANIFEST = Path("data/manifest/datasets.json")
KOSHA_REPO = "https://github.com/gasyoun/kosha"

# id -> (new in_release, new release_asset, rationale) for rows needing a
# release_asset decision or a non-mechanical in_release override.
OVERRIDES = {
    "handoff-lifecycle-gold": (
        "not-applicable",
        None,
        "cross-repo pointer only -- source_repo is Uprava, not kosha; the "
        "underlying file lives at Uprava/data/handoff_lifecycle_gold.jsonl "
        "(verified: no such file exists inside kosha itself). Same pattern as "
        "indische-sprueche/dcs-grapheme-frequency et al. -- kosha never hosts "
        "or re-releases it, so 'unreleased' (which implies kosha will "
        "eventually ship it) was the wrong value. Flagged rather than left "
        "unreleased-with-a-fabricated-asset.",
    ),
    "mw-defgen-eval-sample": (
        "unreleased",
        "data/eval/defgen/frozen_sample.tsv",
        "source_repo is kosha itself; notes declare frozen_sample.tsv "
        "(+ attestations.jsonl) 'the single canonical frozen set' -- the one "
        "citable release_asset for this row.",
    ),
}


def decide_in_release(row):
    if row["id"] in OVERRIDES:
        new_val, _, _ = OVERRIDES[row["id"]]
        return new_val
    if row.get("in_release") is not None:
        return row["in_release"]  # already valid: "unreleased" or a tag
    # null -> vocabulary, decided per row from tier + source_repo (D8/W1c).
    if row.get("tier") == "public" and row.get("source_repo") == KOSHA_REPO:
        return "unreleased"
    return "not-applicable"


def decide_release_asset(row, new_in_release):
    if row["id"] in OVERRIDES:
        _, new_asset, _ = OVERRIDES[row["id"]]
        return new_asset
    return row.get("release_asset")


DATA_STATEMENT_BATCH_URL = (
    "https://github.com/gasyoun/kosha/blob/main/docs/data-statements/"
    "data-v0.2.0-batch.meta.md"
)


def main():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = data["datasets"]

    changed = []
    for row in rows:
        old_ir = row.get("in_release")
        old_ra = row.get("release_asset")
        old_ds = row.get("data_statement")
        new_ir = decide_in_release(row)
        new_ra = decide_release_asset(row, new_ir)
        row["in_release"] = new_ir
        if new_ra is not None:
            row["release_asset"] = new_ra
        # every row entering the data-v0.2.0 batch gets the consolidated
        # data statement unless it already carries its own (unconditional on
        # whether in_release/release_asset changed this run -- idempotent).
        if new_ir == "unreleased" and not row.get("data_statement"):
            row["data_statement"] = DATA_STATEMENT_BATCH_URL
        new_ds = row.get("data_statement")
        if (old_ir, old_ra, old_ds) != (new_ir, new_ra, new_ds):
            changed.append((row["id"], old_ir, new_ir, old_ra, new_ra, old_ds, new_ds))

    MANIFEST.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"{len(changed)} row(s) changed:")
    for id_, old_ir, new_ir, old_ra, new_ra, old_ds, new_ds in changed:
        print(f"  {id_}: in_release {old_ir!r} -> {new_ir!r}", end="")
        if old_ra != new_ra:
            print(f"  | release_asset {old_ra!r} -> {new_ra!r}", end="")
        if old_ds != new_ds:
            print(f"  | data_statement added", end="")
        print()

    # sanity: no null survives, vocabulary is closed
    vocab_bad = [
        r["id"]
        for r in rows
        if r.get("in_release") is None
        or (
            r["in_release"] not in ("unreleased", "not-applicable")
            and not isinstance(r["in_release"], str)
        )
    ]
    if vocab_bad:
        print("ERROR: rows outside vocabulary:", vocab_bad, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
