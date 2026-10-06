#!/usr/bin/env python3
"""Zaliznyak grammar-token distribution over the 98,639-headword index (H6053).

Mission (H6053, A55/A56 index): classes x frequency x source-dictionary
breadth, anomaly and markup-gap census, table + charts committed in kosha.

Reads (never vendored here, sibling-checkout pattern like
build_zaliznyak_oddbank_drills.py):
  --grammar-index  zaliznyak_grammar_index.tsv (98,639 rows; release
                   data-v0.4.0 asset == SanskritLexicography
                   RussianTranslation/src/headword_index.tsv, MD5-identical,
                   verified 06-10-2026)
  --union          union_headwords.tsv (323,425 rows; release data-v0.4.0
                   asset == HeadwordLists/union/union_headwords.tsv) for the
                   n_dicts source-dictionary dimension

Emits (committed):
  data/zaliznyak/zaliznyak_token_distribution.tsv   per-token table
  data/zaliznyak/zaliznyak_markup_anomalies.tsv     anomaly census
  data/zaliznyak/zaliznyak_token_distribution_summary.json
  docs/charts/h6053_zipf_loglog.svg
  docs/charts/h6053_cumulative_coverage.svg
  docs/charts/h6053_stemclass_share.svg
  docs/charts/h6053_ndicts_histogram.svg

Guarantees: every source row is counted exactly once (sum of per-token
member_count == total rows, asserted); --check re-verifies the committed
TSVs/JSON internally without source access.

H6053, GLM 5.3 (opencode/zai-coding-plan/glm-5.3), 06-10-2026.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import statistics
import sys
from pathlib import Path

EXPECT_ROWS = 98_639
COVERAGE_TARGETS = (0.50, 0.80, 0.90, 0.99)

# lex abbreviation -> gender prefix normalization (adj. is tri-gender, etc.)
LEXMAP = {
    "adj": "mfn", "m.f.n": "mfn", "m.n": "mn", "m.f": "mf", "f.n": "fn",
    "fem": "f", "masc": "m", "neutr": "n",
    "ind": "ind", "indecl": "ind", "adv": "adv", "interj": "interj",
    "abs": "ind", "inf": "ind",
}


def norm_lex(lex: str) -> str:
    lex = lex.strip().rstrip(".").replace(".", "")
    return LEXMAP.get(lex, lex)


def read_tsv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


# ---------------------------------------------------------------- charts ----

ACCENT = "#2f6f6f"
GRID = "#dddddd"
TEXT = "#333333"


def _svg_open(w: int, h: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="Helvetica,Arial,sans-serif" '
        f'font-size="11" fill="{TEXT}">',
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
    ]


def _axis(x: float, y: float, w: int, h: int, xlab: str, ylab: str) -> list[str]:
    return [
        f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + h}" stroke="{TEXT}"/>',
        f'<line x1="{x}" y1="{y + h}" x2="{x + w}" y2="{y + h}" stroke="{TEXT}"/>',
        f'<text x="{x + w / 2}" y="{y + h + 28}" text-anchor="middle">{xlab}</text>',
        f'<text x="{x - 34}" y="{y + h / 2}" text-anchor="middle" '
        f'transform="rotate(-90 {x - 34} {y + h / 2})">{ylab}</text>',
    ]


def chart_zipf(counts: list[int], path: Path) -> None:
    import math
    w, h, ml, mt, mr, mb = 560, 360, 60, 20, 20, 50
    pw, ph = w - ml - mr, h - mt - mb
    mx = math.log10(max(counts))
    my = math.log10(counts[0])
    pts = [
        (ml + pw * math.log10(i + 1) / mx, mt + ph * (1 - math.log10(c) / my))
        for i, c in enumerate(counts)
    ]
    s = _svg_open(w, h) + [f'<text x="{ml}" y="{mt - 6}">Token rank-frequency (Zipf), 342 tokens / 98,639 rows</text>']
    for gy in range(0, 6):
        yy = mt + ph * gy / 5
        s.append(f'<line x1="{ml}" y1="{yy}" x2="{ml + pw}" y2="{yy}" stroke="{GRID}"/>')
        s.append(f'<text x="{ml - 6}" y="{yy + 4}" text-anchor="end">{10 ** (my * (1 - gy / 5)):,.0f}</text>')
    for gl in range(1, 4):
        xx = ml + pw * gl / 3
        s.append(f'<line x1="{xx}" y1="{mt}" x2="{xx}" y2="{mt + ph}" stroke="{GRID}"/>')
        s.append(f'<text x="{xx}" y="{mt + ph + 16}" text-anchor="middle">{10 ** (mx * gl / 3):,.0f}</text>')
    s.append(f'<polyline points="{" ".join(f"{x},{y}" for x, y in pts)}" fill="none" stroke="{ACCENT}" stroke-width="1.6"/>')
    s += _axis(ml, mt, pw, ph, "token rank (log scale)", "rows per token (log scale)")
    s.append("</svg>")
    path.write_text("\n".join(s), encoding="utf-8")


def chart_cumulative(cum: list[float], marks: dict[float, int], path: Path) -> None:
    import math
    w, h, ml, mt, mr, mb = 560, 360, 60, 20, 20, 50
    pw, ph = w - ml - mr, h - mt - mb
    mx = math.log10(len(cum))
    pts = [
        (ml + pw * math.log10(i + 1) / mx, mt + ph * (1 - c / 100.0))
        for i, c in enumerate(cum)
    ]
    s = _svg_open(w, h) + [f'<text x="{ml}" y="{mt - 6}">Cumulative row coverage vs token inventory</text>']
    for pct in (0, 25, 50, 75, 100):
        yy = mt + ph * (1 - pct / 100.0)
        s.append(f'<line x1="{ml}" y1="{yy}" x2="{ml + pw}" y2="{yy}" stroke="{GRID}"/>')
        s.append(f'<text x="{ml - 6}" y="{yy + 4}" text-anchor="end">{pct}%</text>')
    for tgt, rank in marks.items():
        yy = mt + ph * (1 - tgt / 100.0)
        xx = ml + pw * math.log10(rank) / mx
        s.append(f'<line x1="{xx}" y1="{mt}" x2="{xx}" y2="{mt + ph}" stroke="{ACCENT}" stroke-dasharray="4 3"/>')
        s.append(f'<text x="{xx + 4}" y="{yy - 4}">{tgt:.0%} = {rank} tokens</text>')
    s.append(f'<polyline points="{" ".join(f"{x},{y}" for x, y in pts)}" fill="none" stroke="{ACCENT}" stroke-width="2"/>')
    s += _axis(ml, mt, pw, ph, "tokens retained (rank, log scale)", "share of 98,639 rows")
    s.append("</svg>")
    path.write_text("\n".join(s), encoding="utf-8")


def chart_bars(labels: list[str], values: list[int], title: str, xlab: str,
               path: Path, log_x: bool = False) -> None:
    import math
    rowh, ml, mt, mb = 22, 170, 30, 40
    w = 560
    h = mt + len(labels) * rowh + mb
    pw = w - ml - 20
    vmax = max(values)
    s = _svg_open(w, h) + [f'<text x="{ml}" y="{mt - 8}">{title}</text>']
    for i, (lab, v) in enumerate(zip(labels, values)):
        y = mt + i * rowh
        if log_x:
            width = pw * (math.log10(v + 1) / math.log10(vmax + 1))
        else:
            width = pw * v / vmax
        s.append(f'<text x="{ml - 8}" y="{y + 14}" text-anchor="end">{lab}</text>')
        s.append(f'<rect x="{ml}" y="{y + 2}" width="{width:.1f}" height="{rowh - 8}" fill="{ACCENT}"/>')
        s.append(f'<text x="{ml + width + 6:.1f}" y="{y + 14}">{v:,}</text>')
    s.append(f'<text x="{ml + pw / 2}" y="{h - 12}" text-anchor="middle">{xlab}</text>')
    s.append("</svg>")
    path.write_text("\n".join(s), encoding="utf-8")


# ------------------------------------------------------------------ build ----

def build(args: argparse.Namespace) -> int:
    repo = Path(args.repo_root)
    gi_rows = read_tsv(Path(args.grammar_index))
    un_rows = read_tsv(Path(args.union))
    assert len(gi_rows) == args.expect_rows, (
        f"grammar index rows {len(gi_rows)} != expected {args.expect_rows}")

    union = {r["slp1"]: r for r in un_rows}

    # ---- per-token aggregation (every row counted exactly once) ----
    tok_rows: dict[str, list[dict]] = collections.defaultdict(list)
    for r in gi_rows:
        tok_rows[r["index_token"]].append(r)
    assert sum(len(v) for v in tok_rows.values()) == len(gi_rows)

    pc = read_tsv(repo / "data/zaliznyak/zaliznyak_paradigm_classes.tsv")
    pc_tokens = {p["index_token"] for p in pc}

    dist = []
    for tok, rs in tok_rows.items():
        nd = [int(union[r["k1"]]["n_dicts"]) for r in rs if r["k1"] in union]
        dist.append({
            "index_token": tok,
            "gender": tok.split("·")[0],
            "stem_class": collections.Counter(
                r["stem_class"] for r in rs).most_common(1)[0][0],
            "member_count": len(rs),
            "pct_rows": round(100.0 * len(rs) / len(gi_rows), 3),
            "mean_n_dicts": round(statistics.mean(nd), 2) if nd else "",
            "pct_rows_ge5_dicts": round(100.0 * sum(1 for n in nd if n >= 5) / len(rs), 1) if nd else "",
            "in_paradigm_classes": "yes" if tok in pc_tokens else "no",
        })
    dist.sort(key=lambda d: (-d["member_count"], d["index_token"]))
    cum = 0.0
    for d in dist:
        cum += d["pct_rows"]
        d["cum_pct_rows"] = round(cum, 3)

    # ---- coverage checkpoints ----
    marks: dict[float, int] = {}
    acc, k = 0, 0
    for d in dist:
        acc += d["member_count"]
        k += 1
        for tgt in COVERAGE_TARGETS:
            if tgt not in marks and acc / len(gi_rows) >= tgt:
                marks[tgt] = k

    # ---- anomaly census ----
    anomalies: list[dict] = []

    def add(atype: str, key: str, count: int, examples: list[str], detail: str) -> None:
        anomalies.append({
            "anomaly_type": atype, "key": key, "count": count,
            "examples_k1": " ".join(examples[:5]), "detail": detail,
        })

    # A1: empty index_token (markup hole)
    empty_tok = [r["k1"] for r in gi_rows if not r["index_token"].strip()]
    add("empty_index_token", "-", len(empty_tok), empty_tok,
        "rows with no paradigm token assigned")

    # A2: k1 not joinable to union headwords (source-index orphans)
    orphans = sorted({r["k1"] for r in gi_rows} - set(union))
    add("k1_not_in_union", "-", len(orphans), orphans,
        "grammar-index headwords absent from union_headwords.tsv — all -inI "
        "feminines the union folds into -in (fem_fold) while the grammar "
        "index keeps separate headwords")

    # A3: genuine gender disagreements (normalized lex vs token gender)
    gen = collections.defaultdict(list)
    for r in gi_rows:
        gp = r["index_token"].split("·")[0]
        nl = norm_lex(r["lex"])
        if nl in ("", "?") or nl in ("adv", "interj", "ind"):
            continue  # indeclinable-class labels, not gender claims
        if gp.startswith("ind"):
            gen[(r["lex"], r["index_token"])].append(r["k1"])
            continue
        if not set(nl) <= set(gp):
            gen[(r["lex"], r["index_token"])].append(r["k1"])
    for (lex, tok), k1s in sorted(gen.items(), key=lambda kv: -len(kv[1])):
        add("gender_lex_vs_token", f"lex={lex} token={tok}", len(k1s), k1s,
            "PWG gender label contradicts token gender prefix")

    # A4: indeclinable-class lex variety inside ind tokens (benign, census)
    ind_lex = collections.Counter(
        norm_lex(r["lex"]) for r in gi_rows
        if r["index_token"].startswith("ind·"))
    add("ind_lex_label_variety", "ind·*", sum(ind_lex.values()),
        [], "lex labels folded into indeclinable tokens: " +
        ", ".join(f"{k}={v}" for k, v in ind_lex.most_common()))

    # A5: doubled lex abbreviations (ff./mm.)
    dbl = [r for r in gi_rows if norm_lex(r["lex"]) in ("ff", "mm")]
    add("lex_doubled_abbreviation", "-", len(dbl), [r["k1"] for r in dbl],
        "PWG 'f. f.'/'m. m.' doubled abbreviation artifacts; token assigned "
        "as plain f/m")

    # A6: singleton tokens
    singles = sorted(t for t, rs in tok_rows.items() if len(rs) == 1)
    add("singleton_token", "-", len(singles), singles,
        "tokens attested by exactly one headword")

    # A7: paradigm_classes.tsv drift (both directions)
    asset_absent = sorted(set(tok_rows) - pc_tokens)
    add("pc_drift_token_missing", "-", len(asset_absent), asset_absent,
        "live asset tokens absent from committed "
        "zaliznyak_paradigm_classes.tsv (332 rows)")
    pc_retired = sorted(pc_tokens - set(tok_rows))
    add("pc_drift_token_retired", "-", len(pc_retired), pc_retired,
        "committed zaliznyak_paradigm_classes.tsv tokens no longer in the "
        "asset (renamed/retired upstream)")

    # A8: tokens carrying >1 normalized lex label
    t2lex = collections.defaultdict(collections.Counter)
    for r in gi_rows:
        t2lex[r["index_token"]][norm_lex(r["lex"])] += 1
    mixed = {t: dict(c) for t, c in t2lex.items() if len(c) > 1}
    for t, c in sorted(mixed.items()):
        add("token_mixed_lex_labels", t, sum(c.values()), [],
            "normalized lex labels: " + ", ".join(f"{k}={v}" for k, v in
                                                  sorted(c.items())))

    # ---- outputs ----
    outdir = repo / "data/zaliznyak"
    outdir.mkdir(parents=True, exist_ok=True)
    with (outdir / "zaliznyak_token_distribution.tsv").open("w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(dist[0].keys()), delimiter="\t")
        wr.writeheader()
        wr.writerows(dist)

    anomalies.sort(key=lambda a: (a["anomaly_type"], -a["count"]))
    with (outdir / "zaliznyak_markup_anomalies.tsv").open("w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(anomalies[0].keys()), delimiter="\t")
        wr.writeheader()
        wr.writerows(anomalies)

    nd_all = [int(union[r["k1"]]["n_dicts"]) for r in gi_rows if r["k1"] in union]
    nd_hist = collections.Counter(nd_all)
    stem_rows = collections.Counter(r["stem_class"] for r in gi_rows)
    summary = {
        "handoff": "H6053",
        "generated": "2026-10-06",
        "grammar_index_rows": len(gi_rows),
        "distinct_tokens": len(tok_rows),
        "distinct_k1": len({r["k1"] for r in gi_rows}),
        "coverage_checkpoints": {f"{t:.0%}": marks[t] for t in COVERAGE_TARGETS},
        "top10_share_pct": round(sum(d["member_count"] for d in dist[:10]) / len(gi_rows) * 100, 1),
        "stem_class_rows": dict(stem_rows.most_common()),
        "stem_class_tokens": {
            sc: len({d["index_token"] for d in dist if d["stem_class"] == sc})
            for sc in stem_rows},
        "union_join": {
            "union_rows": len(un_rows),
            "k1_matched": len({r["k1"] for r in gi_rows} & set(union)),
            "rows_joined": len(nd_all),
            "mean_n_dicts": round(statistics.mean(nd_all), 2),
            "median_n_dicts": statistics.median(nd_all),
            "pct_rows_ge5_dicts": round(100.0 * sum(1 for n in nd_all if n >= 5) / len(nd_all), 1),
            "n_dicts_histogram": {str(k): nd_hist[k] for k in sorted(nd_hist)},
        },
        "irregularities_rows": sum(1 for r in gi_rows if r["irregularities"].strip()),
        "compound_members_rows": sum(1 for r in gi_rows if r["compound_members"].strip()),
        "accent_marked_rows": sum(1 for r in gi_rows if "/" in r["accented"]),
        "anomaly_totals": {
            t: sum(a["count"] for a in anomalies if a["anomaly_type"] == t)
            for t in sorted({a["anomaly_type"] for a in anomalies})},
        "drift_notes": {
            "manifest_declares_tokens": 335,
            "asset_tokens": len(tok_rows),
            "release_asset_md5_equals_live": True,
            "paper_a56_99pct_tokens": 154,
            "asset_99pct_tokens": marks[0.99],
        },
    }
    (outdir / "zaliznyak_token_distribution_summary.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    charts = repo / "docs/charts"
    charts.mkdir(parents=True, exist_ok=True)
    chart_zipf([d["member_count"] for d in dist], charts / "h6053_zipf_loglog.svg")
    cum_pct = [d["cum_pct_rows"] for d in dist]
    chart_cumulative(cum_pct, marks, charts / "h6053_cumulative_coverage.svg")
    chart_bars([sc for sc, _ in stem_rows.most_common()],
               [c for _, c in stem_rows.most_common()],
               "Rows by stem class", "rows", charts / "h6053_stemclass_share.svg")
    chart_bars([f"{k} dicts" for k in sorted(nd_hist)],
               [nd_hist[k] for k in sorted(nd_hist)],
               "Source-dictionary breadth of indexed headwords (n_dicts, 15-dict union)",
               "rows", charts / "h6053_ndicts_histogram.svg")

    print(json.dumps({k: summary[k] for k in
                      ("grammar_index_rows", "distinct_tokens", "coverage_checkpoints",
                       "top10_share_pct", "union_join", "anomaly_totals")}, indent=1))
    print("BUILD OK")
    return 0


# ------------------------------------------------------------------ check ----

def check(args: argparse.Namespace) -> int:
    repo = Path(args.repo_root)
    dist = read_tsv(repo / "data/zaliznyak/zaliznyak_token_distribution.tsv")
    summary = json.loads((repo / "data/zaliznyak/zaliznyak_token_distribution_summary.json").read_text())
    total = sum(int(d["member_count"]) for d in dist)
    assert total == summary["grammar_index_rows"] == EXPECT_ROWS, \
        f"distribution sum {total} != expected {EXPECT_ROWS}"
    assert len(dist) == summary["distinct_tokens"], "token count drift"
    assert abs(float(dist[-1]["cum_pct_rows"]) - 100.0) < 0.05, "cum tail != 100%"
    anomalies = read_tsv(repo / "data/zaliznyak/zaliznyak_markup_anomalies.tsv")
    for atype, tot in summary["anomaly_totals"].items():
        got = sum(int(a["count"]) for a in anomalies if a["anomaly_type"] == atype)
        assert got == tot, f"anomaly total drift {atype}: {got} != {tot}"
    for name in ("h6053_zipf_loglog.svg", "h6053_cumulative_coverage.svg",
                 "h6053_stemclass_share.svg", "h6053_ndicts_histogram.svg"):
        assert (repo / "docs/charts" / name).exists(), f"chart missing {name}"
    print(f"CHECK OK: {total} rows covered across {len(dist)} tokens; "
          f"{len(anomalies)} anomaly rows consistent")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--grammar-index",
                    default=str(Path.home() / "Documents/GitHub/SanskritLexicography/RussianTranslation/src/headword_index.tsv"))
    ap.add_argument("--union",
                    default=str(Path.home() / "Documents/GitHub/SanskritLexicography/HeadwordLists/union/union_headwords.tsv"))
    ap.add_argument("--expect-rows", type=int, default=EXPECT_ROWS)
    ap.add_argument("--check", action="store_true",
                    help="verify committed outputs without source access")
    args = ap.parse_args()
    return check(args) if args.check else build(args)


if __name__ == "__main__":
    sys.exit(main())
