"""smoke_wpage_ux.py — local Playwright smoke for the H3457 word-page UX staging build.

Runs over dist/w-staging/<variant>/ (file://, no network, Chromium headless) and
proves, per page × viewport (375 / 1280):
  * the page loads with zero console errors / page errors;
  * the study badge is present exactly when lemma_frequency.tsv has a core_rank
    for the lemma, and its data-core-rank / data-coverage byte-match the TSV;
  * every PWG entry's print anchor carries the H839 "{vol}-{col:04d}" page key
    (never a bare page) when data/pwg_scan/pwg_L_pc.tsv knows the L;
  * the favorite toggles, SURVIVES A RELOAD (localStorage), and the favorites
    page lists the saved lemma; un-favoriting removes it.

Writes a Markdown log (default docs/evidence is NOT used — evidence for this
handoff lives in the H3457 packet; pass --log to choose the path).

Usage:
    python scripts/build_word_pages.py --ux-staging a --tokens kf,gam,vac,as,deva,Darma,agni,rAma,jana,nf,yA
    python scripts/smoke_wpage_ux.py --variant a --log docs/H3457_WPAGE_UX_SMOKE_LOG_25.08.26.md
"""
import argparse
import csv
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "src"))

from word_page_ux import core_rank_of, pwg_pc_of  # noqa: E402

VIEWPORTS = (375, 1280)


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


def run(variant, log_path, tokens=None):
    from playwright.sync_api import sync_playwright
    stage = ROOT / "dist" / "w-staging" / variant
    w_dir = stage / "w"
    if not w_dir.exists():
        sys.exit(f"error: {w_dir} missing — run build_word_pages.py --ux-staging {variant} first")
    pages = sorted(w_dir.glob("*.html"))
    if tokens:
        want = set(tokens)
        pages = [p for p in pages if p.stem in want]
    rows, fails = [], 0
    t0 = time.time()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for width in VIEWPORTS:
            ctx = browser.new_context(viewport={"width": width, "height": 900})
            for p in pages:
                page = ctx.new_page()
                errs = []
                page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda e: errs.append(str(e)))
                page.goto(p.resolve().as_uri())
                slp1 = _decode_token(p.stem)
                # -- badge
                exp = core_rank_of(slp1)
                badge = page.query_selector(".study-badge[data-core-rank], .study-line[data-core-rank]")
                if exp is None:
                    badge_ok = badge is None
                    badge_note = "no core_rank in TSV, no badge" if badge_ok else "badge WITHOUT tsv rank"
                else:
                    got = (badge.get_attribute("data-core-rank"), badge.get_attribute("data-coverage")) if badge else None
                    badge_ok = got == (str(exp[0]), exp[1])
                    badge_note = f"rank {exp[0]} cov {exp[1]} -> page {got}"
                # -- scan anchors (PWG)
                pwg_bad = 0
                pwg_n = 0
                for a in page.query_selector_all('.dict-entry[id^="e-pwg-"] a.scan'):
                    pwg_n += 1
                    L = a.evaluate("a => a.closest('.dict-entry').id.split('-').pop()")
                    href = a.get_attribute("href") or ""
                    pc = pwg_pc_of(L)
                    if pc and f"page={pc[0]}-{pc[1]:04d}" not in href:
                        pwg_bad += 1
                # -- favorites: toggle, reload, verify, favorites page, untoggle
                fav_ok = None
                fav = page.query_selector("[data-fav]")
                if fav:
                    fav.click()
                    pressed1 = fav.get_attribute("aria-pressed")
                    page.reload()
                    fav = page.query_selector("[data-fav]")
                    pressed2 = fav.get_attribute("aria-pressed") if fav else None
                    page.goto((stage / "favorites.html").resolve().as_uri())
                    listed = page.query_selector(f'#fav-list li[data-k="{slp1}"]') is not None
                    n_txt = page.inner_text("#fav-n")
                    page.goto(p.resolve().as_uri())
                    page.query_selector("[data-fav]").click()
                    page.reload()
                    pressed3 = page.query_selector("[data-fav]").get_attribute("aria-pressed")
                    fav_ok = (pressed1, pressed2, listed, pressed3) == ("true", "true", True, "false")
                    fav_note = f"click->{pressed1} reload->{pressed2} listed={listed} (n={n_txt}) unfav->{pressed3}"
                else:
                    fav_note = "no [data-fav] on page"
                ok = (not errs) and badge_ok and pwg_bad == 0 and fav_ok is True
                fails += 0 if ok else 1
                rows.append({
                    "token": p.stem, "slp1": slp1, "width": width, "ok": ok,
                    "console_errors": len(errs), "badge": badge_note, "badge_ok": badge_ok,
                    "pwg_anchors": pwg_n, "pwg_bad": pwg_bad, "fav": fav_note, "fav_ok": fav_ok,
                    "errs": errs[:3],
                })
                print(f"[smoke] {'PASS' if ok else 'FAIL'} {p.stem:<10} {width:>4}px  {badge_note}; "
                      f"pwg anchors {pwg_n} bad {pwg_bad}; {fav_note}; console_errors={len(errs)}")
                page.close()
            ctx.close()
        browser.close()
    dt = time.time() - t0
    verdict = "PASS" if fails == 0 else f"FAIL ({fails} rows)"
    today = time.strftime("%d-%m-%Y")
    md = [
        f"# H3457 word-page UX staging — Playwright smoke log (variant `{variant}`)",
        "",
        f"_Created: {today} · Last updated: {today}_",
        "",
        f"_Run {time.strftime('%d-%m-%Y %H:%M')} local · Chromium headless via Python Playwright · "
        f"file:// over `dist/w-staging/{variant}/` · {len(pages)} pages × {len(VIEWPORTS)} viewports · "
        f"{dt:.1f} s · verdict **{verdict}**_",
        "",
        "Local-only: nothing here touched docs/, Pages or samskrtam.ru "
        "(docs/NOT_PUBLISHED_H3457_WPAGE_UX.md).",
        "",
        "| token | slp1 | px | ok | console | badge vs lemma_frequency.tsv | PWG anchors (bad) | favorites: click → reload → listed → un-fav |",
        "|---|---|---:|---|---:|---|---|---|",
    ]
    for r in rows:
        md.append(f"| `{r['token']}` | `{r['slp1']}` | {r['width']} | {'✅' if r['ok'] else '❌'} | "
                  f"{r['console_errors']} | {r['badge']} | {r['pwg_anchors']} ({r['pwg_bad']}) | {r['fav']} |")
    md.append("")
    md.append(f"Reproduce: `python scripts/build_word_pages.py --ux-staging {variant} --tokens "
              f"{','.join(p.stem for p in pages)}` then `python scripts/smoke_wpage_ux.py --variant {variant}`.")
    md.append("")
    md.append("_Dr. Mārcis Gasūns_")
    md.append("")
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("\n".join(md), encoding="utf-8")
        print(f"[smoke] log -> {log_path}")
    print(f"[smoke] {verdict}")
    print("[smoke] META " + json.dumps({"variant": variant, "pages": len(pages),
                                        "rows": len(rows), "fails": fails, "seconds": round(dt, 1)}))
    return fails == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", default="a")
    ap.add_argument("--log", type=Path, default=None)
    ap.add_argument("--tokens", default=None, help="comma list to restrict")
    args = ap.parse_args()
    toks = [t.strip() for t in args.tokens.split(",")] if args.tokens else None
    ok = run(args.variant, args.log, toks)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
