#!/usr/bin/env python
"""ISCLS-9 B3 gloss-grounded WSD eval — gold-scored LLM arm over the WordSem
held-out fold (H5877).

Builds on the H1588 WSD spine (wn_to_mw_map.tsv gold, sense_frequency
inventory) but does NOT reuse its fold: wsd_core.fold_of_sentence keys on
Python's per-process-randomized str hash, so H1588's published split is not
reproducible byte-for-byte (integrity finding, H5877). This script pins the
fold deterministically: test iff crc32(sentence_id) % 5 == 0 (~20%).

Task per item: given a DCS context sentence and the lemma's numbered MW sense
glosses (attested inventory from sense_frequency, mw layer), pick the sense a
Sanskrit lexicographer would assign. Gold = the DCS WordSem sense mapped to MW
via wn_to_mw_map (exact|overlap rows only). Arms scored on identical items:

  llm   deepseek/deepseek-chat via OpenRouter, temperature 0, JSON pick
  mfs   train-fold majority sense per lemma (baseline, paired items only)
  floor uniform random 1/k per item

Subcommands:
  build      construct the frozen item set -> items.jsonl (+ meta)
  run-llm    resumable LLM arm -> llm_deepseek_chat.jsonl
  score      all arms -> scores.json + per_item.tsv
  validate   recompute scores from committed artifacts, print PASS/FAIL

  python scripts/wsd_iscls9_eval.py build --n 300 --frozen-only
  python scripts/wsd_iscls9_eval.py run-llm
  python scripts/wsd_iscls9_eval.py score
  python scripts/wsd_iscls9_eval.py validate
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import csv
import hashlib
import io
import json
import math
import os
import random
import sqlite3
import sys
import time
import urllib.request
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wsd_core import (  # noqa: E402
    DEFAULT_DCS,
    SENSE_FREQ,
    WN_MW_MAP,
    iast_to_slp1,
    load_lemma_map,
    load_wn_mw_resolved,
    primary_synset,
)

REPO = os.path.normpath(os.path.join(HERE, ".."))
FROZEN_SAMPLE = os.path.join(REPO, "data", "eval", "defgen", "frozen_sample.tsv")
OUT_DIR = os.path.join(REPO, "data", "eval", "wsd_iscls9")
ITEMS = os.path.join(OUT_DIR, "items.jsonl")
ITEMS_META = os.path.join(OUT_DIR, "items.meta.json")
LLM_OUT = os.path.join(OUT_DIR, "llm_deepseek_chat.jsonl")
SCORES = os.path.join(OUT_DIR, "scores.json")
PER_ITEM = os.path.join(OUT_DIR, "per_item.tsv")

SEED = 5877
FOLD_MOD = 5  # same 20% held-out share as the H1588 spine
MAX_SENSES = 15  # prompt-bloat guard; skipped items are reported
MAX_GLOSS_CHARS = 220
N_CONCURRENCY = 4
RETRIES = 5
OPENROUTER_MODEL = "deepseek/deepseek-chat"
AUTH_STORE = os.path.join(os.path.expanduser("~"), ".local/share/opencode/auth.json")

SYS = (
    "You are a careful Sanskrit lexicographer. Given a context sentence and a "
    "numbered list of dictionary senses for a Sanskrit word, decide which sense "
    "applies in that context. Answer only compact JSON."
)


def out_(name: str) -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    return os.path.join(OUT_DIR, name)


def fold_of(sentence_id: str) -> str:
    """Deterministic fold — crc32, never Python's randomized hash()."""
    return "test" if (zlib.crc32(str(sentence_id).encode()) % FOLD_MOD) == 0 else "train"


