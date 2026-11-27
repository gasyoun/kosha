"""Selftest for scripts/check_frontmatter_byte0.py (H4092-class gate).

Positive controls prove the gate REFUSES the real past mistake (exit 1),
including the byte-exact shape the H4092 wave3 stamping pass wrote to
wiki/docs/roadmap.md before the f525e52a8 / aa8114e3b repairs. Negative
controls prove every legal shape still passes (exit 0). Exit codes are
asserted, not just output text.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts" / "check_frontmatter_byte0.py"

# git show f8bca1186:wiki/docs/roadmap.md — the file as the H4092 wave3
# stamping pass left it (header ABOVE the front-matter, blank line between).
HISTORICAL_STAMPED = (
    "_Created: 03-07-2026 \u00b7 Last updated: 05-09-2026_\n"
    "\n"
    "---\n"
    "title: Roadmap \u2014 phases P1\u2013P7\n"
    "slug: roadmap\n"
    "---\n"
    "\n"
    "# Roadmap\n"
    "Body text.\n"
)

# The post-repair shape (f525e52a8): front-matter at byte 0, stamps below.
GOOD_FRONTMATTER = (
    "---\n"
    "title: Roadmap \u2014 phases P1\u2013P7\n"
    "slug: roadmap\n"
    "---\n"
    "\n"
    "_Created: 03-07-2026 \u00b7 Last updated: 28-11-2026_\n"
    "\n"
    "# Roadmap\n"
    "Body text.\n"
)

# Plain doc with the byline in prose and no front-matter: legal — the
# gate targets displacement, not the stamps themselves.
PLAIN_WITH_BYLINE = (
    "# Plain doc\n"
    "\n"
    "_Created: 03-07-2026 \u00b7 Last updated: 28-11-2026_\n"
    "\n"
    "Body. No front-matter block, byline in prose is fine.\n"
)


def run_gate(*args: object, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GATE), *[str(a) for a in args]],
        capture_output=True,
        text=True,
        cwd=str(cwd or ROOT),
        check=False,
    )


def write(root: Path, rel: str, content: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------- positive


def test_refuses_the_real_h4092_wave3_shape(tmp_path: Path) -> None:
    """The exact pre-fix shape of wiki/docs/roadmap.md must be refused."""
    bad = write(tmp_path, "docs/roadmap.md", HISTORICAL_STAMPED)
    result = run_gate("--root", tmp_path, bad)
    assert result.returncode == 1, result.stderr
    assert "byte 0" in result.stderr
    assert "docs/roadmap.md" in result.stderr
    assert "f525e52a8" in result.stderr  # error names the fix + precedent


def test_refuses_stamp_glued_directly_above_delimiter(tmp_path: Path) -> None:
    """No blank line between stamp and `---` — still the broken shape."""
    glued = (
        "_Dr. M\u0101rcis Gas\u016bns_\n"
        "---\n"
        "title: x\n"
        "slug: x\n"
        "---\n"
        "\n"
        "Body.\n"
    )
    bad = write(tmp_path, "faq/data-licensing.md", glued)
    result = run_gate("--root", tmp_path, bad)
    assert result.returncode == 1, result.stderr
    assert "faq/data-licensing.md" in result.stderr


def test_scan_mode_reports_only_the_bad_file(tmp_path: Path) -> None:
    write(tmp_path, "docs/good.md", GOOD_FRONTMATTER)
    write(tmp_path, "docs/bad.md", HISTORICAL_STAMPED)
    result = run_gate("--root", tmp_path)
    assert result.returncode == 1, result.stderr
    assert "docs/bad.md" in result.stderr
    assert "docs/good.md" not in result.stderr


def test_fail_closed_on_undecodable_file(tmp_path: Path) -> None:
    bad = tmp_path / "docs" / "broken.md"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_bytes(b"\xff\xfe garbage \n---\ntitle: x\n---\n")
    result = run_gate("--root", tmp_path)
    assert result.returncode == 1, result.stderr
    assert "fail-closed" in result.stderr


# ---------------------------------------------------------------- negative


def test_byte0_frontmatter_with_stamps_below_passes(tmp_path: Path) -> None:
    good = write(tmp_path, "docs/roadmap.md", GOOD_FRONTMATTER)
    result = run_gate("--root", tmp_path, good)
    assert result.returncode == 0, result.stderr


def test_plain_byline_doc_without_frontmatter_passes(tmp_path: Path) -> None:
    plain = write(tmp_path, "docs/plain.md", PLAIN_WITH_BYLINE)
    result = run_gate("--root", tmp_path, plain)
    assert result.returncode == 0, result.stderr


def test_thematic_break_rules_are_not_frontmatter(tmp_path: Path) -> None:
    """Two `---` hr lines deep in prose must not trip the gate."""
    doc = (
        "# Doc\n"
        "\n"
        "_Created: 03-07-2026 \u00b7 Last updated: 28-11-2026_\n"
        "\n"
        "Intro.\n"
        "\n"
        "---\n"
        "\n"
        "Section one.\n"
        "\n"
        "---\n"
        "\n"
        "Section two.\n"
    )
    ok = write(tmp_path, "docs/hr.md", doc)
    result = run_gate("--root", tmp_path, ok)
    assert result.returncode == 0, result.stderr


def test_path_outside_the_gated_root_is_skipped(tmp_path: Path) -> None:
    """A file outside wiki/ is not this gate's class — exit 0."""
    outside = tmp_path / "notes.md"
    outside.write_text(HISTORICAL_STAMPED, encoding="utf-8")
    empty_root = tmp_path / "wiki"
    empty_root.mkdir()
    result = run_gate("--root", empty_root, outside)
    assert result.returncode == 0, result.stderr


def test_repo_wiki_tree_is_clean() -> None:
    """Repo-scope negative control: the committed wiki/ passes the scan
    (this also runs in CI, proving the merge-boundary gate is green)."""
    result = run_gate()
    assert result.returncode == 0, result.stderr
