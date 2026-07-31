"""kosha build sources — every external input, resolved and digested.

W0B item 4/5 (H1944). Before this module the build stages each hard-coded
their feed paths as module-level constants (`UNION_HEADWORDS`, `DCS_F2L`,
`CORPUS_LEXICON`, …). That made three things impossible:

- **prerequisite checking** — a missing feed surfaced as a `SystemExit` in the
  middle of a half-built database rather than before the first write;
- **source locking** — nothing recorded *which bytes* a database was built
  from, so a rebuilt feed silently changed the output;
- **fixtures** — no way to point the same graph at a compact public pack.

So each feed is declared once here, with the builder-module attribute it
overrides. The DAG resolves and digests every source a stage declares, then
injects the resolved path into the builder module before calling it. The
builders keep working unchanged when called directly (their constants stay as
defaults), which is D11's compatibility requirement.

Rights note (D18): every source declared here is either a sibling repo already
cloned locally or a file inside this repo. Nothing here fetches restricted
bytes, and an uncertain rights status on a feed never blocks the build — a
missing *optional* source is logged and skipped, not escalated.
"""

from __future__ import annotations

import hashlib
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _github_root(start: Path = ROOT) -> Path:
    """The `GitHub/` directory holding the sibling repos.

    `ROOT.parent` is right for a normal checkout but wrong for a worktree
    nested under `kosha/.claude/worktrees/<name>/`, so probe upward for a
    known sibling — the same trick `scripts/build_db.py` already uses.
    """
    for candidate in (start, *start.parents):
        if (candidate / "SanskritLexicography").is_dir():
            return candidate
    return start.parent


SIBLING = _github_root()


@dataclass(frozen=True)
class Source:
    """One declared build input.

    `targets` are `(module_name, attribute)` pairs the DAG rewrites before it
    calls a builder, so a fixture profile can redirect a feed without editing
    the builder. `env` names the override read from the environment.
    """

    name: str
    default: Path
    targets: tuple[tuple[str, str], ...] = ()
    env: str | None = None
    required: bool = True
    #: Directory sources are digested over their sorted file list.
    is_dir: bool = False
    note: str = ""

    def resolve(self, env: dict[str, str] | None = None) -> Path:
        env = os.environ if env is None else env
        if self.env and env.get(self.env):
            raw = Path(env[self.env]).expanduser()
            return raw if raw.is_absolute() else ROOT / raw
        return self.default


_HEADWORDS = SIBLING / "SanskritLexicography" / "HeadwordLists"
_RU = SIBLING / "SanskritLexicography" / "RussianTranslation"

