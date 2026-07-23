#!/usr/bin/env python
"""Vocabulary drills — in-browser page over data/frequency/vocab_drills.json (H1460).

L4 "surface" move for the frequency-graded vocabulary drill bank built by
H947: that handoff shipped the item bank as an Anki .apkg deck plus a
read-only curriculum table only — there was no learner-facing quiz page.
This script is a standalone generator that reads the already-committed
data/frequency/vocab_drills.json directly (NOT docs/cards/, which is
gitignored and absent in a fresh worktree) and writes a self-contained MCQ
web quiz, following the reading/morphology/drills/index.html shell.

Distinct from the morphology/sandhi shells: vocab prompt/answer text is
dictionary rendered_html (tag-stripped but still carrying literal &, <, >,
quotes), so every user-facing string is escaped at DOM insertion via esc()
(copied from reading/index.html) -- the one place this generator diverges
from the sibling shells.

Public/MIT, credit Dr. Mārcis Gasūns. Usage:
  python scripts/build_vocab_drills_page.py [--seed 20260714]
"""
import argparse
import json
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
SRC_JSON = ROOT / "data" / "frequency" / "vocab_drills.json"
OUT_HTML = ROOT / "reading" / "vocabulary" / "drills" / "index.html"


def mcq_choices(rng, answer, distractors):
    # dedupe + drop empties so a sparse item never yields a choice equal to
    # the answer or an empty option; may leave < 4 choices, that's fine
    seen = {answer}
    choices = [answer]
    for d in distractors:
        if not d or d in seen:
            continue
        seen.add(d)
        choices.append(d)
    rng.shuffle(choices)
    return choices


def build_payload(items, seed):
    rng = random.Random(seed)
    out = []
    for it in items:
        choices = mcq_choices(rng, it["answer"], it.get("distractors", []))
        out.append({
            "id": it["id"],
            "type": it["type"],
            "prompt": it["prompt"],
            "answer": it["answer"],
            "choices": choices,
            "rank": it["rank"],
        })
    return out


def write_html(payload, n_total):
    items_json = json.dumps(payload, ensure_ascii=False)
    page = _PAGE.format(n=n_total, items_json=items_json)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(page, encoding="utf-8", newline="\n")


