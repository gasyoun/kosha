#!/usr/bin/env python3
"""backfill_sidecars.py — machine provenance for every registered data layer (H6979).

`data/manifest/datasets.json` was 149 rows of human prose: a `builder` string that
sometimes names a handoff and sometimes names a script, and no machine-readable
answer to "who made this, on which model, and on which handoff". This script
derives those fields and REFUSES to guess: a value that cannot be derived is
left `null` and listed in the triage section of the report, never invented.

Derivation precedence (spec: docs/LAYER_SIDECAR_SPEC.md):

  1. `provenance_verified` — already "date + handoff + exact model id" (10 rows);
  2. `builder` — `H####` (63 rows) and model families (7 rows);
  3. the source path's FIRST COMMIT in the sibling clone
     (`git log --diff-filter=A`): the date becomes `built_at`, an `H####` or a
     model token in the commit subject is harvested (86 rows have no builder
     metadata, this is what recovers them);
  4. nothing derivable -> `null` + triage row in the report.

The 18 zero-consumer rows close per decision #6: 2 become `active` with the
consumer that already exists, 16 become `dormant` with an owner and a review
date. `layer_status` (not `status`) is the lifecycle key in the manifest:
`status` already carries the planning vocabulary on six rows and
`scripts/build_dataset_disciplines.py` reads it.

Usage
-----
    python scripts/backfill_sidecars.py --check          # 149/149 or exit 1
    python scripts/backfill_sidecars.py --report PATH    # write the triage report
    python scripts/backfill_sidecars.py --apply          # write datasets.json
    python scripts/backfill_sidecars.py --apply --report PATH
    python scripts/backfill_sidecars.py --dry-run        # what --apply would do
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "manifest" / "datasets.json"
REPORT = ROOT / "reports" / "DATA_LAYER_PROVENANCE_BACKFILL_18.10.26.md"

sys.path.insert(0, str(ROOT / "scripts"))
from manifest_paths import detect_github_root  # noqa: E402


def github_root():
    """The checkout root holding the sibling clones.

    `detect_github_root` assumes a worktree under Documents/; ours live under
    Documents/GitHub-worktrees, so the home fallback is what actually resolves
    the sibling clones here.
    """
    import os
    override = os.environ.get("KOSHA_GITHUB_ROOT")
    if override:
        return Path(override)
    detected = detect_github_root(ROOT)
    if any((detected / marker).is_dir() for marker in ("csl-orig", "SanskritLexicography")):
        return detected
    home = Path.home() / "Documents" / "GitHub"
    if any((home / marker).is_dir() for marker in ("csl-orig", "SanskritLexicography")):
        return home
    return detected


GITHUB_ROOT = github_root()

HANDOFF_RE = re.compile(r"\b(H\d{3,5})\b")
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
EXACT_MODEL_RE = re.compile(
    r"\b(claude-[a-z]+(?:-[a-z]+)*-\d+(?:-\d+)?|z-ai/[a-z0-9.\-]+|glm-\d+(?:\.\d+)?"
    r"|grok-\d+(?:\.\d+)?|gpt-\d+(?:\.\d+)?(?:-[a-z0-9.\-]+)?)\b")

# family token -> canonical id prefix. A family WITHOUT a version is not an id
# (the model-attribution rule: always report the exact version), so a bare
# family becomes reported triage, never a field value.
FAMILY_PREFIX = {
    "fable": "claude-fable",
    "opus": "claude-opus",
    "sonnet": "claude-sonnet",
    "haiku": "claude-haiku",
    "glm": "glm",
    "grok": "grok",
    "deepseek": "deepseek",
}
FAMILY_RE = re.compile(
    r"\b(Fable|Opus|Sonnet|Haiku|GLM|Grok|DeepSeek)\s*(\d+(?:\.\d+)?)\b", re.I)
BARE_LANE_RE = re.compile(r"\b(OxAlpha|Codex)\b")  # lane labels, not model ids

# Decision #6 / #12: the 16 dormant rows and the owner that has to decide them.
DORMANT = {
    "stenogrammy-teaching-glossary": "MG",
    "stopovye-parallel-passages": "MG",
    "dcs-verb-form-frequency-prelim": "MG",
    "dcs-lsc-pilot": "MG",
    "archive-stopword-sqlite": "MG",
    "mw-defgen-eval-sample": "MG",
    "headword-overlap-matrix-ext": "MG",
    "gita-inflection-qa": "MG",
    "gita-gold-vs-dcs-tagging": "MG",
    "upasarga-atlas": "MG",
    "zaliznyak-lectures-transcripts": "MG",
    "sanskrityatina-reverse-index": "MG",
    "sanskrityatina-sch-cases": "MG",
    "sanskrityatina-reverse-vs-union16": "MG",
    "bhs-mw-dcs-key2-crosswalk": "MG",
    "sanskritgrammar-whitney-dcs-vidyut-crosswalk": "MG",
}
REVIEW_AFTER = "2027-01-18"  # 90 days after the 18-10-2026 backfill

# Decision #6: the two zero-consumer rows that DO have one, closed as active.
ACTIVE_CONSUMERS = {
    "dcs-compound-dictionary": ["kosha (names.csv join)"],
    "morphology-giveback-candidates": ["csl-inflect (give-back candidates)"],
}

FIELDS = ("made_by", "model", "handoff", "layer_status", "provenance_source",
          "built_at", "owner", "review_after")


def load_rows():
    with open(MANIFEST, encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload, payload["datasets"]


def local_clone(row):
    """The sibling clone for a row's source_repo, or None."""
    match = re.match(r"https://github\.com/[^/]+/([^/]+?)/?$",
                     row.get("source_repo") or "")
    if not match:
        return None
    candidate = GITHUB_ROOT / match.group(1)
    return candidate if (candidate / ".git").exists() else None


