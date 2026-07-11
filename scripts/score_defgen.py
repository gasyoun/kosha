"""Score H730 definition-generation outputs and WSD agreement.

Subcommands:
  defgen  — deterministic metrics for generated glosses vs A3 MW gold:
            corpus chrF2 (primary), corpus BLEU (secondary), and per-item
            best-sense chrF (max sentence chrF over individual gold senses).
            Per-stratum breakdown (freq_band x polysemy_band) + per-item JSONL
            for LLM-judge correlation (Spearman rho; judge never stands alone,
            see docs/DEFGEN_WSD_EVAL_PROTOCOL_MW.md).
  wsd     — inter-model agreement over gloss-grounded sense selection:
            pairwise exact agreement + Cohen's kappa, 3-rater Fleiss kappa.
            No human gold exists yet, so NO accuracy is reported by design.

kappa/rho implementations follow the pure-Python pattern of
SanskritLexicography/RussianTranslation/src/h178_eval_bakeoff.py (H178).

Usage:
  python scripts/score_defgen.py defgen --sample data/eval/defgen/frozen_sample_v1.jsonl \
      --hyp data/eval/defgen/outputs/defgen_haiku45.jsonl [--judge ...judge_haiku45.jsonl]
  python scripts/score_defgen.py wsd --files data/eval/defgen/outputs/wsd_haiku45.jsonl \
      data/eval/defgen/outputs/wsd_sonnet5.jsonl data/eval/defgen/outputs/wsd_fable5.jsonl
"""
import argparse
import collections
import json
import sys
from pathlib import Path

import sacrebleu

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


def load_jsonl(path: str | Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def spearman(xs: list[float], ys: list[float]) -> float:
    """Spearman rho with average ranks for ties (h178 pattern)."""
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    return num / (dx * dy) if dx and dy else 0.0


def cohen_kappa(a: list, b: list) -> float:
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = collections.Counter(a), collections.Counter(b)
    pe = sum(ca[k] * cb.get(k, 0) for k in ca) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def fleiss_kappa(rows: list[list]) -> float:
    """rows: one list of rater labels per item (equal #raters)."""
    cats = sorted({lab for row in rows for lab in row})
    n_r = len(rows[0])
    p_i = []
    cat_tot = collections.Counter()
    for row in rows:
        c = collections.Counter(row)
        cat_tot.update(c)
        p_i.append((sum(v * v for v in c.values()) - n_r) / (n_r * (n_r - 1)))
    pbar = sum(p_i) / len(rows)
    total = len(rows) * n_r
    pe = sum((cat_tot[c] / total) ** 2 for c in cats)
    return (pbar - pe) / (1 - pe) if pe < 1 else 1.0


def gold_ref(row: dict) -> str:
    return "; ".join(row["gold_senses"])


def cmd_defgen(args: argparse.Namespace) -> None:
    sample = {r["slp1"]: r for r in load_jsonl(args.sample)}
    hyps = {r["slp1"]: r["gloss"] for r in load_jsonl(args.hyp)}
    missing = [k for k in sample if k not in hyps]
    if missing:
        print(f"WARN: {len(missing)} sample items missing from {args.hyp}: {missing[:5]}...")
    keys = sorted(k for k in sample if k in hyps)
    hyp_list = [hyps[k] for k in keys]
    ref_list = [gold_ref(sample[k]) for k in keys]

    corpus_chrf = sacrebleu.corpus_chrf(hyp_list, [ref_list]).score
    corpus_bleu = sacrebleu.corpus_bleu(hyp_list, [ref_list]).score

    per_item = []
    for k in keys:
        row = sample[k]
        hyp = hyps[k]
        chrf_full = sacrebleu.sentence_chrf(hyp, [gold_ref(row)]).score
        chrf_best = max(sacrebleu.sentence_chrf(hyp, [s]).score for s in row["gold_senses"])
        per_item.append({
            "slp1": k, "freq_band": row["freq_band"], "polysemy_band": row["polysemy_band"],
            "chrf_full": round(chrf_full, 2), "chrf_best_sense": round(chrf_best, 2),
        })

    print(f"model output: {args.hyp}")
    print(f"n scored: {len(keys)}")
    print(f"corpus chrF2 = {corpus_chrf:.2f}   corpus BLEU = {corpus_bleu:.2f}")

    def bucket_mean(field: str, key: str) -> dict:
        acc = collections.defaultdict(list)
        for it in per_item:
            acc[it[key]].append(it[field])
        return {k: round(sum(v) / len(v), 2) for k, v in sorted(acc.items())}

    print("mean chrf_full by freq_band:    ", bucket_mean("chrf_full", "freq_band"))
    print("mean chrf_full by polysemy_band:", bucket_mean("chrf_full", "polysemy_band"))
    print("mean chrf_best by polysemy_band:", bucket_mean("chrf_best_sense", "polysemy_band"))

    if args.judge:
        judge = {r["slp1"]: r for r in load_jsonl(args.judge)}
        pairs = [(it["chrf_full"], judge[it["slp1"]]["score"])
                 for it in per_item if it["slp1"] in judge]
        rho = spearman([p[0] for p in pairs], [p[1] for p in pairs])
        dist = collections.Counter(judge[k]["score"] for k in judge)
        mean_j = sum(judge[k]["score"] for k in judge) / len(judge)
        print(f"judge: n={len(judge)} mean={mean_j:.3f} dist={dict(sorted(dist.items()))}")
        print(f"Spearman rho (judge score vs chrf_full, n={len(pairs)}): {rho:.3f}")

    if args.per_item_out:
        with open(args.per_item_out, "w", encoding="utf-8", newline="\n") as f:
            for it in per_item:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
        print(f"per-item scores -> {args.per_item_out}")


def cmd_wsd(args: argparse.Namespace) -> None:
    raters = []
    for path in args.files:
        rows = {r["slp1"]: r["sense"] for r in load_jsonl(path)}
        raters.append((Path(path).stem, rows))
    keys = sorted(set.intersection(*(set(r[1]) for r in raters)))
    print(f"WSD items with all {len(raters)} raters: {len(keys)}")
    for i in range(len(raters)):
        for j in range(i + 1, len(raters)):
            a = [raters[i][1][k] for k in keys]
            b = [raters[j][1][k] for k in keys]
            agree = sum(1 for x, y in zip(a, b) if x == y) / len(keys)
            print(f"{raters[i][0]} vs {raters[j][0]}: "
                  f"agreement={agree:.3f} kappa={cohen_kappa(a, b):.3f}")
    if len(raters) >= 3:
        rows = [[r[1][k] for r in raters] for k in keys]
        print(f"Fleiss kappa ({len(raters)} raters): {fleiss_kappa(rows):.3f}")
        unanimous = sum(1 for row in rows if len(set(row)) == 1) / len(rows)
        print(f"unanimous: {unanimous:.3f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("defgen")
    d.add_argument("--sample", default="data/eval/defgen/frozen_sample_v1.jsonl")
    d.add_argument("--hyp", required=True)
    d.add_argument("--judge")
    d.add_argument("--per-item-out")
    d.set_defaults(fn=cmd_defgen)
    w = sub.add_parser("wsd")
    w.add_argument("--files", nargs="+", required=True)
    w.set_defaults(fn=cmd_wsd)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