_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sanskrit vocabulary — drills</title>
<meta name="description" content="A self-contained multiple-choice Sanskrit vocabulary drill quiz, graded by corpus core-vocabulary rank.">
<style>
 :root{{--bg:#fbfaf7;--fg:#1c1a17;--muted:#6b6660;--line:#e6e1d8;--card:#fff;--accent:#7a4f2b;--chip:#f2ede3;--good:#3a7d44;--bad:#b5462f}}
 @media(prefers-color-scheme:dark){{:root{{--bg:#17150f;--fg:#ece7dd;--muted:#9c948a;--line:#2e2a22;--card:#1f1c15;--accent:#d9a066;--chip:#2a251c;--good:#7fbf87;--bad:#e08a70}}}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
 .wrap{{max-width:720px;margin:0 auto;padding:1.5rem 1.1rem 4rem}}
 h1{{font-size:1.5rem;margin:.2rem 0 .3rem}} .sub{{color:var(--muted);font-size:.9rem;margin:0 0 1rem}}
 .bar{{display:flex;gap:.6rem;align-items:center;margin-bottom:1rem;font-size:.85rem;color:var(--muted);flex-wrap:wrap}}
 select,button{{font:inherit;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:.4rem;padding:.35rem .6rem;cursor:pointer}}
 button.primary{{background:var(--accent);color:var(--bg);border-color:var(--accent)}}
 .score{{margin-left:auto}}
 .card{{background:var(--card);border:1px solid var(--line);border-radius:.6rem;padding:1.1rem 1.2rem;min-height:14rem}}
 .tags{{color:var(--muted);font-size:.78rem;margin-bottom:.6rem}}
 .q{{font-size:1.15rem;margin-bottom:1rem}}
 .opt{{display:block;width:100%;text-align:left;margin-bottom:.5rem;padding:.55rem .8rem;border-radius:.4rem;border:1px solid var(--line);background:var(--chip);color:var(--fg);font:inherit;cursor:pointer}}
 .opt:hover{{border-color:var(--accent)}}
 .opt.correct{{border-color:var(--good);background:color-mix(in srgb, var(--good) 18%, var(--chip))}}
 .opt.wrong{{border-color:var(--bad);background:color-mix(in srgb, var(--bad) 18%, var(--chip))}}
 .done{{text-align:center;padding:2rem 1rem}}
 footer{{margin-top:1.6rem;color:var(--muted);font-size:.8rem}}
 a{{color:var(--accent)}}
</style></head><body><div class="wrap">
 <h1>Sanskrit vocabulary — drills</h1>
 <p class="sub">{n} recognition / recall practice items over the frequency-graded core vocabulary, multiple choice. A companion to the <a href="../curriculum/">graded curriculum</a> (read the syllabus there, drill active recall here).</p>
 <div class="bar">
  <label>Type <select id="typeFilter"><option value="">all</option><option value="recognition">recognition</option><option value="recall">recall</option></select></label>
  <label>Rank &le; <select id="rankFilter"><option value="200">200</option><option value="500">500</option><option value="1000">1000</option><option value="999999" selected>all</option></select></label>
  <button id="restart">restart</button>
  <span class="score" id="score">0 / 0</span>
 </div>
 <div class="card" id="card"></div>
 <footer>Item bank: <a href="https://github.com/gasyoun/kosha/blob/main/data/frequency/vocab_drills.json">vocab_drills.json</a> &middot;
  Anki deck: <a href="https://github.com/gasyoun/kosha/blob/main/data/frequency/vocab_curriculum.apkg">vocab_curriculum.apkg</a> &middot;
  built by <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_vocab_drills_page.py">build_vocab_drills_page.py</a>.
  Dr. Mārcis Gasūns.</footer>
</div>
<script>
const ALL_ITEMS = {items_json};
let pool = [], pos = 0, right = 0, answered = 0;

function esc(s){{return (s==null?"":String(s)).replace(/[&<>"]/g,function(c){{
  return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c];}});}}

function shuffle(a) {{
  for (let i = a.length - 1; i > 0; i--) {{
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }}
  return a;
}}

function applyFilters() {{
  const t = document.getElementById('typeFilter').value;
  const rmax = parseInt(document.getElementById('rankFilter').value, 10);
  pool = shuffle(ALL_ITEMS.filter(it => (!t || it.type === t) && it.rank <= rmax));
  pos = 0; right = 0; answered = 0;
  updateScore();
  renderCard();
}}

function updateScore() {{
  document.getElementById('score').textContent = right + ' / ' + answered + ' (' + pool.length + ' loaded)';
}}

function renderCard() {{
  const el = document.getElementById('card');
  if (!pool.length) {{ el.innerHTML = '<p>No items match this filter.</p>'; return; }}
  if (pos >= pool.length) {{
    el.innerHTML = '<div class="done">Done. Score: ' + right + ' / ' + answered + '<br><button class="primary" id="again">go again</button></div>';
    document.getElementById('again').onclick = applyFilters;
    return;
  }}
  const it = pool[pos];
  const opts = it.choices.map((c, i) =>
    '<button class="opt" data-i="' + i + '">' + esc(c) + '</button>').join('');
  el.innerHTML = '<div class="tags">' + esc(it.type) + ' &middot; rank ' + it.rank + '</div>' +
    '<div class="q">' + esc(it.prompt) + '</div>' + opts;
  el.querySelectorAll('.opt').forEach(btn => btn.addEventListener('click', () => onAnswer(btn, it)));
}}

function onAnswer(btn, it) {{
  const chosen = it.choices[parseInt(btn.dataset.i, 10)];
  document.querySelectorAll('.opt').forEach(b => {{
    b.disabled = true;
    const v = it.choices[parseInt(b.dataset.i, 10)];
    if (v === it.answer) b.classList.add('correct');
    else if (b === btn) b.classList.add('wrong');
  }});
  answered++;
  if (chosen === it.answer) right++;
  updateScore();
  setTimeout(() => {{ pos++; renderCard(); }}, 700);
}}

document.getElementById('typeFilter').addEventListener('change', applyFilters);
document.getElementById('rankFilter').addEventListener('change', applyFilters);
document.getElementById('restart').addEventListener('click', applyFilters);
applyFilters();
</script>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260714)
    ap.add_argument("--source", default=str(SRC_JSON))
    args = ap.parse_args()

    data = json.loads(Path(args.source).read_text(encoding="utf-8"))
    items = data["items"]
    payload = build_payload(items, args.seed)
    write_html(payload, len(payload))

    print("wrote %d items" % len(payload))
    print("  %s" % OUT_HTML)


if __name__ == "__main__":
    main()