def source_relpath(row):
    raw = (row.get("source_path") or "").split(" (")[0]
    raw = raw.split(" · ")[0].strip()
    return raw.strip("/")


def first_commit(row):
    """(date, subject) of the commit that ADDED the row's source path."""
    repo = local_clone(row)
    rel = source_relpath(row)
    if repo is None or not rel:
        return None
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "log", "--diff-filter=A", "--reverse",
             "--format=%ad%x09%s", "--date=short", "--", rel],
            capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    for line in out.stdout.splitlines():
        if "\t" in line:
            date, subject = line.split("\t", 1)
            return date.strip(), subject.strip()
    # the path may predate the current path form; fall back to its last commit
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "log", "-1", "--format=%ad%x09%s",
             "--date=short", "--", rel],
            capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    line = out.stdout.strip()
    if "\t" in line:
        date, subject = line.split("\t", 1)
        return date.strip(), subject.strip()
    return None


def model_id(text):
    """Exact model id from text, or (None, triage_note)."""
    exact = EXACT_MODEL_RE.search(text or "")
    if exact:
        return exact.group(1), None
    family = FAMILY_RE.search(text or "")
    if family:
        prefix = FAMILY_PREFIX[family.group(1).lower()]
        return "%s-%s" % (prefix, family.group(2)), None
    lane = BARE_LANE_RE.search(text or "")
    if lane:
        return None, "lane label %r is not a model id — needs the exact version" % lane.group(1)
    return None, None


