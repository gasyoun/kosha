# License — data releases

The data this project builds and redistributes is **derived from upstream
sources whose licenses bind our releases**. The code license
([LICENSE.md](https://github.com/gasyoun/kosha/blob/main/LICENSE.md), CC BY-NC 4.0)
does **not** apply to data; each dataset inherits its upstream terms:

| Component of a kosha data release | Upstream | License we inherit |
|---|---|---|
| Dictionary entries (MW, PWG, AP90 …) and anything derived from them (sense spans, rendered HTML, dumps) | [csl-orig](https://github.com/sanskrit-lexicon/csl-orig) / Cologne CDSL | **CC BY-SA 4.0** (verified in csl-orig/LICENSE, 02-07-2026). ShareAlike: our derived dictionary data MUST be redistributed under CC BY-SA 4.0 — a non-commercial restriction may not be added to it |
| Union headword spine | SanskritLexicography (own work over CDSL headwords) | CC BY-SA 4.0 (derivative of CDSL headword lists) |
| Corpus frequency / attestation data | [DCS](https://github.com/OliverHellwig/sanskrit) (O. Hellwig) | CC BY 3.0 (per dcs website impressum); attribution required |
| Form→lemma glossary | own derivation over DCS + vidyut | CC BY-SA 4.0 for DCS-derived rows; vidyut data per its own terms (MIT-licensed project) |
| Scans | Cologne servers | linked, not redistributed |
| Bloomfield RV *pratīka* cross-reference (`bloomfield_pratika` column, `bloomfield_rv_citations.tsv`) | Marco Franceschini's digital edition of Bloomfield's *A Vedic Concordance* (Harvard Oriental Series 9, 1906) | **Public tier by direct written permission** — non-exclusive, worldwide, perpetual grant from Marco Franceschini (University of Bologna), covering all current and future kosha versions, no separate payment/approval required. Full grant text: [data/manifest/rights/franceschini_hos9_permission_2026-07-13.md](https://github.com/gasyoun/kosha/blob/main/data/manifest/rights/franceschini_hos9_permission_2026-07-13.md). Required citation (per the grantor's own request): "Digitization by Marco Franceschini (University of Bologna), of Maurice Bloomfield's *A Vedic Concordance* (Harvard Oriental Series 9, 1906). Used with permission." |

**Practical consequence:** the SQLite/database release assets are published
under **CC BY-SA 4.0** with attribution to the Cologne Digital Sanskrit
Dictionaries (Univ. of Cologne; Funderburk, Malten et al.), DCS (Hellwig), and
this project. Commercial *use of the data* cannot be forbidden by us — Cologne
chose BY-SA, not BY-NC — but the *service code* remains non-commercial per
LICENSE.md. The two licenses attach to different works.

Attribution block to ship with every data release:

> Gasuns Sanskrit Dictionary data release vX.Y.Z (CC BY-SA 4.0).
> Dictionary source: Cologne Digital Sanskrit Dictionaries (CC BY-SA 4.0),
> csl-orig commits per the `sources` table. Corpus statistics: Digital Corpus
> of Sanskrit, © Oliver Hellwig (CC BY 3.0). Compilation: Dr. Mārcis Gasūns.

_Created: 02-07-2026 · Last updated: 13-07-2026_

_Dr. Mārcis Gasūns_
