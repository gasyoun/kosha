#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""defgen_score.py — H730: score the definition-generation arms + run the
gloss-grounded WSD agreement pilot.

Subcommands (run in order):
  metrics   deterministic scores (sacrebleu BLEU + chrF, token-F1) per arm,
            overall + per stratum cell -> scores_per_item.tsv, scores_summary.json
  judge     blinded deepseek-chat adequacy 0-5 vs gold, all arms incl. the
            A0 floor (judge discrimination check); resumable judge_<arm>.jsonl
  wsd       WSD agreement pilot: 50 seeded poly5p headwords x <=3 sentences,
            deepseek-chat vs deepseek-reasoner pick an MW sense index;
            agreement + Cohen's kappa (NO gold — DCS m_wordsem ids lack a
            local inventory; agreement-only by design, see protocol doc)
  report    fold judge + wsd into scores_summary.json and print the markdown
            tables for the protocol doc

LLM-judge scores never stand alone (org guardrail, H730): the judge is gated
by its Spearman correlation against chrF and by the A0-floor separation, and
any paper claim additionally needs a human-scored subsample.
"""
import argparse
import collections
import io
import json
import math
import os
import random
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import sacrebleu

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data", "eval", "defgen")
SEED = 730
ARMS = ["A0_random_floor", "A1_chat_ctx", "A2_chat_noctx", "A3_reasoner_ctx"]
WSD_N_LEMMAS = 50
WSD_MAX_SENT = 3

sys.path.insert(0, HERE)
from defgen_run_baselines import deepseek, load_sample  # noqa: E402

_lock = threading.Lock()

JUDGE_SYS = (
    "You evaluate a CANDIDATE English gloss for a Sanskrit headword against the GOLD "
    "gloss (Monier-Williams 1899). Score semantic adequacy 0-5: 5 = covers the gold "
    "senses accurately; 3 = core sense right, senses missing or extra; 1 = related "
    "domain but wrong meaning; 0 = unrelated or empty. The gold text may contain "
    "OCR/markup debris (stray punctuation, dangling abbreviations) — judge MEANING "
    "coverage, never formatting. Respond in JSON: {\"adequacy\": <0-5>}")

WSD_SYS = (
    "You disambiguate a Sanskrit word in context. Given a sentence and the numbered "
    "senses of one word from Monier-Williams, pick the ONE sense used in the sentence. "
    "Respond in JSON: {\"sense\": <number>}")


def tok(s):
    return [t for t in re.sub(r"[^\w\s]", " ", (s or "").lower()).split() if t]


def token_f1(cand, gold):
    c, g = collections.Counter(tok(cand)), collections.Counter(tok(gold))
    if not c or not g:
        return 0.0
    overlap = sum((c & g).values())
    if overlap == 0:
        return 0.0
    p, r = overlap / sum(c.values()), overlap / sum(g.values())
    return 2 * p * r / (p + r)


def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        r = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = r
        i = j + 1
    return ranks


def spearman(a, b):
    ra, rb = rank(a), rank(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    da = math.sqrt(sum((x - ma) ** 2 for x in ra))
    db = math.sqrt(sum((y - mb) ** 2 for y in rb))
    return num / (da * db) if da and db else float("nan")


def load_gen(arm):
    path = os.path.join(DATA, "gen_%s.jsonl" % arm)
    out = {}
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            out[r["slp1"]] = r.get("gloss") or ""
    return out


def cmd_metrics():
    rows, _att = load_sample()
    per_item_path = os.path.join(DATA, "scores_per_item.tsv")
    per_item = io.open(per_item_path, "w", encoding="utf-8", newline="\n")
    per_item.write("slp1\tfreq_band\tpoly_band\tarm\tbleu\tchrf\ttoken_f1\tempty\n")
    summary = {}
    for arm in ARMS:
        gen = load_gen(arm)
        cands, golds, items = [], [], []
        cell_scores = collections.defaultdict(lambda: {"bleu": [], "chrf": [], "f1": []})
        n_empty = 0
        for r in rows:
            cand, gold = gen.get(r["slp1"], ""), r["gold_gloss"]
            if not cand:
                n_empty += 1
            bleu = sacrebleu.sentence_bleu(cand, [gold]).score
            chrf = sacrebleu.sentence_chrf(cand, [gold]).score
            f1 = token_f1(cand, gold)
            cands.append(cand)
            golds.append(gold)
            items.append((r, bleu, chrf, f1))
            cell = (r["freq_band"], r["poly_band"])
            for k, v in (("bleu", bleu), ("chrf", chrf), ("f1", f1)):
                cell_scores[cell][k].append(v)
            per_item.write("%s\t%s\t%s\t%s\t%.2f\t%.2f\t%.4f\t%d\n" % (
                r["slp1"], r["freq_band"], r["poly_band"], arm, bleu, chrf, f1,
                0 if cand else 1))
        corpus_bleu = sacrebleu.corpus_bleu(cands, [golds]).score
        corpus_chrf = sacrebleu.corpus_chrf(cands, [golds]).score
        summary[arm] = {
            "n": len(rows), "n_empty": n_empty,
            "corpus_bleu": round(corpus_bleu, 2),
            "corpus_chrf": round(corpus_chrf, 2),
            "mean_sent_bleu": round(sum(x[1] for x in items) / len(items), 2),
            "mean_sent_chrf": round(sum(x[2] for x in items) / len(items), 2),
            "mean_token_f1": round(sum(x[3] for x in items) / len(items), 4),
            "cells": {"/".join(c): {k: round(sum(v) / len(v), 2) for k, v in d.items()}
                      for c, d in sorted(cell_scores.items())},
        }
        print(arm, json.dumps({k: summary[arm][k] for k in
                               ("corpus_bleu", "corpus_chrf", "mean_token_f1", "n_empty")}))
    per_item.close()
    with io.open(os.path.join(DATA, "scores_summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"metrics": summary}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("-> scores_per_item.tsv, scores_summary.json")


def cmd_judge(workers):
    rows, _att = load_sample()
    gold = {r["slp1"]: r["gold_gloss"] for r in rows}
    for arm in ARMS:
        gen = load_gen(arm)
        out_path = os.path.join(DATA, "judge_%s.jsonl" % arm)
        done = set()
        if os.path.exists(out_path):
            with io.open(out_path, encoding="utf-8") as f:
                for line in f:
                    try:
                        done.add(json.loads(line)["slp1"])
                    except (json.JSONDecodeError, KeyError):
                        continue
        todo = [r["slp1"] for r in rows if r["slp1"] not in done]
        print("judge %s: %d done, %d to run" % (arm, len(done), len(todo)))
        if not todo:
            continue
        out_f = io.open(out_path, "a", encoding="utf-8", newline="\n")

        def work(k, arm=arm, gen=gen, out_f=out_f):
            user = ("Headword: %s\nGOLD gloss: %s\nCANDIDATE gloss: %s\n"
                    "Respond in JSON: {\"adequacy\": <0-5>}" % (k, gold[k], gen.get(k, "")))
            raw = deepseek(user, model="deepseek-chat", system=JUDGE_SYS)
            score = None
            if raw:
                m = re.search(r"\{.*\}", raw, re.S)
                if m:
                    try:
                        v = json.loads(m.group(0)).get("adequacy")
                        if isinstance(v, (int, float)) and 0 <= v <= 5:
                            score = v
                    except json.JSONDecodeError:
                        pass
            with _lock:
                out_f.write(json.dumps({"slp1": k, "arm": arm, "adequacy": score},
                                       ensure_ascii=False) + "\n")
                out_f.flush()

        with ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(work, todo))
        out_f.close()


def cmd_wsd(workers):
    rows, att = load_sample()
    poly = sorted(r["slp1"] for r in rows if r["poly_band"] == "poly5p")
    rng = random.Random(SEED)
    rng.shuffle(poly)
    chosen = set(poly[:WSD_N_LEMMAS])
    by_key = {r["slp1"]: r for r in rows}
    jobs = []
    for k in sorted(chosen):
        senses = [s.strip() for s in by_key[k]["gold_gloss"].split(" | ") if s.strip()]
        for s in att[k][:WSD_MAX_SENT]:
            jobs.append((k, s, senses))
    for model in ("deepseek-chat", "deepseek-reasoner"):
        out_path = os.path.join(DATA, "wsd_%s.jsonl" % model.replace("deepseek-", ""))
        done = set()
        if os.path.exists(out_path):
            with io.open(out_path, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                        done.add((r["slp1"], r["sent_id"]))
                    except (json.JSONDecodeError, KeyError):
                        continue
        todo = [j for j in jobs if (j[0], j[1]["sent_id"]) not in done]
        print("wsd %s: %d done, %d to run" % (model, len(done), len(todo)))
        if not todo:
            continue
        out_f = io.open(out_path, "a", encoding="utf-8", newline="\n")

        def work(job, model=model, out_f=out_f):
            k, s, senses = job
            numbered = "\n".join("%d. %s" % (i, t) for i, t in enumerate(senses, 1))
            user = ("Word: %s (IAST %s)\nSentence (IAST, sandhied): %s\n"
                    "Senses of %s (Monier-Williams):\n%s\n"
                    "Which sense number is used here? Respond in JSON: {\"sense\": <number>}"
                    % (k, by_key[k]["iast"], s["text"], by_key[k]["iast"], numbered))
            raw = deepseek(user, model=model, system=WSD_SYS)
            sense = None
            if raw:
                m = re.search(r"\{.*\}", raw, re.S)
                if m:
                    try:
                        v = json.loads(m.group(0)).get("sense")
                        if isinstance(v, int) and 1 <= v <= len(senses):
                            sense = v
                    except json.JSONDecodeError:
                        pass
            with _lock:
                out_f.write(json.dumps({"slp1": k, "sent_id": s["sent_id"],
                                        "n_senses": len(senses), "sense": sense},
                                       ensure_ascii=False) + "\n")
                out_f.flush()

        with ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(work, todo))
        out_f.close()


def cmd_report():
    with io.open(os.path.join(DATA, "scores_summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    rows, _att = load_sample()
    chrf_per = {}
    with io.open(os.path.join(DATA, "scores_per_item.tsv"), encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            d = dict(zip(header, line.rstrip("\n").split("\t")))
            chrf_per[(d["arm"], d["slp1"])] = float(d["chrf"])

    judge = {}
    for arm in ARMS:
        path = os.path.join(DATA, "judge_%s.jsonl" % arm)
        if not os.path.exists(path):
            continue
        scores = {}
        with io.open(path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r.get("adequacy") is not None:
                    scores[r["slp1"]] = r["adequacy"]
        pair = [(scores[k], chrf_per[(arm, k)]) for k in scores if (arm, k) in chrf_per]
        judge[arm] = {
            "n_scored": len(scores),
            "mean_adequacy": round(sum(scores.values()) / len(scores), 3) if scores else None,
            "spearman_vs_chrf": round(spearman([p[0] for p in pair], [p[1] for p in pair]), 3)
            if len(pair) > 2 else None,
        }
    summary["judge"] = judge

    wsd = {}
    picks = {}
    for short in ("chat", "reasoner"):
        path = os.path.join(DATA, "wsd_%s.jsonl" % short)
        if not os.path.exists(path):
            continue
        with io.open(path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                picks.setdefault((r["slp1"], r["sent_id"]), {})[short] = (r["sense"], r["n_senses"])
    both = {k: v for k, v in picks.items() if len(v) == 2
            and v["chat"][0] is not None and v["reasoner"][0] is not None}
    if both:
        agree = sum(1 for v in both.values() if v["chat"][0] == v["reasoner"][0])
        po = agree / len(both)
        # chance agreement: per-item 1/k under independent uniform picks
        pe = sum(1.0 / v["chat"][1] for v in both.values()) / len(both)
        wsd = {"n_items": len(both), "raw_agreement": round(po, 3),
               "chance_agreement_uniform": round(pe, 3),
               "kappa_vs_uniform_chance": round((po - pe) / (1 - pe), 3) if pe < 1 else None}
    summary["wsd_pilot"] = wsd

    with io.open(os.path.join(DATA, "scores_summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write("\n")

    m = summary["metrics"]
    print("\n| Arm | corpus BLEU | corpus chrF | token-F1 | judge 0-5 | judge~chrF rho | empty |")
    print("|---|---|---|---|---|---|---|")
    for arm in ARMS:
        j = judge.get(arm, {})
        print("| %s | %.2f | %.2f | %.4f | %s | %s | %d |" % (
            arm, m[arm]["corpus_bleu"], m[arm]["corpus_chrf"], m[arm]["mean_token_f1"],
            j.get("mean_adequacy", "—"), j.get("spearman_vs_chrf", "—"), m[arm]["n_empty"]))
    print("\nWSD pilot:", json.dumps(wsd))
    print("\nPer-cell chrF (arm A1):")
    print("| cell | chrF |")
    print("|---|---|")
    for cell, d in m["A1_chat_ctx"]["cells"].items():
        print("| %s | %.2f |" % (cell, d["chrf"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["metrics", "judge", "wsd", "report"])
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    if args.cmd == "metrics":
        cmd_metrics()
    elif args.cmd == "judge":
        cmd_judge(args.workers)
    elif args.cmd == "wsd":
        cmd_wsd(args.workers)
    else:
        cmd_report()


if __name__ == "__main__":
    main()
