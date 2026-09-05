# H4038 — Hitopadeśa concordance surface with era badges: rendered proof (04-09-2026)

_Created: 04-09-2026 · Last updated: 05-09-2026_

Executor: OxAlpha (opencode / zai-coding-plan/glm-5.3-flash). The H4034 pilot data
(`data/concordance/text_hitopadesa/`, 7,857 (surface, lemma) forms / 25,040
occurrences / DCS text_id 189) surfaced onto the kosha reader surface, extending —
never forking — the H4026 badge machinery.

## What shipped

1. **The concordance page is now rendered through the H4026 machinery** (prior-art
   fence: reuse, never a second render system):
   - page-level work badge = `app/dating_hydrate.py::badge_html` output, verbatim —
     `data-era='early-medieval'`, tooltip caveat «first attestation in the cited
     corpus, not the origin of the meaning (первое засвидетельствование в цитируемом
     корпусе) · via dharmamitra»;
   - RU+EN caveat + five-bucket legend = `app/word_page.py::_dating_caveat_block()`
     byte-for-byte (same wording as every H4026-badged word page), rendered under the
     H4026 contract (only when the work carries a bucket);
   - era CSS ported from `app/word_page.py` PAGE_CSS (`data-era`-keyed, all 5 buckets).
2. **Wired into the EXISTING Hitopadeśa pack page** (H1448 surface,
   [reading/index.html](../../../reading/index.html)): selecting `hitopadesa-0` now
   shows a «Word concordance →» affordance linking to the page; the page links back
   to `reading/index.html#hitopadesa-0`. Additive conditional — every other pack's
   view byte-unchanged.
3. **Gates** (`scripts/build_text_concordance_hitopadesa.py --check`, DCS-free, also
   run in-build and as `tests/test_text_concordance_hitopadesa.py`):
   - **parity** — concordance.tsv == viewer payload (byte re-derivation) == page
     stats line == MANIFEST stats: 7,857 rows / 25,040 occurrences / 13.0% sense-linked;
   - **order-invariance** — every row's occurrence refs non-decreasing in document
     order (chapter, sentence, subcounter);
   - **honest absence** — no work bucket ⇒ no badge, no caveat, gate-fails if rendered.
4. **Additive fence held**: rebuild over the H4034 committed fold changed ONLY
   `index.html` + this gate/machinery code — `concordance.tsv` and
   `text_hitopadesa.js` byte-identical (sha256-verified pre/post). The pass also
   FIXED a latent H4034 drift the new gate caught: the committed script's payload
   key order no longer reproduced the committed js (`n_refs` before/after `refs`);
   the script now regenerates both committed artifacts byte-identically again.

## Proof files

| file | what to look at |
|---|---|
| `badges-surface.hitopadesa.html` | live-shaped rendered proof: the `api` row — 464 occurrences in document order, 13 PWG sense-id chips, card link `../w/api.html` — under the page-level **early-medieval** badge; and the `avalokya` row (DCS lemma `avalokay`, causative `-ay` stem, no H380 join) rendered `—` — honest absence, nothing fabricated. RU+EN caveat + bucket legend at the bottom, verbatim H4026 block. |
| [../index.html](https://github.com/gasyoun/kosha/blob/main/data/concordance/text_hitopadesa/index.html) | the built concordance page itself (badge in the h1, caveat disclosure under the table). |
| [../../../reading/index.html](../../../reading/index.html) | the pack page hook — pick «Hitopadeśa», the «Word concordance» line appears; pick any other pack, it stays hidden. |

## Reproduce

```bash
python scripts/build_text_concordance_hitopadesa.py --check   # gates: parity OK (7857 rows, 25040 occurrences), order-invariance OK
python -m pytest tests/test_text_concordance_hitopadesa.py -q
python -m http.server 8731  # then: /reading/index.html and /data/concordance/text_hitopadesa/index.html — both 200
```

Live-serve smoke 04-09-2026: all four paths (reader, concordance page, js shard,
evidence proof) HTTP 200 at the repo-relative layout the pages assume.

## Scope note

Production deploy is out of scope per [KOSHA_DEPLOYMENT.md](../../../KOSHA_DEPLOYMENT.md)
(no agent holds deploy credentials; `deploy_guhya.py --upload` is agent-forbidden) —
the page renders live in the repo tree; the samskrtam.ru push stays with the human.

_Dr. Mārcis Gasūns_
