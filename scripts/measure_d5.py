"""D5 measurement harness (PHASE1_PLAN.md D5, ARCHITECTURE.md A4).

Emits the real numbers behind the three parked SLO decisions — DB size, cold/warm
lookup latency across the four /api/v1 read paths (incl. the fat MW `ka` homonym
group), per-dict render() cost on the densest cards, and a top-N static-cache
size projection vs the GitHub 100 MB per-file / 2 GB release-asset ceilings
(RISKS.md R11). All local; no live third-party calls (RISKS.md R12).

Run:  python scripts/measure_d5.py            # full run, human-readable
      python scripts/measure_d5.py --json      # machine-readable dump too

Methodology notes (EVAL_PLAN.md anti-gaming — state what is and isn't measured):
- "warm" = repeated call, OS file-cache hot: the steady-state a running server
  sees. Reported as median + p95 over N iterations.
- "cold" = first call on a freshly-opened read-only connection. NB the app opens
  a NEW sqlite connection per request (app/db.py get_db), so every real request
  starts with an empty sqlite page cache; only the OS file cache carries over.
  True cold-*disk* (OS cache dropped) is not simulated — Windows lacks a portable
  drop-caches; the cold number here is cold-connection / warm-OS, and is labelled
  as such.
- Endpoint latency is measured two ways: (a) the raw DB+render handler cost via
  direct function calls (what the SLO should target), and (b) end-to-end through
  Starlette TestClient (adds ASGI/serialization overhead a real client also pays).
"""
import json
import os
import sqlite3
import statistics
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
DB_PATH = ROOT / "data" / "db" / "kosha.db"

from render import render  # noqa: E402


def _con():
    c = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


def _pct(xs, p):
    xs = sorted(xs)
    if not xs:
        return 0.0
    k = min(len(xs) - 1, int(round((p / 100) * (len(xs) - 1))))
    return xs[k]


def _time_ms(fn, iters):
    ts = []
    for _ in range(iters):
        t0 = time.perf_counter()
        fn()
        ts.append((time.perf_counter() - t0) * 1000)
    return {
        "n": iters,
        "median_ms": round(statistics.median(ts), 3),
        "p95_ms": round(_pct(ts, 95), 3),
        "max_ms": round(max(ts), 3),
        "min_ms": round(min(ts), 3),
    }


def section(t):
    print("\n" + "=" * 72)
    print(t)
    print("=" * 72)


