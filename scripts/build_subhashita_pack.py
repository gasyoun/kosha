#!/usr/bin/env python
"""Beginner subhāṣita reading pack — pedagogy Wave RU, surface W-RU-b (H1279).

Builds the graded beginner reading pack from the curated band
(data/subhashita/beginner_band.tsv — see CURATION_NOTES.md for the criteria and
the full reject log): each selected Indische-Sprüche saying is sandhi-split,
junction-labelled against the corpus rule table, metre-tagged, and shipped as
a JSON dataset + a self-contained viewer shard + an Anki deck.

Pipeline (consumes shipped layers, derives nothing new):
  * split      DharmaMitra `unsandhied` neural segmentation per whitespace
               chunk — split-method C of the sandhi programme's A/B/C harness
               (compare_sandhi_methods.py: near-perfect precision, far ahead of
               vidyut-cheda). Cached to data/sandhi/_cache/
               dharmamitra_indische_sprueche.json (committed), so re-runs are
               offline and byte-stable; pass --allow-network only to fill a
               cold cache. A chunk-initial avagraha is restored to `a` first
               ("'pi" segments as "api").
  * junctions  each seam is labelled with its `X Y → Z` rule and the rule's
               corpus attestation count from data/sandhi/corpus_sandhi.tsv:
               - INSIDE a fused chunk: smallest-DFS reconstruction — pick the
                 attested rule (or bare compound join) whose application makes
                 the rebuilt surface prefix-match the chunk; unresolvable seams
                 stay unlabelled (never guessed).
               - ACROSS chunks: only when both neighbours are single-token
                 (the mode-1 restriction of compare_sandhi_methods B/C),
                 induced with dcs_sandhi_induce.induce_rule — the same
                 notation the Gītā hand table validates.
  * metre      read from data/subhashita/subhashita_difficulty.tsv (W2a-r
               scorer output; every band member has a resolved metre —
               curation criterion C4).
  * gloss.ru   NOT populated: the W-RU-a layer (H1278) has not shipped.
               The absence is recorded in the pack meta (`gloss_ru_status`)
               and is a logged re-run TODO, not a silent gap.

Outputs:
  data/subhashita/subhashita_beginner_pack.json   the dataset (byte-stable)
  reading/subhashita/data.js                      window.SUBHASHITA_DATA shard
  data/subhashita/subhashita_beginner_anki.apkg   Anki deck (genanki; NOT
        byte-stable — sqlite timestamps — same caveat as the other decks)

Usage:
  python scripts/build_subhashita_pack.py [--allow-network] [--built YYYY-MM-DD]
"""
import argparse
import csv
import json
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent if (ROOT.parent / "SanskritLexicography").exists() else ROOT.parent.parent
SPRUECHE = GH / "SanskritLexicography" / "IndischeSprueche" / "data" / "indische_sprueche.jsonl"
BAND_TSV = ROOT / "data" / "subhashita" / "beginner_band.tsv"
DIFF_TSV = ROOT / "data" / "subhashita" / "subhashita_difficulty.tsv"
RULES_TSV = ROOT / "data" / "sandhi" / "corpus_sandhi.tsv"
DM_CACHE = ROOT / "data" / "sandhi" / "_cache" / "dharmamitra_indische_sprueche.json"
OUT_JSON = ROOT / "data" / "subhashita" / "subhashita_beginner_pack.json"
OUT_JS = ROOT / "reading" / "subhashita" / "data.js"
OUT_APKG = ROOT / "data" / "subhashita" / "subhashita_beginner_anki.apkg"

sys.path.insert(0, str(ROOT / "scripts"))
from dcs_sandhi_induce import induce_rule, nfc  # noqa: E402

DM_API = "https://dharmamitra.org/api/tagging/"
DM_BATCH = 32
# stable genanki ids — never regenerate randomly, or re-imports duplicate
ANKI_MODEL_ID = 1720719279
ANKI_DECK_ID = 1720719280

STRIP_CHARS = "|/।॥0123456789()[]"


