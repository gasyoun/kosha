#!/usr/bin/env python3
"""Local deployment rehearsal against fixture data (W1D / H2344).

1. Ensures the fixture DB exists (builds it if missing).
2. Assembles a fixture-profile deploy bundle with digests.
3. Boots uvicorn against that fixture on 127.0.0.1 (ephemeral port).
4. Probes GET /health and GET /ready; optional lemma smoke.
5. Tears down the server.

Never contacts production. Never reads .env.deploy. Exit 0 only when every
gate passes.

Usage:
    python scripts/rehearse_deploy.py
    python scripts/rehearse_deploy.py --skip-assemble
    python scripts/rehearse_deploy.py --port 8765
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _http_get(url: str, timeout: float = 5.0) -> tuple[int, str]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return int(resp.status), body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return int(e.code), body


def ensure_fixture_db() -> Path:
    fixture = REPO_ROOT / "data" / "db" / "kosha_fixture.db"
    if fixture.is_file() and fixture.stat().st_size > 0:
        print(f"fixture db present: {fixture} ({fixture.stat().st_size} bytes)")
        return fixture
    print("fixture db missing — building with --profile fixture …")
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "build_db.py"), "--profile", "fixture"]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    if proc.returncode != 0:
        raise SystemExit(f"fixture build failed with exit {proc.returncode}")
    if not fixture.is_file():
        raise SystemExit(f"fixture build reported success but {fixture} missing")
    print(f"fixture db built: {fixture} ({fixture.stat().st_size} bytes)")
    return fixture


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=0, help="fixed port; 0 = ephemeral")
    ap.add_argument(
        "--skip-assemble",
        action="store_true",
        help="skip bundle assembly (still boots the API against fixture)",
    )
    ap.add_argument(
        "--startup-timeout",
        type=float,
        default=45.0,
        help="seconds to wait for /health after spawning uvicorn",
    )
    args = ap.parse_args()

    log: dict = {
        "handoff": "H2344",
        "profile": "fixture",
        "production_contact": False,
        "steps": [],
    }

    fixture = ensure_fixture_db()
    log["steps"].append({"step": "fixture_db", "path": str(fixture), "ok": True})

    if not args.skip_assemble:
        from kosha.deploy.bundle import assemble_bundle

        report = assemble_bundle(repo_root=REPO_ROOT, profile="fixture")
        if not report.ok:
            for err in report.errors:
                print(f"ERROR assemble: {err}", file=sys.stderr)
            log["steps"].append(
                {"step": "assemble", "ok": False, "errors": report.errors}
            )
            _write_log(log)
            return 1
        print(f"bundle: {report.out_dir} ({report.files_hashed} files)")
        log["steps"].append(
            {
                "step": "assemble",
                "ok": True,
                "out_dir": str(report.out_dir),
                "files_hashed": report.files_hashed,
            }
        )
    else:
        log["steps"].append({"step": "assemble", "ok": True, "skipped": True})

    port = args.port or _free_port()
    env = os.environ.copy()
    env["KOSHA_CORE_DB_PATH"] = str(fixture.resolve())
    env["KOSHA_HISTORY_ENABLED"] = "false"
    env["KOSHA_PUBLIC_BASE"] = f"http://127.0.0.1:{port}"
    env["CORS_ORIGINS"] = '["*"]'
    # Clear expected-version pin so fixture meta is accepted.
    env.pop("KOSHA_EXPECTED_DATA_VERSION", None)
    env.pop("DATABASE_PATH", None)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]
    print(f"starting: {' '.join(cmd)} (fixture DB)")
    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    health_url = f"http://127.0.0.1:{port}/health"
    ready_url = f"http://127.0.0.1:{port}/ready"
    lemma_url = f"http://127.0.0.1:{port}/api/v1/lemma/banD"
    deadline = time.monotonic() + args.startup_timeout
    booted = False
    try:
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                out = proc.stdout.read() if proc.stdout else ""
                print(out, file=sys.stderr)
                log["steps"].append(
                    {
                        "step": "boot",
                        "ok": False,
                        "exit": proc.returncode,
                        "output_tail": out[-2000:],
                    }
                )
                _write_log(log)
                return 1
            try:
                status, body = _http_get(health_url, timeout=1.5)
                if status == 200:
                    booted = True
                    log["steps"].append(
                        {"step": "health", "ok": True, "status": status, "body": body}
                    )
                    print(f"health: {status} {body}")
                    break
            except Exception:
                time.sleep(0.4)
                continue
            time.sleep(0.4)

        if not booted:
            print("ERROR: uvicorn never became healthy", file=sys.stderr)
            log["steps"].append({"step": "health", "ok": False})
            _write_log(log)
            return 1

        ready_status, ready_body = _http_get(ready_url, timeout=5.0)
        print(f"ready: {ready_status} {ready_body[:500]}")
        ready_ok = ready_status == 200
        try:
            ready_json = json.loads(ready_body)
            ready_ok = ready_ok and bool(ready_json.get("ready") is True)
        except json.JSONDecodeError:
            ready_ok = False
        log["steps"].append(
            {
                "step": "ready",
                "ok": ready_ok,
                "status": ready_status,
                "body": ready_body[:2000],
            }
        )
        if not ready_ok:
            print("ERROR: /ready not green", file=sys.stderr)
            _write_log(log)
            return 1

        lemma_status, lemma_body = _http_get(lemma_url, timeout=5.0)
        # Fixture may not contain banD — accept 200 with results OR a clean 404 envelope.
        lemma_ok = lemma_status in {200, 404}
        print(f"lemma smoke: {lemma_status} ({len(lemma_body)} bytes)")
        log["steps"].append(
            {
                "step": "lemma_smoke",
                "ok": lemma_ok,
                "status": lemma_status,
                "bytes": len(lemma_body),
            }
        )
        if not lemma_ok:
            print("ERROR: lemma smoke unexpected status", file=sys.stderr)
            _write_log(log)
            return 1

        log["ok"] = True
        log["port"] = port
        _write_log(log)
        print("REHEARSAL PASS")
        return 0
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


def _write_log(log: dict) -> None:
    out = REPO_ROOT / "data" / "deploy_bundles" / "last_rehearsal.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"rehearsal log: {out}")


if __name__ == "__main__":
    raise SystemExit(main())
