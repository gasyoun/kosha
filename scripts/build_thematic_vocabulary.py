#!/usr/bin/env python
"""Thematic vocabulary axis — group corpus vocabulary by Amarakosa varga (H1462).

Wave alongside H947's frequency axis: instead of "learn the N most frequent
words", this axis is "learn the words in theme X" — the classical Amarakosa
(Amarakosha) organizes ~5,590 synsets into 24 vargas (thematic sections:
sky, earth, humans, animals, ...); the first 20 are genuinely thematic (the
last 4 are grammatical/miscellaneous annexes, per A58's THEMATIC split,
SanskritLexicography/data/semdom_ak_bridge.py).

This is an L4 "surface" move over already-committed data — no new corpus
mining. Three existing assets are joined, none rebuilt:
  1. ../AMAR/amar.txt              -- the AK text itself (varga -> eid -> lemmas)
  2. ../SanskritLexicography/data/semdom_varga_crosswalk.csv -- A58's varga ->
     SIL semdom domain-name labels (used here only as cross-reference tags,
     not as the theme's primary name -- the varga's own Sanskrit name IS the
     theme, semdom tags are secondary keywords for searchability)
  3. data/frequency/vocab_curriculum.tsv -- H947's committed core-vocabulary
     table (deva/iast/gloss/card_href/core_rank), used as the "real card"
     filter -- deliberately NOT docs/cards/ (gitignored, absent in a fresh
     worktree; H1460 flagged this exact trap for the sibling in-browser-page
     handoff). A lemma not in vocab_curriculum.tsv has no card and is dropped
     (reported, never silently absorbed) -- same "no dead links" bar as H947.

`parse_amar` / VARGA_IDS are a straight adaptation of
SanskritLexicography/data/semdom_ak_bridge.py's parser (public/MIT, same
org) -- not re-derived, ported so this repo has no import across the repo
fence.

Outputs:
  * data/frequency/thematic_vocabulary.tsv   varga_id · kanda · theme_iast ·
                                              theme_slp1 · semdom_keywords ·
                                              lemma_slp1 · deva · iast · gloss ·
                                              core_rank · card_href
  * data/frequency/thematic_vocab_drills.json   recognition + recall items,
                                              distractors drawn from the SAME
                                              theme (harder than same-frequency-
                                              band distractors -- the point of
                                              a thematic axis)
  * data/frequency/thematic_vocabulary.apkg  Anki deck, one sub-deck per theme
  * reading/vocabulary/thematic/index.html   browsable-by-theme page

Public/MIT, credit Dr. Mārcis Gasūns. Usage:
  python scripts/build_thematic_vocabulary.py [--seed 20260722]
"""
import argparse
import csv
import html
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent
AMAR = GH / "AMAR" / "amar.txt"
SEMDOM_CROSSWALK = GH / "SanskritLexicography" / "data" / "semdom_varga_crosswalk.csv"
VOCAB_CURRICULUM = ROOT / "data" / "frequency" / "vocab_curriculum.tsv"
OUT_TSV = ROOT / "data" / "frequency" / "thematic_vocabulary.tsv"
OUT_DRILLS = ROOT / "data" / "frequency" / "thematic_vocab_drills.json"
OUT_APKG = ROOT / "data" / "frequency" / "thematic_vocabulary.apkg"
OUT_HTML = ROOT / "reading" / "vocabulary" / "thematic" / "index.html"

sys.path.insert(0, str(GH / "sanskrit-util" / "py"))
from sanskrit_util import from_slp1, slp1_to_devanagari  # noqa: E402

# Vargas in file order -> canonical IDs (must match semdom_varga_crosswalk.csv's
# ak_varga_id and SanskritLexicography/data/semdom_ak_bridge.py's VARGA_IDS).
VARGA_IDS = [
    "AK-1.1", "AK-1.2", "AK-1.3", "AK-1.4", "AK-1.5", "AK-1.6", "AK-1.7",
    "AK-1.8", "AK-1.9", "AK-1.10", "AK-2.1", "AK-2.2", "AK-2.3", "AK-2.4",
    "AK-2.5", "AK-2.6", "AK-2.7", "AK-2.8", "AK-2.9", "AK-2.10", "AK-3.1",
    "AK-3.2", "AK-3.3", "AK-3.4",
]
# The first 20 are genuinely thematic (sky/earth/human/animal/...); the last 4
# are grammatical/miscellaneous annexes (A58's THEMATIC split) -- this axis is
# about theme-based vocabulary study, so it only covers the thematic 20.
THEMATIC_VARGA_IDS = set(VARGA_IDS[:20])

ANKI_MODEL_ID = 1607392030
ANKI_DECK_ID = 1607392031