def openrouter_key() -> str:
    key = (json.load(open(AUTH_STORE, encoding="utf-8")).get("openrouter") or {}).get("key", "")
    if not key:
        sys.exit("no openrouter key in opencode auth store")
    return key


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sense_inventory(path: str) -> dict[str, list[dict]]:
    """lemma_slp1 -> [(sense_id, gloss, sense_rank)] from attested mw rows,
    ordered by sense_rank."""
    inv: dict[str, list[tuple[int, str, str]]] = collections.defaultdict(list)
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r.get("layer") != "mw" or (r.get("provenance") or "attested") != "attested":
                continue
            try:
                rank = int(r.get("sense_rank") or 0)
            except ValueError:
                rank = 0
            inv[r["lemma_slp1"]].append((rank, r["sense_id"], r.get("sense_gloss") or ""))
    for lemma in inv:
        inv[lemma] = [
            {"sense_id": sid, "gloss": g, "rank": rk}
            for rk, sid, g in sorted(inv[lemma])[:MAX_SENSES + 50]
        ]
    return inv


def scan_join(dcs_path: str, wnmw: dict, lid2slp: dict, lemma_filter: set[str] | None):
    """One pass over tagged tokens -> train MFS counters + test items."""
    dcs = sqlite3.connect(dcs_path)
    train = collections.defaultdict(collections.Counter)
    test: dict[tuple[str, str], dict] = {}
    n_raw = n_mapped = n_sent_conflict = 0
    q = (
        "SELECT t.sentence_id, t.lemma_id, t.m_wordsem FROM token t "
        "WHERE t.m_wordsem IS NOT NULL AND t.m_wordsem != '' "
        "AND t.lemma_id IS NOT NULL"
    )
    for sid, lid, ws in dcs.execute(q):
        n_raw += 1
        slp = lid2slp.get(int(lid), "")
        if not slp:
            continue
        if lemma_filter is not None and slp not in lemma_filter:
            continue
        m = wnmw.get((primary_synset(ws), slp))
        if not m:
            continue
        n_mapped += 1
        if fold_of(sid) == "train":
            train[slp][m["sense_id"]] += 1
        else:
            key = (str(sid), slp)
            if key not in test:
                test[key] = {"sentence_id": str(sid), "lemma_slp1": slp, "gold": m["sense_id"]}
            elif test[key]["gold"] != m["sense_id"]:
                n_sent_conflict += 1
    dcs.close()
    return train, test, n_raw, n_mapped, n_sent_conflict


