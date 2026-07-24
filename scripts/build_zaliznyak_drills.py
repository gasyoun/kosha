#!/usr/bin/env python
"""Zaliznyak declension-class drills (H1461, L4 surface, delta vs H1296).

H1296 (SanskritGrammar/sangram) drills corpus-ATTESTED CELLS of kosha lemmas —
"is this cell attested?". This is a different asset, different repo,
complementary question: it drills the PWG **Zaliznyak paradigm-CLASS index**
(headword -> declension-class token, e.g. `f·1`, `m·8i`) -- "which declension
class does this word belong to, and which other words share its paradigm?".
Distractors are same-class headwords, not attested-vs-generated cells. No
corpus-attestation join is involved. kosha's own build_morphology_drills.py
(H946) is also attested-cell-based (DCS join, drills a specific inflected
FORM); this drills CLASS MEMBERSHIP of a headword. Complementary, not a dup.

Source (E31, SanskritLexicography/RussianTranslation, read at build time,
never vendored into kosha -- see MARKED DEFAULT below):
  headword_index.tsv           k1 hom lex accented index_token stem_class
                                compound_members irregularities  (98,639 rows)
  reverse_paradigm_index.json  {index_token: [headword#hom, ...]}  (335 tokens)

`index_token` grammar: `<gender>·<section>[+N]`, gender in {m,f,n,mfn,mn,mf,fn,
ind}. `ind·*` = indeclinable (no declension) -- excluded entirely. The `+N`
compound-arity suffix does NOT change the declension pattern (e.g. `m·1` and
`m·1+2` are both `stem_class=a-stem`) -- so distractor bucketing keys on
`stem_class`, not the raw section string (the class-token-grammar risk the
handoff flagged; verified empirically, see docs/data-statements meta).

Two item types, capped by --max-items (default 4000), tokens sampled in
member-count-descending order so high-yield paradigms dominate:
  classify      "To which declension class does X (m.) belong?"  answer=token
  odd-one-out   "Which word does not share the paradigm class of these?"
                answer = a same-gender different-class headword

Outputs (data/zaliznyak/):
  zaliznyak_drills.json           item bank (schema shared with sandhi/
                                   morphology drills: id/type/question/answer/
                                   choices/tags)
  zaliznyak_drills.tsv             flat fallback
  zaliznyak_drills.apkg             Anki deck (genanki)
  zaliznyak_paradigm_classes.tsv   slim committed class index: index_token,
                                   gender, stem_class, member_count,
                                   representative_k1, repr_devanagari
  reading/zaliznyak/drills/index.html   self-contained theme-aware MCQ quiz

Public/MIT, credit Dr. Mārcis Gasūns. Usage:
  python scripts/build_zaliznyak_drills.py [--max-items 4000] [--seed 20260722]
"""
import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "sanskrit-util" / "py"))
from sanskrit_util import from_slp1, slp1_to_devanagari  # noqa: E402

SRC_DIR = ROOT.parent / "SanskritLexicography" / "RussianTranslation" / "src"
HW_TSV = SRC_DIR / "headword_index.tsv"
REV_JSON = SRC_DIR / "reverse_paradigm_index.json"

OUT_DIR = ROOT / "data" / "zaliznyak"
OUT_JSON = OUT_DIR / "zaliznyak_drills.json"
OUT_TSV = OUT_DIR / "zaliznyak_drills.tsv"
OUT_APKG = OUT_DIR / "zaliznyak_drills.apkg"
OUT_CLASSES_TSV = OUT_DIR / "zaliznyak_paradigm_classes.tsv"
OUT_HTML = ROOT / "reading" / "zaliznyak" / "drills" / "index.html"

# stable genanki model/deck ids -- never reuse sandhi's (1607392014/15) or
# morphology's, or re-imports in Anki collide instead of updating in place.
ANKI_MODEL_ID = 1607392018
ANKI_DECK_ID = 1607392019

GENDER_LABEL = {
    "m": "masculine", "f": "feminine", "n": "neuter",
    "mfn": "adjective (m./f./n.)", "mn": "masc./neut.",
    "mf": "masc./fem.", "fn": "fem./neut.",
}
PER_TOKEN_CAP = 15  # classify items sampled per token (diversity, not raw yield)
PER_TOKEN_ODD_CAP = 8  # odd-one-out groups per token


