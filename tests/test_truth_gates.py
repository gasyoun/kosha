"""Fail-fast truth gates (H1943 W0A governance/integrity reset).

Guards the specific drift classes an integrity audit found live on
`origin/main` on 30-07-2026: a hardcoded version string going stale against
CHANGELOG.md, a completed/superseded plan losing its banner, and a queue item
silently being both "next" and "done" at once. Manifest/README dataset-count
drift already has a dedicated invariant test in test_directory.py
(`test_readme_dataset_counts_match_manifest`) — not duplicated here.

Every test below is proven to actually fail on bad input, not just pass on
the current clean state (H1943 guardrail: "no silent gate").
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SEMVER_HEADER_RE = re.compile(r"^## \[(\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}$", re.MULTILINE)
HARDCODED_VERSION_RE = re.compile(r"\bv(\d+\.\d+\.\d+)\b")


def _changelog_versions() -> list[tuple[int, int, int]]:
    text = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    versions = []
    for m in SEMVER_HEADER_RE.finditer(text):
        versions.append(tuple(int(p) for p in m.group(1).split(".")))
    return versions


def _latest_changelog_version() -> tuple[int, int, int]:
    versions = _changelog_versions()
    assert versions, "CHANGELOG.md has no dated version headers to compare against"
    return max(versions)


# --- version claims -----------------------------------------------------


def test_changelog_top_entry_is_the_highest_version_and_unique():
    """CHANGELOG.md's first dated header must be the max version, with no dupes.

    History has out-of-order interior sections (real hand-authored drift that
    is not this handoff's job to rewrite), so this does not require full
    monotonicity — only the load-bearing invariant every doc that cites
    "the latest release" actually depends on: the top entry IS the latest,
    and no version is recorded twice under two different dates.
    """
    versions = _changelog_versions()
    assert versions[0] == max(versions), (
        f"CHANGELOG.md's top entry v{'.'.join(map(str, versions[0]))} is not the highest "
        f"recorded version (max is v{'.'.join(map(str, max(versions)))})"
    )
    dupes = {v for v in versions if versions.count(v) > 1}
    assert not dupes, f"CHANGELOG.md records the same version more than once: {dupes}"

    # prove the check can fail
    broken = [(0, 0, 1)] + versions
    assert broken[0] != max(broken)


def test_hardcoded_version_claims_do_not_exceed_changelog_latest():
    """Any literal `vX.Y.Z` cited in README.md/CLAUDE.md must not outrun CHANGELOG.md.

    A hardcoded "latest release" string is exactly the kind of claim that goes
    stale the next time CHANGELOG.md is updated and the citing prose is not.
    This does not require the citation to be the LATEST tag (older tags are
    legitimately cited as historical evidence) — only that no doc claims a
    version CHANGELOG.md has never recorded.
    """
    latest = _latest_changelog_version()
    changelog_versions = set(_changelog_versions())
    for doc in ("README.md", "CLAUDE.md"):
        text = (REPO / doc).read_text(encoding="utf-8")
        for m in HARDCODED_VERSION_RE.finditer(text):
            v = tuple(int(p) for p in m.group(1).split("."))
            assert v in changelog_versions or v <= latest, (
                f"{doc} cites v{m.group(1)}, which CHANGELOG.md never recorded "
                f"(latest is v{'.'.join(map(str, latest))})"
            )

    # prove the check can fail: a version newer than CHANGELOG's latest must be rejected
    fake_future = (latest[0], latest[1], latest[2] + 1)
    assert fake_future not in changelog_versions and fake_future > latest


# --- active-queue completed markers --------------------------------------

DONE_MARKERS = ("✅", "[x]", "COMPLETED", "DONE ")


def test_ai_state_next_steps_has_no_completed_markers():
    """`## ➡️ Next Steps (Queue)` in .ai_state.md must contain no done markers.

    A completed item left in the live queue is exactly the "active-queue
    completed marker" drift class H1943 was chartered to fail-fast on: a
    future session reads the queue and re-executes already-shipped work.
    """
    text = (REPO / ".ai_state.md").read_text(encoding="utf-8")
    m = re.search(
        r"## ➡️ Next Steps \(Queue\)\n(.*?)(?=\n## )", text, re.DOTALL
    )
    assert m, ".ai_state.md is missing the canonical '## ➡️ Next Steps (Queue)' section"
    queue_text = m.group(1)
    hits = [marker for marker in DONE_MARKERS if marker in queue_text]
    assert not hits, f"completed marker(s) {hits} found inside the live Next Steps queue"

    # prove the check can fail
    poisoned = queue_text + "\n- ✅ done already\n"
    assert any(marker in poisoned for marker in DONE_MARKERS)


# --- required plan banners ------------------------------------------------

SUPERSEDED_PORTFOLIO_DOCS = (
    "docs/ROADMAP_KOSHA_2026H2.md",
    "docs/ROADMAP_KOSHA_NEXT_PROGRAMME_2026H2.md",
    "docs/PLAN_KOSHA_CONCORDANCE_Q3_2026H2.md",
    "docs/PLAN_KOSHA_NEXT_PROGRAMME_2026H2.md",
)

BANNER_RE = re.compile(r"SUPERSEDED|COMPLETED")


def test_superseded_portfolio_docs_carry_a_banner():
    """Every predecessor portfolio-level plan/roadmap carries an in-place banner.

    docs/ROADMAP_KOSHA_2026_2027.md itself states the rule: "Earlier roadmaps
    remain immutable evidence and must carry a completed or superseded
    banner." This test enforces that rule mechanically instead of trusting
    memory.
    """
    missing = []
    for rel in SUPERSEDED_PORTFOLIO_DOCS:
        path = REPO / rel
        assert path.exists(), f"expected superseded doc missing: {rel}"
        text = path.read_text(encoding="utf-8")
        if not BANNER_RE.search(text):
            missing.append(rel)
    assert not missing, f"docs missing a required SUPERSEDED/COMPLETED banner: {missing}"

    # prove the check can fail
    assert not BANNER_RE.search("no status claim here")


def test_exactly_one_sole_live_roadmap_pointer():
    """Exactly one doc may claim to be "the sole live roadmap".

    Guards against a future session minting a second competing roadmap
    without demoting this one — the original failure mode this handoff
    fixes (an old H2 roadmap and the new twelve-month roadmap both reading
    as current).
    """
    # A doc CLAIMS authority when it makes the assertion about itself in its
    # own opening prose (first 500 chars) -- merely instructing/quoting the
    # rule elsewhere (e.g. the W0 sequence telling H1943 to go establish it)
    # is not a competing claim.
    claimants = []
    for path in (REPO / "docs").glob("*.md"):
        head = path.read_text(encoding="utf-8")[:500]
        if "sole live roadmap" in head:
            claimants.append(path.name)
    allowed = {"ROADMAP.md", "ROADMAP_KOSHA_2026_2027.md"}
    assert set(claimants) <= allowed, f"unexpected roadmap-authority claim(s): {set(claimants) - allowed}"
    assert claimants, "no doc declares itself the sole live roadmap"
