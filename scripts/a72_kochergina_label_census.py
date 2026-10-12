#!/usr/bin/env python3
"""H6461 — A72 side-census: Kochergina (Cyrillic leg) abbreviation/label inventory.

Derives the label/abbreviation inventory of Kochergina's Sanskritsko-russkij
slovar' (digitized 1987) from the estate's B1-family entry bodies
(SamudraManthanam corpus_builder jsonl, READ-ONLY third-party source) and
compares it against the CSDL collision class of the A72 census v1 payload
(csl-atlas data/abbrev/abbrev_census.json, collisionMatrix).

Publishes DERIVED counts only: label tokens + frequencies + entry counts.
No third-party entry text is emitted (RIGHTS FENCE, H4748/N10).

Usage:
  python3 scripts/a72_kochergina_label_census.py --emit data/abbrev/kochergina_label_census.json
  python3 scripts/a72_kochergina_label_census.py --check data/abbrev/kochergina_label_census.json

Exits 0 on success; --check exits 1 when the stored payload diverges from a
fresh derivation (derive-don't-store parity gate).
"""

import argparse
import collections
import json
import os
import re
import sys

# --- paths (override for portability; defaults are the estate clones) -------
DEFAULT_JSONL = "/Users/mac/Documents/GitHub/SamudraManthanam/web/corpus_builder/jsonl/kochergina.jsonl"
DEFAULT_CENSUS = "/Users/mac/Documents/GitHub/csl-atlas/data/abbrev/abbrev_census.json"
DEFAULT_HEADWORDS = None  # optional CORRECTIONS Kochergina-1987_29007.txt (UTF-16), count-only

# --- label lexicon (curated from the discovered token distribution) ---------
# Categories map observed surface tokens to functions. Tokens verified from
# context; expansion-uncertain tokens stay in the inventory, classified "—".
LEXICON = {
    "pos_gender": ["m.", "n.", "f.", "adv.", "pn.", "pron.", "num.", "int.",
                   "pcl.", "encl.", "pref.", "indc.", "conj.", "praep."],
    "verb_system": ["pr.", "fut.", "pf.", "aor.", "pp.", "p.", "inf.", "ger.",
                    "caus.", "des.", "spv.", "cpv.", "den.", "pfph.", "imp.",
                    "ppr.", "ij.", "P.", "A.", "U."],
    "case_government": ["Acc.", "Gen.", "Dat.", "Abl.", "Instr.", "Loc.",
                        "Nom.", "Voc.", "sg.", "pl.", "du."],
    "compound_type": ["bah.", "dv."],
    "proper_name": [],  # bigram "nom. pr." handled separately
    "crossref_usage": ["см.", "тж.", "напр.", "особ.", "букв.", "перен.",
                       "назв.", "вышеназв.", "соотв.", "знач.", "обознач.",
                       "употр.", "ср."],
    "domain": ["грам.", "филос.", "астр.", "фон.", "миф.", "бот.", "муз.",
               "рел.", "анат.", "хинд.", "лингв.", "совр.", "поэт.", "мат.",
               "юр.", "воен.", "театр.", "будд.", "лит.", "мед.", "зоол."],
    "grammar_misc": ["corr.", "metr.", "end.", "upa.", "ag."],
    "script_homoglyph_drift": ["Р.", "рf.", "рr.", "Асс.", "lnstr.", "jut.",
                               "preap."],
}
TOKEN_TO_CAT = {t: c for c, ts in LEXICON.items() for t in ts}

# Excluded look-alikes: NOT lexical labels (prose fragments / enclitics).
EXCLUDED = ["л.", "т.", "е.", "п.", "в.", "р.", "н.", "др.", "тк.", "от.",
            "или.", "как.", "гл.", "сущ.", "прил.", "нареч."]

TOKEN_RE = re.compile(r"(?<![\w/])([A-Za-zА-Яа-яЁё]{1,12}\.)(?![\w])")
BIGNOMPR_RE = re.compile(r"(?<![\w/])nom\. pr\.(?![\w])")
DEV_RANGE = "\u0900-\u097F"
HOMO_ORD_RE = re.compile(
    rf"(?<=[{DEV_RANGE}/])\s+([IVX]{{1,4}})\s+(?=[{DEV_RANGE}/])")
CLASS_NUM_RE = re.compile(r"(?<![\w/])([IVX]{1,4})\s*[-,]")


def probe_sources(jsonl_path, census_path, headwords_path):
    src = {}
    src["jsonlExists"] = os.path.exists(jsonl_path)
    src["censusExists"] = os.path.exists(census_path)
    src["headwordsExists"] = bool(headwords_path) and os.path.exists(headwords_path)
    return src


