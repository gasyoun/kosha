#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""defgen_heritage_delta.py — H2408: the contamination-sensitive quantity.

Each arm was judged twice on the SAME 333 items: once against MW 1899 (the
reference that is certainly in pretraining data, H730/H972 judge files) and once
against Heritage/Huet French (an independent 20th-21st-c. dictionary, this
handoff). The per-item paired difference

    delta_i = adequacy_MW(i) - adequacy_FR(i)

is an "MW-familiarity premium": how much better a system looks when scored
against the dictionary it may have memorised than against an independent one.

Reported per arm as mean delta + a seeded bootstrap 95% CI over items + an exact
two-sided sign test on nonzero pairs, and appended to heritage_ref_scores.json
under "mw_fr_judge_delta". A CI that excludes 0 means the premium is real for
that arm at n=333; overlapping CIs across arms mean the premium does not
separate the arms (i.e. it is not an artefact of one system).
"""
import io
import json
import math
import os
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data", "eval", "defgen")
OUT = os.path.join(DATA, "heritage")
SCORES = os.path.join(OUT, "heritage_ref_scores.json")
ARMS = ["A0_random_floor", "A1_chat_ctx", "A2_chat_noctx", "A3_reasoner_ctx",
        "F1_fable_ctx"]
SEED = 2408
BOOT = 5000


def load_judge(path):
    out = {}
    if not os.path.exists(path):
        return out
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("adequacy") is not None:
                out[r["slp1"]] = float(r["adequacy"])
    return out


def subset_keys():
    keys = []
    with io.open(os.path.join(OUT, "heritage_ref_subset.tsv"), encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            keys.append(dict(zip(header, line.rstrip("\n").split("\t")))["slp1"])
    return keys


def bootstrap_ci(xs, iters=BOOT, seed=SEED):
    rng = random.Random(seed)
    n = len(xs)
    means = []
    for _ in range(iters):
        means.append(sum(xs[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    return means[int(0.025 * iters)], means[int(0.975 * iters)]


def sign_test(xs):
    """Exact two-sided binomial sign test on nonzero pairs, p=0.5."""
    pos = sum(1 for x in xs if x > 0)
    neg = sum(1 for x in xs if x < 0)
    n = pos + neg
    if n == 0:
        return n, pos, neg, 1.0
    k = min(pos, neg)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2.0 ** n)
    return n, pos, neg, min(1.0, 2.0 * tail)


def main():
    keys = subset_keys()
    result = {}
    print("| Arm | judge-MW | judge-FR | mean delta (MW-FR) | 95% CI | n nonzero | MW>FR | FR>MW | sign p |")
    print("|---|---|---|---|---|---|---|---|---|")
    for arm in ARMS:
        mw = load_judge(os.path.join(DATA, "judge_%s.jsonl" % arm))
        fr = load_judge(os.path.join(OUT, "judge_fr_%s.jsonl" % arm))
        common = [k for k in keys if k in mw and k in fr]
        deltas = [mw[k] - fr[k] for k in common]
        lo, hi = bootstrap_ci(deltas)
        n_nz, pos, neg, p = sign_test(deltas)
        mean_mw = sum(mw[k] for k in common) / len(common)
        mean_fr = sum(fr[k] for k in common) / len(common)
        row = {
            "n_paired": len(common),
            "mean_judge_mw": round(mean_mw, 3),
            "mean_judge_fr": round(mean_fr, 3),
            "mean_delta": round(sum(deltas) / len(deltas), 3),
            "ci95": [round(lo, 3), round(hi, 3)],
            "ci_excludes_zero": bool(lo > 0 or hi < 0),
            "n_nonzero": n_nz, "mw_higher": pos, "fr_higher": neg,
            "sign_test_p": round(p, 6),
        }
        result[arm] = row
        print("| %s | %.3f | %.3f | %+.3f | [%+.3f, %+.3f] | %d | %d | %d | %.2g |"
              % (arm, mean_mw, mean_fr, row["mean_delta"], lo, hi, n_nz, pos, neg, p))

    # Does the arm ranking survive the reference swap?
    order_mw = sorted(ARMS, key=lambda a: -result[a]["mean_judge_mw"])
    order_fr = sorted(ARMS, key=lambda a: -result[a]["mean_judge_fr"])
    result["_ranking"] = {
        "by_judge_mw": order_mw,
        "by_judge_fr": order_fr,
        "identical": order_mw == order_fr,
    }
    print("\nranking by judge-MW:", " > ".join(order_mw))
    print("ranking by judge-FR:", " > ".join(order_fr))
    print("ranking preserved under reference swap:", order_mw == order_fr)

    with io.open(SCORES, encoding="utf-8") as f:
        scores = json.load(f)
    scores["mw_fr_judge_delta"] = result
    with io.open(SCORES, "w", encoding="utf-8", newline="\n") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("-> %s (mw_fr_judge_delta)" % SCORES)


if __name__ == "__main__":
    main()
