"""Regenerate `requirements.lock.txt` from the installed dependency closure.

W0B / D12 (H1944) wants a *committed* lock so a build is reproducible, but
`pip freeze` in this repo's dev environment would capture every unrelated
package on the machine. So the lock is computed instead: start from the
declared runtime dependencies in `pyproject.toml`, walk each installed
distribution's own `Requires-Dist` metadata, and pin exactly the closure —
nothing else.

Markers are evaluated for the *current* interpreter and platform, and the
header records both, because a Linux CI runner resolves a different closure
than this Windows workstation (`uvloop` vs none, for one). The lock is a
verified record of one resolved environment, not a cross-platform solver
output; CI installs from `requirements.txt` and verifies against this file
rather than the other way round.

    python scripts/gen_requirements_lock.py            # rewrite the lock
    python scripts/gen_requirements_lock.py --check    # exit 1 if stale
"""

from __future__ import annotations

import argparse
import platform
import sys
import tomllib
from importlib import metadata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
LOCK = ROOT / "requirements.lock.txt"

HEADER = """\
# kosha dependency lock — GENERATED, do not hand-edit.
# Regenerate: python scripts/gen_requirements_lock.py
#
# Closure of the runtime + test dependencies declared in pyproject.toml,
# computed from the {source} on:
#   python   {python}
#   platform {platform}
#
# Cross-platform note: environment markers are evaluated for the interpreter
# above, so a Linux runner may legitimately need extra wheels (uvloop and
# friends). CI installs requirements.txt and treats that difference as
# information — but it does NOT treat a pin contradicting pyproject.toml as
# information: `--audit` fails on that, and generation refuses to write it.
"""


def _requirement_names(raw: str) -> str:
    """Take the bare distribution name out of a `Requires-Dist` string."""
    name = raw.split(";", 1)[0].strip()
    for separator in ("[", "(", "=", "<", ">", "!", "~", " "):
        name = name.split(separator, 1)[0]
    return name.strip()


def _marker_holds(raw: str, extras: set[str]) -> bool:
    if ";" not in raw:
        return True
    marker = raw.split(";", 1)[1].strip()
    try:
        from packaging.markers import Marker
    except ImportError:  # packaging is a pip dependency; assume true without it
        return "extra ==" not in marker
    try:
        if "extra ==" in marker:
            return any(Marker(marker).evaluate({"extra": extra}) for extra in extras)
        return Marker(marker).evaluate()
    except Exception:
        return False


def closure(roots: list[str]) -> dict[str, str]:
    """Resolve `roots` to `{distribution: version}` over installed metadata."""
    seen: dict[str, str] = {}
    queue = [(_requirement_names(root), _extras(root)) for root in roots]
    while queue:
        name, extras = queue.pop()
        key = name.lower().replace("_", "-")
        if key in seen or not name:
            continue
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            print(f"  ! {name} is declared but not installed — omitted", file=sys.stderr)
            continue
        seen[key] = dist.version
        for requirement in dist.requires or []:
            if not _marker_holds(requirement, extras):
                continue
            queue.append((_requirement_names(requirement), _extras(requirement)))
    return seen


def _extras(raw: str) -> set[str]:
    if "[" not in raw:
        return set()
    inside = raw.split("[", 1)[1].split("]", 1)[0]
    return {part.strip() for part in inside.split(",") if part.strip()}


def violations(roots: list[str], pinned: dict[str, str]) -> list[str]:
    """Declared specifiers the closure does not satisfy.

    An environment lagging a declared floor is a fact about that machine — but
    *writing that fact into the committed lock* is the silent contradiction
    W0B exists to remove, and it is what happened: the first committed lock
    pinned `fastapi==0.136.1` under a declared `>=0.140.0` and `pytest==9.0.3`
    under `>=9.1.1`. Installing it produced a set the project's own metadata
    rejects, and a following `pip install -e .` simply upgraded past it, so the
    lock did not even hold. These are therefore fatal now (see `render`), and
    `--resolve` exists so a stale workstation is no longer a reason to ship one.
    """
    try:
        from packaging.requirements import Requirement
    except ImportError:
        return []
    out = []
    for raw in roots:
        try:
            requirement = Requirement(raw)
        except Exception:
            continue
        key = requirement.name.lower().replace("_", "-")
        version = pinned.get(key)
        if version and not requirement.specifier.contains(version, prereleases=True):
            out.append(f"{requirement.name}: declared {requirement.specifier}, locked {version}")
    return out


class LockContradiction(RuntimeError):
    """The closure contradicts what pyproject.toml declares."""


