#!/usr/bin/env python
r"""Step 3 of the kosha sense-frequency layer (H1453) — the deliverable dataset.

Per-**sense** frequency ("частотность значений") on the DCS WordSem gold, at three
cross-linked layers, as a kosha `data/frequency/` sidecar parallel to
`lemma_frequency.tsv`. Long format, one row per (lemma_slp1, layer, sense_id):

  layer=wn      native Sanskrit-WordNet synset (lossless gold; sense_id = synset_id)
  layer=mw      MW numbered sense via wn_to_mw_map.tsv (sense_id = <lemma>#<mw_ord>)
  layer=semdom  WordNet lexicographer supersense (sense_id = supersense name)

Counting is on the native synset first (Layer 1, no loss); Layers 2/3 are projections
whose coverage is measurable against it. Every token that carries a WordSem tag
contributes one count to Layer 1, and one each to Layers 2/3 where the projection
resolves. `provenance=attested` on every wave-1 row (it IS the gold — no accuracy claim);
`confidence` is null (wave-2 WSD fills it for `estimated` rows).

Inputs (all reuse):
  dcs_full.sqlite token         — attestation: (m_wordsem, lemma_id) token counts
  wordsem_inventory.tsv (Step 1)— synset -> concept/gloss/supersense
  wn_to_mw_map.tsv (Step 2)     — (synset, lemma) -> MW sense + match_type
  lemma_frequency.tsv           — the AC#3 containment denominator (per-lemma corpus count)

  python build_sense_frequency_layer.py     # -> sense_frequency.tsv + .meta.json
"""
import argparse
import collections
import csv
import json
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
_DCS_DIR = os.path.normpath(os.path.join(
    HERE, '..', '..', '..', 'VisualDCS', 'src', 'DCS-data-2026'))
DEFAULT_DCS = os.path.join(_DCS_DIR, 'dcs_full.sqlite')
INVENTORY = os.path.join(HERE, 'wordsem_inventory.tsv')
WN_MW_MAP = os.path.join(HERE, 'wn_to_mw_map.tsv')
LEMMA_FREQ = os.path.join(HERE, 'lemma_frequency.tsv')
OUT_TSV = os.path.join(HERE, 'sense_frequency.tsv')
OUT_META = os.path.join(HERE, 'sense_frequency.meta.json')

COLUMNS = ['lemma_slp1', 'layer', 'sense_id', 'sense_gloss', 'count_all',
           'sense_rank', 'lemma_share', 'n_texts', 'dispersion_dp',
           'largest_text_share', 'count_adj', 'sense_rank_adj',
           'periods', 'provenance', 'confidence']
GLOSS_CAP = 100
CSN = "claude-opus-4-8"  # provenance: model tier + exact version (H1453 executor)

try:
    sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'sanskrit-util', 'py'))
    from sanskrit_util import to_slp1 as _su_to_slp1  # noqa: E402
    _HAVE_SU = True
except Exception:
    _HAVE_SU = False
from indic_transliteration import sanscript  # noqa: E402


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


