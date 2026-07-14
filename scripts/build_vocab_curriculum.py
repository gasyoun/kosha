#!/usr/bin/env python
"""Frequency-graded vocabulary curriculum — Wave 1 W1b (H947).

"Learn the N most frequent lemmas -> read X % of the corpus" applied to
words, the exact method of build_sandhi_curriculum.py. Consumes the
Leonchenko core-vocabulary layer already carried by
data/frequency/lemma_frequency.tsv (core_rank + coverage_pct) — does not
re-derive frequency.

`coverage_pct` in the source feed is a per-lemma MARGINAL weight, not a
running cumulative (data/frequency/README.md's explicit caveat: "do not
read it as cumulative % of corpus covered so far"). This script computes
the actual cumulative sum itself, in core_rank order — which is what
"learn N -> read X%" requires, and is what makes the coverage column
monotone by construction.

Only lemmas with a real, committed docs/cards/<token>.json card are kept
(the acceptance bar is "every curriculum lemma links to a real kosha /w/
card, no dead links") — the drop count is reported, never silently
absorbed (453/7120 core lemmas are DCS-internal causative/preverb forms
with no dictionary headword, the known granularity mismatch documented in
data/frequency/README.md).

Gloss = the first dictionary entry's rendered_html for the lemma's own
committed card (MW preferred via DICT_ORDER), tag-stripped + truncated —
the same shape as app/word_page.py::_plain / ui/src/lib/export.js::glossOf.
DCS's own `lemma.meanings` field was tried and rejected as the primary
source: only ~23% of card-having core lemmas have an exact-match DCS
lemma row (DCS's internal citation form frequently diverges from the
kosha/dictionary SLP1 key), too sparse to lead; the MW-card path covers
100% of kept rows by construction (a row with no card is dropped, not
included with an empty gloss).

Outputs:
  * data/frequency/vocab_curriculum.tsv   rank · lemma_slp1 · deva · iast ·
                                           gloss · core_rank · coverage_pct ·
                                           cumulative_pct · lesson · card_href
  * data/frequency/vocab_drills.json      recognition + recall item bank
                                           (ARCHITECTURE §shared item schema)
  * data/frequency/vocab_curriculum.apkg  Anki deck (genanki), one note per
                                           lemma, front=deva/iast back=gloss
  * reading/vocabulary/curriculum/index.html   graded syllabus page

Public/MIT, credit Dr. Mārcis Gasūns. Usage:
  python scripts/build_vocab_curriculum.py [--lesson-size 50] [--seed 20260714]
"""
import argparse
import csv
import html
import json
import random
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
FREQ = ROOT / "data" / "frequency" / "lemma_frequency.tsv"
CARDS_DIR = ROOT / "docs" / "cards"
OUT_TSV = ROOT / "data" / "frequency" / "vocab_curriculum.tsv"
OUT_DRILLS = ROOT / "data" / "frequency" / "vocab_drills.json"
OUT_APKG = ROOT / "data" / "frequency" / "vocab_curriculum.apkg"
OUT_HTML = ROOT / "reading" / "vocabulary" / "curriculum" / "index.html"

sys.path.insert(0, str(ROOT.parent / "sanskrit-util" / "py"))
from sanskrit_util import from_slp1, slp1_to_devanagari  # noqa: E402

DICT_ORDER = ("mw", "pwg", "ap90")
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")

# stable genanki model/deck ids — never regenerate randomly, or re-imports
# in Anki create duplicate decks/note-types instead of updating in place.
ANKI_MODEL_ID = 1607392020
ANKI_DECK_ID = 1607392021


def card_token(slp1):
    """Filesystem/URL-safe SLP1 encoding — exact twin of
    app/word_page.py::card_token / build_static_cache.py / ui/src/lib/cardToken.js."""
    out = []
    for b in slp1.encode("utf-8"):
        if (97 <= b <= 122) or (48 <= b <= 57):
            out.append(chr(b))
        else:
            out.append("_%02x" % b)
    return "".join(out)


def gloss_of(card, limit=100):
    """First DICT_ORDER entry's rendered_html, tag-stripped — the same shape
    as app/word_page.py::_plain / ui/src/lib/export.js::glossOf."""
    by_dict = {}
    for r in card.get("results", []):
        by_dict.setdefault(r["dict"], []).append(r)
    entry = None
    for d in DICT_ORDER:
        if d in by_dict:
            entry = by_dict[d][0]
            break
    if entry is None:
        return ""
    text = html.unescape(entry.get("rendered_html", ""))
    text = WS_RE.sub(" ", TAG_RE.sub(" ", text)).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def load_core_rows(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))
    core = [r for r in rows if r["core_rank"]]
    core.sort(key=lambda r: int(r["core_rank"]))
    return core


