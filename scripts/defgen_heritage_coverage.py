#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""defgen_heritage_coverage.py — H2408 helper: per-arm judge coverage / null count
for the Heritage cross-lingual judge files, so a retry pass can be targeted."""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data", "eval", "defgen", "heritage")
ARMS = ["A0_random_floor", "A1_chat_ctx", "A2_chat_noctx", "A3_reasoner_ctx",
        "F1_fable_ctx"]

total_null = 0
for arm in ARMS:
    path = os.path.join(OUT, "judge_fr_%s.jsonl" % arm)
    scored, null = {}, set()
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("adequacy") is None:
                null.add(r["slp1"])
            else:
                scored[r["slp1"]] = r["adequacy"]
    null -= set(scored)
    total_null += len(null)
    mean = round(sum(scored.values()) / len(scored), 3) if scored else None
    print("%-18s scored=%3d null=%2d mean=%s" % (arm, len(scored), len(null), mean))
print("total unresolved nulls:", total_null)