def load_tsv(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def _short(concept, gloss):
    g = f"{concept} — {gloss}" if gloss and gloss != concept else concept
    return g[:GLOSS_CAP]


def gries_dp(text_counts, text_share):
    """Gries's Deviation of Proportions (DP, 2008) for one sense over corpus texts.
    text_counts: {text_id: n} for this sense; text_share: {text_id: s_i} corpus part size.
    DP = 0.5 * Σ_all_texts |v_i − s_i|, where v_i = n_i/total (0 for absent texts).
    0 = perfectly even w.r.t. text sizes; →1 = maximally concentrated/bursty.
    (Corpus-size-relative — genre-relative stratification is wave-2. Cite Gries 2008,
    IJCL 13(4):403–437; the caveat is documented in the .meta.json.)"""
    total = sum(text_counts.values())
    if total <= 0:
        return 0.0
    present_share = 0.0
    absdiff = 0.0
    for t, n in text_counts.items():
        s_i = text_share.get(t, 0.0)
        absdiff += abs(n / total - s_i)
        present_share += s_i
    absdiff += (1.0 - present_share)  # absent texts contribute their s_i (v_i = 0)
    return 0.5 * absdiff


def _dense_rank(enriched, key):
    """{sense_id: dense_rank} over `enriched` tuples, ranked by `key` descending,
    ties share a rank (deterministic: order by (-key, sense_id))."""
    ordered = sorted(enriched, key=lambda e: (-key(e), e[0]))
    out, rank, prev, seen = {}, 0, None, 0
    for e in ordered:
        seen += 1
        k = key(e)
        if k != prev:
            rank = seen
            prev = k
        out[e[0]] = rank
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dcs', default=DEFAULT_DCS)
    ap.add_argument('--out', default=OUT_TSV)
    args = ap.parse_args()
    for p in (args.dcs, INVENTORY, WN_MW_MAP):
        if not os.path.exists(p):
            sys.exit(f"MISSING input: {p}")

    inv = {r['synset_id']: r for r in load_tsv(INVENTORY)}
    wnmw = {(r['synset_id'], r['lemma_slp1']): r for r in load_tsv(WN_MW_MAP)}

    # Attestation: (lemma_slp1, synset) -> token count (collapsing homograph lemma_ids
    # onto the SLP1 key, as kosha is SLP1-keyed; the homonym axis is WhitneyRoots' job).
    dcs = sqlite3.connect(args.dcs)
    lemma_iast = {r[0]: r[1] for r in dcs.execute("SELECT lemma_id, lemma FROM lemma")}
    pair = collections.Counter()
    # per-text counts per (lemma, synset) — for the wave-1.5 dispersion columns; plus
    # per-text WordSem totals (the corpus part sizes for the Gries-DP expected proportions).
    pair_text = collections.defaultdict(collections.Counter)  # (slp1, synset) -> {text_id: n}
    text_ws_total = collections.Counter()                     # text_id -> WordSem tokens
    for s, lid, tid, c in dcs.execute(
            "SELECT t.m_wordsem, t.lemma_id, ch.text_id, COUNT(*) "
            "FROM token t JOIN sentence se ON t.sentence_id=se.id "
            "JOIN chapter ch ON se.chapter_id=ch.chapter_id "
            "WHERE t.m_wordsem IS NOT NULL AND t.m_wordsem!='' AND t.lemma_id IS NOT NULL "
            "GROUP BY t.m_wordsem, t.lemma_id, ch.text_id"):
        slp1 = iast_to_slp1(lemma_iast.get(lid, ''))
        if slp1:
            pair[(slp1, s)] += c
            pair_text[(slp1, s)][tid] += c
            text_ws_total[tid] += c
    dcs.close()
    grand_total = sum(text_ws_total.values()) or 1
    text_share = {t: n / grand_total for t, n in text_ws_total.items()}  # s_i (corpus part size)

    # Three layer aggregations: {(lemma, layer, sense_id): [count, gloss]}
    agg = collections.defaultdict(lambda: [0, ''])
    agg_text = collections.defaultdict(collections.Counter)  # (lemma,layer,sid) -> {text: n}
    cov = collections.Counter()  # coverage counters for the meta
    for (lemma, syn), c in pair.items():
        meta = inv.get(syn, {})
        pt = pair_text[(lemma, syn)]  # per-text distribution of this (lemma, synset)
        # Layer 1 — WN synset (native gold)
        gloss1 = _short(meta.get('concept', syn), meta.get('gloss', ''))
        k1 = (lemma, 'wn', syn)
        agg[k1][0] += c
        agg[k1][1] = gloss1
        agg_text[k1].update(pt)
        cov['wn_tokens'] += c
        # Layer 2 — MW numbered sense (projection via wn_to_mw_map)
        m = wnmw.get((syn, lemma))
        if m and m['match_type'] in ('exact', 'overlap') and m['mw_sense_ord'] not in ('', '0'):
            sid = f"{lemma}#{m['mw_sense_ord']}"
            k2 = (lemma, 'mw', sid)
            agg[k2][0] += c
            agg[k2][1] = (m['mw_sense_gloss'] or '')[:GLOSS_CAP]
            agg_text[k2].update(pt)
            cov['mw_tokens'] += c
            cov['mw_' + m['match_type']] += c
        else:
            cov['mw_unresolved_tokens'] += c
        # Layer 3 — WordNet supersense (best-effort semantic domain)
        ss = meta.get('supersense', '')
        if ss:
            k3 = (lemma, 'semdom', ss)
            agg[k3][0] += c
            agg[k3][1] = ss
            agg_text[k3].update(pt)
            cov['semdom_tokens'] += c
        else:
            cov['semdom_unresolved_tokens'] += c

    # Rank + share + dispersion within (lemma, layer). Each sense carries its per-text
    # distribution (agg_text) → n_texts, Gries DP, largest_text_share, and the
    # dispersion-adjusted count count_adj = count_all × (1 − DP) (a bursty, genre-concentrated
    # sense is discounted). A second dense rank (sense_rank_adj) orders by count_adj.
    by_ll = collections.defaultdict(list)  # (lemma, layer) -> [(sid, count, gloss, tcounts)]
    for (lemma, layer, sid), (c, gloss) in agg.items():
        by_ll[(lemma, layer)].append((sid, c, gloss, agg_text[(lemma, layer, sid)]))
    rows = []
    for (lemma, layer), senses in by_ll.items():
        total = sum(c for _, c, _, _ in senses)
        # precompute per-sense dispersion + adjusted count
        enriched = []
        for sid, c, gloss, tc in senses:
            dp = gries_dp(tc, text_share)
            n_texts = len(tc)
            largest = (max(tc.values()) / c) if c and tc else 0.0
            c_adj = c * (1.0 - dp)
            enriched.append((sid, c, gloss, n_texts, dp, largest, c_adj))
        # dense rank by raw count desc (sense_rank) and by adjusted count desc (sense_rank_adj)
        raw_rank = _dense_rank(enriched, key=lambda e: e[1])
        adj_rank = _dense_rank(enriched, key=lambda e: e[6])
        for e in enriched:
            sid, c, gloss, n_texts, dp, largest, c_adj = e
            rows.append({
                'lemma_slp1': lemma, 'layer': layer, 'sense_id': sid,
                'sense_gloss': gloss, 'count_all': c, 'sense_rank': raw_rank[sid],
                'lemma_share': round(c / total, 4) if total else 0.0,
                'n_texts': n_texts, 'dispersion_dp': round(dp, 4),
                'largest_text_share': round(largest, 4), 'count_adj': round(c_adj, 2),
                'sense_rank_adj': adj_rank[sid],
                'periods': '', 'provenance': 'attested', 'confidence': '',
            })
    rows.sort(key=lambda r: (r['lemma_slp1'], r['layer'], r['sense_rank'], r['sense_id']))

    with open(args.out, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

    # ---- AC#3 containment: per-lemma Σ(wn count) ≤ lemma_frequency.count_all ----
    lf = {}
    if os.path.exists(LEMMA_FREQ):
        for r in load_tsv(LEMMA_FREQ):
            try:
                lf[r['lemma_slp1']] = int(r['count_all']) if r['count_all'] else None
            except ValueError:
                lf[r['lemma_slp1']] = None
    wn_sum = collections.Counter()
    for (lemma, layer, _sid), (c, _g) in agg.items():
        if layer == 'wn':
            wn_sum[lemma] += c
    checked = violations = no_lf = 0
    worst = []
    for lemma, wsum in wn_sum.items():
        lc = lf.get(lemma)
        if lc is None:
            no_lf += 1
            continue
        checked += 1
        if wsum > lc:
            violations += 1
            worst.append((lemma, wsum, lc, wsum - lc))
    worst.sort(key=lambda x: -x[3])

    n_layers = {ly: sum(1 for r in rows if r['layer'] == ly) for ly in ('wn', 'mw', 'semdom')}
    meta = {
        'generator': 'build_sense_frequency_layer.py',
        'handoff': 'H1453', 'model': f'Opus 4.8 ({CSN})',
        'sources': {
            'attestation': 'VisualDCS/src/DCS-data-2026/dcs_full.sqlite token.m_wordsem '
                           '(canonical CoNLL-U ingest; 219/270 texts sense-tagged)',
            'decode': 'wordsem_inventory.tsv (CoNLL-U lookup/word-senses.csv)',
            'wn_to_mw': 'wn_to_mw_map.tsv (English gloss-overlap adjudication)',
        },
        'join_key': 'lemma_slp1 (SLP1, sanskrit-util normalised) — LEFT-JOIN onto kosha lemmas',
        'layers': {
            'wn': 'native Sanskrit-WordNet synset (lossless gold)',
            'mw': 'MW numbered sense (projection; sense_id=<lemma>#<mw_ord>)',
            'semdom': 'WordNet lexicographer supersense (best-effort semantic domain)',
        },
        'dispersion_debiasing_wave15': {
            'why': 'DCS is not a balanced sample of Sanskrit — the WordSem-tagged subset '
                   'over-represents rasaśāstra/āyurveda (Hellwig\'s research focus), so raw '
                   'token frequency inflates genre-concentrated senses (rasa=mercury). '
                   'Predominant sense is domain-relative (McCarthy, Koeling, Weeds, Carroll, '
                   'ACL 2004 P04-1036; Koeling, McCarthy, Carroll, HLT/EMNLP 2005 H05-1053).',
            'columns': {
                'n_texts': 'document frequency — distinct DCS texts attesting this (lemma, sense)',
                'dispersion_dp': 'Gries Deviation of Proportions over texts (0=even, →1=bursty); '
                                 'Gries 2008 IJCL 13(4):403–437',
                'largest_text_share': 'fraction of the sense\'s tokens in its single biggest text '
                                      '(burstiness diagnostic)',
                'count_adj': 'dispersion-adjusted count = count_all × (1 − dispersion_dp) — '
                             'discounts genre-concentrated senses',
                'sense_rank_adj': 'dense rank within lemma+layer by count_adj (the de-biased order)',
            },
            'caveat': 'DP is CORPUS-SIZE-relative, not genre-relative: it needs no genre labels '
                      '(none ship in the local DCS data) but under-penalises a sense concentrated '
                      'in a few LARGE texts. The fuller fix is wave-2 genre-stratified '
                      'post-stratification: p_balanced(s)=Σ_g w_g·P(s|g) with target (uniform/'
                      'reference) w_g, not count-proportional (Little 1993 JASA; Biber 1993); and '
                      'Chan & Ng 2006 (COLING-ACL P06-1012) EM sense-prior re-estimation. Keep '
                      'BOTH count_all and count_adj — the raw number is right for a reader IN that '
                      'genre; the adjusted one for "Sanskrit generally".',
        },
        'rows': len(rows), 'rows_by_layer': n_layers,
        'attested_pairs': len(pair),
        'wordsem_tokens_total': sum(pair.values()),
        'coverage_tokens': {
            'wn': cov['wn_tokens'],
            'mw_resolved': cov['mw_tokens'],
            'mw_exact': cov['mw_exact'], 'mw_overlap': cov['mw_overlap'],
            'mw_unresolved': cov['mw_unresolved_tokens'],
            'semdom_resolved': cov['semdom_tokens'],
            'semdom_unresolved': cov['semdom_unresolved_tokens'],
        },
        'ac3_containment': {
            'rule': 'per-lemma Σ(wn count_all) ≤ lemma_frequency.count_all',
            'lemmas_checked': checked, 'violations': violations,
            'lemmas_without_lemma_freq_count': no_lf,
            'violation_rate': round(violations / checked, 4) if checked else None,
            'worst_examples': [
                {'lemma': l, 'wn_sum': w, 'lemma_count_all': lc, 'excess': e}
                for l, w, lc, e in worst[:10]],
            'note': 'Any residual excess is a DCS-vintage mismatch between the dcs_full '
                    'token count and the Leonchenko lemma_frequency sheet, not senses '
                    'out-counting the lemma; reported, never hidden.',
        },
        'caveats': [
            'provenance=attested on every wave-1 row — it IS the WordSem gold; no accuracy claim.',
            'WordSem coverage is 219/270 texts (9.3% of corpus tokens); the 51 untagged '
            'texts incl. the 2026 Vedic wave carry zero WordSem (SL FINDINGS §11 addendum).',
            'periods vector is EMPTY in wave-1: no clean per-token text→DCS-period map ships '
            'in the CoNLL-U release; the wave-2 path is conllu/lookup/chapter-info.xml `era`.',
            'Upstream UD Tense=Past conflates aorist/perfect (inherited lemma_frequency caveat).',
            'Layer-3 = WordNet supersense (native to the WordSem id-space), not the SIL-semdom '
            'A58 crosswalk (keyed by Amarakosha eid / Princeton WN — different id-space). '
            'SIL-semdom projection deferred to a follow-on.',
        ],
    }
    with open(OUT_META, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("=== sense_frequency.tsv ===")
    print(f"rows: {len(rows):,}  (wn {n_layers['wn']:,} · mw {n_layers['mw']:,} · semdom {n_layers['semdom']:,})")
    print(f"attested (lemma,synset) pairs: {len(pair):,}; WordSem tokens: {sum(pair.values()):,}")
    print(f"Layer 2 (mw)     token coverage: {cov['mw_tokens']:,} "
          f"({cov['mw_tokens']/cov['wn_tokens']:.1%})")
    print(f"Layer 3 (semdom) token coverage: {cov['semdom_tokens']:,} "
          f"({cov['semdom_tokens']/cov['wn_tokens']:.1%})")
    print(f"\nAC#3 containment: {checked:,} lemmas checked, {violations:,} violations "
          f"({violations/checked:.2%} — must be ~0); {no_lf:,} lemmas lacked a lemma_freq count")
    if worst:
        print("  worst excess:", worst[:3])
    print(f"-> {args.out}\n-> {OUT_META}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