def build_curriculum(core_rows, cards_dir, lesson_size):
    kept = []
    dropped_no_card = 0
    for r in core_rows:
        slp1 = r["lemma_slp1"]
        tok = card_token(slp1)
        cpath = cards_dir / (tok + ".json")
        if not cpath.exists():
            dropped_no_card += 1
            continue
        card = json.loads(cpath.read_text(encoding="utf-8"))
        kept.append({
            "lemma_slp1": slp1,
            "deva": slp1_to_devanagari(slp1),
            "iast": from_slp1(slp1),
            "gloss": gloss_of(card),
            "core_rank": int(r["core_rank"]),
            "coverage_pct": float(r["coverage_pct"]) if r["coverage_pct"] else 0.0,
            "card_token": tok,
        })

    cum = 0.0
    out_rows = []
    for i, k in enumerate(kept, 1):
        cum += k["coverage_pct"]
        lesson = (i - 1) // lesson_size + 1
        out_rows.append(dict(k, rank=i, cumulative_pct=round(cum, 4), lesson=lesson))
    return out_rows, dropped_no_card


def write_tsv(rows):
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["rank", "lemma_slp1", "deva", "iast", "gloss", "core_rank",
                    "coverage_pct", "cumulative_pct", "lesson", "card_href"])
        for r in rows:
            # reading/vocabulary/curriculum/ -> repo/site root -> w/<token>.html
            # (docs/w/ is gitignored/regenerable, mirrors build_reading_pack.py's
            # "../w/%s.html" convention scaled for this page's extra directory depth)
            href = "../../w/%s.html" % r["card_token"]
            w.writerow([r["rank"], r["lemma_slp1"], r["deva"], r["iast"], r["gloss"],
                        r["core_rank"], r["coverage_pct"], r["cumulative_pct"],
                        r["lesson"], href])


def build_drills(rows, seed):
    rng = random.Random(seed)
    by_lesson = {}
    for r in rows:
        by_lesson.setdefault(r["lesson"], []).append(r)

    items = []
    idx = 0
    for r in rows:
        band = by_lesson[r["lesson"]]
        pool = [x for x in band if x["lemma_slp1"] != r["lemma_slp1"]]
        rng.shuffle(pool)
        distractor_glosses = [x["gloss"] for x in pool if x["gloss"]][:3]
        distractor_forms = ["%s / %s" % (x["deva"], x["iast"]) for x in pool][:3]

        idx += 1
        items.append({
            "aspect": "vocabulary", "type": "recognition", "id": "VC-%05d" % idx,
            "prompt": "%s / %s — meaning?" % (r["deva"], r["iast"]),
            "answer": r["gloss"], "distractors": distractor_glosses,
            "rank": r["core_rank"], "evidence": "docs/cards/%s.json" % r["card_token"],
            "source_dataset": "vocab-curriculum",
        })
        idx += 1
        items.append({
            "aspect": "vocabulary", "type": "recall", "id": "VC-%05d" % idx,
            "prompt": "“%s” — which word?" % r["gloss"],
            "answer": "%s / %s" % (r["deva"], r["iast"]), "distractors": distractor_forms,
            "rank": r["core_rank"], "evidence": "docs/cards/%s.json" % r["card_token"],
            "source_dataset": "vocab-curriculum",
        })
    OUT_DRILLS.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "title": "Sanskrit vocabulary — frequency-graded drills",
        "description": "Recognition (word -> meaning) and recall (meaning -> word) items, "
                        "graded by corpus core-vocabulary rank; distractors drawn from the "
                        "same lesson band (same-frequency-band lemmas).",
        "source": {
            "curriculum": "data/frequency/vocab_curriculum.tsv (H947 graded syllabus)",
            "builder": "scripts/build_vocab_curriculum.py",
            "license": "public/MIT; source DCS is CC BY-SA 4.0 (Oliver Hellwig / DCS); "
                       "MW/PWG/AP90 entries per Cologne Sanskrit Dictionaries terms.",
        },
        "items": items,
    }
    OUT_DRILLS.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return items


def write_apkg(rows):
    import genanki
    model = genanki.Model(
        ANKI_MODEL_ID, "Vocabulary drill (H947)",
        fields=[{"name": "Front"}, {"name": "Gloss"}, {"name": "Lesson"}, {"name": "Rank"}],
        templates=[{
            "name": "Card 1",
            "qfmt": "<div class=\"q\">{{Front}}</div>",
            "afmt": "{{FrontSide}}<hr id=\"answer\"><div class=\"a\">{{Gloss}}</div>"
                    "<div class=\"meta\">lesson {{Lesson}} &middot; core rank {{Rank}}</div>",
        }],
        css=".card{font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:20px;"
            "text-align:center;color:#1c1a17;background:#fbfaf7}"
            ".q{font-size:1.2em}.a{font-weight:600;color:#7a4f2b;margin:.3em 0}"
            ".meta{color:#6b6660;font-size:.75em}",
    )
    deck = genanki.Deck(ANKI_DECK_ID, "Sanskrit vocabulary — frequency curriculum (kosha, H947)")
    for r in rows:
        front = "%s &middot; %s" % (r["deva"], r["iast"])
        deck.add_note(genanki.Note(
            model=model,
            fields=[front, r["gloss"] or "(no gloss extracted)", str(r["lesson"]), str(r["core_rank"])],
            tags=["lesson-%d" % r["lesson"]],
        ))
    OUT_APKG.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck).write_to_file(str(OUT_APKG))


