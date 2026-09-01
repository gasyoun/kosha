"""Freeze the public-tier slice of data/manifest/datasets.json for one data release.

Why this exists (H3788). The DOI-archived data releases do not carry the
authoritative manifest. `data-v0.5.0`'s `datasets.json` asset is a 5-row,
`manifest_version` 0.1.0, checksum-free file with no `generated` stamp, while
the in-repo manifest at that moment held 114 rows at schema 0.2.0. A citer who
follows the DOI to the frozen manifest therefore gets something that is neither
the manifest nor a documented subset of it. Every release asset so far was
assembled by hand, which is how the drift got in.

This script makes the frozen manifest a build product instead:

  freeze   Select the rows whose `in_release` equals the given tag, hard-filter
           to `tier == public`, compute a sha256 for every asset whose
           `source_path` resolves locally, and write one self-describing
           document that names the tag, the git commit it was cut from, and the
           concept DOI. That file is the release asset.

  check    Re-run the selection against the current repo manifest and diff it
           against an existing frozen file. Non-zero exit on drift, so CI or a
           release gate can refuse a stale asset.

The public-tier filter is a fence, not a convenience: `tier == restricted` rows
are rights-encumbered (LGPLLR Heritage gloss text, unpublished corpora) and a
release asset is a publication. The script refuses to emit rather than silently
dropping such a row, so a mis-tiered entry fails loudly.

Usage:
    python scripts/freeze_release_manifest.py freeze --tag data-v0.5.0 \
        --out data/manifest/frozen/data-v0.5.0.datasets.json
    python scripts/freeze_release_manifest.py check --tag data-v0.5.0 \
        --frozen data/manifest/frozen/data-v0.5.0.datasets.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from manifest_paths import detect_github_root, local_path_for, repo_url_to_local

REPO = Path(__file__).resolve().parent.parent
DATASETS_JSON = REPO / "data" / "manifest" / "datasets.json"
GITHUB_ROOT = detect_github_root(REPO)
REPO_URL_TO_LOCAL = repo_url_to_local(GITHUB_ROOT)

SCHEMA = "kosha-frozen-release-manifest-v1"
CONCEPT_DOI = "10.5281/zenodo.21965599"

# Fields carried into the frozen document. Deliberately narrower than the repo
# manifest: `consumers`, `consumer_candidates` and `rebuild` are working notes
# that change after the release is cut, and a frozen artifact that changes is
# not frozen.
CARRIED = (
    "id",
    "title",
    "tier",
    "in_release",
    "release_asset",
    "format",
    "rows",
    "size_bytes",
    "keying",
    "source_repo",
    "source_path",
    "builder",
    "data_statement",
    "notes",
)


def resolve(ds):
    return local_path_for(ds, REPO, REPO_URL_TO_LOCAL)


def sha256_of(path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_digest(path, fmt):
    """Digest and size of the LF-canonical form of a text dataset.

    `.gitattributes` declares `* text=auto eol=lf`, so the LF form is the
    repository's canonical byte sequence for every text asset. A Windows
    checkout made before that rule landed still holds CRLF in the working
    tree -- git does not renormalize existing files when `.gitattributes`
    changes -- and hashing those bytes yields a digest no compliant checkout
    can reproduce. H3788 found 28 manifest rows whose recorded size_bytes was
    exactly one byte per line larger than the canonical file, and three
    DOI-archived data releases whose assets were uploaded from that
    non-compliant checkout. Hashing the canonical form is what makes the
    digest verifiable by a citer on any platform.

    Returns (digest, size, had_crlf).
    """
    raw = path.read_bytes()
    if fmt in ("tsv", "csv", "jsonl", "json", "txt", "md") or b"\x00" not in raw[:8192]:
        canon = raw.replace(b"\r\n", b"\n")
        return hashlib.sha256(canon).hexdigest(), len(canon), canon != raw
    return hashlib.sha256(raw).hexdigest(), len(raw), False


def git_sha():
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def select(manifest, tag):
    """Rows belonging to `tag`, with the restricted-tier fence applied."""
    rows = [r for r in manifest["datasets"] if r.get("in_release") == tag]
    bad = [r.get("id") for r in rows if r.get("tier") != "public"]
    if bad:
        raise SystemExit(
            "REFUSING to freeze {}: {} row(s) are not tier=public -- {}.\n"
            "A release asset is a publication; fix the tier or the in_release "
            "field rather than letting this be dropped silently.".format(
                tag, len(bad), ", ".join(sorted(str(b) for b in bad))
            )
        )
    return rows


def build(manifest, tag, version_doi=None):
    rows = select(manifest, tag)
    frozen_rows = []
    crlf_rows = []
    for r in sorted(rows, key=lambda x: str(x.get("id"))):
        out = {k: r.get(k) for k in CARRIED if r.get(k) is not None}
        digest = r.get("sha256")
        source = "manifest" if digest else None
        path = resolve(r)
        if path is not None and path.is_file():
            digest, size, had_crlf = canonical_digest(path, r.get("format"))
            source = "computed"
            if had_crlf:
                crlf_rows.append(r.get("id"))
            # The manifest's size_bytes can lag the file; the frozen document
            # must describe the canonical bytes it hashed, not a stale stat.
            out["size_bytes"] = size
        out["sha256"] = digest
        out["sha256_source"] = source or "unavailable"
        out["sha256_form"] = "lf-canonical"
        frozen_rows.append(out)

    doc = {
        "schema": SCHEMA,
        "release_tag": tag,
        "frozen_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frozen_from_commit": git_sha(),
        "concept_doi": CONCEPT_DOI,
        "version_doi": version_doi,
        "hub": manifest.get("hub"),
        "license_public_tier": manifest.get("license_public_tier"),
        "source_manifest": "data/manifest/datasets.json",
        "source_manifest_version": manifest.get("manifest_version"),
        "note_for_citers": (
            "Frozen public-tier slice of the kosha dataset manifest for this "
            "release tag. tier=restricted rows are excluded by design and are "
            "not part of any published release; consult their source repo. "
            "sha256_source=computed means this file records a digest taken from "
            "the bytes on disk at freeze time; unavailable means the source was "
            "not resolvable locally and the digest is not asserted. Every digest "
            "is over the LF-canonical form of the file (sha256_form), so it is "
            "reproducible from any compliant checkout regardless of platform."
        ),
        "datasets": frozen_rows,
    }
    if crlf_rows:
        # Travels with the artifact on purpose. A frozen manifest cut past the
        # CRLF refusal is still digest-correct (digests are LF-canonical), but a
        # release asset uploaded from the same tree would NOT be, and a reader
        # months later has no other way to know which tree produced this file.
        doc["checkout_warnings"] = {
            "crlf_working_tree_rows": sorted(crlf_rows),
            "meaning": (
                "These source files held CRLF in the checkout this manifest was "
                "cut from. The recorded sha256 values are LF-canonical and remain "
                "correct, but any release asset uploaded from that same tree "
                "carries one extra byte per line and will not match them."
            ),
        }
    return doc, crlf_rows


def cmd_freeze(args):
    manifest = json.loads(DATASETS_JSON.read_text(encoding="utf-8"))
    doc, crlf_rows = build(manifest, args.tag, args.version_doi)
    if not doc["datasets"]:
        raise SystemExit(
            "No manifest rows carry in_release={!r}; nothing to freeze.".format(args.tag)
        )
    if crlf_rows and not args.allow_crlf_checkout:
        raise SystemExit(
            "REFUSING to freeze {}: {} source file(s) hold CRLF in this working "
            "tree -- {}.\nThis checkout predates `.gitattributes` (`* text=auto "
            "eol=lf`); git does not renormalize existing files when that rule "
            "lands. Assets uploaded from here carry one extra byte per line and "
            "no compliant checkout can reproduce their digest (H3788). Fix with:\n"
            "    git add --renormalize .\n"
            "or cut the release from a fresh clone/worktree. Pass "
            "--allow-crlf-checkout only to inspect, never to publish.".format(
                args.tag, len(crlf_rows), ", ".join(sorted(crlf_rows))
            )
        )
    text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    if args.out == "-":
        sys.stdout.write(text)
    else:
        out = Path(args.out)
        if not out.is_absolute():
            out = REPO / out
        out.parent.mkdir(parents=True, exist_ok=True)
        # LF explicitly -- a frozen manifest whose own bytes differ by platform
        # would reproduce the defect this script exists to prevent.
        with out.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("Wrote {} row(s) for {} to {}".format(len(doc["datasets"]), args.tag, out))
    hashed = sum(1 for r in doc["datasets"] if r.get("sha256_source") == "computed")
    print("  sha256 computed from disk: {}/{}".format(hashed, len(doc["datasets"])))
    return 0


def cmd_check(args):
    frozen_path = Path(args.frozen)
    if not frozen_path.is_absolute():
        frozen_path = REPO / frozen_path
    if not frozen_path.is_file():
        print("MISSING frozen manifest: {}".format(frozen_path))
        return 1
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    manifest = json.loads(DATASETS_JSON.read_text(encoding="utf-8"))
    tag = args.tag or frozen.get("release_tag")
    current, _crlf = build(manifest, tag)

    was = {r["id"]: r for r in frozen.get("datasets", [])}
    now = {r["id"]: r for r in current["datasets"]}
    problems = []
    for missing in sorted(set(was) - set(now)):
        problems.append("dropped from the manifest: {}".format(missing))
    for added in sorted(set(now) - set(was)):
        problems.append("added to the manifest, absent from the frozen file: {}".format(added))
    for key in sorted(set(was) & set(now)):
        for field in ("release_asset", "rows", "size_bytes", "sha256"):
            a, b = was[key].get(field), now[key].get(field)
            # An unavailable digest never contradicts a recorded one -- the
            # sibling checkout simply is not present on this box.
            if field == "sha256" and (a is None or b is None):
                continue
            if a != b:
                problems.append("{}: {} {!r} -> {!r}".format(key, field, a, b))

    if problems:
        print("DRIFT between {} and the current manifest ({} issue(s)):".format(frozen_path.name, len(problems)))
        for p in problems:
            print("  - {}".format(p))
        return 1
    print("OK -- {} matches the current manifest for {} ({} rows).".format(frozen_path.name, tag, len(now)))
    return 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="mode", required=True)

    f = sub.add_parser("freeze", help="write the frozen manifest for a release tag")
    f.add_argument("--tag", required=True, help="e.g. data-v0.5.0")
    f.add_argument("--out", default="-", help="output path, or - for stdout")
    f.add_argument("--version-doi", default=None, help="Zenodo version DOI for this tag, if minted")
    f.add_argument(
        "--allow-crlf-checkout",
        action="store_true",
        help="inspect-only escape past the CRLF working-tree refusal; never use to publish",
    )
    f.set_defaults(func=cmd_freeze)

    c = sub.add_parser("check", help="verify a frozen manifest against the repo manifest")
    c.add_argument("--frozen", required=True)
    c.add_argument("--tag", default=None, help="defaults to the frozen file's release_tag")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
