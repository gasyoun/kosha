"""W0B (H1944) — the packaging contract.

Three things drift silently if nothing pins them to each other:

* `pyproject.toml` dependencies vs `requirements.txt` (the flat file every
  runbook installs). A dep added to one and not the other means the installed
  package and the documented install differ.
* `requirements.lock` vs `requirements.txt` — a lock that no longer covers a
  declared requirement is worse than no lock, because it looks authoritative.
* `pyproject.toml` version vs `src/kosha/__init__.py` `__version__` vs
  `CITATION.cff`.

None of this needs a dictionary DB, so it all runs in CI.
"""
import re
import sys
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.fixture

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
REQUIREMENTS = ROOT / "requirements.txt"
LOCK = ROOT / "requirements.lock"


def _pyproject() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def _name(spec: str) -> str:
    """Distribution name from a requirement line, normalised PEP 503 style."""
    spec = spec.split(";", 1)[0].strip()
    spec = spec.split("@", 1)[0].strip()
    spec = re.split(r"[<>=!~\[]", spec, maxsplit=1)[0].strip()
    return re.sub(r"[-_.]+", "-", spec).lower()


def _requirements_lines() -> list[str]:
    lines = []
    for raw in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            lines.append(line)
    return lines


def _lock_lines() -> list[str]:
    lines = []
    for raw in LOCK.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip() if not raw.lstrip().startswith("#") else ""
        if line:
            lines.append(line)
    return lines


def test_pyproject_is_valid_toml():
    assert _pyproject()["project"]["name"] == "kosha"


def test_declared_deps_match_requirements_txt():
    project = _pyproject()["project"]
    declared = {_name(d) for d in project["dependencies"]}
    for extra in project.get("optional-dependencies", {}).values():
        declared |= {_name(d) for d in extra}
    flat = {_name(line) for line in _requirements_lines()}
    assert declared == flat, (
        "pyproject dependencies (incl. extras) and requirements.txt disagree: "
        f"only in pyproject={sorted(declared - flat)}, "
        f"only in requirements.txt={sorted(flat - declared)}"
    )


def test_lock_covers_every_declared_requirement():
    locked = {_name(line) for line in _lock_lines()}
    for line in _requirements_lines():
        assert _name(line) in locked, f"{line!r} is not in requirements.lock"


def test_lock_pins_exact_versions():
    for line in _lock_lines():
        assert "==" in line or " @ " in line, f"unpinned lock line: {line!r}"


def test_lock_vcs_pin_names_a_commit():
    vcs = [line for line in _lock_lines() if " @ " in line]
    assert vcs, "expected the zettelkastenwiki VCS pin in the lock"
    for line in vcs:
        url = line.split(" @ ", 1)[1].split(";", 1)[0].strip()
        base = url.split("#", 1)[0]
        assert re.search(r"@[0-9a-f]{40}$", base), (
            f"VCS pin must name a full commit sha, got {url!r}")


def test_vcs_pins_keep_their_subdirectory_fragment():
    """`#subdirectory=` lives beside `vcs_info` in pip's report, not in the URL.

    Dropping it yields a pin that resolves to the repository root — which for
    `sanskrit-util` has no `pyproject.toml`, so the lock installs cleanly
    nowhere while reading as correct. Compared against requirements.txt, which
    is where the fragment is authored.
    """
    def fragments(lines):
        out = {}
        for line in lines:
            if " @ " not in line:
                continue
            name = _name(line)
            url = line.split(" @ ", 1)[1].split(";", 1)[0].strip()
            _, _, fragment = url.partition("#")
            out[name] = fragment
        return out

    declared = fragments(_requirements_lines())
    locked = fragments(_lock_lines())
    for name, fragment in declared.items():
        assert name in locked, f"{name} VCS pin missing from the lock"
        assert locked[name] == fragment, (
            f"{name}: requirements.txt pins '#{fragment}', the lock has "
            f"'#{locked[name]}' — regenerate with scripts/emit_lock.py")


def test_version_is_consistent_across_metadata():
    version = _pyproject()["project"]["version"]

    sys.path.insert(0, str(ROOT / "src"))
    import kosha  # noqa: PLC0415

    assert kosha.__version__ == version

    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    cited = re.search(r"^version:\s*(\S+)\s*$", citation, re.M)
    assert cited, "CITATION.cff has no version field"
    assert cited.group(1) == version, (
        f"CITATION.cff says {cited.group(1)}, pyproject says {version}")


def test_src_layout_declared():
    tool = _pyproject()["tool"]["setuptools"]
    assert tool["package-dir"] == {"": "src"}
    assert tool["packages"]["find"]["where"] == ["src"]


def test_compatibility_entry_points_still_present():
    # `app/` and `scripts/` are NOT packaged on purpose — the runbooks call
    # them from the checkout. If they ever get swept into the wheel, the
    # import-time sys.path shims in app/__init__.py become wrong.
    assert (ROOT / "app" / "main.py").is_file()
    assert (ROOT / "scripts" / "build_db.py").is_file()
    packages = _pyproject()["tool"]["setuptools"]["packages"]["find"]
    assert "app" not in packages.get("include", ["*"]) or packages["where"] == ["src"]


def test_fixture_marker_is_registered():
    markers = _pyproject()["tool"]["pytest"]["ini_options"]["markers"]
    assert any(m.startswith("fixture:") for m in markers)


def test_lock_satisfies_every_declared_floor():
    """Dependabot bumps `requirements.txt`; it does not know about the lock.

    Without this, a bump raises a floor above what the lock pins and the two
    files quietly disagree about what "the dependency set" means — CI installs
    the lock and passes, a fresh `pip install -r requirements.txt` gets
    something else.
    """
    from packaging.requirements import Requirement
    from packaging.version import Version

    locked = {}
    for line in _lock_lines():
        if "==" not in line:
            continue
        spec = line.split(";", 1)[0].strip()
        name, _, version = spec.partition("==")
        locked[_name(name)] = Version(version.strip())

    for line in _requirements_lines():
        if " @ " in line or line.startswith("-"):
            continue  # VCS pins carry a commit, not a comparable version
        req = Requirement(line)
        pinned = locked.get(_name(req.name))
        assert pinned is not None, f"{req.name} is missing from requirements.lock"
        assert req.specifier.contains(pinned, prereleases=True), (
            f"requirements.txt wants {req.name}{req.specifier} but the lock "
            f"pins {pinned} — regenerate requirements.lock "
            f"(scripts/emit_lock.py)")


def test_required_ci_contexts_match_the_workflow_job_names():
    """The auto-merge gate names the checks it waits for as literal strings.

    Rename a job in python-ci.yml or ui-ci.yml and that gate silently starts
    waiting for a context that will never report — which, since a missing
    context is not SUCCESS, fails closed rather than open, but stops every
    dependency bump dead with no explanation. Pin them together.
    """
    workflows = ROOT / ".github" / "workflows"
    gate = (workflows / "dependabot-auto-merge.yml").read_text(encoding="utf-8")
    for workflow in ("python-ci.yml", "ui-ci.yml"):
        text = (workflows / workflow).read_text(encoding="utf-8")
        job_names = re.findall(r"^\s{4}name:\s*(.+)$", text, re.M)
        assert job_names, f"{workflow} declares no job name"
        for job_name in job_names:
            assert job_name.strip() in gate, (
                f"{workflow} job {job_name.strip()!r} is not among the contexts "
                f"dependabot-auto-merge.yml waits for")
