#!/usr/bin/env python3
"""nws_residue_classification.py — H6050: classify the NWS (Halle) residue
outside the six-dictionary union PWG∪PW∪MW∪SCH∪ACC∪PWKVN.

HEADLINE (pinned 06-10-2026, inputs: nws.tar.gz sha256 054b05da…, csl-orig @
f4c08c5): the H5932 stem-based "82.7% absent" (138,976 of 167,991 lemmas) is a
TRANSLITERATION-CONVENTION artifact, not lexical novelty. The per-lemma JSON
`key1` field carries the same headword in SLP1, and 138,952 of the 138,976
(99.983%) match the union exactly. The true residue is 24 lemma-keys — every
one of them a content-empty record.

Classes (first-match cascade over the 138,976 residue; sums to 100.000%):

  C1 translit_exact       key1 ∈ union (exact)                     138,952
  C2 content_uncollected  key1 ∉ union, entry carries NWS/SCH           0
                          content (would be genuine novelty)
  C3 errata_near          key1 ∉ union, empty, len(key1) ≥ 4, within
                          Levenshtein distance 1 of some union key      18
  C4 orphan_empty         the rest: scrape artifacts, short junk,
                          sandhi-shaped fragments, all empty             6

Method notes:
  - stem/k1 extraction is the session-exact H5932 method, ported from
    csl-observatory scripts/nws_halle_intersections.py (pr #259): NWS keys =
    tar filename stems with leading '-' stripped; dictionary keys = <k1>
    values on <L> lines, whitespace-stripped, leading '-' stripped.
  - the near-neighbor test generates all substitution/deletion/insertion
    variants over ASCII letters and intersects with the union set
    (deterministic; no hand lists anywhere).
  - nothing from the NWS tar is embedded here; run locally against the
    private tar (pwg-ru-data/layers/nws.tar.gz) and the csl-orig checkout.

Usage:
  python scripts/nws_residue_classification.py [--selftest] [--dump DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import string
import subprocess
import sys
import tarfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
LETTERS = string.ascii_letters

DICTS = ["pwg", "pw", "mw", "sch", "acc", "pwkvn"]
K1_RE = re.compile(r"<k1>([^<\n]*)")

TAR_SHA256 = "054b05da96df2f1af2c95c02b7e15d87f8a616d4eaa339f93e3ed7430e07f00c"
CSL_ORIG_PIN = "f4c08c5"  # H5932 measurement revision

# Pinned H6050 numbers (06-10-2026) — checked by --selftest.
PINNED = {
    "nws_stems": 167991,
    "residue": 138976,        # stem-based absent (H5932, reproduced)
    "c1_translit_exact": 138952,
    "c2_content_uncollected": 0,
    "c3_errata_near": 18,
    "c4_orphan_empty": 6,
    "total_key1_in_union": 167967,  # over ALL 167,991 lemmas, not just residue
}


def _github_roots() -> list[Path]:
    roots = [REPO.parent, REPO.parent.parent, Path.home() / "Documents" / "GitHub"]
    seen, out = set(), []
    for r in roots:
        if r not in seen and r.is_dir():
            seen.add(r)
            out.append(r)
    return out


def _default_sibling(rel: str) -> Path:
    for root in _github_roots():
        p = root / rel
        if p.exists():
            return p
    return _github_roots()[0] / rel


DEF_TAR = _default_sibling("pwg-ru-data/layers/nws.tar.gz")
DEF_CSL_ORIG = _default_sibling("csl-orig")


# --- H5932-method key extraction (ported from csl-observatory pr #259) ------

def nws_members(tar_path: Path) -> dict[str, tarfile.TarInfo]:
    """stem -> first tar member (H5932 filter: files, .json, no dot-dirs)."""
    members: dict[str, tarfile.TarInfo] = {}
    with tarfile.open(tar_path, "r:gz") as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            base = m.name.rsplit("/", 1)[-1]
            if base.startswith(".") or "/." in m.name or not base.endswith(".json"):
                continue
            members.setdefault(base[:-5].lstrip("-"), m)
    return members


def dict_k1_keys(csl_orig: Path, dict_code: str) -> set[str]:
    """k1 set of one Cologne dictionary (<k1> on <L> lines, H5932 method)."""
    txt = csl_orig / "v02" / dict_code / f"{dict_code}.txt"
    out: set[str] = set()
    with open(txt, encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.startswith("<L>"):
                continue
            m = K1_RE.search(line)
            if m and m.group(1).strip():
                out.add(m.group(1).strip().lstrip("-"))
    return out


# --- deterministic classification --------------------------------------------

def near_targets(key1: str, union: set[str]) -> list[str]:
    """Sorted union keys within Levenshtein distance 1 (subs/dels/ins)."""
    if not key1:
        return []
    variants: set[str] = set()
    for i in range(len(key1)):  # substitutions + deletions
        head, tail = key1[:i], key1[i + 1:]
        variants.add(head + tail)
        for c in LETTERS:
            variants.add(head + c + tail)
    for i in range(len(key1) + 1):  # insertions
        for c in LETTERS:
            variants.add(key1[:i] + c + key1[i:])
    variants.discard(key1)
    return sorted(variants & union)


def classify(stem: str, key1: str, content_len: int, union: set[str]) -> tuple[str, str]:
    """First-match cascade. Returns (class, evidence)."""
    if key1 in union:
        return "c1_translit_exact", key1
    if content_len > 0:
        return "c2_content_uncollected", key1
    if len(key1) >= 4:
        near = near_targets(key1, union)
        if near:
            return "c3_errata_near", f"{key1} ~ {near[0]}"
    return "c4_orphan_empty", key1 or "(no key1)"


def stem_features(stem: str) -> list[str]:
    """Site-convention diacritic codes carried by a stem (e.g. _a, _s)."""
    return re.findall(r"_[a-z]", stem)


# --- driver -------------------------------------------------------------------

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def csl_orig_head(csl_orig: Path) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=csl_orig,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "(not a git checkout)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--nws-tar", type=Path, default=DEF_TAR)
    ap.add_argument("--csl-orig", type=Path, default=DEF_CSL_ORIG)
    ap.add_argument("--selftest", action="store_true",
                    help="fail (exit 1) unless every pinned H6050 number reproduces")
    ap.add_argument("--dump", type=Path,
                    help="write per-class TSVs (headwords only) into this directory")
    args = ap.parse_args()

    if not args.nws_tar.is_file():
        sys.exit(f"FAIL: NWS tar not found: {args.nws_tar}")
    if not (args.csl_orig / "v02").is_dir():
        sys.exit(f"FAIL: csl-orig checkout not found: {args.csl_orig}")

    tar_sha = sha256_of(args.nws_tar)
    head = csl_orig_head(args.csl_orig)
    union = set()
    K = {}
    for d in DICTS:
        K[d] = dict_k1_keys(args.csl_orig, d)
        union |= K[d]

    members = nws_members(args.nws_tar)
    stems = set(members)
    residue = stems - union

    counts = {k: 0 for k in ("c1_translit_exact", "c2_content_uncollected",
                             "c3_errata_near", "c4_orphan_empty")}
    c1_content = c1_extra = total_key1_hits = 0
    per_dict = {d: 0 for d in DICTS}
    feat_hist: dict[str, int] = {}
    dump_rows: dict[str, list[str]] = {k: [] for k in counts}

    with tarfile.open(args.nws_tar, "r:gz") as tf:
        for stem in sorted(stems):
            in_residue = stem in residue
            if not in_residue:
                # still count overall key1 coverage (cheap: only key1 needed)
                try:
                    j = json.load(tf.extractfile(members[stem]))
                except Exception:
                    continue
                k1 = (j.get("key1") or "").strip().lstrip("-")
                if k1 in union:
                    total_key1_hits += 1
                continue
            try:
                j = json.load(tf.extractfile(members[stem]))
            except Exception:
                counts["c4_orphan_empty"] += 1
                dump_rows["c4_orphan_empty"].append(
                    f"{stem}\t(json-parse-failed)")
                continue
            k1 = (j.get("key1") or "").strip().lstrip("-")
            content_len = len(j.get("nws") or "") + len(j.get("sch") or "")
            klass, ev = classify(stem, k1, content_len, union)
            counts[klass] += 1
            dump_rows[klass].append(f"{stem}\t{ev}\t{iast_of(j)}")
            if k1 in union:
                total_key1_hits += 1
                if len(j.get("nws") or "") > 0:
                    c1_content += 1
                if j.get("has_nws_extra"):
                    c1_extra += 1
                for d in DICTS:
                    if k1 in K[d]:
                        per_dict[d] += 1
            for f_ in stem_features(stem):
                feat_hist[f_] = feat_hist.get(f_, 0) + 1

    n = sum(counts.values())
    print(f"NWS tar        : {args.nws_tar}")
    print(f"tar sha256     : {tar_sha}")
    print(f"csl-orig HEAD  : {head} (pin {CSL_ORIG_PIN})")
    print(f"NWS stems      : {len(stems):,}")
    print(f"residue (H5932 stem-absent): {n:,}  (100.000%)")
    for k, v in counts.items():
        print(f"  {k:<22}: {v:>7,}  ({v / n * 100:.4f}%)")
    print(f"sum check      : {n == len(residue)} ({n:,} == {len(residue):,})")
    print()
    print(f"key1 ∈ union over ALL stems : {total_key1_hits:,} "
          f"({total_key1_hits / len(stems) * 100:.3f}%)")
    print(f"C1 with NWS sense content   : {c1_content:,}")
    print(f"C1 with has_nws_extra       : {c1_extra:,}")
    print(f"residue C1 per-dict hits    : {per_dict}")
    print("stem convention features    : "
          + ", ".join(f"{k}={v}" for k, v in sorted(
              feat_hist.items(), key=lambda x: -x[1])[:8]))

    if args.dump:
        args.dump.mkdir(parents=True, exist_ok=True)
        for k, rows in dump_rows.items():
            p = args.dump / f"{k}.tsv"
            p.write_text("stem\tevidence\tiast\n" + "\n".join(rows) + "\n",
                         encoding="utf-8")
            print(f"dumped {p}")

    if args.selftest:
        got = {
            "nws_stems": len(stems),
            "residue": len(residue),
            **counts,
            "total_key1_in_union": total_key1_hits,
        }
        bad = [f"{k} {v} != {PINNED[k]}" for k, v in got.items() if v != PINNED[k]]
        if tar_sha != TAR_SHA256:
            bad.append(f"tar sha256 drifted: {tar_sha}")
        if bad:
            print("SELFTEST FAIL: " + "; ".join(bad), file=sys.stderr)
            return 1
        print("SELFTEST PASS: all pinned H6050 numbers reproduce exactly.")
    return 0


def iast_of(j: dict) -> str:
    return (j.get("iast") or "").replace("\t", " ")


if __name__ == "__main__":
    sys.exit(main())
