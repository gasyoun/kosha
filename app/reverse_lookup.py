"""kosha P4 Wave K2a (H181) -- reverse-lookup query pipeline.

Given an arbitrary surface form, resolve it to lemmas/entries via a cascade
that HONESTLY reports which stage answered (`resolved_by`):

  1. `inflections` exact hit -- Cologne csl-inflect, case/number/person-labeled
     (nominals + verbs). The authoritative grammatical parse.
  2. miss -> `forms` exact hit -- DCS/vidyut/heritage lemma witness (lemma-only,
     no case/number). Trust order dcs > vidyut > heritage. Heritage rows are
     DEFAULT-OFF per the R7 ruling (10-07-2026, Uprava
     docs/DECISIONS_roadmap_forks_2026H2.md): the 928,262 Heritage-surplus
     forms are rule-generated under a different lemmatization policy, so they
     are never served unless the caller opts in (`include_heritage=True` /
     `?heritage=1` on the API).
  3. miss -> vidyut-cheda segmentation (app/segmenter.py) -- split a sandhied /
     compounded string into padas and re-resolve each pada through stages 1-2.

Across stages 1 and 2 the same lexeme can appear under different stem spellings
(Bagavat in `inflections` vs Bagavant in `forms`); the `stem_bridge` crosswalk
(scripts/build_stem_bridge.py) canonicalizes every lemma so the unified
`lemmas` list carries ONE key per word, with `has_entry` telling the caller
whether that canonical lemma is an actual dictionary headword.

Builds/queries never call a live third-party service (RISKS.md R12): stage 3
uses vidyut as a local library over vendored data, and degrades to
"unavailable" if that data is absent rather than fetching it.
"""
import sqlite3

from transliterate import from_slp1_out


def canonicalize(con: sqlite3.Connection, lemma: str) -> str:
    """Map a lemma spelling to its canonical stem via `stem_bridge`
    (strong->weak), or return it unchanged if it isn't a bridged variant."""
    row = con.execute(
        "SELECT canonical_slp1 FROM stem_bridge WHERE variant_slp1=?", (lemma,)
    ).fetchone()
    return row[0] if row else lemma


def _has_entry(con: sqlite3.Connection, lemma: str) -> bool:
    return con.execute(
        "SELECT 1 FROM entries WHERE slp1_key=? LIMIT 1", (lemma,)
    ).fetchone() is not None


def _inflection_analyses(con: sqlite3.Connection, form_slp1: str):
    rows = con.execute(
        "SELECT lemma_slp1, model, gender, gcase, number, person, tense, voice, refs, source "
        "FROM inflections WHERE form_slp1=? "
        "ORDER BY lemma_slp1, model, gcase, number, person, tense, voice",
        (form_slp1,),
    ).fetchall()
    out = []
    for r in rows:
        canon = canonicalize(con, r["lemma_slp1"])
        out.append({
            "lemma_slp1": r["lemma_slp1"],
            "lemma_iast": from_slp1_out(r["lemma_slp1"], "iast"),
            "canonical_slp1": canon,
            "canonical_iast": from_slp1_out(canon, "iast"),
            "model": r["model"],
            "gender": r["gender"],
            "case": r["gcase"],
            "number": r["number"],
            "person": r["person"],
            "tense": r["tense"],
            "voice": r["voice"],
            "refs": r["refs"],
            "source": r["source"],
            "resolved_by": "inflections",
        })
    return out


def _forms_witnesses(con: sqlite3.Connection, form_slp1: str,
                     include_heritage: bool = False):
    # R7 default-off: heritage witnesses only on explicit opt-in.
    src_filter = "" if include_heritage else "AND source != 'heritage' "
    rows = con.execute(
        "SELECT DISTINCT lemma_slp1, source FROM forms WHERE form_slp1=? "
        f"{src_filter}"
        "ORDER BY lemma_slp1, source",
        (form_slp1,),
    ).fetchall()
    out = []
    for r in rows:
        canon = canonicalize(con, r["lemma_slp1"])
        out.append({
            "lemma_slp1": r["lemma_slp1"],
            "lemma_iast": from_slp1_out(r["lemma_slp1"], "iast"),
            "canonical_slp1": canon,
            "canonical_iast": from_slp1_out(canon, "iast"),
            "source": r["source"],
            "resolved_by": "forms",
        })
    return out


