# dict-corpus-concordance — golden-sample verification record

_Created: 10-07-2026 · Last updated: 10-07-2026_

Stratified spot-check of the B1 concordance (H380 exit check). **Sample: 14 links, seed
`20260710`**, drawn 4 xref / 4 exact / 3 floor from the asserted dataset plus 3 from the
relaxed candidates. Two verification layers per row: **mechanical** (scripted against the
canonical `dcs-full-sqlite`: lemma-string identity, `evidence_count` recount, citable
`dcs:<sent_id>` resolution to a real sentence) and **semantic adjudication** (is the
dictionary headword and the DCS lemma the same lexeme?) — mechanical checks by script,
adjudication by Fable 5 (`claude-fable-5`), 10-07-2026.

| anchor (SLP1) | DCS lemma | tier | mech | adjudication |
|---|---|---|---|---|
| tArkzyaSEla | tārkṣyaśaila | xref | PASS 15 tok, dcs:22633 | ✅ same lexeme (mountain name) |
| upaDAv | upadhāv | xref | PASS 270, dcs:175773 | ✅ same (upa-√dhāv) |
| vyaNga | vyaṅga | xref | PASS 51, dcs:133302 | ✅ same |
| anehas | anehas | xref | PASS 8, dcs:24624 | ✅ same |
| nyaNkuBUruha | nyaṅkubhūruha | exact | PASS 1, dcs:505997 | ✅ byte-identical |
| dvArakA | dvārakā | exact | PASS 193, dcs:157444 | ✅ byte-identical |
| kAleya | kāleya | exact | PASS 36, dcs:565754 | ✅ byte-identical |
| asatI | asatī | exact | PASS 15, dcs:118052 | ✅ byte-identical |
| ameDAH | amedhā | floor | PASS 1, dcs:59002 | ✅ same lexeme — final-visarga strip only |
| UM | ūṅ | floor | PASS 2, dcs:552872 | ✅ defensible — homorganic-nasal fold of the same particle |
| madrakAH | madrakā | floor | PASS 1, dcs:260603 | ✅ same ethnonym (pluralia-tantum headword) |
| ram | rāṃ | relaxed | PASS 3, dcs:541012 | ❌ **conflates a/ā** — √ram vs the syllable rāṃ |
| vikarzaRa | vikarśana | relaxed | PASS 1, dcs:325538 | ❌ **conflates ṣ/ś** — 'dragging' vs 'emaciating' |
| aMSaka | aṃsaka | relaxed | PASS 3, dcs:476910 | ❌ **conflates ś/s** — 'share' vs 'shoulder' |

**Verdict.** Mechanical layer 14/14. Semantic layer: asserted tiers (xref/exact/floor)
**11/11 correct**; relaxed tier **0/3 correct** — `norm()` folds vowel length and the
three sibilants, which are exactly the axes of Sanskrit lexical minimal pairs. Acted on:
the relaxed tier (2,171 links) and the fuzzy tier (0) are **quarantined** to
[`dict_corpus_relaxed_candidates.tsv`](https://github.com/gasyoun/kosha/blob/main/data/concordance/dict_corpus_relaxed_candidates.tsv)
as a human-review queue and removed from the asserted dataset, the viewer, and the
manifest counts. The concordance asserts only what the sample could not fault.

_Dr. Mārcis Gasūns_
