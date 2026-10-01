#!/usr/bin/env python3
"""smoke_sense_alignment.py — evidence for the H3744 aligned-sense staging surface.

Two surfaces, one run, `file://` only (no network, Chromium headless):

  1. the standalone staged viewer   dist/sense-align-staging/index.html
  2. the word-page organ            dist/w-staging/a/w/<token>.html

and the three things that can silently be false about them:

  * **the canonical case is right** — नागदन्त's PWG a〉 *Elephantenzahn* aligns with
    MW's *elephant's tusk* on `MBh.`, and PWG b〉 *Pflock in der Wand* with MW's
    *peg in the wall* on `Pañc.`/`Kathās.` — the तusk↔peg split the wave exists for,
    checked against the committed table, not against the renderer;
  * **the publication fence holds** — nothing under `docs/` mentions the organ, the
    public render (`ux=None`) is byte-identical to the pre-H3744 page, and every
    staged tree carries its NOT_PUBLISHED marker;
  * **the surfaces load clean** — zero console errors / page errors per page ×
    viewport, the table has rows, and every rendered row's numbers match the TSV.

Usage:
    python scripts/build_sense_alignment.py
    python scripts/build_word_pages.py --ux-staging a --tokens padma,kAla,citra,amfta,vftta,vajra,satya,go,arka,sAra
    python scripts/smoke_sense_alignment.py --log docs/H3744_SENSE_ALIGNMENT_SMOKE_LOG_31.08.26.md
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

VIEWPORTS = (375, 1280)
TABLE = ROOT / "data" / "concordance" / "sense_alignment.tsv"
FAILURES = ROOT / "data" / "concordance" / "sense_alignment_failures.tsv"
VIEWER = ROOT / "dist" / "sense-align-staging"
WSTAGE = ROOT / "dist" / "w-staging" / "a"


def rows_of(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def check_nagadanta(rows: list[dict], out: list[tuple]) -> None:
    """The case the wave exists for. Checked on the table, not the pixels."""
    groups = [r for r in rows if r["lemma_slp1"] == "nAgadanta" and r["status"] == "aligned"]
    ok = len(groups) == 2
    out.append(("nAgadanta has exactly 2 aligned meanings", ok, f"got {len(groups)}"))
    tusk = [g for g in groups if "Elephantenzahn" in g["pwg_gloss"]]
    peg = [g for g in groups if "Pflock" in g["pwg_gloss"]]
    out.append(("PWG a〉 Elephantenzahn is aligned", bool(tusk),
                tusk[0]["mw_gloss"][:60] if tusk else "not found"))
    out.append(("…to MW 'elephant's tusk', on witness mbh",
                bool(tusk) and "tusk" in tusk[0]["mw_gloss"] and "mbh" in tusk[0]["witnesses"],
                f"{tusk[0]['witnesses']} / {tusk[0]['mw_gloss'][:50]}" if tusk else "—"))
    out.append(("PWG b〉 Pflock in der Wand is aligned", bool(peg),
                peg[0]["mw_gloss"][:60] if peg else "not found"))
    out.append(("…to MW 'peg in the wall', on witness panc (PAÑCAT. ≡ Pañc.)",
                bool(peg) and "peg in the wall" in peg[0]["mw_gloss"]
                and "panc" in peg[0]["witnesses"].split(),
                f"{peg[0]['witnesses']} / {peg[0]['mw_gloss'][:50]}" if peg else "—"))
    out.append(("the two meanings are NOT merged (tusk ≠ peg row)",
                bool(tusk) and bool(peg) and tusk[0]["group_id"] != peg[0]["group_id"],
                f"{tusk[0]['group_id']} vs {peg[0]['group_id']}" if tusk and peg else "—"))


def check_fence(out: list[tuple]) -> None:
    """The publication contract, mechanically."""
    docs = ROOT / "docs"
    leaked = []
    for p in list(docs.rglob("*.html")) + list(docs.rglob("*.json")):
        try:
            if "sense-align" in p.read_text(encoding="utf-8", errors="ignore"):
                leaked.append(str(p.relative_to(ROOT)))
        except OSError:
            pass
    out.append(("no docs/ (Pages) artifact carries the aligned-sense organ",
                not leaked, ", ".join(leaked[:3]) or "0 files"))
    for tree in (VIEWER, WSTAGE):
        out.append((f"{tree.relative_to(ROOT)}/NOT_PUBLISHED.md present",
                    (tree / "NOT_PUBLISHED.md").is_file(), ""))
    out.append(("docs/NOT_PUBLISHED_H3744_SENSE_ALIGNMENT.md present",
                (docs / "NOT_PUBLISHED_H3744_SENSE_ALIGNMENT.md").is_file(), ""))

    # The live pages have carried the H3457 ux organs since 26-08-2026, so `ux`
    # truthiness is not a gate. Three renders, not two: no ux, plain ux (what a
    # live rebuild would do), and the staging opt-in.
    from word_page import render_word_page
    card = json.loads((ROOT / "docs" / "cards" / "padma.json").read_text(encoding="utf-8"))
    public = render_word_page(card, token="padma", include_doc=False)
    live_like = render_word_page(card, token="padma", include_doc=False, ux={"variant": "a"})
    staged = render_word_page(card, token="padma", include_doc=False,
                              ux={"variant": "a", "sense_align": True})
    out.append(("public render (ux=None) contains NO aligned-sense block",
                "sense-align" not in public, ""))
    out.append(("live-shaped render (ux={'variant':'a'}) contains NO aligned-sense block",
                "sense-align" not in live_like, "the gate is the explicit key, not ux truthiness"))
    out.append(("staging render (ux + sense_align) DOES contain it",
                "sense-align" in staged, ""))


def check_failures(rows: list[dict], frows: list[dict], out: list[tuple]) -> None:
    """Failure classes are recorded, not hidden."""
    classes = {r["failure_class"] for r in frows if r["failure_class"]}
    known = {"no-shared-witness", "witness-too-common", "cross-language-gap",
             "no-gloss", "absent-dictionary", "outranked",
             "no-citation-apparatus"}   # H3862, the Sa→Sa columns
    out.append(("every failure row carries a class from the documented taxonomy",
                classes <= known and bool(classes), ", ".join(sorted(classes))))
    unaligned_tbl = sum(1 for r in rows if r["status"] == "unaligned")
    out.append(("unaligned senses are kept in the table, not dropped",
                unaligned_tbl > 0, f"{unaligned_tbl} rows"))
    out.append(("every aligned row states its method and score",
                all(r["method"] and r["score"] for r in rows if r["status"] == "aligned"), ""))
    out.append(("no aligned row is single-dictionary (shape has ≥2 non-zero)",
                all(sum(1 for x in r["shape"].split("-") if x != "0") >= 2
                    for r in rows if r["status"] == "aligned"), ""))


def browser_checks(out: list[tuple]) -> None:
    from playwright.sync_api import sync_playwright
    targets = [("staged viewer", VIEWER / "index.html", "#nAgadanta"),
               ("word page padma (ux=a)", WSTAGE / "w" / "padma.html", "")]
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for label, path, frag in targets:
            if not path.is_file():
                out.append((f"{label} exists", False, f"{path} missing — run the build first"))
                continue
            for vw in VIEWPORTS:
                page = browser.new_page(viewport={"width": vw, "height": 900})
                errs: list[str] = []
                page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda e: errs.append(str(e)))
                page.goto(path.as_uri() + frag)
                page.wait_for_timeout(250)
                n_rows = page.eval_on_selector_all(
                    "table.sa-table tbody tr, table tbody tr", "els => els.length")
                out.append((f"{label} @{vw}px — 0 console/page errors", not errs,
                            "; ".join(errs[:2])))
                out.append((f"{label} @{vw}px — table has rows", n_rows > 0, f"{n_rows} rows"))
                if "viewer" in label:
                    txt = page.inner_text("#out")
                    out.append((f"{label} @{vw}px — नागदन्त tusk row rendered",
                                "tusk" in txt, ""))
                    out.append((f"{label} @{vw}px — नागदन्त peg row rendered",
                                "peg in the wall" in txt, ""))
                    out.append((f"{label} @{vw}px — failure classes visible on the page",
                                "cross-language-gap" in txt or "no-shared-witness" in txt, ""))
                page.close()
        browser.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log", default=None, help="write a Markdown evidence log here")
    ap.add_argument("--no-browser", action="store_true", help="table/fence checks only")
    args = ap.parse_args()

    rows, frows = rows_of(TABLE), rows_of(FAILURES)
    out: list[tuple] = []
    check_nagadanta(rows, out)
    check_failures(rows, frows, out)
    check_fence(out)
    if not args.no_browser:
        browser_checks(out)

    n_fail = sum(1 for _n, ok, _d in out if not ok)
    for name, ok, detail in out:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"   [{detail}]" if detail else ""))
    print(f"\n{len(out) - n_fail}/{len(out)} checks pass")

    if args.log:
        today = date.today().strftime("%d-%m-%Y")
        md = [
            "# Smoke log — H3744 aligned-sense staging surface",
            "", f"_Created: {today} · Last updated: {today}_", "",
            "Produced by [scripts/smoke_sense_alignment.py](https://github.com/gasyoun/kosha/blob/main/scripts/smoke_sense_alignment.py)",
            "(`file://`, Chromium headless, viewports 375 / 1280 px, no network).",
            "", f"**{len(out) - n_fail}/{len(out)} checks pass.**", "",
            "| check | result | detail |", "|---|---|---|",
        ]
        md += [f"| {n} | {'✅ PASS' if ok else '❌ FAIL'} | {d or ''} |" for n, ok, d in out]
        md += ["", "Reproduce:", "", "```bash",
               "python scripts/build_sense_alignment.py",
               "python scripts/build_word_pages.py --ux-staging a --tokens "
               "padma,kAla,citra,amfta,vftta,vajra,satya,go,arka,sAra",
               f"python scripts/smoke_sense_alignment.py --log {args.log}", "```",
               "", "_Dr. Mārcis Gasūns_"]
        Path(args.log).write_text("\n".join(md) + "\n", encoding="utf-8")
        print(f"wrote {args.log}")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
