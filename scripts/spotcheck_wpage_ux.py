"""spotcheck_wpage_ux.py — H3457 acceptance spot-checks on our own data.

1. Badge: for every staged page, the rendered data-core-rank / data-coverage
   are compared BYTE-WISE against data/frequency/lemma_frequency.tsv
   (`core_rank`, `coverage_pct` columns, raw strings).
2. Scan anchors: every distinct print-anchor href on the staged pages is
   collected; with --live the first N (default 10) PWG vol-col links are
   GET-checked against Cologne's servepdf.php, spaced --spacing seconds apart
   (the host rate-limits per IP — Uprava SERVER_OUTAGES.md rows for
   sanskrit-lexicon.uni-koeln.de; a 429 is reported, never retried).

Prints two Markdown tables (paste into the packet) and exits non-zero on any
badge mismatch. Live check failures are reported, not fatal (external host).

Usage:
    python scripts/spotcheck_wpage_ux.py --variant a
    python scripts/spotcheck_wpage_ux.py --variant a --live --n 10 --spacing 12
"""
import argparse
import csv
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
LEMMA_FREQ = ROOT / "data" / "frequency" / "lemma_frequency.tsv"
BADGE_RE = re.compile(r'class="(?:study-badge|study-line)[^"]*" data-core-rank="(\d+)" data-coverage="([^"]*)"')
ENTRY_RE = re.compile(r'<article class="dict-entry" id="e-(\w+)-(\d+)">.*?<a class="scan[^"]*" href="([^"]+)"', re.S)
PAGE_RE = re.compile(r"page=(\d+)-(\d+)")


def _decode_token(tok):
    out, j = [], 0
    while j < len(tok):
        if tok[j] == "_":
            out.append(chr(int(tok[j + 1:j + 3], 16)))
            j += 3
        else:
            out.append(tok[j])
            j += 1
    return "".join(out)


def tsv_rows():
    d = {}
    with LEMMA_FREQ.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            d[r["lemma_slp1"]] = ((r.get("core_rank") or "").strip(), (r.get("coverage_pct") or "").strip())
    return d


def badge_table(pages, tsv):
    lines = ["| token | slp1 | TSV core_rank | TSV coverage_pct | page data-core-rank | page data-coverage | match |",
             "|---|---|---:|---|---:|---|---|"]
    bad = 0
    for p in pages:
        slp1 = _decode_token(p.stem)
        html = p.read_text(encoding="utf-8")
        m = BADGE_RE.search(html)
        t_rank, t_cov = tsv.get(slp1, ("", ""))
        g_rank, g_cov = (m.group(1), m.group(2)) if m else ("", "")
        ok = (t_rank, t_cov) == (g_rank, g_cov)
        bad += 0 if ok else 1
        lines.append(f"| `{p.stem}` | `{slp1}` | {t_rank or '—'} | {t_cov or '—'} | {g_rank or '—'} | "
                     f"{g_cov or '—'} | {'✅' if ok else '❌'} |")
    return "\n".join(lines), bad


def anchors(pages):
    seen = {}
    for p in pages:
        html = p.read_text(encoding="utf-8")
        for d, L, href in ENTRY_RE.findall(html):
            seen.setdefault(href, (p.stem, d, L))
    return seen


def live_check(hrefs, n, spacing):
    lines = ["| # | page | dict | L | href (page key) | HTTP | bytes | content-type | s |",
             "|---:|---|---|---|---|---:|---:|---|---:|"]
    pwg = [(h, m) for h, m in hrefs.items() if m[1] == "pwg" and PAGE_RE.search(h)]
    ok = 0
    for i, (href, (tok, d, L)) in enumerate(pwg[:n], 1):
        if i > 1:
            time.sleep(spacing)
        t0 = time.time()
        try:
            req = urllib.request.Request(href, headers={"User-Agent": "kosha-h3457-spotcheck/1.0 (+https://github.com/gasyoun/kosha)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
                code, ctype = r.status, r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            code, body, ctype = e.code, b"", ""
        except Exception as e:  # noqa: BLE001
            code, body, ctype = f"ERR {type(e).__name__}", b"", ""
        dt = time.time() - t0
        key = PAGE_RE.search(href).group(0)
        if code == 200:
            ok += 1
        lines.append(f"| {i} | `{tok}` | {d} | {L} | `{key}` | {code} | {len(body)} | {ctype} | {dt:.1f} |")
        print(f"[live] {i}/{min(n, len(pwg))} {tok} {key} -> {code} {len(body)}B {dt:.1f}s")
    return "\n".join(lines), ok, min(n, len(pwg))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", default="a")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--spacing", type=float, default=12.0)
    ap.add_argument("--out", type=Path, default=None, help="write the tables to this .md")
    args = ap.parse_args()
    w_dir = ROOT / "dist" / "w-staging" / args.variant / "w"
    pages = sorted(w_dir.glob("*.html"))
    if not pages:
        sys.exit(f"error: no staged pages in {w_dir}")
    tsv = tsv_rows()
    btab, bad = badge_table(pages, tsv)
    hrefs = anchors(pages)
    n_pwg_vc = sum(1 for h, m in hrefs.items() if m[1] == "pwg" and PAGE_RE.search(h))
    n_pwg = sum(1 for m in hrefs.values() if m[1] == "pwg")
    out = [f"## Badge spot-check vs lemma_frequency.tsv ({len(pages)} staged pages, {bad} mismatches)", "", btab, "",
           f"## Print anchors on the staged pages: {len(hrefs)} distinct hrefs; PWG {n_pwg} "
           f"of which {n_pwg_vc} carry the H839 vol-col key", ""]
    print("\n".join(out))
    if args.live:
        ltab, okc, tried = live_check(hrefs, args.n, args.spacing)
        out += [f"## Live check — {okc}/{tried} PWG vol-col links returned HTTP 200 "
                f"(spacing {args.spacing:g} s, {time.strftime('%d-%m-%Y %H:%M')})", "", ltab, ""]
        print("\n".join(out[-4:]))
    if args.out:
        args.out.write_text("\n".join(out) + "\n", encoding="utf-8")
        print(f"[spotcheck] -> {args.out}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
