"""measure_pages_budget.py — W4b Pages budget re-measure WITH a failing gate (H3745).

A measurement without a threshold is not a gate — an unattended run would always
"succeed". This re-measures the projected Pages footprint (deployed tiers on disk
plus the D4 static word-page head, sampled at build time) and **fails** (exit 1)
if the projection exceeds 70% of the 1,024 MB soft cap (717 MB).

D4 standing rule (ARCHITECTURE.md, H1586): head N is measured from
data/frequency/lemma_frequency.tsv at build time, never carried forward as a
constant. Mean KB/page is likewise sampled at build time (H1586 found the H537
9.7 KB figure stale by ~24%) via a small head-band sample rendered to a scratch
directory — this script never writes into docs/w/.

Run:
    python scripts/measure_pages_budget.py                 # measure + gate + append log row
    python scripts/measure_pages_budget.py --no-log         # measure + gate only, no doc write
    python scripts/measure_pages_budget.py --sample 300     # sample size for mean KB/page (default 300)
"""
import argparse
import datetime
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "app"))

from build_word_pages import (  # noqa: E402
    measure_head_n, select_head_tokens, _read_json, _decode_token, LEMMA_FREQ,
)
from word_page import render_word_page  # noqa: E402

PAGES_SOFT_CAP_MB = 1024.0
GATE_FRACTION = 0.70
GATE_MB = PAGES_SOFT_CAP_MB * GATE_FRACTION  # 716.8 MB

DOCS = ROOT / "docs"
CARDS_DIR = DOCS / "cards"
CONCORDANCE_DIR = ROOT / "concordance"
PANINI_DIR = CONCORDANCE_DIR / "panini"
READING_DIR = ROOT / "reading"
DOCS_JS_DIR = DOCS / "js"

ARCH_DOC = DOCS / "ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md"
LOG_MARKER = "### W4b re-measure log (append-only)"


def dir_size_mb(path):
    if not path.exists():
        return 0.0
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return total / 1e6


