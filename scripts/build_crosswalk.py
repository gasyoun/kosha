"""kosha — sense_crosswalk.tsv emitter (RISKS.md R1 Commitment 2).

Every rebuild that changes sense text or count must leave an audit trail
mapping old senseN -> new senseN, so a citation minted against an old release
can be followed forward. This diffs two per-version sense archives
(scripts/archive_senses.py) entry-by-entry, matching senses by span-text
similarity, and emits one row per changed old sense with a status:

    SAME    old n == new n, identical text                (only emitted... never — see below)
    MOVED   1:1 match, sense number changed
    SPLIT   one old sense best-matches >=2 new senses
    MERGED  >=2 old senses best-match one new sense
    GONE    old sense has no similar new sense (citation breakage)
    NEW     new sense matched by no old sense (added)

**Zero-cost when nothing changed:** entries whose sense count AND per-sense
text are identical emit NO rows (SAME is implicit). The file therefore contains
only the renumbered/rewritten senses — the audit trail when there was one.

    python scripts/build_crosswalk.py --old A --new B [--out FILE] [--threshold 0.6]

Both versions must be archived under {KOSHA_RELEASES_DIR|data/releases}/. The
release notes cite the per-dict renumbered count this script prints (R1 C2).
"""
import argparse
import difflib
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from versions import archive_db_path  # noqa: E402


def load_archive(version):
    path = archive_db_path(version)
    if not path.exists():
        raise SystemExit(f"version '{version}' not archived at {path} "
                         f"(run scripts/archive_senses.py --version {version})")
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    entries = defaultdict(dict)  # (dict, L) -> {sense_n: text_raw}
    for r in con.execute("SELECT dict, L, sense_n, text_raw FROM archive"):
        entries[(r["dict"], r["L"])][r["sense_n"]] = r["text_raw"]
    con.close()
    return entries


def _ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def diff_entry(old, new, threshold):
    """old/new: {sense_n: text}. Returns list of (old_n, new_n, status, sim).
    Empty list when the entry is unchanged (zero-cost)."""
    if old == new:
        return []
    old_ns = sorted(old)
    new_ns = sorted(new)

    # similarity matrix + best matches both directions
    best_new_for_old = {}   # old_n -> (new_n, sim)
    best_old_for_new = {}   # new_n -> (old_n, sim)
    for i in old_ns:
        bj, bs = None, -1.0
        for j in new_ns:
            s = _ratio(old[i], new[j])
            if s > bs:
                bj, bs = j, s
        best_new_for_old[i] = (bj, bs)
    for j in new_ns:
        bi, bs = None, -1.0
        for i in old_ns:
            s = _ratio(old[i], new[j])
            if s > bs:
                bi, bs = i, s
        best_old_for_new[j] = (bi, bs)

    # which olds claim each new as their top match (>=threshold)
    claimants = defaultdict(list)
    for i in old_ns:
        j, s = best_new_for_old[i]
        if s >= threshold:
            claimants[j].append(i)

    rows = []
    matched_new = set()
    for i in old_ns:
        j, s = best_new_for_old[i]
        if s < threshold:
            rows.append((i, None, "GONE", round(s, 3)))
            continue
        co = claimants[j]
        # does old i split across several new senses? (i is top-old for >=2 new)
        splits = [nj for nj in new_ns
                  if best_old_for_new[nj][0] == i and best_old_for_new[nj][1] >= threshold]
        if len(splits) >= 2:
            for nj in splits:
                rows.append((i, nj, "SPLIT", round(_ratio(old[i], new[nj]), 3)))
                matched_new.add(nj)
            continue
        if len(co) >= 2:
            rows.append((i, j, "MERGED", round(s, 3)))
            matched_new.add(j)
            continue
        matched_new.add(j)
        status = "SAME" if (i == j and old[i] == new[j]) else "MOVED"
        if status == "MOVED":
            rows.append((i, j, "MOVED", round(s, 3)))
    # new senses nobody matched -> NEW
    for j in new_ns:
        if j not in matched_new and best_old_for_new[j][1] < threshold:
            rows.append((None, j, "NEW", round(best_old_for_new[j][1], 3)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--threshold", type=float, default=0.6)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    old = load_archive(args.old)
    new = load_archive(args.new)
    out = Path(args.out) if args.out else (
        archive_db_path(args.new).parent.parent / f"sense_crosswalk_{args.old}__{args.new}.tsv")
    out.parent.mkdir(parents=True, exist_ok=True)

    per_dict = defaultdict(int)
    n_rows = 0
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write("dict\tL\told_sense_n\tnew_sense_n\tstatus\tsimilarity\n")
        # entries in old (citation source). Entries only in new can't break an
        # old citation, so they are not renumbering events for existing cites.
        keys = sorted(set(old) | set(new))
        for (dic, L) in keys:
            o = old.get((dic, L), {})
            n = new.get((dic, L), {})
            if not n:  # entry gone entirely -> every old sense GONE
                rows = [(i, None, "GONE", 0.0) for i in sorted(o)]
            elif not o:
                continue  # brand-new entry, no old citation to track
            else:
                rows = diff_entry(o, n, args.threshold)
            for (on, nn, status, sim) in rows:
                f.write(f"{dic}\t{L}\t{'' if on is None else on}\t"
                        f"{'' if nn is None else nn}\t{status}\t{sim}\n")
                per_dict[dic] += 1
                n_rows += 1
    print(f"[crosswalk] {args.old} -> {args.new}: {n_rows} changed senses -> {out}")
    for d in sorted(per_dict):
        print(f"    {d}: {per_dict[d]} renumbered/changed senses")


if __name__ == "__main__":
    main()
