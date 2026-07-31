"""The committed lock must not contradict what `pyproject.toml` declares.

W0B (H1944) shipped `requirements.lock.txt` generated from the *installed*
closure of one workstation. That workstation lagged the declared floors, so the
committed lock pinned `fastapi==0.136.1` under `fastapi>=0.140.0`,
`uvicorn==0.46.0` under `>=0.51.0`, and `pytest==9.0.3` under `>=9.1.1`. The
generator printed a note to stderr and wrote the file anyway; the artifact
carried no trace of it. Installing that lock produced a set the project's own
metadata rejects — and a following `pip install -e .` upgraded straight past
it, so the lock did not even hold.

Nothing could see it: CI installed `requirements.txt` and separately asserted
that the lock file contained the characters `==`.

The invariants pinned here are the ones that hold on **every** platform, which
is why they can be a required check while full-closure equality cannot: a Linux
runner legitimately resolves wheels a Windows workstation does not.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import gen_requirements_lock as gen  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "requirements.lock.txt"


def test_lock_exists_and_pins_something():
    assert LOCK.is_file()
    assert gen.read_pins(LOCK.read_text(encoding="utf-8"))


def test_committed_lock_agrees_with_pyproject():
    problems = gen.audit()
    assert problems == [], "\n".join(problems)


def test_every_declared_root_is_pinned():
    from packaging.requirements import Requirement

    pins = gen.read_pins(LOCK.read_text(encoding="utf-8"))
    for raw in gen.declared_roots():
        name = Requirement(raw).name.lower().replace("_", "-")
        assert name in pins, f"{name} is declared but not locked"


def test_no_pin_falls_below_its_declared_floor():
    pins = gen.read_pins(LOCK.read_text(encoding="utf-8"))
    assert gen.violations(gen.declared_roots(), pins) == []


def test_violations_names_the_contradiction():
    problems = gen.violations(["fastapi>=0.140.0"], {"fastapi": "0.136.1"})
    assert problems and "declared >=0.140.0" in problems[0]
    assert "locked 0.136.1" in problems[0]


def test_generation_refuses_to_write_a_contradictory_lock(monkeypatch):
    """The shape that produced the first committed lock, made fatal.

    `--from-installed` against a floor the installed distribution cannot meet
    used to print a note and write the file. It now raises.
    """
    installed = gen.closure(["fastapi"])
    assert installed, "fastapi must be installed for this test to mean anything"
    impossible = "fastapi>=999.0.0"
    monkeypatch.setattr(gen, "declared_roots", lambda: [impossible])
    with pytest.raises(gen.LockContradiction) as exc:
        gen.render(resolve=False)
    assert "contradicts pyproject.toml" in str(exc.value)
    assert "fastapi" in str(exc.value)


def test_audit_exits_nonzero_on_a_contradictory_lock(tmp_path, monkeypatch):
    broken = tmp_path / "requirements.lock.txt"
    broken.write_text("fastapi==0.1.0\n", encoding="utf-8")
    monkeypatch.setattr(gen, "LOCK", broken)
    assert gen.audit(), "a lock pinning fastapi 0.1.0 must not audit clean"
    assert gen.main(["--audit"]) == 1


def test_audit_is_wired_into_ci():
    workflow = (ROOT / ".github" / "workflows" / "python-ci.yml").read_text(
        encoding="utf-8")
    assert "gen_requirements_lock.py --audit" in workflow, (
        "the lock check must be able to fail; asserting the file contains "
        "'==' is what let the contradictory lock through")


def test_audit_runs_clean_as_a_subprocess():
    """The same invocation CI makes, end to end."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "gen_requirements_lock.py"), "--audit"],
        capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    assert result.returncode == 0, result.stdout + result.stderr
