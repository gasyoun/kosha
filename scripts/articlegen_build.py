#!/usr/bin/env python3
"""Build the frozen A55 x Cologne-MW article-generation sample and model prompts.

Executed under H6253 by Hy4 flash Free (opencode-go/hy4-flash-free).
Inputs are read locally (union headword index + Cologne MW v02); every derived
file carries sha256 provenance so the eval is reproducible without re-deriving.
"""
import argparse
import hashlib
import json
import random
import re
import unicodedata
from datetime import date
from pathlib import Path

K1 = re.compile(r"<k1>([^<]+)<")
LS = re.compile(r"<ls>([^<]*)</ls>")
EX = re.compile(r"<s[^>]*>([^<]*)</s>")
TAG = re.compile(r"<[^>]+>")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def join_words(text):
    """Cologne MW markup gives split words like 'a—kAra'; keep them verbatim."""
    return re.sub(r"\s+", " ", text).strip()


def read_union(path):
    union = {}
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        idx = {name: i for i, name in enumerate(header)}
        for line in f:
            cells = line.rstrip("\n").split("\t")
            if not cells or not cells[0]:
                continue
            slp1 = cells[idx["slp1"]]
            union[slp1] = {
                "iast": cells[idx["iast"]] if "iast" in idx else "",
                "gender": cells[idx["gender"]] if "gender" in idx else "",
            }
    return union


def read_mw(path):
    """Return (entries by k1, global citation inventory as sorted list)."""
    entries = {}
    citations = set()
    cur_head = None
    cur_body = []
    cur_line = 0

    def flush():
        nonlocal cur_head, cur_body
        if cur_head is None:
            return
        m = K1.search(cur_head)
        if not m:
            cur_head, cur_body = None, []
            return
        key = m.group(1)
        body = "".join(cur_body)
        ls = [join_words(x) for x in LS.findall(body) if x.strip()]
        ex = [join_words(x) for x in EX.findall(body) if x.strip()]
        gloss = join_words(TAG.sub(" ", body))
        citations.update(ls)
        entry = {"key": key, "gloss": gloss, "examples": ex, "citations": ls}
        prev = entries.get(key)
        # Prefer the richest homonym: examples + citations, then gloss length.
        rank = lambda e: (bool(e["examples"]), bool(e["citations"]), len(e["gloss"]))
        if prev is None or rank(entry) > rank(prev):
            entry["mw_line"] = cur_line
            entries[key] = entry
        cur_head, cur_body = None, []

    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.startswith("<L>"):
                flush()
                cur_head, cur_body, cur_line = line, [], n
            elif line.startswith("<LEND>"):
                flush()
            elif cur_head is not None:
                cur_body.append(line)
        flush()
    return entries, sorted(citations)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--union", required=True)
    ap.add_argument("--mw", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=6253)
    ap.add_argument("--main-count", type=int, default=100)
    ap.add_argument("--canary-count", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=10)
    args = ap.parse_args()

    out = Path(args.out)
    (out / "prompts").mkdir(parents=True, exist_ok=True)
    union = read_union(args.union)
    mw, citations = read_mw(args.mw)

    eligible = []
    for key, entry in mw.items():
        if key in union and entry["examples"] and entry["citations"] and len(entry["gloss"]) >= 20:
            eligible.append(key)
    eligible.sort()
    if len(eligible) < args.main_count + args.canary_count:
        raise SystemExit("REFUSE: eligible union∩MW pool too small")

    rng = random.Random(args.seed)
    picked = rng.sample(eligible, args.main_count + args.canary_count)
    canary = set(picked[: args.canary_count])
    main = picked[args.canary_count :]

    rows = []
    for key in picked:
        e = mw[key]
        u = union[key]
        rows.append({
            "split": "canary" if key in canary else "main",
            "slp1": key,
            "iast": u["iast"],
            "gender": u["gender"],
            "gold_gloss": e["gloss"],
            "gold_examples": e["examples"],
            "gold_citations": e["citations"],
            "mw_line": e["mw_line"],
        })
    assert sum(r["split"] == "main" for r in rows) == args.main_count
    assert sum(r["split"] == "canary" for r in rows) == args.canary_count

    cols = ["split", "slp1", "iast", "gender", "gold_gloss", "gold_examples", "gold_citations", "mw_line"]
    with open(out / "sample.tsv", "w", encoding="utf-8") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join([
                r["split"], r["slp1"], r["iast"], r["gender"], r["gold_gloss"],
                json.dumps(r["gold_examples"], ensure_ascii=False),
                json.dumps(r["gold_citations"], ensure_ascii=False),
                str(r["mw_line"]),
            ]) + "\n")

    meta = {
        "eval": "H6253 article generation vs Cologne gold",
        "created": date.today().isoformat(),
        "seed": args.seed,
        "union": {"path": str(args.union), "sha256": sha(args.union)},
        "cologne_mw": {"path": str(args.mw), "sha256": sha(args.mw)},
        "eligible_pool": len(eligible),
        "main_count": args.main_count,
        "canary_count": args.canary_count,
        "citation_inventory_size": len(citations),
        "note": "Canary rows require MG manual gold labels before any PASS claim; main rows are agent-scored.",
    }
    (out / "sample.meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "citation_inventory.json").write_text(json.dumps(citations, ensure_ascii=False) + "\n", encoding="utf-8")

    header = (
        "You are a Sanskrit lexicographer. For EVERY headword listed below, write one plausible "
        "dictionary article using your own knowledge. Output STRICT JSONL: exactly one JSON object "
        "per headword, in the given order, with no markdown fences, no numbering, no commentary.\n"
        "Each object has exactly these keys:\n"
        '  "slp1": the SLP1 headword copied exactly as given\n'
        '  "gloss": English gloss(es), semicolon-separated\n'
        '  "examples": array of 1-3 short Sanskrit example phrases in IAST\n'
        '  "citations": array of 0-3 standard Sanskrit textual authority abbreviations (e.g. "MBh.", "R.", "RV.")\n'
        '  "root": the inferred root or stem in IAST (prefix a root with the sign √)\n'
    )
    for i in range(0, len(picked), args.batch_size):
        batch = picked[i : i + args.batch_size]
        text = [header, "HEADWORDS:"]
        for key in batch:
            u = union[key]
            text.append(f"- slp1={key} | iast={u['iast']} | gender={u['gender'] or 'unknown'}")
        (out / "prompts" / f"batch_{i // args.batch_size + 1:02d}.txt").write_text(
            "\n".join(text) + "\n", encoding="utf-8"
        )
    print(json.dumps({"rows": len(rows), "main": args.main_count, "canary": args.canary_count,
                      "batches": (len(picked) + args.batch_size - 1) // args.batch_size,
                      "eligible_pool": len(eligible), "out": str(out)}, indent=2))


if __name__ == "__main__":
    main()