def measure_db_size():
    section("1. DB SIZE ON DISK + PER-OBJECT BREAKDOWN")
    size = os.path.getsize(DB_PATH)
    con = _con()
    ps = con.execute("PRAGMA page_size").fetchone()[0]
    pc = con.execute("PRAGMA page_count").fetchone()[0]
    print(f"file: {size:,} bytes = {size/1024/1024:.1f} MiB = {size/1e6:.1f} MB(dec)")
    print(f"page_size={ps}  page_count={pc:,}")
    print(f"GitHub 100 MB per-file limit: {'OVER' if size > 100e6 else 'under'} "
          f"({size/100e6*100:.0f}% of 100 MB) -> ships as release asset, not in-repo (R11)")
    print(f"2 GB release-asset ceiling: {size/2e9*100:.1f}% of 2 GB (ample)")
    counts = {}
    for (n,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        counts[n] = con.execute(f"SELECT COUNT(*) FROM {n}").fetchone()[0]
    print("row counts:", {k: f"{v:,}" for k, v in counts.items()})
    breakdown = {}
    try:
        print(f"\n{'object':22} {'bytes':>14} {'MiB':>8} {'%':>6}")
        for r in con.execute(
                "SELECT name, SUM(pgsize) b, COUNT(*) p FROM dbstat GROUP BY name ORDER BY b DESC"):
            name, b = r[0], r[1]
            breakdown[name] = b
            print(f"{name:22} {b:>14,} {b/1024/1024:>8.1f} {b/size*100:>5.1f}%")
    except Exception as e:
        print("dbstat unavailable:", e)
    con.close()
    return {"file_bytes": size, "page_size": ps, "page_count": pc,
            "row_counts": counts, "object_bytes": breakdown}


def _densest(con, dict_code, k=3):
    return con.execute(
        "SELECT id, L, slp1_key, length(body) n, body FROM entries WHERE dict=? "
        "ORDER BY length(body) DESC LIMIT ?", (dict_code, k)).fetchall()


def measure_render():
    section("2. render() COST ON THE DENSEST CARDS (per dict)")
    con = _con()
    out = {}
    for d in ("mw", "pwg", "ap90"):
        rows = _densest(con, d, 3)
        med = con.execute(
            "SELECT length(body) FROM entries WHERE dict=? ORDER BY length(body) "
            "LIMIT 1 OFFSET (SELECT COUNT(*)/2 FROM entries WHERE dict=?)",
            (d, d)).fetchone()[0]
        print(f"\n[{d}] median body={med:,} chars; top-3 densest:")
        dd = []
        for r in rows:
            html = render(d, r["body"])
            t = _time_ms(lambda: render(d, r["body"]), 30)
            print(f"  L={r['L']:>10} key={r['slp1_key'][:18]:18} body={r['n']:>7,}c "
                  f"html={len(html):>7,}c  median={t['median_ms']:.2f}ms p95={t['p95_ms']:.2f}ms max={t['max_ms']:.2f}ms")
            dd.append({"L": r["L"], "body_chars": r["n"], "html_chars": len(html), **t})
        # representative-card render cost: sample 200 random-ish entries by rowid stride
        sample = con.execute(
            "SELECT body FROM entries WHERE dict=? AND id % 977 = 0 LIMIT 200", (d,)).fetchall()
        bodies = [s["body"] for s in sample]
        st = _time_ms(lambda: [render(d, b) for b in bodies], 5)
        per_card = st["median_ms"] / max(len(bodies), 1)
        print(f"  [{d}] representative sample n={len(bodies)}: ~{per_card:.3f} ms/card (median of {st['n']} passes)")
        out[d] = {"median_body_chars": med, "densest": dd,
                  "sample_n": len(bodies), "ms_per_card": round(per_card, 4)}
    con.close()
    return out


# --- keys chosen for latency: a light hit, a mid hit, and the fat MW `ka` group ---
LEMMA_KEYS = [("mw", "kamala"), ("mw", "ka"), ("pwg", "agni"), ("ap90", "deva")]
FORM_KEYS = ["bhagavAn", "gacCati", "devasya"]
SEARCH_QS = [("ka", "prefix"), ("deva", "prefix"), ("agni", "exact"), ("kam", "fuzzy")]


def _cold_call(fn):
    """One-shot timing on a freshly-opened connection (empty sqlite page cache).
    NB the app opens a new RO connection per request (app/db.py), so this is the
    real per-request start state; OS file cache still carries over (cold-conn /
    warm-OS, not cold-disk)."""
    t0 = time.perf_counter()
    fn()
    return (time.perf_counter() - t0) * 1000


def measure_handler_latency():
    section("3. HANDLER LATENCY — real endpoint functions (the SLO target)")
    # Call the ACTUAL /api/v1 handler functions from app/main.py, passing a
    # sqlite connection in place of the Depends(get_db) injection. This exercises
    # the exact production code path (transliteration, render, envelope,
    # _entry_payload, sense_id formatting) minus only the HTTP/ASGI framing
    # (measured separately in section 4).
    import main as m  # noqa: E402
    from fastapi import BackgroundTasks, HTTPException, Response
    from starlette.requests import Request as StarletteRequest
    con_warm = _con()
    results = {}

    def _fake_request():
        # search()'s handler signature grew request/response/background_tasks
        # params (anon-visitor logging, added after this harness was first
        # written) -- a minimal ASGI scope is enough to satisfy
        # resolve_anon_id()/hash_ip() (H838 remeasure needed this restored).
        scope = {"type": "http", "headers": [], "client": ("127.0.0.1", 0),
                  "method": "GET", "path": "/api/v1/search", "query_string": b""}
        return StarletteRequest(scope)

    def call(fn, *a, **kw):
        try:
            return fn(*a, con=con_warm, **kw)
        except HTTPException:
            return None

    print("\n--- /api/v1/lemma ---")
    lat = {}
    for dcode, key in LEMMA_KEYS:
        def work(dcode=dcode, key=key, con=con_warm):
            try:
                m.get_lemma(key, in_="auto", out="iast", dicts=dcode, raw=0, con=con)
            except HTTPException:
                pass
        work()  # prime
        res = m.get_lemma(key, in_="auto", out="iast", dicts=dcode, raw=0, con=con_warm)
        nrows = len(res["results"]) if isinstance(res, dict) else 0
        warm = _time_ms(work, 20)
        cold = _cold_call(lambda: m.get_lemma(
            key, in_="auto", out="iast", dicts=dcode, raw=0, con=_con()))
        print(f"  {dcode}/{key:10} entries={nrows:>3}  WARM median={warm['median_ms']:.2f}ms "
              f"p95={warm['p95_ms']:.2f}ms  COLD(new-con)={cold:.2f}ms")
        lat[f"{dcode}/{key}"] = {"entries": nrows, "warm": warm, "cold_newcon_ms": round(cold, 3)}
    results["lemma"] = lat

    print("\n--- /api/v1/search ---")
    lat = {}
    for q, mode in SEARCH_QS:
        def work(q=q, mode=mode, con=con_warm):
            m.search(q=q, request=_fake_request(), response=Response(),
                      background_tasks=BackgroundTasks(), mode=mode,
                      limit=50, offset=0, con=con)
        work()
        res = m.search(q=q, request=_fake_request(), response=Response(),
                         background_tasks=BackgroundTasks(), mode=mode,
                         limit=50, offset=0, con=con_warm)
        total = res["query"]["total"]
        warm = _time_ms(work, 20)
        cold = _cold_call(lambda: m.search(
            q=q, request=_fake_request(), response=Response(),
            background_tasks=BackgroundTasks(), mode=mode, limit=50, offset=0, con=_con()))
        print(f"  q={q:8} mode={mode:7} total={total:>7,}  WARM median={warm['median_ms']:.2f}ms "
              f"p95={warm['p95_ms']:.2f}ms  COLD={cold:.2f}ms")
        lat[f"{q}/{mode}"] = {"total": total, "warm": warm, "cold_newcon_ms": round(cold, 3)}
    results["search"] = lat

    print("\n--- /api/v1/form ---")
    lat = {}
    for form in FORM_KEYS:
        def work(form=form, con=con_warm):
            m.get_form(form, in_="auto", con=con)
        work()
        warm = _time_ms(work, 20)
        cold = _cold_call(lambda: m.get_form(form, in_="auto", con=_con()))
        print(f"  form={form:10}  WARM median={warm['median_ms']:.3f}ms "
              f"p95={warm['p95_ms']:.3f}ms  COLD={cold:.3f}ms")
        lat[form] = {"warm": warm, "cold_newcon_ms": round(cold, 3)}
    results["form"] = lat

    print("\n--- /api/v1/sense (single citable unit) ---")
    lat = {}
    # three senses on the fat MW `ka` group + the banD fixture
    ids = [r[0] for r in con_warm.execute(
        "SELECT e.dict||'.'||e.L||'.'||s.sense_n "
        "FROM senses s JOIN entries e ON e.id=s.entry_id "
        "WHERE e.dict='mw' AND e.slp1_key='ka' ORDER BY e.L LIMIT 3")]
    ids.append("mw.142512.1")
    for sid in ids:
        def work(sid=sid, con=con_warm):
            try:
                m.get_sense(sid, v=None, con=con)
            except HTTPException:
                pass
        work()
        warm = _time_ms(work, 30)
        print(f"  {sid:16}  WARM median={warm['median_ms']:.3f}ms p95={warm['p95_ms']:.3f}ms")
        lat[sid] = {"warm": warm}
    results["sense"] = lat

    con_warm.close()
    return results


def measure_endpoint_e2e():
    section("4. END-TO-END via live uvicorn + httpx (adds real HTTP+ASGI+JSON)")
    # A live server is the honest e2e number a browser client sees. Timeout-guarded
    # so a stall can never hang the harness (the TestClient path did on 3.14).
    import socket
    import subprocess
    import threading
    import urllib.request

    port = 8077
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
         "--port", str(port), "--log-level", "warning"],
        cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def up():
        s = socket.socket()
        s.settimeout(0.3)
        try:
            s.connect(("127.0.0.1", port))
            return True
        except OSError:
            return False
        finally:
            s.close()

    ok = False
    for _ in range(60):  # up to ~6 s startup
        if up():
            ok = True
            break
        time.sleep(0.1)
    if not ok:
        print("  server did not come up in time; skipping e2e")
        proc.terminate()
        return {}

    def get(url, timeout=10):
        req = urllib.request.Request(f"http://127.0.0.1:{port}{url}")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()

    out = {}
    cases = [
        ("lemma ka (fat)", "/api/v1/lemma/ka"),
        ("lemma kamala", "/api/v1/lemma/kamala"),
        ("lemma pwg sTA (huge)", "/api/v1/lemma/sTA?dicts=pwg"),
        ("search ka prefix", "/api/v1/search?q=ka&mode=prefix&limit=50"),
        ("form bhagavAn", "/api/v1/form/bhagavAn"),
        ("sense mw.142512.1", "/api/v1/sense/mw.142512.1"),
        ("meta", "/api/v1/meta"),
    ]
    try:
        for label, url in cases:
            try:
                st, body = get(url)
            except Exception as e:
                print(f"  {label:24} ERROR {e}")
                continue
            size = len(body)
            warm = _time_ms(lambda: get(url), 15)
            print(f"  {label:24} HTTP {st}  resp={size:>9,}B  "
                  f"WARM median={warm['median_ms']:.2f}ms p95={warm['p95_ms']:.2f}ms")
            out[label] = {"status": st, "resp_bytes": size, "warm": warm}
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
    return out


