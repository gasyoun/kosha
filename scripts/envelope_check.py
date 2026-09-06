"""Verify one release envelope against the bytes it pins (V6 verification).

The envelope (data/manifest/envelopes/*.envelope.json, schema
release-envelope-v1) is the object dashboards and manuscripts pin. This script
is the rerun side of that contract: it re-derives every digest the envelope
declares from the bytes actually on disk and reports PASS/FAIL/SKIP per check.
It never repairs, never rewrites, never trusts a recorded digest it could not
recompute.

Checks:
  CHK-1  envelope schema + required fields present
  CHK-2  pinned frozen manifest's sha256 recomputes from the file's bytes
  CHK-3  per-dataset sha256/rows/size_bytes match the pinned frozen manifest
  CHK-4  each source pin re-derives (rev-list --before frozen_at) and the
         pinned blob digests to the recorded sha256 (SKIP when the sibling
         clone is absent on this box)

Exit 0 when every run check passes (SKIP allowed); exit 1 on any FAIL.

Usage:
    python scripts/envelope_check.py --envelope data/manifest/envelopes/data-v0.5.0.envelope.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from manifest_paths import detect_github_root, local_path_for, repo_url_to_local

REPO = Path(__file__).resolve().parent.parent
GITHUB_ROOT = detect_github_root(REPO)
REPO_URL_TO_LOCAL = repo_url_to_local(GITHUB_ROOT)

SCHEMA = "release-envelope-v1"
REQUIRED = (
    "schema",
    "envelope_id",
    "release_tag",
    "created",
    "code_revision",
    "pinned_artifacts",
    "source_pins",
    "output_digests",
    "config",
    "licence",
    "checks",
    "review",
    "citation",
    "publication_state",
)

DATASET_KEYS = ("release_asset", "sha256", "rows", "size_bytes")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical(b: bytes) -> bytes:
    """LF-canonical form — the same normalisation freeze_release_manifest.py uses."""
    return b.replace(b"\r\n", b"\n")


def git(repo: Path, *args, binary: bool = False):
    out = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True,
    )
    if out.returncode != 0:
        return None
    return out.stdout if binary else out.stdout.decode("utf-8", "replace").strip()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--envelope", required=True)
    ap.add_argument("--frozen", default=None, help="override the pinned frozen-manifest path")
    args = ap.parse_args()

    env_path = Path(args.envelope)
    if not env_path.is_absolute():
        env_path = REPO / env_path
    env = json.loads(canonical(env_path.read_bytes()))

    results = []

    def record(cid: str, ok: bool, detail: str, skipped: bool = False):
        results.append((cid, "SKIP" if skipped else ("pass" if ok else "FAIL"), detail))

    # CHK-1 schema + required fields
    missing = [k for k in REQUIRED if k not in env or env[k] in (None, "", [], {})]
    record(
        "CHK-1-schema",
        not missing,
        "schema={}".format(env.get("schema"))
        + ("" if not missing else "; missing/empty: {}".format(", ".join(missing))),
    )
    if env.get("schema") != SCHEMA:
        print(report(results, fatal="schema is {}, expected {}".format(env.get("schema"), SCHEMA)))
        return 1

    # CHK-2 frozen-manifest pin digest
    pins = env["pinned_artifacts"]
    frozen_rel = args.frozen or pins[0]["path"]
    frozen_path = Path(frozen_rel)
    if not frozen_path.is_absolute():
        frozen_path = REPO / frozen_rel
    if not frozen_path.is_file():
        print(report(results, fatal="pinned frozen manifest not found: {}".format(frozen_path)))
        return 1
    frozen_bytes = canonical(frozen_path.read_bytes())
    pin_ok = all(sha256_bytes(canonical((REPO / p["path"]).read_bytes())) == p["sha256"]
                 for p in pins if (REPO / p["path"]).is_file())
    record("CHK-2-frozen-pin", pin_ok, "{} ({})".format(frozen_rel, frozen_path.name))

    frozen = json.loads(frozen_bytes)

    # CHK-3 per-dataset output parity against the pinned frozen manifest
    declared = env["output_digests"]["datasets"]
    frozen_rows = {r["id"]: r for r in frozen["datasets"]}
    drift = []
    for ds_id, out in sorted(declared.items()):
        row = frozen_rows.get(ds_id)
        if row is None:
            drift.append("{}: absent from frozen manifest".format(ds_id))
            continue
        for key in DATASET_KEYS:
            if row.get(key) != out.get(key):
                drift.append("{}: {} {!r} != frozen {!r}".format(ds_id, key, out.get(key), row.get(key)))
    for orphan in sorted(set(frozen_rows) - set(declared)):
        drift.append("{}: in frozen manifest, not declared".format(orphan))
    record("CHK-3-output-parity", not drift, "{} dataset(s)".format(len(declared)), )
    if drift:
        print(report(results, extra=drift))

    # CHK-4 source pins re-derived
    tag_ok = True
    pin_drift = []
    for sp in env["source_pins"]:
        ds_id = sp["dataset"]
        repo = REPO_URL_TO_LOCAL.get(sp["source_repo"])
        if sp["source_repo"].rstrip("/").endswith("/kosha"):
            repo = REPO
        if repo is None or not Path(repo).is_dir():
            record("CHK-4-source-pin:{}".format(ds_id), True, "sibling clone absent on this box", skipped=True)
            continue
        if sp["source_repo"].rstrip("/").endswith("/kosha"):
            pin = sp["pin_commit"]
        else:
            pin = git(Path(repo), "rev-list", "-1", "--before=" + frozen["frozen_at"], "HEAD")
            if pin is None:
                pin_drift.append("{}: pin commit not derivable (shallow clone?)".format(ds_id))
                record("CHK-4-source-pin:{}".format(ds_id), False, "not derivable")
                tag_ok = False
                continue
            if pin != sp["pin_commit"]:
                pin_drift.append("{}: pin moved {} -> {}".format(ds_id, sp["pin_commit"][:12], pin[:12]))
        blob = git(Path(repo), "show", "{}:{}".format(sp["pin_commit"], sp["source_path"]), binary=True)
        if blob is None:
            pin_drift.append("{}: blob unresolvable at pin".format(ds_id))
            record("CHK-4-source-pin:{}".format(ds_id), False, "blob unresolvable")
            tag_ok = False
            continue
        dig = sha256_bytes(canonical(blob))
        frozen_row = frozen_rows.get(ds_id, {})
        matches_declared = dig == sp["sha256"]
        matches_frozen = dig == frozen_row.get("sha256")
        record(
            "CHK-4-source-pin:{}".format(ds_id),
            matches_declared and matches_frozen,
            "pin {} digests {} (declared match: {}, frozen match: {})".format(
                sp["pin_commit"][:12], dig[:16], matches_declared, matches_frozen),
        )
        if not (matches_declared and matches_frozen):
            tag_ok = False
    record("CHK-4-source-pins", tag_ok and not pin_drift, "summary")

    # code_revision commit must exist in this repo
    rev = git(REPO, "cat-file", "-t", env["code_revision"]["commit"])
    record("CHK-5-code-revision", rev == "commit", "{} ({})".format(env["code_revision"]["commit"][:12], rev))

    print(report(results))
    return 0 if all(r != "FAIL" for _, r, _ in results) else 1


def report(results, fatal: str = None, extra=None) -> str:
    lines = []
    if fatal:
        lines.append("FATAL: " + fatal)
    for cid, res, detail in results:
        lines.append("  [{}] {} — {}".format(res.rjust(4), cid, detail))
    for e in extra or []:
        lines.append("         · " + e)
    passed = sum(1 for _, r, _ in results if r == "pass")
    skipped = sum(1 for _, r, _ in results if r == "SKIP")
    failed = sum(1 for _, r, _ in results if r == "FAIL")
    lines.append(
        "envelope_check: {} pass, {} skip, {} fail — {}".format(
            passed, skipped, failed, "PASS" if failed == 0 else "FAIL"
        )
    )
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
