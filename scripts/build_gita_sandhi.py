#!/usr/bin/env python
"""H872 / roadmap W2 — Gītā sandhi layer.

Aggregates the per-word sandhi rule carried in the W0 master
(data/gita/gita_gold_master.tsv, `sandhi` field, e.g. `aḥ a → o '`) into a
**corpus-attested, frequency-ranked** sandhi table for the whole Bhagavadgītā —
the first such table in the ecosystem — plus a self-contained teaching page.

Outputs:
  * data/gita/gita_sandhi.tsv     rule · category · count · pct · examples
  * reading/sandhi/index.html     ranked sandhi-rules page (theme-aware)

Public/MIT, credit Dr. Mārcis Gasūns. Usage: python scripts/build_gita_sandhi.py
"""
import csv
import html
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "data" / "gita" / "gita_gold_master.tsv"
OUT_TSV = ROOT / "data" / "gita" / "gita_sandhi.tsv"
OUT_HTML = ROOT / "reading" / "sandhi" / "index.html"

VOWELS = set("aāiīuūṛṝḷeaioauē")


def categorise(rule):
    junction = rule.split("→")[0].strip()
    left = junction.replace(" ", "")
    if "ḥ" in junction:
        return "visarga"
    if "ṃ" in rule.split("→")[-1] or junction.startswith("m"):
        return "anusvāra / nasal"
    if left and all(ch in VOWELS for ch in left):
        return "vowel coalescence"
    return "consonant / other"


def main():
    rows = list(csv.DictReader(open(MASTER, encoding="utf-8"), delimiter="\t"))
    counts = Counter()
    examples = defaultdict(list)
    for r in rows:
        s = r["sandhi"].strip()
        if not s:
            continue
        counts[s] += 1
        if len(examples[s]) < 4:
            examples[s].append("%s %s" % (r["verse"], r["iast"]))
    total = sum(counts.values())

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["rule", "category", "count", "pct", "examples"])
        for rule, n in counts.most_common():
            w.writerow([rule, categorise(rule), n, round(100.0 * n / total, 2),
                        " · ".join(examples[rule])])

    # category totals
    cat = Counter()
    for rule, n in counts.items():
        cat[categorise(rule)] += n

    rows_html = "\n".join(
        "<tr><td class='r'>{r}</td><td>{c}</td><td class='n'>{n}</td>"
        "<td class='n'>{p}%</td><td class='ex'>{ex}</td></tr>".format(
            r=html.escape(rule), c=html.escape(categorise(rule)), n=n,
            p=round(100.0 * n / total, 1), ex=html.escape(" · ".join(examples[rule])))
        for rule, n in counts.most_common())
    cat_html = " · ".join("<b>%s</b> %d" % (html.escape(k), v)
                          for k, v in cat.most_common())

    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bhagavadgītā sandhi — frequency-ranked rules</title>
<meta name="description" content="Corpus-attested, frequency-ranked sandhi rules of the whole Bhagavadgita.">
<style>
 :root{{--bg:#fbfaf7;--fg:#1c1a17;--muted:#6b6660;--line:#e6e1d8;--card:#fff;--accent:#7a4f2b;--chip:#f2ede3}}
 @media(prefers-color-scheme:dark){{:root{{--bg:#17150f;--fg:#ece7dd;--muted:#9c948a;--line:#2e2a22;--card:#1f1c15;--accent:#d9a066;--chip:#2a251c}}}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
 .wrap{{max-width:820px;margin:0 auto;padding:1.5rem 1.1rem 4rem}}
 h1{{font-size:1.5rem;margin:.2rem 0 .3rem}} .sub{{color:var(--muted);font-size:.9rem;margin:0 0 1rem}}
 .cats{{background:var(--card);border:1px solid var(--line);border-radius:.5rem;padding:.6rem .9rem;font-size:.9rem;margin-bottom:1.2rem}}
 .scroll{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:.92rem}}
 th,td{{text-align:left;padding:.4rem .6rem;border-bottom:1px solid var(--line);vertical-align:top}}
 th{{color:var(--muted);font-weight:600;position:sticky;top:0;background:var(--bg)}}
 td.r{{font-size:1.05rem;white-space:nowrap}} td.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
 td.ex{{color:var(--muted);font-size:.82rem}} a{{color:var(--accent)}}
 footer{{margin-top:1.6rem;color:var(--muted);font-size:.8rem}}
</style></head><body><div class="wrap">
 <h1>Bhagavadgītā — sandhi rules, frequency-ranked</h1>
 <p class="sub">{n} distinct rules over {t} sandhi junctions across all 18 adhyāyas — corpus-attested from the hand-curated word analysis. A learner's map of which sandhis actually recur.</p>
 <div class="cats">By type: {cats}</div>
 <div class="scroll"><table>
  <thead><tr><th>rule</th><th>type</th><th>count</th><th>share</th><th>examples (verse · form)</th></tr></thead>
  <tbody>
{rows}
  </tbody></table></div>
 <footer>Source: hand-curated analysis in SanskritGrammar/Concordance/Gita.xlsm (Dr. Mārcis Gasūns), via
  <a href="https://github.com/gasyoun/kosha/blob/main/data/gita/gita_sandhi.tsv">data/gita/gita_sandhi.tsv</a>.
  Part of the <a href="../">Gītā reading packs</a>.</footer>
</div></body></html>
""".format(n=len(counts), t=total, cats=cat_html, rows=rows_html)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(page, encoding="utf-8", newline="\n")
    print("wrote %s (%d rules, %d junctions) and %s" % (OUT_TSV, len(counts), total, OUT_HTML))
    print("categories:", dict(cat.most_common()))


if __name__ == "__main__":
    main()
