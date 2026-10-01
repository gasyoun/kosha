_Created: 04-09-2026 · Last updated: 05-09-2026_

# Hitopadesa text-concordance pilot — 10-form hand-verified spot check (H4034)

_Created: 04-09-2026_

Method: 10 distinct (surface, lemma) forms stratified across the frequency
spectrum (2 top, 2 mid, 2 rare, 1 hapax, 1 unlinked-residue, 1 sense-linked,
1 xref-linked). For each, the shipped row was verified against an INDEPENDENT
re-derivation — a direct per-form SQL recount against
`VisualDCS/src/DCS-data-2026/dcs_full.sqlite` (text_id 189) with its own
chapter-ordered query, plus the H1455 sense layer and the `card_token` twin —
not by re-running the builder. All ten PASS: counts equal, ordered occurrence
lists byte-identical, sense ids equal the per-sense layer for the joined
headword, hrefs equal the card-token encoding.

| # | form | lemma | pos | n_occ | refs vs independent DB recount | sense-join vs H1455 layer | card_token twin | sense ids | verdict |
|---|------|-------|-----|-------|-------------------------------|---------------------------|-----------------|-----------|---------|
| 1 | ca | ca | CONJ | 780 | count 780==780 ok — ordered list identical | True | True | 10·1a·1b·1c·1d·1e·1f·1g·2·3·4·5·6·7·8·9 | PASS |
| 2 | na | na | PART | 496 | count 496==496 ok — ordered list identical | True | True | — | PASS |
| 3 | deva | deva | NOUN | 16 | count 16==16 ok — ordered list identical | True | True | 1·2a·3b·3c·3d·3e·3f·4·5·6·7·8a·8b·8c·9 | PASS |
| 4 | dhanam | dhana | NOUN | 16 | count 16==16 ok — ordered list identical | True | True | — | PASS |
| 5 | nirjane | nirjana | ADJ | 2 | count 2==2 ok — ordered list identical | True | True | — | PASS |
| 6 | nirmalam | nirmala | ADJ | 3 | count 3==3 ok — ordered list identical | True | True | — | PASS |
| 7 | palāyiṣyase | palāy | VERB | 1 | count 1==1 ok — ordered list identical | True | True | — | PASS |
| 8 | kadācid | kadācid | ADV | 27 | count 27==27 ok — ordered list identical | True | True | — | PASS |
| 9 | abhavam | bhū | VERB | 1 | count 1==1 ok — ordered list identical | True | True | 10·11·1a·1b·1c·1d·1e·1f·1g·1h·1i·1l·2·3·4·5·6·7·8·9 | PASS |
| 10 | _ | vipad | NOUN | 2 | count 2==2 ok — ordered list identical | True | True | — | PASS |
Honest residue: the first spot-check run had 7 false FAILs from a bug in the
CHECKER (recount query lacked chapter ordering), not in the builder; fixed in
the checker and re-run to 10/10 before committing. Slot 10 was re-picked from
the duplicate (`ca` twice) to an xref-linked form (`vipad`) for link-method
coverage.

_Dr. Mārcis Gasūns_