def load_rules():
    """corpus rule table: rule string -> (category, global_count); plus an
    index by (X, Y) for the reconstruction search."""
    by_rule, by_edge = {}, {}
    with RULES_TSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            rule = nfc(row["rule"])
            by_rule[rule] = (row["category"], int(row["global_count"]))
            left, arrow, out = rule.partition(" → ")
            if not arrow:
                continue
            parts = left.split(" ")
            if len(parts) != 2:
                continue
            x, y = parts
            out_joined = out.replace("Ø", "").replace(" ", "")
            by_edge.setdefault((x, y), []).append((rule, out_joined, int(row["global_count"])))
    for v in by_edge.values():
        v.sort(key=lambda t: -t[2])
    return by_rule, by_edge


def clean_chunk(raw):
    """Strip punctuation/digits off a whitespace chunk; keep avagraha."""
    return nfc("".join(c for c in raw if c not in STRIP_CHARS).strip())


def restore_avagraha(chunk):
    return "a" + chunk[1:] if chunk.startswith("'") else chunk


def dm_segment(chunks, allow_network):
    """{chunk (avagraha-restored IAST): [unsandhied tokens]} via the
    DharmaMitra `unsandhied` mode, cache-first (same contract and etiquette as
    compare_sandhi_methods._dm_segment)."""
    cache = json.loads(DM_CACHE.read_text(encoding="utf-8")) if DM_CACHE.exists() else {}
    todo = [c for c in dict.fromkeys(chunks) if c not in cache]
    if todo:
        if not allow_network:
            sys.exit(f"{len(todo)} chunks uncached; pass --allow-network to query DharmaMitra")
        import time
        import requests
        DM_CACHE.parent.mkdir(parents=True, exist_ok=True)
        for i in range(0, len(todo), DM_BATCH):
            batch = todo[i:i + DM_BATCH]
            for attempt in range(4):
                try:
                    resp = requests.post(DM_API, json={"texts": batch, "mode": "unsandhied",
                                                       "human_readable_tags": True}, timeout=120)
                    resp.raise_for_status()
                    break
                except Exception as e:
                    if attempt == 3:
                        DM_CACHE.write_text(json.dumps(cache, ensure_ascii=False, sort_keys=True),
                                            encoding="utf-8")
                        raise RuntimeError(f"DharmaMitra batch failed after 4 tries "
                                           f"({len(cache)} cached so far); rerun to resume: {e}")
                    time.sleep(2 ** attempt)
            for chunk, seg in zip(batch, resp.json()["results"]):
                cache[chunk] = [nfc(t) for t in seg.split("_") if t]
            DM_CACHE.write_text(json.dumps(cache, ensure_ascii=False, sort_keys=True),
                                encoding="utf-8")
            print(f"  DharmaMitra: {min(i + DM_BATCH, len(todo))}/{len(todo)} chunks queried")
            time.sleep(0.3)
    return cache


IAST_OK = set("aāiīuūṛṝḷḹeoṃḥkgṅcjñṭḍṇtdnpbmyrlvśṣsh'")
PRUNE_SLACK = 4  # a token's tail may still be rewritten by the NEXT seam's rule


PAUSA_DRIFT = set("ḥrsśṣmṃoadt")  # chars a final-pausa tail may toggle through


def tail_drift_equal(built, surface):
    """True when built and surface differ only in the final-pausa tail (<=2
    chars, pausa-class characters only) — the chunk's own tail is sandhied
    against the NEXT chunk (m/ṃ, ḥ/r/ś/s, aḥ/o …), which is a cross-boundary
    event, not this seam's. Short strings (<3 chars) must match exactly, or a
    doubled echo like ca->caca would slip through the window."""
    if built == surface:
        return True
    if min(len(built), len(surface)) < 3:
        return False
    common = 0
    for a, b in zip(built, surface):
        if a != b:
            break
        common += 1
    if common < min(len(built), len(surface)) - 2 or abs(len(built) - len(surface)) > 2:
        return False
    return all(c in PAUSA_DRIFT for c in built[common:]) and \
        all(c in PAUSA_DRIFT for c in surface[common:])


def charset_clean(toks):
    return bool(toks) and all(t and all(c in IAST_OK for c in t) for t in toks)


