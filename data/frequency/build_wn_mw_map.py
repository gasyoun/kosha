#!/usr/bin/env python
r"""Step 2 of the kosha sense-frequency layer (H1453).

Map every corpus-attested (WordSem synset, member-lemma) pair onto the best-matching
**MW numbered sense** of that lemma, so Layer 2 (MW) of the frequency layer can count
per MW sense. Output: data/frequency/wn_to_mw_map.tsv.

There is NO usable direct MW->Sanskrit-WordNet bridge in the DCS WordSem id-space (the
semdom-amarakosha bridge, A58, is keyed by Amarakosha eid / Princeton WordNet — a
different id-space), so per IMPLEMENTATION Step 2 we take the "bridge is silent ->
lemma+gloss-overlap scoring" path directly. Matching is English-gloss vs English-gloss:
the synset's WordNet gloss (wordsem_inventory.tsv) against each MW numbered sense's gloss
text (kosha.db `senses` span sliced out of `entries.body`, markup stripped).

  match_type   how chosen
  ----------   -------------------------------------------------------------------
  exact        the synset's concept word occurs in the MW sense text, OR the
               content-word Jaccard >= EXACT_JAC  (a confident single-sense hit)
  overlap      >=1 shared content word but below the exact bar (a plausible projection)
  unresolved   no shared content word, or the lemma has no MW entry at all

Every attested pair gets a row and a match_type; the unresolved fraction is reported,
never hidden (AC#2). FENCE: reads kosha.db, never writes it — the map is standalone.

  python build_wn_mw_map.py                       # needs wordsem_inventory.tsv (Step 1)
  python build_wn_mw_map.py --kosha-db PATH --dcs PATH
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
_DCS_DIR = os.path.normpath(os.path.join(
    HERE, '..', '..', '..', 'VisualDCS', 'src', 'DCS-data-2026'))
DEFAULT_DCS = os.path.join(_DCS_DIR, 'dcs_full.sqlite')
INVENTORY = os.path.join(HERE, 'wordsem_inventory.tsv')
OUT_TSV = os.path.join(HERE, 'wn_to_mw_map.tsv')

EXACT_JAC = 0.34   # content-word Jaccard at/above which a non-concept match is "exact"

COLUMNS = ['synset_id', 'lemma_slp1', 'mw_entry_id', 'mw_sense_n', 'mw_sense_ord',
           'mw_sense_gloss', 'match_type', 'score', 'n_tokens']

# sanskrit-util is the canonical transcoder; indic_transliteration is the fallback.
try:
    sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'sanskrit-util', 'py'))
    from sanskrit_util import to_slp1 as _su_to_slp1  # noqa: E402
    _HAVE_SU = True
except Exception:
    _HAVE_SU = False
from indic_transliteration import sanscript  # noqa: E402

_TAG = re.compile(r'<[^>]+>')
_WORD = re.compile(r'[a-z]+')

# English function words + MW register abbreviations + gloss boilerplate: stripped so
# overlap scoring keys on real lexical content, not grammatical scaffolding.
STOP = frozenset("""
the and for with that this are was has had have from not but any all one out own its his her
their our your they them who whom whose which what when where while into onto unto upon than then
also esp especially name called cf ibid ibidem viz etc opp opposite comp compound gen genitive
instr instrumental acc accusative loc locative dat dative abl ablative nom nominative voc sing plur
dual mfn mnf adj adv ind indecl masc fem neut prep conj part particle verb noun root see col cols
following above below hence used usually often sometimes according applied being kind sort way
manner form thing person more most very much many few made make making made another other others
such same each every either neither some none like unlike part parts whole
""".split())


def iast_to_slp1(iast):
    s = (iast or '').strip()
    if not s:
        return ''
    if _HAVE_SU:
        try:
            return _su_to_slp1(s)
        except Exception:
            pass
    return sanscript.transliterate(s, sanscript.IAST, sanscript.SLP1)


def content_words(text):
    return {w for w in _WORD.findall((text or '').lower()) if len(w) >= 3 and w not in STOP}


def strip_markup(t):
    return re.sub(r'\s+', ' ', _TAG.sub(' ', t or '')).replace('&amp;', '&').strip()


def load_inventory():
    inv = {}
    with open(INVENTORY, encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            inv[r['synset_id']] = (r['concept'], r['gloss'])
    return inv


def build_mw_index(kosha_db, slp1_set):
    """{slp1: [(mw_ord, entry_id, sense_n, gloss_short, content_words), ...]} for the
    attested lemmas only — ordered as MW prints them (entry L asc, then sense_n)."""
    con = sqlite3.connect(kosha_db)
    idx = {}
    # Pull all mw entries for the needed slp1 keys, with their senses, in one pass.
    qmarks = None
    slp1_list = list(slp1_set)
    for i in range(0, len(slp1_list), 900):
        chunk = slp1_list[i:i + 900]
        qmarks = ','.join('?' * len(chunk))
        rows = con.execute(
            f"SELECT e.slp1_key, e.id, CAST(e.L AS INTEGER) AS Ln, e.body, "
            f"       s.sense_n, s.span_start, s.span_end "
            f"FROM entries e JOIN senses s ON s.entry_id = e.id "
            f"WHERE e.dict='mw' AND e.slp1_key IN ({qmarks}) "
            f"ORDER BY e.slp1_key, Ln, s.sense_n", chunk).fetchall()
        for slp1, eid, Ln, body, sn, a, b in rows:
            gloss = strip_markup(body[a:b])
            idx.setdefault(slp1, []).append([eid, sn, gloss, content_words(gloss)])
    con.close()
    # assign lemma-level ordinal after ordering
    out = {}
    for slp1, senses in idx.items():
        out[slp1] = [(o + 1, eid, sn, gloss, cw)
                     for o, (eid, sn, gloss, cw) in enumerate(senses)]
    return out


def score_pair(concept, syn_cw, senses):
    """Best MW sense for one synset gloss. Returns (mw_ord, eid, sn, gloss, match_type, score)."""
    c = (concept or '').lower()
    best = None  # (rank_key, ord, eid, sn, gloss, mtype, score)
    for o, eid, sn, gloss, cw in senses:
        inter = syn_cw & cw
        union = syn_cw | cw
        jac = len(inter) / len(union) if union else 0.0
        concept_hit = len(c) >= 3 and c in cw
        if concept_hit:
            mtype, key = 'exact', (2, jac)
        elif jac >= EXACT_JAC:
            mtype, key = 'exact', (2, jac)
        elif inter:
            mtype, key = 'overlap', (1, jac)
        else:
            mtype, key = 'unresolved', (0, 0.0)
        cand = (key, o, eid, sn, gloss, mtype, round(jac, 3))
        if best is None or cand[0] > best[0]:
            best = cand
    if best is None:
        return (0, None, None, '', 'unresolved', 0.0)
    _key, o, eid, sn, gloss, mtype, score = best
    return (o, eid, sn, gloss, mtype, score)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dcs', default=DEFAULT_DCS)
    ap.add_argument('--kosha-db', default=None,
                    help="kosha.db path (default: sibling main checkout, gitignored)")
    ap.add_argument('--out', default=OUT_TSV)
    args = ap.parse_args()

    kosha_db = args.kosha_db or _resolve_kosha_db()
    for p, what in ((INVENTORY, 'wordsem_inventory.tsv (run Step 1)'),
                    (args.dcs, 'dcs_full.sqlite'), (kosha_db, 'kosha.db')):
        if not p or not os.path.exists(p):
            sys.exit(f"MISSING {what}: {p}")
    print(f"inventory: {INVENTORY}\nkosha.db:  {kosha_db}\ndcs:       {args.dcs}\n")

    inv = load_inventory()

    # Attested (synset, lemma_slp1) pairs + token counts, from the canonical ingest.
    dcs = sqlite3.connect(args.dcs)
    lemma_iast = {r[0]: r[1] for r in dcs.execute("SELECT lemma_id, lemma FROM lemma")}
    pair_tokens = collections.Counter()
    for s, lid, c in dcs.execute(
            "SELECT m_wordsem, lemma_id, COUNT(*) FROM token "
            "WHERE m_wordsem IS NOT NULL AND m_wordsem!='' AND lemma_id IS NOT NULL "
            "GROUP BY m_wordsem, lemma_id"):
        slp1 = iast_to_slp1(lemma_iast.get(lid, ''))
        if slp1:
            pair_tokens[(s, slp1)] += c
    dcs.close()
    print(f"attested (synset, lemma) pairs: {len(pair_tokens):,}")

    slp1_set = {slp1 for _s, slp1 in pair_tokens}
    mw_idx = build_mw_index(kosha_db, slp1_set)
    lemmas_with_mw = sum(1 for s in slp1_set if s in mw_idx)
    print(f"attested lemmas: {len(slp1_set):,}; with >=1 MW sense: {lemmas_with_mw:,} "
          f"({lemmas_with_mw/len(slp1_set):.1%})")

    rows = []
    mt = collections.Counter()
    for (syn, slp1), ntok in pair_tokens.items():
        concept, gloss = inv.get(syn, ('', ''))
        syn_cw = content_words(gloss) or content_words(concept)
        senses = mw_idx.get(slp1)
        if not senses:
            o, eid, sn, sgloss, mtype, score = 0, None, None, '', 'unresolved', 0.0
        else:
            o, eid, sn, sgloss, mtype, score = score_pair(concept, syn_cw, senses)
        mt[mtype] += 1
        rows.append({
            'synset_id': syn, 'lemma_slp1': slp1,
            'mw_entry_id': eid if eid is not None else '',
            'mw_sense_n': sn if sn is not None else '',
            'mw_sense_ord': o, 'mw_sense_gloss': sgloss[:120],
            'match_type': mtype, 'score': score, 'n_tokens': ntok,
        })

    rows.sort(key=lambda r: (r['lemma_slp1'], r['synset_id']))
    with open(args.out, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

    n = len(rows)
    print("\n=== wn_to_mw_map.tsv ===")
    for k in ('exact', 'overlap', 'unresolved'):
        print(f"  {k:11s}: {mt[k]:>7,} ({mt[k]/n:.1%})")
    resolved = mt['exact'] + mt['overlap']
    tok_resolved = sum(r['n_tokens'] for r in rows if r['match_type'] != 'unresolved')
    tok_all = sum(r['n_tokens'] for r in rows)
    print(f"  resolved (pairs):  {resolved:,} ({resolved/n:.1%})")
    print(f"  resolved (tokens): {tok_resolved:,} ({tok_resolved/tok_all:.1%})")
    print(f"-> {args.out}")
    return 0


def _resolve_kosha_db():
    # worktree-local (rare), else the sibling main checkout (gitignored, only there).
    cand = [os.path.join(HERE, '..', '..', 'data', 'db', 'kosha.db'),
            os.path.normpath(os.path.join(HERE, '..', '..', '..', 'kosha', 'data', 'db', 'kosha.db'))]
    for p in cand:
        if os.path.exists(p):
            return os.path.normpath(p)
    return cand[-1]


if __name__ == '__main__':
    sys.exit(main())
