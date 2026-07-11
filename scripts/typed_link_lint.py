#!/usr/bin/env python
"""Lint a Type-D concordance dataset against TYPED_LINK_ID_GRAMMAR.md (H539).

Validates every row of a Type-D link TSV (TYPE_D_RECORD_FIELDS header) against
the cross-repo ID grammar: known grammar-anchor prefixes (spec §2), known
target-locus prefixes (spec §3), tail syntax per prefix, legal `link_type` /
`match_method` values, and a present `date` in DD-MM-YYYY. Exits non-zero with
one diagnostic line per bad row (RISKS-style: never a silent pass).

Usage:
    python typed_link_lint.py <dataset.tsv> [<dataset2.tsv> ...]
    python typed_link_lint.py --inventory anchors.txt:locus.txt <dataset.tsv>

--inventory ANCHOR_FILE:LOCUS_FILE (optional): each file one stable id per
line (anchor ids without prefix, e.g. '3983'; target-locus tails without
prefix, e.g. '1.1.6:668bbf5c1e18769f3d9aafc3'). When given, tails are also
checked for membership, not just syntax.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from concordance_core import TIER_CONFIDENCE, TYPE_D_LINK_TYPES, TYPE_D_RECORD_FIELDS  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

# TYPED_LINK_ID_GRAMMAR.md §2 — grammar-anchor namespace (the "from" side).
# Each entry: prefix -> compiled regex the TAIL (after the prefix) must match.
ANCHOR_PATTERNS = {
    "gra": re.compile(r"^\d+(\.\d+)?$"),                       # gra:3983, gra:5833.1 (homonym suffix)
    "whitney-root": re.compile(r"^\d+$"),                      # whitney-root:1
    "whitney-sec": re.compile(r"^\d+(-\d+)?$"),                # whitney-sec:611[-641]
    "root": re.compile(r"^[A-Za-z]+$"),                        # root:BU (SLP1)
    "sutra": re.compile(r"^\d+\.\d+\.\d+$"),                   # sutra:1.1.1
}
ANCHOR_TYPE_TO_PREFIX = {
    "id-gra": "gra",
    "whitney-root": "whitney-root",
    "whitney-sec": "whitney-sec",
    "root": "root",
    "panini-sutra": "sutra",
}

# TYPED_LINK_ID_GRAMMAR.md §3 — target-locus namespace (the "to" side).
TARGET_PATTERNS = {
    "dcs": re.compile(r"^.+$"),                                 # dcs:<sent_id>, opaque
    "vedaweb": re.compile(r"^\d+(\.\d+)*:[0-9a-fA-F]{24}$"),     # vedaweb:1.1.6:<ObjectId>
    "commentary": re.compile(r"^[\w-]+:.+$"),                    # commentary:<work>:<cite>
    "subject": re.compile(r"^[\w-]+:[\w.-]+$"),                  # subject:<index>:<category>
}

DATE_RE = re.compile(r"^\d{2}-\d{2}-\d{4}$")

MATCH_METHODS = set(TIER_CONFIDENCE.keys())


def split_prefix(value, known_prefixes):
    """'<prefix>:<tail>' -> (prefix, tail) if prefix is known, else (None, value)."""
    if ":" not in value:
        return None, value
    prefix, tail = value.split(":", 1)
    if prefix in known_prefixes:
        return prefix, tail
    return None, value


def load_inventory(spec):
    """'--inventory anchors.txt:locus.txt' -> (set(anchor tails), set(locus tails))."""
    anchor_path, locus_path = spec.split(":", 1)
    anchors = {ln.strip() for ln in Path(anchor_path).read_text(encoding="utf-8").splitlines() if ln.strip()}
    loci = {ln.strip() for ln in Path(locus_path).read_text(encoding="utf-8").splitlines() if ln.strip()}
    return anchors, loci


def lint_row(row, lineno, inventory=None):
    """-> list of diagnostic strings for this row (empty = clean)."""
    errs = []

    anchor_type = row.get("anchor_type", "")
    anchor_id = row.get("anchor_id", "")
    expected_prefix = ANCHOR_TYPE_TO_PREFIX.get(anchor_type)
    if expected_prefix is None:
        errs.append("unknown anchor_type %r (known: %s)" % (
            anchor_type, ", ".join(sorted(ANCHOR_TYPE_TO_PREFIX))))
    else:
        prefix, tail = split_prefix(anchor_id, ANCHOR_PATTERNS)
        if prefix is None:
            errs.append("anchor_id %r has no known prefix (expected %r:...)" % (anchor_id, expected_prefix))
        elif prefix != expected_prefix:
            errs.append("anchor_id %r prefix %r does not match anchor_type %r (expected %r:...)" % (
                anchor_id, prefix, anchor_type, expected_prefix))
        elif not ANCHOR_PATTERNS[prefix].match(tail):
            errs.append("anchor_id %r: tail %r fails %r syntax" % (anchor_id, tail, prefix))
        elif inventory and inventory[0] and tail not in inventory[0]:
            errs.append("anchor_id %r: tail %r not found in anchor inventory" % (anchor_id, tail))

    target_locus = row.get("target_locus", "")
    prefix, tail = split_prefix(target_locus, TARGET_PATTERNS)
    if prefix is None:
        errs.append("target_locus %r has no known prefix (known: %s)" % (
            target_locus, ", ".join(sorted(TARGET_PATTERNS))))
    elif not TARGET_PATTERNS[prefix].match(tail):
        errs.append("target_locus %r: tail %r fails %r syntax" % (target_locus, tail, prefix))
    elif inventory and inventory[1] and tail not in inventory[1]:
        errs.append("target_locus %r: tail %r not found in target-locus inventory" % (target_locus, tail))

    if target_locus.startswith(("http://", "https://", "www.")):
        errs.append("target_locus %r looks like a URL host — reuse the source's own stable id (spec §0)" % target_locus)

    link_type = row.get("link_type", "")
    if link_type not in TYPE_D_LINK_TYPES:
        errs.append("link_type %r not in %s" % (link_type, TYPE_D_LINK_TYPES))

    match_method = row.get("match_method", "")
    if match_method not in MATCH_METHODS:
        errs.append("match_method %r not in %s" % (match_method, sorted(MATCH_METHODS)))

    date = row.get("date", "")
    if not date:
        errs.append("date is missing")
    elif not DATE_RE.match(date):
        errs.append("date %r is not DD-MM-YYYY" % date)

    return ["line %d: %s" % (lineno, e) for e in errs]


def lint_file(path, inventory=None):
    diagnostics = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        missing = [c for c in TYPE_D_RECORD_FIELDS if c not in (reader.fieldnames or [])]
        if missing:
            return ["%s: missing required column(s): %s" % (path, ", ".join(missing))]
        for lineno, row in enumerate(reader, start=2):  # header is line 1
            diagnostics.extend(lint_row(row, lineno, inventory))
    return diagnostics


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("datasets", nargs="+", help="Type-D TSV dataset(s) to lint")
    ap.add_argument("--inventory", default=None,
                    help="ANCHOR_FILE:LOCUS_FILE — verify tails against a canonical inventory")
    args = ap.parse_args()

    inventory = load_inventory(args.inventory) if args.inventory else None

    total_errors = 0
    for ds in args.datasets:
        diags = lint_file(ds, inventory)
        if diags:
            print("%s: %d issue(s)" % (ds, len(diags)))
            for d in diags:
                print("  " + d)
            total_errors += len(diags)
        else:
            print("%s: OK" % ds)

    if total_errors:
        print("\ntyped_link_lint: %d issue(s) across %d file(s)" % (total_errors, len(args.datasets)))
        sys.exit(1)
    print("\ntyped_link_lint: all clean")


if __name__ == "__main__":
    main()
