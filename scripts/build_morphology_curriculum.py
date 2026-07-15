"""Helper module for build_morphology_drills.py -- curriculum/lesson grouping,
drill-item assembly (shared ARCHITECTURE item schema), Anki export, and the
two theme-aware static pages. Split out of the main script only so the DCS
attestation join (the genuinely novel part) is not buried under page-template
boilerplate; not meant to be run standalone.
"""
import csv
import html
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "sanskrit-util" / "py"))
from sanskrit_util import from_slp1, slp1_to_devanagari  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DATASET = "morphology-drills"

# stable genanki model/deck ids -- never regenerate randomly, or re-imports in
# Anki create duplicate decks/note-types instead of updating in place.
ANKI_MODEL_ID = 1607392030
ANKI_DECK_ID = 1607392031


def bucket_for_model(model: str, lemma: str, pronoun_lemmas: set) -> str:
    """Class bucket for the curriculum's lesson ordering (a-stems -> other-
    vowel-stems -> consonant-stems -> pronouns -> present-class-verbs ->
    other). A linguistic classification fact, not a tunable weight -- see
    drill_weights.json's _doc. Grounded in a survey of the live model
    column (`SELECT model, COUNT(DISTINCT lemma_slp1) FROM inflections
    GROUP BY model`): m_a/n_a/f_A are the thematic a/A-stem family; a bare
    single-vowel suffix (m_i, f_I, m_u, f_U, m_f...) is the other-vowel-stem
    family; everything else nominal (m_in/n_an/m_vat/m_c/the *_1_X
    consonant-final subclasses) is consonant-stem; v_* is the present-class
    verb family (kosha's inflections table is present-system-centric, see
    module docstring); pronouns are irregular models identified by LEMMA,
    not by model prefix."""
    if lemma in pronoun_lemmas:
        return "pronouns"
    if model.startswith("v_"):
        return "present-class-verbs"
    if model == "ind":
        return "other"
    if model in ("m_a", "n_a", "f_A", "f_a"):
        return "a-stems"
    suffix = model.split("_", 1)[1] if "_" in model else model
    if suffix in ("i", "I", "u", "U", "f"):
        return "other-vowel-stems"
    return "consonant-stems"


def _label(slp1_form: str) -> dict:
    return {"slp1": slp1_form, "iast": from_slp1(slp1_form),
            "deva": slp1_to_devanagari(slp1_form)}


def write_curriculum(cells, weights_path, out_tsv, out_html):
    w = json.loads(weights_path.read_text(encoding="utf-8"))
    order = w["lesson_group_order"]
    pronoun_lemmas = set(w["pronoun_lemmas"])
    step = w["lesson_coverage_step"]

    attested = [c for c in cells if c["attested"]]
    paradigms = {}
    for c in attested:
        key = (c["lemma"], c["model"])
        p = paradigms.setdefault(key, {
            "lemma": c["lemma"], "model": c["model"], "core_rank": c["core_rank"],
            "bucket": bucket_for_model(c["model"], c["lemma"], pronoun_lemmas),
            "kind": "verb" if "voice" in c else "nominal",
            "count": 0, "n_cells": 0,
        })
        p["count"] += c["corpus_count"]
        p["n_cells"] += 1

    rows = sorted(paradigms.values(),
                  key=lambda p: (order.index(p["bucket"]) if p["bucket"] in order else len(order),
                                 p["core_rank"]))
    total = sum(p["count"] for p in rows) or 1

    cum = 0
    lesson = 1
    lesson_target = step
    out_rows = []
    for i, p in enumerate(rows, 1):
        cum += p["count"]
        cum_pct = cum / total
        out_rows.append({
            "rank": i, "lemma_slp1": p["lemma"], "lemma_iast": from_slp1(p["lemma"]),
            "lemma_deva": slp1_to_devanagari(p["lemma"]),
            "model": p["model"], "kind": p["kind"], "bucket": p["bucket"],
            "core_rank": p["core_rank"], "n_attested_cells": p["n_cells"],
            "corpus_count": p["count"], "pct": round(100.0 * p["count"] / total, 4),
            "cumulative_pct": round(100.0 * cum_pct, 2), "lesson": lesson,
        })
        if cum_pct >= lesson_target and i < len(rows):
            lesson += 1
            lesson_target += step

    out_tsv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_tsv, "w", encoding="utf-8", newline="") as f:
        wtr = csv.writer(f, delimiter="\t", lineterminator="\n")
        wtr.writerow(["rank", "lemma_slp1", "lemma_iast", "model", "kind", "bucket",
                      "core_rank", "n_attested_cells", "corpus_count", "pct",
                      "cumulative_pct", "lesson"])
        for o in out_rows:
            wtr.writerow([o[k] for k in ("rank", "lemma_slp1", "lemma_iast", "model", "kind",
                                          "bucket", "core_rank", "n_attested_cells",
                                          "corpus_count", "pct", "cumulative_pct", "lesson")])

    for target in (50, 80, 90):
        n = next((o["rank"] for o in out_rows if o["cumulative_pct"] >= target), len(out_rows))
        print("learn %4d paradigms -> cover %d%% of attested nominal/verbal tokens" % (n, target))
    print(f"wrote {out_tsv} ({len(out_rows)} paradigms, {out_rows[-1]['lesson'] if out_rows else 0} lessons)")

    _write_curriculum_html(out_rows, total, out_html)
    return out_rows


