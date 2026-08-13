# samskrtam.ru branded kosha proxy

_Created: 13-08-2026 · Last updated: 13-08-2026_

Wire `https://samskrtam.ru/{health,ready,metrics,api,dicts,w}` to the live
kosha unit on `.92` without moving WordPress.

`.95` has FTP only (ISPmanager). `.92` has SSH. They share LAN
`192.168.200.0/24` (`.92` = `192.168.200.92`, `.95` = `192.168.200.95`).

## Pieces

1. **On `.92`:** nginx site
   [`kosha-from-95.nginx`](https://github.com/gasyoun/kosha/blob/main/deploy/samskrtam-brand-proxy/kosha-from-95.nginx)
   listens on `192.168.200.92:8002`, allowlist `.95` + localhost, proxies to
   uvicorn `127.0.0.1:8001`. Installed as
   `/etc/nginx/sites-enabled/kosha-from-95`.
2. **On `.95` via FTP:**
   - `www/samskrtam.ru/kosha/proxy.php` — allowlisted reverse proxy
   - `www/samskrtam.ru/wp-content/mu-plugins/kosha-brand-proxy.php` — WP
     intercept if rewrite is skipped
   - prepend the `htaccess.snippet` block **above** `# BEGIN WordPress`

Upstream order in PHP: LAN `:8002`, then public sslip.

Do **not** proxy `/wp-json/`, `/wp-admin/`, `/faq/`, or `/`.

## Smoke

```sh
curl -fsS https://samskrtam.ru/health
curl -fsS https://samskrtam.ru/ready
curl -fsS https://samskrtam.ru/metrics | head
curl -fsS 'https://samskrtam.ru/api/v1/lemma/banD' | head -c 200
curl -fsS -o /dev/null -w '%{http_code}\n' https://samskrtam.ru/
curl -fsS -o /dev/null -w '%{http_code}\n' https://samskrtam.ru/faq/
```

---

_Dr. Mārcis Gasūns_