def measure_static_cache():
    section("5. TOP-N STATIC-CACHE SIZE PROJECTION (R11: Pages tier)")
    con = _con()
    from transliterate import from_slp1_out
    from scan_resolver import scan_url
    # A per-lemma static card = merged view across dicts: for each entry, rendered
    # HTML + headword + scan_url + sense_ids. Estimate the JSON payload size per
    # lemma by building real payloads for a frequency-representative sample.
    # Sample: take lemmas present in >=1 dict, strided across the entries table.
    sample_keys = con.execute(
        "SELECT DISTINCT slp1_key FROM entries WHERE id % 337 = 0 LIMIT 400").fetchall()
    sizes = []
    entry_counts = []
    for row in sample_keys:
        key = row["slp1_key"]
        payload = {"lemma": key, "iast": from_slp1_out(key, "iast"), "entries": []}
        for d in ("mw", "pwg", "ap90"):
            ents = con.execute("SELECT * FROM entries WHERE dict=? AND slp1_key=? ORDER BY L",
                               (d, key)).fetchall()
            for e in ents:
                senses = con.execute("SELECT sense_n FROM senses WHERE entry_id=?",
                                     (e["id"],)).fetchall()
                payload["entries"].append({
                    "dict": d, "L": e["L"],
                    "headword": from_slp1_out(e["slp1_key"], "iast"),
                    "rendered_html": render(d, e["body"]),
                    "scan_url": scan_url(d, e["page"], e["vol"]),
                    "sense_ids": [f"{d}.{e['L']}.{s['sense_n']}" for s in senses],
                })
        b = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        sizes.append(b)
        entry_counts.append(len(payload["entries"]))
    avg = statistics.mean(sizes)
    med = statistics.median(sizes)
    p95 = _pct(sizes, 95)
    total_lemmas = con.execute("SELECT COUNT(*) FROM lemmas").fetchone()[0]
    lemmas_with_entries = con.execute(
        "SELECT COUNT(DISTINCT slp1_key) FROM entries").fetchone()[0]
    print(f"sample n={len(sizes)} lemmas (with entries): "
          f"avg payload={avg:,.0f}B  median={med:,.0f}B  p95={p95:,.0f}B  "
          f"avg entries/lemma={statistics.mean(entry_counts):.2f}")
    print(f"lemmas total={total_lemmas:,}; with >=1 dict entry={lemmas_with_entries:,}")
    print(f"\n{'N (top lemmas)':>16} | {'as single JSON file':>22} | {'vs 100MB/file':>14} | {'gzip~30%':>12}")
    for N in (1000, 5000, 10000, 50000, 100000, lemmas_with_entries):
        raw = avg * N
        label = f"{N:,}" if N != lemmas_with_entries else f"ALL {N:,}"
        flag = "OVER" if raw > 100e6 else "ok"
        print(f"{label:>16} | {raw/1e6:>19.1f}MB | {flag:>14} | {raw*0.3/1e6:>9.1f}MB")
    con.close()
    return {"sample_n": len(sizes), "avg_bytes": round(avg), "median_bytes": med,
            "p95_bytes": p95, "avg_entries_per_lemma": round(statistics.mean(entry_counts), 3),
            "total_lemmas": total_lemmas, "lemmas_with_entries": lemmas_with_entries}


def main():
    print(f"kosha D5 measurement — DB={DB_PATH}")
    print(f"data_version (meta): "
          f"{_con().execute('SELECT value FROM meta').fetchone()[0]}")
    res = {}
    res["db_size"] = measure_db_size()
    res["render"] = measure_render()
    res["handler_latency"] = measure_handler_latency()
    res["endpoint_e2e"] = measure_endpoint_e2e()
    res["static_cache"] = measure_static_cache()
    if "--json" in sys.argv:
        out = ROOT / "data" / "d5_measurements.json"
        out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON dump -> {out}")


if __name__ == "__main__":
    main()