def _write_curriculum_html(rows, total, out_html):
    lessons = {}
    for o in rows:
        lessons.setdefault(o["lesson"], []).append(o)
    blocks = []
    for lk in sorted(lessons):
        items = lessons[lk]
        cov = items[-1]["cumulative_pct"]
        bucket = items[0]["bucket"]
        rowhtml = "\n".join(
            "<tr><td class='r lemma' data-deva='{deva}' data-iast='{iast}' data-slp1='{slp1}'>{lem}</td>"
            "<td>{m}</td><td>{k}</td><td class='n'>{c}</td></tr>".format(
                deva=html.escape(o["lemma_deva"]), iast=html.escape(o["lemma_iast"]),
                slp1=html.escape(o["lemma_slp1"]), lem=html.escape(o["lemma_deva"]),
                m=html.escape(o["model"]), k=o["kind"], c=o["n_attested_cells"])
            for o in items)
        blocks.append(
            "<section><h2>Lesson {k} <span class='chip'>{b}</span> "
            "<span class='cov'>&rarr; {cov}% cumulative</span></h2>"
            "<div class='scroll'><table><thead><tr><th>lemma</th><th>model</th>"
            "<th>type</th><th>attested cells</th></tr></thead><tbody>{rows}</tbody>"
            "</table></div></section>".format(k=lk, b=html.escape(bucket), cov=cov, rows=rowhtml))
    miles = " &middot; ".join(
        "<b>%d paradigms</b> &rarr; %d%%" % (
            next((o["rank"] for o in rows if o["cumulative_pct"] >= t), len(rows)), t)
        for t in (50, 80, 90))
    page = _CURR_PAGE.format(n=len(rows), t=total, miles=miles, blocks="\n".join(blocks))
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(page, encoding="utf-8", newline="\n")


