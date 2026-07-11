#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""defgen_run_baselines.py — H730: run the definition-generation baseline arms
over the frozen sample (defgen_build_sample.py output).

Arms:
  A0_random_floor  seeded derangement of gold glosses (no model; metric floor)
  A1_chat_ctx      deepseek-chat, headword + grammar + DCS attestations
  A2_chat_noctx    deepseek-chat, headword + grammar only (parametric/memorization arm)
  A3_reasoner_ctx  deepseek-reasoner, same prompt as A1

The DeepSeek caller is adapted from the org-canonical
SanskritLexicography/RussianTranslation/src/build_corpus_lexicon.py deepseek()
(same .env key source, same retry/backoff/Retry-After discipline, same
json_object gotcha: the prompt MUST mention JSON) — parametrized here for
model choice because deepseek-reasoner does not accept response_format, so
its JSON is parsed out of free text instead.

Resumable: each arm appends to data/eval/defgen/gen_<arm>.jsonl and skips
headwords already present. Threaded (default 6 workers).

Usage:
  python scripts/defgen_run_baselines.py --arm A0_random_floor
  python scripts/defgen_run_baselines.py --arm A1_chat_ctx [--workers 6] [--limit N]
"""
import argparse
import io
import json
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
GH = os.path.dirname(REPO)
DATA = os.path.join(REPO, "data", "eval", "defgen")
SAMPLE = os.path.join(DATA, "frozen_sample.tsv")
ATTEST = os.path.join(DATA, "attestations.jsonl")
ENV = os.path.join(GH, "SanskritLexicography", "RussianTranslation", "src", ".env")
API = "https://api.deepseek.com/chat/completions"
SEED = 730
RETRIES = 6
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 300

SYS = ("You are a Sanskrit lexicographer writing English dictionary glosses in the "
       "style of Monier-Williams. Given a Sanskrit headword you produce its concise "
       "English gloss. Separate distinct senses with ' | '. Do not include the "
       "headword itself, etymology, or citations — gloss text only. "
       "Respond in JSON: {\"gloss\": \"...\"}")

_lock = threading.Lock()
_key_cache = [None]


def _key():
    if _key_cache[0] is None:
        for line in io.open(ENV, encoding="utf-8"):
            if line.strip().startswith("DEEPSEEK_API_KEY="):
                _key_cache[0] = line.split("=", 1)[1].strip()
                break
        else:
            sys.exit("no DEEPSEEK_API_KEY in %s" % ENV)
    return _key_cache[0]


def transient(code):
    return code in (429, 500, 502, 503, 504)


def deepseek(user, model="deepseek-chat", system=SYS):
    body = {"model": model, "temperature": 0,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}]}
    if model == "deepseek-chat":
        body["response_format"] = {"type": "json_object"}
    for a in range(RETRIES):
        try:
            r = requests.post(API, headers={"Authorization": "Bearer " + _key()},
                              json=body, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
            if r.status_code >= 400 and transient(r.status_code):
                raise requests.HTTPError("transient HTTP %s" % r.status_code, response=r)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as ex:
            if a == RETRIES - 1:
                sys.stderr.write("deepseek fail: %s\n" % ex)
                return None
            retry_after = getattr(getattr(ex, "response", None), "headers", {}).get("Retry-After")
            wait = min(60.0, (2 ** a) + random.random()) if not retry_after else float(retry_after)
            time.sleep(wait)


def parse_gloss(raw):
    if raw is None:
        return None
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    try:
        g = json.loads(m.group(0)).get("gloss")
        return g.strip() if isinstance(g, str) and g.strip() else None
    except (json.JSONDecodeError, AttributeError):
        return None


def load_sample():
    rows = []
    with io.open(SAMPLE, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            rows.append(dict(zip(header, line.rstrip("\n").split("\t"))))
    att = {}
    with io.open(ATTEST, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            att[r["slp1"]] = r["sentences"]
    return rows, att


def prompt_for(row, att, with_ctx):
    lines = ["Headword: %s (SLP1) / %s (IAST)" % (row["slp1"], row["iast"]),
             "Grammar: %s" % (row["grammar"] or "unknown")]
    if with_ctx:
        lines.append("Corpus attestations (IAST, sandhied, from the Digital Corpus of Sanskrit):")
        for i, s in enumerate(att.get(row["slp1"], []), 1):
            lines.append("%d. %s  [%s]" % (i, s["text"], s["work"]))
    lines.append("Write the English dictionary gloss. Respond in JSON: {\"gloss\": \"...\"}")
    return "\n".join(lines)


def run_arm(arm, workers, limit):
    rows, att = load_sample()
    out_path = os.path.join(DATA, "gen_%s.jsonl" % arm)
    done = set()
    if os.path.exists(out_path):
        with io.open(out_path, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["slp1"])
                except (json.JSONDecodeError, KeyError):
                    continue
    todo = [r for r in rows if r["slp1"] not in done]
    if limit:
        todo = todo[:limit]
    print("%s: %d done, %d to run" % (arm, len(done), len(todo)))

    if arm == "A0_random_floor":
        rng = random.Random(SEED)
        glosses = [r["gold_gloss"] for r in rows]
        idx = list(range(len(rows)))
        while True:  # seeded derangement
            rng.shuffle(idx)
            if all(i != j for i, j in enumerate(idx)):
                break
        with io.open(out_path, "a", encoding="utf-8", newline="\n") as f:
            for i, r in enumerate(rows):
                if r["slp1"] in done:
                    continue
                f.write(json.dumps({"slp1": r["slp1"], "arm": arm,
                                    "gloss": glosses[idx[i]], "model": "none"},
                                   ensure_ascii=False) + "\n")
        print("floor written")
        return

    model = "deepseek-reasoner" if arm.startswith("A3") else "deepseek-chat"
    with_ctx = arm in ("A1_chat_ctx", "A3_reasoner_ctx")
    out_f = io.open(out_path, "a", encoding="utf-8", newline="\n")
    n_ok = [0]

    def work(row):
        raw = deepseek(prompt_for(row, att, with_ctx), model=model)
        gloss = parse_gloss(raw)
        rec = {"slp1": row["slp1"], "arm": arm, "gloss": gloss, "model": model,
               "raw": None if gloss else (raw[:500] if raw else None)}
        with _lock:
            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out_f.flush()
            n_ok[0] += 1 if gloss else 0

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(work, todo))
    out_f.close()
    print("%s complete: %d/%d parsed ok this run" % (arm, n_ok[0], len(todo)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["A0_random_floor", "A1_chat_ctx", "A2_chat_noctx", "A3_reasoner_ctx"])
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    run_arm(args.arm, args.workers, args.limit)


if __name__ == "__main__":
    main()
