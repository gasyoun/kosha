"""measure_pages_budget.py — W4b Pages budget re-measure WITH a failing gate (H3745, H4841).

A measurement without a threshold is not a gate — an unattended run would always
"succeed". This measures the Pages footprint and **fails** (exit 1) if the
projection exceeds 70% of the 1,024 MB soft cap (716.8 MB).

What is measured (H4841 recalibration, 15-09-2026):

1. **The published tree, byte-true.** The Pages source is legacy `main:/` (the
   whole tracked tree, `.nojekyll`) — so the footprint is the sum of tracked
   blob sizes at HEAD (`git ls-tree -r -l HEAD`), broken down by tier (cards,
   concordance, reading, docs/js, the committed repo-root `w/`, data/, rest).
   The tiers partition that one list, so nothing is double-counted or missed —
   the committed `w/` head is a tier like any other (it was invisible before).
2. **The unbuilt head remainder, projected.** D4 head tokens with a card but no
   committed `w/<token>.html` are estimated by rendering a stratified sample with
   the PUBLISHED ux layer (`DEFAULT_LIVE_UX`) and added on top.
3. **A sampler check.** The same estimator is run over the WHOLE head and
   compared to the byte-true census of the committed head pages; the delta is
   printed so a drifting estimator is visible, not silent.

Sampler frame (H4841): a take-all stratum (the largest 2% of head cards by card
JSON bytes — the 250–800 KB monster pages live there) plus a size-sorted
systematic sample inside three rank bands (head / mid / tail thirds of the
selection), proportional allocation. The H3745 sampler rendered WITHOUT the
published ux layer (22.8 vs 36.7 KB/page on the same 300 cards) and multiplied by
N=11,148 instead of the 10,370 head lemmas that have a card — see
docs/PAGES_HEADROOM_PLAN_H4841_15.09.26.md.

D4 standing rule (ARCHITECTURE.md, H1586): head N is measured from
data/frequency/lemma_frequency.tsv at build time, never carried forward as a
constant. Rendering goes to memory only — this script never writes into w/.

Run:
    python scripts/measure_pages_budget.py                 # measure + gate + append log row
    python scripts/measure_pages_budget.py --no-log         # measure + gate only, no doc write
    python scripts/measure_pages_budget.py --sample 300     # rank-band sample size (default 300)
"""
import argparse
import datetime
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "app"))

from build_word_pages import (  # noqa: E402
    measure_head_n, select_head_tokens, _read_json, LEMMA_FREQ, DEFAULT_LIVE_UX,
)
from word_page import render_word_page  # noqa: E402

PAGES_SOFT_CAP_MB = 1024.0
GATE_FRACTION = 0.70
GATE_MB = PAGES_SOFT_CAP_MB * GATE_FRACTION  # 716.8 MB
TAKE_ALL_FRACTION = 0.02
SAMPLER_TOLERANCE = 0.05

DOCS = ROOT / "docs"
CARDS_DIR = DOCS / "cards"
W_DIR = ROOT / "w"

#: Tier = first matching path prefix of a tracked file; order matters
#: (concordance/panini/ before concordance/). Everything else is "other".
TIERS = [
    ("cards", "docs/cards/"),
    ("docs_js", "docs/js/"),
    ("panini", "concordance/panini/"),
    ("concordance", "concordance/"),
    ("reading", "reading/"),
    ("w", "w/"),
    ("data", "data/"),
]

ARCH_DOC = DOCS / "ARCHITECTURE_KOSHA_CONCORDANCE_Q3.md"
LOG_MARKER = "### W4b re-measure log (append-only)"


def tracked_tier_bytes(root=ROOT, rev="HEAD"):
    """Byte-true tracked-tree size by tier: {tier: bytes}, plus 'total'.

    Uses committed blob sizes, so a gitignored local build (docs/w/) is not
    counted — it is not on Pages. Falls back to a filesystem walk (minus .git)
    when git is unavailable."""
    out = {name: 0 for name, _ in TIERS}
    out["other"] = 0
    try:
        res = subprocess.run(["git", "ls-tree", "-r", "-l", "-z", rev], cwd=root,
                             capture_output=True, check=True)
        entries = []
        for rec in res.stdout.split(b"\0"):
            if not rec:
                continue
            meta, path = rec.split(b"\t", 1)
            size = meta.split()[3]
            if size == b"-":  # submodule/commit entry
                continue
            entries.append((path.decode("utf-8", "replace"), int(size)))
    except (OSError, subprocess.CalledProcessError):
        entries = [(p.relative_to(root).as_posix(), p.stat().st_size)
                   for p in root.rglob("*")
                   if p.is_file() and ".git" not in p.relative_to(root).parts]
    for path, size in entries:
        for name, prefix in TIERS:
            if path.startswith(prefix):
                out[name] += size
                break
        else:
            out["other"] += size
    out["total"] = sum(v for k, v in out.items() if k != "total")
    return out


