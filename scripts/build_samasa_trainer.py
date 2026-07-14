#!/usr/bin/env python
"""Samāsa (compound) analysis trainer — pedagogy Wave 1, surface W1c (H948).

Six-stage contract (docs/ARCHITECTURE_KOSHA_PEDAGOGY_SURFACES.md) applied to
compound analysis: teach tatpuruṣa / bahuvrīhi / dvandva / karmadhāraya
recognition + member-splitting from the compound data that already exists.

Two sources, two roles (per docs/IMPLEMENTATION_KOSHA_PEDAGOGY_WAVE1.md §W1c):
  * GOLD  data/gita/gita_morphology_gold.tsv `compound` column (815 hand-tagged
          Gita words) — the only source with a VERIFIED type. Backs `identify`
          items (type known) and `split` items where the `lemma` is
          hyphen-segmented (806/815; 9 lexicalized bahuvrīhis like "govinda"
          carry no segmentation and are identify-only).
  * CORPUS  VisualDCS derived-data/Kompozity cmps.csv (401,478 compound
          headword -> member-split pairs) joined against names.csv's
          frequency vector (168,481 of those carry a measured corpus
          frequency) — the corpus-scale SPLIT-only pool (no verified type,
          so never used for `identify`). Ranked by frequency; the interactive
          drill deck/page/Anki export caps at `corpus_drill_cap`
          (drill_weights.json) — the full ranked pool is reported in the
          build summary, not silently truncated (mirrors the sandhi builder's
          lesson-10 long-tail convention).

Honest residue: an item without a verified answer is dropped, never
fabricated. Gold rows whose `compound` column is a dual tag ("DV/TP" etc,
56/815) are ambiguous-type and excluded from `identify`; still eligible for
`split` if hyphen-segmented.

Outputs:
  * data/samasa/samasa_curriculum.tsv   ordered syllabus (KD/TP first, then
                                         BV/DV, per the MG 14-07-2026 ruling),
                                         gold items only (verified type)
  * data/samasa/reference.tsv           per-type ranked example lookup
  * data/samasa/samasa_drills.json      item bank (identify + split)
  * data/samasa/samasa_drills.tsv       flat fallback
  * data/samasa/samasa_drills.apkg      Anki deck (genanki)
  * reading/samasa/{curriculum,drills,reference}/index.html

Public/MIT, credit Dr. Mārcis Gasūns. Usage:
  python scripts/build_samasa_trainer.py [--corpus-cap 2000] [--seed 20260714]
"""
import argparse
import csv
import html
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent if (ROOT.parent / "VisualDCS").exists() else ROOT.parent.parent
CMPS = GH / "VisualDCS" / "derived-data" / "Kompozity" / "cmps.csv"
NAMES = GH / "VisualDCS" / "derived-data" / "Kompozity" / "names.csv"
GOLD = ROOT / "data" / "gita" / "gita_morphology_gold.tsv"
WEIGHTS = ROOT / "data" / "samasa" / "drill_weights.json"

OUT_CURRICULUM_TSV = ROOT / "data" / "samasa" / "samasa_curriculum.tsv"
OUT_REFERENCE_TSV = ROOT / "data" / "samasa" / "reference.tsv"
OUT_DRILLS_JSON = ROOT / "data" / "samasa" / "samasa_drills.json"
OUT_DRILLS_TSV = ROOT / "data" / "samasa" / "samasa_drills.tsv"
OUT_APKG = ROOT / "data" / "samasa" / "samasa_drills.apkg"
OUT_HTML_CURRICULUM = ROOT / "reading" / "samasa" / "curriculum" / "index.html"
OUT_HTML_DRILLS = ROOT / "reading" / "samasa" / "drills" / "index.html"
OUT_HTML_REFERENCE = ROOT / "reading" / "samasa" / "reference" / "index.html"

SAMASA_QUIZ_URL = "https://sanskrit-lexicon.github.io/csl-guides/docs/users/samasa-quiz"

