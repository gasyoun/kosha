#!/usr/bin/env python3
"""H3456 step 1 - build blinded A/B packets: our c1 TM vs akshara.ru pwg_ru MT.

Inputs  : data/akshara_pilot/parsed_corpus.jsonl   (H3455 restricted corpus, local-only)
          pwg-ru-data tm/pwg_ru_translated.jsonl    (our canonical TM)
Outputs : data/akshara_pilot/bench/tm_snapshot.jsonl     (frozen our-side rows, gitignored)
          data/akshara_pilot/bench/blinding_map.jsonl    (item_id -> side, commit AFTER scores locked)
          data/akshara_pilot/bench/bench_items.jsonl     (blinded judge packets, gitignored)
          stdout summary JSON (committed into the memo by hand)

Entry-level join (honest denominator): our side = TM subcard `ru` texts concatenated
per key1; their side = the whole-entry pwg_ru MT block. Sense-level alignment is NOT
attempted this pass (their MT has no parseable sense scaffolding) - reported as such.
"""
from __future__ import annotations

import hashlib
import html as htmllib
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = Path(r"C:\Users\user\Documents\GitHub\kosha")
CORPUS = ROOT / "data" / "akshara_pilot" / "parsed_corpus.jsonl"
for _c in (CORPUS,
           MAIN / "data" / "akshara_pilot" / "parsed_corpus.jsonl",
           Path(r"C:\Users\user\Documents\GitHub\kosha-akshara\data\akshara_pilot\parsed_corpus.jsonl")):
    if _c.exists():
        CORPUS = _c
        break
TM = Path(r"C:\Users\user\Documents\GitHub\pwg-ru-data\tm\pwg_ru_translated.jsonl")
OUT = ROOT / "data" / "akshara_pilot" / "bench"
SEED = 730
CAP = 6000

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"[ \t]+")


def strip_html(s: str) -> str:
    s = htmllib.unescape(TAG_RE.sub(" ", s))
    s = s.replace("\\n", "\n")
    lines = [WS_RE.sub(" ", ln).strip() for ln in s.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(ln for ln in lines if ln))


def cap_text(s: str) -> tuple[str, bool]:
    if len(s) <= CAP:
        return s, False
    return s[:CAP] + " …[обрезано]", True


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)

    # their side
    corpus = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    theirs = {}
    for r in corpus:
        mt = r.get("mt", {}).get("pwg_ru")
        if mt and r.get("stratum") == "tm":
            theirs[r["slp1"]] = strip_html(mt)

    # our side (+ frozen snapshot)
    ours = {}
    snap_lines = []
    tm_raw = TM.read_bytes()
    for line in tm_raw.decode("utf-8").splitlines():
        row = json.loads(line)
        k = row["key1"]
        if k not in theirs:
            continue
        e = ours.setdefault(k, {"ru_parts": [], "statuses": set(), "n_subcards": 0,
                                "models": set()})
        e["ru_parts"].append(row.get("ru", ""))
        e["statuses"].add(row.get("review_status", "?"))
        e["n_subcards"] += 1
        pv = row.get("provenance") or {}
        if pv.get("model_version"):
            e["models"].add(pv["model_version"])
        snap_lines.append(json.dumps(
            {"key1": k, "subcard": row.get("subcard"), "review_status": row.get("review_status"),
             "ru": row.get("ru"), "de": row.get("de")},
            ensure_ascii=False))
    snap_path = OUT / "tm_snapshot.jsonl"
    snap_path.write_text("\n".join(snap_lines) + "\n", encoding="utf-8", newline="\n")

    items = sorted(set(ours) & set(theirs))
    rng = random.Random(SEED)
    map_rows, pack_rows = [], []
    for n, k in enumerate(items, 1):
        o = ours[k]
        our_text, trunc_o = cap_text(strip_html("\n".join(o["ru_parts"])))
        their_text, trunc_t = cap_text(theirs[k])
        a_is_ours = rng.random() < 0.5
        item_id = f"B{n:03d}"
        map_rows.append({"item_id": item_id, "slp1": k,
                         "A": "ours" if a_is_ours else "theirs",
                         "B": "theirs" if a_is_ours else "ours"})
        pack_rows.append({
            "item_id": item_id, "headword": k,
            "source_de_cap6000": cap_text(strip_html(
                next((json.loads(l)["de"] for l in tm_raw.decode("utf-8").splitlines()
                      if json.loads(l)["key1"] == k and json.loads(l).get("de")), "")))[0],
            "text_A": their_text if a_is_ours else our_text,
            "text_B": our_text if a_is_ours else their_text,
            "chars_A": len(their_text if a_is_ours else our_text),
            "chars_B": len(our_text if a_is_ours else their_text),
            "truncated_A": trunc_t if a_is_ours else trunc_o,
            "truncated_B": trunc_o if a_is_ours else trunc_t,
        })
    (OUT / "blinding_map.jsonl").write_text(
        "\n".join(json.dumps(m, ensure_ascii=False) for m in map_rows) + "\n",
        encoding="utf-8", newline="\n")
    (OUT / "bench_items.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in pack_rows) + "\n",
        encoding="utf-8", newline="\n")

    print(json.dumps({
        "benchmark_items": len(items),
        "tm_snapshot_sha256": hashlib.sha256(tm_raw).hexdigest(),
        "tm_rows_total": sum(1 for _ in open(TM, encoding="utf-8")),
        "snapshot_rows": len(snap_lines),
        "seed": SEED, "cap_chars": CAP,
        "truncated_items_A": sum(1 for p in pack_rows if p["truncated_A"]),
        "truncated_items_B": sum(1 for p in pack_rows if p["truncated_B"]),
        "mean_chars_A": round(sum(p["chars_A"] for p in pack_rows) / max(len(pack_rows), 1)),
        "mean_chars_B": round(sum(p["chars_B"] for p in pack_rows) / max(len(pack_rows), 1)),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
