"""Shared sibling-repo resolution for the dataset manifest.

`data/manifest/datasets.json` stores `source_repo` (a GitHub URL) plus a
repo-relative `source_path`. Turning that pair into a real file needs the
local checkout root that holds the sibling repos.

Deriving that root as `REPO.parent` -- which both `update_manifest.py` and the
first cut of `freeze_release_manifest.py` did -- is correct only in the
canonical checkout `…/GitHub/kosha`. Inside a linked worktree the repo lives at
`…/Documents/kosha-h3788-<pid>`, so `REPO.parent` is `…/Documents`, no sibling
resolves, and every csl-orig / SanskritLexicography / csl-apidev row is silently
skipped: `refresh` reports no drift for them and `freeze` records
`sha256_source: unavailable`. Silently, because "path does not exist" is the
same branch as "gitignored, leave it alone".

Detection therefore probes candidate roots for a known sibling instead of
assuming one. `KOSHA_GITHUB_ROOT` overrides for unusual layouts.
"""

from __future__ import annotations

import os
from pathlib import Path

# Any one of these existing under a candidate proves it is the checkout root.
_MARKERS = ("csl-orig", "SanskritLexicography", "csl-apidev")


def detect_github_root(repo: Path) -> Path:
    """Best-guess local root holding the sibling repos, worktree-safe."""
    override = os.environ.get("KOSHA_GITHUB_ROOT")
    if override:
        return Path(override)
    candidates = [
        repo.parent,                    # canonical …/GitHub/kosha
        repo.parent / "GitHub",         # worktree at …/Documents/kosha-h####-<pid>
        repo.parent.parent / "GitHub",  # worktree one level deeper
    ]
    for cand in candidates:
        if any((cand / m).is_dir() for m in _MARKERS):
            return cand
    return repo.parent


def repo_url_to_local(github_root: Path) -> dict:
    return {
        "https://github.com/sanskrit-lexicon/csl-orig": github_root / "csl-orig",
        "https://github.com/sanskrit-lexicon/csl-apidev": github_root / "csl-apidev",
        "https://github.com/gasyoun/SanskritLexicography": github_root / "SanskritLexicography",
        "https://github.com/gasyoun/SanskritGrammar": github_root / "SanskritGrammar",
        "https://github.com/gasyoun/SanskritRussian": github_root / "SanskritRussian",
        "https://github.com/gasyoun/VisualDCS": github_root / "VisualDCS",
        "https://github.com/gasyoun/SamudraManthanam": github_root / "SamudraManthanam",
    }


def local_path_for(ds: dict, repo: Path, mapping: dict):
    """Resolve one manifest row's source_path to a real path, or None.

    kosha's own rows resolve against `repo` -- which inside a worktree must be
    the worktree, not the canonical checkout, so a freeze describes the tree it
    was cut from.
    """
    source_repo = ds.get("source_repo")
    if source_repo == "https://github.com/gasyoun/kosha":
        base = repo
    else:
        base = mapping.get(source_repo)
    if base is None:
        return None
    raw = ds.get("source_path") or ""
    # strip inline parenthetical annotations e.g. "(GITIGNORED — ...)"
    rel = raw.split(" (")[0].strip()
    if not rel:
        return None
    return base / rel
