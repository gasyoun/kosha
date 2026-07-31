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
# resolved on:
#   python   {python}
#   platform {platform}
#
# Cross-platform note: environment markers are evaluated for the interpreter
# above, so a Linux runner may legitimately need extra wheels (uvloop and
# friends). CI installs requirements.txt and treats a difference here as
# information, not a failure.
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
    """Declared specifiers the *installed* closure does not satisfy.

    Reported rather than raised: an environment lagging a declared floor is a
    fact about this machine, and hiding it inside a generated file is exactly
    the kind of silent contradiction W0B exists to remove.
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
            out.append(f"{requirement.name}: declared {requirement.specifier}, installed {version}")
    return out


def render() -> str:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    project = data["project"]
    roots = list(project.get("dependencies", []))
    roots += project.get("optional-dependencies", {}).get("test", [])
    pinned = closure(roots)
    for problem in violations(roots, pinned):
        print(f"  ! declared/installed drift — {problem}", file=sys.stderr)
    body = "".join(
        f"{name}=={version}\n" for name, version in sorted(pinned.items())
    )
    return HEADER.format(
        python=sys.version.split()[0],
        platform=f"{platform.system()} {platform.machine()}",
    ) + body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the lock is stale")
    args = parser.parse_args(argv)

    rendered = render()
    if args.check:
        current = LOCK.read_text(encoding="utf-8") if LOCK.exists() else ""
        # Compare pins only: the header carries interpreter/platform lines that
        # legitimately differ per machine.
        if _pins(current) != _pins(rendered):
            print("requirements.lock.txt is stale — rerun without --check", file=sys.stderr)
            return 1
        print("requirements.lock.txt matches the installed closure")
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
