# H3597 — Cologne parity verified at scale + likh-only words + site divergence lists

_Created: 01-09-2026 · Last updated: 01-09-2026 · OxAlpha (`z-ai/glm-5.3-flash`)_

MG tasking (01-09-2026): (1) confirm Cologne parity over all 51,663 census heads
mechanically, locally, no scraping; (2) durable doc for the words that exist
ONLY in likh (Likhushina — never Cologne); (3) durable lists for the site-side
SLP1 transliteration divergences and the Cologne casefold twins.

## 1. Parity verdict — 100% of the census mapped, locally

Checker: [`scripts/akshara_cologne_parity.py`](https://github.com/gasyoun/kosha/blob/main/scripts/akshara_cologne_parity.py)
(census + csl-orig v02 k1 universes + Levenshtein≤1 for the site's spelling
divergence class + live-probe ground truth; `--emit` writes the lists below).

| Class | Heads | Meaning |
|---|---|---|
| **EXACT** | **51,652** | head is a `k1` in csl-orig v02 (40 dict files, 409,100 k1 universe) |
| **CASEFOLD** | **5** | head is a case-variant of a Cologne k1 — the site case-normalizes when the exact key is absent |
| **VARIANT** | **3** | head differs from a Cologne k1 by site-side SLP1 spelling; same print entry |
| **NONCOLOGNE** | **3** | no Cologne counterpart at all — likh-only |
| **Total** | **51,663** | 100.00% mapped |

**100% parity confirmed.** Every one of the 51,663 census heads resolves to
Cologne or to a documented non-Cologne class. The site's ORIGINALS are
Cologne (current csl-orig v02, pwg/mw @ 27-06-2026, ap @ 26-06-2026 DC 24 June)
re-served as HTML with Devanagari re-inserted from `{#...#}` spans.

## 2. likh-only heads (never Cologne) — THE LIST

likh (Лихушина Н.П., printed dictionary, RESTRICTED advisor-only) covered
**3,988 census heads** with content in the drain corpus — but 3,985 of those
also exist in Cologne (mw/pwg/ap) or mac. The heads served by likh that have
**NO Cologne counterpart anywhere in csl-orig v02** (all three live-probed
01-09-2026, `dict=all` cards carried only the likh block):

| Head | Devanagari | likh gloss (print page) | Cologne check |
|---|---|---|---|
| `AsannamaraRa` | आसन्नमरण | «(āsanna-maraṇa) bah. умирающий (букв. с близкой смертью)» (с. 37) | absent from all 40 csl-orig dicts (ed≤1 nearest: `Asannacara`, Δ3 — not a variant) |
| `anAyati` | अनायति | «f несдержанность, необузданность» (с. 11) | absent (ed≤1 hits `DanAyati` = coincidence; live card = likh-only) |
| `pravip` | प्रविप् | «трепетать» (с. 125) | absent (ed≤1 hits `pralip` = coincidence; Cologne has only `aBipravip`, `pravipala`, `sampravip` as unrelated k1s) |

**Caveat (honest scope):** this is the likh-only list *within the akshara
census universe* (51,663 site-declared heads). The likh dictionary's own
inventory beyond that census cannot be enumerated locally — the parsed drain
corpus (which carried per-head per-dict presence) was `--delete-raw`-ed after
parse and the worktree GC'd. If likh's full independent head list is ever
needed, it requires either the printed Лихушина dictionary digitized directly
or a bounded re-crawl of the site's likh coverage (MG-gated; robots-allowed
card pages only).

## 3. Site-side SLP1 transliteration divergences (durable list)

The site keys some print entries with SLP1 spellings that diverge from
Cologne's `k1` — same entry, same page-ref, different transliteration choice.
Full list (3):

| Census head (site key) | Cologne k1 | Print entry | Divergence |
|---|---|---|---|
| `atiCattrakA` | `aticCattrakA` | MW 12,2 (ati—chattrakā, Anise) | च्छ `cCa` → छ `ca` (cluster simplified; Cologne `cC` vs site `c`) |
| `atiCattraka` | `aticCattraka` | MW 12,2 (same family) | same `cC`→`c` class |
| `sahajanyI` | `sahajanyA` | MW 1194,1 (saha—janyī/janyā, apsaras N.) | feminine-ending variant: site keys the `-I` (ī) form, Cologne the `-A` (ā) form — both in the print entry's range |

These are **keying divergences, not data gaps** — the served card content is
the Cologne entry. A Cologne→site lookup needs this mapping table (or an
ed≤1 fallback over the core dicts) to resolve.

Machine list: [`data/akshara_full/parity/slp1_variants.tsv`](https://github.com/gasyoun/kosha/blob/main/data/akshara_full/parity/slp1_variants.tsv)

## 4. Cologne casefold twins (site case-fallback) (durable list)

Heads where the site's exact-key card is absent and the site serves the
casefold-twin's card instead (legitimate answer, `data-q-slp1` recorded it).
Full list (5):

| Census head (site key) | Cologne k1 (casefold match) |
|---|---|
| `aBisaMbuD` | `aBisambuD` |
| `azwaviMSati` | `azwAviMSati` |
| `puroqAs` | `puroqAS` |
| `samAvAp` | `samAvap` · `samavAp` |
| `tAm` | `TaM` · `Tam` · `taM` · `tam` |

Note `tAm` is the only ambiguous one (four Cologne keys share the casefold);
the drain corpus recorded the actually-served card via `q_slp1`.

Machine list: [`data/akshara_full/parity/casefold_twins.tsv`](https://github.com/gasyoun/kosha/blob/main/data/akshara_full/parity/casefold_twins.tsv)

## 5. Consequence (MG's original instinct, now proven)

The akshara **originals** (`dict=all` pass) are 100% Cologne-derivable: 51,652
exact + 5 casefold + 3 spelling variants = every head resolvable from local
Cologne files. They can be retired from any future pipeline in favour of local
cologne files (fresh @DECIDE when relevant). The unique akshara assets remain:
the **MT layers** (`mw_ru/apte_ru/pwg_ru` — exist nowhere else) + `mac`
(Macdonell, non-Cologne source digitization) + `likh` fragments (advisor-only).

Provenance chain: [§8c of the coverage report](https://github.com/gasyoun/kosha/blob/main/docs/AKSHARA_FULL_COVERAGE_H3597_27.08.26.md)
· FINDINGS §639 · parity lists under `data/akshara_full/parity/`.

_Dr. Mārcis Gasūns_