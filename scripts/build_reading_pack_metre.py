#!/usr/bin/env python
"""Metre-layer annotator over the reading packs — pedagogy Wave 3, surface W3a (H951).

The field (§3.9) names "metre-ID wired into reading" as a gap. This is the **data
layer** for it: it annotates each reading-pack sentence with its metre. It builds **no
UI and no metre trainer** — SanskritKaraoke owns that (wave notation, Metre-ID / Beat-Tap
quizzes, Apte prosody DB); kosha's contribution is the corpus-grounded per-verse
annotation those tools lack (the ARCHITECTURE integration-surface rule). The output is a
joinable TSV, not a page.

Method (honest, two-tier + a null):
  * **strict vṛtta** — `vidyut.chandas` (the real classifier, over the vendored
    `data/vidyut/chandas/meters.tsv`) identifies fixed-pattern metres per pāda:
    vaṃśastha, upajāti, vasantatilakā, mālinī, … High confidence (validated: the
    Kirātārjunīya-1 pack scans 92/92 as vaṃśastha, which that canto is).
  * **anuṣṭubh (śloka)** — vidyut does NOT classify the loose śloka metre, but the DCS
    sentences align cleanly to half-ślokas: 655 of the unclassified sentences scan at
    **exactly 16 syllables** (= 2 anuṣṭubh pādas). A sentence whose syllable count is a
    multiple of 8 (8/16/24/32) and matched no strict vṛtta is labelled `anuṣṭubh` by
    this **syllable heuristic**. Medium confidence — not a positive pattern match, but
    the standard half-śloka in overwhelmingly-anuṣṭubh epic/Gītā text.
  * **unresolved** — anything else (odd syllable counts, prose, fragments) is left with
    an empty metre and its syllable count recorded. Never guessed.

Determinism: pure read of the packs + the vendored meters.tsv; no network, no clock.
Depends on the W2a reading packs (H949). Requires `vidyut` (see scripts/requirements.txt).

Usage:
  python scripts/build_reading_pack_metre.py
"""
import csv
import glob
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
METERS_TSV = ROOT / "data" / "vidyut" / "chandas" / "meters.tsv"
PACK_DIR = ROOT / "reading" / "data"
OUT_TSV = ROOT / "data" / "metre" / "reading_pack_metre.tsv"
COVERAGE_TSV = ROOT / "data" / "metre" / "metre_coverage.tsv"

# vidyut-chandas (Rust) panics on any non-SLP1 byte, so hard-filter to the SLP1
# alphabet + space before ever handing it a string.
SLP1_CHARS = set("aAiIuUfFxXeEoOMHkKgGNcCjJYwWqQRtTdDnpPbBmyrlvSzshL ")


def clean_slp1(s):
    return "".join(ch for ch in s if ch in SLP1_CHARS)


def load_pack(path):
    txt = Path(path).read_text(encoding="utf-8")
    if path.endswith(".json"):
        return json.loads(txt)
    i, j = txt.find("= {"), txt.rfind("};")
    return json.loads(txt[i + 2:j + 1])


def syllables(match):
    """vidyut's Match.aksharas is a list of pāda-lines; total syllables = sum of
    their lengths."""
    return sum(len(line) for line in match.aksharas)


def classify_sentence(chandas, transliterate, Scheme, text):
    """Return (metre, metre_type, method, confidence, n_syllables)."""
    slp = clean_slp1(transliterate(text, Scheme.Iast, Scheme.Slp1))
    if not slp.strip():
        return ("", "", "unresolved", "", 0)
    try:
        m = chandas.classify(slp)
    except BaseException:
        return ("", "", "unresolved", "", 0)
    n = syllables(m)
    # A vṛtta pāda is >=8 syllables; a strict match on a shorter string is a spurious
    # partial hit on a prose fragment/heading (e.g. the 6-syllable "atha kathāmukham"
    # mis-matching drutavilambitā). Require >=8 syllables to trust a vṛtta ID.
    if m.padya and n >= 8:
        return (m.padya, "vrtta", "vidyut-chandas", "high", n)
    if n >= 8 and n % 8 == 0 and n <= 32:
        return ("anuṣṭubh", "jati", "syllable-heuristic", "medium", n)
    return ("", "", "unresolved", "", n)


def main():
    if not METERS_TSV.exists():
        sys.exit(f"vendored meters.tsv not found at {METERS_TSV}")
    try:
        from vidyut.chandas import Chandas
        from vidyut.lipi import Scheme, transliterate
    except ImportError:
        sys.exit("vidyut not installed — pip install vidyut (see scripts/requirements.txt)")

    chandas = Chandas(str(METERS_TSV))

    paths = sorted(glob.glob(str(PACK_DIR / "*.json")))
    seen = {Path(p).stem for p in paths}
    paths += [p for p in sorted(glob.glob(str(PACK_DIR / "*.js")))
              if Path(p).stem not in seen]

    rows = []
    cov = {}  # slug -> {"n":, "high":, "medium":, "unresolved":, metres:set}
    for p in paths:
        pack = load_pack(p)
        slug = pack.get("slug", Path(p).stem)
        c = cov.setdefault(slug, {"n": 0, "high": 0, "medium": 0, "unresolved": 0,
                                  "metres": {}})
        for s in pack["sentences"]:
            text = s.get("text", "")
            metre, mtype, method, conf, n = classify_sentence(
                chandas, transliterate, Scheme, text)
            locus = s.get("locus", "")
            rows.append({
                "pack": slug,
                "locus": locus,
                "dcs": s.get("dcs") or "",
                "syllables": n,
                "metre": metre,
                "metre_type": mtype,
                "method": method,
                "confidence": conf,
                "text": text[:60],
            })
            c["n"] += 1
            if conf == "high":
                c["high"] += 1
            elif conf == "medium":
                c["medium"] += 1
            else:
                c["unresolved"] += 1
            if metre:
                c["metres"][metre] = c["metres"].get(metre, 0) + 1

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    cols = ["pack", "locus", "dcs", "syllables", "metre", "metre_type",
            "method", "confidence", "text"]
    with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    with open(COVERAGE_TSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["pack", "sentences", "vrtta_high", "anustubh_medium",
                    "unresolved", "identified_pct", "top_metres"])
        for slug in sorted(cov):
            c = cov[slug]
            ident = c["high"] + c["medium"]
            top = ", ".join(f"{k}:{v}" for k, v in sorted(
                c["metres"].items(), key=lambda x: -x[1])[:3])
            w.writerow([slug, c["n"], c["high"], c["medium"], c["unresolved"],
                        round(100.0 * ident / c["n"], 1) if c["n"] else 0.0, top])

    tot = len(rows)
    high = sum(1 for r in rows if r["confidence"] == "high")
    med = sum(1 for r in rows if r["confidence"] == "medium")
    print(f"annotated {tot} sentences across {len(cov)} packs -> {OUT_TSV.name}")
    print(f"  strict vṛtta (high): {high} ({100*high/tot:.0f}%)  ·  "
          f"anuṣṭubh heuristic (medium): {med} ({100*med/tot:.0f}%)  ·  "
          f"unresolved: {tot-high-med} ({100*(tot-high-med)/tot:.0f}%)")
    print(f"  identified overall: {high+med} ({100*(high+med)/tot:.0f}%)")


if __name__ == "__main__":
    main()