TYPE_MAP = {"tatpurusa": "TP", "bahuvrihi": "BV", "dvandva": "DV", "karmadharaya": "KD"}
TYPE_NAME = {"TP": "tatpuruṣa", "BV": "bahuvrīhi", "DV": "dvandva", "KD": "karmadhāraya"}

# stable genanki model/deck ids — never regenerate randomly, or re-imports
# in Anki create duplicate decks/note-types instead of updating in place.
ANKI_MODEL_ID = 1607392020
ANKI_DECK_ID = 1607392021


def load_names_freq(path):
    freq = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split(";")
            if len(parts) < 4:
                continue
            surface = parts[0].strip()
            try:
                freq[surface] = int(parts[3])
            except ValueError:
                continue
    return freq


def load_cmps(path):
    """surface -> member list, first occurrence wins (401,478 rows, 399,162
    unique surfaces; ~2,316 duplicate-surface rows dropped, negligible)."""
    seen = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split(";", 1)
            if len(parts) < 2:
                continue
            surface = parts[0].strip()
            members = parts[1].strip().split()
            if surface and surface not in seen and len(members) >= 2:
                seen[surface] = members
    return seen


def classify(compound_field):
    """-> (type_code or None, is_ambiguous). A dual tag ("DV/TP") is a real
    disagreement in the source annotation, not a single verified answer —
    honest-residue: report it, never collapse it to one guess."""
    if compound_field in TYPE_MAP:
        return TYPE_MAP[compound_field], False
    if "/" in compound_field:
        return None, True
    return None, False


def load_gold(path, names_freq):
    rows = list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))
    items = []
    ambiguous_n = 0
    for r in rows:
        cf = r["compound"]
        if not cf:
            continue
        type_code, ambiguous = classify(cf)
        if ambiguous:
            ambiguous_n += 1
        lemma = r["lemma"]
        members = lemma.split("-") if "-" in lemma else None
        surface_bare = lemma.replace("-", "")
        form_bare = r["form"].replace("-", "")
        freq = names_freq.get(surface_bare) or names_freq.get(form_bare) or 0
        items.append({
            "type": type_code, "raw_type": cf, "ambiguous": ambiguous,
            "lemma": lemma, "members": members, "verse": r["verse"],
            "form": r["form"], "corpus_freq": freq,
        })
    return items, ambiguous_n


def build_identify_items(gold_items):
    """Verified-type-only — the field's evidence-graded principle: no
    verified type, no identify item (56 ambiguous dual-tag rows excluded)."""
    return [g for g in gold_items if g["type"] is not None]


def build_gold_split_items(gold_items):
    """Any verified/ambiguous gold row WITH a hyphen-segmented lemma (806/815
    — 9 lexicalized bahuvrīhis like "govinda" carry no segmentation)."""
    return [g for g in gold_items if g["members"]]


def rank_corpus_items(cmps_by_surface, names_freq, gold_surfaces, min_freq):
    pool = []
    for surface, members in cmps_by_surface.items():
        if surface in gold_surfaces:
            continue
        freq = names_freq.get(surface, 0)
        if freq < min_freq:
            continue
        pool.append((surface, members, freq))
    pool.sort(key=lambda t: -t[2])
    return pool


def build_curriculum(gold_identify, type_order):
    """KD/TP first (the transparent types), then BV/DV — MG's 14-07-2026
    ordering ruling. Within a type-lesson, rank by corpus frequency
    (names.csv join on the gold surface; ties -> Gita verse order) so the
    highest-value verified compounds are taught first."""
    by_type = {t: [] for t in type_order}
    for g in gold_identify:
        by_type[g["type"]].append(g)
    for t in type_order:
        by_type[t].sort(key=lambda g: (-g["corpus_freq"], g["verse"]))

    rows, rank = [], 0
    freq_sum_total = sum(g["corpus_freq"] for g in gold_identify) or 1
    freq_cum = 0
    for lesson, t in enumerate(type_order, 1):
        for g in by_type[t]:
            rank += 1
            freq_cum += g["corpus_freq"]
            rows.append({
                "rank": rank, "lesson": lesson, "type": t, "type_name": TYPE_NAME[t],
                "compound": g["lemma"], "form": g["form"], "verse": g["verse"],
                "corpus_freq": g["corpus_freq"],
                "cumulative_freq_pct": round(100.0 * freq_cum / freq_sum_total, 2),
            })
    return rows, by_type