def sample_head_mean_kb(sample_n):
    """Render a spread sample of the D4 head to a scratch dir; return mean KB/page."""
    att_path = DOCS / "js" / "data" / "attested_keys.json"
    if not att_path.exists():
        sys.exit(f"error: {att_path} not found — run scripts/build_static_cache.py first.")
    attested = _read_json(att_path)["tokens"]
    tokens, meta = select_head_tokens(attested, CARDS_DIR, coverage=0.95)
    head_tokens = [t for t in tokens if (CARDS_DIR / f"{t}.json").exists()]
    if not head_tokens:
        sys.exit("error: no head tokens with a card on disk — build the static cache first.")
    step = max(1, len(head_tokens) // sample_n)
    sample = head_tokens[::step][:sample_n]
    total_bytes = 0
    for tok in sample:
        card = _read_json(CARDS_DIR / f"{tok}.json")
        html_str = render_word_page(card, token=tok)
        total_bytes += len(html_str.encode("utf-8"))
    mean_kb = (total_bytes / len(sample)) / 1024
    return mean_kb, len(sample), meta


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", type=int, default=300,
                     help="head-band sample size for mean KB/page (default 300)")
    ap.add_argument("--no-log", action="store_true",
                     help="skip appending a row to the ARCHITECTURE doc")
    args = ap.parse_args()

    cards_mb = dir_size_mb(CARDS_DIR)
    concordance_mb = dir_size_mb(CONCORDANCE_DIR)
    panini_mb = dir_size_mb(PANINI_DIR)
    reading_mb = dir_size_mb(READING_DIR)
    docs_js_mb = dir_size_mb(DOCS_JS_DIR)

    head_n_meta = measure_head_n(LEMMA_FREQ, coverage=0.95)
    mean_kb, sampled, sel_meta = sample_head_mean_kb(args.sample)
    head_mb = head_n_meta["n"] * mean_kb / 1024

    projected_total_mb = cards_mb + concordance_mb + reading_mb + docs_js_mb + head_mb
    projected_pct = (projected_total_mb / PAGES_SOFT_CAP_MB) * 100

    cards_on_disk = len(list(CARDS_DIR.glob("*.json"))) if CARDS_DIR.exists() else 0
    w_dir_local = DOCS / "w"
    built_w_pages = len(list(w_dir_local.glob("*.html"))) if w_dir_local.exists() else None

    print(f"[budget] cards={cards_mb:.1f} MB  concordance(all)={concordance_mb:.1f} MB "
          f"(panini={panini_mb:.2f} MB)  reading={reading_mb:.1f} MB  docs/js={docs_js_mb:.1f} MB")
    print(f"[budget] D4 head N={head_n_meta['n']} at coverage={head_n_meta['coverage_achieved']*100:.2f}% "
          f"(target 95%) from {head_n_meta['tokens_total']} lemmas")
    print(f"[budget] mean KB/page sampled over n={sampled} head-band cards: {mean_kb:.2f} KB "
          f"-> projected head size {head_mb:.1f} MB")
    print(f"[budget] cards on disk (input population): {cards_on_disk}")
    if built_w_pages is not None:
        print(f"[budget] static /w/ pages built in THIS worktree (docs/w/, gitignored): {built_w_pages}")
    else:
        print("[budget] docs/w/ not built in this worktree (gitignored) — actual deployed "
              "/w/ page count is a Pages-deploy-side fact, not locally measurable; quote it "
              "from the last known deploy figure instead of re-deriving here.")
    print(f"[budget] PROJECTED TOTAL = {projected_total_mb:.1f} MB = {projected_pct:.1f}% "
          f"of {PAGES_SOFT_CAP_MB:.0f} MB cap")
    print(f"[budget] GATE: fail if projected > {GATE_MB:.1f} MB ({GATE_FRACTION*100:.0f}%)")

    gate_failed = projected_total_mb > GATE_MB
    verdict = "FAIL" if gate_failed else "PASS"
    print(f"[budget] GATE {verdict}")

    if not args.no_log:
        date_str = datetime.date.today().strftime("%d-%m-%Y")
        row = (
            f"| **{date_str}** | **{cards_mb:.1f} MB** | **{concordance_mb:.1f} MB** | "
            f"**{panini_mb:.2f} MB** | **{reading_mb:.1f} MB** | **{docs_js_mb:.1f} MB** | "
            f"**{head_mb:.1f} MB** @ sampled mean **{mean_kb:.2f} KB/page** (n={sampled}) | "
            f"**{projected_total_mb:.1f} MB** | **{projected_pct:.1f}%** | "
            f"H3745 re-measure with wired 70% ({GATE_MB:.1f} MB) fail gate — GATE {verdict}. "
            f"Cards on disk (input population): {cards_on_disk}. D4 target head N={head_n_meta['n']}; "
            f"actual deployed `/w/` page count is a Pages-deploy-side fact (2,324 per H3745 mint, "
            f"30-08-2026), not re-measurable from this worktree since `docs/w/` is gitignored. |\n"
        )
        text = ARCH_DOC.read_text(encoding="utf-8")
        if LOG_MARKER not in text:
            sys.exit(f"error: log marker {LOG_MARKER!r} not found in {ARCH_DOC}")
        lines = text.splitlines(keepends=True)
        marker_i = next(i for i, l in enumerate(lines) if LOG_MARKER in l)
        # advance past marker/blank/header/separator to the first "| ..." data row,
        # then keep advancing while rows continue — insert after the LAST such row.
        i = marker_i + 1
        last_row_i = None
        seen_header = False
        while i < len(lines) and (lines[i].strip() == "" or lines[i].lstrip().startswith("|")):
            if lines[i].lstrip().startswith("|"):
                if not seen_header:
                    seen_header = True  # the "| Date | ... |" header line
                elif set(lines[i].strip().replace("|", "").replace("-", "").replace(":", "")) == set():
                    pass  # the "|---|---:|" separator line
                else:
                    last_row_i = i
            elif last_row_i is not None:
                break
            i += 1
        if last_row_i is None:
            sys.exit(f"error: could not locate the last data row of the W4b log table in {ARCH_DOC}")
        insert_at = last_row_i + 1
        lines.insert(insert_at, row)
        ARCH_DOC.write_text("".join(lines), encoding="utf-8")
        print(f"[budget] appended log row to {ARCH_DOC.relative_to(ROOT)}")

    sys.exit(1 if gate_failed else 0)


if __name__ == "__main__":
    main()