def head_selection(cards_dir=CARDS_DIR):
    att_path = DOCS / "js" / "data" / "attested_keys.json"
    if not att_path.exists():
        sys.exit(f"error: {att_path} not found — run scripts/build_static_cache.py first.")
    attested = _read_json(att_path)["tokens"]
    tokens, meta = select_head_tokens(attested, cards_dir, coverage=0.95)
    head = [t for t in tokens if (cards_dir / f"{t}.json").exists()]
    if not head:
        sys.exit("error: no head tokens with a card on disk — build the static cache first.")
    return head, meta


def stratified_frame(tokens, card_bytes, sample_n, take_all_fraction=TAKE_ALL_FRACTION):
    """Sample frame over a rank-ordered token list.

    Returns {"take_all": [...], "bands": [{"name", "lo", "hi", "size", "sample"}]}
    with lo/hi as rank positions in ``tokens``. The take-all stratum is the
    largest ``take_all_fraction`` of cards by JSON bytes; the rest is split into
    head/mid/tail rank thirds, each sorted by card bytes and sampled
    systematically (midpoint of each step) with proportional allocation."""
    k = int(len(tokens) * take_all_fraction)
    take_all = set(sorted(tokens, key=lambda t: -card_bytes[t])[:k])
    rest = [(i, t) for i, t in enumerate(tokens) if t not in take_all]
    bands = []
    third = len(rest) / 3
    for bi, name in enumerate(("head", "mid", "tail")):
        band = rest[int(bi * third):int((bi + 1) * third)]
        if not band:
            continue
        n = max(1, min(len(band), round(sample_n * len(band) / len(rest))))
        by_size = sorted(band, key=lambda it: card_bytes[it[1]])
        step = len(by_size) / n
        sample = [by_size[int(step * j + step / 2)][1] for j in range(n)]
        bands.append({"name": name, "lo": band[0][0], "hi": band[-1][0],
                      "size": len(band), "sample": sample})
    return {"take_all": [t for t in tokens if t in take_all], "bands": bands}


def _page_bytes(tok, cards_dir):
    card = _read_json(cards_dir / f"{tok}.json")
    return len(render_word_page(card, token=tok, ux=DEFAULT_LIVE_UX).encode("utf-8"))