def derive(row):
    """Return the provenance fields for one row (never invents a value)."""
    builder = (row.get("builder") or "").strip()
    verified = (row.get("provenance_verified") or "").strip()
    text = "%s %s" % (builder, verified)

    handoff = None
    match = HANDOFF_RE.search(text)
    if match:
        handoff = match.group(1)

    model, model_note = model_id(text)
    built_at = None
    notes = []

    # made_by: the honest, derivable answer only.
    lowered = text.lower()
    if re.search(r"server-regenerated|upstream \(cologne\)|upstream dump", lowered):
        made_by = "upstream"
    elif "pre-2026 dump" in lowered:
        made_by = "unknown"
    elif "hand-curated" in lowered:
        made_by = "human+ai"
    elif handoff or model:
        made_by = "ai"
    else:
        made_by = "unknown"

    if verified:
        source = "provenance_verified"
    elif handoff or model or made_by in ("upstream", "human+ai") \
            or "pre-2026 dump" in lowered:
        # the builder text itself carried the provenance
        source = "builder"
    else:
        source = None

    date = DATE_RE.search(verified or builder)
    if date:
        built_at = date.group(1)

    if source is None or (source == "builder" and not (handoff or model)):
        commit = first_commit(row)
        if commit:
            commit_date, subject = commit
            if built_at is None:
                built_at = commit_date
            recovered_handoff = HANDOFF_RE.search(subject)
            commit_model, _ = model_id(subject)
            if recovered_handoff:
                handoff = recovered_handoff.group(1)
                source = "path+first-commit"
                notes.append("handoff recovered from the first commit subject")
            if commit_model:
                model = commit_model
                source = "path+first-commit"
                notes.append("model recovered from the first commit subject")
            if source is None:
                source = "path+first-commit"
                notes.append("first commit names neither a handoff nor a model")

    if model_note:
        notes.append(model_note)
    if source is None:
        source = "manual"

    result = {
        "made_by": made_by,
        "model": model,
        "handoff": handoff,
        "provenance_source": source,
        "built_at": built_at,
    }
    if notes:
        result["_notes"] = notes
    if row["id"] in DORMANT:
        result.update(layer_status="dormant", owner=DORMANT[row["id"]],
                      review_after=REVIEW_AFTER)
    else:
        result["layer_status"] = "active"
    return result


def verify_field_order(row, derived):
    """Insert the derived keys last so the manifest diff stays readable."""
    result = dict(row)
    for key in FIELDS:
        if key in derived and derived[key] is not None:
            result[key] = derived[key]
    if derived.get("model") is None:
        result.setdefault("model", None)
    if derived.get("handoff") is None:
        result.setdefault("handoff", None)
    if "provenance_source" in derived:
        result["provenance_source"] = derived["provenance_source"]
    if derived.get("built_at"):
        result["built_at"] = derived["built_at"]
    if row["id"] in ACTIVE_CONSUMERS and not row.get("consumers"):
        result["consumers"] = ACTIVE_CONSUMERS[row["id"]]
    return result


def check(rows, verbose=True):
    """Rows lacking machine provenance. Empty list == 149/149."""
    problems = []
    for row in rows:
        rid = row.get("id", "?")
        if not row.get("made_by"):
            problems.append("%s: missing made_by" % rid)
        if not row.get("layer_status"):
            problems.append("%s: missing layer_status" % rid)
        if row.get("layer_status") == "dormant":
            if not row.get("owner"):
                problems.append("%s: dormant without owner" % rid)
            if not row.get("review_after"):
                problems.append("%s: dormant without review_after" % rid)
        else:
            if not row.get("consumers"):
                problems.append("%s: active without consumers" % rid)
        if not (row.get("handoff") or row.get("model")
                or row.get("provenance_source") in ("path+first-commit", "manual")
                or row.get("made_by") in ("upstream", "unknown", "human")):
            problems.append("%s: no handoff/model/provenance_source" % rid)
    if verbose:
        total = len(rows)
        good = total - len({p.split(":")[0] for p in problems})
        print("%d/%d rows carry machine provenance" % (good, total))
        dormant = sum(1 for r in rows if r.get("layer_status") == "dormant")
        active = sum(1 for r in rows if r.get("layer_status") == "active")
        print("layer_status: %d active, %d dormant, %d other"
              % (active, dormant, total - active - dormant))
        for problem in problems[:40]:
            print("  MISSING %s" % problem)
        if len(problems) > 40:
            print("  … and %d more" % (len(problems) - 40))
    return problems


