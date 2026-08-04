# Sandhi rule-induction — methods deep manual

_Created: 01-08-2026 · Last updated: 01-08-2026_

**What this is.** Operator/scholar methods manual for the kosha **sandhi programme**: how rules are induced, scored, which splitter to use, failure taxonomy, and portability contracts.  

**What this is not.** The programme hub / “what exists” page remains [SANDHI_PROGRAMME.md](https://github.com/gasyoun/kosha/blob/main/SANDHI_PROGRAMME.md). Pedagogy surfaces and curriculum TSVs are covered there; this doc is the **methods** layer the hub deliberately does not expand.

**Handoff:** [H2069](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2069-Grok_kosha_sandhi-methods-deep-manual_01.08.26.md) · Grok 4.5 (`grok-4.5`).  
**Census residual:** DEEP_MANUAL_GAP_CENSUS row 14 🟡.

---

## 1. Problem statement

DCS CoNLL-U gives every token:

- **FORM** — sandhied surface  
- **`Unsandhied=`** (MISC) — pre-sandhi form  

It does **not** give the sandhi **rule**. The junction-rule inducer derives `X Y → Z` notation automatically so the same schema as the hand Gītā table (`data/gita/gita_sandhi.tsv`) generalises to any DCS text.

**Exit metric (programme):** ≥90 % of Gītā hand rules **by frequency mass** covered by method A. Measured: **96.3 %** frequency-mass coverage ([score_gita_gold.py](https://github.com/gasyoun/kosha/blob/main/scripts/score_gita_gold.py), H897).

**Residual mass:** ~**3.7 %** of Gītā gold frequency mass not recovered as exact rule strings — this is the “miss taxonomy” agents must not re-derive from scratch.

---

## 2. Method A / B / C — decision table

| Method | Input | Split source | Use when | F1 / role |
|---|---|---|---|---|
| **A** | DCS CoNLL-U | Gold `Unsandhied=` + FORM | Any DCS text; rule tables; curriculum | Ceiling for induction; **96.3 %** Gītā mass |
| **B** | Plain sandhied text | vidyut-cheda (offline FST) | Offline-only experiments | F1 ~0.22–0.28 vs DCS gold — **not** GRETIL production |
| **C** | Plain sandhied text | DharmaMitra neural (`--allow-network`) | **GRETIL / non-DCS** (Phase 3) | F1 ~0.70–0.80; precision ~0.90–0.97 |

**Standing verdict:** GRETIL path = **method C**. Bake-off driver: [`scripts/compare_sandhi_methods.py`](https://github.com/gasyoun/kosha/blob/main/scripts/compare_sandhi_methods.py) (`--methods ABC --allow-network`).

Runtime skill twins (org skills): `/sandhi-split` (prefer C where available), `/sandhi-scaffold`, `/sandhi-gold-audit`, `/sandhi-council` for ambiguous junctions.

---

## 3. Method A induction mechanics

Canonical script: [`scripts/dcs_sandhi_induce.py`](https://github.com/gasyoun/kosha/blob/main/scripts/dcs_sandhi_induce.py).

### 3.1 Two modes (H888)

| Mode | What | Why needed |
|---|---|---|
| **1 — EDGE** | Visarga / anusvāra / consonant sandhi between adjacent **syntactic** words | FORM ≠ Unsandhied at facing edges |
| **2 — VOWEL COALESCENCE** | Inside CoNLL-U **multi-word tokens** (MWT) | DCS records coalesced surface on MWT range; component FORM stays un-coalesced — mode 1 never sees the merge |

Phase 0 bug: counting MWT range lines as tokens — fixed. Phase 1.1: MWT right-edge visarga.

### 3.2 Phoneme helpers

IAST phonemes: aspirates `kh gh ch …` count as one unit (`first_phoneme` / `last_phoneme`). Rule notation reuses Gītā `categorise()` so categories stay schema-compatible.

### 3.3 Output schema (per text)

`data/sandhi/<slug>_sandhi.tsv` columns: `rule · category · count · pct · examples` (same as `gita_sandhi.tsv`).

```text
python scripts/dcs_sandhi_induce.py --text "Aṣṭāvakragīta"
python scripts/dcs_sandhi_induce.py --text Aṣṭāvakragīta --debug
```

Default DCS root in script: `C:/Users/user/Documents/GitHub/dcs-conllu/files` (override if layout differs).

---

## 4. Scoring & the 3.7 % miss taxonomy

### 4.1 How to re-measure

```text
python scripts/score_gita_gold.py
```

Requires DCS Gītā files as `*BhaGī*.conllu` under Mahābhārata (`MBh, 6, BhaGī 1–18` packaging — see VisualDCS / DCS consumer manual; Gītā is **not** absent).

Reports:

- rule-string coverage  
- **frequency-mass coverage** (roadmap exit metric)  
- P/R/F1 on rule strings  
- **top gold rules still missed**, ranked by frequency mass  

### 4.2 Miss classes agents should expect (~3.7 % mass)

When investigating residual gold rules not in induced set, classify before “fixing” the inducer:

| Class | Description | Typical response |
|---|---|---|
| **Notation / spacing** | Same surface sandhi, different string form (`m p→` vs `m p →`) | Notation normalise (H897 class); do not double-count |
| **MWT boundary** | Coalescence or visarga on MWT edge | Mode 2 / right-edge visarga paths |
| **Rare / low-count gold** | Hand table has rare rules under-attested in DCS packaging | Accept residual; do not lower mass metric |
| **Gold typo / non-IAST** | Hand table glyph errors | `/sandhi-gold-audit` |
| **Scope packaging** | Gītā inside MBh path missing files | Fix DCS path, not inducer |

**Do not** treat “61 % on a small pilot text” as programme failure — Aṣṭāvakragīta under-attests rare rules; **only Gītā mass score is exit**.

---

## 5. Corpus sweep & merge

| Script | Role |
|---|---|
| `build_corpus_sandhi.py` | Per-text tables + merged `data/sandhi/corpus_sandhi.tsv` |
| `build_sandhi_curriculum.py` | Graded syllabus + page |
| `build_sandhi_reference.py` | Per-class reference |
| `build_sandhi_drills.py` | Drill items |
| `build_gita_sandhi.py` | Original hand Gītā seed (H872) |

Rebuild (needs local `dcs-conllu`):

```text
python scripts/build_corpus_sandhi.py
python scripts/build_sandhi_curriculum.py
python scripts/build_sandhi_reference.py
python scripts/score_gita_gold.py
```

**Scale (programme hub):** 41 texts · ~708k junctions · ~13,012 distinct rules; learn 23→50 %, 79→80 %, 132→90 % mass.

---

## 6. Portability contract (reuse outside Gītā)

1. **Any DCS text with Unsandhied** → method A inducer → same TSV schema.  
2. **No Unsandhied** → cannot induce gold rules; use method C to **split**, then optionally induce from proposed splits (treat as lower tier).  
3. **Curriculum weights** → `data/sandhi/difficulty_weights.json` (MG ruling 14-07-2026); do not hardcode lesson cutoffs in a second place.  
4. **Manifest registration** → `data/manifest/datasets.json` rows: `gita-sandhi`, `corpus-sandhi`, `sandhi-curriculum`.  
5. **License:** derived tables public/MIT; DCS source CC BY-SA 4.0 (Hellwig) — attribution in hub.  
6. **Reader hover** lives in SanskritGrammar (H917); drills/curriculum in kosha — do not rebuild hover in kosha.

---

## 7. Failure modes

| Failure | Cause | Fix |
|---|---|---|
| Empty induce | Wrong DCS path / missing Unsandhied | Check `DEFAULT_DCS` and CoNLL-U MISC |
| Low coverage on pilot text | Rare rules absent | Score on Gītā, not pilot |
| Mode 1 only misses coalescence | MWT not processed | Ensure mode 2 path |
| Network splitter fails | Method C blocked | Offline B for debug only; do not ship B as production |
| Double pedagogy surface | Sibling handoffs H902/H917/H918 | Check FEATURES_INDEX / SANDHI_PROGRAMME before building |

---

## 8. Related skills & manuals

| Resource | Role |
|---|---|
| [SANDHI_PROGRAMME.md](https://github.com/gasyoun/kosha/blob/main/SANDHI_PROGRAMME.md) | Hub / surfaces |
| [PIPELINE_OPERATOR_RUNBOOK.md](https://github.com/gasyoun/kosha/blob/main/docs/PIPELINE_OPERATOR_RUNBOOK.md) | Broader kosha ops |
| [DCS_SQLITE_CONLLU_CONSUMER_DEEP_MANUAL.md](https://github.com/gasyoun/VisualDCS/blob/main/docs/DCS_SQLITE_CONLLU_CONSUMER_DEEP_MANUAL.md) | DCS packaging (incl. Gītā locus) |
| `/sandhi-scaffold` · `/sandhi-split` · `/sandhi-gold-audit` · `/sandhi-annotate` | Session skills |

---

## 9. LAST_VERIFIED

01-08-2026 · Grok 4.5 (`grok-4.5`) · H2069 · grounded in `SANDHI_PROGRAMME.md`, `dcs_sandhi_induce.py`, `score_gita_gold.py` headers and hub metrics. Live re-score of 96.3 % requires local `dcs-conllu` Gītā files — if absent, treat the hub number as last published measurement, not re-run this session.

_Dr. Mārcis Gasūns_
