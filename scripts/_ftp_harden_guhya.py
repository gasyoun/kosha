"""Harden www/samskrtam.ru/guhya against public HTTP reads."""
from __future__ import annotations

import ftplib
import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def main() -> int:
    cfg = load_env(REPO / ".env.deploy")
    ftp = ftplib.FTP()
    ftp.connect(cfg["FTP_HOST"], int(cfg.get("FTP_PORT", "21")), timeout=45)
    ftp.login(cfg["FTP_USER"], cfg["FTP_PASS"])
    ftp.cwd("/www/samskrtam.ru/guhya")
    try:
        ftp.delete("README.txt")
        print("deleted README.txt")
    except ftplib.error_perm as e:
        print("delete README:", e)

    ht = """# Restricted backup path (guhya) — not linked from public pages
Options -Indexes
<IfModule mod_authz_core.c>
  Require all denied
</IfModule>
<IfModule !mod_authz_core.c>
  Order deny,allow
  Deny from all
</IfModule>
"""
    ftp.storbinary("STOR .htaccess", io.BytesIO(ht.encode("utf-8")))
    print("rewrote .htaccess")
    print("nlst", ftp.nlst())
    ftp.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