def _unified_lemmas(con: sqlite3.Connection, records):
    """Collapse a list of stage records (each carrying `canonical_slp1`,
    `source`, `resolved_by`) into one entry per canonical lemma."""
    by_key = {}
    for rec in records:
        key = rec["canonical_slp1"]
        u = by_key.get(key)
        if u is None:
            u = by_key[key] = {
                "lemma_slp1": key,
                "lemma_iast": from_slp1_out(key, "iast"),
                "has_entry": _has_entry(con, key),
                "resolved_by": set(),
                "sources": set(),
            }
        u["resolved_by"].add(rec["resolved_by"])
        u["sources"].add(rec.get("source") or rec["resolved_by"])
    out = []
    for u in by_key.values():
        u["resolved_by"] = sorted(u["resolved_by"])
        u["sources"] = sorted(u["sources"])
        out.append(u)
    # entries first (dictionary-attested), then by lemma for determinism.
    out.sort(key=lambda x: (not x["has_entry"], x["lemma_slp1"]))
    return out


def analyze(con: sqlite3.Connection, form_slp1: str,
            include_heritage: bool = False) -> dict:
    """Run the reverse-lookup cascade. Returns the result block for one form.

    `include_heritage` (R7 opt-in) admits `source='heritage'` witnesses at
    stages 2 and 3; by default they are excluded everywhere."""
    analyses = _inflection_analyses(con, form_slp1)
    if analyses:
        return {
            "resolved_by": "inflections",
            "analyses": analyses,
            "lemmas": _unified_lemmas(con, analyses),
        }

    witnesses = _forms_witnesses(con, form_slp1, include_heritage)
    if witnesses:
        return {
            "resolved_by": "forms",
            "analyses": [],
            "forms_witnesses": witnesses,
            "lemmas": _unified_lemmas(con, witnesses),
        }

    # stage 3: sandhi/compound split, then re-resolve each pada through 1-2.
    from segmenter import segment, available as seg_available
    if not seg_available():
        return {
            "resolved_by": None,
            "analyses": [],
            "segmentation_available": False,
            "lemmas": [],
        }

    segs = segment(form_slp1)
    # a single-token result that equals the input is not a real split -> a
    # genuine miss, not a segmentation answer.
    if len(segs) <= 1 and (not segs or segs[0]["text"] == form_slp1):
        return {
            "resolved_by": None,
            "analyses": [],
            "segmentation_available": True,
            "segments": [],
            "lemmas": [],
        }

    seg_out = []
    all_records = []
    for s in segs:
        seg_form = s["text"]
        seg_an = _inflection_analyses(con, seg_form)
        seg_wit = _forms_witnesses(con, seg_form, include_heritage)
        recs = []
        for a in seg_an:
            a = dict(a, resolved_by="segmentation")
            recs.append(a)
        for w in seg_wit:
            w = dict(w, resolved_by="segmentation")
            recs.append(w)
        # vidyut's own lemma for the pada, if the sub-tables didn't resolve it.
        if not recs and s["lemma"]:
            canon = canonicalize(con, s["lemma"])
            recs.append({
                "lemma_slp1": s["lemma"],
                "lemma_iast": from_slp1_out(s["lemma"], "iast"),
                "canonical_slp1": canon,
                "canonical_iast": from_slp1_out(canon, "iast"),
                "source": "vidyut",
                "resolved_by": "segmentation",
            })
        all_records.extend(recs)
        seg_out.append({
            "text": seg_form,
            "text_iast": from_slp1_out(seg_form, "iast"),
            "vidyut_lemma": s["lemma"],
            "lemmas": _unified_lemmas(con, recs),
        })

    return {
        "resolved_by": "segmentation" if all_records else None,
        "analyses": [],
        "segmentation_available": True,
        "segments": seg_out,
        "lemmas": _unified_lemmas(con, all_records),
    }
