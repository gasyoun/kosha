#!/usr/bin/env python
"""Graded sandhi curriculum — roadmap Phase 4, surface 2 (H902).

Turns the corpus-wide frequency-ranked sandhi table (data/sandhi/corpus_sandhi.tsv,
H900/H901) into an ORDERED teaching syllabus: "learn these N junctions and you can
resolve X % of all sandhi in the corpus." The one genuinely new pedagogy artifact
of the programme — the rest of Phase 4 (reader hover, drills, reference tables)
consumes existing tables directly; this one needs a difficulty model.

Rules are ordered by a PRIORITY score (highest-value + easiest first), per MG's
14-07-2026 ruling `frequency × class × environment-generality`. The weights live
in a visible, tunable config (data/sandhi/difficulty_weights.json) — NOT hard-coded
here, per that ruling — so the syllabus can be re-tuned by editing the JSON and
re-running, without touching this script.

Outputs:
  * data/sandhi/sandhi_curriculum.tsv        rank · rule · category · count · pct ·
                                             cumulative_pct · family_size · priority · lesson
  * reading/sandhi/curriculum/index.html      theme-aware graded-syllabus page

Public/MIT, credit Dr. Mārcis Gasūns. Usage:
  python scripts/build_sandhi_curriculum.py [--weights data/sandhi/difficulty_weights.json]
"""
import argparse
import csv
import html
import json
import math
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "sandhi" / "corpus_sandhi.tsv"
WEIGHTS = ROOT / "data" / "sandhi" / "difficulty_weights.json"
OUT_TSV = ROOT / "data" / "sandhi" / "sandhi_curriculum.tsv"
OUT_HTML = ROOT / "reading" / "sandhi" / "curriculum" / "index.html"


def family_key(rule):
    """(left-input phoneme, left-output phoneme) — rules sharing it are one
    principle, e.g. all `m X → ṃ X` share `(m, ṃ)`. A large family = a general
    rule worth teaching once."""
    ins, _, outs = rule.partition("→")
    in_left = (ins.split() or [""])[0]
    out_left = (outs.split() or [""])[0]
    return (in_left, out_left)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default=str(WEIGHTS))
    ap.add_argument("--corpus", default=str(CORPUS))
    args = ap.parse_args()

    w = json.loads(Path(args.weights).read_text(encoding="utf-8"))
    freq_exp = w.get("frequency_exponent", 1.0)
    class_w = {k: v for k, v in w.get("class_weight", {}).items() if not k.startswith("_")}
    env_w = w.get("environment_generality_weight", 0.15)
    step = w.get("lesson_coverage_step", 0.1)
    min_count = w.get("min_count", 1)

    rows = [r for r in csv.DictReader(open(args.corpus, encoding="utf-8"), delimiter="\t")
            if int(r["global_count"]) >= min_count]
    total = sum(int(r["global_count"]) for r in rows)

    fam = Counter(family_key(r["rule"]) for r in rows)
    for r in rows:
        c = int(r["global_count"])
        cw = class_w.get(r["category"], 0.5)
        fs = fam[family_key(r["rule"])]
        r["_priority"] = (c ** freq_exp) * cw * (1 + env_w * math.log(1 + fs))
        r["_count"] = c

    rows.sort(key=lambda r: -r["_priority"])

    # group into lessons by cumulative RAW coverage (each lesson adds ~step of
    # all corpus sandhi occurrences), so "finish lesson k → read X % of sandhi".
    cum = 0
    lesson = 1
    lesson_target = step
    out_rows = []
    for i, r in enumerate(rows, 1):
        cum += r["_count"]
        cum_pct = cum / total if total else 0
        out_rows.append({
            "rank": i, "rule": r["rule"], "category": r["category"],
            "count": r["_count"], "pct": round(100.0 * r["_count"] / total, 3),
            "cumulative_pct": round(100.0 * cum_pct, 2),
            "family_size": fam[family_key(r["rule"])],
            "priority": round(r["_priority"], 1), "lesson": lesson,
            "examples": r.get("examples", ""),
        })
        if cum_pct >= lesson_target and i < len(rows):
            lesson += 1
            lesson_target += step

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
        wtr = csv.writer(f, delimiter="\t", lineterminator="\n")
        wtr.writerow(["rank", "rule", "category", "count", "pct", "cumulative_pct",
                      "family_size", "priority", "lesson"])
        for o in out_rows:
            wtr.writerow([o["rank"], o["rule"], o["category"], o["count"], o["pct"],
                          o["cumulative_pct"], o["family_size"], o["priority"], o["lesson"]])

    _write_html(out_rows, total, len(rows), step)

    # milestones: rules needed to reach 50/80/90 %
    for target in (50, 80, 90):
        n = next((o["rank"] for o in out_rows if o["cumulative_pct"] >= target), len(out_rows))
        print("learn %3d rules → read %d%% of all corpus sandhi" % (n, target))
    print("wrote %s (%d rules, %d lessons) and %s"
          % (OUT_TSV, len(out_rows), out_rows[-1]["lesson"] if out_rows else 0, OUT_HTML))


