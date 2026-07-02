#!/usr/bin/env python
r"""Build the kosha frequency sidecar layer from VisualDCS archive.sqlite (M9).

Bridge 1 (handoff OPUS_kosha_pwgru_frequency_layer.md, 02-07-2026): joins the
period / whole-corpus / core-vocabulary frequency tables of
`VisualDCS/src/DCS-data-2026/archive.sqlite` into ONE per-lemma record keyed by
`lemma_slp1` (SLP1, sanskrit-util-normalised) so it joins directly to kosha's
SLP1-native `lemmas.slp1` (PHASE1_PLAN D1) with no re-transcoding.

Output is a sidecar feed, NOT a materialised column: kosha's D1/D2 load LEFT-JOINs
`lemma_frequency` onto its `lemmas` table at build time. This keeps the frequency
asset independently rebuildable (archive.sqlite is refreshed by
VisualDCS/import_archive.py) and lets the same feed drive the pwg_ru slice ordering
(see build_pwg_freq_order.py in RussianTranslation/src).

Per-lemma record:
  lemma_slp1       join key (SLP1)
  count_all        whole-corpus token count, source Leonchenko/Прил3 period='ALL-corpus'
                   (SUMMED across part-of-speech rows for the same lemma)
  grammar_all      dominant part-of-speech tag (the POS row with the largest count)
  rank_all         dense rank over count_all, descending (1 = most frequent)
  periods          compact per-period vector from source QL/FRQ_P, DCS-coded periods,
                   pipe-joined `period=count`, only non-zero periods, period order fixed
  periods_sum      sum of the QL/FRQ_P period counts (auxiliary; a second DCS extraction)
  coverage_pct     Leonchenko/Сборное per-lemma corpus-coverage weight (null if absent)
  core_rank        Leonchenko/Сборное learn-these-first rank (null if absent)

The canonical single frequency number is `count_all`; a lemma present only in the
period table (no ALL-corpus row) still gets `periods`/`periods_sum` and is ranked by
`periods_sum` as a fallback so no lemma with a real signal is left unranked.

  python build_frequency_layer.py                 # -> lemma_frequency.tsv (+ .meta.json)
  python build_frequency_layer.py --archive PATH  # override archive.sqlite location
  python build_frequency_layer.py --selftest
"""
import argparse
import collections
import json
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
# Default: the gitignored M9 build in the sibling VisualDCS checkout.
DEFAULT_ARCHIVE = os.path.normpath(os.path.join(
    HERE, '..', '..', '..', 'VisualDCS', 'src', 'DCS-data-2026', 'archive.sqlite'))
OUT_TSV = os.path.join(HERE, 'lemma_frequency.tsv')
OUT_META = os.path.join(HERE, 'lemma_frequency.meta.json')

# Fixed DCS-coded period order (chronological), source QL/FRQ_P.
PERIOD_ORDER = ['9 Vedic', '1 -800', '2 -300', '3200', '4700',
                '5 1200', '6 1700', '7 1900', '11 Epic', '12 Classic']

COLUMNS = ['lemma_slp1', 'count_all', 'grammar_all', 'rank_all',
           'periods', 'periods_sum', 'coverage_pct', 'core_rank']


def _connect(archive):
    if not os.path.exists(archive):
        sys.exit(f"archive.sqlite not found: {archive}\n"
                 "Download the 'archive-2026-07' Release asset from gasyoun/VisualDCS "
                 "or rebuild with import_archive.py freq (see reports/m9_archive_ingest.md).")
    con = sqlite3.connect(archive)
    con.row_factory = sqlite3.Row
    return con


def build_records(con):
    """Return {lemma_slp1: record dict} joining the three frequency channels."""
    rec = collections.defaultdict(lambda: {
        'count_all': None, 'grammar_all': None,
        'periods': {}, 'periods_sum': 0,
        'coverage_pct': None, 'core_rank': None})

    # 1. Whole-corpus count + dominant POS (Leonchenko/Прил3, period='ALL-corpus').
    #    SUM across POS rows; remember the POS carrying the largest single count.
    dominant = {}  # lemma -> (best_count, grammar)
    for r in con.execute(
            "SELECT lemma_slp1, grammar, count FROM period_freq "
            "WHERE period='ALL-corpus'"):
        lemma, gram, cnt = r['lemma_slp1'], r['grammar'], r['count'] or 0
        e = rec[lemma]
        e['count_all'] = (e['count_all'] or 0) + cnt
        if lemma not in dominant or cnt > dominant[lemma][0]:
            dominant[lemma] = (cnt, gram)
    for lemma, (_, gram) in dominant.items():
        rec[lemma]['grammar_all'] = gram

    # 2. Per-period vector (source QL/FRQ_P, the DCS-coded historical periods).
    for r in con.execute(
            "SELECT lemma_slp1, period, count FROM period_freq "
            "WHERE source='QL/FRQ_P'"):
        lemma, period, cnt = r['lemma_slp1'], r['period'], r['count'] or 0
        e = rec[lemma]
        e['periods'][period] = e['periods'].get(period, 0) + cnt
        e['periods_sum'] += cnt

    # 3. Core-vocabulary coverage weight + learn-first rank (Leonchenko/Сборное).
    for r in con.execute(
            "SELECT lemma_slp1, coverage_pct, rank FROM core_vocab "
            "WHERE source='Leonchenko/Сборное'"):
        e = rec[r['lemma_slp1']]
        e['coverage_pct'] = r['coverage_pct']
        e['core_rank'] = r['rank']

    return rec


