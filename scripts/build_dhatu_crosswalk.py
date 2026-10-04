"""build_dhatu_crosswalk.py — P4 Wave E1 verb follow-on (H855, after H185 Task C;
stage-2 bare-seeded resolution added by the A03 roadmap-drain rung, 01-10-2026).

Cologne's `inflections` verb rows store the **bare SLP1 root** (e.g. `sad`,
`arT`), but vidyut's `Dhatu.mula` wants the *aupadeśika* upadeśa — the
dhātupāṭha citation form with accent + anubandhas (e.g. `za\\da~\\`,
`arTa~`). Passing the bare root resolves only ~70 % of the gaṇa-1/4/6/10 roots
Cologne ingested (K2a); the rest derive nothing, which inflated COLOGNE_ONLY and
depressed the reported present-system agreement in
[`compare_vidyut_verbs.py`](compare_vidyut_verbs.py) (the "12.68 %" the E1 report
flagged as a *mapping artifact*, not real divergence).

**Stage 1 (H855)** builds a static **Cologne-root → aupadeśika-dhātu crosswalk**
that lifts root resolution to ~93 %. For each Cologne `(root, gaṇa)` it picks,
in order:

  1. **3sg** — the dhātupāṭha entry in that gaṇa whose vidyut present-3sg-active
     matches Cologne's own present-3sg-active (the most Cologne-faithful match);
  2. **direct** — the bare root already derives a non-empty paradigm as-is;
  3. **bare** — a normalized-bare-root match (strip accents + the trailing
     anunāsika it-vowel) against the dhātupāṭha;
  4. otherwise **unresolved** (reported honestly, never guessed).

**Stage 2 (A03, this file's namesake rung)** resolves the residue H3166 measured:
the `direct` entries (seed == bare root, 212 of 779 at H855) whose passives
malform (`yat` → `yyate` where Cologne has `yatyate`), and the `unresolved`
entries. Each target is re-decided **on Cologne form evidence** over candidates
gathered across ALL four gaṇas (the dhātupāṭha entry may live in a different
gaṇa than Cologne's model claims — a gaṇa-shift is itself a finding):

  * candidates: dhātupāṭha entries matched by present-3sg form (either pada) or
    by normalized bare string, plus the current bare-root seed itself;
  * each candidate is scored by how many Cologne present-3sg forms it derives
    (active-derived vs Cologne-active, ātmanepada-derived vs Cologne-middle —
    voice-consistent), preferring licensed entries over the bare seed at equal
    evidence, then same-gaṇa, then the lowest dhātupāṭha code;
  * `cells` / `cells-xgana` — a licensed entry wins (xgana carries a `gana`
    override the comparison must use in `Dhatu.mula`);
  * `direct` (kept, now with an `evidence` count) — the bare seed itself
    demonstrably derives Cologne's forms and no licensed entry does better
    (e.g. `v_10|BI` → `BAyayati`: vidyut's curādi machinery agrees verbatim);
  * `no-dhatu` — nothing licenses the derivation: aupadeśika stays null, and the
    comparison now **abstains** (vidyut empty → COLOGNE_ONLY, the coverage-gap
    class) instead of feeding `Dhatu.mula` an unmarked root and miscounting the
    malformed output as genuine conflict. Never guessed.

The crosswalk (`data/e1/dhatu_crosswalk.json`) is **committed** so the verb
comparison needs only the *bundled* vidyut package (`Dhatu.mula`, R12-clean),
NOT the ~large external `vidyut-data` download, at run time. Build-time only,
with the sibling `vidyut-data` present:

    python -c "import vidyut; vidyut.download_data('../vidyut-data')"
    python scripts/build_dhatu_crosswalk.py
"""
import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "db" / "kosha.db"
DEFAULT_VDATA = ROOT.parent / "vidyut-data" / "prakriya"
DEFAULT_OUT = ROOT / "data" / "e1" / "dhatu_crosswalk.json"

from vidyut.prakriya import (
    Vyakarana, Dhatu, Gana, Lakara, Prayoga, Purusha, Vacana, DhatuPada, Pada, Data,
)

# The four thematic gaṇas Cologne's K2a verb ingest covers (models v_1/v_4/v_6/v_10).
GANA_OF_MODEL = {"v_1": Gana.Bhvadi, "v_4": Gana.Divadi, "v_6": Gana.Tudadi, "v_10": Gana.Curadi}
GANA_INT = {Gana.Bhvadi: 1, Gana.Divadi: 4, Gana.Tudadi: 6, Gana.Curadi: 10}
GANA_INT_TO_GANA = {i: g for g, i in GANA_INT.items()}
MODEL_G_INT = {m: GANA_INT[g] for m, g in GANA_OF_MODEL.items()}
_ACCENTS = "\\^/="
_IT_VOWELS = "aAiIuUfFxXeEoO"