def load_headwords():
    """k1#hom (or bare k1) -> (k1, hom, lex, index_token, stem_class), skipping
    indeclinables (gender 'ind' -- no declension class to drill)."""
    rows = {}
    with open(HW_TSV, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            token = r["index_token"]
            gender = token.split("·", 1)[0]
            if gender == "ind":
                continue
            key = "%s#%s" % (r["k1"], r["hom"]) if r["hom"] else r["k1"]
            rows[key] = (r["k1"], r["hom"], r["lex"], token, r["stem_class"], gender)
    return rows


def load_reverse_index():
    return json.loads(REV_JSON.read_text(encoding="utf-8"))


def build_class_table(headwords, reverse_index):
    """index_token -> {gender, stem_class, members: [key,...], representative}."""
    classes = {}
    for token, members in reverse_index.items():
        gender = token.split("·", 1)[0]
        if gender == "ind":
            continue
        live_members = [m for m in members if m in headwords]
        if not live_members:
            continue
        stem_class = headwords[live_members[0]][4]
        classes[token] = {
            "gender": gender, "stem_class": stem_class,
            "members": live_members, "member_count": len(live_members),
        }
    return classes


def display_headword(key, headwords):
    k1, hom, lex, token, stem_class, gender = headwords[key]
    return {
        "k1": k1, "lex": lex,
        "devanagari": slp1_to_devanagari(k1),
        "iast": from_slp1(k1),
    }


def gender_class_pool(classes):
    """gender -> [(token, stem_class), ...] for distractor bucketing."""
    pool = defaultdict(list)
    for token, c in classes.items():
        pool[c["gender"]].append((token, c["stem_class"]))
    return pool


def pick_distractor_tokens(rng, pool, gender, exclude_stem_class, k=3):
    """3 tokens of a DIFFERENT stem_class than exclude_stem_class -- same
    gender preferred, cross-gender fallback if the gender bucket is too thin
    (mf/fn/mn genders carry only a handful of tokens each)."""
    same = [t for t, sc in pool.get(gender, []) if sc != exclude_stem_class]
    cands = list(dict.fromkeys(same))
    rng.shuffle(cands)
    if len(cands) >= k:
        return cands[:k]
    # cross-gender fallback
    other = [t for g, lst in pool.items() if g != gender for t, sc in lst if sc != exclude_stem_class]
    other = list(dict.fromkeys(other))
    rng.shuffle(other)
    for t in other:
        if t not in cands:
            cands.append(t)
        if len(cands) == k:
            break
    return cands[:k]


def pick_odd_member(rng, classes, gender, exclude_token, exclude_stem_class, headwords):
    """A single headword key from a different-class token (same gender
    preferred), for the odd-one-out distractor."""
    cands_tokens = [t for t, c in classes.items()
                     if t != exclude_token and c["gender"] == gender
                     and c["stem_class"] != exclude_stem_class]
    if not cands_tokens:
        cands_tokens = [t for t, c in classes.items()
                         if t != exclude_token and c["stem_class"] != exclude_stem_class]
    if not cands_tokens:
        return None
    rng.shuffle(cands_tokens)
    t = cands_tokens[0]
    members = classes[t]["members"]
    return rng.choice(members)


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


def build_items(headwords, classes, max_items, seed):
    rng = random.Random(seed)
    pool = gender_class_pool(classes)
    ordered_tokens = sorted(classes, key=lambda t: -classes[t]["member_count"])

    items, idx = [], 0
    half = max_items // 2

    # -- classify: "to which declension class does X belong?" --
    n_classify_skipped_thin = 0
    for token in ordered_tokens:
        if len(items) >= half:
            break
        c = classes[token]
        distractor_tokens = pick_distractor_tokens(rng, pool, c["gender"], c["stem_class"])
        if len(distractor_tokens) < 3:
            n_classify_skipped_thin += 1
            continue
        members = list(c["members"])
        rng.shuffle(members)
        for key in members[:PER_TOKEN_CAP]:
            if len(items) >= half:
                break
            hw = display_headword(key, headwords)
            idx += 1
            items.append({
                "id": "ZD-%04d" % idx, "type": "classify",
                "question": "To which declension class does %s (%s, %s) belong?" % (
                    hw["devanagari"], hw["iast"], hw["lex"]),
                "answer": token,
                "choices": mcq_choices(rng, token, distractor_tokens),
                "index_token": token, "gender": c["gender"], "stem_class": c["stem_class"],
                "member_count": c["member_count"],
                "tags": ["classify", c["gender"], c["stem_class"]],
            })

    # -- odd-one-out: "which word does not share the paradigm class of these?" --
    n_odd_skipped_thin = 0
    for token in ordered_tokens:
        if len(items) >= max_items:
            break
        c = classes[token]
        if c["member_count"] < 4:
            n_odd_skipped_thin += 1
            continue
        members = list(c["members"])
        rng.shuffle(members)
        n_groups = min(PER_TOKEN_ODD_CAP, len(members) // 3)
        for g in range(n_groups):
            if len(items) >= max_items:
                break
            same_keys = members[g * 3:(g + 1) * 3]
            if len(same_keys) < 3:
                break
            same_hw = [display_headword(k, headwords) for k in same_keys]
            same_faces = ["%s (%s)" % (h["devanagari"], h["iast"]) for h in same_hw]
            if len(set(same_faces)) < 3:
                continue  # two same-class members render identically (homonyms) -- skip group
            odd_face = None
            for _try in range(5):
                odd_key = pick_odd_member(rng, classes, c["gender"], token, c["stem_class"], headwords)
                if odd_key is None:
                    break
                odd_hw = display_headword(odd_key, headwords)
                cand_face = "%s (%s)" % (odd_hw["devanagari"], odd_hw["iast"])
                if cand_face not in same_faces:
                    odd_face = cand_face
                    break
            if odd_face is None:
                continue
            idx += 1
            items.append({
                "id": "ZD-%04d" % idx, "type": "odd-one-out",
                "question": "Which word does NOT share the paradigm class of the others: %s?" % (
                    ", ".join(same_faces + [odd_face])),
                "answer": odd_face,
                "choices": mcq_choices(rng, odd_face, same_faces),
                "index_token": token, "gender": c["gender"], "stem_class": c["stem_class"],
                "member_count": c["member_count"],
                "tags": ["odd-one-out", c["gender"], c["stem_class"]],
            })

    print("[items] %d classify-eligible tokens skipped (< 3 cross-class distractors)" % n_classify_skipped_thin)
    print("[items] %d odd-one-out tokens skipped (< 4 members)" % n_odd_skipped_thin)
    return items


def write_classes_tsv(classes, headwords):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_CLASSES_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["index_token", "gender", "stem_class", "member_count",
                    "representative_k1", "repr_devanagari"])
        for token in sorted(classes, key=lambda t: -classes[t]["member_count"]):
            c = classes[token]
            repr_key = c["members"][0]
            repr_hw = display_headword(repr_key, headwords)
            w.writerow([token, c["gender"], c["stem_class"], c["member_count"],
                        repr_hw["k1"], repr_hw["devanagari"]])


def write_json(items, n_tokens):
    out = {
        "title": "Sanskrit declension-class drills (Zaliznyak paradigm index)",
        "description": "Classify a PWG headword's declension class, or spot the word "
                        "that doesn't share a group's paradigm class -- over the "
                        "Zaliznyak-style paradigm-class index (E31).",
        "source": {
            "index": "SanskritLexicography/RussianTranslation/src/headword_index.tsv + "
                      "reverse_paradigm_index.json (E31, PWG-derived)",
            "builder": "scripts/build_zaliznyak_drills.py",
            "license": "public/MIT; data CC BY-SA 4.0 (Cologne PWG, DCS/Dr. Mārcis Gasūns)",
            "distinct_classes": n_tokens,
        },
        "item_types": {
            "classify": "Given a headword, choose its declension-class token.",
            "odd-one-out": "Given 4 words, choose the one that inflects differently.",
        },
        "items": items,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")


def write_tsv(items):
    with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["id", "type", "index_token", "gender", "stem_class",
                    "question", "answer", "choices"])
        for i in items:
            w.writerow([i["id"], i["type"], i["index_token"], i["gender"], i["stem_class"],
                        i["question"], i["answer"], " | ".join(i["choices"])])


def write_apkg(items):
    import genanki
    model = genanki.Model(
        ANKI_MODEL_ID, "Zaliznyak declension drill (H1461)",
        fields=[{"name": "Question"}, {"name": "Answer"}, {"name": "Choices"},
                {"name": "Token"}, {"name": "StemClass"}, {"name": "Type"}],
        templates=[{
            "name": "Card 1",
            "qfmt": "<div class=\"q\">{{Question}}</div>"
                    "<div class=\"choices\">{{Choices}}</div>",
            "afmt": "{{FrontSide}}<hr id=\"answer\">"
                    "<div class=\"a\">{{Answer}}</div>"
                    "<div class=\"meta\">{{Token}} &middot; {{StemClass}} &middot; {{Type}}</div>",
        }],
        css=".card{font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:20px;"
            "text-align:center;color:#1c1a17;background:#fbfaf7}"
            ".q{font-size:1.1em;margin-bottom:.4em}.choices{color:#6b6660;font-size:.85em}"
            ".a{font-weight:600;color:#7a4f2b;margin:.3em 0}"
            ".meta{color:#6b6660;font-size:.75em}",
    )
    deck = genanki.Deck(ANKI_DECK_ID, "Sanskrit declension-class drills (kosha, H1461)")
    for i in items:
        deck.add_note(genanki.Note(
            model=model,
            fields=[i["question"], i["answer"], " / ".join(i["choices"]),
                    i["index_token"], i["stem_class"], i["type"]],
            tags=[t.replace(" ", "-").replace("/", "-") for t in i["tags"]],
        ))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck).write_to_file(str(OUT_APKG))