def label_internal_seams(surface, tokens, by_edge):
    """DFS over per-seam candidate rules so the rebuilt string equals the fused
    chunk surface (tail-pausa drift tolerated at the end). Returns the label
    list (rule string or "+" bare join per seam) — or None when NO candidate
    path rebuilds the surface. That None doubles as the validation verdict:
    a segmentation that cannot rebuild its own surface is either splitter
    garbage (misaligned DharmaMitra batches were observed returning another
    text's tokens) or uses a junction the corpus rule table has never seen —
    either way it is not shown to a learner ('no fabricated signal'). The
    prefix prune leaves PRUNE_SLACK chars of slack — a token's final visarga/
    vowel is often rewritten only when the NEXT seam's rule is applied
    (atithiḥ -> atithir...)."""
    surface = nfc(surface)
    n = len(tokens)
    if n <= 1:
        return []

    def dfs(built, i, labels):
        if i == n:
            return labels if tail_drift_equal(built, surface) else None
        t = nfc(tokens[i])
        cands = [(built + t, "+")]
        for (x, y), rules in by_edge.items():
            if built.endswith(x) and t.startswith(y):
                for rule, out_joined, _cnt in rules:
                    cands.append((built[:-len(x)] + out_joined + t[len(y):], rule))
        for cand_built, label in cands:
            stable = cand_built[:max(0, len(cand_built) - PRUNE_SLACK)]
            if not surface.startswith(stable[:len(surface)]):
                continue
            if len(cand_built) - PRUNE_SLACK > len(surface) + 2:
                continue
            got = dfs(cand_built, i + 1, labels + [label])
            if got:
                return got
        return None

    return dfs(nfc(tokens[0]), 1, [])


def accept_seg(under, toks, by_edge):
    """Validation ladder for one chunk's candidate segmentation. Returns
    (tokens, seam_labels) or None. Single token: charset + tail-drift
    resemblance. Multi token: charset, no 1-char fragments (splitters were
    observed shaving morphology into 'jāt'+'o' / 'a'+'vicārya' — a word-level
    split never yields a bare letter), and the DFS must rebuild the surface."""
    if not charset_clean(toks):
        return None
    if len(toks) == 1:
        return (toks, []) if tail_drift_equal(nfc(toks[0]), nfc(under)) else None
    if any(len(t) < 2 for t in toks):
        return None
    labels = label_internal_seams(under, toks, by_edge)
    return (toks, labels) if labels else None


_chedaka = None


def cheda_fallback(chunk):
    """Offline vidyut-cheda (split-method B) for chunks whose DharmaMitra
    result failed validation; surface itself if cheda has nothing either."""
    global _chedaka
    from vidyut.lipi import Scheme, transliterate
    if _chedaka is None:
        from vidyut.cheda import Chedaka
        _chedaka = Chedaka(str(GH / "vidyut-data"))
    slp = transliterate(chunk, Scheme.Iast, Scheme.Slp1)
    try:
        toks = [transliterate(t.text, Scheme.Slp1, Scheme.Iast) for t in _chedaka.run(slp)]
    except Exception:
        toks = []
    return [nfc(t) for t in toks]


