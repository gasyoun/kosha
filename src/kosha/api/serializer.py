"""kosha — the one entry serializer (W0C items 2–4, H1945).

`/api/v1/lemma`, the `/dicts/*` Salt faces, the prerendered static cards and
the `/w/{slp1}` SSR page all consume one full entry model. Until W0C they produced
*three* entry objects held together by a comment ("Mirror of
app/main.py::_entry_payload — keep the two in lockstep") and by nobody
changing them. That is the drift D13 exists to end: one serializer, explicit
public projections, and parity tests that fail when shared fields diverge.

Everything crossing this boundary is built on the Salt profile
(`kosha.api.models`); the strict `/dicts/*` projection is defined at the end of
this module. The rendered HTML crossing it is sanitized
(`kosha.api.sanitize`) — those are the same boundary on purpose. A surface that
wants entry HTML gets it through here and therefore gets it sanitized; there is
no path that serves `render()` output directly.
"""

from __future__ import annotations

import re
import sqlite3

from kosha.api import repository
from kosha.api.models import (
    CiteObject,
    CslBlock,
    HeritageWitness,
    KoshaBlock,
    SaltEntry,
)
from kosha.api.sanitize import sanitize_html
from kosha.cite import cite_object
from kosha.evidence import build_evidence
from kosha.render import render
from kosha.scan_resolver import scan_url
from kosha.transliterate import from_slp1_out

#: Ported from csl-apidev `api1/salt_common.php` (~L168-181), read directly
#: rather than re-derived: the homonym marker is the `<info hui="N"/>`
#: attribute on the entry's own tail element. A bare `<hom>N</hom>` text tag
#: also occurs deep inside cross-reference prose (MW L41336.1/.3 quote another
#: headword's homonym number in running text), so matching that would
#: false-positive.
_RE_HUI = re.compile(r'<info\b[^>]*\bhui="([^"]*)"[^>]*/?>')
_RE_REFS = re.compile(r"<ls>(.*?)</ls>", re.S)
_RE_TAGS = re.compile(r"<[^>]+>")
_RE_WS = re.compile(r"\s+")


def mint_salt_id(slp1_key: str, lnum: str, body: str, hom_count: int) -> str:
    """Salt profile §8.1 entry id.

    `lemma-{key}` for a unique headword; `lemma-{key}-{hui}` when the record
    carries Cologne's own homonym number; `lemma-{key}-L{lnum}` for un-numbered
    sub-records, which is the sanctioned Phase-1 divergence the profile records
    in its loss report — ids must stay unique even where Cologne numbered
    nothing.
    """
    if hom_count <= 1:
        return f"lemma-{slp1_key}"
    hui = _RE_HUI.search(body)
    if hui:
        return f"lemma-{slp1_key}-{hui.group(1)}"
    return f"lemma-{slp1_key}-L{lnum}"


def render_sanitized(dict_code: str, markup: str) -> str:
    """Render Cologne markup to serve-able HTML — the only sanctioned path.

    `render()` is the faithful `basicdisplay.php` port and stays that way
    (`tests/test_render_golden.py` locks it); nothing outside this module
    should call it and serve the result. `/api/v1/sense` did exactly that for
    both its live and its archived branches, which meant the entire sanitizer
    could be walked around by asking for a sense instead of a lemma — an
    archived body is the *older*, less-scrutinized markup of the two.
    """
    return sanitize_html(render(dict_code, markup))


def _plain(markup: str) -> str:
    """Tags stripped, whitespace collapsed — a gloss string, not a rendering."""
    return _RE_WS.sub(" ", _RE_TAGS.sub("", markup or "")).strip()


def _sense_glosses(body: str, senses: list[sqlite3.Row]) -> list[str]:
    """Salt profile §8.1 `sense[]`.

    Cheap on purpose: the spans are sliced from the stored body and stripped,
    not re-rendered. A Salt face may return 25 entries per request, and
    rendering every sense of every one of them separately would multiply the
    render cost by the sense count for a field whose contract is "sense
    glosses", i.e. text.
    """
    glosses = []
    for sense in senses:
        gloss = _plain(body[sense["span_start"]:sense["span_end"]])
        if gloss:
            glosses.append(gloss)
    return glosses


def _heritage(
    row: sqlite3.Row | None | bool, heritage_base: str
) -> HeritageWitness | None:
    """`False` (no `heritage_anchor` table in this build) → `None`.

    Absence of the layer and a negative finding are different facts; see
    `repository.heritage_row`.
    """
    if row is False:
        return None
    if row is None or not row["covered"]:
        return HeritageWitness(covered=False)
    anchor = row["anchor"]
    return HeritageWitness(
        covered=True,
        anchor=anchor,
        # The DICO key after the fragment is Heritage's own lemma spelling
        # (Velthuis-style, homonym suffix kept, e.g. "a.mzaka#1"); None on the
        # ~2.3% unresolved-anchor tier.
        heritage_lemma=anchor.split("#", 1)[1] if anchor else None,
        # Site-relative anchor + configurable host, like COLOGNE_SCAN_BASE:
        # the link target stays deployable elsewhere.
        url=heritage_base + anchor if anchor else None,
    )


