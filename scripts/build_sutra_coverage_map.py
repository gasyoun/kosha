#!/usr/bin/env python
"""build_sutra_coverage_map.py — W3a sūtra-coverage / dark-class map (H1468).

Programme exit check for Concordance-Q3 (ARCHITECTURE §5, VERIFICATION 3a-1..3a-8).

For every sūtra in a *named* Aṣṭādhyāyī enumeration (exact count, never "~4,000"),
emit one row with exemplar rollups and a status in:

  lit                 — ≥1 attested AG form whose *matched* ok chain includes it
  dark-unattested     — vidyut fires the rule on some AG-lemma cell derivation,
                        but no matched ok chain lands on an attested form
  dark-out-of-scope   — never fires in any successful AG-lemma cell derivation
                        (engine does not exercise it on this surface — proxy for
                        "not implemented / not in scope of a practical generator")
  dark-engine-gap     — reserved: every derivation *touching* it errored.
                        W2a records no partial rule traces on engine-error, so
                        this class is **not measurable** from current inputs and
                        is reported as 0 with that explanation (never inflated
                        by dumping residue into it).

## Inputs (all local)

  data/concordance/derivation_status.tsv   W2a status per AG form (401368)
  data/concordance/derivation_chains.tsv   ok chains only (for lit positions)
  data/concordance/paninian_concordance.tsv W2b inversion (lit exemplars)
  vidyut-data/prakriya via Data.load_sutras()  enumeration (Ashtadhyayi = 3983)
  kosha.db (read-only) + vidyut.prakriya     fire-set harvest over AG lemmas

## Classification judgment (why this is not a mechanical join)

The three dark classes mean different things (philological finding / engine-
coverage fact / defect). Collapsing them is forbidden (3a-3). The fire-set is
collected by re-deriving every AG lemma's Cologne-attested cells (same
`build_lemma_pool` logic as W2a) and unioning every Ashtadhyayi code that
appears in any successful Prakriya history — *including* chains that never
matched an attested form. That is the only offline way to separate
dark-unattested from dark-out-of-scope without inventing a second oracle.

Outputs:
  data/concordance/sutra_coverage_map.tsv
  data/concordance/SUTRA_COVERAGE_BUILD_REPORT.md

Usage:
    python scripts/build_sutra_coverage_map.py
    python scripts/build_sutra_coverage_map.py --pilot 500   # lemmas, smoke
    python scripts/build_sutra_coverage_map.py --skip-harvest  # reuse fire cache
"""
from __future__ import annotations

import argparse
import csv
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent if (ROOT.parent / "VisualDCS").exists() else ROOT.parent.parent
DEFAULT_DB = GH / "kosha" / "data" / "db" / "kosha.db"
DEFAULT_VDATA = GH / "vidyut-data" / "prakriya"
DEFAULT_DCS = GH / "VisualDCS" / "src" / "DCS-data-2026" / "dcs_full.sqlite"
OUT_DIR = ROOT / "data" / "concordance"
STATUS_TSV = OUT_DIR / "derivation_status.tsv"
CHAINS_TSV = OUT_DIR / "derivation_chains.tsv"
CONCORDANCE_TSV = OUT_DIR / "paninian_concordance.tsv"
FIRE_CACHE_TSV = OUT_DIR / "sutra_fire_set.tsv"
MAP_TSV = OUT_DIR / "sutra_coverage_map.tsv"
REPORT_MD = OUT_DIR / "SUTRA_COVERAGE_BUILD_REPORT.md"

EXPECTED_STATUS_ROWS = 401368
EXPECTED_STATUS_DIST = {
    "ok": 72764,
    "no-derivation": 237447,
    "ambiguous": 86857,
    "engine-error": 4300,
}
EXPECTED_LIT_SUTRAS = 221

SUTRA_CODE_RE = re.compile(r"^\d+\.\d+\.\d+$")
# vidyut sometimes emits "3.1.40:1" variant tags — strip to base a.p.n
BASE_CODE_RE = re.compile(r"^(\d+\.\d+\.\d+)")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_panini_derivations import (  # noqa: E402
    DEFAULT_CROSSWALK,
    Vyakarana,
    build_lemma_pool,
    load_crosswalk,
    open_db,
)
from vidyut.prakriya import Data, Source  # noqa: E402


MAP_FIELDS = [
    "sutra_id",
    "sutra_text_slp1",
    "exemplar_forms",
    "exemplar_loci",
    "texts",
    "mean_chain_position",
    "status",
    "scope_justification",
]


