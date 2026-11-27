#!/usr/bin/env python3
"""Front-matter byte-0 gate for wiki/ content files (H4092-class, 28-11-2026).

Repeated mistake this gate makes impossible: a mechanical byline/header
stamping sweep prepends `_Created: ..._` / `_Dr. ..._` lines ABOVE the
opening `---` of a YAML front-matter block. Front-matter parsers require
the delimiter at byte 0, so the parse comes back EMPTY while the file
still reads as perfectly normal Markdown — the docs-site generator
(scripts/build_docs_site.py -> zettelkastenwiki) then loses
title/slug/seo fields and the published pages degrade silently.

Prior occurrences (evidence for the class):
  * kosha PR #529 / fix f525e52a8 (05-09-2026): H4092 wave3 stamped
    `_Created:` headers above the front-matter of 5 wiki/*.md files;
    the generator parse broke; 12-file repair + docs-site regen.
  * kosha PR #530 / fix aa8114e3b (05-09-2026): the identical mis-stamp
    repeated the same day on the les1990 branch; 5-file repair + regen.
  * Same class org-wide: Veche/Uprava FINDINGS §1544 (ORS-FAQ 49/133
    content-invariant reds, csl-guides slug 404) and §721
    (IndologyScholars frozen-manifest hashes + anonymity copy).

Wired fail-closed at BOTH boundaries: .githooks/pre-commit (commit) and
Python CI (merge — main is branch-protected with this workflow required).
Selftest with positive/negative controls: tests/test_frontmatter_byte0_gate.py.

Usage:
  python scripts/check_frontmatter_byte0.py             # scan wiki/ (CI)
  python scripts/check_frontmatter_byte0.py wiki/a.md   # check given files
  python scripts/check_frontmatter_byte0.py --root DIR [files...]

Exit codes: 0 = clean; 1 = refusal (bad shape found); 2 = usage error.
Fail-closed: a gated file that cannot be decoded is a refusal, not a skip.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_ROOT = REPO / "wiki"

# A displaced front-matter opener sits within a few lines of a prepended
# stamp; a `---` deeper in the file is a thematic break, not front-matter.
MAX_LOOKAHEAD = 12
# How far past the opener a closing `---` may sit.
MAX_BLOCK_LINES = 60

# One `key: value` line inside the block proves it is real YAML
# front-matter (not a pair of thematic-break rules).
KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*:\s*\S")

FIX = (
    "move the dated header/byline BELOW the closing `---` of the YAML "
    "front-matter (front-matter must start at byte 0 for "
    "scripts/build_docs_site.py -> zettelkastenwiki to parse it); "
    "H4092 wave3 broke exactly this shape, repaired in f525e52a8 + aa8114e3b"
)


def displaced_frontmatter(text: str) -> int | None:
    """Return the 1-based line of a YAML front-matter opener that is NOT
    at byte 0, else None.

    A file whose first line is `---` is well-formed front-matter. A file
    with no front-matter-shaped block at all (plain Markdown, byline in
    prose) is also fine — the H4092-class defect is specifically a block
    that exists but starts late.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() == "---":
        return None
    for i in range(1, min(len(lines), MAX_LOOKAHEAD)):
        if lines[i].strip() != "---":
            continue
        # Candidate opener at line i (0-based). Require a closing `---`
        # with at least one `key: value` line between them.
        limit = min(len(lines), i + MAX_BLOCK_LINES)
        for j in range(i + 1, limit):
            if lines[j].strip() == "---":
                if any(KEY_RE.match(lines[k]) for k in range(i + 1, j)):
                    return i + 1
                break  # empty/hr pair — not front-matter
    return None


def check_file(path: Path, root: Path) -> str | None:
    """Return the violation message for `path`, or None if it is clean."""
    try:
        rel = str(path.relative_to(root))
    except ValueError:
        return None  # outside the gated tree — not this gate's class
    if path.suffix.lower() != ".md" or not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return f"{rel}: unreadable/undecodable gated file ({exc}) — fail-closed"
    hit = displaced_frontmatter(text)
    if hit is None:
        return None
    return f"{rel}: YAML front-matter opens at line {hit}, not byte 0 — {FIX}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="gated tree to scan (default: repo wiki/)",
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="check only these files (pre-commit passes staged paths)",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    if args.files:
        targets = []
        for p in args.files:
            # Accept absolute paths, cwd-relative paths (pre-commit runs at
            # the repo top) and --root-relative paths (selftest fixtures).
            cands = [p] if p.is_absolute() else [Path.cwd() / p, root / p]
            chosen = next((c for c in cands if c.is_file()), cands[0])
            targets.append(chosen.resolve())
    else:
        targets = sorted(root.rglob("*.md"))

    violations = [msg for msg in (check_file(p, root) for p in targets) if msg]
    if violations:
        print("front-matter byte-0 gate: REFUSED", file=sys.stderr)
        for msg in violations:
            print(f"  {msg}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