def _write_html(rows, dropped, lesson_size):
    lessons = {}
    for r in rows:
        lessons.setdefault(r["lesson"], []).append(r)
    blocks = []
    for lk in sorted(lessons):
        items = lessons[lk]
        cov = items[-1]["cumulative_pct"]
        rowhtml = "\n".join(
            "<tr><td class='dv'>{d}</td><td class='ia'>{i}</td>"
            "<td class='gl'>{g}</td><td class='n'>{r}</td></tr>".format(
                d=html.escape(o["deva"]), i=html.escape(o["iast"]),
                g=html.escape(o["gloss"] or "—"), r=o["core_rank"])
            for o in items)
        blocks.append(
            "<section><h2>Lesson {k} <span class='cov'>→ {cov}% cumulative</span></h2>"
            "<div class='scroll'><table><thead><tr><th>देव</th><th>IAST</th>"
            "<th>gloss</th><th>core rank</th></tr></thead><tbody>{rows}</tbody>"
            "</table></div></section>".format(k=lk, cov=cov, rows=rowhtml))

    milestones = []
    for target in (30, 50, 70):
        hit = next((o for o in rows if o["cumulative_pct"] >= target), None)
        if hit:
            milestones.append("<b>%d lemmas</b> → %d%%" % (hit["rank"], target))
    miles = " · ".join(milestones) if milestones else "coverage below 30% across the core list"

    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sanskrit vocabulary — graded curriculum</title>
<meta name="description" content="A corpus-ranked graded vocabulary syllabus: learn the highest-coverage lemmas first.">
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
 th{{color:var(--muted);font-weight:600}} td.dv{{font-size:1.1rem;white-space:nowrap}}
 td.ia{{white-space:nowrap;color:var(--muted)}} td.gl{{color:var(--fg)}}
 td.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;color:var(--muted)}}
 a{{color:var(--accent)}} footer{{margin-top:1.6rem;color:var(--muted);font-size:.8rem}}
</style></head><body><div class="wrap">
 <h1>Sanskrit vocabulary — a graded curriculum</h1>
 <p class="sub">{n} corpus-attested core-vocabulary lemmas (Leonchenko ranking), {lessons} lessons of ~{step} words each, ordered highest-coverage first. {dropped} core lemmas dropped for having no committed dictionary card (no dead links).</p>
 <div class="mile">{miles}</div>
 {blocks}
 <footer>Ranked by <a href="https://github.com/gasyoun/kosha/blob/main/data/frequency/lemma_frequency.tsv">lemma_frequency.tsv</a>'s
  Leonchenko <code>core_rank</code>/<code>coverage_pct</code> columns (cumulative coverage computed here, not copied — see
  <a href="https://github.com/gasyoun/kosha/blob/main/data/frequency/README.md">README.md</a>'s marginal-weight caveat). Built by
  <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_vocab_curriculum.py">build_vocab_curriculum.py</a>.
  Every lemma links to its <a href="https://github.com/gasyoun/kosha/blob/main/docs/cards">kosha dictionary card</a>.
  Dr. Mārcis Gasūns.</footer>
</div></body></html>
"""
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(
        page.format(n=len(rows), lessons=(rows[-1]["lesson"] if rows else 0),
                    step=lesson_size, dropped=dropped, miles=miles, blocks="\n".join(blocks)),
        encoding="utf-8", newline="\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson-size", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20260714)
    ap.add_argument("--freq", default=str(FREQ))
    ap.add_argument("--cards-dir", default=str(CARDS_DIR))
    args = ap.parse_args()

    core_rows = load_core_rows(Path(args.freq))
    rows, dropped = build_curriculum(core_rows, Path(args.cards_dir), args.lesson_size)
    write_tsv(rows)
    items = build_drills(rows, args.seed)
    write_apkg(rows)
    _write_html(rows, dropped, args.lesson_size)

    print("dropped %d/%d core lemmas with no committed kosha card (no dead /w/ links)"
          % (dropped, dropped + len(rows)))
    total_cum = rows[-1]["cumulative_pct"] if rows else 0.0
    for target in (30, 50, 70):
        hit = next((r for r in rows if r["cumulative_pct"] >= target), None)
        if hit:
            print("learn %4d lemmas -> read %d%% of the core-vocabulary corpus mass"
                  % (hit["rank"], target))
        else:
            print("cumulative coverage never reaches %d%% (max %.2f%% at rank %d) -- "
                  "the Leonchenko core list caps out here, not a bug"
                  % (target, total_cum, len(rows)))
    print("wrote %s (%d lemmas, %d lessons), %d drill items, %s, %s"
          % (OUT_TSV, len(rows), rows[-1]["lesson"] if rows else 0, len(items), OUT_APKG, OUT_HTML))


if __name__ == "__main__":
    main()