def cmd_build(args: argparse.Namespace) -> int:
    t0 = time.time()
    os.makedirs(OUT_DIR, exist_ok=True)
    lemma_filter = None
    if args.frozen_only:
        with open(FROZEN_SAMPLE, encoding="utf-8", newline="") as f:
            lemma_filter = {r["slp1"] for r in csv.DictReader(f, delimiter="\t")}
        print(f"frozen-sample lemma filter: {len(lemma_filter)} lemmas")

    print("loading wn→mw resolved map …")
    wnmw = load_wn_mw_resolved(WN_MW_MAP)
    print(f"  resolved pairs: {len(wnmw)}")
    print("loading sense inventory …")
    inv = load_sense_inventory(SENSE_FREQ)
    print(f"  lemmas with attested MW senses: {len(inv)}")
    print("loading lemma map …")
    lid2slp = load_lemma_map(DEFAULT_DCS)
    print(f"  lemmas: {len(lid2slp)}")

    print("scanning WordSem join (this is the slow pass) …")
    train, test, n_raw, n_mapped, n_conflict = scan_join(DEFAULT_DCS, wnmw, lid2slp, lemma_filter)
    print(f"  tagged tokens: {n_raw}  mapped: {n_mapped}  test items: {len(test)}  same-sentence sense conflicts: {n_conflict}")

    # eligibility: gold inside the lemma's attested inventory, polysemous, k cap
    pool, n_mono, n_gold_out, n_too_many = [], 0, 0, 0
    for it in test.values():
        cand = inv.get(it["lemma_slp1"], [])
        if len(cand) < 2:
            n_mono += 1
            continue
        if len(cand) > MAX_SENSES:
            n_too_many += 1
            continue
        if it["gold"] not in {c["sense_id"] for c in cand}:
            n_gold_out += 1
            continue
        it["candidates"] = cand
        pool.append(it)
    print(f"  eligible polysemous: {len(pool)}  (mono {n_mono}, gold-not-in-inv {n_gold_out}, k>{MAX_SENSES} {n_too_many})")

    rng = random.Random(SEED)
    pool.sort(key=lambda x: (x["sentence_id"], x["lemma_slp1"]))
    sample = pool if args.n == 0 else (
        pool[:] if len(pool) <= args.n else rng.sample(pool, args.n)
    )
    sample.sort(key=lambda x: (x["sentence_id"], x["lemma_slp1"]))

    # attach sentence text + IAST lemma/grammar (per item, not per sentence)
    rev_lemma: dict[str, tuple[str, str]] = {}
    dcs = sqlite3.connect(DEFAULT_DCS)
    for lem, gram in dcs.execute("SELECT lemma, grammar FROM lemma"):
        slp = iast_to_slp1(lem or "")
        if slp and slp not in rev_lemma:
            rev_lemma[slp] = (lem or "", gram or "")
    sent_cache: dict[str, str] = {}
    for it in sample:
        sid = it["sentence_id"]
        if sid not in sent_cache:
            row = dcs.execute(
                "SELECT text_sandhied FROM sentence WHERE sent_id = ?", (sid,)
            ).fetchone()
            sent_cache[sid] = (row[0] if row else "") or ""
        it["sentence_iast"] = sent_cache[sid]
        it["lemma_iast"], it["grammar"] = rev_lemma.get(it["lemma_slp1"], ("", ""))
    dcs.close()

    meta = {
        "handoff": "H5877",
        "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "seed": SEED,
        "fold": f"crc32(sent_id) % {FOLD_MOD} == 0 -> test (pinned; NOT wsd_core hash — see module docstring)",
        "pool": {
            "tagged_tokens_scanned": n_raw,
            "gold_mapped": n_mapped,
            "test_items_before_eligibility": len(test),
            "eligible_polysemous": len(pool),
            "skipped_mono": n_mono,
            "skipped_gold_not_in_inventory": n_gold_out,
            "skipped_k_gt_cap": n_too_many,
            "same_sentence_gold_conflicts_kept_first": n_conflict,
        },
        "sample_n": len(sample),
        "constraints": {
            "polysemous_only": True,
            "max_senses": MAX_SENSES,
            "gold_source": "DCS m_wordsem -> wn_to_mw_map.tsv (exact|overlap) -> lemma#ord",
            "inventory_source": "sense_frequency.tsv mw layer, attested rows",
        },
        "sha256": {
            "wn_to_mw_map.tsv": sha256_file(WN_MW_MAP),
            "sense_frequency.tsv": sha256_file(SENSE_FREQ),
            "frozen_sample.tsv": sha256_file(FROZEN_SAMPLE) if args.frozen_only else None,
            "dcs_full.sqlite": sha256_file(DEFAULT_DCS),
        },
        "elapsed_s": round(time.time() - t0, 1),
    }
    with open(ITEMS, "w", encoding="utf-8") as f:
        for it in sample:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    meta["sha256"]["items.jsonl"] = hashlib.sha256(
        open(ITEMS, "rb").read()
    ).hexdigest()
    with open(ITEMS_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write("\n")
    ks = [len(it["candidates"]) for it in sample]
    print(f"wrote {len(sample)} items -> {ITEMS}  (k: min {min(ks)} / median {sorted(ks)[len(ks)//2]} / max {max(ks)})")
    print("wrote", ITEMS_META)
    return 0


def build_prompt(it: dict) -> str:
    lines = [
        f"Sanskrit word: {it.get('lemma_iast') or it['lemma_slp1']}"
        + (f" ({it['grammar']})" if it.get("grammar") else ""),
        f"Context sentence: {it['sentence_iast']}",
        "Numbered senses:",
    ]
    for i, c in enumerate(it["candidates"], 1):
        g = c["gloss"][:MAX_GLOSS_CHARS]
        lines.append(f"{i}. {g}")
    lines.append('Which sense applies in the context? Answer JSON: {"sense": <number>}')
    return "\n".join(lines)


def call_llm(key: str, it: dict) -> dict:
    body = {
        "model": OPENROUTER_MODEL,
        "temperature": 0,
        "max_tokens": 30,
        "reasoning": {"enabled": False},
        "messages": [
            {"role": "system", "content": SYS},
            {"role": "user", "content": build_prompt(it)},
        ],
    }
    last = None
    for a in range(RETRIES):
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(body).encode(),
                headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
            )
            r = json.load(urllib.request.urlopen(req, timeout=90))
            raw = r["choices"][0]["message"]["content"] or ""
            m = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
            pick = int(m.get("sense"))
            if 1 <= pick <= len(it["candidates"]):
                return {"item": it["_id"], "pick": pick, "raw": raw[:120], "ok": True}
            return {"item": it["_id"], "pick": None, "raw": raw[:120], "ok": False, "err": "out_of_range"}
        except Exception as ex:  # noqa: BLE001 — resumable loop reports and retries
            last = str(ex)[:160]
            time.sleep(min(60.0, (2 ** a) + 0.5))
    return {"item": it["_id"], "pick": None, "raw": "", "ok": False, "err": last}


