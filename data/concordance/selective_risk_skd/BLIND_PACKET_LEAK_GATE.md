# H5296 — Blind-packet leak gate receipts (selective_risk_skd deck)

_Created: 24-09-2026 · Last updated: 24-09-2026_

Gate: [scripts/check_blind_packet_leak.py](https://github.com/gasyoun/kosha/blob/main/scripts/check_blind_packet_leak.py) ·
Tests: [tests/test_blind_packet_leak_gate.py](https://github.com/gasyoun/kosha/blob/main/tests/test_blind_packet_leak_gate.py) (11 passed)

## Deck-builder census and selection (post-01-09-2026, excluding H5070)

| Deck family | Builder | Status | Verdict |
|---|---|---|---|
| `selective_risk/` (H5070) | `sample_sense_alignment_selective_risk.py` | frozen 22-09 (#631), canary-leak fix already landed there | EXCLUDED per handoff |
| `selective_risk_skd/` (H5252/ŚKDR) | same sampler, `--stratify-channel` mode (#633); gated by `measure_skd_root_nominal_gate.py` (#637) — a content gate, NOT a blind-packet leak gate | active, latest commit on main | SELECTED |

No blind-packet metadata-leak check existed for the SKD family — the gap this handoff fills.

## GREEN — rendered reviewer packet is blind

```
$ python3 scripts/check_blind_packet_leak.py \
    --deck data/concordance/selective_risk_skd/review_deck.tsv \
    --key  data/concordance/selective_risk_skd/canary_key.json
packet(deck) sha256  bde688df44ccd5aa3b003a48af179a5fcc74b6fe3607ce4cea7353e1965b7132
hidden key  sha256  023a53e533a5a82a440b0f2e501cdf9109b5fc2a47ab5a1910df5dfdce1f6270
GREEN  review_deck.tsv: control C025 not identifiable from the rendered packet (61 cards)
```

Reuse proof, frozen H5070 deck read-only (no file under `selective_risk/` modified):
`GREEN  review_deck.tsv: control C041 not identifiable from the rendered packet (61 cards)`,
deck sha256 `4384f766691d5fa15e57b24b6dab56c102a54ae09d66b9b19d5ede300bbb7052`.

## RED — five planted mutations, each caught, packet restored after each

| Mutation | Planted tell | Caught by | Mutated sha256 |
|---|---|---|---|
| `unique_metadata` | shape `9-9-9-9-9-9` + witnesses `zzz` on the control | `rendered_field_tell` | `2de0bcc6efccb741…` |
| `ordering` | control moved to last card | `rendered_position_tell` | `2fbded7a3c40ce55…` |
| `missing_gloss` | control's MW gloss blanked | `rendered_missingness_tell` | `7e35af44ee69ebc9…` |
| `formatting` | control card id zero-pad broken (`C025`→`C25`) | `rendered_format_tell` | `ce5cd063ec0a55a8…` |
| `legacy_hidden_metadata` | the literal PR #631 arithmetic (`stratum_eligible=0`, `population_share=0.000000`) | `field_tell,joint_tell` (strict TSV layer) | `d3f6eb4eb60234a4…` |

All mutations ran on temp copies; the committed packet was restored byte-identically
(sha256 above unchanged across the whole run). Receipts are layer-attributed: surface
mutations are caught by the rendered-packet layer, the #631 specimen by the strict
TSV layer — never by a pre-existing residual.

## STRICT — frozen-deck residual, disclosed not hidden

```
STRICT deck-TSV findings (2) — packet-of-record residuals, each needs a documented
limitation or a builder fix:
  field_tell  score  control's score='0.930' is shared by no real row
  joint_tell  control's full coded-column tuple is unique in the packet
```

Limitation: the frozen, already-adjudicated SKD deck carries a TSV-level score tell
(`0.930` unique; real score domain tops out at `1.000` — but appears once). The reviewer
packet is the rendered card text, which by renderer design never prints score/stratum/
method — so the reviewer-facing surface is blind (GREEN above). The frozen deck stays
byte-pinned by `test_skd_deck_reproduces_byte_for_byte` and its adjudication lineage
(population sha256 `9b589b2b…`); re-dressing it would falsify published rates. New decks
should pass `--strict-deck-metadata` as a build check; the gate exists for exactly that.

## Fresh isolated blind re-test (24-09-2026)

Isolation, machine-attested: the adjudicator session's context read list contains
exactly `/tmp/H5296_blind/cards.txt` (249 lines) and `/tmp/H5296_blind/rubric.txt`
(32 lines) — the rendered packet (`render_selective_risk_deck.py --width 400`) and the
blind rubric only. No key, no control disclosure anywhere in its context.

- Verdicts: [adjudication_h5296_blind3.tsv](https://github.com/gasyoun/kosha/blob/main/data/concordance/selective_risk_skd/adjudication_h5296_blind3.tsv) — 61/61 cards
- Bound packet hash: `bde688df44ccd5aa3b003a48af179a5fcc74b6fe3607ce4cea7353e1965b7132`
- Control result: C025 → `different`, exactly the hidden key's `expected_verdict` — the
  control behaved as designed and was never flagged as odd (its note treats it as an
  ordinary card). Verdict distribution: 41 different / 17 same / 3 unsure.
- Agreement vs H5252 blind adjudicator 2: **59/61 = 96.7%** (the H5252 pair itself:
  95%). The control's agreement is at the deck's own agreement level — a control the
  reviewer could spot would show a deviating pattern; this one does not.

## Checks

- `python3 -m pytest tests/test_blind_packet_leak_gate.py -q -p no:cacheprovider --noconftest` → **11 passed**
- Gate exit codes: 0 clean, 2 leak, 1 gate defect (mutation uncaught).

_Гасунс_
