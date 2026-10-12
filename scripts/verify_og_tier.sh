#!/usr/bin/env bash
# verify_og_tier.sh — PLAYBOOK_OG_PREVIEW_CARDS §6 as a machine check (H6527).
#
# Verifies one served /w/ og: surface end-to-end and exits 0 only when every
# §6 gate is green; any miss exits 1 with the failing probe named. Cite the
# exit code in close packets — prose never counts (H6221 machine-DoD).
#
# Usage:
#   scripts/verify_og_tier.sh https://kosha.193.232.229.92.sslip.io [token]
#   scripts/verify_og_tier.sh https://gasyoun.github.io/kosha  agni
#
# The base URL must serve /w/<token>.html; og: URLs inside the page are
# absolute (samskrtam.ru) by design, so the card probe follows them wherever
# the page is served from.
set -u
BASE="${1:?usage: verify_og_tier.sh <base-url> [token=agni]}"
TOKEN="${2:-agni}"
fail() { echo "FAIL $1"; exit 1; }

page=$(curl -sS -m 30 "$BASE/w/${TOKEN}.html") || fail "page fetch $BASE/w/${TOKEN}.html"
echo "$page" | grep -q '<title>' || fail "s6.3 no <title>"
echo "$page" | grep -o '<title>[^<]*' | head -1 | grep -qi "$TOKEN" || fail "s6.3 title does not name the token"
[ "$(printf '%s' "$page" | grep -c 'twitter:card')" -eq 1 ] || fail "s6.1 twitter:card count != 1"

img=$(printf '%s' "$page" | grep -o 'property="og:image" content="[^"]*"' | head -1 | sed 's/.*content="//;s/"$//')
[ -n "$img" ] || fail "s6.2 no og:image"
case "$img" in https://*) ;; *) fail "s6.2 og:image not absolute: $img" ;; esac
code=$(curl -sS -o /dev/null -w '%{http_code}' -m 30 -I "$img")
[ "$code" = "200" ] || fail "s6.2 og:image $img -> $code (want 200)"
ctype=$(curl -sS -o /dev/null -w '%{content_type}' -m 30 -I "$img")
[ "$ctype" = "image/png" ] || fail "s6.2 og:image content-type $ctype (want image/png)"

echo "PASS $BASE/w/${TOKEN}.html twitter:card=1 og:image=$img 200 image/png title-ok"