def serialize_entry(
    con: sqlite3.Connection,
    row: sqlite3.Row,
    *,
    hom_count: int,
    data_version: str,
    public_base: str,
    out: str = "iast",
    include_raw: bool = False,
    heritage_base: str = "https://sanskrit.inria.fr/",
) -> SaltEntry:
    """One `entries` row → the Salt-profile entry every surface serves.

    `hom_count` is the size of the row's homonym group and cannot be derived
    from the row alone — the id suffix depends on it, so the caller must have
    read the whole group (`repository.entries_for_key`).
    """
    body = row["body"]
    senses = repository.sense_rows(con, row["id"])
    sense_ids = [
        f"{row['dict']}.{row['L']}.{s['sense_n']}@{data_version}" for s in senses
    ]

    heritage = _heritage(repository.heritage_row(con, row["slp1_key"]), heritage_base)

    headword = from_slp1_out(row["slp1_key"], out)
    scan = scan_url(row["dict"], row["page"], row["vol"])

    return SaltEntry(
        id=mint_salt_id(row["slp1_key"], row["L"], body, hom_count),
        headword_slp1=row["slp1_key"],
        sense=_sense_glosses(body, senses),
        # kosha has no run-on/sub-headword layer; an empty list is the honest
        # answer, not a placeholder to be filled by guesswork.
        re_headwords_slp1=[],
        created=None,
        # Profile §8.1: MUST stay null until TEI conversion ships, and MUST NOT
        # be filled with CSL display-XML — that is `csl.xmlCsl` below.
        xml=None,
        csl=CslBlock(
            lnum=str(row["L"]),
            page=str(row["page"]) if row["page"] is not None else None,
            column=str(row["col"]) if row["col"] is not None else None,
            scanUrl=scan,
            references=[_plain(ref) for ref in _RE_REFS.findall(body)],
            accentedKey=row["k2"],
            headwordIast=from_slp1_out(row["slp1_key"], "iast"),
            headwordDeva=from_slp1_out(row["slp1_key"], "deva"),
            xmlCsl=body if include_raw else None,
        ),
        kosha=KoshaBlock(
            dict_code=row["dict"],
            L=str(row["L"]),
            headword=headword,
            scan_url=scan,
            sense_ids=sense_ids,
            rendered_html=render_sanitized(row["dict"], body),
            evidence=build_evidence(repository.lemma_row(con, row["slp1_key"])),
            heritage=heritage,
            cite=CiteObject(
                **cite_object(
                    row["dict"], row["L"], 1, data_version, public_base, headword
                )
            ),
            raw=body if include_raw else None,
        ),
    )


def serialize_lemma_card(
    con: sqlite3.Connection,
    slp1_key: str,
    *,
    data_version: str,
    public_base: str,
    out: str = "iast",
    dicts=repository.ALL_DICTS,
    include_raw: bool = False,
    heritage_base: str = "https://sanskrit.inria.fr/",
) -> list[SaltEntry]:
    """Every dictionary's entry for one headword — the lemma card.

    This is the function the API route, the SSR route and the static-card
    builder all call, which is what makes their outputs comparable rather than
    merely similar.
    """
    return [
        serialize_entry(
            con,
            row,
            hom_count=hom_count,
            data_version=data_version,
            public_base=public_base,
            out=out,
            include_raw=include_raw,
            heritage_base=heritage_base,
        )
        for row, hom_count in repository.entries_for_key_across_dicts(
            con, slp1_key, dicts
        )
    ]


def entry_dict(entry: SaltEntry) -> dict:
    """JSON-ready form — the single place the wire shape is produced.

    `by_alias=True` because `kosha.dict_code` serializes as `dict`, and
    `exclude_none` stays off deliberately: `xml: null` and `heritage: null` are
    contract-bearing values (profile §8.1 / the missing-layer distinction), not
    absent fields to be tidied away.
    """
    return entry.model_dump(mode="json", by_alias=True)


# Salt profile v0.1.0 §8.1/§9: the strict public face may add `csl` and no
# other top-level object. Keep this projection at the HTTP boundary while the
# full serializer remains shared by every surface.
SALT_FACE_TOP_LEVEL = (
    "id",
    "headword_slp1",
    "sense",
    "re_headwords_slp1",
    "created",
    "xml",
    "csl",
)


def salt_face_entry_dict(entry: SaltEntry) -> dict:
    """Project one full kosha entry onto the strict CSL Salt wire contract.

    `/api/v1`, static cards, and SSR retain the namespaced `kosha` block. The
    `/dicts/*` compatibility faces expose only C-SALT fields plus the one
    extension Salt §9 permits: `csl`.
    """
    full = entry_dict(entry)
    return {field: full[field] for field in SALT_FACE_TOP_LEVEL}
