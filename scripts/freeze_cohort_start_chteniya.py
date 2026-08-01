#!/usr/bin/env python3
"""H2109 — freeze export for «Старт чтения» cohort packs.

Pins owned assets under data/cohort_start_chteniya/ with MANIFEST.json + sha256.
No new linguistics — copy + lesson-filtered subset only.

Usage (from kosha root):
  python scripts/freeze_cohort_start_chteniya.py
  python scripts/freeze_cohort_start_chteniya.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "cohort_start_chteniya"
BUILT = date.today().isoformat()

SOURCES = {
    "hitopadesa-0": {
        "slug": "hitopadesa-0",
        "kind": "reading_pack",
        "source_path": "reading/data/hitopadesa-0.json",
        "pin_name": "hitopadesa-0.json",
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
            "German translation_de not EN gloss. Systema import (H2110) must adapt "
            "or normalize — do not invent a second schema silently."
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
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def walk_dicts(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk_dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_dicts(v)


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
        if meta["slug"] == "hitopadesa-0":
            toks = 0
            ru = 0
            for s in data.get("sentences", []):
                for t in s.get("tokens", []):
                    toks += 1
                    if t.get("gloss_ru"):
                        ru += 1
            gloss_note = (
                f"{ru}/{toks} tokens have gloss_ru ({100.0 * ru / toks:.1f}%)"
                if toks
                else "no tokens"
            )
            stats = data.get("stats")
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
                "pin_path": f"data/cohort_start_chteniya/{meta['pin_name']}",
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

    # sandhi drills L1–3
    drills_src = ROOT / "data/sandhi/sandhi_drills.json"
    drills = json.loads(drills_src.read_text(encoding="utf-8"))
    items = [it for it in drills["items"] if int(it.get("lesson", 0)) <= 3]
    if not items:
        raise SystemExit("no sandhi drills for lessons 1-3")
    bl = Counter(int(it["lesson"]) for it in items)
    bt = Counter(it.get("type") for it in items)
    subset = {
        "title": "Sandhi drills — lessons 1–3 (cohort «Старт чтения» freeze)",
        "description": (
            "Subset of data/sandhi/sandhi_drills.json restricted to curriculum "
            "lessons 1–3 (beginner band for 5-week pilot). No new items authored."
        ),
        "source": {
            **(drills.get("source") or {}),
            "parent": "data/sandhi/sandhi_drills.json",
            "parent_sha256": sha256_file(drills_src),
            "lesson_max": 3,
            "freeze": "cohort_start_chteniya",
            "handoff": "H2109",
        },
        "item_types": drills.get("item_types"),
        "stats": {
            "items": len(items),
            "by_lesson": {str(k): bl[k] for k in sorted(bl)},
            "by_type": dict(bt),
        },
        "items": items,
    }
    drills_dst = OUT / "sandhi_drills_l1_l3.json"
    write_json(drills_dst, subset)
    packs.append(
        {
            "slug": "sandhi-drills-l1-l3",
            "kind": "sandhi_drills_subset",
            "source_path": "data/sandhi/sandhi_drills.json",
            "pin_path": "data/cohort_start_chteniya/sandhi_drills_l1_l3.json",
            "sha256": sha256_file(drills_dst),
            "bytes": drills_dst.stat().st_size,
            "built_source": (drills.get("source") or {}).get("built"),
            "schema": "sandhi_drills items[] filtered lesson<=3 (join/split/identify MCQ)",
            "adapter_note": None,
            "gloss_ru_coverage": "n/a (drill bank, not glossed reading)",
            "stats": subset["stats"],
        }
    )
    print(f"pinned sandhi drills L1-3 n={len(items)}")

    # sandhi curriculum L1–3
    cur_src = ROOT / "data/sandhi/sandhi_curriculum.tsv"
    cur_lines = cur_src.read_text(encoding="utf-8").splitlines()
    header = cur_lines[0]
    kept = [header]
    for line in cur_lines[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        try:
            lesson = int(parts[-1])
        except ValueError:
            continue
        if lesson <= 3:
            kept.append(line)
    cur_dst = OUT / "sandhi_curriculum_l1_l3.tsv"
    cur_dst.write_text("\n".join(kept) + "\n", encoding="utf-8")
    packs.append(
        {
            "slug": "sandhi-curriculum-l1-l3",
            "kind": "sandhi_curriculum_subset",
            "source_path": "data/sandhi/sandhi_curriculum.tsv",
            "pin_path": "data/cohort_start_chteniya/sandhi_curriculum_l1_l3.tsv",
            "sha256": sha256_file(cur_dst),
            "bytes": cur_dst.stat().st_size,
            "built_source": None,
            "schema": "sandhi_curriculum.tsv rows with lesson<=3",
            "adapter_note": None,
            "gloss_ru_coverage": "n/a",
            "stats": {"rules": len(kept) - 1, "lessons": "1-3"},
        }
    )
    print(f"pinned sandhi curriculum L1-3 rules={len(kept) - 1}")

    # optional lemma TSV
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()

    hito = json.loads((OUT / "hitopadesa-0.json").read_text(encoding="utf-8"))
    for s in hito.get("sentences", []):
        n = s.get("n")
        for t in s.get("tokens", []):
            lemma = (t.get("lemma") or t.get("slp1") or "").strip()
            if not lemma:
                continue
            form = (t.get("form") or "").strip()
            gr = t.get("gloss_ru")
            if isinstance(gr, dict):
                gloss = gr.get("lemma") or gr.get("surface") or ""
            else:
                gloss = gr or t.get("gloss") or ""
            key = ("hitopadesa-0", lemma)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "pack": "hitopadesa-0",
                    "lemma_slp1": lemma,
                    "surface": form,
                    "gloss_ru": gloss if isinstance(gloss, str) else "",
                    "gloss_en": t.get("gloss") or "",
                    "locus": str(n) if n is not None else "",
                }
            )

    def as_str(val) -> str:
        if val is None:
            return ""
        if isinstance(val, str):
            return val.strip()
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, list):
            # rare multi-lemma slots — take first non-empty string
            for x in val:
                s = as_str(x)
                if s:
                    return s
            return ""
        return ""

    sub = json.loads((OUT / "subhashita_beginner_pack.json").read_text(encoding="utf-8"))
    for tok in walk_dicts(sub):
        lemma = as_str(tok.get("lemma_slp1") or tok.get("lemma"))
        if not lemma:
            continue
        surface = as_str(tok.get("t") or tok.get("form") or tok.get("surface"))
        gr = tok.get("gloss_ru")
        if isinstance(gr, dict):
            gloss = as_str(gr.get("lemma") or gr.get("surface"))
        else:
            gloss = as_str(gr)
        key = ("subhashita-beginner", lemma)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "pack": "subhashita-beginner",
                "lemma_slp1": lemma,
                "surface": surface,
                "gloss_ru": gloss,
                "gloss_en": "",
                "locus": "",
            }
        )

    lemma_path = OUT / "lemmas_for_srs.tsv"

    def esc(s: str) -> str:
        return (s or "").replace("\t", " ").replace("\n", " ")

    with lemma_path.open("w", encoding="utf-8", newline="") as f:
        f.write("pack\tlemma_slp1\tsurface\tgloss_ru\tgloss_en\tlocus\n")
        for r in sorted(rows, key=lambda x: (x["pack"], x["lemma_slp1"])):
            f.write(
                "\t".join(
                    esc(r[k])
                    for k in (
                        "pack",
                        "lemma_slp1",
                        "surface",
                        "gloss_ru",
                        "gloss_en",
                        "locus",
                    )
                )
                + "\n"
            )

    packs.append(
        {
            "slug": "lemmas-for-srs",
            "kind": "lemma_tsv",
            "source_path": "derived from hitopadesa-0 + subhashita-beginner pins",
            "pin_path": "data/cohort_start_chteniya/lemmas_for_srs.tsv",
            "sha256": sha256_file(lemma_path),
            "bytes": lemma_path.stat().st_size,
            "built_source": BUILT,
            "schema": (
                "TSV pack|lemma_slp1|surface|gloss_ru|gloss_en|locus — unique lemma per pack"
            ),
            "adapter_note": "Optional SRS import feed for H2106; not a full koloda seed.",
            "gloss_ru_coverage": (
                f"{sum(1 for r in rows if r['gloss_ru'])}/{len(rows)} rows have gloss_ru"
            ),
            "stats": {
                "unique_lemmas": len(rows),
                "hitopadesa_0": sum(1 for r in rows if r["pack"] == "hitopadesa-0"),
                "subhashita_beginner": sum(
                    1 for r in rows if r["pack"] == "subhashita-beginner"
                ),
            },
        }
    )
    print(
        "lemma TSV unique="
        f"{len(rows)} hito={packs[-1]['stats']['hitopadesa_0']} "
        f"sub={packs[-1]['stats']['subhashita_beginner']}"
    )

    manifest = {
        "id": "cohort-start-chteniya-pack-freeze",
        "title": (
            "«Старт чтения» cohort pack freeze "
            "(Hitopadeśa-0 + subhāṣita-beginner + sandhi L1–3)"
        ),
        "cohort_slug": "start_chteniya",
        "built": BUILT,
        "handoff": "H2109",
        "executor": (
            "Grok 4.5 (grok-4.5) — override dual-run of Sonnet-filename handoff"
        ),
        "goal": "Pin owned packs for Systema embed without new linguistics",
        "fence": (
            "No new analysis layers; no human-overlay overwrite; freeze only"
        ),
        "consumers": [
            "Systema-Sanscriticum resources/data/cohort_start_chteniya/ (H2106)",
            "reading_pack import (H2110)",
        ],
        "packs": packs,
        "notes": [
            "hitopadesa-0 is the interim week-3 continuous-prose pack (PLAN D3).",
            "subhashita-beginner is week-5 literature band (or week-5 fallback).",
            "sandhi L1-3 is the beginner drill/curriculum band.",
            (
                "Schema delta on subhashita is intentional prior art "
                "(H1279/H1312) — adapter note in pack row."
            ),
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
    # goal stop: MANIFEST present + hashes
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
