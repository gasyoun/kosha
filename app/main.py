"""kosha — fast Sanskrit dictionary lookup service.

FastAPI entry point. Phase 1 (PHASE1_PLAN.md D4): kosha API v1
(ARCHITECTURE.md "API v1 contract") + the two Salt facade REST faces
("Maximum-reuse rules" point 4). GraphQL face is P7-scoped, not here.
"""
import json
import os
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from db import get_db, data_version  # noqa: E402
from render import render  # noqa: E402
from salt import entries_for_key, salt_entry, mint_salt_id  # noqa: E402
from scan_resolver import scan_url  # noqa: E402
from transliterate import to_slp1_auto, from_slp1_out  # noqa: E402
from versions import parse_sense_id, has_archive, resolve_sense  # noqa: E402
from cite import cite_object  # noqa: E402
from evidence import build_evidence  # noqa: E402
from reverse_lookup import analyze as reverse_analyze  # noqa: E402

load_dotenv()

# Public base for browser-resolvable citation URLs (RISKS.md R1 Commitment 1).
# NOT the samskrtam.ru server (R5: citations never depend on the server host);
# defaults to the local dev API. In production this is the durable API mirror.
PUBLIC_BASE = os.getenv("KOSHA_PUBLIC_BASE", "http://localhost:8000")

app = FastAPI(
    title=os.getenv("API_TITLE", "kosha"),
    description=os.getenv("API_DESCRIPTION", "Fast Sanskrit Dictionary Lookup"),
    version=os.getenv("API_VERSION", "0.1.0"),
)

try:
    origins = json.loads(os.getenv("CORS_ORIGINS", '["*"]'))
except json.JSONDecodeError:
    origins = ["*"]

# NB: allow_credentials must stay False while origins may be ["*"] —
# Starlette silently drops the wildcard otherwise.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def envelope(con, query: dict, results):
    return {"data_version": data_version(con), "query": query, "results": results}


def error(code: str, message: str, status: int, suggestions=None):
    raise HTTPException(status_code=status, detail={
        "error": {"code": code, "message": message, "suggestions": suggestions or []}
    })


