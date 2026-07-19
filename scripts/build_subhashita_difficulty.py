#!/usr/bin/env python
"""Indische Sprüche difficulty grading — pedagogy Wave RU, surface W-RU-b (H1279).

Scores all 7,537 Böhtlingk subhāṣitas (SanskritLexicography F33, public domain)
for reading difficulty, so the graded beginner reader can select its band from
evidence instead of vibes. This is the W2a difficulty scorer applied to a corpus
with NO gold token analysis — so, exactly like the reduced 3-axis Gītā ordering
already documented in data/difficulty/METHODS.md (H977), it runs a REDUCED,
renormalised variant of the shipped formula rather than fabricating missing
signal ("no fabricated signal" rule):

    difficulty_reduced = w_vocab·VOCAB + w_fusion·FUSION

  VOCAB   vocabulary rarity, same definition as W2a: each content lemma ->
          rank in data/frequency/lemma_frequency.tsv; load = log10(rank)/
          log10(maxrank); unseen lemma = 1.0. Lemmas come from vidyut-cheda
          (offline, deterministic — split-method B of the sandhi programme's
          A/B/C harness, compare_sandhi_methods.py). A whitespace chunk cheda
          cannot fully analyse counts as ONE unknown content word (load 1.0).
          Function lemmas (lemma_frequency grammar_all in {ind, pron} — the
          UD FUNCTION_UPOS analogue) are excluded from this axis only.
  FUSION  boundary fusion, the W2a SANDHI definition (tokens − whitespace
          chunks)/tokens — but WITHOUT gold morphology a splitter cannot tell
          a compound member from a sandhi fusion, so this one axis absorbs
          BOTH the sandhi and the compound weights (their renormalised sum),
          rather than double-counting one signal under two names.

  MORPH is dropped (needs the DCS upos|morph signatures; the sprueche have no
  UD analysis); weights renormalise per the H977 procedure:
  vocab 0.4/(0.4+0.2+0.15)=0.5333 · fusion (0.2+0.15)/0.75=0.4667.

  NOT COMPARABLE to the 4-axis pack table or the reduced Gītā table — different
  axis set again; this orders the 7,537 sayings AMONG THEMSELVES only.

Also emitted per saying (curation + pack inputs, not part of the score):
  pct_w1b    share of content-lemma occurrences inside the W1b vocab
             curriculum (data/frequency/vocab_curriculum.tsv) — the "prefer
             sayings whose lemmas sit inside the top-frequency bands" signal.
  metre      strict vṛtta via vidyut.chandas over the vendored meters.tsv,
             else the anuṣṭubh syllable heuristic, else unresolved — the same
             two-tier + null method as build_reading_pack_metre.py (W3a).

Avagraha: a chunk-initial IAST apostrophe marks an elided initial a-
("aṃśo 'pi" = aṃśo api); it is restored before segmentation so cheda sees the
underlying word, and stripped everywhere else (vidyut rejects it).

Determinism: pure reads of the pinned JSONL + two TSVs + the vendored vidyut
data; no network, no clock. Byte-stable on re-run.

Source (consumed in place, never copied into kosha — F33):
  ../SanskritLexicography/IndischeSprueche/data/indische_sprueche.jsonl

Usage:
  python scripts/build_subhashita_difficulty.py [--limit N]
"""
import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent if (ROOT.parent / "SanskritLexicography").exists() else ROOT.parent.parent
SPRUECHE = GH / "SanskritLexicography" / "IndischeSprueche" / "data" / "indische_sprueche.jsonl"
VIDYUT_DATA_ROOT = GH / "vidyut-data"
FREQ_TSV = ROOT / "data" / "frequency" / "lemma_frequency.tsv"
W1B_TSV = ROOT / "data" / "frequency" / "vocab_curriculum.tsv"
WEIGHTS_JSON = ROOT / "data" / "difficulty" / "difficulty_weights.json"
METERS_TSV = ROOT / "data" / "vidyut" / "chandas" / "meters.tsv"
OUT_TSV = ROOT / "data" / "subhashita" / "subhashita_difficulty.tsv"

# hard SLP1 alphabet filter — vidyut (cheda AND chandas) rejects any other byte
SLP1_CHARS = set("aAiIuUfFxXeEoOMHkKgGNcCjJYwWqQRtTdDnpPbBmyrlvSzshL")
FUNCTION_GRAMMAR = {"ind", "pron"}  # lemma_frequency grammar_all ≈ FUNCTION_UPOS


def load_weights():
    w = json.loads(WEIGHTS_JSON.read_text(encoding="utf-8"))["weights"]
    w_vocab = w["vocab"]
    w_fusion = w["sandhi"] + w["compound"]  # one fusion axis absorbs both
    s = w_vocab + w_fusion
    return w_vocab / s, w_fusion / s


def load_ranks():
    ranks, grammar = {}, {}
    with FREQ_TSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            ranks[row["lemma_slp1"]] = int(row["rank_all"])
            grammar[row["lemma_slp1"]] = row["grammar_all"]
    return ranks, grammar, max(ranks.values())


def load_w1b():
    with W1B_TSV.open(encoding="utf-8") as f:
        return {row["lemma_slp1"] for row in csv.DictReader(f, delimiter="\t")}


def chunk_clean(chunk):
    """SLP1-filter one whitespace chunk, restoring an avagraha-elided initial a-."""
    kept = "".join(c for c in chunk if c in SLP1_CHARS or c == "'")
    if kept.startswith("'"):
        kept = "a" + kept[1:]
    return "".join(c for c in kept if c in SLP1_CHARS)