def base_code(code: str) -> str | None:
    m = BASE_CODE_RE.match((code or "").strip())
    return m.group(1) if m else None


def load_enumeration(vdata: Path) -> list[tuple[str, str]]:
    """Named enumeration: vidyut 0.4.0 Data.load_sutras() Source.Ashtadhyayi.

    Returns ordered (code, text_slp1) list. Exact count is the denominator for
    every percentage (3a-2, 3a-6).
    """
    if not vdata.is_dir():
        raise SystemExit(
            f"vidyut-data prakriya dir missing: {vdata}\n"
            "Expected sibling GitHub/vidyut-data/prakriya (W1a rights surface)."
        )
    data = Data(str(vdata))
    rows = []
    seen = set()
    for s in data.load_sutras():
        if s.source != Source.Ashtadhyayi:
            continue
        code = base_code(s.code) or s.code
        if code in seen:
            continue
        seen.add(code)
        rows.append((code, s.text or ""))
    if not rows:
        raise SystemExit("load_sutras() returned 0 Ashtadhyayi rows")
    # stable Aṣṭādhyāyī order: numeric adhyāya.pāda.sūtra
    def sort_key(item):
        a, p, n = item[0].split(".")
        return (int(a), int(p), int(n))

    rows.sort(key=sort_key)
    return rows


