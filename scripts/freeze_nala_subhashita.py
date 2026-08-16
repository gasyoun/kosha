#!/usr/bin/env python3
"""H2165 — freeze export for the Nalopākhyāna + Subhāṣita-beginner course.

Pins owned assets under data/nala_subhashita/ with MANIFEST.json + sha256.
No new linguistics — copy only. Extends the H2109 freeze pattern
(scripts/freeze_cohort_start_chteniya.py is the exact template) with a
separate manifest since nala-1/2/3 + subhashita-beginner form a distinct
course, not the "Старт чтения" cohort.

Usage (from kosha root):
  python scripts/freeze_nala_subhashita.py
  python scripts/freeze_nala_subhashita.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "nala_subhashita"
BUILT = date.today().isoformat()

SOURCES = {
    "nala-1": {
        "slug": "nala-1",
        "kind": "reading_pack",
        "source_path": "reading/data/nala-1.json",
        "pin_name": "nala-1.json",
        "schema": (
            "reading_pack_v1 (sentences[].tokens[] with form/lemma/upos/morph/"
            "gloss/slp1; optional gloss_ru)"
        ),
        "adapter_note": None,
    },
    "nala-2": {
        "slug": "nala-2",
        "kind": "reading_pack",
        "source_path": "reading/data/nala-2.json",
        "pin_name": "nala-2.json",
        "schema": (
            "reading_pack_v1 (sentences[].tokens[] with form/lemma/upos/morph/"
            "gloss/slp1; optional gloss_ru)"
        ),
        "adapter_note": None,
    },
    "nala-3": {
        "slug": "nala-3",
        "kind": "reading_pack",
        "source_path": "reading/data/nala-3.json",
        "pin_name": "nala-3.json",
        "schema": (
            "reading_pack_v1 (sentences[].tokens[] with form/lemma/upos/morph/"
            "gloss/slp1; optional gloss_ru)"
        ),
        "adapter_note": None,
    },
    "subhashita-beginner": {
        "slug": "subhashita-beginner",
        "kind": "subhashita_reader_pack",
        "source_path": "data/subhashita/subhashita_beginner_pack.json",
        "pin_name": "subhashita_beginner_pack.json",
        "schema": (
            "subhashita_reader_pack (sayings[] with lines[].chunks[] tokens; "
            "NOT sentences/tokens reading_pack shape)"
        ),
        "adapter_note": (
            "Schema delta vs reading_pack_v1: top-level sayings[] not sentences[]; "
            "tokens live under lines[].chunks[] as t/lemma_slp1/gloss_ru triples; "
            "German translation_de not EN gloss. Reader wiring (H2168) must adapt "
            "or normalize — do not invent a second schema silently. Same pin content "
            "as H2109's cohort_start_chteniya freeze; pinned again here so the "
            "Nala+Subhāṣita course has one self-contained manifest (H2165 decision, "
            "logged in .ai_state.md)."
        ),
    },
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: object) -> None:
    # newline="\n" pins LF regardless of host OS, so the hash embedded in
    # MANIFEST.json can't drift when .gitattributes (eol=lf) normalizes on
    # commit (H2109/H2129 found exactly this CRLF-vs-LF sha256 mismatch gap).
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def reading_pack_gloss_note(data: dict) -> tuple[str, dict | None]:
    toks = 0
    ru = 0
    for s in data.get("sentences", []):
        for t in s.get("tokens", []):
            toks += 1
            if t.get("gloss_ru"):
                ru += 1
    note = (
        f"{ru}/{toks} tokens have gloss_ru ({100.0 * ru / toks:.1f}%)"
        if toks
        else "no tokens"
    )
    return note, data.get("stats")


def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    packs: list[dict] = []

    for meta in SOURCES.values():
        src = ROOT / meta["source_path"]
        if not src.is_file():
            raise SystemExit(f"missing source: {src}")
        dst = OUT / meta["pin_name"]
        shutil.copy2(src, dst)
        digest = sha256_file(dst)
        data = json.loads(dst.read_text(encoding="utf-8"))
        if meta["slug"] in ("nala-1", "nala-2", "nala-3"):
            gloss_note, stats = reading_pack_gloss_note(data)
        else:
            st = data.get("stats") or {}
            gloss_note = (
                f"lemma-layer RU gloss {st.get('gloss_ru_coverage_pct')}% "
                f"({st.get('gloss_ru_lemma_hit')}/{st.get('gloss_ru_tokens')} tokens); "
                f"status: {str(data.get('gloss_ru_status', ''))[:80]}"
            )
            stats = st
        packs.append(
            {
                "slug": meta["slug"],
                "kind": meta["kind"],
                "source_path": meta["source_path"],
                "pin_path": f"data/nala_subhashita/{meta['pin_name']}",
                "sha256": digest,
                "bytes": dst.stat().st_size,
                "built_source": data.get("built"),
                "schema": meta["schema"],
                "adapter_note": meta["adapter_note"],
                "gloss_ru_coverage": gloss_note,
                "stats": stats,
            }
        )
        print(f"pinned {meta['slug']} sha256={digest[:16]}…")

    manifest = {
        "id": "nala-subhashita-pack-freeze",
        "title": (
            "Nalopākhyāna + subhāṣita-beginner course pack freeze "
            "(nala-1/2/3 + subhāṣita-beginner)"
        ),
        "cohort_slug": "nala_subhashita",
        "built": BUILT,
        "handoff": "H2165",
        "executor": "Sonnet 5 (claude-sonnet-5)",
        "goal": "Pin owned packs for reader-wiring embed without new linguistics",
        "fence": (
            "No new analysis layers; no human-overlay overwrite; freeze only; "
            "no changes to underlying reading-pack JSON content"
        ),
        "consumers": [
            "H2168 Systema-Sanscriticum reader wiring "
            "(ReadingPackController multi-course multi-pack)",
        ],
        "packs": packs,
        "notes": [
            "nala-1/2/3 is the Nalopākhyāna sequence (MBh 3.50-3.52), "
            "built 13/15-07-2026, 96-99% link rate.",
            "subhashita-beginner is the same 106-saying pack already frozen "
            "under data/cohort_start_chteniya/ by H2109 — pinned again here "
            "under its own manifest so this course is self-contained; "
            "H2109's cohort_start_chteniya freeze is left untouched.",
            "Decision (per H2165 work step 3): fresh manifest, not an "
            "extension of H2109's cohort_start_chteniya/MANIFEST.json — "
            "nala+subhashita is a distinct course from the "
            '"Старт чтения" cohort (hitopadesa-0 + sandhi L1-3), so a '
            "separate freeze keeps the two courses' pin sets independently "
            "verifiable and avoids growing an unrelated manifest.",
        ],
    }
    man_path = OUT / "MANIFEST.json"
    write_json(man_path, manifest)
    return manifest


def check(manifest: dict | None = None) -> int:
    if manifest is None:
        man_path = OUT / "MANIFEST.json"
        if not man_path.is_file():
            print("FAIL: MANIFEST.json missing", file=sys.stderr)
            return 1
        manifest = json.loads(man_path.read_text(encoding="utf-8"))
    ok = True
    for p in manifest["packs"]:
        path = ROOT / p["pin_path"]
        if not path.is_file():
            print(f"FAIL missing {p['pin_path']}", file=sys.stderr)
            ok = False
            continue
        got = sha256_file(path)
        if got != p["sha256"]:
            print(f"FAIL hash {p['slug']}: got {got} expected {p['sha256']}")
            ok = False
        else:
            print(f"HASH OK {p['slug']} {p['sha256'][:16]}… ({p['bytes']} B)")
    if ok:
        print("GOAL OK — MANIFEST.json with sha256 of pinned packs validates")
        return 0
    print("GOAL FAIL", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--check",
        action="store_true",
        help="only re-verify MANIFEST sha256 (no rebuild)",
    )
    args = ap.parse_args()
    if args.check:
        return check()
    manifest = build()
    return check(manifest)


if __name__ == "__main__":
    raise SystemExit(main())
