#!/usr/bin/env python3
"""H6464 — A72 E5: abbreviation-disambiguation WSD eval (WSD-shaped).

Protocol per docs/A72_ABBREV_WSD_EVAL_H6464_13.10.26.md, following the
A59 (H5877 ISCLS9_B3_WSD_GOLD_EVAL) / A71 (H6048 hybrid) precedents:
deterministic in-data gold, pinned crc32 fold, honest negatives, exact
McNemar vs MFS.

Item  = one in-entry occurrence (<ab>/<lex>) of a qualifying ambiguous
        grammatical-abbreviation legend (csl-atlas census payload, 448
        polysemous legend strings), inside a dictionary whose own legend
        fixes the expansion (deterministic gold).
Gold  = the host dictionary's single legend expansion for that label.
Arms  = mfs (train-fold majority sense), majority (census-wide majority
        expansion), floor (uniform 1/k), llm (deepseek/deepseek-chat,
        OpenRouter, temp 0, JSON pick, blind to host dictionary).
Fold  = crc32(item_id) % 5 == 0 -> test, else train (pinned, logged).

Subcommands:
  build     extract instances from the csl-orig corpus, pin gold + fold
  run-llm   resumable LLM arm -> llm_deepseek_chat.jsonl
  score     score all arms -> scores.json (+ per-sense P/R/F1, McNemar)
  validate  PASS = scores.json byte-recomputes from committed artifacts
"""
import argparse
import collections
import hashlib
import json
import math
import os
import random
import re
import sys
import time
import zlib
from html import unescape

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "data", "eval", "abbrev_wsd_h6464")
CENSUS_PATH = os.path.join(
    os.path.expanduser("~"), "Documents", "GitHub", "csl-atlas", "data", "abbrev", "abbrev_census.json")
CORPUS_ROOT = os.path.join(
    os.path.expanduser("~"), "Documents", "GitHub", "csl-orig", "v02")
LLM_OUT = os.path.join(OUT_DIR, "llm_deepseek_chat.jsonl")
ITEMS_OUT = os.path.join(OUT_DIR, "items.jsonl")
SCORES_OUT = os.path.join(OUT_DIR, "scores.json")
META_OUT = os.path.join(OUT_DIR, "items.meta.json")
UNBUILDABLE_OUT = os.path.join(OUT_DIR, "unbuildable.json")
TRAIN_OUT = os.path.join(OUT_DIR, "train_counts.json")

