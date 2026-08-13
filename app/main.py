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
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from kosha.api import catalog as dataset_catalog  # noqa: E402
from kosha.api import repository, serializer  # noqa: E402
from kosha.api.errors import install_error_handlers, raise_error  # noqa: E402
from kosha.api.models import (  # noqa: E402
    IMPLEMENTED_FIELDS,
    IMPLEMENTED_QUERY_TYPES,
    SaltQueryType,
)
from kosha.feature_gates import history_enabled  # noqa: E402
from kosha.api.serializer import render_sanitized  # noqa: E402
from kosha.scan_resolver import scan_url  # noqa: E402
from kosha.settings import get_settings  # noqa: E402
from kosha.transliterate import to_slp1_auto, from_slp1_out  # noqa: E402
from kosha.cite import cite_object  # noqa: E402

from db import get_db, data_version  # noqa: E402
from versions import parse_sense_id, has_archive, resolve_sense  # noqa: E402
from reverse_lookup import analyze as reverse_analyze  # noqa: E402
from neighbors import (  # noqa: E402
    entry_location, column_entries, physical_page_entries, group_label,
)
from paradigm import build_paradigm  # noqa: E402
from word_page import render_word_page, card_token  # noqa: E402
from history_db import log_search_event, open_connection as open_history_db, upsert_visitor  # noqa: E402
from identity import hash_ip, resolve_anon_id  # noqa: E402
from history import router as history_router  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

load_dotenv()

# Public base for browser-resolvable citation URLs (RISKS.md R1 Commitment 1).
# NOT the samskrtam.ru server (R5: citations never depend on the server host);
# defaults to the local dev API. In production this is the durable API mirror.
PUBLIC_BASE = get_settings().public_base

