#!/usr/bin/env python
"""Corpus-wide sandhi reference pages — roadmap Phase 4, surface 3 (H902).

A LOOK-UP reference (distinct from the graded curriculum's syllabus and the
Gītā-only frequency page): every recurring sandhi in the 17-text corpus, grouped
by rule-class (visarga / anusvāra-nasal / vowel coalescence / consonant), each
class ranked by frequency with corpus counts + an attested example. "I met
`ḥ t → s t` — what class is that, how common, what else is in it?"

Consumes data/sandhi/corpus_sandhi.tsv (H900/H901) — no new data, a reference
view. Each class shows its top rules (the long consonant tail is summarised, not
dumped: 3,794 consonant rules would drown the page).

Output: reading/sandhi/reference/index.html (theme-aware, self-contained).

Public/MIT, credit Dr. Mārcis Gasūns.
Usage: python scripts/build_sandhi_reference.py [--top 50]
"""
import argparse
import csv
import html
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "sandhi" / "corpus_sandhi.tsv"
OUT_HTML = ROOT / "reading" / "sandhi" / "reference" / "index.html"

# display order + one-line teaching gloss per class
CLASS_ORDER = [
    ("anusvāra / nasal", "final <b>m</b> → anusvāra <b>ṃ</b> before a consonant — the most mechanical, most frequent class."),
    ("visarga", "final visarga <b>ḥ</b> → <b>s/ś/ṣ/r/o/Ø</b> conditioned by the following sound."),
    ("vowel coalescence", "two meeting vowels merge (<b>a a → ā</b>) or form a glide/guṇa/vṛddhi — few rules, very high frequency."),
    ("consonant / other", "final-stop assimilation (<b>t → d/j/n/c…</b>) and the long tail of rarer junctions."),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=50, help="rows shown per class")
    ap.add_argument("--corpus", default=str(CORPUS))
    args = ap.parse_args()

    by_cat = defaultdict(list)
    grand = 0
    for r in csv.DictReader(open(args.corpus, encoding="utf-8"), delimiter="\t"):
        by_cat[r["category"]].append(r)
        grand += int(r["global_count"])

    sections, nav = [], []
    for cat, gloss in CLASS_ORDER:
        rows = sorted(by_cat.get(cat, []), key=lambda r: -int(r["global_count"]))
        if not rows:
            continue
        cat_total = sum(int(r["global_count"]) for r in rows)
        shown = rows[:args.top]
        shown_total = sum(int(r["global_count"]) for r in shown)
        tail_n = len(rows) - len(shown)
        tail_occ = cat_total - shown_total
        anchor = cat.split()[0].replace("/", "").lower()
        nav.append("<a href='#%s'>%s</a> <span class='c'>(%d)</span>"
                   % (anchor, html.escape(cat), len(rows)))
        rowhtml = "\n".join(
            "<tr><td class='r'>{r}</td><td class='n'>{n}</td><td class='n'>{p}%</td>"
            "<td class='n'>{nt}</td><td class='ex'>{ex}</td></tr>".format(
                r=html.escape(x["rule"]), n=int(x["global_count"]),
                p=round(100.0 * int(x["global_count"]) / cat_total, 1),
                nt=x["n_texts"],
                ex=html.escape((x.get("examples", "") or "").split(" · ")[0][:64]))
            for x in shown)
        tail = ("<p class='tail'>… and <b>%d</b> rarer %s rules (%d occurrences, "
                "%.0f%% of the class) — the long tail; see "
                "<a href='https://github.com/gasyoun/kosha/blob/main/data/sandhi/corpus_sandhi.tsv'>corpus_sandhi.tsv</a>.</p>"
                % (tail_n, html.escape(cat), tail_occ,
                   100.0 * tail_occ / cat_total if cat_total else 0)) if tail_n else ""
        sections.append(
            "<section id='{a}'><h2>{cat} <span class='cov'>{tot} occ · {share}% of corpus</span></h2>"
            "<p class='gloss'>{gloss}</p><div class='scroll'><table><thead><tr><th>rule</th>"
            "<th>count</th><th>of class</th><th>texts</th><th>example</th></tr></thead>"
            "<tbody>{rows}</tbody></table></div>{tail}</section>".format(
                a=anchor, cat=html.escape(cat), tot=cat_total,
                share=round(100.0 * cat_total / grand, 1) if grand else 0,
                gloss=gloss, rows=rowhtml, tail=tail))

    total_rules = sum(len(v) for v in by_cat.values())
    page = _PAGE.format(nrules=total_rules, total=grand,
                        nav=" · ".join(nav), sections="\n".join(sections),
                        top=args.top)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(page, encoding="utf-8", newline="\n")
    print("wrote %s — %d rules across %d classes (top %d shown per class)"
          % (OUT_HTML, total_rules, len(sections), args.top))


_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sanskrit sandhi — corpus reference by class</title>
<meta name="description" content="Every recurring Sanskrit sandhi across a 17-text corpus, grouped by class and ranked by frequency.">
<style>
 :root{{--bg:#fbfaf7;--fg:#1c1a17;--muted:#6b6660;--line:#e6e1d8;--card:#fff;--accent:#7a4f2b}}
 @media(prefers-color-scheme:dark){{:root{{--bg:#17150f;--fg:#ece7dd;--muted:#9c948a;--line:#2e2a22;--card:#1f1c15;--accent:#d9a066}}}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
 .wrap{{max-width:880px;margin:0 auto;padding:1.5rem 1.1rem 4rem}}
 h1{{font-size:1.5rem;margin:.2rem 0 .3rem}} .sub{{color:var(--muted);font-size:.9rem;margin:0 0 1rem}}
 .nav{{background:var(--card);border:1px solid var(--line);border-radius:.5rem;padding:.6rem .9rem;font-size:.9rem;margin-bottom:1.4rem}}
 .nav a{{color:var(--accent);text-decoration:none}} .nav .c{{color:var(--muted)}}
 section{{margin-bottom:1.8rem}} h2{{font-size:1.1rem;border-bottom:2px solid var(--line);padding-bottom:.2rem}}
 h2 .cov{{color:var(--muted);font-weight:400;font-size:.82rem;float:right}}
 .gloss{{color:var(--muted);font-size:.9rem;margin:.3rem 0 .6rem}}
 .scroll{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:.9rem}}
 th,td{{text-align:left;padding:.35rem .55rem;border-bottom:1px solid var(--line);vertical-align:top}}
 th{{color:var(--muted);font-weight:600}} td.r{{font-size:1.05rem;white-space:nowrap}}
 td.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}} td.ex{{color:var(--muted);font-size:.82rem}}
 .tail{{color:var(--muted);font-size:.85rem;margin:.4rem 0 0}} a{{color:var(--accent)}}
 footer{{margin-top:1.6rem;color:var(--muted);font-size:.8rem}}
</style></head><body><div class="wrap">
 <h1>Sanskrit sandhi — corpus reference by class</h1>
 <p class="sub">{nrules} corpus-attested rules over {total} junctions (17 texts), grouped by class and ranked by frequency (top {top} per class). A look-up companion to the <a href="../curriculum/">graded curriculum</a>.</p>
 <div class="nav">{nav}</div>
 {sections}
 <footer>Built by <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_reference.py">build_sandhi_reference.py</a>
  over <a href="https://github.com/gasyoun/kosha/blob/main/data/sandhi/corpus_sandhi.tsv">corpus_sandhi.tsv</a>. Dr. Mārcis Gasūns.</footer>
</div></body></html>
"""


if __name__ == "__main__":
    main()
