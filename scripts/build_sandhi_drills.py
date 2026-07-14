#!/usr/bin/env python
"""Sandhi drills/flashcards — roadmap Phase 4, surface 4b (H918).

The last core-programme Phase-4 surface (surface 4a, reader hover, is a
separate SanskritGrammar handoff, H917). Turns the graded curriculum
(data/sandhi/sandhi_curriculum.tsv, H902) into active-recall practice items —
distinct from the curriculum (a syllabus to READ) and the reference
(a table to LOOK UP): these are quiz items to ANSWER.

Scope: lessons 1..--max-lesson (default 9) of the curriculum — the 132 rules
that carry 90% of all corpus sandhi (the roadmap's own coverage milestone);
lesson 10's 2,049-row long tail is excluded by default as low pedagogical
value per card (--max-lesson to widen).

Three item types per rule, each with same-class distractors (reuses the
csl-guides sandhi-quiz.json question/answer/tags shape):
  * join     "Apply sandhi: X + Y -> ?"            answer: Z
  * split    "You meet Z. What was the junction?"   answer: X + Y
  * identify "Which class is X Y -> Z?"             answer: category

Outputs:
  * data/sandhi/sandhi_drills.json   item bank (id, type, rule, category,
                                      lesson, difficulty, question, answer,
                                      choices, context, tags)
  * data/sandhi/sandhi_drills.tsv    flat fallback (same items, one per row)
  * data/sandhi/sandhi_drills.apkg   Anki deck (genanki), Basic front/back +
                                      MCQ choices shown on the back
  * reading/sandhi/drills/index.html self-contained theme-aware MCQ web quiz

Public/MIT, credit Dr. Mārcis Gasūns. Usage:
  python scripts/build_sandhi_drills.py [--max-lesson 9] [--seed 20260714]
"""
import argparse
import csv
import html
import json
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "sandhi" / "corpus_sandhi.tsv"
CURRICULUM = ROOT / "data" / "sandhi" / "sandhi_curriculum.tsv"
OUT_JSON = ROOT / "data" / "sandhi" / "sandhi_drills.json"
OUT_TSV = ROOT / "data" / "sandhi" / "sandhi_drills.tsv"
OUT_APKG = ROOT / "data" / "sandhi" / "sandhi_drills.apkg"
OUT_HTML = ROOT / "reading" / "sandhi" / "drills" / "index.html"

CATEGORIES = ["anusvāra / nasal", "visarga", "vowel coalescence", "consonant / other"]

# stable genanki model/deck ids — never regenerate randomly, or re-imports
# in Anki create duplicate decks/note-types instead of updating in place.
ANKI_MODEL_ID = 1607392014
ANKI_DECK_ID = 1607392015


def lhs_display(lhs):
    parts = lhs.split()
    return " + ".join(parts) if len(parts) == 2 else lhs


def difficulty_for(lesson):
    if lesson <= 3:
        return "easy"
    if lesson <= 6:
        return "medium"
    return "hard"


def first_example(examples):
    if not examples:
        return ""
    return examples.split(" · ")[0].strip()


def pick_distractors(rng, pool, exclude, k=3):
    cands = [x for x in pool if x != exclude]
    rng.shuffle(cands)
    seen, out = set(), []
    for c in cands:
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
        if len(out) == k:
            break
    return out


def mcq_choices(rng, answer, distractors):
    choices = [answer] + distractors
    rng.shuffle(choices)
    return choices


def build_items(curriculum_rows, corpus_by_rule, max_lesson, seed):
    rng = random.Random(seed)
    by_cat_rhs = {c: [] for c in CATEGORIES}
    by_cat_lhs = {c: [] for c in CATEGORIES}
    rows = [r for r in curriculum_rows if int(r["lesson"]) <= max_lesson]
    for r in rows:
        rule = r["rule"]
        cat = r["category"]
        lhs, _, rhs = rule.partition(" → ")
        by_cat_rhs.setdefault(cat, []).append(rhs)
        by_cat_lhs.setdefault(cat, []).append(lhs_display(lhs))

    items = []
    idx = 0
    for r in rows:
        rule = r["rule"]
        cat = r["category"]
        lesson = int(r["lesson"])
        lhs, _, rhs = rule.partition(" → ")
        lhs_d = lhs_display(lhs)
        corpus_row = corpus_by_rule.get(rule, {})
        context = first_example(corpus_row.get("examples", ""))
        count = int(r.get("count", corpus_row.get("global_count", 0)) or 0)
        diff = difficulty_for(lesson)
        base = {
            "rule": rule, "category": cat, "lesson": lesson,
            "difficulty": diff, "corpus_count": count, "context": context,
        }

        idx += 1
        jd = pick_distractors(rng, by_cat_rhs[cat], rhs)
        items.append(dict(base, id="SD-%04d" % idx, type="join",
                           question="Apply sandhi: %s → ?" % lhs_d,
                           answer=rhs, choices=mcq_choices(rng, rhs, jd),
                           tags=["join", cat]))

        idx += 1
        sd = pick_distractors(rng, by_cat_lhs[cat], lhs_d)
        items.append(dict(base, id="SD-%04d" % idx, type="split",
                           question="You meet “%s” while reading. What was the original junction?" % rhs,
                           answer=lhs_d, choices=mcq_choices(rng, lhs_d, sd),
                           tags=["split", cat]))

        idx += 1
        id_choices = mcq_choices(rng, cat, [c for c in CATEGORIES if c != cat])
        items.append(dict(base, id="SD-%04d" % idx, type="identify",
                           question="Which sandhi class is “%s → %s”?" % (lhs_d, rhs),
                           answer=cat, choices=id_choices,
                           tags=["identify", cat]))
    return items


