#!/usr/bin/env python
r"""Step 1 of the kosha sense-frequency layer (H1453 / PLAN_KOSHA_SENSE_FREQUENCY_2026H2.md).

Recover the DCS **WordSem synset -> gloss decode inventory** that the stub
`dcs_full.sqlite` lacked (SL FINDINGS §78: `token.m_wordsem` carries 531,747
bare numeric synset IDs with NO local decode table). The decode ships in the DCS
CoNLL-U *distribution* — `conllu/lookup/word-senses.csv` — which the sqlite ingest
dropped; this script reunites it with the corpus attestation.

Decode source (per synset id):
  conllu/lookup/word-senses.csv (TAB-separated despite the .csv name):
    col0 id · col1 word(concept) · col2 gloss · col3 wordnet21id
    · col4 supersenseId · col5 supersenseName
  Fallback for corpus synsets absent from word-senses.csv: the most-frequent
  member lemma's DCS `lemma.meanings` gloss (decode_src=lemma-fallback); if no
  member lemma carries a gloss either, decode_src=undecodable (listed, not hidden).

Attestation source (which Sanskrit lemmas realise each synset, and how often):
  VisualDCS/src/DCS-data-2026/dcs_full.sqlite — the CANONICAL CoNLL-U ingest
  (import_dcs_conllu.py; kosha manifest dcs-full-sqlite). REUSE, not a re-parse:
  the manifest warns 5 repos historically re-parsed the 15,901 CoNLL-U files; the
  sqlite `token.m_wordsem`+`lemma_id` columns ARE that parse, losslessly, and carry
  the identical 531,747 WordSem tokens (cross-checked vs annotation_layers_by_text.csv).

Layer-3 semantic domain (best-effort): WordNet lexicographer supersense
  (wordnetSupersenseName, 26 categories: plant/animal/artifact/person/act/...),
  native to the same synset id-space. Only ~14% of corpus synsets carry a DIRECT
  supersense, so we PROPAGATE it down the WordNet hypernym tree using
  conllu/lookup/sembank-relations.csv (`parent<TAB>child<TAB>"~"` hyponym edges):
  a synset with no direct supersense inherits the nearest supersensed ancestor's.
  LOG (autonomy contract): the PLAN named Layer-3 as "SIL semdom via the
  semdom-amarakosha xwalk (A58)", but that crosswalk is keyed by Amarakosha eid /
  Princeton-WordNet, NOT the DCS Sanskrit-WordNet synset id-space, so it cannot join
  directly. The WN supersense IS the architecture's first-named "WN->semdom" path,
  same id-space, higher coverage — adopted for wave-1; the SIL-semdom projection is
  deferred (needs a sparse wordnet21id->semdom bridge). See ARCHITECTURE §traps.

Output: data/frequency/wordsem_inventory.tsv (one row per corpus-attested synset).

  python build_wordsem_inventory.py              # -> wordsem_inventory.tsv
  python build_wordsem_inventory.py --dcs PATH --lookup DIR
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
# VisualDCS is a sibling of the kosha checkout root (../../.. from data/frequency/).
_DCS_DIR = os.path.normpath(os.path.join(
    HERE, '..', '..', '..', 'VisualDCS', 'src', 'DCS-data-2026'))
DEFAULT_DCS = os.path.join(_DCS_DIR, 'dcs_full.sqlite')
DEFAULT_LOOKUP = os.path.join(_DCS_DIR, 'conllu', 'lookup')
OUT_TSV = os.path.join(HERE, 'wordsem_inventory.tsv')

MEMBER_CAP = 24  # cap the displayed member-lemma list; n_member_lemmas keeps the true count.

COLUMNS = ['synset_id', 'concept', 'gloss', 'wordnet21id', 'supersense',
           'supersense_src', 'n_member_lemmas', 'n_tokens', 'member_lemmas_slp1',
           'decode_src']

try:
    sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'sanskrit-util', 'py'))
    from sanskrit_util import to_slp1 as _su_to_slp1  # noqa: E402
    _HAVE_SU = True
except Exception:
    _HAVE_SU = False

from indic_transliteration import sanscript  # noqa: E402

_WS = re.compile(r'\s+')


def clean(text):
    """Collapse embedded newlines/tabs/runs so every field is one tab-safe line —
    downstream consumers split on \\t and read one physical row per record."""
    return _WS.sub(' ', (text or '').replace('"', "'")).strip()


def iast_to_slp1(iast):
    """DCS lemma (IAST) -> SLP1 join key (kosha lemmas.slp1 space). Prefer the
    canonical sanskrit-util transcoder; fall back to indic_transliteration."""
    s = (iast or '').strip()
    if not s:
        return ''
    if _HAVE_SU:
        try:
            return _su_to_slp1(s)
        except Exception:
            pass
    return sanscript.transliterate(s, sanscript.IAST, sanscript.SLP1)


def load_word_senses(lookup_dir):
    """word-senses.csv -> {synset_id: (concept, gloss, wn21id, supersense)}.
    Header names 5 cols but rows carry 6 tab fields (the gloss column is unnamed);
    parse positionally."""
    path = os.path.join(lookup_dir, 'word-senses.csv')
    ws = {}
    with open(path, encoding='utf-8', newline='') as f:
        rdr = csv.reader(f, delimiter='\t')
        next(rdr, None)  # header
        for row in rdr:
            if len(row) < 6:
                continue
            sid, word, gloss, wn21, _ssid, ssname = row[0], row[1], row[2], row[3], row[4], row[5]
            ss = '' if ssname in ('', '_') else ssname.strip()
            wn21 = '' if wn21 in ('', '_') else wn21.strip()
            ws[sid] = (clean(word), clean(gloss), wn21, ss)
    return ws


def load_hypernyms(lookup_dir):
    """sembank-relations.csv rows `parent<TAB>child<TAB>"~"` are WordNet hyponym
    pointers (parent has-hyponym child). Return {child: [parent, ...]} so we can
    walk UP the hypernymy chain."""
    path = os.path.join(lookup_dir, 'sembank-relations.csv')
    up = collections.defaultdict(list)
    if not os.path.exists(path):
        return up
    with open(path, encoding='utf-8', newline='') as f:
        for row in csv.reader(f, delimiter='\t'):
            if len(row) >= 3 and row[2].strip('"') == '~':
                parent, child = row[0], row[1]
                up[child].append(parent)
    return up


def propagate_supersense(synset_id, direct, up, memo, _depth=0, _seen=None):
    """Nearest-ancestor supersense for a synset lacking a direct one. BFS up the
    hypernym DAG; deterministic (nearest wins; ties -> most common -> smallest id).
    Depth-capped + cycle-guarded."""
    d = direct.get(synset_id)
    if d:
        return d, 'direct'
    if synset_id in memo:
        return memo[synset_id]
    result = ('', 'none')
    frontier = list(up.get(synset_id, []))
    seen = {synset_id}
    depth = 0
    while frontier and depth < 20:
        depth += 1
        hits = [direct[p] for p in frontier if direct.get(p)]
        if hits:
            best = collections.Counter(hits).most_common()
            top = max(c for _, c in best)
            winner = sorted(ss for ss, c in best if c == top)[0]
            result = (winner, 'propagated')
            break
        nxt = []
        for p in frontier:
            if p in seen:
                continue
            seen.add(p)
            nxt.extend(up.get(p, []))
        frontier = nxt
    memo[synset_id] = result
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dcs', default=DEFAULT_DCS)
    ap.add_argument('--lookup', default=DEFAULT_LOOKUP)
    ap.add_argument('--out', default=OUT_TSV)
    args = ap.parse_args()

    for p, what in ((args.dcs, 'dcs_full.sqlite'),
                    (os.path.join(args.lookup, 'word-senses.csv'), 'word-senses.csv')):
        if not os.path.exists(p):
            sys.exit(f"MISSING {what}: {p}\n"
                     "Need the VisualDCS DCS-data-2026 checkout (dcs-full-sqlite asset "
                     "+ CoNLL-U lookup/ folder). See kosha manifest dcs-full-sqlite.")

    print(f"decode:      {os.path.join(args.lookup, 'word-senses.csv')}")
    print(f"attestation: {args.dcs}\n")

    ws = load_word_senses(args.lookup)
    print(f"word-senses.csv decode ids: {len(ws):,}")
    direct_ss = {sid: v[3] for sid, v in ws.items() if v[3]}
    up = load_hypernyms(args.lookup)
    print(f"hypernym edges (child->parent nodes): {len(up):,}; "
          f"synsets with a DIRECT supersense: {len(direct_ss):,}")

    con = sqlite3.connect(args.dcs)
    con.row_factory = sqlite3.Row

    # Corpus attestation: per synset, member lemma_ids + token count.
    #   token.m_wordsem (synset) x token.lemma_id ; lemma table for IAST + meanings.
    syn_tokens = collections.Counter()
    syn_lemmas = collections.defaultdict(collections.Counter)  # synset -> {lemma_id: count}
    for r in con.execute(
            "SELECT m_wordsem AS s, lemma_id AS lid, COUNT(*) AS c "
            "FROM token WHERE m_wordsem IS NOT NULL AND m_wordsem != '' "
            "GROUP BY m_wordsem, lemma_id"):
        s, lid, c = r['s'], r['lid'], r['c']
        syn_tokens[s] += c
        if lid is not None:
            syn_lemmas[s][lid] += c
    print(f"corpus distinct synsets: {len(syn_tokens):,}; "
          f"total WordSem tokens: {sum(syn_tokens.values()):,}")

    # lemma_id -> (IAST lemma, meanings) for the member lemmas we touch.
    lemma_meta = {}
    needed = {lid for m in syn_lemmas.values() for lid in m}
    cur = con.execute("SELECT lemma_id, lemma, meanings FROM lemma")
    for r in cur:
        if r['lemma_id'] in needed:
            lemma_meta[r['lemma_id']] = (r['lemma'], r['meanings'] or '')

    memo = {}
    rows = []
    n_direct = n_fallback = n_undecodable = 0
    n_ss_direct = n_ss_prop = 0
    for sid, ntok in syn_tokens.items():
        members = syn_lemmas[sid]  # {lemma_id: count}
        # member SLP1 lemmas, most-frequent first, deduped preserving order
        ordered_lids = [lid for lid, _ in members.most_common()]
        seen, member_slp1 = set(), []
        for lid in ordered_lids:
            iast = lemma_meta.get(lid, ('', ''))[0]
            slp1 = iast_to_slp1(iast)
            if slp1 and slp1 not in seen:
                seen.add(slp1)
                member_slp1.append(slp1)

        # decode
        if sid in ws:
            concept, gloss, wn21, _ss = ws[sid]
            decode_src = 'word-senses'
            n_direct += 1
        else:
            # fallback: most-frequent member lemma's DCS meanings
            concept, gloss, wn21 = '', '', ''
            for lid in ordered_lids:
                iast, meanings = lemma_meta.get(lid, ('', ''))
                if meanings.strip():
                    concept = clean(iast)
                    gloss = clean(meanings.split(';')[0])  # first sub-gloss
                    break
            if gloss:
                decode_src = 'lemma-fallback'
                n_fallback += 1
            else:
                decode_src = 'undecodable'
                n_undecodable += 1

        supersense, ss_src = propagate_supersense(sid, direct_ss, up, memo)
        if ss_src == 'direct':
            n_ss_direct += 1
        elif ss_src == 'propagated':
            n_ss_prop += 1

        rows.append({
            'synset_id': sid,
            'concept': concept,
            'gloss': gloss,
            'wordnet21id': wn21,
            'supersense': supersense,
            'supersense_src': ss_src,
            'n_member_lemmas': len(member_slp1),
            'n_tokens': ntok,
            'member_lemmas_slp1': '|'.join(member_slp1[:MEMBER_CAP]),
            'decode_src': decode_src,
        })

    rows.sort(key=lambda r: (-r['n_tokens'], r['synset_id']))
    with open(args.out, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

    n = len(rows)
    decoded = n_direct + n_fallback
    print("\n=== wordsem_inventory.tsv ===")
    print(f"synsets (rows):            {n:,}")
    print(f"  decoded (word-senses):   {n_direct:,} ({n_direct/n:.1%})")
    print(f"  decoded (lemma-fallback):{n_fallback:,} ({n_fallback/n:.1%})")
    print(f"  undecodable:             {n_undecodable:,} ({n_undecodable/n:.1%})")
    print(f"  TOTAL decoded:           {decoded:,} ({decoded/n:.1%})")
    print(f"supersense (Layer 3):      direct {n_ss_direct:,} + propagated {n_ss_prop:,} "
          f"= {n_ss_direct + n_ss_prop:,} ({(n_ss_direct + n_ss_prop)/n:.1%})")
    empty_on_decoded = sum(1 for r in rows if r['decode_src'] != 'undecodable' and not r['gloss'])
    print(f"AC#1 empty glosses on decoded rows: {empty_on_decoded} (must be 0)")
    print(f"AC#1 baseline check: sqlite shipped 0 decoded; recovered {decoded:,} > 0  -> PASS")
    print(f"-> {args.out}")
    return 0 if empty_on_decoded == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
