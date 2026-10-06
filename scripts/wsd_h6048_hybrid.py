#!/usr/bin/env python
"""H6048 — MFS+LLM hybrid WSD over the frozen B3 set, with the context-join fix.

H6047 found the H5877 LLM arm showed the WRONG sentence in 298/300 items
(`token.sentence_id` — internal int — joined against `sentence.sent_id` —
external text). This lane lands the prescribed fix FORWARD (H1588 precedent:
H5877 artifacts stay frozen):

  build    inherit the frozen 300-item B3 set verbatim (gold, candidates,
           lemma/grammar) and re-attach the TRUE context sentence via
           `SELECT text_sandhied FROM sentence WHERE id = ?`; verify the
           target lemma occurs in the attached sentence (lemma_id join).
  run-llm  the IDENTICAL prompt/arm as H5877 (deepseek/deepseek-chat, temp 0,
           JSON pick) — the only delta vs the frozen run is the context text.
  tune     train-fold leave-one-out profile of MFS accuracy vs the top-2
           corpus-share gap and train count (threshold justification; no
           test data touched).
  score    llm / mfs / hybrid arms + exact two-sided McNemar
           (hybrid-vs-MFS is the mission test; llm-vs-MFS re-measures the
           H5877 claim in-context). Hybrid routing is PRE-REGISTERED:
           route to LLM iff (gap < DELTA_GAP) or (n_train < MIN_TRAIN),
           else MFS. Try number is recorded; sensitivity sweep is reported
           as post-hoc analysis only.
  validate recompute scores from committed artifacts; PASS/FAIL.

DB resolution: $KOSHA_DCS_SQLITE, then wsd_core.DEFAULT_DCS, then the
main-tree sibling checkout (H6047 convention).

  python scripts/wsd_h6048_hybrid.py build
  python scripts/wsd_h6048_hybrid.py run-llm
  python scripts/wsd_h6048_hybrid.py tune
  python scripts/wsd_h6048_hybrid.py score
  python scripts/wsd_h6048_hybrid.py validate
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import csv
import hashlib
import json
import math
import os
import sqlite3
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wsd_iscls9_eval import (  # noqa: E402 — reuse the frozen-lane primitives
    AUTH_STORE,
    MAX_GLOSS_CHARS,
    OPENROUTER_MODEL,
    RETRIES,
    SYS,
    build_prompt,
    openrouter_key,
    scan_join,
    sha256_file,
)
from wsd_core import (  # noqa: E402
    DEFAULT_DCS,
    SENSE_FREQ,
    WN_MW_MAP,
    load_lemma_map,
    load_wn_mw_resolved,
)

REPO = os.path.normpath(os.path.join(HERE, ".."))
FROZEN_DIR = os.path.join(REPO, "data", "eval", "wsd_iscls9")
FROZEN_ITEMS = os.path.join(FROZEN_DIR, "items.jsonl")
OUT_DIR = os.path.join(REPO, "data", "eval", "wsd_h6048_hybrid")
ITEMS = os.path.join(OUT_DIR, "items.jsonl")
ITEMS_META = os.path.join(OUT_DIR, "items.meta.json")
LLM_OUT = os.path.join(OUT_DIR, "llm_deepseek_chat.jsonl")
SCORES = os.path.join(OUT_DIR, "scores.json")
PER_ITEM = os.path.join(OUT_DIR, "per_item.tsv")

# --- pre-registered hybrid routing (try 1; mission: "top-2 close senses") ----
DELTA_GAP = 0.20   # route to LLM iff corpus share gap p1-p2 < 0.20 …
MIN_TRAIN = 10     # … or the lemma has < 10 train-fold tokens (sparse prior)
HANDOFF = "H6048"
N_CONCURRENCY = 4


def resolve_dcs() -> str:
    cands = [
        os.environ.get("KOSHA_DCS_SQLITE", ""),
        DEFAULT_DCS,
        "/Users/mac/Documents/GitHub/VisualDCS/src/DCS-data-2026/dcs_full.sqlite",
    ]
    for c in cands:
        if c and os.path.exists(c):
            return c
    sys.exit("dcs_full.sqlite not found (KOSHA_DCS_SQLITE / wsd_core default)")


def cmd_build(args: argparse.Namespace) -> int:
    t0 = time.time()
    os.makedirs(OUT_DIR, exist_ok=True)
    frozen = [json.loads(l) for l in open(FROZEN_ITEMS, encoding="utf-8")]
    print(f"frozen B3 items (H5877): {len(frozen)}")

    dcs_path = resolve_dcs()
    dcs = sqlite3.connect(dcs_path)
    lid2slp = load_lemma_map(dcs_path)
    slp2lid = collections.defaultdict(list)
    for lid, slp in lid2slp.items():
        slp2lid[slp].append(lid)

    n_fixed = n_lemma_present = 0
    for it in frozen:
        sid = int(it["sentence_id"])
        row = dcs.execute(
            "SELECT text_sandhied FROM sentence WHERE id = ?", (sid,)
        ).fetchone()  # THE FIX (H6047): key on internal sentence.id
        true_text = (row[0] if row else "") or ""
        if true_text and true_text != it.get("sentence_iast"):
            n_fixed += 1
        it["sentence_iast_broken"] = it.get("sentence_iast", "")
        it["sentence_iast"] = true_text
        lids = slp2lid.get(it["lemma_slp1"], [])
        q = (
            "SELECT COUNT(*) FROM token WHERE sentence_id = ? AND lemma_id IN "
            f"({','.join('?' * len(lids))})"
        )
        n_lemma_present += bool(dcs.execute(q, (sid, *lids)).fetchone()[0])
    dcs.close()
    print(f"  context re-attached (differs from broken): {n_fixed}/{len(frozen)}")
    print(f"  true sentence contains target lemma: {n_lemma_present}/{len(frozen)}")
    if n_lemma_present != len(frozen):
        print("  WARN: some true sentences lack the target lemma token")

    with open(ITEMS, "w", encoding="utf-8") as f:
        for it in frozen:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    meta = {
        "handoff": HANDOFF,
        "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "inherits": "H5877 frozen B3 items (same 300 items, gold, candidates — byte-identical)",
        "context_fix": "text attached via sentence WHERE id = token.sentence_id (H6047 finding)",
        "checks": {"context_differs_from_broken": n_fixed, "lemma_in_true_sentence": n_lemma_present},
        "dcs_db": os.path.basename(dcs_path),
        "sha256": {
            "frozen_items.jsonl": sha256_file(FROZEN_ITEMS),
            "wn_to_mw_map.tsv": sha256_file(WN_MW_MAP),
            "sense_frequency.tsv": sha256_file(SENSE_FREQ),
            "dcs_full.sqlite": sha256_file(dcs_path),
            "items.jsonl": hashlib.sha256(open(ITEMS, "rb").read()).hexdigest(),
        },
        "elapsed_s": round(time.time() - t0, 1),
    }
    with open(ITEMS_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("wrote", ITEMS)
    print("wrote", ITEMS_META)
    return 0


def load_items_and_results() -> tuple[list[dict], dict[str, dict]]:
    items = [json.loads(l) for l in open(ITEMS, encoding="utf-8")]
    for it in items:
        it.setdefault("_id", f"{it['sentence_id']}|{it['lemma_slp1']}")
    res = {}
    if os.path.exists(LLM_OUT):
        for l in open(LLM_OUT, encoding="utf-8"):
            r = json.loads(l)
            res[r["item"]] = r
    return items, res


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
    items, done = load_items_and_results()
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


def rebuild_train(dcs_path: str) -> dict[str, collections.Counter]:
    wnmw = load_wn_mw_resolved(WN_MW_MAP)
    lid2slp = load_lemma_map(dcs_path)
    train, _, _, _, _ = scan_join(dcs_path, wnmw, lid2slp, None)
    return train


def item_features(train: dict, it: dict) -> dict:
    """Routing features from TRAIN-fold counters only (no gold)."""
    cnt = train.get(it["lemma_slp1"], collections.Counter())
    n_train = sum(cnt.values())
    top2 = [c / n_train for _, c in cnt.most_common(2)] if n_train else []
    p1 = top2[0] if top2 else 0.0
    p2 = top2[1] if len(top2) > 1 else 0.0
    return {"n_train": n_train, "p1": round(p1, 4), "gap": round(p1 - p2, 4)}


def routed(feat: dict, delta_gap: float = DELTA_GAP, min_train: int = MIN_TRAIN) -> bool:
    return feat["gap"] < delta_gap or feat["n_train"] < min_train


def cmd_tune(args: argparse.Namespace) -> int:
    """Train-fold LOO profile of MFS accuracy vs gap / n_train (no test data)."""
    dcs_path = resolve_dcs()
    wnmw = load_wn_mw_resolved(WN_MW_MAP)
    lid2slp = load_lemma_map(dcs_path)
    train, _, _, _, _ = scan_join(dcs_path, wnmw, lid2slp, None)
    dcs = sqlite3.connect(dcs_path)

    # replay the train fold token-by-token for LOO scoring
    bins_gap = {"<0.20": [0, 0], ">=0.20": [0, 0]}
    bins_n = {"<10": [0, 0], ">=10": [0, 0]}
    q = (
        "SELECT t.sentence_id, t.lemma_id, t.m_wordsem FROM token t "
        "WHERE t.m_wordsem IS NOT NULL AND t.m_wordsem != '' AND t.lemma_id IS NOT NULL"
    )
    import zlib

    from wsd_core import primary_synset

    n = right = 0
    for sid, lid, ws in dcs.execute(q):
        slp = lid2slp.get(int(lid), "")
        if not slp:
            continue
        m = wnmw.get((primary_synset(ws), slp))
        if not m:
            continue
        if (zlib.crc32(str(sid).encode()) % 5) == 0:
            continue  # test fold — never touched here
        cnt = train[slp]
        gold = m["sense_id"]
        cnt[gold] -= 1  # leave-one-out
        pred = cnt.most_common(1)[0][0] if sum(cnt.values()) > 0 else None
        cnt[gold] += 1
        n += 1
        ok = pred == gold
        right += ok
        feat = item_features(train, {"lemma_slp1": slp})
        bg = bins_gap["<0.20" if routed_gap(feat) else ">=0.20"]
        bn = bins_n["<10" if feat["n_train"] < MIN_TRAIN else ">=10"]
        bg[0] += 1
        bg[1] += ok
        bn[0] += 1
        bn[1] += ok
    dcs.close()
    prof = {
        "n_train_tokens": n,
        "loo_mfs_accuracy": round(right / n, 4) if n else 0.0,
        "by_stratum": {
            k: {"n": v[0], "loo_mfs_acc": round(v[1] / v[0], 4) if v[0] else None}
            for k, v in {**bins_gap, **{f"n_train {k}": v for k, v in bins_n.items()}}.items()
        },
        "pre_registered_rule": {"delta_gap": DELTA_GAP, "min_train": MIN_TRAIN},
    }
    out = os.path.join(OUT_DIR, "tune_loo_profile.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(prof, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps(prof, indent=1))
    print("wrote", out)
    return 0


def routed_gap(feat: dict) -> bool:
    return feat["gap"] < DELTA_GAP


def tail_items(train: dict, items: list[dict]) -> list[dict]:
    """Routed (ambiguous-tail) items with top-2 close corpus senses attached."""
    out = []
    for it in items:
        feat = item_features(train, it)
        if not routed(feat):
            continue
        cnt = train[it["lemma_slp1"]]
        top2 = cnt.most_common(2)
        # glosses from the item's own candidates (byte-identical storage)
        gloss = {c["sense_id"]: c["gloss"] for c in it["candidates"]}
        t = dict(it)
        t["_tail"] = [
            {"sense_id": sid, "gloss": gloss.get(sid, ""), "rank": i}
            for i, (sid, _c) in enumerate(top2, 1)
        ]
        out.append(t)
    return out


def build_prompt_tail(it: dict, prior_hint: bool = False) -> str:
    lines = [
        f"Sanskrit word: {it.get('lemma_iast') or it['lemma_slp1']}"
        + (f" ({it['grammar']})" if it.get("grammar") else ""),
        f"Context sentence: {it['sentence_iast']}",
    ]
    if prior_hint:
        lines.append(
            "Two candidate senses. Sense 1 is the corpus-most-frequent sense of "
            "this word and is the DEFAULT choice."
        )
    else:
        lines.append("Numbered senses (the two corpus-most-frequent; pick between them):")
    for i, c in enumerate(it["_tail"], 1):
        lines.append(f"{i}. {c['gloss'][:MAX_GLOSS_CHARS]}")
    if prior_hint:
        lines.append(
            "Rule: pick sense 2 only if the context sentence clearly matches "
            "sense 2 AND clearly does not match sense 1; otherwise pick sense 1. "
            'Answer JSON: {"sense": <number>}'
        )
    else:
        lines.append('Which sense applies in the context? Answer JSON: {"sense": <number>}')
    return "\n".join(lines)


def call_tail_llm(key: str, model: str, it: dict, prior_hint: bool = False) -> dict:
    body = {
        "model": model,
        "temperature": 0,
        "max_tokens": 400,  # sonnet-class models burn budget on reasoning; JSON still first
        "messages": [
            {"role": "system", "content": SYS},
            {"role": "user", "content": build_prompt_tail(it, prior_hint)},
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
            if 1 <= pick <= len(it["_tail"]):
                return {"item": it["_id"], "pick": pick,
                        "sense_id": it["_tail"][pick - 1]["sense_id"],
                        "raw": raw[:120], "ok": True}
            return {"item": it["_id"], "pick": None, "sense_id": None,
                    "raw": raw[:120], "ok": False, "err": "out_of_range"}
        except Exception as ex:  # noqa: BLE001 — resumable loop reports and retries
            last = str(ex)[:160]
            time.sleep(min(60.0, (2 ** a) + 0.5))
    return {"item": it["_id"], "pick": None, "sense_id": None, "raw": "", "ok": False, "err": last}


def cmd_run_tail(args: argparse.Namespace) -> int:
    dcs_path = resolve_dcs()
    train = rebuild_train(dcs_path)
    items, _ = load_items_and_results()
    tail = tail_items(train, items)
    out_path = os.path.join(OUT_DIR, f"llm_tail_{args.tag}.jsonl")
    done: dict[str, dict] = {}
    if os.path.exists(out_path):
        for l in open(out_path, encoding="utf-8"):
            r = json.loads(l)
            if r.get("ok"):  # failed rows stay retryable
                done[r["item"]] = r
    todo = [it for it in tail if it["_id"] not in done]
    print(f"tail items: {len(tail)}  done: {len(done)}  todo: {len(todo)}  model: {args.model}")
    if not todo:
        return 0
    key = openrouter_key()
    n_new_fail = 0
    with open(out_path, "a", encoding="utf-8") as f, concurrent.futures.ThreadPoolExecutor(
        max_workers=args.workers
    ) as ex:
        futures = [ex.submit(call_tail_llm, key, args.model, it, args.prior_hint) for it in todo]
        for n, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            r = fut.result()
            if not r.get("ok"):
                n_new_fail += 1
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
    print(f"appended {len(todo)} results ({n_new_fail} failed) -> {out_path}")
    return 0 if n_new_fail == 0 else 3


def load_tail(tag: str) -> dict[str, dict]:
    path = os.path.join(OUT_DIR, f"llm_tail_{tag}.jsonl")
    res = {}
    for l in open(path, encoding="utf-8"):
        r = json.loads(l)
        res[r["item"]] = r
    return res


def mcnemar(bb: int, cc: int) -> float:
    nn = bb + cc
    if nn == 0:
        return 1.0
    tail = sum(math.comb(nn, i) for i in range(0, min(bb, cc) + 1))
    return min(1.0, 2 * tail * (0.5 ** nn))


def compute_scores(items: list[dict], res: dict[str, dict], try_no: int = 1,
                   tail_tag: str | None = None, tail_model: str = "") -> dict:
    dcs_path = resolve_dcs()
    train = rebuild_train(dcs_path)
    tail_res = load_tail(tail_tag) if tail_tag else {}

    n = llm_ok = mfs_ok = hyb_ok = n_routed = 0
    floor_sum = 0.0
    b_lm = c_lm = 0      # llm vs mfs
    b_hm = c_hm = 0      # hybrid vs mfs (mission test)
    per = []
    for it in items:
        k = len(it["candidates"])
        n += 1
        floor_sum += 1.0 / k
        gold = it["gold"]
        cand_ids = [x["sense_id"] for x in it["candidates"]]

        r = res.get(it["_id"])
        llm_pick = cand_ids[r["pick"] - 1] if r and r.get("ok") else None
        llm_right = llm_pick == gold

        mfs_pred = None
        cnt = train.get(it["lemma_slp1"])
        if cnt:
            mfs_pred = cnt.most_common(1)[0][0]
        mfs_right = mfs_pred == gold

        feat = item_features(train, it)
        to_llm = routed(feat)
        if to_llm:
            n_routed += 1
        if to_llm and tail_res:
            tr = tail_res.get(it["_id"])
            hybrid_pick = tr["sense_id"] if tr and tr.get("ok") else mfs_pred
            hybrid_source = "tail_llm" if tr and tr.get("ok") else "mfs"
        else:
            hybrid_pick = llm_pick if to_llm else mfs_pred
            hybrid_source = "llm" if to_llm else "mfs"
        hybrid_right = hybrid_pick == gold

        llm_ok += llm_right
        mfs_ok += mfs_right
        hyb_ok += hybrid_right
        if llm_right and not mfs_right:
            b_lm += 1
        elif not llm_right and mfs_right:
            c_lm += 1
        if hybrid_right and not mfs_right:
            b_hm += 1
        elif not hybrid_right and mfs_right:
            c_hm += 1
        per.append({
            "sentence_id": it["sentence_id"], "lemma_slp1": it["lemma_slp1"],
            "gold": gold, "k": k, **feat, "routed": int(to_llm),
            "llm_pick": llm_pick, "llm_right": int(llm_right),
            "mfs_pred": mfs_pred, "mfs_right": int(mfs_right),
            "hybrid_pick": hybrid_pick, "hybrid_right": int(hybrid_right),
            "hybrid_source": hybrid_source,
        })

    # post-hoc sensitivity sweep (analysis only; selection stays pre-registered)
    sweep = []
    for dg in (0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 1.01):
        for mt in (0, 10, 25):
            hy = lm = mr = nr = 0
            bh = ch = 0
            for it in items:
                gold = it["gold"]
                cand_ids = [x["sense_id"] for x in it["candidates"]]
                r = res.get(it["_id"])
                llm_pick = cand_ids[r["pick"] - 1] if r and r.get("ok") else None
                cnt = train.get(it["lemma_slp1"])
                mfs_pred = cnt.most_common(1)[0][0] if cnt else None
                f = item_features(train, it)
                to_llm = f["gap"] < dg or f["n_train"] < mt
                pick = llm_pick if to_llm else mfs_pred
                nr += to_llm
                hy += pick == gold
                lm += llm_pick == gold
                mr += mfs_pred == gold
                if pick == gold and mfs_pred != gold:
                    bh += 1
                elif pick != gold and mfs_pred == gold:
                    ch += 1
            sweep.append({
                "delta_gap": dg, "min_train": mt, "n_routed": nr,
                "hybrid_acc": round(hy / n, 4), "mfs_acc": round(mr / n, 4),
                "b": bh, "c": ch, "mcnemar_p": round(mcnemar(bh, ch), 5),
            })

    return {
        "n_items": n,
        "floor": round(floor_sum / n, 4) if n else 0.0,
        "llm_incontext": {
            "model": OPENROUTER_MODEL,
            "accuracy": round(llm_ok / n, 4) if n else 0.0,
            "n_ok": sum(1 for it in items if res.get(it["_id"], {}).get("ok")),
        },
        "mfs": {"accuracy": round(mfs_ok / n, 4) if n else 0.0},
        "hybrid": {
            "try": try_no,
            "rule": {"route_to_llm_iff": f"gap(p1-p2) < {DELTA_GAP} or n_train < {MIN_TRAIN}", "delta_gap": DELTA_GAP, "min_train": MIN_TRAIN},
            "tail_arm": {"tag": tail_tag, "model": tail_model,
                         "candidates": "train-counter top-2 senses"} if tail_tag else None,
            "n_routed": n_routed,
            "routed_share": round(n_routed / n, 4) if n else 0.0,
            "accuracy": round(hyb_ok / n, 4) if n else 0.0,
        },
        "paired_llm_vs_mfs": {
            "llm_right_mfs_wrong": b_lm, "llm_wrong_mfs_right": c_lm,
            "mcnemar_p_two_sided": round(mcnemar(b_lm, c_lm), 5),
        },
        "paired_hybrid_vs_mfs": {
            "hybrid_right_mfs_wrong": b_hm, "hybrid_wrong_mfs_right": c_hm,
            "mcnemar_p_two_sided": round(mcnemar(b_hm, c_hm), 5),
        },
        "sensitivity_sweep_post_hoc": sweep,
        "per_item": per,
    }


def cmd_score(args: argparse.Namespace) -> int:
    t0 = time.time()
    items, res = load_items_and_results()
    print(f"scoring {len(items)} items … (try {getattr(args, 'try')}, tail={args.tail or '-'})")
    sc = compute_scores(items, res, try_no=getattr(args, "try"),
                        tail_tag=args.tail, tail_model=args.tail_model)
    per = sc.pop("per_item")
    sc["generated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sc["handoff"] = HANDOFF
    sc["elapsed_s"] = round(time.time() - t0, 1)
    with open(SCORES, "w", encoding="utf-8") as f:
        json.dump(sc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(PER_ITEM, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(per[0].keys()), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(per)
    print(json.dumps({k: v for k, v in sc.items() if k not in ("per_item", "sensitivity_sweep_post_hoc")}, indent=1))
    print("wrote", SCORES)
    print("wrote", PER_ITEM)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    items, res = load_items_and_results()
    committed = json.load(open(SCORES, encoding="utf-8"))
    hyb = committed.get("hybrid") or {}
    tail_info = hyb.get("tail_arm") or {}
    fresh = compute_scores(items, res, try_no=hyb.get("try", 1),
                           tail_tag=tail_info.get("tag"),
                           tail_model=tail_info.get("model", ""))
    per = fresh.pop("per_item")
    for d in (fresh, committed):
        d.pop("generated", None)
        d.pop("elapsed_s", None)
    fresh.setdefault("handoff", HANDOFF)
    committed.setdefault("handoff", HANDOFF)
    ok = fresh == committed
    # per-item continuity vs the frozen lane: MFS arm must be identical
    frozen_scores = json.load(open(os.path.join(FROZEN_DIR, "scores.json"), encoding="utf-8"))
    mfs_match = abs(committed["mfs"]["accuracy"] - frozen_scores["mfs"]["accuracy_on_scored"]) < 1e-9
    print("validate:", "PASS" if ok and mfs_match else "FAIL", f"(mfs continuity vs H5877: {mfs_match})")
    if not ok:
        for k in fresh:
            if fresh[k] != committed.get(k):
                print(f"  differs: {k}")
        return 2
    return 0 if mfs_match else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    r = sub.add_parser("run-llm")
    r.add_argument("--workers", type=int, default=N_CONCURRENCY)
    sub.add_parser("tune")
    t = sub.add_parser("run-tail")
    t.add_argument("--tag", required=True, help="output tag, e.g. top2_deepseek / top2_sonnet5")
    t.add_argument("--model", default=OPENROUTER_MODEL)
    t.add_argument("--prior-hint", action="store_true",
                   help="rank-1-as-DEFAULT instruction (try 4: suppress false rank-2 overrides)")
    t.add_argument("--workers", type=int, default=N_CONCURRENCY)
    s = sub.add_parser("score")
    s.add_argument("--try", type=int, default=1, dest="try")
    s.add_argument("--tail", default=None, help="tail arm tag (run-tail --tag)")
    s.add_argument("--tail-model", default="", help="tail arm model id (provenance)")
    sub.add_parser("validate")
    args = ap.parse_args()
    return {"build": cmd_build, "run-llm": cmd_run_llm, "tune": cmd_tune,
            "run-tail": cmd_run_tail, "score": cmd_score, "validate": cmd_validate}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