def write_json(items, max_lesson):
    n_rules = len({i["rule"] for i in items})
    out = {
        "title": "Sanskrit sandhi drills",
        "description": "Corpus-attested sandhi practice items (join / split / identify-class), "
                        "graded by curriculum lesson, with same-class multiple-choice distractors.",
        "source": {
            "corpus": "data/sandhi/corpus_sandhi.tsv (17 texts, ~580k junctions)",
            "curriculum": "data/sandhi/sandhi_curriculum.tsv (H902 graded syllabus)",
            "scope": "lessons 1..%d (%d rules)" % (max_lesson, n_rules),
            "builder": "scripts/build_sandhi_drills.py",
            "license": "public/MIT; source DCS is CC BY-SA 4.0 (Oliver Hellwig / DCS)",
        },
        "item_types": {
            "join": "Given the pre-sandhi junction (X + Y), choose the sandhied result (Z).",
            "split": "Given the sandhied result (Z), choose the original junction (X + Y).",
            "identify": "Given a rule (X Y → Z), choose its sandhi class.",
        },
        "items": items,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")


def write_tsv(items):
    with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["id", "type", "rule", "category", "lesson", "difficulty",
                    "question", "answer", "choices", "context"])
        for i in items:
            w.writerow([i["id"], i["type"], i["rule"], i["category"], i["lesson"],
                        i["difficulty"], i["question"], i["answer"],
                        " | ".join(i["choices"]), i["context"]])


def write_apkg(items):
    import genanki
    model = genanki.Model(
        ANKI_MODEL_ID, "Sandhi drill (H918)",
        fields=[{"name": "Question"}, {"name": "Answer"}, {"name": "Choices"},
                {"name": "Rule"}, {"name": "Category"}, {"name": "Lesson"}, {"name": "Context"}],
        templates=[{
            "name": "Card 1",
            "qfmt": "<div class=\"q\">{{Question}}</div>"
                    "<div class=\"choices\">{{Choices}}</div>",
            "afmt": "{{FrontSide}}<hr id=\"answer\">"
                    "<div class=\"a\">{{Answer}}</div>"
                    "<div class=\"meta\">{{Rule}} &middot; {{Category}} &middot; lesson {{Lesson}}</div>"
                    "<div class=\"ctx\">{{Context}}</div>",
        }],
        css=".card{font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:20px;"
            "text-align:center;color:#1c1a17;background:#fbfaf7}"
            ".q{font-size:1.1em;margin-bottom:.4em}.choices{color:#6b6660;font-size:.85em}"
            ".a{font-weight:600;color:#7a4f2b;margin:.3em 0}"
            ".meta{color:#6b6660;font-size:.75em}.ctx{color:#9c948a;font-size:.7em;margin-top:.4em}",
    )
    deck = genanki.Deck(ANKI_DECK_ID, "Sanskrit sandhi drills (kosha, H918)")
    for i in items:
        anki_tags = [t.replace(" ", "-").replace("/", "-") for t in i["tags"]]
        deck.add_note(genanki.Note(
            model=model,
            fields=[i["question"], i["answer"], " / ".join(i["choices"]),
                    i["rule"], i["category"], str(i["lesson"]), i["context"]],
            tags=anki_tags,
        ))
    OUT_APKG.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck).write_to_file(str(OUT_APKG))


def write_html(items, max_lesson):
    payload = json.dumps(items, ensure_ascii=False)
    n_rules = len({i["rule"] for i in items})
    page = _PAGE.format(n=len(items), rules=n_rules, lessons=max_lesson, items_json=payload)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(page, encoding="utf-8", newline="\n")