def build_saying(rec, diff, seg_cache, by_rule, by_edge, seg_src_stats):
    lines = []
    for raw_line in rec["iast"].replace("||", "|").split("/"):
        line = raw_line.strip().strip("|").strip()
        if not line or line.isdigit():
            continue
        raw_chunks = [clean_chunk(c) for c in line.split()]
        raw_chunks = [c for c in raw_chunks if c]
        chunks = []
        for c in raw_chunks:
            under = restore_avagraha(c)
            got = accept_seg(under, seg_cache.get(under) or [], by_edge)
            if got:
                seg_src_stats["dm"] += 1
            else:
                got = accept_seg(under, cheda_fallback(under), by_edge)
                if got:
                    seg_src_stats["cheda"] += 1
                else:
                    got = ([under], [])
                    seg_src_stats["surface"] += 1
            toks, seams = got
            chunks.append({"s": c, "t": toks, "j": seams})
        cross = []
        for a, b in zip(chunks, chunks[1:]):
            rule = None
            if len(a["t"]) == 1 and len(b["t"]) == 1:  # mode-1 restriction
                r, _flag = induce_rule(a["t"][0], a["s"], b["t"][0], restore_avagraha(b["s"]))
                rule = nfc(r) if r else None
            cross.append(rule)
        lines.append({"text": line, "chunks": chunks, "xj": cross})

    n_seams = n_labelled = 0
    for ln in lines:
        for ch in ln["chunks"]:
            n_seams += len(ch["j"])
            n_labelled += sum(1 for j in ch["j"] if j and j != "+")
        n_seams += len(ln["xj"])
        n_labelled += sum(1 for j in ln["xj"] if j)

    return {
        "num": rec["num"],
        "saying_id": rec["saying_id"],
        "deva": rec["deva"],
        "iast": rec["iast"],
        "translation_de": (rec.get("translation_de") or "").replace("/", " "),
        "source_attribution": (rec.get("source_attribution") or "").replace("/", " "),
        "difficulty": float(diff["difficulty"]),
        "metre": diff["metre"],
        "metre_method": diff["metre_method"],
        "syllables": int(diff["syllables"]),
        "lines": lines,
        "n_junctions": n_seams,
        "n_junctions_labelled": n_labelled,
        "gloss_ru": None,
    }


def attested(rule, by_rule):
    hit = by_rule.get(nfc(rule)) if rule and rule != "+" else None
    return hit[1] if hit else None


def render_split(saying, by_rule):
    """Plain-text split rendering for the Anki back: tokens joined, fused seams
    marked with ·, labelled junction rules listed under the line."""
    out_lines, rules_seen = [], []
    for ln in saying["lines"]:
        words = [" · ".join(ch["t"]) if len(ch["t"]) > 1 else ch["t"][0] for ch in ln["chunks"]]
        out_lines.append(" ".join(words))
        for ch in ln["chunks"]:
            for j in ch["j"]:
                if j and j != "+":
                    rules_seen.append(j)
        for j in ln["xj"]:
            if j:
                rules_seen.append(j)
    uniq = list(dict.fromkeys(rules_seen))
    tagged = [f"{r} (×{attested(r, by_rule)})" if attested(r, by_rule) else r for r in uniq]
    return out_lines, tagged


