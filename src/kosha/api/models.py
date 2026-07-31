"""kosha — the canonical typed API contract (W0C item 1, H1945).

Before W0C the payload shape existed only as dict literals built in three
places that were kept in step by a comment saying "keep the two in lockstep"
(`app/main.py::_entry_payload`, `scripts/build_static_cache.py::entry_payload`,
`app/salt.py::salt_entry`). Nothing enforced it. These models are the contract
those three now serialize *through*, so a field added in one place cannot go
missing in another.

The shape is the **C-SALT / CSL Salt profile**
([SALT_API_PROFILE.md](https://github.com/sanskrit-lexicon/csl-standards/blob/main/docs/SALT_API_PROFILE.md)
§8), which D6 makes binding for `/api/v1`:

* §8.1 top-level fields (`id`, `headword_slp1`, `sense`, `re_headwords_slp1`,
  `created`, `xml`) reproduce C-SALT exactly, so a client written against
  C-SALT reads a kosha entry unchanged;
* §8.2's `csl` object carries Cologne record provenance — the lnum, the scan
  coordinates, the reference labels, the accented key;
* a `kosha` object carries everything that is kosha's own work and has no slot
  in either model: sense ids, the rendered HTML, the evidence badges, the
  Heritage witness, and the citation payload.

**Why the rendered HTML lives under `kosha`, not `csl.html`.** The profile
lists `csl.html` as the CSL *host's* own rendering. kosha is not that host — it
is a derivative that re-renders Cologne markup through its own port of
`basicdisplay.php` (`app/render.py`) and then sanitizes it
(`kosha.api.sanitize`). Publishing our render in Cologne's slot would claim an
authority we do not have, so `csl.html`/`csl.text` stay `None` and the render
is served, honestly attributed, at `kosha.rendered_html`. D6's rule — kosha-only
fields namespaced under `kosha` — points the same way.

`xml` stays `None` per profile §8.1 until TEI conversion ships; it MUST NOT
carry CSL display-XML. The unmodified Cologne markup is available instead at
`csl.xmlCsl`, opt-in (`?raw=1`) because it doubles the payload.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CslBlock(BaseModel):
    """Salt profile §8.2 — Cologne record provenance.

    Field names are camelCase because the profile fixes them that way; this is
    the one place in the codebase where that casing is correct rather than a
    style slip.
    """

    model_config = ConfigDict(extra="forbid")

    lnum: str
    page: str | None = None
    column: str | None = None
    scanUrl: str | None = None  # noqa: N815 — profile-mandated casing
    references: list[str] = Field(default_factory=list)
    accentedKey: str | None = None  # noqa: N815 — profile-mandated casing
    headwordIast: str | None = None  # noqa: N815 — profile-mandated casing
    headwordDeva: str | None = None  # noqa: N815 — profile-mandated casing
    #: Unmodified Cologne display-XML. Populated only when the caller asks for
    #: it; the raw bytes are never rewritten (only the *rendered* copy is
    #: sanitized), so this stays the auditable original.
    xmlCsl: str | None = None  # noqa: N815 — profile-mandated casing
    #: The CSL host's own rendering. kosha does not have it — see the module
    #: docstring. Present so the object stays profile-shaped, always None here.
    html: str | None = None
    text: str | None = None


class HeritageWitness(BaseModel):
    """H345 — is this headword in Heritage/INRIA's hand-built lexicon?

    A coverage/link-out signal, deliberately not the rule-generated
    `forms.source='heritage'` paradigm layer (H111, lowest trust).
    """

    model_config = ConfigDict(extra="forbid")

    covered: bool
    anchor: str | None = None
    heritage_lemma: str | None = None
    url: str | None = None


class CiteObject(BaseModel):
    """RISKS.md R1 — what makes a 2026 citation resolve in a 2028 browser."""

    model_config = ConfigDict(extra="forbid")

    text: str
    resolution_url: str
    #: `None` for `*-dev` builds, which ship no release and are not citable.
    release_asset: str | None = None
    bibtex: str
    csl_json: dict[str, Any]


class KoshaBlock(BaseModel):
    """D6 — everything kosha adds beyond C-SALT and CSL, namespaced.

    A C-SALT client that ignores this object loses nothing C-SALT defines.
    """

    #: `populate_by_name` so the block can be built with either the wire name
    #: (`dict`) or the Python name (`dict_code`); serialization always uses the
    #: alias, so the wire shape is unaffected by the rename.
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    #: Named `dict_code` in Python because a field literally called `dict`
    #: shadows `BaseModel.dict`; the alias keeps the wire name `dict`, which is
    #: what every existing client reads.
    dict_code: str = Field(alias="dict")
    #: Cologne record id. Duplicates `csl.lnum` deliberately: `csl` is the
    #: profile's provenance block, and a kosha client should not have to reach
    #: into another namespace for the id every kosha route keys on.
    L: str
    headword: str
    scan_url: str | None = None
    sense_ids: list[str] = Field(default_factory=list)
    #: Sanitized entry HTML (`kosha.api.sanitize`). Never the raw markup.
    rendered_html: str = ""
    evidence: dict[str, Any] | None = None
    heritage: HeritageWitness | None = None
    cite: CiteObject | None = None
    #: Present only when the caller passed `raw=1`; the unmodified Cologne body.
    raw: str | None = None


class SaltEntry(BaseModel):
    """One dictionary entry in Salt-profile shape (§8).

    **`id` is dictionary-scoped, not globally unique.** The profile addresses
    entries under `/dicts/{dict}/restful/ids`, so `lemma-agni` means "agni in
    *this* dictionary" — and MW, PWG and Apte each mint exactly that string for
    their own agni. C-SALT never has to notice, because a C-SALT response is
    always one dictionary's. kosha's `/api/v1/lemma` merges three, so a client
    keying a lemma card by `id` alone silently drops entries; the key is
    `(kosha.dict, id)`. Pinned by `test_salt_face_entry_equals_the_api_entry`.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    headword_slp1: str
    sense: list[str] = Field(default_factory=list)
    re_headwords_slp1: list[str] = Field(default_factory=list)
    created: str | None = None
    #: TEI-P5 body. `None` until TEI conversion ships (profile §8.1); it MUST
    #: NOT be filled with CSL display-XML — that is `csl.xmlCsl`.
    xml: str | None = None
    csl: CslBlock
    kosha: KoshaBlock


