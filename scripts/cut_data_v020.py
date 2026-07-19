"""H1264 W1c step 5: flip the 33 'unreleased' rows to data-v0.2.0 + repoint
interim_release. Run once, after migrate_manifest_schema.py, right before the
data-v0.2.0 tag/release is actually cut.
"""
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

MANIFEST = Path("data/manifest/datasets.json")
NEW_TAG = "data-v0.2.0"


def main():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = data["datasets"]

    flipped = [r["id"] for r in rows if r.get("in_release") == "unreleased"]
    for row in rows:
        if row.get("in_release") == "unreleased":
            row["in_release"] = NEW_TAG

    data["interim_release"] = f"https://github.com/gasyoun/kosha/releases/tag/{NEW_TAG}"

    MANIFEST.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"{len(flipped)} row(s) flipped to {NEW_TAG}:")
    for id_ in flipped:
        print(" ", id_)
    print("interim_release ->", data["interim_release"])


if __name__ == "__main__":
    main()
