#!/usr/bin/env python3
"""defgen_fable_arm.py — H972: the F1_fable_ctx arm of the H730 defgen eval.

The generation model for this arm is the Claude Code session itself (Fable 5,
`claude-fable-5`), so generation cannot be an API loop here. Instead this
script implements the parked-lane "gold-free inputs projection" (protocol
§ next-steps 7a, grafted under H752):

  emit      write scratchpad batch files containing ONLY headword + grammar +
            attestations (identical text contract to defgen_run_baselines.
            prompt_for(with_ctx=True)) — the gold gloss is structurally absent,
            so the generating session never has the answer key in context.
  assemble  validate the session's response JSONL batches (coverage vs the
            frozen sample, non-empty glosses) and write
            data/eval/defgen/gen_F1_fable_ctx.jsonl in the exact gen_* schema.

Usage:
  python scripts/defgen_fable_arm.py emit --outdir <scratch> [--batch-size 50]
  python scripts/defgen_fable_arm.py assemble --indir <scratch>

The frozen sample is read by THIS SCRIPT only; the session reads only the
emitted batches. H972, Fable 5 (`claude-fable-5`).
"""
import argparse
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from defgen_run_baselines import load_sample, prompt_for  # noqa: E402

DATA = os.path.join(HERE, "..", "data", "eval", "defgen")
ARM = "F1_fable_ctx"
MODEL = "claude-fable-5"


def emit(outdir, batch_size):
    rows, att = load_sample()
    os.makedirs(outdir, exist_ok=True)
    n_batches = 0
    for b0 in range(0, len(rows), batch_size):
        batch = rows[b0:b0 + batch_size]
        n_batches += 1
        path = os.path.join(outdir, "batch_%02d.txt" % n_batches)
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            for row in batch:
                f.write("### ITEM %s\n" % row["slp1"])
                # identical input contract to the API arms, minus the JSON
                # instruction line (the session writes JSONL directly)
                text = prompt_for(row, att, with_ctx=True)
                text = text.rsplit("\n", 1)[0]  # drop the respond-in-JSON line
                f.write(text + "\n\n")
    print("emitted %d rows in %d batches to %s" % (len(rows), n_batches, outdir))


def assemble(indir):
    rows, _ = load_sample()
    want = [r["slp1"] for r in rows]
    got = {}
    for name in sorted(os.listdir(indir)):
        if not (name.startswith("responses_") and name.endswith(".jsonl")):
            continue
        with io.open(os.path.join(indir, name), encoding="utf-8") as f:
            for ln, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    print("PARSE FAIL %s:%d" % (name, ln))
                    continue
                slp1, gloss = r.get("slp1"), (r.get("gloss") or "").strip()
                if not slp1 or not gloss:
                    print("EMPTY %s:%d %r" % (name, ln, slp1))
                    continue
                if slp1 in got and got[slp1] != gloss:
                    print("DUP-DIVERGENT %s (%s) — keeping first" % (slp1, name))
                    continue
                got[slp1] = gloss
    missing = [s for s in want if s not in got]
    extra = [s for s in got if s not in set(want)]
    print("coverage: %d/%d; missing %d; extra %d" % (len(got) - len(extra),
                                                     len(want), len(missing),
                                                     len(extra)))
    if missing:
        print("missing:", " ".join(missing[:20]), "..." if len(missing) > 20 else "")
        return 1
    if extra:
        print("extra (not in frozen sample, dropped):", " ".join(extra[:10]))
    out = os.path.join(DATA, "gen_%s.jsonl" % ARM)
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        for s in want:  # frozen-sample order, like the API arms
            f.write(json.dumps({"slp1": s, "arm": ARM, "gloss": got[s],
                                "model": MODEL}, ensure_ascii=False) + "\n")
    print("wrote %s (%d records)" % (out, len(want)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("emit")
    e.add_argument("--outdir", required=True)
    e.add_argument("--batch-size", type=int, default=50)
    a = sub.add_parser("assemble")
    a.add_argument("--indir", required=True)
    args = ap.parse_args()
    if args.cmd == "emit":
        emit(args.outdir, args.batch_size)
        return 0
    return assemble(args.indir)


if __name__ == "__main__":
    sys.exit(main())