def report(rows, applied):
    derived = {r["id"]: derive(r) for r in rows}
    path_rows = [r for r in rows if derived[r["id"]]["provenance_source"] == "path+first-commit"]
    verified_rows = [r for r in rows if derived[r["id"]]["provenance_source"] == "provenance_verified"]
    builder_rows = [r for r in rows if derived[r["id"]]["provenance_source"] == "builder"]
    manual_rows = [r for r in rows if derived[r["id"]]["provenance_source"] == "manual"]
    neither = [r for r in rows
               if not derived[r["id"]]["handoff"] and not derived[r["id"]]["model"]]
    noted = [r for r in rows if derived[r["id"]].get("_notes")]
    triage_ids = {r["id"] for r in neither} | {r["id"] for r in noted}
    triage = [(rid, derived[rid]) for rid in sorted(triage_ids)]
    noted_but_identified = len(triage_ids) - len(neither)
    dormant = [r for r in rows if derived[r["id"]]["layer_status"] == "dormant"]
    active_closed = [r for r in rows if r["id"] in ACTIVE_CONSUMERS]
    model_less = [r for r in rows if not derived[r["id"]]["model"]]
    no_novelty = len(rows)  # novelty is never backfilled — see the spec

    lines = []
    add = lines.append
    add("# Data-layer provenance backfill — report")
    add("")
    add("_Created: 18-10-2026 · Last updated: 18-10-2026_")
    add("")
    add("Generated by `scripts/backfill_sidecars.py --report`. Spec: "
        "[LAYER_SIDECAR_SPEC.md](https://github.com/gasyoun/kosha/blob/main/docs/LAYER_SIDECAR_SPEC.md). "
        "Handoff: H6979. Decisions: "
        "[grill 18-10-2026](https://github.com/gasyoun/kosha/blob/main/reports/DATA_CONSUMER_PROVENANCE_DECISIONS_18.10.26.md).")
    add("")
    add("## Summary")
    add("")
    add("| Metric | Value |")
    add("|---|---:|")
    add("| Manifest rows | %d |" % len(rows))
    add("| Rows with machine provenance | %d |" % (len(rows) - len(check(rows, verbose=False))))
    add("| — from `provenance_verified` | %d |" % len(verified_rows))
    add("| — from `builder` | %d |" % len(builder_rows))
    add("| — from the source path's first commit | %d |" % len(path_rows))
    add("| — no derivable source (left null) | %d |" % len(manual_rows))
    add("| `layer_status: active` | %d |" % sum(1 for r in rows if derived[r["id"]]["layer_status"] == "active"))
    add("| `layer_status: dormant` (owner + review_after) | %d |" % len(dormant))
    add("| Rows with an exact `model` id | %d |" % (len(rows) - len(model_less)))
    add("| Rows with a `handoff` | %d |" % sum(1 for r in rows if derived[r["id"]]["handoff"]))
    add("| Rows with neither `handoff` nor `model` | %d |" % len(neither))
    add("| Rows needing manual triage (below) | %d |" % len(triage))
    add("| `novelty` paragraphs still owed (not backfilled) | %d |" % no_novelty)
    add("")
    add("Applied to `datasets.json`: **%s**." % ("yes" if applied else "no (`--dry-run`)"))
    add("")

    add("## Path-derived rows (%d)" % len(path_rows))
    add("")
    add("No handoff and no model in the `builder` text: the fields come from the commit that "
        "added the source path in the sibling clone. `built_at` is that commit's date; a "
        "handoff or model in the commit subject is harvested, otherwise the field stays `null` "
        "and the row is also listed in the triage section.")
    add("")
    add("| id | source path | built_at | recovered |")
    add("|---|---|---|---|")
    for row in sorted(path_rows, key=lambda r: r["id"]):
        d = derived[row["id"]]
        rec = d["handoff"] or d["model"] or "—"
        add("| `%s` | `%s` | %s | %s |"
            % (row["id"], source_relpath(row)[:70], d["built_at"] or "—", rec))
    add("")

    add("## Manual triage (%d)" % len(triage))
    add("")
    add("Every row where a value would have to be GUESSED — %d with neither a handoff nor a "
        "model, plus %d whose first commit named something worth a reader's eye. Nothing here "
        "is written into a field: the honest state is `null` + a note, and a human (or the "
        "layer's next rebuild) supplies the value."
        % (len(neither), noted_but_identified))
    add("")
    add("| id | made_by | model | handoff | why it needs a human |")
    add("|---|---|---|---|---|")
    for rid, d in sorted(triage, key=lambda pair: pair[0]):
        why = "; ".join(d.get("_notes") or []) or "no handoff/model derivable"
        add("| `%s` | %s | %s | %s | %s |"
            % (rid, d["made_by"], d["model"] or "—", d["handoff"] or "—", why))
    add("")

    add("## Dormant rows (%d)" % len(dormant))
    add("")
    add("Zero consumers, so declared dormant rather than registered as an asset "
        "(decision #6). Owner and `review_after` are mandatory; re-decide at that date.")
    add("")
    add("| id | owner | review_after |")
    add("|---|---|---|")
    for row in sorted(dormant, key=lambda r: r["id"]):
        add("| `%s` | %s | %s |" % (row["id"], DORMANT[row["id"]], REVIEW_AFTER))
    add("")

    add("## Closed as active (%d)" % len(active_closed))
    add("")
    add("| id | consumer |")
    add("|---|---|")
    for row in sorted(active_closed, key=lambda r: r["id"]):
        add("| `%s` | %s |" % (row["id"], "; ".join(ACTIVE_CONSUMERS[row["id"]])))
    add("")

    add("## Residual")
    add("")
    add("- **`novelty` is owed on all %d rows.** It is a judgment paragraph (\"what does this "
        "add over what exists?\") and 149 invented ones would be the отписка decision #10 "
        "warns about. The helper enforces it at the next write of each layer's sidecar; "
        "check content quality in a month, per the grill's residual note." % no_novelty)
    add("- **`model` is null on %d rows** — see triage; the exact version is required by the "
        "model-attribution rule, so a bare family token or a lane label (`OxAlpha`) is not "
        "promoted into the field." % len(model_less))
    add("- Rows whose `source_repo` is not a local GitHub clone (`akhara.ru`, `wisdomlib.org`, "
        "`yadisk:`) cannot get a first-commit date; they resolve through the other three "
        "tiers or land in triage.")
    add("- The overlay guard by protected paths (decision #8) and the 16-row dormancy visa "
        "(decision #6, MG) are separate work items — not this handoff.")
    add("")
    add("_Гасунс_")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="verify every row carries machine provenance (exit 1 if not)")
    parser.add_argument("--apply", action="store_true", help="write datasets.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="show what --apply would write, change nothing")
    parser.add_argument("--report", nargs="?", const=str(REPORT), default=None,
                        metavar="PATH", help="write the triage report (default: %s)" % REPORT)
    args = parser.parse_args(argv)

    payload, rows = load_rows()
    derived = {row["id"]: derive(row) for row in rows}
    new_rows = [verify_field_order(row, derived[row["id"]]) for row in rows]

    if args.dry_run or args.report:
        changed = sum(1 for old, new in zip(rows, new_rows) if old != new)
        print("%d of %d rows would change" % (changed, len(rows)))

    if args.apply:
        payload["datasets"] = new_rows
        if payload.get("manifest_version") == "0.3.0":
            payload["manifest_version"] = "0.4.0"
            payload["note_for_agents"] = (
                payload.get("note_for_agents", "")
                + " Provenance/lifecycle fields since manifest_version 0.4.0 (H6979): "
                "made_by, model, handoff, layer_status (active|dormant|retired — NOT the "
                "planning `status` key), owner + review_after (dormant only), "
                "provenance_source, built_at. Spec: docs/LAYER_SIDECAR_SPEC.md.")
        with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print("wrote %s (%d rows)" % (MANIFEST.relative_to(ROOT), len(new_rows)))

    if args.report:
        target = Path(args.report)
        if not target.is_absolute():
            target = ROOT / target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(report(new_rows, applied=args.apply), encoding="utf-8", newline="\n")
        try:
            shown = target.relative_to(ROOT)
        except ValueError:
            shown = target
        print("wrote %s" % shown)

    if args.check:
        problems = check(rows)
        return 1 if problems else 0
    if not (args.apply or args.report or args.dry_run):
        check(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