class Segmenter:
    """Per-chunk vidyut-cheda with a dedupe cache (ca/na/hi recur thousands of
    times). A chunk is 'analyzable' when cheda returns >=1 token and every
    token carries a lemma."""

    def __init__(self):
        from vidyut.cheda import Chedaka
        self.chedaka = Chedaka(str(VIDYUT_DATA_ROOT))
        self.cache = {}

    def run(self, chunk):
        if chunk not in self.cache:
            try:
                self.cache[chunk] = [(t.text, t.lemma) for t in self.chedaka.run(chunk)]
            except Exception:
                self.cache[chunk] = []
        return self.cache[chunk]


def classify_metre(chandas, slp_verse):
    """Same two-tier + null method as build_reading_pack_metre.classify_sentence,
    applied to the whole saying: strict vṛtta (>=8 syllables), else the
    anuṣṭubh multiple-of-8 heuristic (8..32), else unresolved. Metre names are
    normalised to IAST (vidyut reports them in SLP1)."""
    from vidyut.lipi import Scheme, transliterate
    slp = "".join(c for c in slp_verse if c in SLP1_CHARS or c == " ").strip()
    if not slp:
        return ("", "unresolved", 0)
    try:
        m = chandas.classify(slp)
    except BaseException:
        return ("", "unresolved", 0)
    n = sum(len(line) for line in m.aksharas)
    if m.padya and n >= 8:
        return (transliterate(m.padya, Scheme.Slp1, Scheme.Iast), "vidyut-chandas", n)
    if n >= 8 and n % 8 == 0 and n <= 32:
        return ("anuṣṭubh", "syllable-heuristic", n)
    return ("", "unresolved", n)


def score_saying(iast, seg, ranks, grammar, maxrank, w1b):
    from vidyut.lipi import Scheme, transliterate
    slp = transliterate(iast, Scheme.Iast, Scheme.Slp1)
    n_chunks = n_tokens = n_unan = 0
    vocab_loads, w1b_hits, w1b_n = [], 0, 0
    log_max = math.log10(maxrank)
    for raw in re.split(r"[/|\s]+", slp):
        chunk = chunk_clean(raw)
        if not chunk:
            continue
        n_chunks += 1
        toks = seg.run(chunk)
        analyzable = bool(toks) and all(l is not None for _, l in toks)
        n_tokens += max(1, len(toks))
        if not analyzable:
            n_unan += 1
            vocab_loads.append(1.0)  # one unknown content word
            w1b_n += 1
            continue
        for _text, lemma in toks:
            if grammar.get(lemma) in FUNCTION_GRAMMAR:
                continue  # function words: fusion axis only, like W2a
            rank = ranks.get(lemma)
            vocab_loads.append(math.log10(rank) / log_max if rank else 1.0)
            w1b_n += 1
            if lemma in w1b:
                w1b_hits += 1
    vocab = sum(vocab_loads) / len(vocab_loads) if vocab_loads else 0.0
    fusion = (n_tokens - n_chunks) / n_tokens if n_tokens else 0.0
    pct_w1b = w1b_hits / w1b_n if w1b_n else 0.0
    return vocab, fusion, n_chunks, n_tokens, n_unan, pct_w1b, slp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="score only the first N sayings")
    args = ap.parse_args()

    if not SPRUECHE.exists():
        sys.exit(f"Indische Sprüche JSONL not found at {SPRUECHE} (F33 — clone SanskritLexicography)")
    try:
        from vidyut.chandas import Chandas
    except ImportError:
        sys.exit("vidyut not installed — pip install vidyut (see scripts/requirements.txt)")

    w_vocab, w_fusion = load_weights()
    ranks, grammar, maxrank = load_ranks()
    w1b = load_w1b()
    seg = Segmenter()
    chandas = Chandas(str(METERS_TSV))

    rows = []
    with SPRUECHE.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            iast = r.get("iast") or ""
            vocab, fusion, n_chunks, n_tokens, n_unan, pct_w1b, slp = score_saying(
                iast, seg, ranks, grammar, maxrank, w1b)
            metre, metre_method, syllables = classify_metre(chandas, slp)
            head = re.split(r"[/|]", iast)[0].strip()
            rows.append({
                "num": r["num"],
                "saying_id": r["saying_id"],
                "difficulty": round(w_vocab * vocab + w_fusion * fusion, 4),
                "vocab": round(vocab, 4),
                "fusion": round(fusion, 4),
                "n_chunks": n_chunks,
                "n_tokens": n_tokens,
                "n_unanalyzable": n_unan,
                "pct_w1b": round(pct_w1b, 3),
                "syllables": syllables,
                "metre": metre,
                "metre_method": metre_method,
                "iast_head": head[:60],
            })
            if args.limit and len(rows) >= args.limit:
                break
            if len(rows) % 1000 == 0:
                print(f"  scored {len(rows)} sayings")

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_TSV.open("w", encoding="utf-8", newline="") as f:
        wtr = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        wtr.writeheader()
        wtr.writerows(rows)

    ranked = sorted(rows, key=lambda r: r["difficulty"])
    print(f"scored {len(rows)} sayings -> {OUT_TSV}")
    print(f"weights: vocab={w_vocab:.4f} fusion={w_fusion:.4f} (reduced from {WEIGHTS_JSON.name})")
    print("easiest 10:")
    for r in ranked[:10]:
        print(f"  {r['num']:>5}  {r['difficulty']:.4f}  {r['metre'] or '-':<12} {r['iast_head'][:50]}")


if __name__ == "__main__":
    main()