def build_reference(by_type, type_order):
    rows = []
    for t in type_order:
        for rank_in_type, g in enumerate(by_type[t], 1):
            rows.append({
                "type": t, "type_name": TYPE_NAME[t], "rank_in_type": rank_in_type,
                "compound": g["lemma"], "verse": g["verse"], "corpus_freq": g["corpus_freq"],
            })
    return rows


def build_drill_items(gold_identify, gold_split, corpus_pool, corpus_cap, seed):
    rng = random.Random(seed)
    items = []
    idx = 0

    identify_answers = [g["type"] for g in gold_identify]
    for g in gold_identify:
        idx += 1
        distractors = [t for t in set(identify_answers) if t != g["type"]]
        # always offer all 3 other classes if present in the gold set, so a
        # learner sees the real 4-way contrast, not whatever happened to be sampled
        for t in TYPE_NAME:
            if t != g["type"] and t not in distractors:
                distractors.append(t)
        distractors = distractors[:3]
        choices = [g["type"]] + distractors
        rng.shuffle(choices)
        items.append({
            "id": "SM-%04d" % idx, "type": "identify", "provenance": "gold",
            "aspect": "samasa", "prompt": "Which compound class is “%s” (%s)?"
                                            % (g["lemma"], g["form"]),
            "answer": g["type"], "choices": choices,
            "rank": None, "evidence": "Bhagavadgītā %s (“%s”), gold-tagged" % (g["verse"], g["form"]),
            "source_dataset": "gita-morphology-gold",
        })

    for g in gold_split:
        idx += 1
        items.append({
            "id": "SM-%04d" % idx, "type": "split", "provenance": "gold",
            "aspect": "samasa", "prompt": "Split into members: “%s”" % g["lemma"],
            "answer": " + ".join(g["members"]), "choices": None,
            "rank": None, "evidence": "Bhagavadgītā %s (“%s”), gold-tagged" % (g["verse"], g["form"]),
            "source_dataset": "gita-morphology-gold",
        })

    corpus_used = corpus_pool[:corpus_cap]
    for surface, members, freq in corpus_used:
        idx += 1
        items.append({
            "id": "SM-%04d" % idx, "type": "split", "provenance": "corpus",
            "aspect": "samasa", "prompt": "Split into members: “%s”" % surface,
            "answer": " + ".join(members), "choices": None,
            "rank": None,
            "evidence": "DCS compound dictionary (Kompozity cmps.csv/names.csv), corpus frequency %d" % freq,
            "source_dataset": "dcs-compound-dictionary",
        })
    return items, len(corpus_used)


def write_curriculum_tsv(rows):
    OUT_CURRICULUM_TSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CURRICULUM_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["rank", "lesson", "type", "type_name", "compound", "form",
                    "verse", "corpus_freq", "cumulative_freq_pct"])
        for r in rows:
            w.writerow([r["rank"], r["lesson"], r["type"], r["type_name"],
                        r["compound"], r["form"], r["verse"], r["corpus_freq"],
                        r["cumulative_freq_pct"]])


def write_reference_tsv(rows):
    OUT_REFERENCE_TSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_REFERENCE_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["type", "type_name", "rank_in_type", "compound", "verse", "corpus_freq"])
        for r in rows:
            w.writerow([r["type"], r["type_name"], r["rank_in_type"],
                        r["compound"], r["verse"], r["corpus_freq"]])