TOP_K_LEGENDS = 24          # scope cap: top-K qualifying homographs by occurrence
MAX_TRAIN_PER_LEGEND = 12
MAX_TEST_PER_LEGEND = 8
SAMPLE_SEED = 6464
LLM_MODEL = "deepseek/deepseek-chat"
AUTH_STORE = os.path.join(os.path.expanduser("~"), ".local/share/opencode/auth.json")
CTX_CHARS = 280


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_exp(s: str) -> str:
    """Normalize an expansion for candidate dedup + gold matching."""
    s = unescape(s)
    s = s.casefold()
    s = re.sub(r"[^0-9a-zāīūṛṝḷḹṭḍṇśṣṁṃḥâêîôû ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def fold_of(item_id: str) -> int:
    return zlib.crc32(item_id.encode("utf-8")) % 5


def load_census():
    d = json.load(open(CENSUS_PATH, encoding="utf-8"))
    lt = d["labelTable"]
    cm = {r["label"]: r for r in d["collisionMatrix"]}
    return d, lt, cm


def qualifying_legends(lt, cm):
    """Legends with >=2 deterministic dict-legends and >=2 distinct expansions."""
    qual = []
    for label, row in cm.items():
        legends = lt.get(label, {}).get("legends", [])
        if not legends:
            continue
        bydict = collections.defaultdict(set)
        for lg in legends:
            bydict[lg["dict"]].add(lg["expansion"])
        det = {k for k, v in bydict.items() if len(v) == 1}
        has_gram = any("grammatical" in lg["category"] for lg in legends)
        if len(det) >= 2 and has_gram:
            exps = {norm_exp(next(iter(bydict[k]))) for k in det}
            if len(exps) >= 2:
                occ = sum(sum(t.values()) for t in lt.get(label, {}).get("tags", {}).values())
                qual.append((label, occ, det))
    qual.sort(key=lambda x: (-x[1], x[0]))
    return qual[:TOP_K_LEGENDS], qual


def cmd_build(args):
    os.makedirs(OUT_DIR, exist_ok=True)
    d, lt, cm = load_census()
    picked, all_qual = qualifying_legends(lt, cm)

    # --- unbuildable ledger: every qualifying legend's per-dict determinism ---
    unbuildable = {"reason_key": "host dictionary legend lists >1 expansion for the label "
                                "-> no deterministic gold; instances recorded as unbuildable, never hand-labelled",
                   "legends": {}}
    for label, occ, _ in all_qual:
        legends = lt[label]["legends"]
        bydict = collections.defaultdict(set)
        for lg in legends:
            bydict[lg["dict"]].add(lg["expansion"])
        multi = {k: sorted(v) for k, v in bydict.items() if len(v) > 1}
        unbuildable["legends"][label] = {
            "det_dict_legends": sum(1 for v in bydict.values() if len(v) == 1),
            "multi_expansion_dicts": {k: v for k, v in multi.items()},
            "n_multi_expansion_dicts": len(multi),
        }
    json.dump(unbuildable, open(UNBUILDABLE_OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)

    # candidate inventories per legend: distinct normalized expansions across ALL dicts
    candidates = {}
    for label, _, _ in picked:
        exps = sorted({norm_exp(lg["expansion"]) for lg in lt[label]["legends"]})
        candidates[label] = exps

    # --- extract in-entry occurrences: ONE combined pass per corpus file ---
    def esc_label(s: str) -> str:
        return s if "&amp;" in s else s.replace("&", "&amp;")

    patterns = {label: re.compile(rf"<(ab|lex)>{re.escape(esc_label(label))}</\1>")
                for label, _, _ in picked}
    gold_by = {label: {} for label, _, _ in picked}
    for label, _, _ in picked:
        for lg in lt[label]["legends"]:
            gold_by[label].setdefault(lg["dict"], set()).add(lg["expansion"])
    dicts_all = sorted({dt for _, _, det in picked for dt in det})
    rng = random.Random(SAMPLE_SEED)
    buckets = collections.defaultdict(lambda: {"train": [], "test": []})
    files_read = set()
    t0 = time.time()
    for dt in dicts_all:
        dt_dir = os.path.join(CORPUS_ROOT, dt.lower())
        if not os.path.isdir(dt_dir):
            continue
        for fn in sorted(os.listdir(dt_dir)):
            if fn != dt.lower() + ".txt":  # entry lines live in <dict>.txt (v02 layout)
                continue
            path = os.path.join(dt_dir, fn)
            labels_here = [lab for lab, _, det in picked
                           if dt in det and lab in patterns]
            if not labels_here:
                continue
            try:
                fh = open(path, encoding="utf-8", errors="replace")
            except OSError:
                continue
            for line_no, line in enumerate(fh, 1):
                for label in labels_here:
                    if label not in line:
                        continue
                    for occ_idx, m in enumerate(patterns[label].finditer(line)):
                        item_id = f"{dt.lower()}:{fn}:{line_no}:{occ_idx}"
                        channel = m.group(1)
                        start = max(0, m.start() - CTX_CHARS)
                        end = min(len(line), m.end() + CTX_CHARS)
                        ctx = re.sub(r"\s+", " ", line[start:end].strip())
                        golds_dt = gold_by[label][dt]  # exactly one: det dict
                        gold = next(iter(golds_dt))
                        hw = re.search(r"<h>([^<]{1,120})", line)
                        buckets[label][
                            "test" if fold_of(item_id) == 0 else "train"
                        ].append({
                            "id": item_id, "label": label, "dict": dt, "file": fn,
                            "line_no": line_no, "occ_idx": occ_idx, "channel": channel,
                            "context": ctx,
                            "headword": unescape(hw.group(1)).strip() if hw else "",
                            "gold": gold, "gold_norm": norm_exp(gold),
                            "candidates": candidates[label],
                        })
            fh.close()
            files_read.add(path)
        print(f"[{time.time()-t0:5.1f}s] dict {dt}: "
              f"train={sum(len(buckets[l]['train']) for l,_,_ in picked)} "
              f"test={sum(len(buckets[l]['test']) for l,_,_ in picked)}", file=sys.stderr)

    # --- deterministic sampling within each legend x fold bucket ---
    items = []
    for label, _, _ in picked:
        for fold, cap in (("train", MAX_TRAIN_PER_LEGEND), ("test", MAX_TEST_PER_LEGEND)):
            pool = buckets[label][fold]
            if len(pool) > cap:
                pool = sorted(rng.sample(pool, cap), key=lambda x: x["id"])
            for it in pool:
                it = dict(it)
                it["fold"] = fold
                it["sense_index"] = candidates[label].index(it["gold_norm"]) + 1
                items.append(it)
    items.sort(key=lambda x: x["id"])
    with open(ITEMS_OUT, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    # --- train-fold sense counts per legend (MFS baseline support) ---
    train_counts = {label: dict(collections.Counter(
        it["gold_norm"] for it in items if it["label"] == label and it["fold"] == "train"))
        for label, _, _ in picked}
    json.dump({"seed": SAMPLE_SEED, "counts": train_counts},
              open(TRAIN_OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)

    n_train = sum(1 for it in items if it["fold"] == "train")
    n_test = sum(1 for it in items if it["fold"] == "test")
    meta = {
        "handoff": "H6464", "model": LLM_MODEL,
        "census_payload": {"path": CENSUS_PATH, "sha256": sha256_file(CENSUS_PATH)},
        "corpus_root": CORPUS_ROOT, "files_read": sorted(files_read),
        "fold_rule": "crc32(f'{dict}:{file}:{line_no}:{occ_idx}') % 5 == 0 -> test (pinned, H5877 precedent)",
        "sample_seed": SAMPLE_SEED, "top_k_legends": TOP_K_LEGENDS,
        "max_train_per_legend": MAX_TRAIN_PER_LEGEND, "max_test_per_legend": MAX_TEST_PER_LEGEND,
        "channels": ["ab", "lex"], "channels_excluded": ["lang"],
        "n_items": len(items), "n_train": n_train, "n_test": n_test,
        "items_sha256": sha256_file(ITEMS_OUT),
    }
    json.dump(meta, open(META_OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    print(f"built: {len(items)} items ({n_train} train / {n_test} test) over {len(picked)} legends; "
          f"unbuildable ledger: {len(unbuildable['legends'])} legends", file=sys.stderr)
    return 0


def cmd_validate_build(args):
    ok = sha256_file(ITEMS_OUT) == json.load(open(META_OUT))["items_sha256"]
    print("PASS" if ok else "FAIL", "items.jsonl matches pinned checksum")
    return 0 if ok else 1


# ---------------------------------------------------------------- LLM arm ---
def openrouter_key() -> str:
    key = (json.load(open(AUTH_STORE, encoding="utf-8")).get("openrouter") or {}).get("key", "")
    if not key:
        sys.exit("no openrouter key in opencode auth store")
    return key


def prompt_for(it: dict) -> str:
    cands = "\n".join(f"{i}. {c}" for i, c in enumerate(it["candidates"], 1))
    marker = f"<{it['channel']}>{it['label']}</{it['channel']}>"
    ctx = it["context"].replace(marker, "<<HERE>>", 1)
    return (
        f"In a Sanskrit dictionary entry the grammatical abbreviation "
        f"\"{it['label']}\" occurs (marked <<HERE>> in the entry text). "
        f"Dictionary legends vary, so the abbreviation is ambiguous. "
        f"Using ONLY the entry context, pick which expansion applies HERE.\n\n"
        f"Entry: {ctx}\n\n"
        f"Candidate expansions:\n{cands}\n\n"
        f'Answer with JSON only: {{"pick": <number>}}'
    )


def call_llm(key: str, it: dict, tries: int = 3) -> dict:
    import urllib.request
    body = {
        "model": LLM_MODEL, "temperature": 0, "max_tokens": 30,
        "messages": [{"role": "user", "content": prompt_for(it)}],
    }
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(body).encode(), method="POST",
                headers={"Authorization": "Bearer " + key,
                         "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                out = json.load(r)
            txt = out["choices"][0]["message"]["content"]
            return {"id": it["id"], "raw": txt, "ok": True}
        except Exception as e:  # transient backoff, H6464 rule 4
            last = str(e)
            time.sleep(2 ** attempt * 3)
    return {"id": it["id"], "raw": f"__ERROR__ {last}", "ok": False}


def parse_pick(raw: str, k: int):
    m = re.search(r'"pick"\s*:\s*([0-9]+)', raw)
    if not m:
        return None
    n = int(m.group(1))
    return n if 1 <= n <= k else None


def cmd_run_llm(args):
    import concurrent.futures
    key = openrouter_key()
    items = [json.loads(l) for l in open(ITEMS_OUT, encoding="utf-8") if '"test"' in l]
    done = set()
    if os.path.exists(LLM_OUT) and not args.force:
        for l in open(LLM_OUT, encoding="utf-8"):
            try:
                done.add(json.loads(l)["id"])
            except Exception:
                pass
    todo = [it for it in items if it["id"] not in done]
    print(f"llm arm: {len(todo)} to run ({len(done)} already done)", file=sys.stderr)
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for res in ex.map(lambda it: call_llm(key, it), todo):
            with open(LLM_OUT, "a", encoding="utf-8") as f:
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
            if not res["ok"]:
                print(f"  API fail: {res['id']}: {res['raw'][:80]}", file=sys.stderr)
    print(f"llm arm done in {time.time()-t0:.0f}s", file=sys.stderr)
    return 0


# ---------------------------------------------------------------- scoring ---
def mcnemar_exact(b: int, c: int) -> float:
    """Exact two-sided McNemar via binomial tail."""
    n = b + c
    if n == 0:
        return 1.0
    p = min(1.0, 2.0 * sum(math.comb(n, i) for i in range(0, min(b, c) + 1)) / 2 ** n)
    return min(1.0, p)


def prf(preds, golds):
    """Per-sense + macro P/R/F1 over matched (pred, gold) pairs."""
    per = {}
    senses = sorted(set(golds) | set(preds))
    for s in senses:
        tp = sum(1 for p, g in zip(preds, golds) if p == s and g == s)
        fp = sum(1 for p, g in zip(preds, golds) if p == s and g != s)
        fn = sum(1 for p, g in zip(preds, golds) if p != s and g == s)
        n_gold = tp + fn
        n_pred = tp + fp
        prec = tp / n_pred if n_pred else 0.0
        rec = tp / n_gold if n_gold else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        per[s] = {"precision": round(prec, 4), "recall": round(rec, 4),
                  "f1": round(f1, 4), "n_gold": n_gold, "n_pred": n_pred, "tp": tp}
    tested = [per[s] for s in per if per[s]["n_gold"] > 0]
    macro = round(sum(x["f1"] for x in tested) / len(tested), 4) if tested else 0.0
    return {"per_sense": per, "macro_f1": macro}


def cmd_score(args, out_path=None):
    out_path = out_path or SCORES_OUT
    items = [json.loads(l) for l in open(ITEMS_OUT, encoding="utf-8")]
    test = [it for it in items if it["fold"] == "test"]
    meta = json.load(open(META_OUT))
    assert sha256_file(ITEMS_OUT) == meta["items_sha256"], "items checksum mismatch"
    train_counts = json.load(open(TRAIN_OUT))["counts"]
    census, lt, cm = load_census()

    # candidate ordering must match build
    _, picked_all = qualifying_legends(lt, cm)
    picked = {label: sorted({norm_exp(lg["expansion"]) for lg in lt[label]["legends"]})
              for label, _, _ in picked_all}

    # census-wide majority (majority-sense baseline): det dict with max occurrences
    census_majority = {}
    for label, _, _ in picked_all:
        tags = lt[label].get("tags", {})
        bydict = collections.defaultdict(set)
        for lg in lt[label]["legends"]:
            bydict[lg["dict"]].add(lg["expansion"])
        det = {k: next(iter(v)) for k, v in bydict.items() if len(v) == 1}
        if det:
            weighted = {k: sum(tags.get(k.lower(), {}).values()) or 1 for k in det}
            best = max(weighted, key=lambda k: (weighted[k], k))
            census_majority[label] = norm_exp(det[best])

    llm_raw = {}
    if os.path.exists(LLM_OUT):
        for l in open(LLM_OUT, encoding="utf-8"):
            try:
                r = json.loads(l)
                llm_raw[r["id"]] = r
            except Exception:
                pass

    def mfs_pick(it):
        c = train_counts.get(it["label"], {})
        if not c:
            return None
        mx = max(c.values())
        return sorted(k for k, v in c.items() if v == mx)[0]

    arms = {"mfs": [], "majority": [], "floor": [], "llm": []}
    errors = 0
    for it in test:
        gold = it["gold_norm"]
        cands = picked[it["label"]]
        k = len(cands)
        arms["mfs"].append(mfs_pick(it))
        arms["majority"].append(census_majority.get(it["label"]))
        r = llm_raw.get(it["id"])
        if r and r.get("ok"):
            n = parse_pick(r["raw"], k)
            arms["llm"].append(cands[n - 1] if n else None)
        else:
            arms["llm"].append(None)
            if it["id"] in llm_raw and not llm_raw[it["id"]].get("ok"):
                errors += 1
    # floor: deterministic uniform draw = round-robin by item position per legend
    pos = collections.Counter()
    floor = []
    for it in test:
        cands = picked[it["label"]]
        floor.append(cands[pos[(it["label"])] % len(cands)])
        pos[it["label"]] += 1
    arms["floor"] = floor

    golds = [it["gold_norm"] for it in test]
    scores = {"n_test": len(test), "n_train": meta["n_train"], "llm_model": LLM_MODEL,
              "llm_api_errors": errors,
              "denominators": {"items": len(test),
                               "legends": len({it["label"] for it in test})},
              "arms": {}}
    for name, preds in arms.items():
        acc = sum(1 for p, g in zip(preds, golds) if p == g)
        scores["arms"][name] = {
            "n_scored": sum(1 for p in preds if p is not None),
            "n_skipped_parse": sum(1 for p in preds if p is None),
            "accuracy": round(acc / len(test), 4) if test else 0.0,
            "prf": prf([p for p in preds if p is not None],
                       [g for p, g in zip(preds, golds) if p is not None]),
        }
    for name in ("llm", "majority", "floor"):
        b = sum(1 for p, m, g in zip(arms[name], arms["mfs"], golds)
                if p == g and m != g)
        c = sum(1 for p, m, g in zip(arms[name], arms["mfs"], golds)
                if p != g and m == g)
        scores["arms"][name]["mcnemar_vs_mfs"] = {
            "arm_right_mfs_wrong": b, "arm_wrong_mfs_right": c,
            "p_exact_two_sided": round(mcnemar_exact(b, c), 6)}
    scores["arms"]["mfs"]["note"] = "reference arm; McNemar reported for the others vs MFS"
    json.dump(scores, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)

    print(f"n_test={len(test)}")
    for name in ("llm", "mfs", "majority", "floor"):
        a = scores["arms"][name]
        m = a.get("mcnemar_vs_mfs")
        print(f"{name:9s} acc={a['accuracy']:.4f} macroF1={a['prf']['macro_f1']:.4f}"
              + (f"  McNemar b={m['arm_right_mfs_wrong']} c={m['arm_wrong_mfs_right']} p={m['p_exact_two_sided']}" if m else ""))
    return 0


def cmd_validate(args):
    """PASS = scores.json byte-recomputes from committed artifacts."""
    if not os.path.exists(SCORES_OUT):
        print("FAIL: scores.json missing"); return 1
    committed = open(SCORES_OUT, encoding="utf-8").read()
    tmp = SCORES_OUT + ".recompute"
    try:
        cmd_score(args, out_path=tmp)
        recomputed = open(tmp, encoding="utf-8").read()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    ok = committed == recomputed
    print("PASS: scores.json byte-recomputes" if ok else "FAIL: drift detected")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build").set_defaults(fn=cmd_build)
    p = sub.add_parser("run-llm"); p.add_argument("--workers", type=int, default=4)
    p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_run_llm)
    sub.add_parser("score").set_defaults(fn=cmd_score)
    p = sub.add_parser("validate"); p.set_defaults(fn=cmd_validate)
    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