_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sanskrit sandhi — drills</title>
<meta name="description" content="A self-contained multiple-choice sandhi drill quiz, graded by the corpus-ranked curriculum.">
<style>
 :root{{--bg:#fbfaf7;--fg:#1c1a17;--muted:#6b6660;--line:#e6e1d8;--card:#fff;--accent:#7a4f2b;--chip:#f2ede3;--good:#3a7d44;--bad:#b5462f}}
 @media(prefers-color-scheme:dark){{:root{{--bg:#17150f;--fg:#ece7dd;--muted:#9c948a;--line:#2e2a22;--card:#1f1c15;--accent:#d9a066;--chip:#2a251c;--good:#7fbf87;--bad:#e08a70}}}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
 .wrap{{max-width:720px;margin:0 auto;padding:1.5rem 1.1rem 4rem}}
 h1{{font-size:1.5rem;margin:.2rem 0 .3rem}} .sub{{color:var(--muted);font-size:.9rem;margin:0 0 1rem}}
 .bar{{display:flex;gap:.6rem;align-items:center;margin-bottom:1rem;font-size:.85rem;color:var(--muted)}}
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
 .ctx{{color:var(--muted);font-size:.82rem;margin-top:.8rem;font-style:italic}}
 .done{{text-align:center;padding:2rem 1rem}}
 footer{{margin-top:1.6rem;color:var(--muted);font-size:.8rem}}
 a{{color:var(--accent)}}
</style></head><body><div class="wrap">
 <h1>Sanskrit sandhi — drills</h1>
 <p class="sub">{n} corpus-attested practice items over {rules} rules (curriculum lessons 1&ndash;{lessons}, the highest-value junctions). Join / split / identify-class, multiple choice. A companion to the <a href="../curriculum/">graded curriculum</a> and <a href="../reference/">reference</a>.</p>
 <div class="bar">
  <label>Type <select id="typeFilter"><option value="">all</option><option value="join">join</option><option value="split">split</option><option value="identify">identify</option></select></label>
  <label>Lesson &le; <select id="lessonFilter"><option value="{lessons}">all</option><option value="3">3</option><option value="6">6</option><option value="9">9</option></select></label>
  <button id="restart">restart</button>
  <span class="score" id="score">0 / 0</span>
 </div>
 <div class="card" id="card"></div>
 <footer>Item bank: <a href="https://github.com/gasyoun/kosha/blob/main/data/sandhi/sandhi_drills.json">sandhi_drills.json</a> &middot;
  Anki deck: <a href="https://github.com/gasyoun/kosha/blob/main/data/sandhi/sandhi_drills.apkg">sandhi_drills.apkg</a> &middot;
  built by <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_sandhi_drills.py">build_sandhi_drills.py</a>.
  Dr. Mārcis Gasūns.</footer>
</div>
<script>
const ALL_ITEMS = {items_json};
let pool = [], pos = 0, right = 0, answered = 0;

function shuffle(a) {{
  for (let i = a.length - 1; i > 0; i--) {{
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }}
  return a;
}}

function applyFilters() {{
  const t = document.getElementById('typeFilter').value;
  const lmax = parseInt(document.getElementById('lessonFilter').value, 10);
  pool = shuffle(ALL_ITEMS.filter(it => (!t || it.type === t) && it.lesson <= lmax));
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
  const opts = it.choices.map(c =>
    '<button class="opt" data-c="' + encodeURIComponent(c) + '">' + c + '</button>').join('');
  el.innerHTML = '<div class="tags">' + it.type + ' &middot; ' + it.category + ' &middot; lesson ' + it.lesson + '</div>' +
    '<div class="q">' + it.question + '</div>' + opts +
    (it.context ? '<div class="ctx">' + it.context + '</div>' : '');
  el.querySelectorAll('.opt').forEach(btn => btn.addEventListener('click', () => onAnswer(btn, it)));
}}

function onAnswer(btn, it) {{
  const chosen = decodeURIComponent(btn.dataset.c);
  document.querySelectorAll('.opt').forEach(b => {{
    b.disabled = true;
    const v = decodeURIComponent(b.dataset.c);
    if (v === it.answer) b.classList.add('correct');
    else if (b === btn) b.classList.add('wrong');
  }});
  answered++;
  if (chosen === it.answer) right++;
  updateScore();
  setTimeout(() => {{ pos++; renderCard(); }}, 700);
}}

document.getElementById('typeFilter').addEventListener('change', applyFilters);
document.getElementById('lessonFilter').addEventListener('change', applyFilters);
document.getElementById('restart').addEventListener('click', applyFilters);
applyFilters();
</script>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-lesson", type=int, default=9)
    ap.add_argument("--seed", type=int, default=20260714)
    ap.add_argument("--corpus", default=str(CORPUS))
    ap.add_argument("--curriculum", default=str(CURRICULUM))
    args = ap.parse_args()

    corpus_rows = list(csv.DictReader(open(args.corpus, encoding="utf-8"), delimiter="\t"))
    corpus_by_rule = {r["rule"]: r for r in corpus_rows}
    curriculum_rows = list(csv.DictReader(open(args.curriculum, encoding="utf-8"), delimiter="\t"))

    items = build_items(curriculum_rows, corpus_by_rule, args.max_lesson, args.seed)
    write_json(items, args.max_lesson)
    write_tsv(items)
    write_apkg(items)
    write_html(items, args.max_lesson)

    n_rules = len({i["rule"] for i in items})
    print("wrote %d items over %d rules (lessons 1..%d)" % (len(items), n_rules, args.max_lesson))
    print("  %s" % OUT_JSON)
    print("  %s" % OUT_TSV)
    print("  %s" % OUT_APKG)
    print("  %s" % OUT_HTML)


if __name__ == "__main__":
    main()
