#!/usr/bin/env python
"""Build the minimal kosha sense-dating bucket layer (H4019).

ADDITIVE data layer only: the printed PWG sense order is never reordered, no
PWG→RU entry text changes. Buckets are machine-readable kosha data; the
preface caveat («первое засвидетельствование в цитируемом корпусе, не
происхождение значения» / "first attestation in the cited corpus, not the
origin of the meaning") ships in data/dating/README.md and in every render
tooltip (app/dating_hydrate.py).

Evidence base (measured upstream, consumed here — never re-derived):
  * H3673 verb probe (GO×WEAK 63%) + H4016 nomina probe (GO×STRONG 78.3%).
    Seed = H4016's hand-checked alias map + per-citation classification:
    data/dating/evidence/nomen.classification.0309.json — every hand tier
    keeps its era/via verbatim; this build never overrides a seed call.
  * Date sources, tiered:
      (1) Dharmamitra chronology snapshot (1,618 works, 6 eras, primary)
      (2) DCS date table 2021 (251 texts, secondary; seed-verbatim only)
      (3) hand:class / hand:siglum / hand:disputed (tertiary, with reasons)
    Disputed / boundary / recension-dependent → NULL, never forced.
  * Canonical work-identity spine: citation_canon.json topTexts (50 canon
    texts + variants) — DM/DCS dates join onto CANON IDENTITY, never raw
    title strings. String-level matching is only the fold-prefix match
    against canon variants and the curated hand table; anything that does
    not match a curated identity stays NULL (via=no-match), never silent.

Inputs (all committed):
  data/concordance/sense_corpus_concordance.tsv   per-sense <ls> loci (conf ≥ 0.99)
  data/dating/evidence/nomen.classification.0309.json   H4016 seed (verbatim)
  data/dating/evidence/dharmamitra-chronology.snapshot-2026-09-03.json
  data/dating/evidence/dcs-text-dates-2021.tsv
  data/dating/evidence/citation-canon-top-texts.snapshot-2026-09-03.json
  data/dating/works_hand.tsv   curated hand layer (canon_dm joins, hand calls,
                               UNDATEABLE classes, conflict notes)

Outputs (derived — derive-don't-store, `--check` recompute == stored):
  data/dating/work_dates.tsv (+ .json)   per distinct resolved locus prefix:
                                         work identity → era bucket + via + reason
  data/dating/abbrev_map.tsv             per PWG citation abbreviation: the
                                         work it resolves to (mode share ≥
                                         ABBREV_MIN_SHARE) + era — the render
                                         badge lookup (P3)
  data/dating/sense_dating.tsv           per sense (slp1, hom, sense_id):
                                         n_cites, n_dateable, first_era,
                                         bucket_via, marginal, conflicts
  data/dating/COVERAGE_REPORT.md         era × via × mass-share + spot-check

Bucket vocabulary (era rank order): vedic < epic-sutra < classical <
early-medieval < late-medieval. NULL era = UNDATEABLE / unresolved — always
carried, never dropped.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATING = REPO / "data" / "dating"
EVIDENCE = DATING / "evidence"
CONCORDANCE = REPO / "data" / "concordance" / "sense_corpus_concordance.tsv"

ERAS = ["vedic", "epic-sutra", "classical", "early-medieval", "late-medieval"]
ERA_RANK = {e: i for i, e in enumerate(ERAS)}
UNDATEABLE = "UNDATEABLE"
UNRESOLVED = "UNRESOLVED"
MIN_CONF = 0.99
ABBREV_MIN_SHARE = 0.9

_DM_ERA_MAP = {
    "Vedic": "vedic",
    "Epic & Sutra": "epic-sutra",
    "Classical": "classical",
    "Early Medieval": "early-medieval",
    "Late Medieval": "late-medieval",
    "Outside display range": None,
}

_MARKER_RE = re.compile(r"^\s*\?\s*\[Cologne Addition\]")
_COORD_TAIL_RE = re.compile(r"\s+\d[\d,.\-– ()abxfg.]*$")
_DCS_UNDATED = 2500


def fold(s: str) -> str:
    """Case/diacritic/PW-digit-encoding fold. S̃→S (combining tilde stripped),
    'SAM5BHAVA'→'SAMBHAVA' (PW's digit combining-mark encodings dropped)."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[45]", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def locus_prefix(locus: str) -> str:
    """Resolved locus string minus a trailing coordinate block."""
    loc = _MARKER_RE.sub("", locus)
    return _COORD_TAIL_RE.sub("", loc).strip()


def is_unresolved(locus: str) -> bool:
    return bool(_MARKER_RE.match(locus)) or not locus.strip()


# ---------------------------------------------------------------- inputs


def load_seed() -> dict[str, dict]:
    """H4016 seed: fold(locus_prefix) → era/via (verbatim; conflicts rejected).

    UNDATEABLE seed calls are KEPT — every hand tier keeps its reason string
    (hand:disputed, anthology, modern-ref, edition-siglum are real undateable
    classes). Only via='no-rule' rows (the probe applied no rule) are dropped:
    silence is not a call, and the hand table may extend over them."""
    data = json.loads((EVIDENCE / "nomen.classification.0309.json").read_text())
    by_fold: dict[str, Counter] = defaultdict(Counter)
    via_by_fold: dict[str, Counter] = defaultdict(Counter)
    for sense in data:
        for det in sense.get("details", []):
            locus = det.get("locus", "")
            if is_unresolved(locus):
                continue
            f = fold(locus_prefix(locus))
            if not f:
                continue
            if det["era"] == UNDATEABLE and det["via"] == "no-rule":
                continue
            by_fold[f][det["era"]] += 1
            via_by_fold[f][det["via"]] += 1
    out = {}
    for f, eras in by_fold.items():
        if len(eras) > 1:
            raise SystemExit(f"seed fold conflict for {f!r}: {dict(eras)}")
        era = next(iter(eras))
        vias = via_by_fold[f]
        out[f] = {"era": "" if era == UNDATEABLE else era,
                  "via": vias.most_common(1)[0][0], "source": "seed"}
    return out


def load_hand() -> list[dict]:
    with open(DATING / "works_hand.tsv") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def load_dm() -> dict[str, list[dict]]:
    data = json.loads(
        (EVIDENCE / "dharmamitra-chronology.snapshot-2026-09-03.json").read_text()
    )
    fam: dict[str, list[dict]] = defaultdict(list)
    for w in data["works"]:
        fam[fold(w["title"])].append(w)
    return fam


def dm_family_era(fam: dict[str, list[dict]], key: str) -> tuple[str | None, str, str]:
    """Family-mode era + a minority-stratum note for one dm_title_folds key."""
    hits = [w for f, ws in fam.items() if f == key or f.startswith(key + " ") for w in ws]
    if not hits:
        raise SystemExit(f"H4019 build: DM family missing for {key!r} — "
                         "the hand-verified canon_dm join does not match the snapshot")
    eras = Counter(_DM_ERA_MAP.get(w.get("era")) for w in hits)
    if len([e for e in eras if e]) > 1:
        era, n = eras.most_common(1)[0]
        minority = {e: c for e, c in eras.items() if e and e != era}
        note = (f"DM chunk strata vary: mode {era} ({n}/{len(hits)} chunks), "
                f"minority {minority} — recorded, not averaged")
        return era, hits[0].get("dateEstimate", ""), note
    era = eras.most_common(1)[0][0]
    return era, hits[0].get("dateEstimate", ""), ""


def load_canon_variants() -> dict[str, str]:
    """fold(variant) → canon text, for the identity spine."""
    data = json.loads(
        (EVIDENCE / "citation-canon-top-texts.snapshot-2026-09-03.json").read_text()
    )
    out = {}
    for t in data["topTexts"]:
        for v in t["variants"].split(";"):
            f = fold(v)
            if len(f) >= 4:
                out.setdefault(f, t["text"])
    return out


def load_dcs() -> dict[str, tuple[int, int]]:
    out = {}
    with open(EVIDENCE / "dcs-text-dates-2021.tsv") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            out[r["text"]] = (int(r["date1"]), int(r["date2"]))
    return out


# ---------------------------------------------------------------- resolver


class Resolver:
    """locus + abbreviation → work identity + era bucket (H4019 tier order)."""

    def __init__(self):
        self.seed = load_seed()
        self.hand = load_hand()
        self.dm = load_dm()
        self.canon = load_canon_variants()
        self.dcs = load_dcs()
        self._hand_by_fold: list[tuple[str, dict]] = []
        self._canon_dm: list[tuple[list[str], dict]] = []
        self._hand_by_abbrev: dict[str, dict] = {}
        self.dm_notes: dict[str, str] = {}
        for row in self.hand:
            kind = row["kind"]
            if kind == "note":
                continue
            if kind == "canon_dm":
                keys = [k.strip() for k in row["dm_title_folds"].split(";") if k.strip()]
                era, est, note = dm_family_era(self.dm, keys[0])
                expected = row["era"]
                if era != expected:
                    raise SystemExit(
                        f"H4019 build: canon_dm join for {row['work_key']!r} resolved "
                        f"{era!r} but the hand-verified expectation is {expected!r} — "
                        "the DM snapshot moved; re-verify before shipping")
                if note:
                    self.dm_notes[row["work_key"]] = note
                self._canon_dm.append(
                    ([fold(row["match_locus_folds"])], row, era, est))
            else:
                folds = [fold(x) for x in row["match_locus_folds"].split(";") if x.strip()]
                self._hand_by_fold.extend((f, row) for f in folds)
                for ab in [a.strip() for a in row["match_abbrevs"].split(";") if a.strip()]:
                    self._hand_by_abbrev.setdefault(ab, row)
        self.stats = Counter()

    def identity_for(self, pf: str) -> str:
        """Stable work identity for a seed fold: the canon_dm work whose match
        fold prefix-matches it, else the fold itself (coordinate-suffix locus
        variants of one work must not fragment the identity)."""
        if getattr(self, "_ident_cache", None) is None:
            self._ident_cache = {}
        hit = self._ident_cache.get(pf)
        if hit is not None:
            return hit
        hit = pf
        for folds, row, _era, _est in self._canon_dm:
            if any(pf == f or pf.startswith(f + " ") for f in folds):
                hit = row["work_key"]
                break
        self._ident_cache[pf] = hit
        return hit

    def resolve(self, locus: str, abbrev: str) -> dict:
        abbrev = abbrev.strip()
        pf = fold(locus_prefix(locus))
        # 1. seed (H4016 verbatim — highest precedence for resolved loci;
        #       'no-rule' seed rows never enter the map: silence is not a call)
        if pf and pf in self.seed:
            self.stats["seed"] += 1
            s = self.seed[pf]
            via = s["via"]
            if via == "dcs":
                reason = ("H4016 hand-checked seed call via the DCS date table 2021 "
                          "(per-citation evidence in the seed JSON, data/dating/evidence/)")
            elif via == "dharmamitra":
                reason = "H4016 hand-checked seed call via the Dharmamitra chronology"
            else:
                reason = f"H4016 hand-checked seed call ({via})"
            return {"work_key": self.identity_for(pf), "display": "", "era": s["era"],
                    "date_range": "", "via": via, "tier": "seed",
                    "reason": reason, "flags": "", "notes": ""}
        # 2. hand fold rows
        if pf:
            for f, row in self._hand_by_fold:
                if pf == f or pf.startswith(f + " "):
                    self.stats["hand"] += 1
                    return self._row_result(row, pf)
            # 3. canon_dm spine
            for folds, row, era, est in self._canon_dm:
                if any(pf == f or pf.startswith(f + " ") for f in folds):
                    self.stats["canon_dm"] += 1
                    return self._row_result(row, pf, era=era, date_range=est,
                                            notes=self.dm_notes.get(row["work_key"], ""))
            # 4. hand abbrev binding on a resolved locus that matched nothing
            row = self._hand_by_abbrev.get(abbrev)
            if row is not None:
                self.stats["hand_abbrev"] += 1
                return self._row_result(row, pf)
            self.stats["no_match"] += 1
            return {"work_key": "", "display": "", "era": "", "date_range": "",
                    "via": "no-match", "tier": "no-match",
                    "reason": "no curated identity matches this resolved locus",
                    "flags": "", "notes": ""}
        # 5. unresolved locus → second chance via unambiguous abbrev binding
        row = self._hand_by_abbrev.get(abbrev)
        if row is not None:
            self.stats["unresolved_abbrev"] += 1
            return self._row_result(row, pf)
        self.stats["unresolved"] += 1
        return {"work_key": "", "display": "", "era": "", "date_range": "",
                "via": "unresolved", "tier": "unresolved",
                "reason": "PWG locus resolution failed (? [Cologne Addition]); "
                          "no unambiguous abbreviation binding",
                "flags": "", "notes": ""}

    @staticmethod
    def _row_result(row: dict, pf: str, era: str | None = None,
                    date_range: str | None = None, notes: str = "") -> dict:
        era = era if era is not None else row["era"]
        return {"work_key": row["work_key"], "display": row["display"],
                "era": "" if era == UNDATEABLE else era,
                "date_range": date_range if date_range is not None else row["date_range"],
                "via": row["via"], "tier": row["kind"],
                "reason": row["reason"], "flags": row["flags"],
                "notes": (notes + ("; " if notes and row["notes"] else "") + row["notes"]).strip("; ")}


# ---------------------------------------------------------------- build


def read_concordance() -> list[dict]:
    rows = []
    with open(CONCORDANCE) as f:
        for r in csv.DictReader(f, delimiter="\t"):
            try:
                conf = float(r["conf"])
            except ValueError:
                continue
            if conf >= MIN_CONF:
                rows.append(r)
    return rows


def build_work_dates(conc: list[dict], resolver: Resolver) -> tuple[list[dict], dict[str, dict]]:
    per_prefix: dict[str, dict] = {}
    for r in conc:
        locus, abbrev = r["locus"], r["source"].strip()
        pf = locus_prefix(locus)
        key = pf if pf else locus.strip()
        ent = per_prefix.get(key)
        if ent is None:
            ent = per_prefix[key] = {"locus_prefix": pf, "fold": fold(pf),
                                     "n_rows": 0, **resolver.resolve(locus, abbrev)}
        else:
            ent["n_rows"] += 1
    # abbreviation → work identity: row-level mode over RESOLVED rows only.
    # An abbreviation that resolves to more than one work identity is
    # homonym-dense (the H1684 warning) and is demoted to unusable for badges.
    ab_works: Counter = Counter()
    ab_total: Counter = Counter()
    for r in conc:
        ab = r["source"].strip()
        ab_total[ab] += 1
        pf = locus_prefix(r["locus"])
        ent = per_prefix.get(pf if pf else r["locus"].strip())
        if ent is not None and ent["era"]:
            ab_works[(ab, ent["work_key"])] += 1
    best: dict[str, tuple[str, int]] = {}
    for (ab, wk), n in ab_works.items():
        if best.get(ab, ("", -1))[1] < n:
            best[ab] = (wk, n)
    abbrev_map: dict[str, dict] = {}
    work_by_key = {}
    for e in per_prefix.values():
        work_by_key.setdefault(e["work_key"], e)
    for ab, total in ab_total.items():
        wk, n = best.get(ab, ("", 0))
        share = n / total if total else 0.0
        ent = work_by_key.get(wk)
        if ent is None or share < ABBREV_MIN_SHARE:
            continue
        abbrev_map[ab] = {"abbrev": ab, "work_key": wk,
                          "display": ent["display"] or ent["work_key"],
                          "era": ent["era"],
                          "via": ent["via"], "mode_share": round(share, 3)}
    return out_sorted(per_prefix), abbrev_map


def out_sorted(per_prefix: dict[str, dict]) -> list[dict]:
    return sorted(per_prefix.values(), key=lambda e: -e["n_rows"])


def build_sense_dating(conc: list[dict], per_prefix: dict[str, dict]) -> list[dict]:
    def row_key(locus: str):
        pf = locus_prefix(locus)
        return pf if pf else locus.strip()

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in conc:
        groups[(r["slp1"], r["hom"], r["sense_id"])].append(r)
    out = []
    for (slp1, hom, sense_id), rows in groups.items():
        n_cites = len(rows)
        eras, vias, notes, ceiling_only_win = [], set(), [], True
        n_dateable = 0
        for r in rows:
            ent = per_prefix.get(row_key(r["locus"]))
            if ent is None or not ent["era"]:
                continue
            n_dateable += 1
            eras.append((ERA_RANK[ent["era"]], ent["era"], ent))
        first_era = ""
        bucket_via = ""
        if eras:
            best = min(e for e, _, _ in eras)
            winners = [ent for rank, era, ent in eras if rank == best]
            first_era = winners[0]["era"]
            bucket_via = "+".join(sorted({w["via"] for w in winners}))
            ceiling_only_win = all("low_value" in (w["flags"] or "") for w in winners)
            seen_notes = set()
            for w in winners:
                for n in (w["notes"], w["reason"]):
                    if n and n not in seen_notes:
                        seen_notes.add(n)
                        notes.append(n)
                if "low_value" in (w["flags"] or ""):
                    notes.append("terminus-ceiling work: attestation value low")
        marginal = 1 if (n_dateable == 1 or (n_dateable > 0 and ceiling_only_win)) else 0
        if n_dateable == 0:
            all_unresolved = all(is_unresolved(r["locus"]) for r in rows)
            cls = UNRESOLVED if all_unresolved else UNDATEABLE
        else:
            cls = "DATEABLE-MARGINAL" if marginal else "DATEABLE"
        out.append({"slp1": slp1, "hom": hom, "sense_id": sense_id,
                    "n_cites": n_cites, "n_dateable": n_dateable,
                    "first_era": first_era, "bucket_via": bucket_via,
                    "marginal": marginal, "class": cls,
                    "conflict_notes": " | ".join(notes)})
    out.sort(key=lambda r: (r["slp1"], r["hom"], r["sense_id"]))
    return out


def write_tsv(path: Path, cols: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", lineterminator="\n",
                           extrasaction="raise")
        w.writeheader()
        w.writerows(rows)


WORK_COLS = ["locus_prefix", "fold", "work_key", "display", "era", "date_range",
             "via", "tier", "reason", "flags", "notes", "n_rows"]
SENSE_COLS = ["slp1", "hom", "sense_id", "n_cites", "n_dateable", "first_era",
              "bucket_via", "marginal", "class", "conflict_notes"]
ABBREV_COLS = ["abbrev", "work_key", "display", "era", "via", "mode_share"]


def run(out_dir: Path = DATING) -> dict:
    conc = read_concordance()
    resolver = Resolver()
    work_rows, abbrev_map = build_work_dates(conc, resolver)
    per_prefix = {r["locus_prefix"] or r["fold"]: r for r in work_rows}
    sense_rows = build_sense_dating(conc, per_prefix)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(out_dir / "work_dates.tsv", WORK_COLS, work_rows)
    write_tsv(out_dir / "abbrev_map.tsv", ABBREV_COLS,
              sorted(abbrev_map.values(), key=lambda r: r["abbrev"]))
    write_tsv(out_dir / "sense_dating.tsv", SENSE_COLS, sense_rows)
    (out_dir / "work_dates.json").write_text(
        json.dumps(work_rows, ensure_ascii=False, indent=1))

    report = coverage_report(conc, work_rows, sense_rows, resolver)
    (out_dir / "COVERAGE_REPORT.md").write_text(report)
    return {"n_conc_rows": len(conc), "n_works": len(work_rows),
            "n_abbrevs": len(abbrev_map), "n_senses": len(sense_rows),
            "resolver": dict(resolver.stats)}


def coverage_report(conc, work_rows, sense_rows, resolver) -> str:
    by_prefix: dict[str, dict] = {}
    for e in work_rows:
        if e["locus_prefix"]:
            by_prefix[e["locus_prefix"]] = e
    era_via = defaultdict(int)
    undateable_via = Counter()
    unresolved = 0
    for r in conc:
        pf = locus_prefix(r["locus"])
        ent = by_prefix.get(pf)
        if ent is None or not ent["era"]:
            if ent is not None and ent["tier"] != "unresolved":
                undateable_via[ent["via"] or "no-match"] += 1
            else:
                unresolved += 1
            continue
        era_via[(ent["era"], ent["via"])] += 1
    total = sum(era_via.values()) + sum(undateable_via.values()) + unresolved
    lines = [
        "# Sense-dating layer — coverage report (H4019)",
        "",
        f"_Generated from `data/concordance/sense_corpus_concordance.tsv` "
        f"(conf ≥ {MIN_CONF}); builder `scripts/build_sense_dating.py` "
        f"(derive-don't-store; `--check` recomputes). "
        f"Resolver stats: {dict(resolver.stats)}._",
        "",
        f"**Instances:** {total:,} citation instances over {len(sense_rows):,} senses; "
        f"{sum(era_via.values()):,} dateable "
        f"({100.0 * sum(era_via.values()) / max(total, 1):.1f}%).",
        "",
        "## Era × via (citation instances)",
        "",
        "| era | " + " | ".join(sorted({v for _, v in era_via})) + " | total | share |",
        "|---|" + "---|" * (len({v for _, v in era_via}) + 2),
    ]
    vias = sorted({v for _, v in era_via})
    for era in ERAS:
        cells = [era_via.get((era, v), 0) for v in vias]
        tot = sum(cells)
        if tot:
            lines.append(f"| {era} | " + " | ".join(str(c) for c in cells) +
                         f" | {tot:,} | {100.0 * tot / total:.1f}% |")
    lines += ["| **undateable** | " + " | ".join(str(undateable_via.get(v, 0)) for v in vias) +
              f" | {sum(undateable_via.values()):,} | "
              f"{100.0 * sum(undateable_via.values()) / total:.1f}% |"]
    lines += ["| **unresolved loci** | " + " | ".join("—" for _ in vias) +
              f" | {unresolved:,} | {100.0 * unresolved / total:.1f}% |",
              "",
              "## Work-level table (top 40 by instances)",
              "",
              "| locus prefix | work | era | via | tier | instances |",
              "|---|---|---|---|---|---|"]
    for e in work_rows[:40]:
        name = e["display"] or e["work_key"] or "(unmatched)"
        lines.append(f"| {e['locus_prefix'][:48]} | {name[:36]} | "
                     f"{e['era'] or UNDATEABLE} | {e['via']} | {e['tier']} | {e['n_rows']:,} |")
    lines += ["",
              "## Nomina-first spot-check — H4016 probe senses through the new layer",
              "",
              "The probe's 20 hand-classified senses (5 nominal headwords) recomputed "
              "by the build; agreement with the H4016 hand calls is the acceptance "
              "spot-check (bounded, documented).",
              "",
              "| sense | probe class | probe era | layer class | layer era | agree |",
              "|---|---|---|---|---|---|"]
    probe = json.loads((EVIDENCE / "nomen.classification.0309.json").read_text())
    layer_by_key = {(r["slp1"], r["hom"], r["sense_id"]): r for r in sense_rows}
    agree = mism = 0
    for s in probe:
        lr = next((r for (s1, _h, sid), r in layer_by_key.items()
                   if s1 == s["slp1"] and sid == s["sense_id"]), None)
        probe_era = s["bucket"] if s["bucket"] != "UNDATEABLE" else ""
        layer_era = lr["first_era"] if lr else ""
        ok = (probe_era == layer_era)
        cls_ok = (lr["class"].startswith("DATEABLE") if lr else False) == \
                 s["class"].startswith("ORDERABLE")
        if ok:
            agree += 1
        else:
            mism += 1
        lines.append(f"| {s['slp1']} {s['sense_id']} | {s['class']} | {probe_era} | "
                     f"{lr['class'] if lr else '?'} | {layer_era} | "
                     f"{'yes' if ok and cls_ok else 'NO'} |")
    lines += ["",
              f"**Era agreement: {agree}/{agree + mism}.**",
              "",
              "## Verb-root honesty check (expect all-tie vedic)",
              "",
              "The verb probe predicted high-frequency verb senses sit at the ṚV "
              "floor — all-tie. Sampled here: `han` 2, `car` 4, `gam` 3a.",
              "",
              "| sense | n_cites | n_dateable | first_era | class |",
              "|---|---|---|---|---|"]
    for key in [("han", "1", "2"), ("car", "", "4"), ("gam", "1", "3a")]:
        r = layer_by_key.get(key)
        if r:
            lines.append(f"| {key[0]} {key[2]} | {r['n_cites']} | {r['n_dateable']} | "
                         f"{r['first_era'] or UNDATEABLE} | {r['class']} |")
    lines += ["",
              "## Honest residue",
              "",
              f"- Unresolved loci (`? [Cologne Addition]`): {unresolved:,} instances — "
              "a resolution gap, not a dating gap (H4016 §5).",
              f"- No-match resolved loci: {resolver.stats.get('no_match', 0):,} distinct "
              "prefixes below the curated top-N — carried as NULL, never forced.",
              "- Disputed/boundary works stay UNDATEABLE by design "
              "(Suśruta layered, Medinīkoṣa, Kāmandakīya, Kāvyādarśa, Mṛcchakaṭikā, "
              "Mudrārākṣasa, Śrutabodha, Rājanighaṇṭu, Vaikhānasadharmasūtra).",
              "- Śabdakalpadruma carries the terminus-ceiling discount "
              "(H4019 addendum §1): low attestation value, marginal-flagged "
              "when it is the only winner.",
              "",
              "## Preface caveat (must ship with any render of this layer)",
              "",
              "«Первое засвидетельствование в цитируемом корпусе, не происхождение "
              "значения.» — *First attestation in the cited corpus, not the origin "
              "of the meaning.* The printed PWG sense order is never reordered by "
              "this layer; buckets are additive machine-readable data.",
              ""]
    return "\n".join(lines)


def _stringify(rows: list[dict], cols: list[str]) -> list[dict]:
    return [{c: str(r[c]) for c in cols} for r in rows]


def check() -> int:
    """Parity gate: recompute from inputs and compare against the stored outputs."""
    conc = read_concordance()
    resolver = Resolver()
    work_rows, abbrev_map = build_work_dates(conc, resolver)
    per_prefix = {r["locus_prefix"] or r["fold"]: r for r in work_rows}
    sense_rows = build_sense_dating(conc, per_prefix)
    ok = True
    stored = list(csv.DictReader(open(DATING / "work_dates.tsv"), delimiter="\t"))
    if _stringify(work_rows, WORK_COLS) != stored:
        print("parity FAIL: work_dates.tsv", file=sys.stderr)
        ok = False
    stored_ab = list(csv.DictReader(open(DATING / "abbrev_map.tsv"), delimiter="\t"))
    want_ab = sorted(abbrev_map.values(), key=lambda r: r["abbrev"])
    if _stringify(want_ab, ABBREV_COLS) != stored_ab:
        print("parity FAIL: abbrev_map.tsv", file=sys.stderr)
        ok = False
    stored_s = list(csv.DictReader(open(DATING / "sense_dating.tsv"), delimiter="\t"))
    if _stringify(sense_rows, SENSE_COLS) != stored_s:
        print("parity FAIL: sense_dating.tsv", file=sys.stderr)
        ok = False
    print("parity:", "OK" if ok else "FAIL",
          f"({len(work_rows)} works, {len(abbrev_map)} abbrevs, {len(sense_rows)} senses)")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="recompute from inputs; exit 0 iff stored outputs match")
    args = ap.parse_args()
    if args.check:
        return check()
    stats = run()
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