# H345: link-out base for Heritage (INRIA) DICO anchors. heritage_anchor.anchor
# is a site-relative path ("DICO/<n>.html#<key>") so the target host stays
# configurable, like COLOGNE_SCAN_BASE for scans.
HERITAGE_BASE = os.getenv("HERITAGE_DICO_BASE", "https://sanskrit.inria.fr/")

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
# Starlette silently drops the wildcard otherwise. Cookie-scoped personal
# history (/api/v1/history, /api/v1/auth/*) needs credentialed CORS, so a
# production deployment MUST set CORS_ORIGINS to an explicit origin list
# (e.g. ["https://samskrtam.ru", "https://gasyoun.github.io"]) in .env — the
# wildcard default only works same-origin, credential-free (public
# /api/v1/stats/* endpoints still work fine under it).
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=origins != ["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# D10 — history, magic-link auth, and analytics are OFF for public v1. The
# router is mounted only when `KOSHA_HISTORY_ENABLED` is explicitly truthy, so
# with the default configuration `/api/v1/history`, `/api/v1/auth/*`, and
# `/api/v1/stats/*` are absent from the app and from the OpenAPI schema — a
# real 404, not a disabled handler. Tests that need the surface mount it at
# runtime via `kosha.feature_gates.mount_history`.
if history_enabled():
    app.include_router(history_router)

# W0C item 5 (H1945): one documented error shape leaves `/api/v1`
# (`{"error": {code, message, suggestions}}`, top level — not nested inside
# FastAPI's `detail`), and the C-SALT string form leaves `/dicts/*`. This also
# catches request-validation failures and unhandled exceptions, which used to
# escape in two further shapes of their own.
install_error_handlers(app)


def envelope(con, query: dict, results):
    return {"data_version": data_version(con), "query": query, "results": results}


def error(code: str, message: str, status: int, suggestions=None):
    """Kept as the route-level spelling; the shape is owned by `kosha.api.errors`."""
    raise_error(code, message, status, suggestions)


@app.get("/")
def root():
    return {"message": "kosha — Sanskrit Dictionary Lookup", "docs": "/docs"}


@app.get("/health")
def health():
    """Liveness only — process is up. Use `/ready` for dependency checks."""
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """W1C readiness probe (H2343).

    Fail-closed for missing core DB / data-version mismatch; optional
    subsystems (history when flag off, empty citation archive) report
    disabled/unconfigured without 500. Body is built by
    `kosha.api.readiness` — this route only maps ready → 200 / 503.
    """
    from fastapi.responses import JSONResponse
    from kosha.api.readiness import readiness_payload

    body, status = readiness_payload()
    return JSONResponse(status_code=status, content=body)


# ---------------------------------------------------------------------------
# W2B / P-D6 — public dataset catalog (not the Salt dictionary-entry lane)
# ---------------------------------------------------------------------------


@app.get("/api/v1/datasets")
def list_public_datasets():
    """List public-tier rows from data/manifest/datasets.json.

    Restricted and intermediate rows are omitted. An empty public set is
    explicit (`empty_reason`), never a silent `[]`.
    """
    manifest = dataset_catalog.load_manifest()
    records = dataset_catalog.public_records(manifest)
    return dataset_catalog.list_payload(manifest, records)


@app.get("/api/v1/datasets/{dataset_id}")
def get_public_dataset(dataset_id: str):
    """Resolve one public catalog row. Restricted / unknown → same 404."""
    manifest = dataset_catalog.load_manifest()
    record = dataset_catalog.get_public_record(manifest, dataset_id)
    if record is None:
        error("dataset_not_found", "No public dataset with that id", 404)
    return record


# ---------------------------------------------------------------------------
# kosha API v1 (ARCHITECTURE.md)
# ---------------------------------------------------------------------------

ALL_DICTS = repository.ALL_DICTS


def _lemma_entries(con, slp1_key: str, out: str, raw: bool, dicts=ALL_DICTS):
    """The lemma card, through the one shared serializer (W0C item 2).

    This function is deliberately thin. Everything that used to live inline
    here — the per-dict query, the sense-id minting, the evidence join, the
    Heritage witness, the render — moved into `kosha.api.serializer`, which the
    static-card builder and the SSR route call too. That is what makes
    `tests/test_contract_parity.py` able to assert the three surfaces are
    equal rather than merely similar.
    """
    return [
        serializer.entry_dict(entry)
        for entry in serializer.serialize_lemma_card(
            con,
            slp1_key,
            data_version=data_version(con),
            public_base=PUBLIC_BASE,
            out=out,
            dicts=dicts,
            include_raw=raw,
            heritage_base=HERITAGE_BASE,
        )
    ]


@app.get("/api/v1/lemma/{key}")
def get_lemma(key: str, in_: str = Query("auto", alias="in"), out: str = "iast",
              dicts: str = ",".join(ALL_DICTS), raw: int = 0,
              con: sqlite3.Connection = Depends(get_db)):
    """D6: results are Salt-profile entries with kosha's own fields under
    `kosha`. Pre-public breaking change — the flat `{dict, L, headword,
    rendered_html, …}` object this route returned through v0.97 is now the
    `kosha` block of a Salt entry, and the golden fixtures in
    `tests/golden/contract/` freeze both sides of the cut."""
    slp1_key = to_slp1_auto(key, in_)
    dict_list = [d.strip() for d in dicts.split(",") if d.strip() in ALL_DICTS]
    results = _lemma_entries(con, slp1_key, out, bool(raw), dict_list)
    if not results:
        lemma = con.execute("SELECT slp1 FROM lemmas WHERE slp1=?", (slp1_key,)).fetchone()
        error("lemma_not_found", f"no entries for '{key}' (slp1={slp1_key})", 404,
              suggestions=[] if lemma is None else ["lemma exists in the union spine but has no dict entries"])
    return envelope(con, {"key": key, "in": in_, "out": out, "dicts": dict_list}, results)


@app.get("/w/{slp1}", response_class=HTMLResponse)
def word_page(slp1: str, con: sqlite3.Connection = Depends(get_db)):
    """P5-4 SSR half (H537): server-render the word page for the long tail — any
    lemma, not just the top-N the static prerender ships. Renders the EXACT same
    card the static tier holds (the /api/v1/lemma envelope) through the shared
    app/word_page.py template, so static ∥ SSR are byte-comparable on primary
    content (P5-4 parity; tests/test_word_page.py locks it). Permalinks address by
    SLP1 key, the canonical addressing scheme (P5_ADVANCED_UI_DESIGN.md §3).
    """
    slp1_key = to_slp1_auto(slp1, "slp1")
    results = _lemma_entries(con, slp1_key, "iast", False)
    dv = data_version(con)
    if not results:
        # Crawlable, honest 404 — still links the browse spine, no fabricated body.
        body = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
                f'<title>{slp1_key} — not found | kosha</title></head><body>'
                f'<main style="max-width:40rem;margin:2rem auto;font-family:system-ui">'
                f'<h1>No entry for <code>{slp1_key}</code></h1>'
                f'<p>This SLP1 key has no MW / PWG / Apte entry. '
                f'<a href="/browse/">Browse the dictionary →</a></p></main></body></html>')
        return HTMLResponse(body, status_code=404)
    card = {"data_version": dv,
            "query": {"key": slp1_key, "in": "slp1", "out": "iast", "dicts": list(ALL_DICTS)},
            "results": results}
    return HTMLResponse(render_word_page(card, token=card_token(slp1_key), data_version=dv))


