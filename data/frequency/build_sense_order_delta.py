#!/usr/bin/env python
r"""Step 4 of the kosha sense-frequency layer (H1453).

The decision-#3 finding report: where MW's printed **sense-1 does not express the
corpus-dominant sense** of a headword. Surfaced as a **DCS-derivation finding**, NOT an
MW defect — MW's canonical sense order is trusted and left untouched (the fence: this
script reads kosha.db + sense_frequency.tsv and writes only markdown). Feeds M01 Ch6
"Senses: Inheritance and Order".

LOG (autonomy contract — refinement of IMPLEMENTATION Step 4). Step 4 literally says
"compare the frequency-dominant MW sense (rank-1 in the mw layer) against MW sense-1".
Taken literally that OVER-counts divergence: the gloss-overlap MW projection
(wn_to_mw_map) can assign a synset to a *later* MW sense that merely shares a word — e.g.
`agni`'s "fire" synset lands on the MW sense containing "fire-altar", not MW sense-1
"fire", producing a false divergence when MW in fact leads with the dominant sense. So
the DIVERGE/AGREE verdict is taken on the **native WN layer** (lossless): the
corpus-dominant WN synset's concept+gloss vs MW sense-1's gloss, by content-word overlap.
This removes the projection artifact (agni -> AGREE) while keeping the real signal
(rasa "mercury" vs MW sense-1 "juice" -> DIVERGE). The MW sense the dominant synset maps
to is still shown as supplementary context.

Output: data/frequency/dcs_mw_sense_order_delta.md

  python build_sense_order_delta.py         # needs sense_frequency.tsv (Step 3) + kosha.db
"""
import argparse
import collections
import csv
import os
import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
SENSE_FREQ = os.path.join(HERE, 'sense_frequency.tsv')
INVENTORY = os.path.join(HERE, 'wordsem_inventory.tsv')
WN_MW_MAP = os.path.join(HERE, 'wn_to_mw_map.tsv')
OUT_MD = os.path.join(HERE, 'dcs_mw_sense_order_delta.md')
TODAY = '22-07-2026'
CSN = 'Opus 4.8 (`claude-opus-4-8`)'
MIN_TOKENS = 30

_TAG = re.compile(r'<[^>]+>')
_WORD = re.compile(r'[a-z]+')
STOP = frozenset("""
the and for with that this are was has had have from not but any all one out own its his her
their our your they them who whom whose which what when where while into onto unto upon than then
also esp especially name called cf ibid viz etc opp comp gen instr acc loc dat abl nom voc sing
plur dual mfn adj adv ind indecl masc fem neut prep conj part particle verb noun root see col cols
following above below hence used usually often sometimes according applied being kind sort way
manner form thing person more most very much many few made make another other such same each every
""".split())


def content_words(t):
    return {w for w in _WORD.findall((t or '').lower()) if len(w) >= 3 and w not in STOP}


def strip_markup(t):
    return re.sub(r'\s+', ' ', _TAG.sub(' ', t or '')).replace('&amp;', '&').strip()


def _resolve_kosha_db():
    cand = [os.path.join(HERE, '..', '..', 'data', 'db', 'kosha.db'),
            os.path.normpath(os.path.join(HERE, '..', '..', '..', 'kosha', 'data', 'db', 'kosha.db'))]
    for p in cand:
        if os.path.exists(p):
            return os.path.normpath(p)
    return cand[-1]


def mw_sense1(kosha_db, lemmas):
    con = sqlite3.connect(kosha_db)
    out = {}
    lst = list(lemmas)
    for i in range(0, len(lst), 900):
        chunk = lst[i:i + 900]
        q = ','.join('?' * len(chunk))
        for slp1, Ln, body, sn, a, b in con.execute(
                f"SELECT e.slp1_key, CAST(e.L AS INTEGER) AS Ln, e.body, s.sense_n, "
                f"s.span_start, s.span_end FROM entries e JOIN senses s ON s.entry_id=e.id "
                f"WHERE e.dict='mw' AND e.slp1_key IN ({q}) ORDER BY e.slp1_key, Ln, s.sense_n",
                chunk):
            if slp1 not in out:
                out[slp1] = strip_markup(body[a:b])
    con.close()
    return out