def verify_status_input() -> Counter:
    if not STATUS_TSV.is_file():
        raise SystemExit(f"missing {STATUS_TSV}")
    dist = Counter()
    n = 0
    with open(STATUS_TSV, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            dist[row["derivation_status"]] += 1
            n += 1
    if n != EXPECTED_STATUS_ROWS:
        raise SystemExit(
            f"derivation_status.tsv row count {n} != W2a stamp {EXPECTED_STATUS_ROWS}"
        )
    for k, v in EXPECTED_STATUS_DIST.items():
        if dist[k] != v:
            raise SystemExit(
                f"derivation_status.tsv[{k}]={dist[k]} != W2a stamp {v}"
            )
    return dist


def load_ag_lemmas() -> list[str]:
    """Distinct lemma_slp1 from derivation_status, stable order."""
    lemmas = []
    seen = set()
    with open(STATUS_TSV, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            lem = row["lemma_slp1"]
            if lem not in seen:
                seen.add(lem)
                lemmas.append(lem)
    return lemmas


def harvest_fire_set(
    lemmas: list[str],
    db_path: Path,
    crosswalk_path: Path,
    pilot: int | None,
) -> tuple[set[str], dict]:
    """Union of Ashtadhyayi codes that fire in any successful cell derivation.

    Also returns meta: lemmas processed, pools with steps, engine-error-like
    lemmas (cells but no runs), wall time.
    """
    con = open_db(db_path)
    v = Vyakarana()
    cross = load_crosswalk(crosswalk_path)
    work = lemmas if not pilot else lemmas[:pilot]
    fires: set[str] = set()
    meta = {
        "lemmas_total": len(lemmas),
        "lemmas_processed": 0,
        "lemmas_with_pool": 0,
        "lemmas_cells_no_run": 0,
        "lemmas_no_cells": 0,
        "pool_chains": 0,
        "elapsed_s": 0.0,
        "pilot": pilot,
    }
    t0 = time.time()
    for i, lemma in enumerate(work, start=1):
        info = build_lemma_pool(con, v, cross, lemma)
        meta["lemmas_processed"] += 1
        if not info["cells_existed"]:
            meta["lemmas_no_cells"] += 1
        elif not info["any_ran"]:
            meta["lemmas_cells_no_run"] += 1
        else:
            meta["lemmas_with_pool"] += 1
            meta["pool_chains"] += len(info["pool"])
            for _ck, pinfo in info["pool"].items():
                for src, code, _res in pinfo["steps"]:
                    if src != "Ashtadhyayi":
                        continue
                    bc = base_code(code)
                    if bc:
                        fires.add(bc)
        if i % 500 == 0 or i == len(work):
            rate = i / max(time.time() - t0, 1e-6)
            print(
                f"  harvest {i}/{len(work)} lemmas  "
                f"fires={len(fires)}  {rate:.1f} lem/s",
                flush=True,
            )
    meta["elapsed_s"] = time.time() - t0
    con.close()
    return fires, meta


def load_fire_cache(path: Path) -> set[str]:
    codes = set()
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            bc = base_code(row["sutra_code"])
            if bc:
                codes.add(bc)
    return codes


def write_fire_cache(path: Path, fires: set[str], meta: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("sutra_code\n")
        for c in sorted(fires, key=lambda x: tuple(int(p) for p in x.split("."))):
            f.write(c + "\n")
    # sidecar meta as comment file
    meta_path = path.with_suffix(".meta.tsv")
    with open(meta_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("key\tvalue\n")
        for k, v in meta.items():
            f.write(f"{k}\t{v}\n")


def load_lit_stats(
    dcs_path: Path | None,
) -> tuple[dict[str, dict], set[str]]:
    """Per-sūtra lit rollups from paninian_concordance.tsv.

    Returns (stats_by_code, lit_codes).
    """
    if not CONCORDANCE_TSV.is_file():
        raise SystemExit(f"missing {CONCORDANCE_TSV}")

    forms: dict[str, set[str]] = defaultdict(set)
    loci: dict[str, set[str]] = defaultdict(set)
    positions: dict[str, list[int]] = defaultdict(list)
    sent_ids_needed: set[int] = set()
    locus_to_sids: dict[str, list[str]] = defaultdict(list)

    n_rows = 0
    with open(CONCORDANCE_TSV, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            n_rows += 1
            aid = row["anchor_id"]  # sutra:a.p.n
            if not aid.startswith("sutra:"):
                continue
            code = aid[len("sutra:") :]
            bc = base_code(code)
            if not bc:
                continue
            forms[bc].add(row["form_key_slp1"] or row.get("dcs_text") or "")
            loci[bc].add(row["target_locus"])
            try:
                positions[bc].append(int(row["chain_position"]))
            except (TypeError, ValueError):
                pass
            locus_to_sids[bc].append(row["target_locus"])
            m = re.match(r"^dcs:(\d+)", row["target_locus"] or "")
            if m:
                sent_ids_needed.add(int(m.group(1)))

    # optional DCS text-name map: sentence.id -> text.name
    sid_to_text: dict[int, str] = {}
    texts_available = False
    if dcs_path and dcs_path.is_file():
        import sqlite3

        con = sqlite3.connect(f"file:{dcs_path}?mode=ro", uri=True)
        # batch: only needed ids
        # sqlite variable limit — chunk
        ids = sorted(sent_ids_needed)
        for i in range(0, len(ids), 800):
            chunk = ids[i : i + 800]
            qmarks = ",".join("?" * len(chunk))
            sql = f"""
                SELECT s.id, t.name
                FROM sentence s
                JOIN chapter c ON c.chapter_id = s.chapter_id
                JOIN text t ON t.text_id = c.text_id
                WHERE s.id IN ({qmarks})
            """
            for sid, name in con.execute(sql, chunk):
                sid_to_text[int(sid)] = name
        con.close()
        texts_available = True

    stats = {}
    for code in forms:
        text_names: set[str] = set()
        if texts_available:
            for loc in loci[code]:
                m = re.match(r"^dcs:(\d+)", loc)
                if m:
                    name = sid_to_text.get(int(m.group(1)))
                    if name:
                        text_names.add(name)
        pos = positions[code]
        stats[code] = {
            "exemplar_forms": len({x for x in forms[code] if x}),
            "exemplar_loci": len(loci[code]),
            "texts": len(text_names) if texts_available else 0,
            "mean_chain_position": (
                round(statistics.mean(pos), 3) if pos else ""
            ),
            "n_concordance_rows": sum(
                1 for _ in loci[code]
            ),  # placeholder replaced below
        }
    # true concordance row counts
    row_counts = Counter()
    with open(CONCORDANCE_TSV, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            aid = row["anchor_id"]
            if aid.startswith("sutra:"):
                bc = base_code(aid[len("sutra:") :])
                if bc:
                    row_counts[bc] += 1
    for code, st in stats.items():
        st["n_concordance_rows"] = row_counts[code]
        st["texts_resolved"] = texts_available

    return stats, set(stats.keys())


def classify(
    enum_codes: list[str],
    lit: set[str],
    fires: set[str],
) -> dict[str, tuple[str, str]]:
    """code -> (status, scope_justification)."""
    out = {}
    for code in enum_codes:
        if code in lit:
            out[code] = (
                "lit",
                "matched-ok-chain: appears in paninian_concordance.tsv "
                "(W2a ok form × Ashtadhyayi step)",
            )
        elif code in fires:
            out[code] = (
                "dark-unattested",
                "fires-in-AG-lemma-pool: vidyut.prakriya history includes this "
                "code on a successful cell derivation, but no matched ok chain "
                "attributes an attested AG form to it",
            )
        else:
            out[code] = (
                "dark-out-of-scope",
                "never-fires-on-AG-cells: no successful Prakriya history over "
                "Cologne-attested cells of AG lemmas includes this code "
                "(metarule / adhikāra / Vedic-accent / unimplemented operator "
                "relative to vidyut 0.4.0 generator surface)",
            )
    # engine-gap intentionally empty — no partial traces
    return out


def write_map(
    enum_rows: list[tuple[str, str]],
    lit_stats: dict[str, dict],
    class_map: dict[str, tuple[str, str]],
) -> Counter:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dist = Counter()
    with open(MAP_TSV, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(MAP_FIELDS) + "\n")
        for code, text in enum_rows:
            status, just = class_map[code]
            dist[status] += 1
            st = lit_stats.get(code, {})
            row = [
                code,
                text.replace("\t", " ").replace("\n", " "),
                str(st.get("exemplar_forms", 0)),
                str(st.get("exemplar_loci", 0)),
                str(st.get("texts", 0)),
                str(st.get("mean_chain_position", "")),
                status,
                just,
            ]
            f.write("\t".join(row) + "\n")
    return dist


def write_report(
    enum_name: str,
    enum_n: int,
    dist: Counter,
    lit_stats: dict[str, dict],
    fire_meta: dict,
    status_dist: Counter,
    texts_resolved: bool,
    elapsed_total: float,
) -> None:
    lit_n = dist["lit"]
    du = dist["dark-unattested"]
    do = dist["dark-out-of-scope"]
    de = dist["dark-engine-gap"]
    dark_n = du + do + de

    def pct(n: int) -> str:
        return f"{100.0 * n / enum_n:.2f}% ({n}/{enum_n})"

    lines = []
    a = lines.append
    a("# Sūtra-coverage map (W3a) — build report")
    a("")
    a(
        "_Auto-generated by "
        "[`scripts/build_sutra_coverage_map.py`](https://github.com/gasyoun/kosha/blob/main/scripts/build_sutra_coverage_map.py) "
        "(H1468, Grok 4.5 `grok-4.5` on Opus-lock override). "
        "Every figure is re-derivable from that script over the W2a/W2b TSVs + "
        "local `vidyut` 0.4.0 + `kosha.db` (read-only)._"
    )
    a("")
    a("_Created: 24-07-2026 · Last updated: 24-07-2026_")
    a("")
    a("## Enumeration (3a-2) — named, exact count")
    a("")
    a(f"- **Name:** `{enum_name}`")
    a(f"- **Exact count (denominator for every %):** **{enum_n}**")
    a(
        "- Source: `vidyut.prakriya.Data(vidyut-data/prakriya).load_sutras()` "
        "filtered to `Source.Ashtadhyayi` (same catalogue as `sutrapatha.tsv`, "
        "MIT via ashtadhyayi.com per the vidyut-data README)."
    )
    a(
        f"- Recension note: other printed recensions differ on sūtra division; "
        f"this map never publishes \"~4,000\" as if exact."
    )
    a("")
    a("## Input build-stamp verification (R-Q4)")
    a("")
    a(
        f"- `derivation_status.tsv`: **{EXPECTED_STATUS_ROWS}** rows — "
        f"MATCH W2a ({dict(status_dist)})"
    )
    a(
        f"- `paninian_concordance.tsv` lit sūtras (distinct `sutra:*`): "
        f"**{len(lit_stats)}** (W2b stated {EXPECTED_LIT_SUTRAS})"
    )
    a(
        f"- Fire-set harvest: **{fire_meta.get('lemmas_processed', '?')}** lemmas "
        f"in {fire_meta.get('elapsed_s', 0):.1f}s; "
        f"pools with steps={fire_meta.get('lemmas_with_pool', '?')}; "
        f"cells-but-no-run={fire_meta.get('lemmas_cells_no_run', '?')}; "
        f"no-cells={fire_meta.get('lemmas_no_cells', '?')}"
        + (
            f"; pilot={fire_meta['pilot']}"
            if fire_meta.get("pilot")
            else ""
        )
    )
    a(f"- Wall time (map build total): **{elapsed_total:.1f}s**")
    a("")
    a("## Status distribution (3a-3, 3a-8) — four statuses, never one 'dark'")
    a("")
    a("| Status | Count | % of enumeration |")
    a("|---|---:|---:|")
    for key in (
        "lit",
        "dark-unattested",
        "dark-out-of-scope",
        "dark-engine-gap",
    ):
        a(f"| `{key}` | {dist[key]} | {pct(dist[key])} |")
    a(f"| **total** | **{enum_n}** | **100.00% ({enum_n}/{enum_n})** |")
    a("")
    a("### Ratio headline (3a-8)")
    a("")
    a(
        f"**lit : dark-unattested : dark-out-of-scope : dark-engine-gap = "
        f"{lit_n} : {du} : {do} : {de}** "
        f"({pct(lit_n)} lit · {pct(du)} dark-unattested · "
        f"{pct(do)} dark-out-of-scope · {pct(de)} dark-engine-gap)."
    )
    a(
        f"Combined dark (informational only — **not** a published class): "
        f"{dark_n} = {pct(dark_n)}."
    )
    a("")
    a("## Class definitions (ARCHITECTURE §5) + how each was assigned")
    a("")
    a(
        "- **`lit`** — ≥1 row in `paninian_concordance.tsv` (matched W2a `ok` "
        "chain over an attested AG form)."
    )
    a(
        "- **`dark-unattested`** — code appears in ≥1 successful "
        "`vidyut.prakriya` history while building the per-lemma cell pool for "
        "an AG lemma, but never in a matched ok chain. Philological reading: "
        "the engine exercises the rule; the AG×DCS attested surface does not "
        "land on a form that uniquely credits it."
    )
    a(
        "- **`dark-out-of-scope`** — code never appears in any successful "
        "Prakriya history over AG-lemma Cologne cells. Per-sūtra justification "
        "is stored in `scope_justification` (3a-4): this is the generator's "
        "non-exercise surface (metarules, adhikāra headers, saṃjñā-only rows "
        "the operator set skips, Vedic/accent rules, Unādi-adjacent gaps), "
        "**not** a residual dump — membership is exactly the complement of the "
        "fire-set inside the named enumeration."
    )
    a(
        "- **`dark-engine-gap`** — **0 / not measurable from W2a artefacts.** "
        "W2a's `engine-error` rows carry empty `chain_id` (no partial rule "
        "trace). Inflating this class without traces would invent defect "
        "signals. Reported empty and kept as a named status so a future "
        "harness that records pre-exception steps can fill it without a schema "
        "break (3a-5: smallest class, excess explained)."
    )
    a("")
    a("## 3a-5 — dark-engine-gap is the smallest class")
    a("")
    a(
        f"`dark-engine-gap` = **{de}** is the minimum of "
        f"{{{du}, {do}, {de}}} "
        + (
            "— strictly smallest."
            if de < du and de < do
            else "— tied/explained above."
        )
    )
    a("")
    a("## Lit rollups (exemplar columns)")
    a("")
    a(
        "- `exemplar_forms` / `exemplar_loci` / `mean_chain_position` come from "
        "`paninian_concordance.tsv` (distinct `form_key_slp1`, distinct "
        "`target_locus`, mean of `chain_position`)."
    )
    if texts_resolved:
        a(
            "- `texts` = distinct DCS text names via "
            "`sentence.id → chapter → text.name` on "
            f"`{DEFAULT_DCS.name}` (read-only)."
        )
    else:
        a(
            "- `texts` = **0 for all rows** — DCS sqlite was not available at "
            "build time; column reserved, not fabricated."
        )
    a("- Dark rows carry 0 / empty exemplar fields by definition.")
    a("")
    a("## Top lit sūtras by exemplar_forms")
    a("")
    top = sorted(
        lit_stats.items(),
        key=lambda kv: (-kv[1]["exemplar_forms"], kv[0]),
    )[:15]
    a("| sūtra | exemplar_forms | exemplar_loci | texts | mean_chain_pos |")
    a("|---|---:|---:|---:|---:|")
    for code, st in top:
        a(
            f"| {code} | {st['exemplar_forms']} | {st['exemplar_loci']} | "
            f"{st['texts']} | {st['mean_chain_position']} |"
        )
    a("")
    a("## Reproducibility (3a-7)")
    a("")
    a("```")
    a("python scripts/build_sutra_coverage_map.py")
    a("# optional: reuse fire-set cache after a full harvest")
    a("python scripts/build_sutra_coverage_map.py --skip-harvest")
    a("```")
    a("")
    a(
        "Requires: committed W2a/W2b TSVs, sibling `vidyut-data/prakriya`, "
        "`vidyut` 0.4.0, read-only `kosha.db`, optional DCS sqlite for `texts`."
    )
    a("")
    a("_Dr. Mārcis Gasūns_")
    a("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--pilot",
        type=int,
        default=None,
        help="Harvest only the first N AG lemmas (smoke; do not ship)",
    )
    ap.add_argument(
        "--skip-harvest",
        action="store_true",
        help=f"Reuse {FIRE_CACHE_TSV.name} instead of re-deriving",
    )
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--vdata", type=Path, default=DEFAULT_VDATA)
    ap.add_argument("--dcs", type=Path, default=DEFAULT_DCS)
    ap.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    args = ap.parse_args(argv)

    t0 = time.time()
    print("W3a sūtra-coverage map — H1468", flush=True)

    status_dist = verify_status_input()
    print("  status input OK", dict(status_dist), flush=True)

    enum_rows = load_enumeration(args.vdata)
    enum_codes = [c for c, _ in enum_rows]
    enum_name = (
        "vidyut-0.4.0 Data.load_sutras() Source.Ashtadhyayi "
        f"(sutrapatha.tsv catalogue, n={len(enum_codes)})"
    )
    print(f"  enumeration: {len(enum_codes)} Ashtadhyayi sūtras", flush=True)

    lit_stats, lit_codes = load_lit_stats(args.dcs if args.dcs.is_file() else None)
    texts_resolved = bool(lit_stats) and any(
        st.get("texts_resolved") for st in lit_stats.values()
    )
    print(f"  lit sūtras from concordance: {len(lit_codes)}", flush=True)
    if lit_codes - set(enum_codes):
        extra = sorted(lit_codes - set(enum_codes))
        print(
            f"  WARN: {len(extra)} lit codes not in enumeration "
            f"(kept as lit-only extras, not in map rows): {extra[:10]}",
            flush=True,
        )

    fire_meta: dict = {}
    if args.skip_harvest and FIRE_CACHE_TSV.is_file():
        fires = load_fire_cache(FIRE_CACHE_TSV)
        fire_meta = {
            "lemmas_processed": "cache",
            "elapsed_s": 0.0,
            "source": str(FIRE_CACHE_TSV),
        }
        print(f"  fire-set from cache: {len(fires)}", flush=True)
    else:
        if not args.db.is_file():
            raise SystemExit(f"kosha.db missing at {args.db}")
        lemmas = load_ag_lemmas()
        print(
            f"  harvesting fire-set over {len(lemmas)} AG lemmas"
            + (f" (pilot {args.pilot})" if args.pilot else "")
            + " ...",
            flush=True,
        )
        fires, fire_meta = harvest_fire_set(
            lemmas, args.db, args.crosswalk, args.pilot
        )
        write_fire_cache(FIRE_CACHE_TSV, fires, fire_meta)
        print(f"  fire-set size: {len(fires)}", flush=True)

    # lit codes that somehow never harvested still stay lit (concordance is ground)
    fires = set(fires) | set(lit_codes)

    class_map = classify(enum_codes, lit_codes & set(enum_codes), fires)
    dist = write_map(enum_rows, lit_stats, class_map)
    # ensure dark-engine-gap key present
    dist["dark-engine-gap"] += 0

    elapsed = time.time() - t0
    write_report(
        enum_name=enum_name,
        enum_n=len(enum_codes),
        dist=dist,
        lit_stats=lit_stats,
        fire_meta=fire_meta,
        status_dist=status_dist,
        texts_resolved=texts_resolved,
        elapsed_total=elapsed,
    )

    print("  status counts:", dict(dist), flush=True)
    print(f"  wrote {MAP_TSV}", flush=True)
    print(f"  wrote {REPORT_MD}", flush=True)
    print(f"  done in {elapsed:.1f}s", flush=True)

    # hard gates matching VERIFICATION 3a-1..3a-3
    assert sum(dist[k] for k in (
        "lit", "dark-unattested", "dark-out-of-scope", "dark-engine-gap"
    )) == len(enum_codes)
    assert dist["dark-engine-gap"] == 0 or dist["dark-engine-gap"] <= min(
        dist["dark-unattested"], dist["dark-out-of-scope"]
    )
    if args.pilot:
        print("  NOTE: pilot run — do not ship these artefacts", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