def parse_amar(path):
    """Yield (varga_id, eid, [slp1 lemmas]) in file order.

    Ported from SanskritLexicography/data/semdom_ak_bridge.py::parse_amar
    (same regex, same varga-header marker) -- not re-derived.
    """
    out = []
    vi = -1
    with open(path, encoding="utf-8", errors="replace") as f:
        for ln in f:
            ln = ln.strip()
            if ln.startswith(";v{"):
                vi += 1
                continue
            m = re.match(r"<eid>(\d+)<syns><s>(.*?)</s>", ln)
            if m and vi >= 0:
                eid = int(m.group(1))
                lemmas = []
                for tok in m.group(2).split(","):
                    tok = tok.strip()
                    if "-" in tok:
                        tok = tok.rsplit("-", 1)[0]  # strip gender code
                    if tok:
                        lemmas.append(tok)
                out.append((VARGA_IDS[vi], eid, lemmas))
    return out


def load_varga_meta(amar_path, crosswalk_path):
    """Return {varga_id: {"iast": ..., "slp1": ..., "keywords": [...], "kanda": n}}."""
    meta = {}
    vi = -1
    with open(amar_path, encoding="utf-8", errors="replace") as f:
        for ln in f:
            ln = ln.strip()
            m = re.match(r";v\{<s>(.*?)</s>\}", ln)
            if m:
                vi += 1
                if vi >= len(VARGA_IDS):
                    break
                vid = VARGA_IDS[vi]
                slp1 = m.group(1)
                meta[vid] = {
                    "slp1": slp1, "iast": from_slp1(slp1),
                    "kanda": int(vid.split("-")[1].split(".")[0]),
                    "keywords": [],
                }
    keywords_by_varga = defaultdict(list)
    for r in csv.DictReader(open(crosswalk_path, encoding="utf-8")):
        vid = r["ak_varga_id"]
        if r["match_type"] == "close" and len(keywords_by_varga[vid]) < 3:
            keywords_by_varga[vid].append(r["semdom_name"])
    for vid, kws in keywords_by_varga.items():
        if vid in meta:
            meta[vid]["keywords"] = kws
    return meta


def load_curriculum_lookup(path):
    """{lemma_slp1: row} from the committed H947 vocab_curriculum.tsv."""
    rows = list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))
    out = {}
    for r in rows:
        out.setdefault(r["lemma_slp1"], r)  # first (highest-frequency) row wins
    return out


def build_theme_rows(synsets, varga_meta, curriculum):
    rows = []
    seen = set()  # (varga_id, lemma_slp1) -- a lemma can repeat within a varga
    dropped_no_card = 0
    considered = 0
    for varga_id, eid, lemmas in synsets:
        if varga_id not in THEMATIC_VARGA_IDS:
            continue
        vm = varga_meta.get(varga_id)
        if vm is None:
            continue
        for lemma in lemmas:
            considered += 1
            key = (varga_id, lemma)
            if key in seen:
                continue
            seen.add(key)
            c = curriculum.get(lemma)
            if c is None:
                dropped_no_card += 1
                continue
            rows.append({
                "varga_id": varga_id, "kanda": vm["kanda"],
                "theme_iast": vm["iast"], "theme_slp1": vm["slp1"],
                "semdom_keywords": "; ".join(vm["keywords"]),
                "lemma_slp1": lemma, "deva": slp1_to_devanagari(lemma),
                "iast": from_slp1(lemma), "gloss": c["gloss"],
                "core_rank": int(c["core_rank"]), "card_href": c["card_href"],
            })
    rows.sort(key=lambda r: (VARGA_IDS.index(r["varga_id"]), r["core_rank"]))
    return rows, considered, dropped_no_card


def write_tsv(rows):
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["varga_id", "kanda", "theme_iast", "theme_slp1", "semdom_keywords",
                    "lemma_slp1", "deva", "iast", "gloss", "core_rank", "card_href"])
        for r in rows:
            w.writerow([r["varga_id"], r["kanda"], r["theme_iast"], r["theme_slp1"],
                        r["semdom_keywords"], r["lemma_slp1"], r["deva"], r["iast"],
                        r["gloss"], r["core_rank"], r["card_href"]])