def write_drills_json(items, corpus_universe, corpus_used_n, corpus_cap):
    out = {
        "title": "Sanskrit samāsa (compound) drills",
        "description": "Compound-analysis practice items (identify class / split into members), "
                        "gold-verified where possible, corpus-scale split practice beyond that.",
        "source": {
            "gold": "data/gita/gita_morphology_gold.tsv (815 hand-tagged Gita compounds, H873)",
            "corpus": "VisualDCS derived-data/Kompozity cmps.csv x names.csv (%d distinct attested "
                      "compounds carry a measured corpus frequency, out of %d total headword-split "
                      "pairs); this deck includes the top %d by frequency (--corpus-cap, "
                      "default %d) — the full ranked pool is reported in the build log, not shipped "
                      "inline, to keep the page a reasonable size." % (
                          corpus_universe, corpus_universe if corpus_universe else 0,
                          corpus_used_n, corpus_cap),
            "builder": "scripts/build_samasa_trainer.py",
            "license": "public/MIT; source DCS is CC BY-SA 4.0 (Oliver Hellwig / DCS)",
        },
        "item_types": {
            "identify": "Given a compound (gold-verified only), choose its class (KD/TP/BV/DV).",
            "split": "Given a compound, give its member breakdown (gold: verified; corpus: DCS-supplied, unverified type).",
        },
        "items": items,
    }
    OUT_DRILLS_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_DRILLS_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")


def write_drills_tsv(items):
    with open(OUT_DRILLS_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["id", "type", "provenance", "prompt", "answer", "choices", "evidence", "source_dataset"])
        for i in items:
            w.writerow([i["id"], i["type"], i["provenance"], i["prompt"], i["answer"],
                        " | ".join(i["choices"]) if i["choices"] else "", i["evidence"], i["source_dataset"]])


def write_apkg(items):
    import genanki
    model = genanki.Model(
        ANKI_MODEL_ID, "Samasa drill (H948)",
        fields=[{"name": "Prompt"}, {"name": "Answer"}, {"name": "Choices"},
                {"name": "Type"}, {"name": "Provenance"}, {"name": "Evidence"}],
        templates=[{
            "name": "Card 1",
            "qfmt": "<div class=\"q\">{{Prompt}}</div><div class=\"choices\">{{Choices}}</div>",
            "afmt": "{{FrontSide}}<hr id=\"answer\"><div class=\"a\">{{Answer}}</div>"
                    "<div class=\"meta\">{{Type}} &middot; {{Provenance}}</div>"
                    "<div class=\"ctx\">{{Evidence}}</div>",
        }],
        css=".card{font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:20px;"
            "text-align:center;color:#1c1a17;background:#fbfaf7}"
            ".q{font-size:1.1em;margin-bottom:.4em}.choices{color:#6b6660;font-size:.85em}"
            ".a{font-weight:600;color:#7a4f2b;margin:.3em 0}"
            ".meta{color:#6b6660;font-size:.75em}.ctx{color:#9c948a;font-size:.7em;margin-top:.4em}",
    )
    deck = genanki.Deck(ANKI_DECK_ID, "Sanskrit samasa (compound) drills (kosha, H948)")
    for i in items:
        deck.add_note(genanki.Note(
            model=model,
            fields=[i["prompt"], i["answer"], " / ".join(i["choices"]) if i["choices"] else "",
                    i["type"], i["provenance"], i["evidence"]],
            tags=[i["type"], i["provenance"]],
        ))
    OUT_APKG.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck).write_to_file(str(OUT_APKG))