def _present_3sg(v, dhatu, pada):
    """vidyut present-3sg-active-or-middle (laṭ, prathama, eka, kartari, pada)."""
    try:
        return {p.text for p in v.derive(Pada.Tinanta(
            dhatu=dhatu, prayoga=Prayoga.Kartari, lakara=Lakara.Lat,
            purusha=Purusha.Prathama, vacana=Vacana.Eka, dhatu_pada=pada))}
    except Exception:
        return set()


def _present_3sg_active(v, dhatu):
    return _present_3sg(v, dhatu, DhatuPada.Parasmaipada)


def _bare(aupadeshika: str) -> str:
    """Strip accents and the trailing anunāsika it-vowel from an upadeśa to get
    an approximate bare root for spelling-level matching against Cologne."""
    f = aupadeshika
    for a in _ACCENTS:
        f = f.replace(a, "")
    if f.endswith("~"):
        f = f[:-1]
        if f and f[-1] in _IT_VOWELS:
            f = f[:-1]
    return f.replace("~", "")


def build_indexes(v, entries):
    """Index the gaṇa-1/4/6/10 dhātupāṭha by (gaṇa_int, present-3sg, pada) and by
    (gaṇa_int, bare-root). Values are (code, aupadeśika), lowest-code first.
    Both pada lanes are indexed: Cologne tabulates some roots ātmanepada where
    the dhātupāṭha entry is parasmaipada (the report's pada-assignment fork),
    so a candidate can be evidenced through either voice."""
    by_3sg_p = defaultdict(list)   # parasmaipada derivations
    by_3sg_a = defaultdict(list)   # ātmanepada derivations
    by_bare = defaultdict(list)
    n = 0
    for e in entries:
        g = e.dhatu.gana
        if g not in GANA_INT:
            continue
        n += 1
        gi = GANA_INT[g]
        au = e.dhatu.aupadeshika
        try:
            dhatu = Dhatu.mula(au, g)
        except Exception:
            continue
        for f in _present_3sg(v, dhatu, DhatuPada.Parasmaipada):
            by_3sg_p[(gi, f)].append((e.code, au))
        for f in _present_3sg(v, dhatu, DhatuPada.Atmanepada):
            by_3sg_a[(gi, f)].append((e.code, au))
        by_bare[(gi, _bare(au))].append((e.code, au))
    for idx in (by_3sg_p, by_3sg_a, by_bare):
        for k in idx:
            idx[k].sort()  # deterministic: lowest dhātupāṭha code wins
    return by_3sg_p, by_3sg_a, by_bare, n


def cologne_present_3sg(con, root, model):
    return {r["form_slp1"] for r in con.execute(
        "SELECT form_slp1 FROM inflections WHERE lemma_slp1=? AND model=? "
        "AND person='3' AND number='sg' AND tense='pre' AND voice='active'", (root, model))}


def cologne_present_3sg_voices(con, root, model):
    """{voice: set(forms)} for Cologne's present-3sg cells (active + middle)."""
    out = {"active": set(), "middle": set()}
    for r in con.execute(
            "SELECT form_slp1, voice FROM inflections WHERE lemma_slp1=? AND model=? "
            "AND person='3' AND number='sg' AND tense='pre'", (root, model)):
        if r["voice"] in out:
            out[r["voice"]].add(r["form_slp1"])
    return out


def resolve(v, con, by_3sg, by_bare, root, model):
    """Return (aupadeshika, via, code) or (None, 'unresolved', None)."""
    gi = MODEL_G_INT[model]
    gana = GANA_OF_MODEL[model]
    # 1. present-3sg match (most Cologne-faithful)
    for f in sorted(cologne_present_3sg(con, root, model)):
        if (gi, f) in by_3sg:
            code, au = by_3sg[(gi, f)][0]
            return au, "3sg", code
    # 2. the bare root already derives directly (identity upadeśa)
    try:
        d0 = Dhatu.mula(root, gana)
        if _present_3sg_active(v, d0):
            return root, "direct", None
    except Exception:
        pass
    # 3. normalized bare-root match
    if (gi, root) in by_bare:
        code, au = by_bare[(gi, root)][0]
        return au, "bare", code
    return None, "unresolved", None