class Envelope(BaseModel):
    """The kosha `/api/v1` envelope: what was asked, against which build.

    Kept unchanged across the W0C migration — only `results` changed shape.
    `data_version` is what makes a response citable: every sense id in it is
    pinned to that build.
    """

    model_config = ConfigDict(extra="forbid")

    data_version: str
    query: dict[str, Any]
    results: list[Any]


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    suggestions: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """The documented top-level error object (W0C item 5).

    FastAPI's default is `{"detail": …}`, and kosha's `error()` helper used to
    nest the real object one level *inside* that, so every client had to reach
    through `detail.error.code`. The contract is a top-level `error` key and
    nothing else; `kosha.api.errors` installs the handlers that guarantee it
    for validation failures and unhandled exceptions too, not just for the
    errors raised deliberately.
    """

    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail


class SaltFaceError(BaseModel):
    """Salt profile §3.2 error form — a bare string, not the object above.

    The `/dicts/*` faces are wire-compatible with C-SALT, and C-SALT answers a
    bad parameter with `{"error": "Missing or invalid parameter: 'field'"}`.
    Normalizing those to kosha's richer object would break the compatibility
    the faces exist to provide, so the two error shapes coexist by design:
    structured under `/api/v1`, C-SALT-shaped under `/dicts/*`.
    """

    model_config = ConfigDict(extra="forbid")

    error: str


#: Search modes the Salt profile §4 defines. Modes kosha has not indexed must
#: return an explicit 400 — never a silently empty result set.
SaltQueryType = Literal[
    "term", "prefix", "wildcard", "regexp", "fuzzy", "match", "match_phrase"
]

#: The subset kosha implements today. The rest 400 with `unsupported_query_type`.
IMPLEMENTED_QUERY_TYPES: frozenset[str] = frozenset({"term", "prefix"})

#: Fields the profile §3.1 allows for `field=`.
SaltField = Literal[
    "id", "headword_slp1", "sense", "re_headwords_slp1", "created", "xml"
]

IMPLEMENTED_FIELDS: frozenset[str] = frozenset({"headword_slp1"})