_CURRICULUM_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sanskrit samāsa — graded curriculum</title>
<meta name="description" content="A graded syllabus for compound (samāsa) analysis: karmadhāraya/tatpuruṣa first, then bahuvrīhi/dvandva, gold-verified from the Bhagavadgītā.">
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
 td.n{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
 a{{color:var(--accent)}} footer{{margin-top:1.6rem;color:var(--muted);font-size:.8rem}}
</style></head><body><div class="wrap">
 <h1>Sanskrit samāsa — a graded curriculum</h1>
 <p class="sub">{n} gold-verified compounds from the Bhagavadgītā, ordered karmadhāraya/tatpuruṣa (the transparent types) first, then bahuvrīhi/dvandva — within each type, highest corpus-frequency first. Practice the split/identify skill on the corpus-scale pool at the <a href="../drills/">drills page</a>; try the hosted quiz at <a href="{quiz_url}">csl-guides</a>.</p>
 <div class="mile">{miles}</div>
 {blocks}
 <footer>Built by <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_samasa_trainer.py">build_samasa_trainer.py</a>
  over <a href="https://github.com/gasyoun/kosha/blob/main/data/gita/gita_morphology_gold.tsv">gita_morphology_gold.tsv</a> and the
  <a href="https://github.com/gasyoun/VisualDCS/blob/main/derived-data/Kompozity/README.md">Kompozity</a> compound dictionary.
  See also the <a href="{quiz_url}">csl-guides samāsa quiz</a>. Dr. Mārcis Gasūns.</footer>
</div></body></html>
"""


def write_curriculum_html(rows, ambiguous_n, dropped_split_n):
    lessons = {}
    for r in rows:
        lessons.setdefault(r["lesson"], []).append(r)
    blocks = []
    for lk in sorted(lessons):
        items = lessons[lk]
        t = items[0]["type"]
        cov = items[-1]["cumulative_freq_pct"]
        rowhtml = "\n".join(
            "<tr><td class='r'>{c}</td><td class='ex'>{v}</td><td class='n'>{f}</td></tr>".format(
                c=html.escape(o["compound"]), v=html.escape(o["verse"]), f=o["corpus_freq"])
            for o in items)
        blocks.append(
            "<section><h2>Lesson {k} — {tn} ({t}) <span class='cov'>{n} items, "
            "→ {cov}% cumulative freq-mass</span></h2>"
            "<div class='scroll'><table><thead><tr><th>compound</th><th>Gitā locus</th>"
            "<th>corpus freq</th></tr></thead><tbody>{rows}</tbody></table></div></section>".format(
                k=lk, tn=TYPE_NAME[t], t=t, n=len(items), cov=cov, rows=rowhtml))
    type_counts = Counter(r["type"] for r in rows)
    miles = " · ".join("<b>%s</b> %d" % (TYPE_NAME[t], type_counts.get(t, 0)) for t in TYPE_NAME)
    miles += (" · <b>%d</b> ambiguous dual-tag rows excluded from identify · "
              "<b>%d</b> unsegmented lemmas excluded from split" % (ambiguous_n, dropped_split_n))
    OUT_HTML_CURRICULUM.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML_CURRICULUM.write_text(
        _CURRICULUM_PAGE.format(n=len(rows), miles=miles, blocks="\n".join(blocks),
                                 quiz_url=SAMASA_QUIZ_URL),
        encoding="utf-8", newline="\n")


_REFERENCE_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sanskrit samāsa — reference by class</title>
<meta name="description" content="A look-up reference of gold-verified Sanskrit compounds grouped by class, ranked by corpus frequency.">
<style>
 :root{{--bg:#fbfaf7;--fg:#1c1a17;--muted:#6b6660;--line:#e6e1d8;--card:#fff;--accent:#7a4f2b}}
 @media(prefers-color-scheme:dark){{:root{{--bg:#17150f;--fg:#ece7dd;--muted:#9c948a;--line:#2e2a22;--card:#1f1c15;--accent:#d9a066}}}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
 .wrap{{max-width:860px;margin:0 auto;padding:1.5rem 1.1rem 4rem}}
 h1{{font-size:1.5rem;margin:.2rem 0 .3rem}} .sub{{color:var(--muted);font-size:.9rem;margin:0 0 1rem}}
 section{{margin-bottom:1.6rem}} h2{{font-size:1.05rem;border-bottom:2px solid var(--line);padding-bottom:.2rem}}
 .scroll{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:.9rem}}
 th,td{{text-align:left;padding:.35rem .55rem;border-bottom:1px solid var(--line)}}
 th{{color:var(--muted);font-weight:600}} td.n{{text-align:right;font-variant-numeric:tabular-nums}}
 a{{color:var(--accent)}} footer{{margin-top:1.6rem;color:var(--muted);font-size:.8rem}}
</style></head><body><div class="wrap">
 <h1>Sanskrit samāsa — reference by class</h1>
 <p class="sub">Every gold-verified compound from the Bhagavadgītā, grouped by class, ranked by corpus frequency. See the <a href="../curriculum/">graded curriculum</a> and <a href="../drills/">drills</a>.</p>
 {sections}
 <footer>Built by <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_samasa_trainer.py">build_samasa_trainer.py</a>. Dr. Mārcis Gasūns.</footer>
</div></body></html>
"""


def write_reference_html(rows, type_order):
    by_type = {}
    for r in rows:
        by_type.setdefault(r["type"], []).append(r)
    sections = []
    for t in type_order:
        items = by_type.get(t, [])
        if not items:
            continue
        rowhtml = "\n".join(
            "<tr><td class='n'>{r}</td><td>{c}</td><td>{v}</td><td class='n'>{f}</td></tr>".format(
                r=o["rank_in_type"], c=html.escape(o["compound"]),
                v=html.escape(o["verse"]), f=o["corpus_freq"])
            for o in items)
        sections.append(
            "<section><h2>{tn} ({t}) <span style='color:var(--muted);font-weight:400;font-size:.85rem'>"
            "{n} attested</span></h2><div class='scroll'><table><thead><tr><th>#</th><th>compound</th>"
            "<th>Gitā locus</th><th>corpus freq</th></tr></thead><tbody>{rows}</tbody>"
            "</table></div></section>".format(tn=TYPE_NAME[t], t=t, n=len(items), rows=rowhtml))
    OUT_HTML_REFERENCE.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML_REFERENCE.write_text(_REFERENCE_PAGE.format(sections="\n".join(sections)),
                                   encoding="utf-8", newline="\n")


_DRILLS_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sanskrit samāsa — drills</title>
<meta name="description" content="Self-contained compound identify/split practice, gold-verified plus corpus-scale split items.">
<style>
 :root{{--bg:#fbfaf7;--fg:#1c1a17;--muted:#6b6660;--line:#e6e1d8;--card:#fff;--accent:#7a4f2b;--chip:#f2ede3;--good:#3a7d44;--bad:#b5462f}}
 @media(prefers-color-scheme:dark){{:root{{--bg:#17150f;--fg:#ece7dd;--muted:#9c948a;--line:#2e2a22;--card:#1f1c15;--accent:#d9a066;--chip:#2a251c;--good:#7fbf87;--bad:#e08a70}}}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
 .wrap{{max-width:720px;margin:0 auto;padding:1.5rem 1.1rem 4rem}}
 h1{{font-size:1.5rem;margin:.2rem 0 .3rem}} .sub{{color:var(--muted);font-size:.9rem;margin:0 0 1rem}}
 .bar{{display:flex;gap:.6rem;align-items:center;margin-bottom:1rem;font-size:.85rem;color:var(--muted);flex-wrap:wrap}}
 select,button,input{{font:inherit;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:.4rem;padding:.35rem .6rem;cursor:pointer}}
 button.primary{{background:var(--accent);color:var(--bg);border-color:var(--accent)}}
 .score{{margin-left:auto}}
 .card{{background:var(--card);border:1px solid var(--line);border-radius:.6rem;padding:1.1rem 1.2rem;min-height:14rem}}
 .tags{{color:var(--muted);font-size:.78rem;margin-bottom:.6rem}}
 .q{{font-size:1.15rem;margin-bottom:1rem}}
 .opt{{display:block;width:100%;text-align:left;margin-bottom:.5rem;padding:.55rem .8rem;border-radius:.4rem;border:1px solid var(--line);background:var(--chip);color:var(--fg);font:inherit;cursor:pointer}}
 .opt:hover{{border-color:var(--accent)}}
 .opt.correct{{border-color:var(--good);background:color-mix(in srgb, var(--good) 18%, var(--chip))}}
 .opt.wrong{{border-color:var(--bad);background:color-mix(in srgb, var(--bad) 18%, var(--chip))}}
 .reveal{{margin-top:.6rem;font-weight:600;color:var(--accent)}}
 .ctx{{color:var(--muted);font-size:.82rem;margin-top:.8rem;font-style:italic}}
 .done{{text-align:center;padding:2rem 1rem}}
 footer{{margin-top:1.6rem;color:var(--muted);font-size:.8rem}}
 a{{color:var(--accent)}}
</style></head><body><div class="wrap">
 <h1>Sanskrit samāsa — drills</h1>
 <p class="sub">{n} practice items: gold-verified identify (choose the class) + split (give the member breakdown), plus corpus-scale split practice from the DCS compound dictionary. A companion to the <a href="../curriculum/">graded curriculum</a> and <a href="../reference/">reference</a>; try the hosted <a href="{quiz_url}">csl-guides quiz</a> too.</p>
 <div class="bar">
  <label>Type <select id="typeFilter"><option value="">all</option><option value="identify">identify</option><option value="split">split</option></select></label>
  <label>Source <select id="provFilter"><option value="">all</option><option value="gold">gold</option><option value="corpus">corpus</option></select></label>
  <button id="restart">restart</button>
  <span class="score" id="score">0 / 0</span>
 </div>
 <div class="card" id="card"></div>
 <footer>Item bank: <a href="https://github.com/gasyoun/kosha/blob/main/data/samasa/samasa_drills.json">samasa_drills.json</a> &middot;
  Anki deck: <a href="https://github.com/gasyoun/kosha/blob/main/data/samasa/samasa_drills.apkg">samasa_drills.apkg</a> &middot;
  built by <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_samasa_trainer.py">build_samasa_trainer.py</a>.
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
  const p = document.getElementById('provFilter').value;
  pool = shuffle(ALL_ITEMS.filter(it => (!t || it.type === t) && (!p || it.provenance === p)));
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
  const tagline = it.type + ' \\u00b7 ' + it.provenance;
  let body;
  if (it.type === 'identify') {{
    const opts = it.choices.map(c =>
      '<button class="opt" data-c="' + encodeURIComponent(c) + '">' + c + '</button>').join('');
    body = '<div class="q">' + it.prompt + '</div>' + opts;
  }} else {{
    body = '<div class="q">' + it.prompt + '</div>' +
      '<input type="text" id="splitInput" placeholder="member + member" style="width:100%">' +
      '<button class="primary" id="reveal" style="margin-top:.6rem">reveal</button>' +
      '<div class="reveal" id="revealAns" style="display:none"></div>';
  }}
  el.innerHTML = '<div class="tags">' + tagline + '</div>' + body +
    (it.evidence ? '<div class="ctx">' + it.evidence + '</div>' : '');
  if (it.type === 'identify') {{
    el.querySelectorAll('.opt').forEach(btn => btn.addEventListener('click', () => onAnswerMcq(btn, it)));
  }} else {{
    document.getElementById('reveal').addEventListener('click', () => onReveal(it));
  }}
}}

function onAnswerMcq(btn, it) {{
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

function onReveal(it) {{
  const el = document.getElementById('revealAns');
  el.style.display = 'block';
  el.textContent = it.answer;
  answered++;
  updateScore();
  setTimeout(() => {{ pos++; renderCard(); }}, 900);
}}

document.getElementById('typeFilter').addEventListener('change', applyFilters);
document.getElementById('provFilter').addEventListener('change', applyFilters);
document.getElementById('restart').addEventListener('click', applyFilters);
applyFilters();
</script>
</body></html>
"""


def write_drills_html(items):
    payload = json.dumps(items, ensure_ascii=False)
    page = _DRILLS_PAGE.format(n=len(items), items_json=payload, quiz_url=SAMASA_QUIZ_URL)
    OUT_HTML_DRILLS.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML_DRILLS.write_text(page, encoding="utf-8", newline="\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus-cap", type=int, default=None,
                     help="override drill_weights.json corpus_drill_cap")
    ap.add_argument("--seed", type=int, default=20260714)
    ap.add_argument("--cmps", default=str(CMPS))
    ap.add_argument("--names", default=str(NAMES))
    ap.add_argument("--gold", default=str(GOLD))
    ap.add_argument("--weights", default=str(WEIGHTS))
    ap.add_argument("--skip-apkg", action="store_true", help="skip genanki export (if not installed)")
    args = ap.parse_args()

    weights = json.loads(Path(args.weights).read_text(encoding="utf-8"))
    type_order = weights["type_teaching_order"]
    min_freq = weights["min_corpus_freq"]
    corpus_cap = args.corpus_cap if args.corpus_cap is not None else weights["corpus_drill_cap"]

    print("loading names.csv frequency vector ...")
    names_freq = load_names_freq(args.names)
    print("  %d surfaces with a measured corpus frequency" % len(names_freq))

    print("loading gold Gita compounds ...")
    gold_items, ambiguous_n = load_gold(args.gold, names_freq)
    print("  %d gold-tagged compounds (%d ambiguous dual-tag, excluded from identify)"
          % (len(gold_items), ambiguous_n))

    gold_identify = build_identify_items(gold_items)
    gold_split = build_gold_split_items(gold_items)
    dropped_split_n = len(gold_items) - len(gold_split)
    type_dist = Counter(g["type"] for g in gold_identify)
    print("  type distribution (identify pool): %s"
          % ", ".join("%s=%d" % (t, type_dist.get(t, 0)) for t in type_order))
    print("  %d gold rows unsegmented (no hyphen in lemma), excluded from split" % dropped_split_n)

    print("loading cmps.csv compound dictionary ...")
    cmps = load_cmps(args.cmps)
    print("  %d unique compound headwords" % len(cmps))

    gold_surfaces = {g["lemma"].replace("-", "") for g in gold_items}
    corpus_pool = rank_corpus_items(cmps, names_freq, gold_surfaces, min_freq)
    print("  %d of those carry a measured corpus frequency >= %d (the ranked corpus pool)"
          % (len(corpus_pool), min_freq))

    curriculum_rows, by_type = build_curriculum(gold_identify, type_order)
    reference_rows = build_reference(by_type, type_order)
    items, corpus_used_n = build_drill_items(gold_identify, gold_split, corpus_pool, corpus_cap, args.seed)

    write_curriculum_tsv(curriculum_rows)
    write_reference_tsv(reference_rows)
    write_drills_json(items, len(corpus_pool), corpus_used_n, corpus_cap)
    write_drills_tsv(items)
    if not args.skip_apkg:
        write_apkg(items)
    write_curriculum_html(curriculum_rows, ambiguous_n, dropped_split_n)
    write_reference_html(reference_rows, type_order)
    write_drills_html(items)

    print()
    for t in type_order:
        n = type_dist.get(t, 0)
        print("type %s (%s): %d gold-verified example%s" % (t, TYPE_NAME[t], n, "" if n == 1 else "s"))
    print("wrote %s (%d rows, %d lessons)" % (OUT_CURRICULUM_TSV, len(curriculum_rows), len(type_order)))
    print("wrote %s (%d rows)" % (OUT_REFERENCE_TSV, len(reference_rows)))
    print("wrote %s (%d items: %d identify, %d split-gold, %d split-corpus)"
          % (OUT_DRILLS_JSON, len(items), len(gold_identify), len(gold_split), corpus_used_n))
    print("wrote %s, %s, %s" % (OUT_HTML_CURRICULUM, OUT_HTML_DRILLS, OUT_HTML_REFERENCE))


if __name__ == "__main__":
    main()