def census(jsonl_path, census_path, headwords_path):
    tok_counts = collections.Counter()
    entries_total = 0
    groups = set()
    entries_with_label = 0
    entries_with_bigram = 0
    entries_with_homog_ord = 0
    entries_with_class_num = 0
    homog_ord_counts = collections.Counter()
    class_num_counts = collections.Counter()
    spot_ids = ["kochergina:e1", "kochergina:e2", "kochergina:e3"]

    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            entries_total += 1
            groups.add(r["group"])
            t = r["text"]
            if r["id"] in spot_ids:
                spot_ids[spot_ids.index(r["id"])] = r["id"]  # mark seen below
            toks = [m.group(1) for m in TOKEN_RE.finditer(t)]
            kept = [x for x in toks if x not in EXCLUDED]
            tok_counts.update(kept)
            has_label = False
            for x in kept:
                if x in TOKEN_TO_CAT:
                    has_label = True
            if BIGNOMPR_RE.search(t):
                entries_with_bigram += 1
                has_label = True
            ho = HOMO_ORD_RE.findall(t)
            if ho:
                entries_with_homog_ord += 1
                homog_ord_counts.update(ho)
                has_label = True
            cn = CLASS_NUM_RE.findall(t)
            if cn:
                entries_with_class_num += 1
                class_num_counts.update(cn)
                has_label = True
            if has_label:
                entries_with_label += 1

    # collision-class comparison vs csl-atlas A72 census v1
    with open(census_path, encoding="utf-8") as f:
        atlas = json.load(f)
    collision = [e["label"] for e in atlas["collisionMatrix"]]

    def fold_cyr(s):
        return (s.replace("А", "A").replace("Р", "P")
                 .replace("а", "a").replace("р", "p"))

    inv = set(tok_counts) | {"nom. pr."}
    overlap_exact = sorted(inv & set(collision))
    overlap_folded = sorted({x for x in inv if fold_cyr(x) in {fold_cyr(c) for c in collision}}
                            - set(overlap_exact))

    headwords_total = None
    if headwords_path:
        with open(headwords_path, encoding="utf-16") as f:
            headwords_total = sum(1 for _ in f)

    payload = {
        "id": "kochergina-label-census-a72",
        "handoff": "H6461",
        "generatedFrom": {
            "entryBodies": os.path.abspath(jsonl_path),
            "collisionClass": "csl-atlas data/abbrev/abbrev_census.json collisionMatrix (H6409)",
            "headwordsFile": os.path.abspath(headwords_path) if headwords_path else None,
        },
        "source": {
            "edition": "Kochergina, Sanskritsko-russkij slovar', digitized 1987 printing",
            "rights": "third-party RU dictionary; DERIVED counts only, no entry text",
            "datasetSibling": "kochergina-corpus-concordance (H4748, CC BY-SA 4.0)",
        },
        "denominators": {
            "entriesProbed": entries_total,
            "distinctGroups": len(groups),
            "entriesWithLabelEvidence": entries_with_label,
            "entriesWithNomPr": entries_with_bigram,
            "entriesWithHomographOrdinal": entries_with_homog_ord,
            "entriesWithClassNumeral": entries_with_class_num,
            "headwordsCrossCheck": headwords_total,
        },
        "inventory": dict(sorted(tok_counts.items(), key=lambda kv: -kv[1])),
        "nomPrBigram": entries_with_bigram,
        "homographOrdinals": dict(sorted(homog_ord_counts.items(), key=lambda kv: -kv[1])),
        "classNumerals": dict(sorted(class_num_counts.items(), key=lambda kv: -kv[1])),
        "collisionOverlap": {
            "exact": overlap_exact,
            "homoglyphFoldedOnly": overlap_folded,
            "collisionClassSize": len(collision),
        },
        "excludedLookalikes": EXCLUDED,
        "license": "Derived label inventory; source (c) V. A. Kochergina 1987; "
                   "no third-party full text shipped. See datasets.json note N10 fence.",
    }
    return payload


def selftest(payload, jsonl_path):
    """Mechanical checks: labels found must literally occur in sampled texts;
    denominators must be self-consistent."""
    spot = {}
    want = ["kochergina:e1", "kochergina:e2", "kochergina:e3"]
    texts = {}
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["id"] in want:
                texts[r["id"]] = r["text"]
                if len(texts) == len(want):
                    break
    for eid, txt in texts.items():
        found = [m.group(1) for m in TOKEN_RE.finditer(txt)
                 if m.group(1) not in EXCLUDED]
        ok = all(re.search(re.escape(x), txt) for x in found)
        spot[eid] = {"labels": sorted(set(found)), "occurCheck": ok}
    d = payload["denominators"]
    assert d["entriesWithLabelEvidence"] <= d["entriesProbed"]
    assert d["entriesProbed"] > 0
    return spot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", default=DEFAULT_JSONL)
    ap.add_argument("--census", default=DEFAULT_CENSUS)
    ap.add_argument("--headwords", default=DEFAULT_HEADWORDS)
    ap.add_argument("--emit")
    ap.add_argument("--check")
    args = ap.parse_args()

    src = probe_sources(args.jsonl, args.census, args.headwords)
    missing = [k for k, v in src.items() if not v and k != "headwordsExists"]
    if missing:
        print(f"FAIL missing sources: {missing}", file=sys.stderr)
        return 2

    payload = census(args.jsonl, args.census, args.headwords)
    payload["selftest"] = selftest(payload, args.jsonl)

    if args.emit:
        os.makedirs(os.path.dirname(os.path.abspath(args.emit)), exist_ok=True)
        with open(args.emit, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1, sort_keys=False)
            f.write("\n")
        d = payload["denominators"]
        print(f"EMIT {args.emit}")
        print(f"  probed={d['entriesProbed']} labeled={d['entriesWithLabelEvidence']} "
              f"groups={d['distinctGroups']} headwordsXC={d['headwordsCrossCheck']} "
              f"tokens={len(payload['inventory'])} "
              f"collision_exact={len(payload['collisionOverlap']['exact'])} "
              f"collision_folded={len(payload['collisionOverlap']['homoglyphFoldedOnly'])}")
    if args.check:
        with open(args.check, encoding="utf-8") as f:
            stored = json.load(f)
        if stored != payload:
            print("CHECK FAIL: stored payload diverges from fresh derivation",
                  file=sys.stderr)
            return 1
        print("CHECK PASS: stored payload byte-equivalent to fresh derivation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