def cmd_run_llm(args: argparse.Namespace) -> int:
    items = [json.loads(l) for l in open(ITEMS, encoding="utf-8")]
    for i, it in enumerate(items):
        it["_id"] = f"{it['sentence_id']}|{it['lemma_slp1']}"
    done: dict[str, dict] = {}
    if os.path.exists(LLM_OUT):
        for l in open(LLM_OUT, encoding="utf-8"):
            r = json.loads(l)
            done[r["item"]] = r
    todo = [it for it in items if it["_id"] not in done]
    print(f"items: {len(items)}  done: {len(done)}  todo: {len(todo)}")
    if not todo:
        return 0
    key = openrouter_key()
    t0 = time.time()
    n_new_fail = 0
    with open(LLM_OUT, "a", encoding="utf-8") as f, concurrent.futures.ThreadPoolExecutor(
        max_workers=args.workers
    ) as ex:
        futures = [ex.submit(call_llm, key, it) for it in todo]
        for n, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            r = fut.result()
            if not r.get("ok"):
                n_new_fail += 1
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            if n % 25 == 0 or n == len(todo):
                rate = n / max(time.time() - t0, 1)
                print(f"  {n}/{len(todo)}  ({rate:.1f}/s, eta {int((len(todo)-n)/max(rate,0.01))}s)")
    print(f"appended {len(todo)} results ({n_new_fail} failed) -> {LLM_OUT}")
    return 0 if n_new_fail == 0 else 3


def load_items_and_results() -> tuple[list[dict], dict[str, dict]]:
    items = [json.loads(l) for l in open(ITEMS, encoding="utf-8")]
    for i, it in enumerate(items):
        it.setdefault("_id", f"{it['sentence_id']}|{it['lemma_slp1']}")
    res = {}
    for l in open(LLM_OUT, encoding="utf-8"):
        r = json.loads(l)
        res[r["item"]] = r
    return items, res


