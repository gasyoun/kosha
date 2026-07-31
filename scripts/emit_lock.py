"""Emit a cross-platform version lock from `pip install --dry-run --report` JSON.

Markers are recovered from the resolved graph itself: for every non-requested
distribution, collect the markers each parent attached to its requirement. If
EVERY path into a package carries the same marker, that marker is reproduced in
the lock (this is what keeps Windows-only pins like colorama from being
installed on Linux CI). If any path is unconditional, the pin is unconditional.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

try:  # packaging ships with pip's vendored deps and is a pytest dependency
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
except ImportError:  # pragma: no cover
    print("packaging is required", file=sys.stderr)
    raise

REPORT = Path(sys.argv[1])
OUT = Path(sys.argv[2])

report = json.loads(REPORT.read_text(encoding="utf-8"))
items = report["install"]

installed = {canonicalize_name(i["metadata"]["name"]): i for i in items}

# name -> set of markers seen on the edges leading to it ("" = unconditional)
edges: dict[str, set[str]] = {name: set() for name in installed}
for item in items:
    parent_extras = set(item.get("requested_extras") or [])
    for raw in item["metadata"].get("requires_dist") or []:
        try:
            req = Requirement(raw)
        except Exception:
            continue
        child = canonicalize_name(req.name)
        if child not in installed:
            continue
        marker = str(req.marker) if req.marker else ""
        # An extra-gated edge only exists if that extra was actually requested.
        if "extra ==" in marker:
            if not any(f'extra == "{e}"' in marker for e in parent_extras):
                continue
            # Strip the extra clause; keep any platform half of the marker.
            parts = [p.strip() for p in marker.split(" and ") if "extra ==" not in p]
            marker = " and ".join(parts)
        edges[child].add(marker)

rows = []
for name, item in sorted(installed.items()):
    meta = item["metadata"]
    dist = meta["name"]
    info = item.get("download_info", {})
    vcs = info.get("vcs_info")
    if vcs:
        commit = vcs.get("commit_id") or vcs.get("requested_revision") or ""
        url = info.get("url", "")
        pin = f"{dist} @ {vcs.get('vcs', 'git')}+{url}@{commit}"
        # `#subdirectory=` lives beside vcs_info, not inside the URL. Dropping
        # it produces a pin that resolves to the repo ROOT — which for
        # sanskrit-util has no pyproject.toml, so `pip install -r
        # requirements.lock` fails on a clean runner while looking correct here.
        subdirectory = info.get("subdirectory")
        if subdirectory:
            pin = f"{pin}#subdirectory={subdirectory}"
    else:
        pin = f"{dist}=={meta['version']}"

    if item.get("requested"):
        marker = ""
    else:
        seen = edges.get(name, set())
        if not seen or "" in seen:
            # At least one unconditional path into this package.
            marker = ""
        elif len(seen) == 1:
            marker = next(iter(seen))
        else:
            # Several conditional paths: the package is needed when ANY of
            # them holds. (click and pytest reach colorama under two different
            # spellings of "on Windows"; the disjunction is the honest pin.)
            marker = " or ".join(f"({m})" for m in sorted(seen))
    if marker:
        pin = f"{pin} ; {marker}"
    rows.append(pin)

header = [
    "# kosha dependency lock (W0B / H1944) — GENERATED, do not hand-edit.",
    "#",
    "# Regenerate with:",
    "#   python -m pip install --dry-run --ignore-installed \\",
    "#       --report report.json -r requirements.txt",
    "#   python scripts/emit_lock.py report.json requirements.lock",
    "#",
    "# This is a VERSION lock, not a hash lock: `vidyut` ships platform-specific",
    "# wheels, so a single hash set cannot cover both the Windows dev machine and",
    "# the Linux CI runner. Exact versions are pinned; artefact integrity is left",
    "# to PyPI's own TLS + wheel checksums.",
    "#",
    "# Install with:  pip install -r requirements.lock",
    "",
]
OUT.write_text("\n".join(header + rows) + "\n", encoding="utf-8")
print(f"{len(rows)} pinned -> {OUT}")
for r in rows:
    print("  " + r)
