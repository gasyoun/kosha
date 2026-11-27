# 2026-11-27 — manifest: two planned-wording consumer rows relabeled (H8162)

Per ESTATE_CONTRADICTIONS_TRIAGE_25-09-2026 (`manifest:planned-consumer-in-live-list:*`):
`cyrillic-proper-noun-slp1` consumer "SamudraManthanam name glossaries" relabeled
to live wording ("live since 18-09-2026, PR #358 merged" — the edge is landed, the
queued->live bookkeeping wording left the live consumers array);
`amarakosa-mw-pwg-sense-crosswalk` candidate-shortlist consumer "sense-alignment
follow-ups (needs gold + adjudication per H1670)" moved out of `consumers` into
`consumer_candidates` (repo: SanskritLexicography, confidence: low) — it records no
landed edge. No dataset bytes changed; sizes/sha256 unaffected. Acceptance: JSON
parses, grep over both consumers arrays shows no planned/candidate/queued/shortlist
wording. NEXT_UP row (owner=drain, trivial).
