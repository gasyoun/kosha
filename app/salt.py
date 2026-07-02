"""kosha D4 — Salt-profile entry serialization (ARCHITECTURE.md
"Maximum-reuse rules"): per-dictionary entries inside /api/v1 responses,
and the two Salt facade REST faces, share ONE Salt-profile entry shape.

Ported from csl-apidev's real logic (api1/salt_common.php — read directly,
csl-apidev has no importable Python module), not re-derived:

    id construction (salt_common.php ~L168-181):
        homCount = # of entries.body sharing this dict+slp1_key
        if homCount > 1:
            suffix = "-{hom}" if a <hom> tag is present in this entry's body
                     else "-L{lnum}"
        else:
            suffix = ""
        id = f"lemma-{slp1_key}{suffix}"

kosha extends the Salt entry with namespaced kosha.* fields (kosha.sense_ids,
kosha.rendered_html, kosha.evidence, kosha.cite) per ARCHITECTURE §Maximum-
reuse-rules point 1 — same object, no translation layer.
"""
import re

from scan_resolver import scan_url

_RE_KEY2 = re.compile(r"<key2>(.*?)</key2>", re.S)
_RE_REFS = re.compile(r"<ls>(.*?)</ls>", re.S)
# The homonym marker is the <info hui="N"/> ATTRIBUTE on this entry's own tail
# <info> element — not a bare <hom>N</hom> text tag, which also appears deep
# inside cross-reference prose (e.g. MW L41336.1/.3 quote another headword's
# homonym number in running text) and would false-positive if matched naively.
_RE_HUI = re.compile(r'<info\b[^>]*\bhui="([^"]*)"[^>]*/?>')


def mint_salt_id(dict_code: str, slp1_key: str, lnum: str, body: str, hom_count: int) -> str:
    if hom_count <= 1:
        return f"lemma-{slp1_key}"
    hui_m = _RE_HUI.search(body)
    if hui_m:
        return f"lemma-{slp1_key}-{hui_m.group(1)}"
    return f"lemma-{slp1_key}-L{lnum}"


def entries_for_key(con, dict_code: str, slp1_key: str):
    """All entry rows sharing (dict, slp1_key) — the homonym group Salt ids
    are minted against."""
    return con.execute(
        "SELECT id, dict, L, slp1_key, k2, pc_raw, vol, page, col, body "
        "FROM entries WHERE dict=? AND slp1_key=? ORDER BY L",
        (dict_code, slp1_key),
    ).fetchall()


def salt_entry(con, row, hom_count: int, data_version_str: str) -> dict:
    """Row -> Salt-profile entry object, extended with kosha.* fields."""
    body = row["body"]
    salt_id = mint_salt_id(row["dict"], row["slp1_key"], row["L"], body, hom_count)
    refs = _RE_REFS.findall(body)
    refs = [re.sub("<[^>]+>", "", r) for r in refs]

    senses = con.execute(
        "SELECT sense_n FROM senses WHERE entry_id=? ORDER BY sense_n", (row["id"],)
    ).fetchall()
    sense_ids = [f"{row['dict']}.{row['L']}.{s['sense_n']}@{data_version_str}" for s in senses]

    return {
        "id": salt_id,
        "headword_slp1": row["slp1_key"],
        "sense": [],
        "re_headwords_slp1": [],
        "created": None,
        "xml": None,
        "csl": {
            "lnum": str(row["L"]),
            "page": str(row["page"]) if row["page"] is not None else None,
            "column": str(row["col"]) if row["col"] is not None else None,
            "scanUrl": scan_url(row["dict"], row["page"]),
            "references": refs,
            "accentedKey": row["k2"],
        },
        "kosha": {
            "sense_ids": sense_ids,
            "rendered_html": None,  # render.py partial port — see data/SOURCES.md D4 note
            "evidence": [],
            "cite": {
                "text": f"{row['dict']}.{row['L']}.1@{data_version_str}",
                "bibtex": None,
                "csl_json": None,
            },
        },
    }
