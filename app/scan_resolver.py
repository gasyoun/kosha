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
dictcode is uppercase (MW, PWG, AP90, ...).

Multi-volume disambiguation (H839, 13-07-2026, resolved definitively -- source
read + live content-diff, not just status-code probing):
  - Cologne's servepdf.php has NO `vol=`/`volume=` GET parameter at all.
    `Parm::servepdfParms()` (csl-apidev/parm.php) reads only `$_REQUEST['page']`
    (and `key`) -- any other query param is silently ignored, which is why the
    endpoint returns 200 regardless of what a `vol=`/`volume=` guess is set to.
  - The real mechanism: for PWG, volume lives INSIDE the `page` value itself,
    as `"{vol}-{page:04d}"` (e.g. "1-0001", "7-0001") -- this is exactly PWG's
    own <pc> "vol-Spalte" format, and matches the literal keys in Cologne's
    pdffiles.txt (see PWG/pwgissues/issue76/pwgvn/pdffiles.txt: "1-0001:...",
    "7-0001:...", 7 volumes total) that ServepdfClass::getImagefiles()
    (csl-apidev/servepdfClass.php) looks the page up against.
  - Live-verified against the production endpoint: page=1-0001 -> pwg1-0001.pdf;
    page=7-0001 -> pwg7-0001.pdf (different scans, proving the vol-page format
    IS honored). page=1-0001&vol=99 -> byte-identical to page=1-0001 (vol=
    proven ignored). page=1&vol=7 -> STILL resolves to pwg1-0001.pdf, i.e. a
    bare page silently defaults to volume 1 no matter what vol= says -- the
    exact ambiguity bug this module now avoids by requiring `vol` for PWG.
  - MW/AP90 are single-volume; `vol` is not applicable there (always None in
    kosha's own `entries.vol` column, per app/neighbors.py's parse_pc()).
"""
DICT_SCAN_DIR = {"mw": "MW", "pwg": "PWG", "ap90": "AP90"}
# Dicts whose Cologne pdffiles.txt keys are "{vol}-{page:04d}" rather than a
# bare page/column number -- see module docstring for the live-verified proof.
MULTI_VOLUME_DICTS = {"pwg"}


def scan_url(dict_code: str, page, vol=None) -> str | None:
    """(dict, page[, vol]) -> Cologne servepdf.php scan-viewer URL, or None if
    the dict has no known scan directory. Deterministic, no table
    (ARCHITECTURE.md: "Scan URLs are computed, not stored").

    For multi-volume dicts (PWG) `vol` is required: Cologne has no vol=/volume=
    GET param (see module docstring), so the caller MUST pass kosha's own
    `entries.vol` for the row, and this function folds it into the `page`
    value as "{vol}-{page:04d}" -- the only mechanism Cologne actually honors.
    Without `vol`, a multi-volume dict returns None rather than emitting a
    silently-wrong (defaults-to-volume-1) link.
    """
    dict_key = dict_code.lower()
    scan_dir = DICT_SCAN_DIR.get(dict_key)
    if scan_dir is None or page is None:
        return None
    if dict_key in MULTI_VOLUME_DICTS:
        if vol is None:
            return None
        page_param = f"{int(vol)}-{int(page):04d}"
    else:
        page_param = page
    return (
        f"https://sanskrit-lexicon.uni-koeln.de/scans/{scan_dir}Scan/2020/"
        f"web/webtc/servepdf.php?page={page_param}"
    )