def build_drills(rows, seed):
    rng = random.Random(seed)
    by_theme = defaultdict(list)
    for r in rows:
        by_theme[r["varga_id"]].append(r)

    items = []
    idx = 0
    for r in rows:
        theme_pool = [x for x in by_theme[r["varga_id"]] if x["lemma_slp1"] != r["lemma_slp1"]]
        rng.shuffle(theme_pool)
        distractor_glosses = [x["gloss"] for x in theme_pool if x["gloss"]][:3]
        distractor_forms = ["%s / %s" % (x["deva"], x["iast"]) for x in theme_pool][:3]

        idx += 1
        items.append({
            "aspect": "vocabulary-thematic", "type": "recognition", "id": "TV-%05d" % idx,
            "prompt": "%s / %s — meaning?" % (r["deva"], r["iast"]),
            "answer": r["gloss"], "distractors": distractor_glosses,
            "theme": r["theme_iast"], "varga_id": r["varga_id"], "rank": r["core_rank"],
            "evidence": r["card_href"], "source_dataset": "thematic-vocabulary",
        })
        idx += 1
        items.append({
            "aspect": "vocabulary-thematic", "type": "recall", "id": "TV-%05d" % idx,
            "prompt": "In the theme “%s” — “%s”?" % (r["theme_iast"], r["gloss"]),
            "answer": "%s / %s" % (r["deva"], r["iast"]), "distractors": distractor_forms,
            "theme": r["theme_iast"], "varga_id": r["varga_id"], "rank": r["core_rank"],
            "evidence": r["card_href"], "source_dataset": "thematic-vocabulary",
        })
    OUT_DRILLS.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "title": "Sanskrit vocabulary — thematic (Amarakosa varga) drills",
        "description": "Recognition (word -> meaning) and recall (meaning -> word) items, "
                        "grouped by classical Amarakosa thematic section (varga); distractors "
                        "drawn from the SAME theme, not the same frequency band -- the harder, "
                        "more meaningful confusion set for a thematic-study axis.",
        "source": {
            "vargas": "../AMAR/amar.txt (Amarakosa, 20 thematic vargas of 24)",
            "keywords": "../SanskritLexicography/data/semdom_varga_crosswalk.csv (A58 crosswalk, "
                        "cross-reference only, not the theme's primary name)",
            "cards": "data/frequency/vocab_curriculum.tsv (H947, real-card filter)",
            "builder": "scripts/build_thematic_vocabulary.py",
            "license": "public/MIT; AK text via sanskrit.uohyd.ac.in/scl; "
                       "MW/PWG/AP90 entries per Cologne Sanskrit Dictionaries terms.",
        },
        "items": items,
    }
    OUT_DRILLS.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return items


def write_apkg(rows):
    import genanki
    model = genanki.Model(
        ANKI_MODEL_ID, "Thematic vocabulary drill (H1462)",
        fields=[{"name": "Front"}, {"name": "Gloss"}, {"name": "Theme"}, {"name": "Rank"}],
        templates=[{
            "name": "Card 1",
            "qfmt": "<div class=\"q\">{{Front}}</div><div class=\"t\">{{Theme}}</div>",
            "afmt": "{{FrontSide}}<hr id=\"answer\"><div class=\"a\">{{Gloss}}</div>"
                    "<div class=\"meta\">core rank {{Rank}}</div>",
        }],
        css=".card{font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:20px;"
            "text-align:center;color:#1c1a17;background:#fbfaf7}"
            ".q{font-size:1.2em}.t{color:#7a4f2b;font-size:.8em;margin-top:.2em}"
            ".a{font-weight:600;color:#7a4f2b;margin:.3em 0}.meta{color:#6b6660;font-size:.75em}",
    )
    by_theme = {}
    deck_id_base = ANKI_DECK_ID
    top_deck = genanki.Deck(deck_id_base, "Sanskrit vocabulary — thematic (kosha, H1462)")
    decks = [top_deck]
    for i, r in enumerate(rows):
        theme = r["theme_iast"]
        if theme not in by_theme:
            by_theme[theme] = genanki.Deck(
                deck_id_base + len(by_theme) + 1,
                "Sanskrit vocabulary — thematic (kosha, H1462)::%s" % theme)
            decks.append(by_theme[theme])
        front = "%s &middot; %s" % (r["deva"], r["iast"])
        by_theme[theme].add_note(genanki.Note(
            model=model,
            fields=[front, r["gloss"] or "(no gloss extracted)", theme, str(r["core_rank"])],
            tags=[re.sub(r"\W+", "-", theme).strip("-")],
        ))
    OUT_APKG.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(decks).write_to_file(str(OUT_APKG))


def _write_html(rows, considered, dropped, n_vargas_kept):
    by_theme = defaultdict(list)
    order = []
    for r in rows:
        if r["varga_id"] not in by_theme:
            order.append(r["varga_id"])
        by_theme[r["varga_id"]].append(r)

    blocks = []
    for vid in order:
        items = by_theme[vid]
        kw = items[0]["semdom_keywords"]
        rowhtml = "\n".join(
            "<tr><td class='dv'>{d}</td><td class='ia'>{i}</td>"
            "<td class='gl'>{g}</td></tr>".format(
                d=html.escape(o["deva"]), i=html.escape(o["iast"]),
                g=html.escape(o["gloss"] or "—"))
            for o in items)
        blocks.append(
            "<section><h2>{iast} <span class='n'>{n} words</span></h2>"
            "<p class='kw'>{kw}</p>"
            "<div class='scroll'><table><thead><tr><th>देव</th><th>IAST</th>"
            "<th>gloss</th></tr></thead><tbody>{rows}</tbody></table></div></section>".format(
                iast=html.escape(items[0]["theme_iast"]), n=len(items),
                kw=html.escape(kw) if kw else "&nbsp;", rows=rowhtml))

    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sanskrit vocabulary — by theme (Amarakosa)</title>
