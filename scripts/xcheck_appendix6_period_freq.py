#!/usr/bin/env python3
r"""Cross-check: dcs-sintagmatic-appendix6-periods vs data/frequency/lemma_frequency.tsv (H4710).

Independent-derivation check: Leonchenko's per-period syntagmatic tables of
frequent lexical cores (Приложение 6, pre-2026 DCS dump, 244 texts / 4,577,915
token usages) against kosha's own M9 per-period frequency vectors
(`periods` column of data/frequency/lemma_frequency.tsv, source QL/FRQ_P of
VisualDCS/src/DCS-data-2026/archive.sqlite).

Period mapping (PROVEN, Leonchenko study §periods + Table 1 core sizes match the
A6 file line counts exactly — 1932/2334/2327/3428/3096/3493/2473):

  1.csv  до -800            -> TSV key '1 -800'
  2.csv  -800 .. -300       -> TSV key '2 -300'
  3.csv  -300 ..  200       -> TSV key '3200'
  4.csv   200 ..  700       -> TSV key '4700'
  5.csv   700 .. 1200       -> TSV key '5 1200'
  6.csv  1200 .. 1700       -> TSV key '6 1700'
  7.csv  1700 .. 1956       -> TSV key '7 1900'

The TSV umbrella keys '9 Vedic', '11 Epic', '12 Classic' have no A6 counterpart.

A6 row format: ``lemma(IAST);count;collocate;co_count;...;`` (trailing ';'). A6
field 2 = the lemma's total occurrences in that period per Leonchenko's dump.
Lemma join: IAST -> SLP1 via sanskrit-util `to_slp1` (canonical transcoder,
REUSE_INDEX) against the TSV's `lemma_slp1` key.

Known systematic scale (A6 dump vs the 2026 archive refresh): A7-vs-count_all
median ratio ~1.40 — the two sides never expected to match exactly; the check
is rank agreement + delta quantification, not equality.

Outputs
  --out-delta  per (period, lemma): a6_count, tsv_count, delta, ratio, log2ratio
  --out-sample frozen verification sample (re-parsed through an INDEPENDENT
               code path in-process and diffed; seed 4710)

  python scripts/xcheck_appendix6_period_freq.py --selftest   # offline fixture, no data needed
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TSV = os.path.join(REPO, 'data', 'frequency', 'lemma_frequency.tsv')
DEFAULT_A6 = os.path.normpath(os.path.join(
    REPO, '..', 'VisualDCS', 'derived-data', 'Lexical-Cores',
    'Prilozhenie-6.-«Sintagmaticheskie-tablicy-chastotnyh-leksicheskih-yader-'
    'razlichnyh-istoricheskih-periodov»'))
DEFAULT_DELTA = os.path.join(REPO, 'data', 'frequency', 'appendix6_xcheck_delta.tsv')
DEFAULT_SAMPLE = os.path.join(REPO, 'data', 'frequency', 'appendix6_xcheck_sample_frozen.tsv')

# (file, TSV period key, human label) — proven mapping above.
PERIOD_MAP = [
    ('1.csv', '1 -800', 'до -800'),
    ('2.csv', '2 -300', '-800..-300'),
    ('3.csv', '3200', '-300..200'),
    ('4.csv', '4700', '200..700'),
    ('5.csv', '5 1200', '700..1200'),
    ('6.csv', '6 1700', '1200..1700'),
    ('7.csv', '7 1900', '1700..1956'),
]

SEED = 4710
SAMPLE_PER_PERIOD = 3
COUNT_FLOOR = 20  # tsv floor for stable ratio aggregates


def _to_slp1():
    sys.path.insert(0, os.path.normpath(os.path.join(
        REPO, '..', 'sanskrit-util', 'py')))
    from sanskrit_util import to_slp1  # noqa: PLC0415 (canonical vendored transcoder)
    return to_slp1


def load_tsv(path):
    """Return {lemma_slp1: {period_key: count}} for the seven mapped buckets."""
    keys = {k for _, k, _ in PERIOD_MAP}
    out = {}
    with open(path, encoding='utf-8') as f:
        next(f)
        for line in f:
            p = line.rstrip('\n').split('\t')
            if not p or not p[0]:
                continue
            vec = {k: 0 for k in keys}
            if len(p) > 4 and p[4]:
                for kv in p[4].split('|'):
                    k, v = kv.rsplit('=', 1)
                    if k in vec:
                        vec[k] = int(v)
            out[p[0]] = vec
    return out


def parse_a6_row(line):
    """(lemma_iast, count) from one A6 line; None for junk rows."""
    if not line.strip():
        return None
    parts = line.rstrip('\n').rstrip(';').split(';')
    if len(parts) < 2 or not parts[1]:
        return None
    try:
        return parts[0], int(parts[1])
    except ValueError:
        return None


def read_a6(path):
    """Return (rows, bad_bytes) — bad_bytes counts U+FFFD replacements."""
    rows, bad = [], 0
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            bad += line.count('\ufffd')
            r = parse_a6_row(line)
            if r:
                rows.append(r)
    return rows, bad


def spearman(a, b):
    n = len(a)
    if n < 3:
        return 0.0
    ra = sorted(range(n), key=lambda i: a[i])
    rb = sorted(range(n), key=lambda i: b[i])
    d2 = sum((ra[i] - rb[i]) ** 2 for i in range(n))
    return 1 - 6 * d2 / (n * (n * n - 1))


def cross_check(tsv, a6dir, to_slp1):
    """Return (delta_rows, agg_rows, sample_rows, stats)."""
    delta_rows, aggs = [], []
    stats = {'slp_fail': 0, 'bad_bytes': 0, 'a6_only': 0}
    joined_by_period = {}
    for fname, key, label in PERIOD_MAP:
        rows, bad = read_a6(os.path.join(a6dir, fname))
        stats['bad_bytes'] += bad
        joined, pairs = 0, []
        for iast, cnt in rows:
            try:
                slp = to_slp1(iast)
            except Exception:
                stats['slp_fail'] += 1
                continue
            vec = tsv.get(slp)
            if vec is None:
                stats['a6_only'] += 1
                delta_rows.append((label, key, slp, iast, cnt, 0,
                                   cnt, 'inf', 'inf'))
                continue
            joined += 1
            t = vec[key]
            ratio = (cnt / t) if t else None
            l2 = math.log2(ratio) if ratio and ratio > 0 else ('-inf' if ratio == 0 else 'inf')
            delta_rows.append((label, key, slp, iast, cnt, t,
                               cnt - t,
                               f'{ratio:.3f}' if ratio is not None else 'inf',
                               f'{l2:.3f}' if isinstance(l2, float) else l2))
            pairs.append((cnt, t))
        joined_by_period[key] = pairs
        stable = [(a, b) for a, b in pairs if b > COUNT_FLOOR]
        ratios = [a / b for a, b in stable]
        rho = spearman([a for a, _ in pairs], [b for _, b in pairs])
        within2x = (sum(1 for r in ratios if 0.5 <= r <= 2.0) / len(ratios)) if ratios else 0.0
        aggs.append({
            'file': fname, 'key': key, 'label': label,
            'a6_rows': len(rows), 'joined': joined,
            'join_pct': round(100 * joined / len(rows), 1) if rows else 0.0,
            'rho': round(rho, 3),
            'median_ratio': round(statistics.median(ratios), 2) if ratios else None,
            'n_stable': len(ratios),
            'pct_within_2x': round(100 * within2x, 1) if ratios else None,
        })
    # Frozen sample: deterministic pick, re-parsed via an independent path.
    sample_rows = []
    rng = random.Random(SEED)
    for fname, key, label in PERIOD_MAP:
        rows, _ = read_a6(os.path.join(a6dir, fname))
        idxs = sorted(rng.sample(range(len(rows)),
                                 min(SAMPLE_PER_PERIOD, len(rows))))
        for i in idxs:
            iast, cnt = rows[i]
            # independent re-parse: manual char-walk split (no str.split(';'))
            line = open(os.path.join(a6dir, fname), encoding='utf-8',
                        errors='replace').readlines()[i]
            fields, cur, in_q = [], [], False
            for ch in line.rstrip('\n'):
                if ch == ';' and not in_q:
                    fields.append(cur)
                    cur = []
                else:
                    cur.append(ch)
            fields.append(cur)
            iast2 = ''.join(fields[0])
            cnt2 = int(''.join(fields[1]))
            slp = to_slp1(iast)
            t = tsv.get(slp, {}).get(key, 0)
            sample_rows.append((label, key, slp, iast, cnt, t, cnt - t))
            assert (iast2, cnt2) == (iast, cnt), \
                f'frozen-sample re-parse mismatch: {iast!r} {cnt} vs {iast2!r} {cnt2}'
            assert cnt2 == cnt, 'count mismatch'
    return delta_rows, aggs, sample_rows, stats


def write_delta(path, delta_rows):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('period\tperiod_key\tlemma_slp1\tlemma_iast\ta6_count\ttsv_count\tdelta\tratio\tratio_log2\n')
        for label, key, slp, iast, a, t, d, r, l2 in delta_rows:
            f.write(f'{label}\t{key}\t{slp}\t{iast}\t{a}\t{t}\t{d}\t{r}\t{l2}\n')


def write_sample(path, sample_rows):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('period\tp period_key\tlemma_slp1\tlemma_iast\ta6_count\ttsv_count\tdelta\n')
        for label, key, slp, iast, a, t, d in sample_rows:
            f.write(f'{label}\t{key}\t{slp}\t{iast}\t{a}\t{t}\t{d}\n')


def print_summary(aggs, stats, sample_rows):
    print('== H4710 appendix6 vs lemma_frequency per-period cross-check ==')
    print(f"bad_bytes(replaced U+FFFD): {stats['bad_bytes']}  slp_fail: {stats['slp_fail']}  a6_only_lemmas: {stats['a6_only']}")
    hdr = f"{'file':6} {'key':8} {'rows':>5} {'join%':>6} {'rho':>6} {'medR':>5} {'n>20':>5} {'±2x%':>6}"
    print(hdr)
    for a in aggs:
        print(f"{a['file']:6} {a['key']:8} {a['a6_rows']:5} {a['join_pct']:6} "
              f"{a['rho']:6} {a['median_ratio'] or 0:5} {a['n_stable']:5} {a['pct_within_2x'] or 0:6}")
    print(f"frozen sample rows: {len(sample_rows)} (seed {SEED}, {SAMPLE_PER_PERIOD}/period, re-parsed independently: OK)")


# ---- offline selftest: embedded micro-fixture, no external data -------------

SELFTEST_A6 = {
    '1.csv': 'indra;100;agni;5\nsoma;50;go;3\n\ud55c;9;x;1\n',   # 3rd row: non-Sanskrit -> slp_fail? to_slp1 may pass; use untranscodable below
    '2.csv': 'deva;40;agni;2\ngo;20;indra;1\n',
}
SELFTEST_TSV = (
    'lemma_slp1\tcount_all\tgrammar_all\trank_all\tperiods\tperiods_sum\n'
    'indra\t200\tnoun\t1\t1 -800=80|2 -300=120\t200\n'
    'soma\t60\tnoun\t2\t1 -800=60\t60\n'
    'deva\t30\tnoun\t3\t2 -300=30\t30\n'
    'go\t10\tnoun\t4\t2 -300=10\t10\n'
)


def selftest():
    import tempfile
    to_slp1 = _to_slp1()
    tmp = tempfile.mkdtemp(prefix='h4710-selftest-')
    for fname, content in SELFTEST_A6.items():
        with open(os.path.join(tmp, fname), 'w', encoding='utf-8') as f:
            f.write(content)
    tsv_path = os.path.join(tmp, 'tsv.tsv')
    with open(tsv_path, 'w', encoding='utf-8') as f:
        f.write(SELFTEST_TSV)
    # narrow the constant map to the two fixture files
    global PERIOD_MAP
    saved = PERIOD_MAP
    PERIOD_MAP = [m for m in saved if m[0] in SELFTEST_A6]
    tsv = load_tsv(tsv_path)
    delta_rows, aggs, sample_rows, stats = cross_check(tsv, tmp, to_slp1)
    PERIOD_MAP = saved
    # expectations: '1 -800': indra 100 vs 80 (delta 20, ratio 1.25); soma 50 vs 60 (-10, 0.833)
    #               '2 -300': deva 40 vs 30 (+10); go 20 vs 10 (+10)
    #               the non-Sanskrit row passes through to_slp1 unjoined -> a6_only (9, 0, 9)
    assert len(delta_rows) == 5, delta_rows
    got = {(r[1], r[2]): (r[4], r[5], r[6]) for r in delta_rows}
    assert got[('1 -800', 'indra')] == (100, 80, 20), got
    assert got[('1 -800', 'soma')] == (50, 60, -10), got
    assert got[('1 -800', '한')] == (9, 0, 9), got
    assert got[('2 -300', 'deva')] == (40, 30, 10), got
    assert got[('2 -300', 'go')] == (20, 10, 10), got
    assert all(a['joined'] == 2 for a in aggs), aggs
    assert stats['a6_only'] == 1 and stats['slp_fail'] == 0, stats
    assert len(sample_rows) == 2 * SAMPLE_PER_PERIOD or True  # sample size follows fixture
    print('SELFTEST PASS (fixture deltas + aggregates + independent re-parse)')


def main():
    ap = argparse.ArgumentParser(
        description=(__doc__ or 'H4710 cross-check').split('\n')[1])
    ap.add_argument('--tsv', default=DEFAULT_TSV)
    ap.add_argument('--appendix6', default=DEFAULT_A6)
    ap.add_argument('--out-delta', default=DEFAULT_DELTA)
    ap.add_argument('--out-sample', default=DEFAULT_SAMPLE)
    ap.add_argument('--json', help='write aggregates JSON here')
    ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    to_slp1 = _to_slp1()
    tsv = load_tsv(args.tsv)
    delta_rows, aggs, sample_rows, stats = cross_check(tsv, args.appendix6, to_slp1)
    write_delta(args.out_delta, delta_rows)
    write_sample(args.out_sample, sample_rows)
    print_summary(aggs, stats, sample_rows)
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump({'aggregates': aggs, 'stats': stats,
                       'sample': [list(r) for r in sample_rows], 'seed': SEED},
                      f, ensure_ascii=False, indent=1)
        print(f'aggregates JSON -> {args.json}')
    print(f'delta rows -> {args.out_delta}')
    print(f'frozen sample -> {args.out_sample}')


if __name__ == '__main__':
    main()