@app.get("/")
def root():
    return {"message": "kosha — Sanskrit Dictionary Lookup", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# kosha API v1 (ARCHITECTURE.md)
# ---------------------------------------------------------------------------

ALL_DICTS = ("mw", "pwg", "ap90")


def _entry_payload(con, row, out: str, raw: bool):
    payload = {
        "dict": row["dict"], "L": row["L"], "sense_ids": [],
        "scan_url": scan_url(row["dict"], row["page"]),
        "headword": from_slp1_out(row["slp1_key"], out),
        "rendered_html": render(row["dict"], row["body"]),
    }
    if raw:
        payload["raw"] = row["body"]
    senses = con.execute(
        "SELECT sense_n FROM senses WHERE entry_id=? ORDER BY sense_n", (row["id"],)
    ).fetchall()
    dv = data_version(con)
    payload["sense_ids"] = [f"{row['dict']}.{row['L']}.{s['sense_n']}@{dv}" for s in senses]
    # P3 evidence layer (IMPLEMENTATION_PLAN.md P3 / EVAL_PLAN.md T-UC4):
    # band + attestation count + first era + one corpus example, each badge
    # carrying its own provenance source. Keyed off the entry's own
    # slp1_key, not the input query key, so homonym-suffixed entries under
    # the same headword still resolve the right lemma row.
    lemma_row = con.execute(
        "SELECT * FROM lemmas WHERE slp1=?", (row["slp1_key"],)
    ).fetchone()
    payload["evidence"] = build_evidence(lemma_row)
    return payload


@app.get("/api/v1/lemma/{key}")
def get_lemma(key: str, in_: str = Query("auto", alias="in"), out: str = "iast",
              dicts: str = ",".join(ALL_DICTS), raw: int = 0,
              con: sqlite3.Connection = Depends(get_db)):
    slp1_key = to_slp1_auto(key, in_)
    dict_list = [d.strip() for d in dicts.split(",") if d.strip() in ALL_DICTS]
    results = []
    for d in dict_list:
        rows = con.execute(
            "SELECT * FROM entries WHERE dict=? AND slp1_key=? ORDER BY L", (d, slp1_key)
        ).fetchall()
        for r in rows:
            results.append(_entry_payload(con, r, out, bool(raw)))
    if not results:
        lemma = con.execute("SELECT slp1 FROM lemmas WHERE slp1=?", (slp1_key,)).fetchone()
        error("lemma_not_found", f"no entries for '{key}' (slp1={slp1_key})", 404,
              suggestions=[] if lemma is None else ["lemma exists in the union spine but has no dict entries"])
    return envelope(con, {"key": key, "in": in_, "out": out, "dicts": dict_list}, results)


@app.get("/api/v1/form/{form}")
def get_form(form: str, in_: str = Query("auto", alias="in"),
             con: sqlite3.Connection = Depends(get_db)):
    # H111 trust ordering (highest to lowest): dcs > vidyut > heritage.
    # `source='heritage'` is Heritage/INRIA's rule-generated full paradigm —
    # it over-generates unattested forms, so a heritage-only result here is
    # corroborating evidence, not attested usage. Callers that need "attested"
    # rather than "grammatically possible" should filter source != 'heritage'.
    slp1_form = to_slp1_auto(form, in_)
    lemma_rows = con.execute(
        "SELECT DISTINCT lemma_slp1, source FROM forms WHERE form_slp1=?", (slp1_form,)
    ).fetchall()
    lemmas = [{"lemma_slp1": r["lemma_slp1"], "lemma_iast": from_slp1_out(r["lemma_slp1"], "iast"),
               "source": r["source"]} for r in lemma_rows]
    if not lemmas:
        return envelope(con, {"form": form, "in": in_}, [{"lemmas": [], "suggestions": []}])
    return envelope(con, {"form": form, "in": in_}, [{"lemmas": lemmas}])


@app.get("/api/v1/forms/{form}/analyze")
def analyze_form(form: str, in_: str = Query("auto", alias="in"),
                  con: sqlite3.Connection = Depends(get_db)):
    """P4 Wave K2a (H181): reverse-lookup query pipeline over an arbitrary
    surface form. A honest cascade that reports which stage answered via
    `resolved_by`:

      1. `inflections` exact hit -- Cologne csl-inflect, case/number/person-
         labeled (nominals AND, since K2a, verbs). Full grammatical parse(s);
         a form genuinely ambiguous in Sanskrit (dharmakSetre = loc-sg of both
         the m_a and n_a stems, plus nom/acc/voc-du of n_a) returns every
         parse, not one. Verb forms (Bavati = 3sg pre of BU) now resolve here.
      2. miss -> `forms` exact hit -- DCS/vidyut/heritage lemma witness
         (lemma-only), returned under `forms_witnesses`.
      3. miss -> vidyut-cheda segmentation (app/segmenter.py): split a
         sandhied/compound string into padas and re-resolve each through 1-2,
         returned under `segments`. Local vendored data only (RISKS.md R12); if
         that data is absent, `segmentation_available` is false and the form is
         an honest miss rather than an error.

    Stem spellings that differ between `inflections` (Bagavat) and `forms`
    (Bagavant) are unified via the `stem_bridge` crosswalk -- every result
    carries `canonical_slp1`, and the top-level `lemmas` list has ONE entry per
    canonical lemma with `has_entry` (is it a dictionary headword?).
    """
    slp1_form = to_slp1_auto(form, in_)
    result = reverse_analyze(con, slp1_form)
    return envelope(con, {"form": form, "in": in_, "form_slp1": slp1_form}, [result])


@app.get("/api/v1/search")
def search(q: str, mode: str = "prefix", limit: int = 50, offset: int = 0,
           con: sqlite3.Connection = Depends(get_db)):
    if limit > 200:
        error("bad_request", "limit must be <= 200", 400)
    slp1_q = to_slp1_auto(q, "auto")
    if mode == "exact":
        where, params = "slp1 = ?", (slp1_q,)
    elif mode == "prefix":
        where, params = "slp1 LIKE ?", (slp1_q + "%",)
    elif mode == "fuzzy":
        where, params = "slp1 LIKE ?", ("%" + slp1_q + "%",)
    else:
        error("bad_request", f"unknown mode '{mode}'", 400)
    total = con.execute(f"SELECT COUNT(*) FROM lemmas WHERE {where}", params).fetchone()[0]
    # P3 frequency-weighted ranking (IMPLEMENTATION_PLAN.md P3): an exact
    # key match (slp1 = the query key) always sorts first regardless of
    # mode -- a student typing the exact headword should never see a more
    # frequent prefix-sibling above it. Within that, `rank_all ASC` (1 =
    # most frequent), nulls (no DCS attestation, band 5) sorted after every
    # ranked lemma, then `slp1 ASC` as the final deterministic tiebreak.
    # Documented, not tunable per-request -- no client-supplied sort param.
    order = (
        "ORDER BY (slp1 = ?) DESC, "
        "(rank_all IS NULL), rank_all ASC, slp1 ASC"
    )
    rows = con.execute(
        f"SELECT slp1, iast, n_dicts, dicts, rank_all FROM lemmas WHERE {where} "
        f"{order} LIMIT ? OFFSET ?",
        (*params, slp1_q, limit, offset)
    ).fetchall()
    results = [{"slp1": r["slp1"], "iast": r["iast"], "n_dicts": r["n_dicts"], "dicts": r["dicts"],
                "rank_all": r["rank_all"]} for r in rows]
    return {"data_version": data_version(con),
            "query": {"q": q, "mode": mode, "limit": limit, "offset": offset, "total": total},
            "results": results}


@app.get("/api/v1/sense/{sense_id}")
def get_sense(sense_id: str, v: str = Query(None),
              con: sqlite3.Connection = Depends(get_db)):
    parsed = parse_sense_id(sense_id)
    if parsed is None:
        error("bad_request", f"malformed sense id '{sense_id}' (expected dict.L.n[@version])", 400)
    dict_code, L, sense_n, id_version = parsed
    dv = data_version(con)
    # The pinned version comes from the id's @suffix, or an explicit ?v= override
    # (RISKS.md R1: an old citation resolves against the release it names).
    want_version = v or id_version or dv

    # Archived (old) version: resolve against its frozen dump (app/versions.py),
    # not the live DB — this is the version-resolution path T-UC10 forces.
    if want_version != dv:
        if not has_archive(want_version):
            error("version_not_archived",
                  f"data version '{want_version}' is not archived on this instance",
                  404,
                  suggestions=[
                      "citations resolve against GitHub release assets: "
                      f"{cite_object(dict_code, L, sense_n, want_version, PUBLIC_BASE)['release_asset']}",
                  ])
        arch = resolve_sense(want_version, sense_id)
        if arch is None:
            error("sense_not_found",
                  f"no sense {dict_code}.{L}.{sense_n} in archived version '{want_version}'", 404)
        result = {
            "sense_id": f"{dict_code}.{L}.{sense_n}@{want_version}",
            "dict": dict_code, "L": L, "sense_n": sense_n, "resolved_from": "archive",
            "text_raw": arch["text_raw"], "text_rendered": render(dict_code, arch["text_raw"]),
            "entry": {"dict": dict_code, "L": L, "headword": arch["headword"]},
            "scan_url": None,
            "cite": cite_object(dict_code, L, sense_n, want_version, PUBLIC_BASE, arch["headword"]),
        }
        return {"data_version": want_version, "query": {"sense_id": sense_id, "v": v}, "results": [result]}

    # Live (current) version: resolve against the DB.
    row = con.execute("SELECT * FROM entries WHERE dict=? AND L=?", (dict_code, L)).fetchone()
    if row is None:
        error("sense_not_found", f"no entry {dict_code}.{L}", 404)
    sense = con.execute(
        "SELECT * FROM senses WHERE entry_id=? AND sense_n=?", (row["id"], sense_n)
    ).fetchone()
    if sense is None:
        error("sense_not_found", f"no sense {sense_n} on {dict_code}.{L}", 404)

    headword = from_slp1_out(row["slp1_key"], "iast")
    body_span = row["body"][sense["span_start"]:sense["span_end"]]
    result = {
        "sense_id": f"{dict_code}.{L}.{sense_n}@{dv}", "dict": dict_code, "L": L,
        "sense_n": sense_n, "resolved_from": "live",
        "text_raw": body_span, "text_rendered": render(dict_code, body_span),
        "entry": {"dict": dict_code, "L": L, "headword": headword},
        "scan_url": scan_url(dict_code, row["page"]),
        "cite": cite_object(dict_code, L, sense_n, dv, PUBLIC_BASE, headword),
    }
    return envelope(con, {"sense_id": sense_id, "v": v}, [result])


@app.get("/api/v1/meta")
def meta(con: sqlite3.Connection = Depends(get_db)):
    sources = con.execute("SELECT * FROM sources").fetchall()
    counts = {
        "lemmas": con.execute("SELECT COUNT(*) FROM lemmas").fetchone()[0],
        "entries": con.execute("SELECT COUNT(*) FROM entries").fetchone()[0],
        "forms": con.execute("SELECT COUNT(*) FROM forms").fetchone()[0],
    }
    return {
        "data_version": data_version(con),
        "sources": [dict(s) for s in sources],
        "counts": counts,
    }


# ---------------------------------------------------------------------------
# Salt facade REST faces (ARCHITECTURE.md "Maximum-reuse rules" point 4)
# ---------------------------------------------------------------------------

@app.get("/dicts/{dict_id}/restful/entries")
def salt_entries(dict_id: str, field: str = "headword_slp1", query: str = "",
                  query_type: str = "term", size: int = 25, input: str = "slp1",
                  output: str = "deva", con: sqlite3.Connection = Depends(get_db)):
    dict_code = dict_id.lower()
    if dict_code not in ALL_DICTS:
        return {"error": f"unknown dict '{dict_id}'"}
    if field != "headword_slp1":
        return {"error": f"unsupported field '{field}' (Phase 1: headword_slp1 only)"}
    slp1_q = to_slp1_auto(query, "slp1" if input == "slp1" else input) if query else ""
    if query_type == "term":
        where, params = "slp1_key = ?", (slp1_q,)
    elif query_type == "prefix":
        where, params = "slp1_key LIKE ?", (slp1_q + "%",)
    else:
        return {"error": f"unsupported query_type '{query_type}' (Phase 1: term/prefix)"}
    keys = con.execute(
        f"SELECT DISTINCT slp1_key FROM entries WHERE dict=? AND {where} LIMIT ?",
        (dict_code, *params, size),
    ).fetchall()
    dv = data_version(con)
    entries = []
    for k in keys:
        rows = entries_for_key(con, dict_code, k["slp1_key"])
        for r in rows:
            entries.append(salt_entry(con, r, len(rows), dv))
    return {"data": {"entries": entries}}


@app.get("/dicts/{dict_id}/restful/ids")
def salt_ids(dict_id: str, ids: list[str] = Query(default=[]),
             con: sqlite3.Connection = Depends(get_db)):
    dict_code = dict_id.lower()
    if dict_code not in ALL_DICTS:
        return {"error": f"unknown dict '{dict_id}'"}
    dv = data_version(con)
    out_entries = []
    for req_id in ids:
        body_id = req_id[len("lemma-"):] if req_id.startswith("lemma-") else req_id
        m_l = body_id.rsplit("-L", 1)
        m_n = body_id.rsplit("-", 1)
        if len(m_l) == 2 and m_l[1].replace(".", "").isdigit():
            key, lnum = m_l[0], m_l[1]
            row = con.execute("SELECT * FROM entries WHERE dict=? AND slp1_key=? AND L=?",
                               (dict_code, key, lnum)).fetchone()
            if row:
                hom_rows = entries_for_key(con, dict_code, key)
                out_entries.append(salt_entry(con, row, len(hom_rows), dv))
            continue
        if len(m_n) == 2 and m_n[1].isdigit():
            key, hui = m_n[0], m_n[1]
            hom_rows = entries_for_key(con, dict_code, key)
            for r in hom_rows:
                if mint_salt_id(dict_code, r["slp1_key"], r["L"], r["body"], len(hom_rows)) == req_id:
                    out_entries.append(salt_entry(con, r, len(hom_rows), dv))
            continue
        # bare "lemma-{key}" — all records for that key
        hom_rows = entries_for_key(con, dict_code, body_id)
        for r in hom_rows:
            out_entries.append(salt_entry(con, r, len(hom_rows), dv))
    return {"data": {"ids": out_entries}}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