#: Declared inputs, keyed by logical name.
SOURCES: dict[str, Source] = {
    "union_headwords": Source(
        "union_headwords",
        _HEADWORDS / "union" / "union_headwords.tsv",
        (("build_db", "UNION_HEADWORDS"),),
        env="KOSHA_SRC_UNION_HEADWORDS",
        note="sibling SanskritLexicography — the lemma spine (D1)",
    ),
    "lemma_frequency": Source(
        "lemma_frequency",
        ROOT / "data" / "frequency" / "lemma_frequency.tsv",
        (("build_db", "FREQ_TSV"),),
        env="KOSHA_SRC_LEMMA_FREQUENCY",
        note="in-repo DCS frequency sidecar",
    ),
    "heritage_crosswalk": Source(
        "heritage_crosswalk",
        _HEADWORDS / "mw_heritage_crosswalk.tsv",
        (("build_db", "HERITAGE_CROSSWALK"),),
        env="KOSHA_SRC_HERITAGE_CROSSWALK",
        note="H345 MW↔Heritage coverage witness",
    ),
    "csl_sqlite_cache": Source(
        "csl_sqlite_cache",
        ROOT / "data" / "raw_sqlite",
        (("build_entries", "DL_DIR"),),
        env="KOSHA_SRC_CSL_SQLITE",
        is_dir=True,
        note=(
            "csl-sqlite release extract, one <dict>/<dict>.sqlite per dict. "
            "Populated by `build_entries.fetch_release_sqlite` at a PINNED "
            "release tag; a release build refuses the 'latest' alias."
        ),
    ),
    "dcs_form2lemma": Source(
        "dcs_form2lemma",
        SIBLING / "SanskritRussian" / "dcs_form2lemma.tsv",
        (("build_forms", "DCS_F2L"),),
        env="KOSHA_SRC_DCS_FORM2LEMMA",
    ),
    "vidyut_form2lemma": Source(
        "vidyut_form2lemma",
        SIBLING / "SanskritRussian" / "vidyut_form2lemma.tsv",
        (("build_forms", "VIDYUT_F2L"),),
        env="KOSHA_SRC_VIDYUT_FORM2LEMMA",
    ),
    "heritage_forms": Source(
        "heritage_forms",
        _HEADWORDS / "heritage_only_forms.tsv",
        (("build_forms", "HERITAGE_F2L"),),
        env="KOSHA_SRC_HERITAGE_FORMS",
    ),
    "mwinflect_nominals": Source(
        "mwinflect_nominals",
        SIBLING / "MWinflect" / "nominals" / "pysanskritv2" / "tables" / "calc_tables.txt",
        (("build_inflections", "DEFAULT_CALC_TABLES"),),
        env="KOSHA_SRC_MWINFLECT_NOMINALS",
        # Required *by the builder* (it exits when the table is missing) even
        # though the `inflections` stage itself is optional: absence skips the
        # stage, it does not let the stage run half-fed. The two flags answer
        # different questions — "can the builder cope?" vs "can the build?".
        note="generated MWinflect table; absent on most dev machines",
    ),
    "mwinflect_verbs": Source(
        "mwinflect_verbs",
        SIBLING / "MWinflect" / "verbs" / "pysanskritv2" / "tables" / "calc_tables.txt",
        (("build_inflections", "DEFAULT_VERB_TABLES"),),
        env="KOSHA_SRC_MWINFLECT_VERBS",
        required=False,
    ),
    "gita_morphology_gold": Source(
        "gita_morphology_gold",
        ROOT / "data" / "gita" / "gita_morphology_gold.tsv",
        (("build_pronoun_corrections", "GOLD"),),
        env="KOSHA_SRC_GITA_GOLD",
    ),
    "corpus_lexicon": Source(
        "corpus_lexicon",
        _RU / "src" / "corpus_lexicon.jsonl",
        (("build_evidence", "CORPUS_LEXICON"),),
        env="KOSHA_SRC_CORPUS_LEXICON",
        required=False,
        note="P3 evidence examples; large sibling feed, optional",
    ),
    # The three layer feeds below are `required` for the same reason as
    # mwinflect_nominals: `build_db_layers` exits on a missing file rather
    # than skipping it. Only mw_roots/mw_etymology degrade gracefully.
    "sense_frequency": Source(
        "sense_frequency",
        ROOT / "data" / "frequency" / "sense_frequency.tsv",
        (("build_db_layers", "SENSE_FREQ_TSV"),),
        env="KOSHA_SRC_SENSE_FREQUENCY",
    ),
    "roots_frequency": Source(
        "roots_frequency",
        ROOT / "data" / "roots" / "roots_frequency.tsv",
        (("build_db_layers", "ROOTS_FREQ_TSV"),),
        env="KOSHA_SRC_ROOTS_FREQUENCY",
    ),
    "dict_corpus_coverage": Source(
        "dict_corpus_coverage",
        ROOT / "data" / "concordance" / "dict_corpus_coverage.tsv",
        (("build_db_layers", "DICT_COVERAGE_TSV"),),
        env="KOSHA_SRC_DICT_CORPUS_COVERAGE",
    ),
    "mw_roots": Source(
        "mw_roots",
        SIBLING / "csl-orig" / "v02" / "mw" / "mw_roots.tsv",
        (("build_db_layers", "MW_ROOTS_TSV"),),
        env="KOSHA_SRC_MW_ROOTS",
        required=False,
        note="sibling csl-orig; optional layer feed",
    ),
    "mw_etymology": Source(
        "mw_etymology",
        SIBLING / "csl-orig" / "v02" / "mw" / "mw_etymology.tsv",
        (("build_db_layers", "MW_ETYMOLOGY_TSV"),),
        env="KOSHA_SRC_MW_ETYMOLOGY",
        required=False,
        note="sibling csl-orig; optional layer feed",
    ),
}