def compute_scores(items: list[dict], res: dict[str, dict]) -> dict:
    """Score LLM + MFS (train-side counters rebuilt deterministically) + floor."""
    wnmw = load_wn_mw_resolved(WN_MW_MAP)
    lid2slp = load_lemma_map(DEFAULT_DCS)
    train, _, _, _, _ = scan_join(DEFAULT_DCS, wnmw, lid2slp, None)

    n = llm_ok = mfs_scored = mfs_ok = 0
    floor_sum = 0.0
    b = c = 0  # mcnemar: b llm-right/mfs-wrong, c llm-wrong/mfs-right
    per, errors = [], collections.Counter()
    for it in items:
        k = len(it["candidates"])
        n += 1
        floor_sum += 1.0 / k
        gold = it["gold"]
        cand_ids = [x["sense_id"] for x in it["candidates"]]

        r = res.get(it["_id"])
        llm_pick = None
        if r and r.get("ok"):
            llm_pick = cand_ids[r["pick"] - 1]
        elif r:
            errors[r.get("err") or "unknown"] += 1
        llm_right = llm_pick == gold

        mfs_pred = None
        cnt = train.get(it["lemma_slp1"])
        if cnt:
            mfs_pred = cnt.most_common(1)[0][0]
        mfs_right = None
        if mfs_pred is not None:
            mfs_scored += 1
            mfs_right = mfs_pred == gold

        if llm_right:
            llm_ok += 1
        if mfs_right is True:
            mfs_ok += 1
        if mfs_right is not None:
            if llm_right and not mfs_right:
                b += 1
            elif not llm_right and mfs_right:
                c += 1
        per.append({
            "sentence_id": it["sentence_id"], "lemma_slp1": it["lemma_slp1"],
            "gold": gold, "k": k, "llm_pick": llm_pick, "llm_right": int(llm_right),
            "mfs_pred": mfs_pred, "mfs_right": "" if mfs_right is None else int(mfs_right),
        })

    def mcnemar(bb: int, cc: int) -> float:
        nn = bb + cc
        if nn == 0:
            return 1.0
        tail = sum(math.comb(nn, i) for i in range(0, min(bb, cc) + 1))
        return min(1.0, 2 * tail * (0.5 ** nn))

    return {
        "n_items": n,
        "floor": round(floor_sum / n, 4) if n else 0.0,
        "llm": {
            "model": OPENROUTER_MODEL,
            "n_ok": sum(1 for it in items if res.get(it["_id"], {}).get("ok")),
            "n_error": sum(errors.values()),
            "errors": dict(errors),
            "accuracy": round(llm_ok / n, 4) if n else 0.0,
        },
        "mfs": {
            "n_scored": mfs_scored,
            "n_no_train": n - mfs_scored,
            "accuracy_on_scored": round(mfs_ok / mfs_scored, 4) if mfs_scored else 0.0,
        },
        "paired": {
            "n_both": mfs_scored,
            "llm_right_mfs_wrong": b,
            "llm_wrong_mfs_right": c,
            "mcnemar_p_two_sided": round(mcnemar(b, c), 5),
        },
        "per_item": per,
    }


def cmd_score(args: argparse.Namespace) -> int:
    t0 = time.time()
    items, res = load_items_and_results()
    print(f"scoring {len(items)} items …")
    sc = compute_scores(items, res)
    per = sc.pop("per_item")
    sc["generated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sc["handoff"] = "H5877"
    sc["elapsed_s"] = round(time.time() - t0, 1)
    with open(SCORES, "w", encoding="utf-8") as f:
        json.dump(sc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(PER_ITEM, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(per[0].keys()), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(per)
    print(json.dumps({k: v for k, v in sc.items() if k != "per_item"}, indent=1)[:900])
    print("wrote", SCORES)
    print("wrote", PER_ITEM)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    items, res = load_items_and_results()
    fresh = compute_scores(items, res)
    fresh.pop("per_item")
    committed = json.load(open(SCORES, encoding="utf-8"))
    fresh.pop("generated", None)
    committed.pop("generated", None)
    fresh.pop("elapsed_s", None)
    committed.pop("elapsed_s", None)
    fresh.setdefault("handoff", "H5877")
    ok = fresh == committed
    print("validate:", "PASS" if ok else "FAIL")
    if not ok:
        for k in fresh:
            if fresh[k] != committed.get(k):
                print(f"  differs: {k}")
        return 2
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--n", type=int, default=300, help="sample size (0 = all eligible)")
    b.add_argument("--frozen-only", action="store_true",
                   help="restrict to the 500 defgen frozen-sample lemmas")
    r = sub.add_parser("run-llm")
    r.add_argument("--workers", type=int, default=N_CONCURRENCY)
    sub.add_parser("score")
    sub.add_parser("validate")
    args = ap.parse_args()
    return {"build": cmd_build, "run-llm": cmd_run_llm, "score": cmd_score,
            "validate": cmd_validate}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