def _neighbor_payload(con, row, out: str, query_L=None):
    return {
        "dict": row["dict"], "L": row["L"],
        "headword": from_slp1_out(row["slp1_key"], out),
        "pc_raw": row["pc_raw"],
        "scan_url": scan_url(row["dict"], row["page"], row["vol"]),
        "is_query": row["L"] == query_L,
    }


@app.get("/api/v1/page/{dict_id}")
def get_page(dict_id: str, page: int, vol: int = Query(None),
             merge: int = 0, out: str = "iast",
             con: sqlite3.Connection = Depends(get_db)):
    """All entries that physically shared one printed column (or, with merge=1,
    one two-column leaf) — the words that sat together on the page."""
    d = dict_id.lower()
    if d not in ALL_DICTS:
        error("bad_dict", f"unknown dict '{dict_id}'; use one of {ALL_DICTS}", 404)
    rows = (physical_page_entries(con, d, vol, page) if merge
            else column_entries(con, d, vol, page))
    if not rows:
        error("page_empty", f"no entries at {group_label(d, vol, page, merge=bool(merge))}", 404,
              suggestions=["check vol/page; PWG needs vol, MW/AP90 do not"])
    results = [_neighbor_payload(con, r, out) for r in rows]
    return envelope(con, {
        "dict": d, "vol": vol, "page": page, "merge": bool(merge), "out": out,
        "unit": "physical_page (2 columns)" if merge else "column",
        "label": group_label(d, vol, page, merge=bool(merge)),
        "count": len(results),
    }, results)