@dataclass
class ResolvedSource:
    """A source after path resolution and digesting."""

    name: str
    path: Path
    exists: bool
    required: bool
    sha256: str | None = None
    bytes: int | None = None
    files: int | None = None
    members: dict[str, str] = field(default_factory=dict)

    def as_lock_entry(self) -> dict:
        entry = {
            "path": str(self.path),
            "exists": self.exists,
            "required": self.required,
        }
        if self.sha256:
            entry["sha256"] = self.sha256
        if self.bytes is not None:
            entry["bytes"] = self.bytes
        if self.files is not None:
            entry["files"] = self.files
        if self.members:
            entry["members"] = self.members
        return entry


def _digest_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def _digest_dir(path: Path) -> tuple[str, int, int, dict[str, str]]:
    """Digest a directory as the hash of its sorted `relpath:filehash` list.

    Order-independent and mtime-independent, so two machines that fetched the
    same csl-sqlite release lock to the same value.
    """
    members: dict[str, str] = {}
    total = 0
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        digest, size = _digest_file(file)
        members[file.relative_to(path).as_posix()] = digest
        total += size
    roll = hashlib.sha256()
    for rel, digest in sorted(members.items()):
        roll.update(f"{rel}:{digest}\n".encode())
    return roll.hexdigest(), total, len(members), members


def resolve(name: str, env: dict[str, str] | None = None) -> ResolvedSource:
    """Resolve one declared source and digest it when present."""
    spec = SOURCES[name]
    path = spec.resolve(env)
    if spec.is_dir:
        if not path.is_dir():
            return ResolvedSource(name, path, False, spec.required)
        digest, total, count, members = _digest_dir(path)
        return ResolvedSource(
            name, path, True, spec.required,
            sha256=digest, bytes=total, files=count, members=members,
        )
    if not path.is_file():
        return ResolvedSource(name, path, False, spec.required)
    digest, size = _digest_file(path)
    return ResolvedSource(name, path, True, spec.required, sha256=digest, bytes=size)


@contextmanager
def injected(resolved: dict, modules: dict[str, object]):
    """Point every resolved source at its builder module, then restore.

    The restore matters: builder modules are imported once per process, so a
    permanent rewrite would leak one build's source paths (a fixture pack, a
    release checkout) into every later caller in the same interpreter.
    """
    saved: list[tuple[object, str, object]] = []
    try:
        for name, source in resolved.items():
            if not source.exists:
                continue
            for module_name, attribute in SOURCES[name].targets:
                module = modules.get(module_name)
                if module is None:
                    continue
                saved.append((module, attribute, getattr(module, attribute, None)))
                setattr(module, attribute, source.path)
        yield
    finally:
        for module, attribute, previous in reversed(saved):
            setattr(module, attribute, previous)


def inject(name: str, path: Path, modules: dict[str, object]) -> list[str]:
    """Point a builder module's path constant at the resolved source.

    Returns the `module.ATTR` names actually rewritten, so the caller can log
    exactly what the graph redirected. Modules that are not imported (a stage
    that will not run) are skipped rather than force-imported.
    """
    rewritten = []
    for module_name, attribute in SOURCES[name].targets:
        module = modules.get(module_name)
        if module is None:
            continue
        setattr(module, attribute, path)
        rewritten.append(f"{module_name}.{attribute}")
    return rewritten