def _write_html(rows, total, n_rules, step):
    lessons = {}
    for o in rows:
        lessons.setdefault(o["lesson"], []).append(o)
    blocks = []
    for lk in sorted(lessons):
        items = lessons[lk]
        cov = items[-1]["cumulative_pct"]
        rowhtml = "\n".join(
            "<tr><td class='r'>{r}</td><td>{c}</td><td class='n'>{p}%</td>"
            "<td class='ex'>{ex}</td></tr>".format(
                r=html.escape(o["rule"]), c=html.escape(o["category"]),
                p=o["pct"], ex=html.escape((o["examples"] or "").split(" · ")[0][:70]))
            for o in items)
        blocks.append(
            "<section><h2>Lesson {k} <span class='cov'>→ {cov}% cumulative</span></h2>"
            "<div class='scroll'><table><thead><tr><th>rule</th><th>type</th>"
            "<th>share</th><th>example</th></tr></thead><tbody>{rows}</tbody>"
            "</table></div></section>".format(k=lk, cov=cov, rows=rowhtml))
    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sanskrit sandhi — graded curriculum</title>
<meta name="description" content="A corpus-ranked graded syllabus of Sanskrit sandhi: learn the highest-value rules first.">
<style>
 :root{{--bg:#fbfaf7;--fg:#1c1a17;--muted:#6b6660;--line:#e6e1d8;--card:#fff;--accent:#7a4f2b;--chip:#f2ede3}}
 @media(prefers-color-scheme:dark){{:root{{--bg:#17150f;--fg:#ece7dd;--muted:#9c948a;--line:#2e2a22;--card:#1f1c15;--accent:#d9a066;--chip:#2a251c}}}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
 .wrap{{max-width:860px;margin:0 auto;padding:1.5rem 1.1rem 4rem}}
 h1{{font-size:1.5rem;margin:.2rem 0 .3rem}} .sub{{color:var(--muted);font-size:.9rem;margin:0 0 1rem}}
 .mile{{background:var(--card);border:1px solid var(--line);border-radius:.5rem;padding:.7rem .9rem;font-size:.95rem;margin-bottom:1.4rem}}
 .mile b{{color:var(--accent)}}
 section{{margin-bottom:1.6rem}} h2{{font-size:1.05rem;border-bottom:2px solid var(--line);padding-bottom:.2rem}}
 h2 .cov{{color:var(--muted);font-weight:400;font-size:.85rem;float:right}}
 .scroll{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:.9rem}}
 th,td{{text-align:left;padding:.35rem .55rem;border-bottom:1px solid var(--line);vertical-align:top}}
 th{{color:var(--muted);font-weight:600}} td.r{{font-size:1.05rem;white-space:nowrap}}
 td.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}} td.ex{{color:var(--muted);font-size:.82rem}}
 a{{color:var(--accent)}} footer{{margin-top:1.6rem;color:var(--muted);font-size:.8rem}}
</style></head><body><div class="wrap">
 <h1>Sanskrit sandhi — a graded curriculum</h1>
 <p class="sub">{n} corpus-attested rules over {t} junctions (17 texts), ordered highest-value + easiest first. Each lesson adds ~{step}% of all the sandhi you'll actually meet when reading.</p>
 <div class="mile">{miles}</div>
 {blocks}
 <footer>Ordered by the tunable weights in
  <a href="https://github.com/gasyoun/kosha/blob/main/data/sandhi/difficulty_weights.json">difficulty_weights.json</a>
  (frequency × class × environment-generality). Built by
  <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_curriculum.py">build_sandhi_curriculum.py</a>
  over <a href="https://github.com/gasyoun/kosha/blob/main/data/sandhi/corpus_sandhi.tsv">corpus_sandhi.tsv</a>.
  Dr. Mārcis Gasūns.</footer>
</div></body></html>
"""
    miles = " · ".join(
        "<b>%d rules</b> → %d%%" % (
            next((o["rank"] for o in rows if o["cumulative_pct"] >= t), len(rows)), t)
        for t in (50, 80, 90))
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(page.format(n=n_rules, t=total, step=int(step * 100),
                                    miles=miles, blocks="\n".join(blocks)),
                        encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