def declared_roots() -> list[str]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    project = data["project"]
    roots = list(project.get("dependencies", []))
    roots += project.get("optional-dependencies", {}).get("test", [])
    return roots


def read_pins(text: str) -> dict[str, str]:
    pins = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, _, version = line.split(";", 1)[0].strip().partition("==")
        pins[name.strip().lower().replace("_", "-")] = version.strip()
    return pins


def resolved_closure(roots: list[str]) -> dict[str, str]:
    """Ask pip to RESOLVE the roots instead of reading what is installed.

    Nothing is installed or downloaded into the environment: this is
    `pip install --dry-run --report`, so it works on a workstation whose
    packages lag the declared floors — which is precisely the situation that
    produced a contradictory lock.
    """
    import json
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "report.json"
        command = [sys.executable, "-m", "pip", "install", "--dry-run",
                   "--ignore-installed", "--quiet", "--report", str(report)]
        command += roots
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding="utf-8")
        if result.returncode != 0 or not report.exists():
            raise LockContradiction(
                "pip could not resolve the declared dependencies:\n"
                + (result.stderr or result.stdout))
        data = json.loads(report.read_text(encoding="utf-8"))
    return {
        item["metadata"]["name"].lower().replace("_", "-"): item["metadata"]["version"]
        for item in data["install"]
    }


def audit() -> list[str]:
    """Platform-independent checks on the COMMITTED lock.

    Deliberately not full-closure equality: a Linux runner legitimately
    resolves wheels a Windows workstation does not (uvloop and friends), so
    comparing whole closures across platforms would fail for honest reasons.
    What must hold everywhere is that each declared root is pinned and no pin
    contradicts its declared specifier.
    """
    if not LOCK.exists():
        return [f"{LOCK.name} does not exist"]
    pins = read_pins(LOCK.read_text(encoding="utf-8"))
    if not pins:
        return [f"{LOCK.name} pins nothing"]
    problems = []
    try:
        from packaging.requirements import Requirement
    except ImportError:
        return []
    for raw in declared_roots():
        requirement = Requirement(raw)
        key = requirement.name.lower().replace("_", "-")
        if key not in pins:
            problems.append(f"{requirement.name}: declared but not in the lock")
    problems += violations(declared_roots(), pins)
    return problems


def render(resolve: bool = True) -> str:
    roots = declared_roots()
    pinned = resolved_closure(roots) if resolve else closure(roots)
    problems = violations(roots, pinned)
    if problems:
        raise LockContradiction(
            "refusing to write a lock that contradicts pyproject.toml:\n  "
            + "\n  ".join(problems)
            + ("\n\nThe installed environment lags the declared floors. Use the "
               "default --resolve mode, which asks pip to resolve them without "
               "installing anything." if not resolve else "")
        )
    body = "".join(
        f"{name}=={version}\n" for name, version in sorted(pinned.items())
    )
    return HEADER.format(
        source="pip resolver (nothing installed)" if resolve else "installed closure",
        python=sys.version.split()[0],
        platform=f"{platform.system()} {platform.machine()}",
    ) + body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if the lock differs from a fresh render")
    parser.add_argument("--audit", action="store_true",
                        help="platform-independent checks on the committed lock")
    parser.add_argument("--from-installed", action="store_true",
                        help="pin what is installed here instead of resolving")
    args = parser.parse_args(argv)

    if args.audit:
        problems = audit()
        if problems:
            print("requirements.lock.txt disagrees with pyproject.toml:",
                  file=sys.stderr)
            for problem in problems:
                print(f"  ! {problem}", file=sys.stderr)
            return 1
        print("requirements.lock.txt agrees with pyproject.toml")
        return 0

    try:
        rendered = render(resolve=not args.from_installed)
    except LockContradiction as exc:
        print(f"{exc}", file=sys.stderr)
        return 1

    if args.check:
        current = LOCK.read_text(encoding="utf-8") if LOCK.exists() else ""
        # Compare pins only: the header carries interpreter/platform lines that
        # legitimately differ per machine.
        if _pins(current) != _pins(rendered):
            print("requirements.lock.txt is stale — rerun without --check", file=sys.stderr)
            return 1
        print("requirements.lock.txt matches a fresh render")
        return 0

    LOCK.write_text(rendered, encoding="utf-8")
    print(f"wrote {LOCK} ({len(_pins(rendered))} pinned distributions)")
    return 0


def _pins(text: str) -> list[str]:
    return sorted(
        line.strip() for line in text.splitlines()
        if line.strip() and not line.startswith("#")
    )


if __name__ == "__main__":
    raise SystemExit(main())