_STYLE = """
 :root{{--bg:#fbfaf7;--fg:#1c1a17;--muted:#6b6660;--line:#e6e1d8;--card:#fff;--accent:#7a4f2b;--chip:#f2ede3;--good:#3a7d44;--bad:#b5462f}}
 @media(prefers-color-scheme:dark){{:root{{--bg:#17150f;--fg:#ece7dd;--muted:#9c948a;--line:#2e2a22;--card:#1f1c15;--accent:#d9a066;--chip:#2a251c;--good:#7fbf87;--bad:#e08a70}}}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
 .wrap{{max-width:860px;margin:0 auto;padding:1.5rem 1.1rem 4rem}}
 h1{{font-size:1.5rem;margin:.2rem 0 .3rem}} .sub{{color:var(--muted);font-size:.9rem;margin:0 0 1rem}}
 .mile{{background:var(--card);border:1px solid var(--line);border-radius:.5rem;padding:.7rem .9rem;font-size:.95rem;margin-bottom:1.4rem}}
 .mile b{{color:var(--accent)}}
 section{{margin-bottom:1.6rem}} h2{{font-size:1.05rem;border-bottom:2px solid var(--line);padding-bottom:.2rem}}
 h2 .cov{{color:var(--muted);font-weight:400;font-size:.85rem;float:right}}
 h2 .chip{{background:var(--chip);border-radius:.4rem;padding:.05rem .5rem;font-size:.75rem;font-weight:400;color:var(--muted)}}
 .scroll{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:.9rem}}
 th,td{{text-align:left;padding:.35rem .55rem;border-bottom:1px solid var(--line);vertical-align:top}}
 th{{color:var(--muted);font-weight:600}} td.r{{font-size:1.05rem;white-space:nowrap}}
 td.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
 a{{color:var(--accent)}} footer{{margin-top:1.6rem;color:var(--muted);font-size:.8rem}}
 .bar{{display:flex;gap:.6rem;align-items:center;margin-bottom:1rem;font-size:.85rem;color:var(--muted)}}
 select{{font:inherit;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:.4rem;padding:.35rem .6rem;cursor:pointer}}
"""

_CURR_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sanskrit morphology — graded curriculum</title>
<meta name="description" content="A corpus-attested graded syllabus of Sanskrit noun/verb paradigms: learn the highest-value declensions and conjugations first.">
<style>""" + _STYLE + """</style></head><body><div class="wrap">
 <h1>Sanskrit morphology — a graded curriculum</h1>
 <p class="sub">{n} attested paradigms over {t} corpus-attested inflected-form occurrences, ordered by declension/conjugation class then by lemma frequency. Only forms the corpus actually attests are drilled -- see the <a href="../drills/">drills</a> for practice, and the <a href="https://github.com/gasyoun/SanskritGrammar/blob/main/DIGITAL_SANSKRIT_PEDAGOGY_FIELD_2026.md">field's RQ1</a> for why.</p>
 <div class="bar"><label>Script <select id="scriptToggle">
  <option value="deva" selected>Devanāgarī</option>
  <option value="iast">IAST</option>
  <option value="slp1">SLP1</option>
 </select></label></div>
 <div class="mile">{miles}</div>
 {blocks}
 <footer>Ordered by <a href="https://github.com/gasyoun/kosha/blob/main/data/morphology/drill_weights.json">drill_weights.json</a>. Built by
  <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_morphology_drills.py">build_morphology_drills.py</a>
  over the P4 paradigm engine + VisualDCS <code>dcs_full.sqlite</code> attestation join.
  Dr. Mārcis Gasūns.</footer>
