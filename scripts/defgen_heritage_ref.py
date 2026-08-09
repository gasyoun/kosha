#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""defgen_heritage_ref.py — H2408: add the Heritage (Huet) French gloss layer as
an INDEPENDENT SECOND REFERENCE to the H730/H972 definition-generation eval.

This is next-step #4 of docs/DEFGEN_MW_GLOSS_EVAL_PROTOCOL.md ("Second
reference — D20 heritage_dico_gloss.tsv French glosses as a multi-reference or
cross-lingual arm"). It does NOT re-run generation: the five arms
(A0_random_floor, A1_chat_ctx, A2_chat_noctx, A3_reasoner_ctx, F1_fable_ctx)
are already frozen as gen_<arm>.jsonl and are re-scored here against a second,
non-MW reference.

Why a second reference matters here: every number in the 11-07/15-07 runs is
scored against MW 1899 itself, which is certainly in every model's pretraining
data (the protocol's load-bearing contamination caveat). Heritage/Huet is an
independent 20th-21st-c. dictionary in FRENCH, so agreement with it measures
sense coverage against a different lexicographic authority instead of
reproduction of MW's own wording.

Subcommands (run in order):
  build    frozen subset = frozen_sample.tsv keys present in the Heritage gloss
           layer; writes keys + SHA-256 digests ONLY (no Heritage text — the
           layer is tier=restricted, LGPLLR-pending; see RIGHTS below)
  metrics  deterministic chrF/BLEU/token-F1 per arm on the subset, against
           (a) MW gold alone, (b) Heritage-FR alone, (c) MW+FR multi-reference,
           plus MW-vs-FR reference divergence
  judge    blinded deepseek-chat adequacy 0-5 of each arm's ENGLISH candidate
           against the FRENCH Heritage gloss (cross-lingual, resumable)
  report   fold judge into heritage_ref_scores.json + print markdown tables

RIGHTS. Heritage `gloss_fr` is LGPLLR content, composition with CC BY-SA
approved by Gerard Huet 03-07-2026, registered tier=restricted in
data/manifest/datasets.json. It is therefore read at runtime from the local
SanskritLexicography sibling and NEVER copied into this repo: the committed
subset carries mw_key1 + DICO anchor + gloss SHA-256 + word count, which is
enough to verify an identical join without redistributing the text.

LLM-judge scores never stand alone (org guardrail, H730): gates are A0-floor
separation on the FR reference, and Spearman against both chrF and the existing
MW-referenced judge.
"""
import argparse
import collections
import hashlib
import io
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import sacrebleu

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
GH = os.path.dirname(REPO)
DATA = os.path.join(REPO, "data", "eval", "defgen")
OUT = os.path.join(DATA, "heritage")
HERITAGE = os.path.join(GH, "SanskritLexicography", "HeadwordLists",
                        "heritage_dico_gloss.tsv")
SUBSET = os.path.join(OUT, "heritage_ref_subset.tsv")
SUBSET_META = os.path.join(OUT, "heritage_ref_subset.meta.json")
SCORES = os.path.join(OUT, "heritage_ref_scores.json")
PER_ITEM = os.path.join(OUT, "heritage_ref_per_item.tsv")

ARMS = ["A0_random_floor", "A1_chat_ctx", "A2_chat_noctx", "A3_reasoner_ctx",
        "F1_fable_ctx"]

sys.path.insert(0, HERE)
from defgen_run_baselines import deepseek, load_sample  # noqa: E402
from defgen_score import spearman, token_f1  # noqa: E402

_lock = threading.Lock()

# Cross-lingual judge: the candidate is English, the reference is French. The
# judge is told to score MEANING coverage across the language gap and to ignore
# both the language mismatch and Heritage's own markup/abbreviation debris.
JUDGE_FR_SYS = (
    "You evaluate a CANDIDATE English gloss for a Sanskrit headword against a "
    "REFERENCE gloss written in FRENCH (Sanskrit Heritage Dictionary, Gerard Huet). "
    "The two are in different languages on purpose: score how well the candidate "
    "covers the MEANING given by the French reference, 0-5. 5 = covers the "
    "reference senses accurately; 3 = core sense right, senses missing or extra; "
    "1 = related domain but wrong meaning; 0 = unrelated or empty. Never penalise "
    "the candidate for being in English, for wording differences, or for the "
    "reference's markup debris (bracketed etymologies, grammatical abbreviations, "
    "cross-reference tails). Judge meaning coverage only. "
    "Respond in JSON: {\"adequacy\": <0-5>}")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_heritage():
    """mw_key1 -> (anchor, gloss_fr). Read-only, from the sibling repo."""
    out = {}
    with io.open(HERITAGE, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < len(header):
                parts += [""] * (len(header) - len(parts))
            d = dict(zip(header, parts))
            key = d["mw_key1"]
            if key and key not in out:
                out[key] = (d.get("heritage_entry_anchor", ""),
                            (d.get("gloss_fr") or "").strip())
    return out


def load_gen(arm):
    path = os.path.join(DATA, "gen_%s.jsonl" % arm)
    out = {}
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            out[r["slp1"]] = r.get("gloss") or ""
    return out


def cmd_build():
    rows, _att = load_sample()
    her = load_heritage()
    os.makedirs(OUT, exist_ok=True)
    kept, skipped = [], []
    for r in rows:
        hit = her.get(r["slp1"])
        if not hit or not hit[1]:
            skipped.append({"slp1": r["slp1"],
                            "reason": "no_heritage_entry" if not hit else "empty_gloss"})
            continue
        anchor, gloss = hit
        kept.append({
            "slp1": r["slp1"], "iast": r["iast"],
            "freq_band": r["freq_band"], "poly_band": r["poly_band"],
            "mw_gold_words": len(r["gold_gloss"].split()),
            "heritage_anchor": anchor,
            "heritage_gloss_sha256": hashlib.sha256(gloss.encode("utf-8")).hexdigest(),
            "heritage_gloss_words": len(gloss.split()),
        })
    cols = ["slp1", "iast", "freq_band", "poly_band", "mw_gold_words",
            "heritage_anchor", "heritage_gloss_sha256", "heritage_gloss_words"]
    with io.open(SUBSET, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(cols) + "\n")
        for k in kept:
            f.write("\t".join(str(k[c]) for c in cols) + "\n")
    cells = collections.Counter((k["freq_band"], k["poly_band"]) for k in kept)
    meta = {
        "handoff": "H2408",
        "purpose": ("Heritage (Huet) French glosses as an independent second "
                    "reference for the H730/H972 definition-generation eval "
                    "(protocol next-step #4)"),
        "n_frozen_sample": len(rows),
        "n_subset": len(kept),
        "n_skipped": len(skipped),
        "cells": {"/".join(c): n for c, n in sorted(cells.items())},
        "rights": ("Heritage gloss_fr is LGPLLR (composition with CC BY-SA approved "
                   "by Gerard Huet 03-07-2026), registered tier=restricted in "
                   "data/manifest/datasets.json. Gloss TEXT is deliberately NOT "
                   "copied here; the sha256 + word count pin the join instead."),
        "inputs": {
            "frozen_sample.tsv": sha256(os.path.join(DATA, "frozen_sample.tsv")),
            "attestations.jsonl": sha256(os.path.join(DATA, "attestations.jsonl")),
            "heritage_dico_gloss.tsv": sha256(HERITAGE),
        },
        "skipped": skipped,
    }
    with io.open(SUBSET_META, "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("subset n=%d of %d (skipped %d) -> %s"
          % (len(kept), len(rows), len(skipped), SUBSET))
    print("cells:", json.dumps(meta["cells"]))


def load_subset():
    keys = []
    with io.open(SUBSET, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            keys.append(dict(zip(header, line.rstrip("\n").split("\t"))))
    return keys


def verify_join(subset, her):
    """The committed subset carries digests, not text — check the local Heritage
    file still produces byte-identical glosses before scoring against it."""
    bad = []
    for s in subset:
        gloss = her.get(s["slp1"], ("", ""))[1]
        got = hashlib.sha256(gloss.encode("utf-8")).hexdigest()
        if got != s["heritage_gloss_sha256"]:
            bad.append(s["slp1"])
    return bad


def cmd_metrics():
    rows, _att = load_sample()
    by_key = {r["slp1"]: r for r in rows}
    subset = load_subset()
    her = load_heritage()
    bad = verify_join(subset, her)
    if bad:
        sys.exit("REFUSE: %d subset rows no longer match the local Heritage file "
                 "(first: %s). Re-run build only if the layer legitimately changed."
                 % (len(bad), ", ".join(bad[:5])))
    print("join verified: %d/%d gloss digests match" % (len(subset), len(subset)))

    mw = [by_key[s["slp1"]]["gold_gloss"] for s in subset]
    fr = [her[s["slp1"]][1] for s in subset]

    # Reference divergence: how far apart the two traditions' surface text is.
    div_chrf = sacrebleu.corpus_chrf(mw, [fr]).score
    div_f1 = sum(token_f1(a, b) for a, b in zip(mw, fr)) / len(mw)

    summary = {
        "n": len(subset),
        "reference_divergence": {
            "chrf_mw_vs_fr": round(div_chrf, 2),
            "mean_token_f1_mw_vs_fr": round(div_f1, 4),
            "mean_words_mw": round(sum(len(x.split()) for x in mw) / len(mw), 1),
            "mean_words_fr": round(sum(len(x.split()) for x in fr) / len(fr), 1),
        },
        "arms": {},
    }
    per = io.open(PER_ITEM, "w", encoding="utf-8", newline="\n")
    per.write("slp1\tfreq_band\tpoly_band\tarm\tchrf_mw\tchrf_fr\tchrf_multi\ttoken_f1_mw\ttoken_f1_fr\n")
    for arm in ARMS:
        gen = load_gen(arm)
        cands = [gen.get(s["slp1"], "") for s in subset]
        cell = collections.defaultdict(lambda: {"chrf_mw": [], "chrf_fr": [], "chrf_multi": []})
        s_mw, s_fr, s_multi, f_mw, f_fr = [], [], [], [], []
        for s, cand, g_mw, g_fr in zip(subset, cands, mw, fr):
            c_mw = sacrebleu.sentence_chrf(cand, [g_mw]).score
            c_fr = sacrebleu.sentence_chrf(cand, [g_fr]).score
            c_mu = sacrebleu.sentence_chrf(cand, [g_mw, g_fr]).score
            t_mw, t_fr = token_f1(cand, g_mw), token_f1(cand, g_fr)
            s_mw.append(c_mw); s_fr.append(c_fr); s_multi.append(c_mu)
            f_mw.append(t_mw); f_fr.append(t_fr)
            c = (s["freq_band"], s["poly_band"])
            cell[c]["chrf_mw"].append(c_mw)
            cell[c]["chrf_fr"].append(c_fr)
            cell[c]["chrf_multi"].append(c_mu)
            per.write("%s\t%s\t%s\t%s\t%.2f\t%.2f\t%.2f\t%.4f\t%.4f\n"
                      % (s["slp1"], s["freq_band"], s["poly_band"], arm,
                         c_mw, c_fr, c_mu, t_mw, t_fr))
        summary["arms"][arm] = {
            "corpus_chrf_mw": round(sacrebleu.corpus_chrf(cands, [mw]).score, 2),
            "corpus_chrf_fr": round(sacrebleu.corpus_chrf(cands, [fr]).score, 2),
            "corpus_chrf_multi": round(sacrebleu.corpus_chrf(cands, [mw, fr]).score, 2),
            "corpus_bleu_mw": round(sacrebleu.corpus_bleu(cands, [mw]).score, 2),
            "corpus_bleu_multi": round(sacrebleu.corpus_bleu(cands, [mw, fr]).score, 2),
            "mean_sent_chrf_mw": round(sum(s_mw) / len(s_mw), 2),
            "mean_sent_chrf_fr": round(sum(s_fr) / len(s_fr), 2),
            "mean_sent_chrf_multi": round(sum(s_multi) / len(s_multi), 2),
            "mean_token_f1_mw": round(sum(f_mw) / len(f_mw), 4),
            "mean_token_f1_fr": round(sum(f_fr) / len(f_fr), 4),
            "mean_words": round(sum(len(c.split()) for c in cands) / len(cands), 1),
            "n_empty": sum(1 for c in cands if not c),
            "cells": {"/".join(c): {k: round(sum(v) / len(v), 2) for k, v in d.items()}
                      for c, d in sorted(cell.items())},
        }
        print(arm, json.dumps({k: summary["arms"][arm][k] for k in
                               ("corpus_chrf_mw", "corpus_chrf_fr", "corpus_chrf_multi")}))
    per.close()
    prev = {}
    if os.path.exists(SCORES):
        with io.open(SCORES, encoding="utf-8") as f:
            prev = json.load(f)
    prev["metrics"] = summary
    with io.open(SCORES, "w", encoding="utf-8", newline="\n") as f:
        json.dump(prev, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("reference divergence chrF(MW,FR) = %.2f" % div_chrf)
    print("-> %s, %s" % (PER_ITEM, SCORES))


def cmd_judge(workers, limit):
    subset = load_subset()
    her = load_heritage()
    bad = verify_join(subset, her)
    if bad:
        sys.exit("REFUSE: %d subset rows no longer match the local Heritage file" % len(bad))
    if limit:
        subset = subset[:limit]
    for arm in ARMS:
        gen = load_gen(arm)
        out_path = os.path.join(OUT, "judge_fr_%s.jsonl" % arm)
        done = set()
        if os.path.exists(out_path):
            with io.open(out_path, encoding="utf-8") as f:
                for line in f:
                    try:
                        r = json.loads(line)
                        if r.get("adequacy") is not None:
                            done.add(r["slp1"])
                    except (json.JSONDecodeError, KeyError):
                        continue
        todo = [s["slp1"] for s in subset if s["slp1"] not in done]
        print("judge_fr %s: %d done, %d to run" % (arm, len(done), len(todo)), flush=True)
        if not todo:
            continue
        out_f = io.open(out_path, "a", encoding="utf-8", newline="\n")

        def work(k, arm=arm, gen=gen, out_f=out_f):
            user = ("Headword: %s\nFRENCH REFERENCE gloss (Heritage, Huet): %s\n"
                    "CANDIDATE English gloss: %s\n"
                    "Respond in JSON: {\"adequacy\": <0-5>}"
                    % (k, her[k][1], gen.get(k, "")))
            raw = deepseek(user, model="deepseek-chat", system=JUDGE_FR_SYS)
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


def _load_judge(path, keyset=None):
    out = {}
    if not os.path.exists(path):
        return out
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("adequacy") is None:
                continue
            if keyset is not None and r["slp1"] not in keyset:
                continue
            out[r["slp1"]] = r["adequacy"]
    return out


def cmd_report():
    subset = load_subset()
    keys = [s["slp1"] for s in subset]
    keyset = set(keys)
    with io.open(SCORES, encoding="utf-8") as f:
        scores = json.load(f)
    per = {}
    with io.open(PER_ITEM, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            d = dict(zip(header, line.rstrip("\n").split("\t")))
            per[(d["arm"], d["slp1"])] = d

    judge = {}
    for arm in ARMS:
        fr = _load_judge(os.path.join(OUT, "judge_fr_%s.jsonl" % arm), keyset)
        # the MW-referenced judge from H730/H972, restricted to this subset
        mwj = _load_judge(os.path.join(DATA, "judge_%s.jsonl" % arm), keyset)
        common = [k for k in keys if k in fr and k in mwj]
        pair_chrf = [(fr[k], float(per[(arm, k)]["chrf_fr"])) for k in fr if (arm, k) in per]
        row = {
            "n_scored": len(fr),
            "mean_adequacy_fr": round(sum(fr.values()) / len(fr), 3) if fr else None,
            "mean_adequacy_mw_same_subset": round(sum(mwj[k] for k in common) / len(common), 3)
            if common else None,
            "spearman_fr_judge_vs_chrf_fr": round(spearman([p[0] for p in pair_chrf],
                                                           [p[1] for p in pair_chrf]), 3)
            if len(pair_chrf) > 2 else None,
            "spearman_fr_judge_vs_mw_judge": round(spearman([fr[k] for k in common],
                                                            [mwj[k] for k in common]), 3)
            if len(common) > 2 else None,
            "n_common_with_mw_judge": len(common),
        }
        judge[arm] = row
    scores["judge_fr"] = judge

    floor = judge.get("A0_random_floor", {}).get("mean_adequacy_fr")
    systems = [judge[a]["mean_adequacy_fr"] for a in ARMS
               if a != "A0_random_floor" and judge.get(a, {}).get("mean_adequacy_fr") is not None]
    scores["gates"] = {
        "floor_separation_fr": {
            "floor": floor, "min_system": min(systems) if systems else None,
            "pass": bool(floor is not None and systems and min(systems) - floor >= 1.0),
        },
        "human_subsample": "NOT run — still required before any paper-grade claim",
    }
    with io.open(SCORES, "w", encoding="utf-8", newline="\n") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)
        f.write("\n")

    m = scores["metrics"]
    print("\nn = %d (subset of 500 frozen MW sample)" % m["n"])
    d = m["reference_divergence"]
    print("Reference divergence: chrF(MW,FR) %.2f · token-F1 %.4f · words MW %.1f / FR %.1f"
          % (d["chrf_mw_vs_fr"], d["mean_token_f1_mw_vs_fr"], d["mean_words_mw"], d["mean_words_fr"]))
    print("\n| Arm | chrF vs MW | chrF vs FR | chrF multi-ref | token-F1 MW | token-F1 FR "
          "| judge-FR 0-5 | judge-MW 0-5 (same subset) | rho FR~chrF-FR | rho FR~MW judge |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for arm in ARMS:
        a, j = m["arms"][arm], judge.get(arm, {})
        print("| %s | %.2f | %.2f | %.2f | %.4f | %.4f | %s | %s | %s | %s |"
              % (arm, a["corpus_chrf_mw"], a["corpus_chrf_fr"], a["corpus_chrf_multi"],
                 a["mean_token_f1_mw"], a["mean_token_f1_fr"],
                 j.get("mean_adequacy_fr", "—"), j.get("mean_adequacy_mw_same_subset", "—"),
                 j.get("spearman_fr_judge_vs_chrf_fr", "—"),
                 j.get("spearman_fr_judge_vs_mw_judge", "—")))
    print("\nGates:", json.dumps(scores["gates"], ensure_ascii=False))
    print("\nPer-cell judge-FR is not computed (per-cell chrF only); per-cell chrF, arm F1_fable_ctx:")
    print("| cell | chrF vs MW | chrF vs FR |")
    print("|---|---|---|")
    for cell, dd in m["arms"]["F1_fable_ctx"]["cells"].items():
        print("| %s | %.2f | %.2f |" % (cell, dd["chrf_mw"], dd["chrf_fr"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "metrics", "judge", "report"])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="judge: cap items (smoke test)")
    args = ap.parse_args()
    if args.cmd == "build":
        cmd_build()
    elif args.cmd == "metrics":
        cmd_metrics()
    elif args.cmd == "judge":
        cmd_judge(args.workers, args.limit)
    else:
        cmd_report()


if __name__ == "__main__":
    main()