# --------------------------------------------------------------------------
# Stage 2 (A03, 01-10-2026): resolve the bare-seeded `direct` entries (seed ==
# bare root) and the `unresolved` entries on Cologne form evidence.
# --------------------------------------------------------------------------

def _candidates(v, root, model, col, by_3sg_p, by_3sg_a, by_bare, p3_cache):
    """Candidate seeds for one (root, model), keyed (au, gaṇa_int, licensed).
    Licensed entries come from the present-3sg form indexes (either pada) and
    the normalized-bare-string index, across ALL four gaṇas; the current bare
    root itself joins as the unlicensed incumbent (what the comparison derives
    today). Each candidate carries its voice-consistent Cologne evidence:
    (active-derived ∩ Cologne-active) + (ātmanepada-derived ∩ Cologne-middle)."""
    gi = MODEL_G_INT[model]
    gana = GANA_OF_MODEL[model]
    col_act, col_mid = col["active"], col["middle"]
    cand = {}

    def add(au, ggi, code, licensed):
        key = (au, ggi, licensed)
        if key in cand:
            return
        acts = mids = None
        if licensed:
            ck = (au, ggi)
            if ck not in p3_cache:
                try:
                    d = Dhatu.mula(au, GANA_INT_TO_GANA[ggi])
                    p3_cache[ck] = (_present_3sg(v, d, DhatuPada.Parasmaipada),
                                    _present_3sg(v, d, DhatuPada.Atmanepada))
                except Exception:
                    p3_cache[ck] = (set(), set())
            acts, mids = p3_cache[ck]
        else:  # the incumbent bare seed, derived under the model's gaṇa
            ck = (au, gi, False)
            if ck not in p3_cache:
                try:
                    d = Dhatu.mula(au, gana)
                    p3_cache[ck] = (_present_3sg(v, d, DhatuPada.Parasmaipada),
                                    _present_3sg(v, d, DhatuPada.Atmanepada))
                except Exception:
                    p3_cache[ck] = (set(), set())
            acts, mids = p3_cache[ck]
        cand[key] = {"code": code, "evidence": len(acts & col_act) + len(mids & col_mid)}

    # licensed: present-3sg form match, either pada lane, any gaṇa
    for f in col_act:
        for ggi in (1, 4, 6, 10):
            for code, au in by_3sg_p.get((ggi, f), []):
                add(au, ggi, code, True)
    for f in col_mid:
        for ggi in (1, 4, 6, 10):
            for code, au in by_3sg_a.get((ggi, f), []):
                add(au, ggi, code, True)
    # licensed: normalized bare-string match, any gaṇa
    for ggi in (1, 4, 6, 10):
        for code, au in by_bare.get((ggi, root), []):
            add(au, ggi, code, True)
    # the incumbent bare seed
    if col_act or col_mid:
        add(root, gi, None, False)
    return cand


def upgrade_bare_seeded(v, con, by_3sg_p, by_3sg_a, by_bare, cross):
    """Stage-2 pass over the stage-1 result. Only `direct` (seed == bare root)
    and `unresolved` (no seed) entries are re-decided; the H855 `3sg` and `bare`
    resolutions are left byte-identical. Returns (touched_counts, n_targets)."""
    targets = [k for k, e in cross.items() if e["via"] in ("direct", "unresolved")]
    p3_cache = {}
    outcome = defaultdict(int)
    for k in targets:
        model, root = k.split("|", 1)
        entry = cross[k]
        prev_via = entry["via"]
        col = cologne_present_3sg_voices(con, root, model)
        if not (col["active"] or col["middle"]):
            # no 3sg evidence either way — keep the stage-1 resolution honestly
            entry["prev_via"] = prev_via
            outcome["kept_no_3sg_evidence"] += 1
            continue
        cand = _candidates(v, root, model, col, by_3sg_p, by_3sg_a, by_bare, p3_cache)
        # rank: most evidence first, then licensed over bare, then same-gaṇa,
        # then the lowest dhātupāṭha code (the incumbent bare seed sorts last)
        def rank(item):
            (au, ggi, licensed), c = item
            return (-c["evidence"], 0 if licensed else 1,
                    0 if ggi == MODEL_G_INT[model] else 1,
                    c["code"] or "99.9999")
        (au, ggi, licensed), best = min(cand.items(), key=rank)
        if best["evidence"] == 0:
            # nothing licenses the derivation — vidyut abstains (the comparison
            # treats a null seed as COLOGNE_ONLY, never a bare-root pseudo-form)
            entry.update(aupadeshika=None, via="no-dhatu", code=None,
                         prev_via=prev_via, candidates_tried=len(cand))
            outcome["no_dhatu"] += 1
        elif au == root and not licensed:
            # the bare seed itself demonstrably derives Cologne's forms — keep
            entry.update(via="direct", code=None, evidence=best["evidence"])
            outcome["kept_direct_verified"] += 1
        else:
            entry.update(aupadeshika=au, code=best["code"], prev_via=prev_via)
            if ggi == MODEL_G_INT[model]:
                entry["via"] = "cells"
            else:
                entry["via"] = "cells-xgana"
                entry["gana"] = ggi  # comparison must call Dhatu.mula(au, this gaṇa)
            outcome[entry["via"]] += 1
    return dict(outcome), len(targets)


