#!/usr/bin/env python
"""H876 / roadmap W6 — render the upasarga-semantics dataset as a browsable page.

Reads data/gita/upasarga_semantics.tsv and writes reading/upasarga/index.html:
one card per root (base sense + each preverb-modified sense), corpus-frequency
sorted. Theme-aware, self-contained.
"""
import csv
import html
import sys
from collections import OrderedDict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "gita" / "upasarga_semantics.tsv"
OUT = ROOT / "reading" / "upasarga" / "index.html"


def main():
    roots = OrderedDict()
    for r in csv.DictReader(open(SRC, encoding="utf-8"), delimiter="\t"):
        d = roots.setdefault(r["root"], {"base": "", "count": 0, "variants": []})
        if not r["preverb"]:
            d["base"] = r["sense"]
            d["count"] = int(r["count"]) if r["count"].isdigit() else 0
        else:
            d["variants"].append((r["preverb"], r["combined"], r["sense"]))
    ordered = sorted(roots.items(), key=lambda kv: (-kv[1]["count"], kv[0]))
    n_var = sum(len(v["variants"]) for _, v in ordered)

    cards = []
    for root, d in ordered:
        vs = "".join(
            "<li><span class='pv'>{c}</span> <span class='ar'>→</span> {s}</li>".format(
                c=html.escape(comb), s=html.escape(sense))
            for pre, comb, sense in d["variants"])
        cnt = ("<span class='cnt'>%d×</span>" % d["count"]) if d["count"] else ""
        cards.append(
            "<div class='card'><div class='rt'>{r} {cnt}<span class='base'>{b}</span></div>"
            "{vl}</div>".format(r=html.escape(root), cnt=cnt, b=html.escape(d["base"]),
                                vl=("<ul>%s</ul>" % vs) if vs else ""))

    page = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sanskrit upasarga semantics — root × preverb → sense</title>
<meta name="description" content="How preverbs (upasarga) shift Sanskrit verb-root meaning, attested in the Bhagavadgita.">
<style>
 :root{{--bg:#fbfaf7;--fg:#1c1a17;--muted:#6b6660;--line:#e6e1d8;--card:#fff;--accent:#7a4f2b;--chip:#f2ede3}}
 @media(prefers-color-scheme:dark){{:root{{--bg:#17150f;--fg:#ece7dd;--muted:#9c948a;--line:#2e2a22;--card:#1f1c15;--accent:#d9a066;--chip:#2a251c}}}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
 .wrap{{max-width:900px;margin:0 auto;padding:1.5rem 1.1rem 4rem}}
 h1{{font-size:1.5rem;margin:.2rem 0 .3rem}} .sub{{color:var(--muted);font-size:.9rem;margin:0 0 1.2rem}}
 .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:.8rem}}
 .card{{background:var(--card);border:1px solid var(--line);border-radius:.55rem;padding:.7rem .85rem}}
 .rt{{font-size:1.12rem;font-weight:600}} .base{{font-weight:400;color:var(--muted);margin-left:.4rem;font-size:.92rem}}
 .cnt{{color:var(--accent);font-size:.75rem;margin-left:.3rem;font-weight:600}}
 ul{{list-style:none;margin:.5rem 0 0;padding:0}} li{{font-size:.9rem;padding:.12rem 0;border-top:1px solid var(--line)}}
 .pv{{color:var(--accent);font-weight:600}} .ar{{color:var(--muted)}}
 footer{{margin-top:1.6rem;color:var(--muted);font-size:.8rem}} a{{color:var(--accent)}}
</style></head><body><div class="wrap">
 <h1>Sanskrit upasarga semantics — how preverbs shift the root</h1>
 <p class="sub">{nr} verb roots attested in the Bhagavadgītā, with {nv} preverb-modified senses (√vac ‘speak’ → pra-vac ‘declare’; √as ‘be’ → sam-ni-as ‘renounce’). A compositional dimension the dictionaries are thin on. Sorted by corpus frequency.</p>
 <div class="grid">
{cards}
 </div>
 <footer>Source: hand-curated <code>verbs</code> sheet of SanskritGrammar/Concordance/Gita.xlsm (Dr. Mārcis Gasūns), via
 <a href="https://github.com/gasyoun/kosha/blob/main/data/gita/upasarga_semantics.tsv">data/gita/upasarga_semantics.tsv</a>.
 Part of the <a href="../">Gītā reading packs</a>.</footer>
</div></body></html>
""".format(nr=len(ordered), nv=n_var, cards="\n".join(cards))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8", newline="\n")
    print("wrote %s — %d roots, %d variants" % (OUT, len(ordered), n_var))


if __name__ == "__main__":
    main()