def load_tsv(p):
    with open(p, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--kosha-db', default=None)
    ap.add_argument('--out', default=OUT_MD)
    args = ap.parse_args()
    kosha_db = args.kosha_db or _resolve_kosha_db()
    for p in (SENSE_FREQ, INVENTORY):
        if not os.path.exists(p):
            sys.exit(f"MISSING {p} (run Steps 1&3)")

    inv = {r['synset_id']: r for r in load_tsv(INVENTORY)}
    wnmw = {(r['synset_id'], r['lemma_slp1']): r for r in load_tsv(WN_MW_MAP)} \
        if os.path.exists(WN_MW_MAP) else {}

    # WN layer, per lemma: dominant (rank-1) synset + tokens + n synsets.
    wn = collections.defaultdict(list)   # slp1 -> [(count, synset, share)]
    for r in load_tsv(SENSE_FREQ):
        if r['layer'] == 'wn':
            wn[r['lemma_slp1']].append((int(r['count_all']), r['sense_id'], float(r['lemma_share'])))

    s1 = mw_sense1(kosha_db, wn.keys())

    total = diverge = multi_total = multi_div = no_s1 = 0
    examples = []
    for lemma, senses in wn.items():
        senses.sort(key=lambda x: (-x[0], x[1]))
        dom_c, dom_syn, dom_share = senses[0]
        tokens = sum(c for c, _s, _sh in senses)
        n_syn = len(senses)
        meta = inv.get(dom_syn, {})
        dom_concept = meta.get('concept', '')
        dom_gloss = meta.get('gloss', '')
        s1g = s1.get(lemma)
        if s1g is None:
            no_s1 += 1
            continue
        total += 1
        if n_syn >= 2:
            multi_total += 1
        # robust verdict: does MW sense-1 express the dominant WN concept?
        dom_cw = content_words(dom_concept + ' ' + dom_gloss)
        s1_cw = content_words(s1g)
        concept_in_s1 = len(dom_concept) >= 3 and dom_concept.lower() in s1_cw
        agrees = concept_in_s1 or bool(dom_cw & s1_cw)
        if not agrees:
            diverge += 1
            if n_syn >= 2:
                multi_div += 1
            m = wnmw.get((dom_syn, lemma))
            mw_ord = m['mw_sense_ord'] if (m and m['match_type'] in ('exact', 'overlap')) else ''
            examples.append((lemma, s1g, dom_concept, dom_gloss, dom_share, tokens, n_syn, mw_ord))

    examples.sort(key=lambda d: (-d[5], -d[4]))
    rate = diverge / total if total else 0

    L = []
    L.append("# DCS-vs-MW sense-order delta — where MW sense-1 ≠ the corpus-dominant sense")
    L.append("")
    L.append(f"_Created: {TODAY} · Last updated: {TODAY}_")
    L.append("")
    L.append(f"_Auto-generated by `build_sense_order_delta.py` ({CSN}), H1453 wave-1._")
    L.append("")
    L.append("## What this is")
    L.append("")
    L.append(
        "For each MW headword carrying WordSem-gold attestations, this asks whether **MW's "
        "printed sense-1 expresses the corpus-dominant sense** — the rank-1 Sanskrit-WordNet "
        "synset in the native (`wn`) layer of "
        "[`sense_frequency.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/sense_frequency.tsv). "
        "A **divergence** means the corpus most often attests a meaning that MW's first sense "
        "does not carry.")
    L.append("")
    L.append(
        "The verdict is taken on the **native WN layer** (lossless gold), not the MW-projection "
        "layer: the gloss-overlap MW map can assign a synset to a *later* MW sense that merely "
        "shares a word (e.g. `agni`'s \"fire\" synset lands on a sense mentioning \"fire-altar\", "
        "though MW sense-1 already **is** \"fire\"), which would fabricate divergences. Judging on "
        "the WN synset's concept vs MW sense-1's gloss removes that artifact.")
    L.append("")
    L.append(
        "**This is a DCS-derivation finding, not an MW defect** (decision #3, "
        "[PLAN](https://github.com/gasyoun/kosha/blob/main/docs/PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md)). "
        "MW's canonical sense order is sound and left **untouched** — the frequency layer is a "
        "read-only sidecar. The divergence is data about corpus usage; it feeds M01 Ch6 \"Senses: "
        "Inheritance and Order\". No MW sense is reordered anywhere in this pipeline.")
    L.append("")
    L.append("## Numbers")
    L.append("")
    L.append("| metric | value |")
    L.append("|---|---|")
    L.append(f"| MW headwords with WordSem attestation | {total:,} |")
    L.append(f"| …where MW sense-1 does NOT express the corpus-dominant sense | {diverge:,} ({rate:.1%}) |")
    L.append(f"| headwords with ≥2 attested WN synsets | {multi_total:,} |")
    L.append(f"| …of those, MW sense-1 ≠ dominant | {multi_div:,} "
             f"({multi_div/multi_total:.1%} of multi-sense) |")
    L.append("")
    L.append("## Patterns observed")
    L.append("")
    L.append(
        "The divergence is not random noise — a recurring cause, visible directly in the examples "
        "below, is that **MW's first record for a headword is often not a semantic gloss at all**: it "
        "is a Devanāgarī-letter record (`ca` → \"the 20th letter of the alphabet\", corpus-dominant "
        "\"and\" 92%), a grammatical / Dhātupāṭha conjugation preamble (`kf`, `arTa`, `BU`), or a "
        "rare etymological sense (`vā` \"going\" vs corpus \"or\" 93%; `rāma` \"causing rest\" vs the "
        "god Rāma 97%; `sūta` \"impelled\" vs \"mercury\" 87%). The corpus-dominant meaning then sits "
        "in a *later* MW record. This is the \"inheritance and order\" signal M01 Ch6 examines: a "
        "corpus-frequency reordering of MW's records diverges systematically from MW's print order, "
        "which is organised by the 1899 lexicographer's principles (etymology, homograph typography), "
        "not by attestation frequency. It is not evidence that MW's order is wrong.")
    L.append("")
    L.append(f"## Worked examples (≥{MIN_TOKENS} attestations, ≥2 WN synsets)")
    L.append("")
    L.append("| lemma (SLP1) | MW sense-1 (printed first) | corpus-dominant sense (WN) | dom. share | tokens |")
    L.append("|---|---|---|---|---|")
    shown = 0
    for lemma, s1g, dcpt, dgl, dshare, tok, nsyn, mword in examples:
        if nsyn < 2 or tok < MIN_TOKENS:
            continue
        s1s = (s1g or '')[:66].replace('|', '\\|')
        dom = f"{dcpt} — {dgl}"[:66].replace('|', '\\|')
        mw_note = f" (→ MW #{mword})" if mword else ""
        L.append(f"| `{lemma}` | {s1s} | {dom}{mw_note} | {dshare:.0%} | {tok:,} |")
        shown += 1
        if shown >= 40:
            break
    L.append("")
    L.append("## Fence / provenance")
    L.append("")
    L.append(
        "- **MW canonical senses untouched.** Reads "
        "[`kosha.db`](https://github.com/gasyoun/kosha/blob/main/data/db/kosha.db) `senses` + "
        "`sense_frequency.tsv`; writes only this report. `git diff` on any DB/sense artifact is clean.")
    L.append(
        "- **Dominance is on WordSem gold** (219/270 texts, `provenance=attested`) — a corpus-usage "
        "signal, not an accuracy claim about disambiguation. The 51 untagged texts (incl. the 2026 "
        "Vedic wave) contribute nothing, so genres under-represented in the sense-tagged subset are "
        "under-weighted (e.g. rasaśāstra texts inflate `rasa`'s \"mercury\" dominance).")
    L.append(
        "- Verdict basis: native WN layer; the MW-sense pointer shown per row is the gloss-overlap "
        "projection [`wn_to_mw_map.tsv`](https://github.com/gasyoun/kosha/blob/main/data/frequency/wn_to_mw_map.tsv) "
        "(68.8% token coverage), for context only.")
    L.append("")
    L.append("_Dr. Mārcis Gasūns_")
    L.append("")

    with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))

    print("=== dcs_mw_sense_order_delta.md ===")
    print(f"MW headwords with attestation: {total:,}")
    print(f"MW sense-1 ≠ corpus-dominant: {diverge:,} ({rate:.1%})")
    print(f"multi-synset headwords: {multi_total:,}; divergent: {multi_div:,} "
          f"({multi_div/multi_total:.1%})")
    print(f"lemmas without an MW sense-1 gloss (skipped): {no_s1:,}")
    print(f"worked examples available: {len(examples):,} (showing ≤40)")
    print(f"-> {args.out}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
