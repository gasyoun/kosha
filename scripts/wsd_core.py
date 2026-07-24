#!/usr/bin/env python
"""Shared helpers for kosha two-witness WSD (H1588 / sense-frequency Wave 3).

House rules:
  - length-preserving SLP1 via sanskrit-util when available
  - MW senses are read-only sidecars — never rewrite kosha/MW senses
  - WordSem held-out fold is deterministic (sentence_id hash)
"""
from __future__ import annotations

import csv
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
FREQ = os.path.join(REPO, "data", "frequency")
CACHE_DIR = os.path.join(FREQ, ".cache")
SCL_CACHE = os.path.join(CACHE_DIR, "scl_sense_labels.jsonl")
DEFAULT_DCS = os.path.normpath(
    os.path.join(REPO, "..", "VisualDCS", "src", "DCS-data-2026", "dcs_full.sqlite")
)
WN_MW_MAP = os.path.join(FREQ, "wn_to_mw_map.tsv")
SENSE_FREQ = os.path.join(FREQ, "sense_frequency.tsv")
GATE_THRESHOLD = 0.70
FOLD_MOD = 5  # 1/5 → test (~20%), 4/5 → train
MODEL_PROV = "Grok 4.5 (grok-4.5)"  # H1588 executor (Opus-lock override)

try:
    sys.path.insert(0, os.path.join(REPO, "..", "sanskrit-util", "py"))
    from sanskrit_util import to_slp1 as _su_to_slp1  # noqa: E402

    _HAVE_SU = True
except Exception:
    _HAVE_SU = False
from indic_transliteration import sanscript  # noqa: E402


def iast_to_slp1(iast: str) -> str:
    s = (iast or "").strip()
    if not s:
        return ""
    if _HAVE_SU:
        try:
            return _su_to_slp1(s)
        except Exception:
            pass
    return sanscript.transliterate(s, sanscript.IAST, sanscript.SLP1)


def load_tsv(path: str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def fold_of_sentence(sentence_id) -> str:
    """Deterministic train/test fold. test when hash % FOLD_MOD == 0 (~20%)."""
    return "test" if (hash(str(sentence_id)) % FOLD_MOD) == 0 else "train"


def primary_synset(m_wordsem: str) -> str:
    """DCS may store multi-label 'id1,id2'; take the first non-empty token."""
    if not m_wordsem:
        return ""
    return str(m_wordsem).split(",")[0].strip()


def load_wn_mw_resolved(path: str = WN_MW_MAP) -> dict[tuple[str, str], dict]:
    """(synset_id, lemma_slp1) → map row for exact|overlap matches only.

    sense_id form matches build_sense_frequency_layer: f\"{lemma}#{mw_sense_ord}\".
    """
    out: dict[tuple[str, str], dict] = {}
    for r in load_tsv(path):
        mt = (r.get("match_type") or "").lower()
        if mt not in ("exact", "overlap"):
            continue
        ord_ = (r.get("mw_sense_ord") or "").strip()
        if not ord_ or ord_ == "0":
            continue
        syn = (r.get("synset_id") or "").strip()
        lemma = (r.get("lemma_slp1") or "").strip()
        if not syn or not lemma:
            continue
        row = dict(r)
        row["sense_id"] = f"{lemma}#{ord_}"
        out[(syn, lemma)] = row
    return out


def load_mw_mfs_from_sense_freq(path: str = SENSE_FREQ) -> dict[str, dict]:
    """lemma_slp1 → dominant MW sense row from attested sense_frequency (mw layer)."""
    best: dict[str, dict] = {}
    for r in load_tsv(path):
        if r.get("layer") != "mw":
            continue
        if (r.get("provenance") or "attested") != "attested":
            continue
        lemma = r["lemma_slp1"]
        try:
            cnt = int(r["count_all"])
        except (ValueError, KeyError):
            continue
        cur = best.get(lemma)
        if cur is None or cnt > cur["_cnt"]:
            best[lemma] = {
                "_cnt": cnt,
                "sense_id": r["sense_id"],
                "sense_gloss": r.get("sense_gloss") or "",
                "lemma_share": r.get("lemma_share") or "",
                "count_all": cnt,
            }
    for v in best.values():
        v.pop("_cnt", None)
    return best


def load_lemma_map(dcs_path: str = DEFAULT_DCS) -> dict[int, str]:
    dcs = sqlite3.connect(dcs_path)
    try:
        return {
            int(lid): iast_to_slp1(lem)
            for lid, lem in dcs.execute("SELECT lemma_id, lemma FROM lemma")
        }
    finally:
        dcs.close()


def ensure_cache_dir() -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return CACHE_DIR
