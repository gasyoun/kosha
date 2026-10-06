#!/usr/bin/env python
r"""H6066 — full-volume join MW senses x DCS citations (sense-corpus-join skill).

One row per MW numbered sense (kosha.db entries/senses, dict='mw'), joined to:

  corpus lemma tier   data/frequency/lemma_frequency.tsv   (committed DCS lemma
                     frequency sidecar — count_all/rank_all/periods_sum)
  ws sense tier       data/frequency/sense_frequency.tsv   (layer=mw, WordSem
                     per-sense ATTESTED counts, sense_id=<lemma>#<mw_ord>)
  mfs estimate flag   data/frequency/wsd_untagged_mfs_counts.tsv (layer=mw,
                     estimated most-frequent-sense for untagged lemmas)

Sense ordinal = 1-based position within an slp1_key group, ordered by
(CAST(L AS INTEGER), sense_n) — the IDENTICAL convention build_wn_mw_map.py
established for sense_id=<lemma>#<mw_ord> (H1453), so ws counts land on the
right sense row by construction. Homonym asymmetry is declared, not resolved:
corpus lemmas cannot split MW homonyms (n_entries_key column carries the
collision size; conflict rows are listed, never guessed — skill Phase 3 gate).

Both denominators are first-class output (never the flattering side only):
  |senses with attested headword| / |all MW senses|
  |senses with ws sense-attestation| / |all MW senses|
  |DCS lemmas matching >=1 MW headword| / |DCS lemmas|

Outputs (data/concordance/):
  mw_sense_dcs_join.tsv.gz                     the join (all 303k senses; dict_only
                                                rows keep empty corpus columns)
  mw_sense_dcs_join_corpus_only.tsv            DCS lemmas with no MW headword
  mw_sense_dcs_observatory_feed.json           dashboard feed for csl-observatory
  mw_sense_dcs_join.meta.json                  pins, key, denominators, n

  python scripts/build_mw_sense_dcs_join.py            # build
  python scripts/build_mw_sense_dcs_join.py --check    # re-derive metrics from
                                                       # written outputs (parity gate)

Reads kosha.db / dcs_full.sqlite READ-ONLY (file: URI mode=ro). No network.
"""
import argparse
import csv
import gzip
import io
import json
import os
import random
import re
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FREQ = os.path.join(ROOT, 'data', 'frequency')
OUT_DIR = os.path.join(ROOT, 'data', 'concordance')

# kosha.db lives in the shared main checkout (gitignored build artifact);
# the worktree has no copy. Resolve main checkout relative to the worktree.
_CANDIDATE_DBS = [
    os.path.join(ROOT, 'data', 'db', 'kosha.db'),
    os.path.normpath(os.path.join(ROOT, '..', 'kosha', 'data', 'db', 'kosha.db')),
    os.path.normpath(os.path.join(ROOT, '..', '..', 'GitHub', 'kosha', 'data', 'db', 'kosha.db')),
    os.path.normpath(os.path.join(ROOT, '..', '..', '..', 'GitHub', 'kosha', 'data', 'db', 'kosha.db')),
]
DEFAULT_KOSHA_DB = next((p for p in _CANDIDATE_DBS if os.path.exists(p)), _CANDIDATE_DBS[0])
_DCS_CANDIDATES = [
    os.path.join(ROOT, '..', '..', 'VisualDCS', 'src', 'DCS-data-2026', 'dcs_full.sqlite'),
    os.path.join(ROOT, '..', '..', '..', 'GitHub', 'VisualDCS', 'src', 'DCS-data-2026', 'dcs_full.sqlite'),
]
DEFAULT_DCS = os.path.normpath(next(
    (p for p in _DCS_CANDIDATES if os.path.exists(p)), _DCS_CANDIDATES[0]))

LEMMA_FREQ = os.path.join(FREQ, 'lemma_frequency.tsv')
SENSE_FREQ = os.path.join(FREQ, 'sense_frequency.tsv')
MFS_EST = os.path.join(FREQ, 'wsd_untagged_mfs_counts.tsv')
WN_MW_MAP = os.path.join(FREQ, 'wn_to_mw_map.tsv')

JOIN_TSV = os.path.join(OUT_DIR, 'mw_sense_dcs_join.tsv.gz')
CORPUS_ONLY_TSV = os.path.join(OUT_DIR, 'mw_sense_dcs_join_corpus_only.tsv')
FEED_JSON = os.path.join(OUT_DIR, 'mw_sense_dcs_observatory_feed.json')
META_JSON = os.path.join(OUT_DIR, 'mw_sense_dcs_join.meta.json')