</div>
<script>
document.getElementById('scriptToggle').addEventListener('change', (e) => {{
  const scr = e.target.value;
  document.querySelectorAll('td.lemma').forEach(td => {{ td.textContent = td.dataset[scr]; }});
}});
</script>
</body></html>
"""


def write_drills(cells, out_json, seed, max_cells=0):
    rng = random.Random(seed)
    attested = [c for c in cells if c["attested"]]
    # within-lemma frequency order, per IMPLEMENTATION SS2 ("within a lemma,
    # order cells by attested-form frequency"); core_rank groups by lemma.
    attested.sort(key=lambda c: (c["core_rank"], -c["corpus_count"]))

    total_attested = len(attested)
    if max_cells and total_attested > max_cells:
        # same discipline as build_sandhi_drills.py's --max-lesson: the
        # active-recall deck is a curated subset of the full attested-cell
        # set (already in morphology_curriculum.tsv in full), not a dump of
        # every corpus-attested cell -- embedding all of them inline would
        # make the self-contained HTML page tens of megabytes. Never a
        # silent cap: reported below and --max-drill-cells 0 disables it.
        attested = attested[:max_cells]
        print(f"[drills] scoped to top {max_cells}/{total_attested} attested cells "
              f"by (core_rank, corpus frequency) -- pass --max-drill-cells 0 for the full set")

    by_lemma = {}
    for c in attested:
        by_lemma.setdefault(c["lemma"], []).append(c)

    items = []
    idx = 0
    for c in attested:
        siblings = [s for s in by_lemma[c["lemma"]] if s is not c]
        form_pool = [_label(s["form"])["deva"] for s in siblings]
        label_pool = [s["cell_label"] for s in siblings]
        rng.shuffle(form_pool)
        rng.shuffle(label_pool)
        form_d = [x for x in dict.fromkeys(form_pool) if x != _label(c["form"])["deva"]][:3]
        label_d = [x for x in dict.fromkeys(label_pool) if x != c["cell_label"]][:3]

        lem = _label(c["lemma"])
        form = _label(c["form"])
        idx += 1
        fill_choices = [form["deva"]] + form_d
        rng.shuffle(fill_choices)
        items.append({
            "id": "MD-%05d-F" % idx, "aspect": "morphology", "type": "fill",
            "prompt": "%s (%s) — %s → ?" % (lem["deva"], lem["iast"], c["cell_label"]),
            "answer": form["deva"], "choices": fill_choices, "distractors": form_d,
            "rank": c["core_rank"], "evidence": c["evidence"], "source_dataset": SOURCE_DATASET,
            "lemma_iast": lem["iast"], "form_iast": form["iast"], "cell_label": c["cell_label"],
            "corpus_count": c["corpus_count"],
        })
        idx += 1
        match_choices = [c["cell_label"]] + label_d
        rng.shuffle(match_choices)
        items.append({
            "id": "MD-%05d-M" % idx, "aspect": "morphology", "type": "match",
            "prompt": "%s (%s) — which paradigm cell?" % (form["deva"], form["iast"]),
            "answer": c["cell_label"], "choices": match_choices, "distractors": label_d,
            "rank": c["core_rank"], "evidence": c["evidence"], "source_dataset": SOURCE_DATASET,
            "lemma_iast": lem["iast"], "form_iast": form["iast"], "cell_label": c["cell_label"],
            "corpus_count": c["corpus_count"],
        })

    out = {
        "title": "Sanskrit morphology drills",
        "description": "Corpus-attested paradigm-cell practice items (fill the form / identify "
                        "the cell), graded by lemma frequency, evidence-linked to a DCS corpus locus.",
        "source": {
            "paradigm_engine": "app/paradigm.py (P4 Wave K2b, H183)",
            "attestation": "VisualDCS dcs_full.sqlite token table (lemma+form+morphology join)",
            "builder": "scripts/build_morphology_drills.py",
            "license": "public/MIT; source DCS is CC BY-SA 4.0 (Oliver Hellwig / DCS)",
        },
        "item_types": {
            "fill": "Given the lemma and a paradigm cell, produce the attested inflected form.",
            "match": "Given an attested inflected form, identify its paradigm cell.",
        },
        "items": items,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"wrote {out_json} ({len(items)} items over {len(attested)} attested cells)")
    return items


def write_apkg(items, out_apkg):
    import genanki
    model = genanki.Model(
        ANKI_MODEL_ID, "Morphology drill (H946)",
        fields=[{"name": "Question"}, {"name": "Answer"}, {"name": "Type"},
                {"name": "Lemma"}, {"name": "Cell"}, {"name": "Evidence"}],
        templates=[{
            "name": "Card 1",
            "qfmt": "<div class=\"q\">{{Question}}</div>",
            "afmt": "{{FrontSide}}<hr id=\"answer\">"
                    "<div class=\"a\">{{Answer}}</div>"
                    "<div class=\"meta\">{{Lemma}} &middot; {{Cell}}</div>"
                    "<div class=\"ctx\">{{Evidence}}</div>",
        }],
        css=".card{font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:20px;"
            "text-align:center;color:#1c1a17;background:#fbfaf7}"
            ".q{font-size:1.1em;margin-bottom:.4em}"
            ".a{font-weight:600;color:#7a4f2b;margin:.3em 0}"
            ".meta{color:#6b6660;font-size:.75em}.ctx{color:#9c948a;font-size:.7em;margin-top:.4em}",
    )
    deck = genanki.Deck(ANKI_DECK_ID, "Sanskrit morphology drills (kosha, H946)")
    fill_items = [i for i in items if i["type"] == "fill"]
    for i in fill_items:
        deck.add_note(genanki.Note(
            model=model,
            fields=[i["prompt"], i["answer"], i["type"], i["lemma_iast"], i["cell_label"],
                    i["evidence"] or ""],
            tags=[i["type"], "morphology"],
        ))
    out_apkg.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck).write_to_file(str(out_apkg))
    print(f"wrote {out_apkg} ({len(fill_items)} notes)")


def write_drills_html(items, out_html):
    payload = json.dumps(items, ensure_ascii=False)
    page = _DRILLS_PAGE.format(n=len(items), items_json=payload)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(page, encoding="utf-8", newline="\n")
    print(f"wrote {out_html}")


_DRILLS_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sanskrit morphology — drills</title>
<meta name="description" content="A self-contained multiple-choice Sanskrit morphology drill quiz, graded by lemma frequency, every item corpus-evidence-linked.">
<style>""" + _STYLE + """
 .bar{{display:flex;gap:.6rem;align-items:center;margin-bottom:1rem;font-size:.85rem;color:var(--muted)}}
 select,button{{font:inherit;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:.4rem;padding:.35rem .6rem;cursor:pointer}}
 button.primary{{background:var(--accent);color:var(--bg);border-color:var(--accent)}}
 .score{{margin-left:auto}}
 .card{{background:var(--card);border:1px solid var(--line);border-radius:.6rem;padding:1.1rem 1.2rem;min-height:14rem}}
 .tags{{color:var(--muted);font-size:.78rem;margin-bottom:.6rem}}
 .q{{font-size:1.25rem;margin-bottom:1rem}}
 .opt{{display:block;width:100%;text-align:left;margin-bottom:.5rem;padding:.55rem .8rem;border-radius:.4rem;border:1px solid var(--line);background:var(--chip);color:var(--fg);font:inherit;cursor:pointer}}
 .opt:hover{{border-color:var(--accent)}}
 .opt.correct{{border-color:var(--good);background:color-mix(in srgb, var(--good) 18%, var(--chip))}}
 .opt.wrong{{border-color:var(--bad);background:color-mix(in srgb, var(--bad) 18%, var(--chip))}}
 .ctx{{color:var(--muted);font-size:.78rem;margin-top:.8rem;font-style:italic}}
 .done{{text-align:center;padding:2rem 1rem}}
</style></head><body><div class="wrap">
 <h1>Sanskrit morphology — drills</h1>
 <p class="sub">{n} corpus-attested practice items (fill the form / identify the cell), every one evidence-linked to a DCS corpus locus. A companion to the <a href="../curriculum/">graded curriculum</a>.</p>
 <div class="bar">
  <label>Type <select id="typeFilter"><option value="">all</option><option value="fill">fill</option><option value="match">match</option></select></label>
  <button id="restart">restart</button>
  <span class="score" id="score">0 / 0</span>
 </div>
 <div class="card" id="card"></div>
 <footer>Item bank: <a href="https://github.com/gasyoun/kosha/blob/main/data/morphology/drills.json">drills.json</a> &middot;
  Anki deck: <a href="https://github.com/gasyoun/kosha/blob/main/data/morphology/morphology_drills.apkg">morphology_drills.apkg</a> &middot;
  built by <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_morphology_drills.py">build_morphology_drills.py</a>.
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
  pool = shuffle(ALL_ITEMS.filter(it => !t || it.type === t));
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
  el.innerHTML = '<div class="tags">' + it.type + ' &middot; rank ' + it.rank + '</div>' +
    '<div class="q">' + it.prompt + '</div>' + opts +
    (it.evidence ? '<div class="ctx">' + it.evidence + ' (' + it.corpus_count + '&times; attested)</div>' : '');
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
document.getElementById('restart').addEventListener('click', applyFilters);
applyFilters();
</script>
</body></html>
"""