def build_crosswalk(db_path=DEFAULT_DB, vdata=DEFAULT_VDATA, out=DEFAULT_OUT):
    if not Path(vdata).exists():
        raise SystemExit(
            f"vidyut-data not found at {vdata}\n"
            "Fetch it (build-time only) with:\n"
            "  python -c \"import vidyut; vidyut.download_data('../vidyut-data')\"")
    v = Vyakarana()
    entries = Data(str(vdata)).load_dhatu_entries()
    by_3sg_p, by_3sg_a, by_bare, n_gana = build_indexes(v, entries)
    print(f"[H855] dhātupāṭha entries in gaṇas 1/4/6/10: {n_gana}")

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT DISTINCT lemma_slp1 AS root, model FROM inflections "
        "WHERE person IS NOT NULL AND model IN ('v_1','v_4','v_6','v_10') "
        "ORDER BY lemma_slp1, model").fetchall()

    # stage 1 (H855): 3sg / direct / bare / unresolved
    cross = {}
    via_counts = defaultdict(int)
    for r in rows:
        root, model = r["root"], r["model"]
        au, via, code = resolve(v, con, by_3sg_p, by_bare, root, model)
        via_counts[via] += 1
        cross[f"{model}|{root}"] = {"aupadeshika": au, "via": via, "code": code}
    print(f"[H855] stage 1 — {dict(via_counts)}")

    # stage 2 (A03): evidence-decide the bare-seeded `direct` + `unresolved` targets
    stage2, n_targets = upgrade_bare_seeded(v, con, by_3sg_p, by_3sg_a, by_bare, cross)
    via_counts = defaultdict(int)
    for e in cross.values():
        via_counts[e["via"]] += 1
    resolved = sum(1 for e in cross.values() if e["aupadeshika"])
    total = len(rows)
    print(f"[A03] stage 2 — {n_targets} bare-seeded/unresolved targets: {stage2}")

    payload = {
        "_about": "Cologne verb root -> vidyut aupadeśika-dhātu crosswalk (H855 + "
                  "A03 stage-2 bare-seeded resolution). Key 'model|root'; use "
                  "Dhatu.mula(aupadeshika, gaṇa-of-model — or the entry's 'gana' "
                  "override for via='cells-xgana'). A null aupadesika "
                  "(via='unresolved'/'no-dhatu') means vidyut ABSTAINS for that "
                  "root-model — never seed Dhatu.mula with the bare root. "
                  "via: 3sg=present-3sg match, direct=bare seed kept with Cologne "
                  "form evidence, bare=normalized-bare match (H855), "
                  "cells/cells-xgana=licensed dhātupāṭha entry picked on Cologne "
                  "form evidence (xgana carries a 'gana' override), "
                  "no-dhatu=nothing licenses a derivation.",
        "vidyut_version": __import__("vidyut").__version__,
        "gana_dhatupatha_entries": n_gana,
        "cologne_root_models": total,
        "resolved": resolved,
        "resolved_pct": round(100 * resolved / total, 1) if total else None,
        "via_counts": dict(via_counts),
        "bare_seeded_resolution": {
            "targets": n_targets,
            "kept_direct_verified": stage2.get("kept_direct_verified", 0),
            "cells": stage2.get("cells", 0),
            "cells_xgana": stage2.get("cells-xgana", 0),
            "no_dhatu": stage2.get("no_dhatu", 0),
            "kept_no_3sg_evidence": stage2.get("kept_no_3sg_evidence", 0),
        },
        "crosswalk": dict(sorted(cross.items())),
    }
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[A03] licensed-seed resolution {resolved}/{total} ({payload['resolved_pct']}%) "
          f"— via {dict(via_counts)}")
    print(f"[H855+A03] wrote {out}")
    return payload


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--vdata", type=Path, default=DEFAULT_VDATA)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    build_crosswalk(args.db, args.vdata, args.out)