def project_pages_bytes(tokens, sample_n, cards_dir=CARDS_DIR):
    """Estimate the total rendered bytes of ``tokens`` (published ux layer)."""
    if not tokens:
        return 0, {"take_all": 0, "rendered": 0, "bands": []}
    card_bytes = {t: (cards_dir / f"{t}.json").stat().st_size for t in tokens}
    frame = stratified_frame(tokens, card_bytes, sample_n)
    total = sum(_page_bytes(t, cards_dir) for t in frame["take_all"])
    rendered = len(frame["take_all"])
    for band in frame["bands"]:
        pb = [_page_bytes(t, cards_dir) for t in band["sample"]]
        total += sum(pb) / len(pb) * band["size"]
        rendered += len(pb)
    info = {"take_all": len(frame["take_all"]), "rendered": rendered,
            "bands": [(b["name"], b["lo"], b["hi"], len(b["sample"])) for b in frame["bands"]]}
    return total, info


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", type=int, default=300,
                     help="rank-band sample size for the head estimator (default 300)")
    ap.add_argument("--no-log", action="store_true",
                     help="skip appending a row to the ARCHITECTURE doc")
    args = ap.parse_args()

    tiers = tracked_tier_bytes()
    mb = {k: v / 1e6 for k, v in tiers.items()}

    head_n_meta = measure_head_n(LEMMA_FREQ, coverage=0.95)
    head, _sel_meta = head_selection()
    built = [t for t in head if (W_DIR / f"{t}.html").exists()]
    unbuilt = [t for t in head if not (W_DIR / f"{t}.html").exists()]
    census_bytes = sum((W_DIR / f"{t}.html").stat().st_size for t in built)

    unbuilt_bytes, _ = project_pages_bytes(unbuilt, args.sample)
    unbuilt_mb = unbuilt_bytes / 1e6

    # Sampler check: the estimator over the whole head vs the byte-true census
    # of the committed head pages (only meaningful once the head is built).
    check = None
    if built and not unbuilt:
        est_bytes, frame_info = project_pages_bytes(head, args.sample)
        check = (est_bytes, census_bytes, (est_bytes / census_bytes - 1), frame_info)

    projected_total_mb = mb["total"] + unbuilt_mb
    projected_pct = (projected_total_mb / PAGES_SOFT_CAP_MB) * 100
    served_mb = mb["cards"] + mb["docs_js"] + mb["panini"] + mb["concordance"] + mb["reading"] + mb["w"]

    print(f"[budget] published tree (Pages source main:/, tracked bytes at HEAD) = "
          f"{mb['total']:.1f} MB")
    print(f"[budget]   cards={mb['cards']:.1f}  concordance={mb['concordance'] + mb['panini']:.1f} "
          f"(panini={mb['panini']:.2f})  reading={mb['reading']:.1f}  docs/js={mb['docs_js']:.1f}  "
          f"w/ (committed)={mb['w']:.1f}  data/={mb['data']:.1f}  other={mb['other']:.1f} MB")
    print(f"[budget]   served tiers (cards+concordance+reading+docs/js+w/) = {served_mb:.1f} MB "
          f"= {served_mb / PAGES_SOFT_CAP_MB * 100:.1f}%")
    print(f"[budget] D4 head N={head_n_meta['n']} at coverage={head_n_meta['coverage_achieved']*100:.2f}% "
          f"(target 95%) from {head_n_meta['tokens_total']} tokens; head with card={len(head)}")
    print(f"[budget] head pages committed in w/: {len(built)} ({census_bytes / 1e6:.1f} MB byte-true, "
          f"mean {census_bytes / max(len(built), 1) / 1024:.2f} KB/page); unbuilt: {len(unbuilt)} "
          f"-> projected +{unbuilt_mb:.1f} MB")
    if check is not None:
        est_bytes, cen, delta, info = check
        bands = ", ".join(f"{n}[{lo}..{hi}] n={k}" for n, lo, hi, k in info["bands"])
        print(f"[budget] sampler check: estimate {est_bytes / 1e6:.1f} MB vs census {cen / 1e6:.1f} MB "
              f"= {delta * 100:+.2f}% (tolerance ±{SAMPLER_TOLERANCE * 100:.0f}%); "
              f"take-all={info['take_all']} rendered={info['rendered']}; bands: {bands}")
        if abs(delta) > SAMPLER_TOLERANCE:
            print("[budget] WARNING: sampler drifted outside tolerance — the unbuilt-head "
                  "projection is not trustworthy; re-check the frame before relying on it.")
    print(f"[budget] PROJECTED TOTAL = {projected_total_mb:.1f} MB = {projected_pct:.1f}% "
          f"of {PAGES_SOFT_CAP_MB:.0f} MB cap")
    print(f"[budget] GATE: fail if projected > {GATE_MB:.1f} MB ({GATE_FRACTION*100:.0f}%)")

    gate_failed = projected_total_mb > GATE_MB
    verdict = "FAIL" if gate_failed else "PASS"
    print(f"[budget] GATE {verdict}")

    if not args.no_log:
        date_str = datetime.date.today().strftime("%d-%m-%Y")
        check_s = (f"sampler check {check[2] * 100:+.2f}% vs census" if check is not None
                   else "sampler check n/a (head not fully built)")
        row = (
            f"| **{date_str}** | **{mb['cards']:.1f} MB** | **{mb['concordance'] + mb['panini']:.1f} MB** | "
            f"**{mb['panini']:.2f} MB** | **{mb['reading']:.1f} MB** | **{mb['docs_js']:.1f} MB** | "
            f"**{mb['w']:.1f} MB** committed `w/` byte-true ({len(built)} head pages, "
            f"{census_bytes / max(len(built), 1) / 1024:.2f} KB/page) + {unbuilt_mb:.1f} MB unbuilt | "
            f"**{projected_total_mb:.1f} MB** | **{projected_pct:.1f}%** | "
            f"H4841 recalibrated gate (70% = {GATE_MB:.1f} MB, unchanged) — GATE {verdict}. "
            f"Total = whole published tree (Pages source `main:/`) incl. data/ {mb['data']:.1f} MB + "
            f"other {mb['other']:.1f} MB; served tiers alone {served_mb:.1f} MB = "
            f"{served_mb / PAGES_SOFT_CAP_MB * 100:.1f}%. {check_s}. D4 N={head_n_meta['n']}, "
            f"head with card {len(head)}. |\n"
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