<meta name="description" content="Corpus vocabulary grouped by classical Amarakosa thematic section, for study by topic rather than frequency.">
<style>
 :root{{--bg:#fbfaf7;--fg:#1c1a17;--muted:#6b6660;--line:#e6e1d8;--card:#fff;--accent:#7a4f2b;--chip:#f2ede3}}
 @media(prefers-color-scheme:dark){{:root{{--bg:#17150f;--fg:#ece7dd;--muted:#9c948a;--line:#2e2a22;--card:#1f1c15;--accent:#d9a066;--chip:#2a251c}}}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
 .wrap{{max-width:860px;margin:0 auto;padding:1.5rem 1.1rem 4rem}}
 h1{{font-size:1.5rem;margin:.2rem 0 .3rem}} .sub{{color:var(--muted);font-size:.9rem;margin:0 0 1rem}}
 section{{margin-bottom:1.6rem}} h2{{font-size:1.05rem;border-bottom:2px solid var(--line);padding-bottom:.2rem}}
 h2 .n{{color:var(--muted);font-weight:400;font-size:.85rem;float:right}}
 p.kw{{color:var(--muted);font-size:.82rem;margin:.2rem 0 .5rem}}
 .scroll{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:.9rem}}
 th,td{{text-align:left;padding:.35rem .55rem;border-bottom:1px solid var(--line);vertical-align:top}}
 th{{color:var(--muted);font-weight:600}} td.dv{{font-size:1.1rem;white-space:nowrap}}
 td.ia{{white-space:nowrap;color:var(--muted)}} td.gl{{color:var(--fg)}}
 a{{color:var(--accent)}} footer{{margin-top:1.6rem;color:var(--muted);font-size:.8rem}}
</style></head><body><div class="wrap">
 <h1>Sanskrit vocabulary — by theme</h1>
 <p class="sub">{n} corpus-attested core-vocabulary lemmas ({dropped} Amarakosa lemmas of {considered}
 considered had no committed dictionary card, dropped — no dead links), grouped into
 {nv} classical Amarakosa thematic sections (varga). Ordered within each theme by corpus core-vocabulary
 rank (most frequent first). Semdom cross-reference tags are the closest matching
 <a href="https://semdom.org">SIL semantic domains</a> (A58 crosswalk), shown for orientation only.</p>
 {blocks}
 <footer>Vargas + lemmas from the <a href="https://github.com/gasyoun/AMAR">Amarakosa</a> (UoHyd SCL).
  Semdom cross-reference: <a href="https://github.com/gasyoun/SanskritLexicography/blob/master/data/SEMDOM_AK_CROSSWALK_2026.md">A58 crosswalk</a>.
  Cards/glosses from <a href="https://github.com/gasyoun/kosha/blob/main/data/frequency/vocab_curriculum.tsv">vocab_curriculum.tsv</a> (H947).
  Built by <a href="https://github.com/gasyoun/kosha/blob/main/scripts/build_thematic_vocabulary.py">build_thematic_vocabulary.py</a>.
  Dr. Mārcis Gasūns.</footer>
</div></body></html>
"""
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(
        page.format(n=len(rows), dropped=dropped, considered=considered, nv=n_vargas_kept,
                    blocks="\n".join(blocks)),
        encoding="utf-8", newline="\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260722)
    ap.add_argument("--amar", default=str(AMAR))
    ap.add_argument("--crosswalk", default=str(SEMDOM_CROSSWALK))
    ap.add_argument("--curriculum", default=str(VOCAB_CURRICULUM))
    args = ap.parse_args()

    varga_meta = load_varga_meta(Path(args.amar), Path(args.crosswalk))
    synsets = parse_amar(Path(args.amar))
    curriculum = load_curriculum_lookup(Path(args.curriculum))

    rows, considered, dropped = build_theme_rows(synsets, varga_meta, curriculum)
    write_tsv(rows)
    items = build_drills(rows, args.seed)
    write_apkg(rows)
    n_vargas_kept = len({r["varga_id"] for r in rows})
    _write_html(rows, considered, dropped, n_vargas_kept)

    print("dropped %d/%d Amarakosa (varga, lemma) pairs with no committed vocab_curriculum "
          "card (no dead /w/ links)" % (dropped, considered))
    print("wrote %s (%d rows, %d themes), %d drill items, %s, %s"
          % (OUT_TSV, len(rows), n_vargas_kept, len(items), OUT_APKG, OUT_HTML))


if __name__ == "__main__":
    main()
