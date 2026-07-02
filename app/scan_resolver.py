"""kosha D3 — entry -> scan-URL resolver (Cologne servepdf, page-image scans).

NB deviation from PHASE1_PLAN.md D3's literal wording ("port ls_resolver.py
for entry->scan-URL resolution"): SanskritLexicography/RussianTranslation/src/
ls_resolver.py (1226 lines) is a faithful port of csl-app's LsService — it
resolves <ls> CITATION cross-references embedded in entry prose (RV./AV./MBh./
Pāṇini sūtra numbers etc.) to EXTERNAL corpus scan/HTML viewers. It has no
serveimg/servepdf logic and cannot resolve "this entry's own dictionary page
scan" — a different, much simpler Cologne mechanism documented at
COLOGNE/api/servepdf.md. That is what this module implements (small, NEW,
per PHASE1_PLAN's own allowance for genuinely-new D2/D3 glue). ls_resolver.py
itself is out of scope for D3 (it belongs to the render()/citation-body work,
not scan-link resolution) — flagged, not silently skipped.

Pattern (COLOGNE/api/servepdf.md, live-verified 02-07-2026):
    https://sanskrit-lexicon.uni-koeln.de/scans/{DICT}Scan/2020/web/webtc/servepdf.php?page={page}
dictcode is uppercase (MW, PWG, AP90, ...). No documented volume parameter
for multi-volume dicts (PWG) — `page` is passed as-is; PWG's own <pc> `page`
component is per-volume, so cross-volume scan addressing for PWG is a known
open item (not blocking: the URL still resolves to *a* servepdf.php page,
verified live below, just not disambiguated by volume server-side).
"""
DICT_SCAN_DIR = {"mw": "MW", "pwg": "PWG", "ap90": "AP90"}


def scan_url(dict_code: str, page) -> str | None:
    """(dict, page) -> Cologne servepdf.php scan-viewer URL, or None if the
    dict has no known scan directory. Deterministic, no table (ARCHITECTURE.md:
    "Scan URLs are computed, not stored")."""
    scan_dir = DICT_SCAN_DIR.get(dict_code.lower())
    if scan_dir is None or page is None:
        return None
    return (
        f"https://sanskrit-lexicon.uni-koeln.de/scans/{scan_dir}Scan/2020/"
        f"web/webtc/servepdf.php?page={page}"
    )