def write_html(items, n_tokens):
    payload = json.dumps(items, ensure_ascii=False)
    genders = sorted({i["gender"] for i in items})
    gender_opts = "".join(
        '<option value="%s">%s</option>' % (g, GENDER_LABEL.get(g, g)) for g in genders)
    page = _PAGE.format(n=len(items), tokens=n_tokens, items_json=payload, gender_opts=gender_opts)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(page, encoding="utf-8", newline="\n")


_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sanskrit declension classes — drills</title>
<meta name="description" content="A self-contained multiple-choice drill over the PWG Zaliznyak paradigm-class index: classify a word's declension class, or spot the odd one out.">
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
 <h1>Sanskrit declension classes — drills</h1>
 <p class="sub">{n} items over {tokens} PWG Zaliznyak paradigm-class tokens (E31). Classify a headword's declension class, or spot the word that inflects differently. Multiple choice.</p>
 <div class="bar">
  <label>Type <select id="typeFilter"><option value="">all</option><option value="classify">classify</option><option value="odd-one-out">odd-one-out</option></select></label>
  <label>Gender <select id="genderFilter"><option value="">all</option>{gender_opts}</select></label>
  <button id="restart">restart</button>
  <span class="score" id="score">0 / 0</span>
 </div>
 <div class="card" id="card"></div>
 <footer>Item bank: <a href="https://github.com/gasyoun/kosha/blob/main/data/zaliznyak/zaliznyak_drills.json">zaliznyak_drills.json</a> &middot;
  Anki deck: <a href="https://github.com/gasyoun/kosha/blob/main/data/zaliznyak/zaliznyak_drills.apkg">zaliznyak_drills.apkg</a> &middot;
  source: <a href="https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/reverse_index.py">reverse_index.py</a> (E31) &middot;
  built by <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_zaliznyak_drills.py">build_zaliznyak_drills.py</a>.
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
  const g = document.getElementById('genderFilter').value;
  pool = shuffle(ALL_ITEMS.filter(it => (!t || it.type === t) && (!g || it.gender === g)));
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
  el.innerHTML = '<div class="tags">' + it.type + ' &middot; ' + it.gender + ' &middot; ' + it.stem_class + '</div>' +
    '<div class="q">' + it.question + '</div>' + opts;
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
document.getElementById('genderFilter').addEventListener('change', applyFilters);
document.getElementById('restart').addEventListener('click', applyFilters);
applyFilters();
</script>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-items", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=20260722)
    args = ap.parse_args()

    if not HW_TSV.exists() or not REV_JSON.exists():
        sys.exit("sibling source missing: %s / %s (SanskritLexicography clone required)" % (HW_TSV, REV_JSON))

    headwords = load_headwords()
    reverse_index = load_reverse_index()
    classes = build_class_table(headwords, reverse_index)
    print("[classes] %d declension-class tokens (excl. indeclinable), %d headwords" % (
        len(classes), len(headwords)))

    items = build_items(headwords, classes, args.max_items, args.seed)
    write_classes_tsv(classes, headwords)
    write_json(items, len(classes))
    write_tsv(items)
    write_apkg(items)
    write_html(items, len(classes))

    n_classify = sum(1 for i in items if i["type"] == "classify")
    n_odd = sum(1 for i in items if i["type"] == "odd-one-out")
    print("wrote %d items (%d classify, %d odd-one-out) over %d classes" % (
        len(items), n_classify, n_odd, len(classes)))
    print("  %s" % OUT_CLASSES_TSV)
    print("  %s" % OUT_JSON)
    print("  %s" % OUT_TSV)
    print("  %s" % OUT_APKG)
    print("  %s" % OUT_HTML)


if __name__ == "__main__":
    main()