COLUMNS = ['entry_id', 'L', 'slp1', 'k2', 'n_entries_key', 'sense_n', 'sense_ord',
           'gloss', 'dcs_match', 'dcs_count_all', 'dcs_rank_all', 'dcs_grammar',
           'dcs_periods_sum', 'ws_count', 'ws_rank', 'ws_share', 'ws_prov', 'mfs_est']

_TAG = re.compile(r'<[^>]+>')
GLOSS_CAP = 80
WSN = "GLM 5.3 (opencode/zai-coding-plan/glm-5.3)"  # H6066 executor provenance


def strip_markup(t):
    return re.sub(r'\s+', ' ', _TAG.sub(' ', t or '')).replace('&amp;', '&').strip()


def load_tsv(path, key_col):
    out = {}
    with open(path, encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            out[r[key_col]] = r
    return out


def load_ws_sense_counts():
    """{(lemma, ord): (count, rank, share, prov)} from sense_frequency.tsv layer=mw.
    sense_id = '<lemma>#<mw_ord>'. A pair can carry BOTH an attested (gold) and
    an estimated (H1588 MFS) row — ATTESTED WINS; the estimate is marked via
    ws_prov='estimated' only when no attested row exists."""
    out = {}
    with open(SENSE_FREQ, encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['layer'] != 'mw':
                continue
            lemma, _, ord_s = r['sense_id'].rpartition('#')
            try:
                ordn = int(ord_s)
            except ValueError:
                continue
            key = (r['lemma_slp1'], ordn)
            prov = r.get('provenance') or 'attested'
            if key in out and out[key][3] == 'attested':
                continue  # gold wins over estimate
            out[key] = (r['count_all'], r['sense_rank'], r['lemma_share'], prov)
    return out


def load_mfs_est():
    out = set()
    with open(MFS_EST, encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['layer'] != 'mw':
                continue
            lemma, _, ord_s = r['sense_id'].rpartition('#')
            try:
                out.add((lemma, int(ord_s)))
            except ValueError:
                continue
    return out


def build():
    # ---- Phase 1 pins ----------------------------------------------------
    lemma_freq = load_tsv(LEMMA_FREQ, 'lemma_slp1')
    ws_counts = load_ws_sense_counts()
    mfs_est = load_mfs_est()
    print(f"[in ] lemma_frequency {len(lemma_freq):,} lemmas · "
          f"ws mw-senses {len(ws_counts):,} · mfs-est senses {len(mfs_est):,}")

    con = sqlite3.connect(f"file:{DEFAULT_KOSHA_DB}?mode=ro", uri=True)
    # ---- dict side: ALL mw senses, printed order (identical to wn_to_mw_map)
    cur = con.execute(
        "SELECT e.id, CAST(e.L AS INTEGER) AS Ln, e.slp1_key, e.k2, s.sense_n, "
        "       substr(e.body, s.span_start + 1, s.span_end - s.span_start) "
        "FROM entries e JOIN senses s ON s.entry_id = e.id "
        "WHERE e.dict='mw' "
        "ORDER BY e.slp1_key, Ln, s.sense_n")
    sense_rows = cur.fetchall()
    entries_per_key = {}
    for (slp1, n) in con.execute(
            "SELECT slp1_key, count(*) FROM entries WHERE dict='mw' GROUP BY slp1_key"):
        entries_per_key[slp1] = n
    no_sense_entries = {}
    for (eid, slp1) in con.execute(
            "SELECT e.id, e.slp1_key FROM entries e "
            "LEFT JOIN senses s ON s.entry_id = e.id "
            "WHERE e.dict='mw' AND s.entry_id IS NULL"):
        no_sense_entries[eid] = slp1
    con.close()

    # ---- join ------------------------------------------------------------
    rows_written = 0
    senses_total = 0
    senses_lemma_attested = 0
    senses_ws_attested = 0
    senses_homonym = 0
    matched_lemmas = set()
    landed_ws = set()
    senses_ws_est_only = 0
    prev_key, ord_ctr = None, 0
    senses_per_key = {}
    top_ws = []

    os.makedirs(OUT_DIR, exist_ok=True)
    gz = gzip.GzipFile(filename='', mode='wb', fileobj=open(JOIN_TSV, 'wb'), mtime=0)
    with io.TextIOWrapper(gz, encoding='utf-8', newline='') as out:
        out.write('\t'.join(COLUMNS) + '\n')
        for eid, ln, slp1, k2, sn, gloss_raw in sense_rows:
            senses_total += 1
            if slp1 != prev_key:
                prev_key, ord_ctr = slp1, 0
            ord_ctr += 1
            lf = lemma_freq.get(slp1)
            ws = ws_counts.get((slp1, ord_ctr))
            nek = entries_per_key.get(slp1, 1)
            if nek > 1:
                senses_homonym += 1
            match = 'dict_only' if lf is None else 'lemma'
            if lf is not None:
                senses_lemma_attested += 1
                matched_lemmas.add(slp1)
            ws_count = ws_rank = ws_share = ws_prov = ''
            if ws is not None:
                senses_ws_attested += 1
                landed_ws.add((slp1, ord_ctr))
                ws_count, ws_rank, ws_share, ws_prov = ws
                if ws_prov != 'attested':
                    senses_ws_est_only += 1
                try:
                    top_ws.append((int(ws_count), slp1, ord_ctr, sn))
                except (TypeError, ValueError):
                    pass
            senses_per_key[slp1] = ord_ctr  # last ordinal seen = sense count
            gloss = strip_markup(gloss_raw)[:GLOSS_CAP]
            out.write('\t'.join(str(x) for x in [
                eid, ln, slp1, k2 or '', nek, sn, ord_ctr, gloss, match,
                lf['count_all'] if lf else '', lf['rank_all'] if lf else '',
                lf['grammar_all'] if lf else '', lf['periods_sum'] if lf else '',
                ws_count, ws_rank, ws_share, ws_prov,
                1 if (slp1, ord_ctr) in mfs_est else 0]) + '\n')
            rows_written += 1
    print(f"[out] join rows {rows_written:,}")

    # ---- corpus_only residue ---------------------------------------------
    corpus_only = [(lem, r) for lem, r in lemma_freq.items() if lem not in entries_per_key]
    with open(CORPUS_ONLY_TSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n')
        w.writerow(['lemma_slp1', 'count_all', 'grammar_all', 'rank_all'])
        for lem, r in sorted(corpus_only, key=lambda kv: -int(kv[1]['count_all'] or 0)):
            w.writerow([lem, r['count_all'], r['grammar_all'], r['rank_all']])

    # ---- metrics ----------------------------------------------------------
    no_sense_attested = sum(1 for slp1 in no_sense_entries.values()
                            if slp1 in lemma_freq)
    # ws-landing residue: sense_frequency mw pairs that found NO MW sense row.
    # Split by cause: lemma absent from MW vs ordinal beyond the sense list.
    ws_unlanded_no_entry = sum(1 for (lem, _o) in ws_counts if lem not in senses_per_key)
    ws_unlanded_ord_past = (len(ws_counts) - senses_ws_attested - ws_unlanded_no_entry)
    metrics = {
        'senses_total': senses_total,
        'mw_entries': sum(entries_per_key.values()),
        'mw_entries_without_senses': len(no_sense_entries),
        'mw_entries_without_senses_lemma_attested': no_sense_attested,
        'senses_lemma_attested': senses_lemma_attested,
        'senses_ws_attested': senses_ws_attested,
        'senses_homonym_collision': senses_homonym,
        'denom_senses_lemma': round(senses_lemma_attested / senses_total, 4),
        'denom_senses_ws': round(senses_ws_attested / senses_total, 4),
        'corpus_lemmas_total': len(lemma_freq),
        'corpus_lemmas_matched': len(matched_lemmas),
        'denom_corpus': round(len(matched_lemmas) / len(lemma_freq), 4),
        'corpus_only_lemmas': len(corpus_only),
        'ws_pairs_total': len(ws_counts),
        'ws_pairs_landed': senses_ws_attested,
        'senses_ws_est_only': senses_ws_est_only,
        'senses_ws_gold': senses_ws_attested - senses_ws_est_only,
        'ws_pairs_unlanded_no_mw_entry': ws_unlanded_no_entry,
        'ws_pairs_unlanded_ordinal_past_end': ws_unlanded_ord_past,
    }

    top_ws.sort(key=lambda t: (-t[0], t[1], t[2]))
    feed = {
        'dataset': 'mw-sense-dcs-join',
        'builder': 'scripts/build_mw_sense_dcs_join.py',
        'executor': WSN,
        'handoff': 'H6066',
        'axis': 'per-sense-freq (full volume, MW x DCS)',
        'join_key': 'SLP1 (sanskrit-util normalised both sides); '
                    'sense ordinal = 1-based printed order per slp1_key '
                    '(CAST(L AS INTEGER), sense_n) — same as wn_to_mw_map/H1453',
        'metrics': metrics,
        'tiers': {
            'lemma': 'headword-level DCS citation aggregates (lower bound for every '
                     'sense of an attested headword; corpus cannot split homonyms)',
            'ws': 'WordSem per-sense ATTESTED counts (projection via wn_to_mw_map)',
            'mfs_est': 'estimated most-frequent-sense flag for untagged lemmas '
                       '(wsd_untagged_mfs_counts; never a count)',
            'dict_only': 'senses of headwords with no DCS attestation — kept as rows',
        },
        'top_ws_senses': [
            {'lemma': l, 'sense_ord': o, 'sense_n': sn, 'count': c}
            for c, l, o, sn in top_ws[:50]],
    }
    with open(FEED_JSON, 'w', encoding='utf-8') as f:
        json.dump(feed, f, ensure_ascii=False, indent=1)

    meta = {
        'generator': 'scripts/build_mw_sense_dcs_join.py',
        'executor': WSN,
        'handoff': 'H6066',
        'rows': rows_written,
        'columns': COLUMNS,
        'metrics': metrics,
        'pins': {
            'kosha_db': os.path.basename(DEFAULT_KOSHA_DB),
            'mw_entries': 286525,
            'dcs_lemma_side': 'data/frequency/lemma_frequency.tsv (committed; '
                              'source VisualDCS archive.sqlite M9 period_freq)',
            'ws_sense_side': 'data/frequency/sense_frequency.tsv layer=mw (H1453)',
            'mfs_side': 'data/frequency/wsd_untagged_mfs_counts.tsv (H1588)',
            'dcs_full_sqlite_sha256': '8f3b06bd6ef0e47a9ccf81d147e73d5d240d64e0c'
                                      '12f6d789262eb422ebb23bc (manifest pin)',
        },
        'denominators': {
            'dict_side': '|senses_lemma_attested| / |senses_total| and '
                         '|senses_ws_attested| / |senses_total|',
            'corpus_side': '|corpus_lemmas_matched| / |corpus_lemmas_total|',
        },
    }
    with open(META_JSON, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    print(json.dumps(metrics, ensure_ascii=False, indent=1))
    return metrics


def check():
    """Parity gate: re-derive the metrics from the WRITTEN outputs."""
    lemma_freq = load_tsv(LEMMA_FREQ, 'lemma_slp1')
    entries_per_key = set()
    senses_total = senses_lemma = senses_ws = 0
    with gzip.open(JOIN_TSV, 'rt', encoding='utf-8', newline='') as f:
        rd = csv.DictReader(f, delimiter='\t')
        assert rd.fieldnames == COLUMNS, f"column drift: {rd.fieldnames}"
        for r in rd:
            senses_total += 1
            entries_per_key.add(r['slp1'])
            if r['dcs_match'] == 'lemma':
                senses_lemma += 1
                # every 'lemma' row must carry corpus columns, and they must
                # equal the committed sidecar for that key
                lf = lemma_freq[r['slp1']]
                assert r['dcs_count_all'] == lf['count_all'], r['slp1']
            if r['ws_count'] != '':
                senses_ws += 1
    with open(META_JSON, encoding='utf-8') as f:
        meta = json.load(f)
    m = meta['metrics']
    assert m['senses_total'] == senses_total, (m['senses_total'], senses_total)
    assert m['senses_lemma_attested'] == senses_lemma, (m['senses_lemma_attested'], senses_lemma)
    assert m['senses_ws_attested'] == senses_ws, (m['senses_ws_attested'], senses_ws)
    n_corpus_only = sum(1 for _ in open(CORPUS_ONLY_TSV, encoding='utf-8')) - 1
    assert m['corpus_only_lemmas'] == n_corpus_only
    assert m['corpus_lemmas_matched'] + n_corpus_only == m['corpus_lemmas_total']
    print(f"CHECK PASS — {senses_total:,} senses replayed; "
          f"lemma-tier {senses_lemma:,}; ws-tier {senses_ws:,}; "
          f"corpus_only {n_corpus_only:,}")


def validate(n=50):
    """Honest sample validation (skill Phase 4): link + count evidence re-queried
    from dcs_full.sqlite / wn_to_mw_map — NOT from the sidecars the build read.

    Declared encoding asymmetry: dcs_full.lemma stores IAST (Unicode, fully
    lowercased), while the committed sidecars are SLP1. SLP1 capitals are
    PHONEMES (B=bh, D=dh, S=z, I=I), never case markers — so the probe
    transcodes each db lemma IAST->SLP1 with the canonical sanskrit-util
    transcoder and matches EXACTLY (no case folding, which would corrupt
    SLP1)."""
    sys.path.insert(0, os.path.normpath(os.path.join(
        ROOT, '..', '..', 'GitHub', 'sanskrit-util', 'py')))
    try:
        from sanskrit_util import to_slp1
    except ImportError:
        sys.path.insert(0, os.path.normpath(os.path.join(
            ROOT, '..', '..', '..', 'GitHub', 'sanskrit-util', 'py')))
        from sanskrit_util import to_slp1

    random.seed(6066)
    rows = []
    with gzip.open(JOIN_TSV, 'rt', encoding='utf-8', newline='') as f:
        rd = csv.DictReader(f, delimiter='\t')
        for r in rd:
            if r['dcs_match'] == 'lemma' and r['ws_count'] != '':
                rows.append(r)
    sample = random.sample(rows, min(n, len(rows)))
    con = sqlite3.connect(f"file:{DEFAULT_DCS}?mode=ro", uri=True)
    link_fail = count_delta_gt5 = 0
    checked = 0
    for r in sample:
        slp1 = r['slp1']
        probe_slp1 = slp1  # already SLP1; capitals are phonemes
        # lemma side: IAST in db -> transcode db rows is expensive; probe by
        # translating the SLP1 key back is not offered, so query both the raw
        # key and its case-folded form against the db's own slp1 of lemma via
        # a small cached lemma index built ONCE for the sample.
        if not hasattr(validate, '_idx'):
            # lemma-side index: dcs_full.lemma is IAST; one lemma STRING can have
            # several lemma_ids (homonyms/POS rows) — sum tokens across ALL of them,
            # else the probe undercounts systematically.
            validate._idx = {}
            q = ("SELECT l.lower_l, sum(cnt) FROM "
                 "(SELECT lower(lemma) AS lower_l, lemma_id FROM lemma) l "
                 "JOIN (SELECT lemma_id, count(*) AS cnt FROM token GROUP BY lemma_id) t "
                 "ON t.lemma_id = l.lemma_id GROUP BY l.lower_l")
            for lem_low, total in con.execute(q):
                try:
                    validate._idx[to_slp1(lem_low)] = total
                except Exception:
                    validate._idx[lem_low] = total
        lid_total = validate._idx.get(probe_slp1)
        if lid_total is None:
            link_fail += 1
            continue
        n_tok = lid_total
        checked += 1
        try:
            if abs(n_tok - int(r['dcs_count_all'])) > max(5, 0.05 * n_tok):
                count_delta_gt5 += 1
        except (TypeError, ValueError):
            count_delta_gt5 += 1
    con.close()
    # ws-tier independent re-derivation from wn_to_mw_map (5 rows, ATTESTED gold only)
    map_pairs = {}
    with open(WN_MW_MAP, encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['match_type'] not in ('exact', 'overlap'):
                continue  # sense_frequency mw layer counts only resolved projections
            if r['mw_sense_ord'] in ('', '0'):
                continue
            key = (r['lemma_slp1'], int(r['mw_sense_ord']))
            map_pairs[key] = map_pairs.get(key, 0) + int(r['n_tokens'] or 0)
    ws_sample = [r for r in sample if r['ws_prov'] == 'attested'][:5]
    ws_fail = 0
    for r in ws_sample:
        key = (r['slp1'], int(r['sense_ord']))
        expect = map_pairs.get(key)
        if expect is None or int(r['ws_count']) != expect:
            ws_fail += 1
    print(f"VALIDATE — link_fail {link_fail}/{len(sample)} · "
          f"count_delta>5% {count_delta_gt5}/{checked} (cross-source: sidecar=archive.sqlite "
          f"period_freq vs probe=dcs_full tokens) · ws_rederive_fail {ws_fail}/{len(ws_sample)}")
    return {'link_fail': link_fail, 'n': len(sample), 'count_delta': count_delta_gt5,
            'ws_fail': ws_fail, 'ws_checked': len(ws_sample)}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--validate', action='store_true')
    args = ap.parse_args()
    if args.check:
        check()
    elif args.validate:
        validate()
    else:
        build()