def write_apkg(pack, by_rule):
    import genanki
    model = genanki.Model(
        ANKI_MODEL_ID, "Subhāṣita beginner (H1279)",
        fields=[{"name": "Deva"}, {"name": "Iast"}, {"name": "Split"}, {"name": "Rules"},
                {"name": "Metre"}, {"name": "TranslationDE"}, {"name": "Source"}, {"name": "Num"}],
        templates=[{
            "name": "Card 1",
            "qfmt": "<div class=\"deva\">{{Deva}}</div><div class=\"iast\">{{Iast}}</div>",
            "afmt": "{{FrontSide}}<hr id=\"answer\">"
                    "<div class=\"split\">{{Split}}</div>"
                    "<div class=\"rules\">{{Rules}}</div>"
                    "<div class=\"metre\">{{Metre}}</div>"
                    "<div class=\"tr\">{{TranslationDE}}</div>"
                    "<div class=\"src\">Indische Sprüche {{Num}} &middot; {{Source}}</div>",
        }],
        css=".card{font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:20px;"
            "text-align:center;color:#1c1a17;background:#fbfaf7}"
            ".deva{font-size:1.25em;margin-bottom:.2em}.iast{color:#6b6660;font-size:.85em}"
            ".split{font-weight:600;color:#7a4f2b;margin:.3em 0}"
            ".rules{color:#6b6660;font-size:.72em}.metre{color:#2a6f4e;font-size:.8em;margin:.2em 0}"
            ".tr{font-size:.8em;margin-top:.35em}.src{color:#9c948a;font-size:.65em;margin-top:.4em}",
    )
    deck = genanki.Deck(ANKI_DECK_ID, "Sanskrit subhāṣita — beginner band (kosha, H1279)")
    for s in pack["sayings"]:
        split_lines, rules = render_split(s, by_rule)
        deck.add_note(genanki.Note(
            model=model,
            fields=[s["deva"].replace("/", " "), s["iast"].replace("/", " "),
                    "<br>".join(split_lines), " &middot; ".join(rules),
                    f"{s['metre']} ({s['syllables']} syllables)",
                    s["translation_de"], s["source_attribution"][:120], str(s["num"])],
            tags=[f"metre::{s['metre'].replace(' ', '-')}", "kosha-subhashita-beginner"],
        ))
    genanki.Package(deck).write_to_file(str(OUT_APKG))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-network", action="store_true",
                    help="permit DharmaMitra API calls for uncached chunks")
    ap.add_argument("--built", default="2026-07-19", help="build date stamp (pinned for byte-stability)")
    args = ap.parse_args()

    band = {}
    with BAND_TSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            band[int(row["num"])] = row["note"]
    diffs = {}
    with DIFF_TSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if int(row["num"]) in band:
                diffs[int(row["num"])] = row
    recs = {}
    with SPRUECHE.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["num"] in band:
                recs[r["num"]] = r
    missing = sorted(set(band) - set(recs))
    if missing:
        sys.exit(f"band nums missing from JSONL: {missing}")

    by_rule, by_edge = load_rules()

    all_chunks = []
    for r in recs.values():
        for raw_line in r["iast"].replace("||", "|").split("/"):
            for c in raw_line.strip().strip("|").split():
                cc = clean_chunk(c)
                if cc:
                    all_chunks.append(restore_avagraha(cc))
    seg_cache = dm_segment(all_chunks, args.allow_network)

    seg_src_stats = {"dm": 0, "cheda": 0, "surface": 0}
    sayings = [build_saying(recs[n], diffs[n], seg_cache, by_rule, by_edge, seg_src_stats)
               for n in band]
    sayings.sort(key=lambda s: (s["difficulty"], s["num"]))
    for i, s in enumerate(sayings, 1):
        s["order"] = i

    n_internal = sum(len(ch["j"]) for s in sayings for ln in s["lines"] for ch in ln["chunks"])
    n_internal_res = sum(1 for s in sayings for ln in s["lines"] for ch in ln["chunks"]
                         for j in ch["j"] if j)
    n_cross = sum(1 for s in sayings for ln in s["lines"] for j in ln["xj"] if j)
    n_seams = sum(s["n_junctions"] for s in sayings)
    n_lab = sum(s["n_junctions_labelled"] for s in sayings)
    pack = {
        "slug": "subhashita-beginner",
        "title": "Subhāṣita — beginner band (Indische Sprüche, graded)",
        "source": "Böhtlingk, Indische Sprüche (2nd ed. 1870–73), public domain — "
                  "SanskritLexicography F33 indische_sprueche.jsonl",
        "built": args.built,
        "curation": "data/subhashita/CURATION_NOTES.md",
        "gloss_ru_status": "absent — W-RU-a (H1278) had not shipped at build time; "
                           "re-run build_subhashita_pack.py with the ru_gloss layer "
                           "once it lands (logged re-run TODO, not a silent gap)",
        "stats": {
            "sayings": len(sayings),
            "difficulty_min": min(s["difficulty"] for s in sayings),
            "difficulty_max": max(s["difficulty"] for s in sayings),
            "junctions": n_seams,
            "junctions_labelled": n_lab,
            "internal_seams": n_internal,
            "internal_seams_resolved": n_internal_res,
            "cross_boundary_rules": n_cross,
            "seg_source_chunks": seg_src_stats,
            "metres": sorted({s["metre"] for s in sayings}),
        },
        "sayings": sayings,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(pack, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    OUT_JS.parent.mkdir(parents=True, exist_ok=True)
    OUT_JS.write_text("window.SUBHASHITA_DATA = " +
                      json.dumps(pack, ensure_ascii=False) + ";\n", encoding="utf-8")
    write_apkg(pack, by_rule)

    print(f"pack: {len(sayings)} sayings; internal seams resolved {n_internal_res}/{n_internal}; "
          f"cross-boundary rules {n_cross}; seg sources {seg_src_stats}")
    print(f"  -> {OUT_JSON}\n  -> {OUT_JS}\n  -> {OUT_APKG}")


if __name__ == "__main__":
    main()
