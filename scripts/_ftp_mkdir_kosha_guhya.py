"""One-shot: create www/samskrtam.ru/kosha and .../guhya via plain FTP.

Uses kosha/.env.deploy (never prints secrets). Plain FTP because the host's
TLS cert fails default verify (self-signed); credentials are the same.
"""
from __future__ import annotations

import ftplib
import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
ENV_PATH = REPO / ".env.deploy"


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def ensure_dir(ftp: ftplib.FTP, remote_dir: str) -> None:
    parts = [p for p in remote_dir.replace("\\", "/").split("/") if p]
    ftp.cwd("/")
    for part in parts:
        try:
            ftp.cwd(part)
            print(f"exists  {ftp.pwd()}")
        except ftplib.error_perm:
            ftp.mkd(part)
            ftp.cwd(part)
            print(f"created {ftp.pwd()}")


def store_text(ftp: ftplib.FTP, name: str, text: str) -> None:
    bio = io.BytesIO(text.encode("utf-8"))
    ftp.storbinary(f"STOR {name}", bio)
    print(f"wrote   {ftp.pwd()}/{name} ({len(text)} bytes)")


def main() -> int:
    if not ENV_PATH.is_file():
        print(f"missing {ENV_PATH}", file=sys.stderr)
        return 1
    cfg = load_env(ENV_PATH)
    for key in ("FTP_HOST", "FTP_USER", "FTP_PASS"):
        if not cfg.get(key):
            print(f"incomplete {ENV_PATH}: need {key}", file=sys.stderr)
            return 1

    host = cfg["FTP_HOST"]
    user = cfg["FTP_USER"]
    passwd = cfg["FTP_PASS"]
    port = int(cfg.get("FTP_PORT", "21"))
    print(f"connecting {host}:{port} as {user[:2]}***")

    ftp = ftplib.FTP()
    ftp.connect(host, port, timeout=45)
    ftp.login(user, passwd)
    print("login ok")

    for d in ("www/samskrtam.ru/kosha", "www/samskrtam.ru/guhya"):
        print(f"--- {d}")
        ensure_dir(ftp, d)

    # Public kosha landing (points at live API on .92 sslip)
    ensure_dir(ftp, "www/samskrtam.ru/kosha")
    kosha_index = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>kosha — Sanskrit dictionary</title>
  <meta http-equiv="refresh" content="0; url=https://kosha.193.232.229.92.sslip.io/">
</head>
<body>
  <p>kosha API:
    <a href="https://kosha.193.232.229.92.sslip.io/">https://kosha.193.232.229.92.sslip.io/</a>
  </p>
  <p>First promote on 193.232.229.92 (sslip). Branded reverse-proxy residual.</p>
</body>
</html>
"""
    store_text(ftp, "index.html", kosha_index)

    # Restricted guhya: deny web listing/read if Apache honors .htaccess
    ensure_dir(ftp, "www/samskrtam.ru/guhya")
    guhya_htaccess = """# Restricted backup path — not linked from public pages
Options -Indexes
<IfModule mod_authz_core.c>
  Require all denied
</IfModule>
<IfModule !mod_authz_core.c>
  Deny from all
</IfModule>
"""
    store_text(ftp, ".htaccess", guhya_htaccess)
    store_text(
        ftp,
        "README.txt",
        "Restricted kosha backup path (guhya). Not for public linking.\n"
        "Created 2026-08-08 via FTP from kosha/.env.deploy FTP_PATH.\n",
    )

    for d in ("www/samskrtam.ru/kosha", "www/samskrtam.ru/guhya"):
        ftp.cwd("/")
        ensure_dir(ftp, d)
        names = ftp.nlst()
        print(f"list {d}: {names}")

    ftp.quit()
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