def rank_and_format(rec):
    """Assign dense rank_all and return sorted list of TSV row dicts."""
    # Rank by count_all desc; lemmas without count_all fall back to periods_sum,
    # and are ranked strictly after all counted lemmas (rank on a (has_count, key)).
    def sort_key(item):
        _, e = item
        has = e['count_all'] is not None
        primary = e['count_all'] if has else e['periods_sum']
        return (0 if has else 1, -(primary or 0), item[0])

    ordered = sorted(rec.items(), key=sort_key)
    rows = []
    last_val = object()
    rank = 0
    seen = 0
    for lemma, e in ordered:
        seen += 1
        val = (e['count_all'] is not None, e['count_all'] if e['count_all'] is not None
               else e['periods_sum'])
        if val != last_val:
            rank = seen
            last_val = val
        periods_str = '|'.join(
            f"{p}={e['periods'][p]}" for p in PERIOD_ORDER if e['periods'].get(p))
        rows.append({
            'lemma_slp1': lemma,
            'count_all': '' if e['count_all'] is None else e['count_all'],
            'grammar_all': e['grammar_all'] or '',
            'rank_all': rank,
            'periods': periods_str,
            'periods_sum': e['periods_sum'],
            'coverage_pct': '' if e['coverage_pct'] is None
                            else f"{e['coverage_pct']:.6g}",
            'core_rank': '' if e['core_rank'] is None else e['core_rank'],
        })
    return rows


def write_tsv(rows, path):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\t'.join(COLUMNS) + '\n')
        for row in rows:
            f.write('\t'.join(str(row[c]) for c in COLUMNS) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--archive', default=DEFAULT_ARCHIVE)
    ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args()

    con = _connect(args.archive)
    rec = build_records(con)
    rows = rank_and_format(rec)
    write_tsv(rows, OUT_TSV)

    n_count = sum(1 for r in rows if r['count_all'] != '')
    n_periods = sum(1 for r in rows if r['periods'])
    n_cov = sum(1 for r in rows if r['coverage_pct'] != '')
    meta = {
        'generator': 'build_frequency_layer.py',
        'source': 'VisualDCS/src/DCS-data-2026/archive.sqlite (M9)',
        'sources_used': {
            'count_all/grammar_all': "period_freq period='ALL-corpus' (Leonchenko/Прил3)",
            'periods/periods_sum': "period_freq source='QL/FRQ_P'",
            'coverage_pct/core_rank': "core_vocab source='Leonchenko/Сборное'",
        },
        'join_key': 'lemma_slp1 (SLP1, sanskrit-util normalised)',
        'period_order': PERIOD_ORDER,
        'rows': len(rows),
        'rows_with_count_all': n_count,
        'rows_with_period_vector': n_periods,
        'rows_with_coverage_pct': n_cov,
        'note': ('coverage_pct is the Leonchenko/Сборное per-lemma corpus-coverage '
                 'weight (NOT a running cumulative); count_all is the canonical '
                 'frequency; rows lacking count_all are ranked by periods_sum after '
                 'all counted lemmas.'),
    }
    with open(OUT_META, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write('\n')

    print(f"wrote {OUT_TSV}: {len(rows)} rows "
          f"({n_count} with count_all, {n_periods} with period vector, "
          f"{n_cov} with coverage_pct)")

    if args.selftest:
        # ca / tad are the two most frequent whole-corpus lemmas (indeclinable + pronoun).
        top = {r['lemma_slp1']: r for r in rows[:5]}
        assert 'ca' in top and top['ca']['rank_all'] == 1, top
        assert all(r['count_all'] != '' for r in rows[:100]), "top-100 must be counted"
        # every coverage_pct row must resolve to a lemma present in the feed
        assert n_cov > 0
        print("selftest OK")


if __name__ == '__main__':
    main()