@app.get("/api/v1/neighbors/{dict_id}/{L}")
def get_neighbors(dict_id: str, L: str, merge: int = 0, out: str = "iast",
                  con: sqlite3.Connection = Depends(get_db)):
    """Given one entry, the other words printed on the same column (or leaf).
    The query entry is included, flagged is_query=true, in printed order."""
    d = dict_id.lower()
    if d not in ALL_DICTS:
        error("bad_dict", f"unknown dict '{dict_id}'; use one of {ALL_DICTS}", 404)
    loc = entry_location(con, d, L)
    if loc is None:
        error("entry_not_found", f"no {d} entry with L={L}", 404)
    if loc["page"] is None:
        error("no_location", f"{d} L={L} ({from_slp1_out(loc['slp1_key'], out)}) "
              f"has an unparseable <pc> ({loc['pc_raw']!r}); no page location", 422)
    rows = (physical_page_entries(con, d, loc["vol"], (loc["page"] + 1) // 2) if merge
            else column_entries(con, d, loc["vol"], loc["page"]))
    results = [_neighbor_payload(con, r, out, query_L=L) for r in rows]
    return envelope(con, {
        "dict": d, "L": L, "headword": from_slp1_out(loc["slp1_key"], out),
        "merge": bool(merge), "out": out,
        "unit": "physical_page (2 columns)" if merge else "column",
        "label": group_label(d, loc["vol"],
                             (loc["page"] + 1) // 2 if merge else loc["page"],
                             merge=bool(merge)),
        "count": len(results),
    }, results)


@app.get("/api/v1/form/{form}")
def get_form(form: str, in_: str = Query("auto", alias="in"),
             heritage: bool = Query(False),
             con: sqlite3.Connection = Depends(get_db)):
    # H111 trust ordering (highest to lowest): dcs > vidyut > heritage.
    # `source='heritage'` is Heritage/INRIA's rule-generated full paradigm —
    # it over-generates unattested forms under a different lemmatization
    # policy. Per the R7 ruling (10-07-2026, Uprava
    # docs/DECISIONS_roadmap_forks_2026H2.md) heritage rows are DEFAULT-OFF:
    # served only when the caller opts in with `?heritage=1` (H696).
    slp1_form = to_slp1_auto(form, in_)
    src_filter = "" if heritage else "AND source != 'heritage' "
    lemma_rows = con.execute(
        "SELECT DISTINCT lemma_slp1, source FROM forms WHERE form_slp1=? "
        f"{src_filter}", (slp1_form,)
    ).fetchall()
    lemmas = [{"lemma_slp1": r["lemma_slp1"], "lemma_iast": from_slp1_out(r["lemma_slp1"], "iast"),
               "source": r["source"]} for r in lemma_rows]
    if not lemmas:
        return envelope(con, {"form": form, "in": in_, "heritage": heritage},
                        [{"lemmas": [], "suggestions": []}])
    return envelope(con, {"form": form, "in": in_, "heritage": heritage},
                    [{"lemmas": lemmas}])


@app.get("/api/v1/forms/{form}/analyze")
def analyze_form(form: str, in_: str = Query("auto", alias="in"),
                  heritage: bool = Query(False),
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
         (lemma-only), returned under `forms_witnesses`. Heritage witnesses
         are DEFAULT-OFF per the R7 ruling (10-07-2026) -- opt in with
         `?heritage=1` (H696).
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
    result = reverse_analyze(con, slp1_form, include_heritage=heritage)
    return envelope(con, {"form": form, "in": in_, "form_slp1": slp1_form,
                          "heritage": heritage}, [result])


@app.get("/api/v1/paradigm/{lemma}")
def get_paradigm(lemma: str, in_: str = Query("auto", alias="in"),
                 con: sqlite3.Connection = Depends(get_db)):
    """P4 Wave K2b (H183): forward stem->paradigm lookup. Returns every model's
    full case x number (nominal) or voice/tense/person x number (verb) grid for
    a stem, grouped from the `inflections` table. Same JSON shape the static
    tier emits (scripts/build_paradigms.py) -- parity locked by
    tests/test_paradigms.py. Cells carry SLP1 forms; the caller renders script.

    A stem spelled as an `inflections` variant (Bagavant) is folded to its
    canonical stem (Bagavat) via `stem_bridge` before lookup, so either spelling
    lands one paradigm."""
    slp1_lemma = to_slp1_auto(lemma, in_)
    bridged = con.execute(
        "SELECT canonical_slp1 FROM stem_bridge WHERE variant_slp1=?", (slp1_lemma,)
    ).fetchone()
    canonical = bridged["canonical_slp1"] if bridged else slp1_lemma
    result = build_paradigm(con, canonical)
    if result is None:
        error("paradigm_not_found",
              f"no inflection paradigm for '{lemma}' (slp1={canonical})", 404,
              suggestions=["the stem may be a dictionary headword with no ingested "
                           "inflection table (Cologne csl-inflect coverage is partial)"])
    return envelope(con, {"lemma": lemma, "in": in_, "lemma_slp1": canonical}, [result])


#: W0C: the prefix-seek bound had a copy here and another in the Salt face.
#: Both now call the one in `kosha.api.repository` — the same de-duplication
#: the entry serializer got, applied to the query helper it sits next to.
_prefix_range_bound = repository.prefix_range_bound


def _log_search_background(anon_id: str, ts: str, query_raw: str, query_slp1: str,
                            mode: str, results_total: int, ip_hash: str | None):
    # Opens its OWN connection rather than reusing a request-scoped Depends()
    # connection: FastAPI tears down `Depends(...)` resources before
    # BackgroundTasks run, so a request-scoped connection would already be
    # closed by the time this executes.
    hcon = open_history_db()
    try:
        upsert_visitor(hcon, anon_id, ts)
        log_search_event(hcon, anon_id, ts, query_raw, query_slp1, mode, results_total, ip_hash)
    finally:
        hcon.close()


@app.get("/api/v1/search")
def search(q: str, request: Request, response: Response, background_tasks: BackgroundTasks,
           mode: str = "prefix", limit: int = 50, offset: int = 0,
           con: sqlite3.Connection = Depends(get_db)):
    if limit > 200:
        error("bad_request", "limit must be <= 200", 400)
    slp1_q = to_slp1_auto(q, "auto")
    if mode == "exact":
        where, params = "slp1 = ?", (slp1_q,)
    elif mode == "prefix":
        if slp1_q:
            where, params = "slp1 >= ? AND slp1 < ?", (slp1_q, _prefix_range_bound(slp1_q))
        else:
            where, params = "1=1", ()
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
    # Log after results are computed, via BackgroundTasks so this never adds
    # latency to the D5-1 search SLO (KOSHA_DECISIONS_NEEDED.md D5-1).
    #
    # D10 gate (H1944): with history off — the public-v1 default — no visitor
    # identity cookie is minted, no IP hash is computed, and nothing is
    # written to the history store. Mounting the read routes and silently
    # collecting anyway would be the worst of both worlds.
    if history_enabled():
        anon_id = resolve_anon_id(request, response)
        background_tasks.add_task(
            _log_search_background, anon_id, datetime.now(timezone.utc).isoformat(),
            q, slp1_q, mode, total, hash_ip(request),
        )
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
            "text_raw": arch["text_raw"],
            # Sanitized like every other served render (W0C item 6): an
            # archived body is the OLDER markup, not the safer one.
            "text_rendered": render_sanitized(dict_code, arch["text_raw"]),
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
        "text_raw": body_span,
        "text_rendered": render_sanitized(dict_code, body_span),
        "entry": {"dict": dict_code, "L": L, "headword": headword},
        "scan_url": scan_url(dict_code, row["page"], row["vol"]),
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
    try:  # H345; absent on a pre-H345 kosha.db
        counts["heritage_covered"] = con.execute(
            "SELECT COUNT(*) FROM heritage_anchor WHERE covered=1"
        ).fetchone()[0]
    except sqlite3.OperationalError:
        counts["heritage_covered"] = None
    return {
        "data_version": data_version(con),
        "sources": [dict(s) for s in sources],
        "counts": counts,
    }


# ---------------------------------------------------------------------------
# Salt facade REST faces (ARCHITECTURE.md "Maximum-reuse rules" point 4)
# ---------------------------------------------------------------------------

def _salt_entries_for_keys(con, dict_code: str, keys, dv: str) -> list[dict]:
    """Shared by both Salt faces — the same serializer `/api/v1` uses.

    An id's homonym suffix is only correct relative to the whole group, so the
    group is read even when one row is wanted.
    """
    entries = []
    for key in keys:
        rows = repository.entries_for_key(con, dict_code, key)
        for row in rows:
            entries.append(serializer.entry_dict(serializer.serialize_entry(
                con, row, hom_count=len(rows), data_version=dv,
                public_base=PUBLIC_BASE, heritage_base=HERITAGE_BASE,
            )))
    return entries


@app.get("/dicts/{dict_id}/restful/entries")
def salt_entries(dict_id: str, field: str = "headword_slp1", query: str = "",
                  query_type: str = "term", size: int = 25, input: str = "slp1",
                  output: str = "deva", con: sqlite3.Connection = Depends(get_db)):
    """Salt profile §3. Errors here keep C-SALT's bare-string form and, since
    W0C, C-SALT's status codes: the profile says a missing or invalid parameter
    MUST be HTTP 400, and these routes used to answer 200 with an error body —
    a client checking the status would have read a failure as success."""
    dict_code = dict_id.lower()
    if dict_code not in ALL_DICTS:
        error("unknown_dict", f"unknown dict '{dict_id}'", 400)
    if field not in IMPLEMENTED_FIELDS:
        # §4: an unimplemented search surface MUST 400, never return empty.
        error("unsupported_field",
              f"Missing or invalid parameter: 'field' — '{field}' is not indexed "
              f"(implemented: {sorted(IMPLEMENTED_FIELDS)})", 400)
    if query_type not in IMPLEMENTED_QUERY_TYPES:
        known = set(SaltQueryType.__args__)
        detail = ("not indexed yet" if query_type in known
                  else "not a Salt query_type")
        error("unsupported_query_type",
              f"Missing or invalid parameter: 'query_type' — '{query_type}' is "
              f"{detail} (implemented: {sorted(IMPLEMENTED_QUERY_TYPES)})", 400)
    slp1_q = to_slp1_auto(query, "slp1" if input == "slp1" else input) if query else ""
    if query_type == "term":
        where, params = "slp1_key = ?", (slp1_q,)
    else:  # prefix — H838/H1369 half-open range seek, not a case-folding LIKE
        if slp1_q:
            where, params = ("slp1_key >= ? AND slp1_key < ?",
                             (slp1_q, repository.prefix_range_bound(slp1_q)))
        else:
            where, params = "1=1", ()
    keys = repository.distinct_keys(con, dict_code, where, params, size)
    return {"data": {"entries": _salt_entries_for_keys(
        con, dict_code, keys, data_version(con))}}


@app.get("/dicts/{dict_id}/restful/ids")
def salt_ids(dict_id: str, ids: list[str] = Query(default=[]),
             con: sqlite3.Connection = Depends(get_db)):
    """Salt profile §5 — get-by-id, not a search."""
    dict_code = dict_id.lower()
    if dict_code not in ALL_DICTS:
        error("unknown_dict", f"unknown dict '{dict_id}'", 400)
    dv = data_version(con)

    def serialize(row, hom_count):
        return serializer.entry_dict(serializer.serialize_entry(
            con, row, hom_count=hom_count, data_version=dv,
            public_base=PUBLIC_BASE, heritage_base=HERITAGE_BASE,
        ))

    out_entries = []
    for req_id in ids:
        body_id = req_id[len("lemma-"):] if req_id.startswith("lemma-") else req_id
        m_l = body_id.rsplit("-L", 1)
        m_n = body_id.rsplit("-", 1)
        if len(m_l) == 2 and m_l[1].replace(".", "").isdigit():
            key, lnum = m_l[0], m_l[1]
            row = repository.entry_by_lnum(con, dict_code, lnum)
            if row is not None and row["slp1_key"] == key:
                hom_rows = repository.entries_for_key(con, dict_code, key)
                out_entries.append(serialize(row, len(hom_rows)))
            continue
        if len(m_n) == 2 and m_n[1].isdigit():
            key = m_n[0]
            hom_rows = repository.entries_for_key(con, dict_code, key)
            for r in hom_rows:
                minted = serializer.mint_salt_id(
                    r["slp1_key"], r["L"], r["body"], len(hom_rows))
                if minted == req_id:
                    out_entries.append(serialize(r, len(hom_rows)))
            continue
        # bare "lemma-{key}" — all records for that key
        hom_rows = repository.entries_for_key(con, dict_code, body_id)
        for r in hom_rows:
            out_entries.append(serialize(r, len(hom_rows)))
    return {"data": {"ids": out_entries}}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
