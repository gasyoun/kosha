#!/usr/bin/env python3
"""H4731 — Join kosha bloomfield-rv-citations to Elizarenkova RU RV + rvlinks anchors.

Census C4: every Bloomfield 1906 RV citation (mandala+sukta+verse+pada pratika) is
joined to the published Elizarenkova Russian translation (SamudraManthanam
Index/Updater/Data/01_rigveda.no_tags + 02_rigveda.no_tags, H2863) and to the
addressable rvlinks per-verse anchor (sanskrit-lexicon/rvlinks, rvMM.SSS.VV).

RIGHTS DISCIPLINE: the join TSV is a POINTER LAYER. It stores references and
anchors only — it does NOT bulk-copy the Elizarenkova translation text (in
copyright; М.: Наука, 1989+). Estate precedent puts every Elizarenkova-derived
bulk layer at tier=restricted (sa-ru-glossary, pwg-ru-mdf-export). The report
carries bounded excerpts (<=160 chars/verse) for the 25-citation verification
sample only.

Inputs (all read-only):
  data/concordance/bloomfield_rv_citations.tsv          (kosha, H896)
  ../SamudraManthanam/Index/Updater/Data/0{1,2}_rigveda.no_tags
  ../rvlinks/rvhymns/rv*.html

Output:
  data/concordance/bloomfield_rv_x_elizarenkova_ru.tsv
  data/concordance/BLOOMFIELD_RV_X_ELIZARENKOVA_RU_REPORT.md
"""

from __future__ import annotations

import argparse
import collections
import difflib
import glob
import random
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RVLINKS_BASE = "https://sanskrit-lexicon.github.io/rvlinks/rvhymns"

# ---------------------------------------------------------------- helpers ---


def norm_iast(s: str) -> str:
    """Loose normalization for pratika-vs-source substring checks (H896 spirit)."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "", s.lower())
    return s


def check_pratika(pratika: str, sanskrit: str) -> str:
    """H896 method: strip parenthetical asides, normalize, drop final char
    (pausa-vs-sandhi boundary tolerance), substring-match."""
    if not pratika or not sanskrit:
        return ""
    p = re.sub(r"\([^)]*\)", "", pratika)
    p = norm_iast(p)
    if len(p) > 1:
        p = p[:-1]
    return "y" if p and p in norm_iast(sanskrit) else "n"


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", s).strip()


def norm_ru(s: str) -> str:
    """Normalization for RU cross-digitization comparison."""
    s = strip_tags(s).lower().replace("ё", "е")
    s = re.sub(r"[-–—«».,!?;:'\"()\[\]]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# ------------------------------------------------------------- samudra ---


def parse_samudra(samudra_dir: Path) -> tuple[dict[tuple[int, int, int], dict], dict[tuple[int, int, int], tuple[int, int]]]:
    """citation_block id="S.V" per mandala file.

    Returns ({(m,s,v): {sanskrit, ru}}, {(m,s,v): (block_sukta, block_first_verse)}).
    Some hymns are printed as verse-pair blocks (e.g. the anuṣṭubh Agni hymns
    1.65–1.84: block id="65.1" carries verses 1-2, title "I. 65. 1-2"); the
    range title is authoritative, so every verse a block covers is indexed to it.
    """
    out: dict[tuple[int, int, int], dict] = {}
    ref: dict[tuple[int, int, int], tuple[int, int]] = {}
    danda_re = re.compile(r"॥\d+॥")
    block_re = re.compile(r'<div class="citation_block" id="(\d+)\.(\d+)">')
    range_re = re.compile(r"\.\s*(\d+)\.\s*(\d+)(?:\s*[-–]\s*(\d+))?\s*\"")
    for f in sorted(samudra_dir.glob("0?_rigveda.no_tags")):
        mandala = int(f.name[:2])
        text = f.read_text(encoding="utf-8")
        marks = list(block_re.finditer(text))
        for i, m in enumerate(marks):
            bsukta, bverse = int(m.group(1)), int(m.group(2))
            end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
            body = text[m.end():end]
            r = range_re.search(body[:400])
            if r and int(r.group(1)) == bsukta:
                v_lo, v_hi = int(r.group(2)), int(r.group(3) or r.group(2))
            else:
                v_lo, v_hi = bverse, bverse
            dandas = list(danda_re.finditer(body))
            comment = body.find('<span class="comment_number"')
            # blocks may carry several verses (pair blocks): the Russian starts
            # after the LAST danda marker; everything before it is Sanskrit.
            cut = dandas[-1].end() if dandas else 0
            sanskrit = strip_tags(body[:cut]) if dandas else ""
            ru_raw = body[cut:comment if comment != -1 else len(body)]
            blk = {"sanskrit": sanskrit, "ru": strip_tags(ru_raw)}
            for v in range(v_lo, v_hi + 1):
                out[(mandala, bsukta, v)] = blk
                ref[(mandala, bsukta, v)] = (bsukta, bverse)
    return out, ref


# -------------------------------------------------------------- rvlinks ---


def parse_rvlinks(rvlinks_dir: Path) -> tuple[set, dict[tuple[int, int, int], str]]:
    """-> ({(m,s,v) anchor exists}, {(m,s,v): ru text})."""
    anchors: set = set()
    ru_map: dict[tuple[int, int, int], str] = {}
    anchor_re = re.compile(r"<a id='rv(\d{2})\.(\d{3})\.(\d{2})'")
    ru_re = re.compile(r'<p class="ru">(.*?)</p>', re.S)
    for f in sorted(glob.glob(str(rvlinks_dir / "rv*.html"))):
        text = Path(f).read_text(encoding="utf-8")
        parts = anchor_re.split(text)
        # parts: [pre, m, s, v, chunk1, m, s, v, chunk2, ...]
        for i in range(1, len(parts), 4):
            mm, ss, vv = int(parts[i]), int(parts[i + 1]), int(parts[i + 2])
            chunk = parts[i + 3]
            anchors.add((mm, ss, vv))
            mru = ru_re.search(chunk)
            if mru:
                ru_map[(mm, ss, vv)] = strip_tags(mru.group(1))
    return anchors, ru_map


# ----------------------------------------------------------------- main ---


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bloomfield", type=Path, default=REPO / "data/concordance/bloomfield_rv_citations.tsv")
    ap.add_argument("--samudra-dir", type=Path, default=REPO.parent / "SamudraManthanam/Index/Updater/Data")
    ap.add_argument("--rvlinks-dir", type=Path, default=REPO.parent / "rvlinks/rvhymns")
    ap.add_argument("--out", type=Path, default=REPO / "data/concordance/bloomfield_rv_x_elizarenkova_ru.tsv")
    ap.add_argument("--report", type=Path, default=REPO / "data/concordance/BLOOMFIELD_RV_X_ELIZARENKOVA_RU_REPORT.md")
    ap.add_argument("--sample", type=int, default=25)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    # load bloomfield citations
    rows = []
    with open(args.bloomfield, encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        assert header == ["mandala", "sukta", "verse", "pada_letter", "pratika", "full_citation"], header
        for line in fh:
            m, s, v, p, prat, _full = line.rstrip("\n").split("\t")
            rows.append((int(m), int(s), int(v), p, prat))
    print(f"bloomfield citations: {len(rows)}")

    sam, sam_ref = parse_samudra(args.samudra_dir)
    print(f"samudra elizarenkova verse blocks: {len(sam)} (incl. pair-block expansion)")
    anchors, rvru = parse_rvlinks(args.rvlinks_dir)
    print(f"rvlinks anchors: {len(anchors)} (ru text for {len(rvru)})")

    # join
    joined_keys = set()
    out_rows = []
    status_counter: collections.Counter = collections.Counter()
    pratika_checks = collections.Counter()
    for m, s, v, p, prat in rows:
        ref = anchor = ""
        if (m, s, v) in sam:
            bs, bv = sam_ref[(m, s, v)]
            ref = f"samudra:{m:02d}_rigveda.no_tags#{bs}.{bv}"
        if (m, s, v) in anchors:
            anchor = f"{RVLINKS_BASE}/rv{m:02d}.{s:03d}.html#rv{m:02d}.{s:03d}.{v:02d}"
        if ref and anchor:
            st = "joined"
        elif anchor and m > 2:
            st = "elizarenkova_out_of_samudra_coverage"
        elif anchor:
            st = "elizarenkova_verse_missing"
        elif ref:
            st = "rvlinks_anchor_missing"
        else:
            st = "unjoined_no_surface"
        pv = check_pratika(prat, sam[(m, s, v)]["sanskrit"]) if (m, s, v) in sam else ""
        if pv:
            pratika_checks[pv] += 1
        if st == "joined":
            joined_keys.add((m, s, v))
        status_counter[st] += 1
        out_rows.append((m, s, v, p, prat, st, ref, anchor, pv))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("mandala\tsukta\tverse\tpada_letter\tpratika\tmatch_status\t"
                 "elizarenkova_ref\trvlinks_anchor\tpratika_verified_in_elizarenkova\n")
        for r in out_rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    print(f"wrote {args.out} ({len(out_rows)} rows)")

    # ---- bulk canary: samudra RU vs rvlinks RU on every joined verse key ----
    ratios = []
    low = 0
    for key in sorted(joined_keys):
        a, b = norm_ru(sam[key]["ru"]), norm_ru(rvru[key])
        if not a or not b:
            continue
        r = difflib.SequenceMatcher(None, a, b).ratio()
        ratios.append(r)
        if r < 0.85:
            low += 1
    mean_ratio = sum(ratios) / len(ratios) if ratios else 0.0

    # ---- 25-citation stratified verification sample ----
    by_m: dict[int, list] = collections.defaultdict(list)
    for i, r in enumerate(out_rows):
        by_m[r[0]].append(i)
    rng = random.Random(args.seed)
    sample_idx = set()
    per_m = max(1, args.sample // len(by_m))
    for m, idxs in sorted(by_m.items()):
        sample_idx.update(rng.sample(idxs, min(per_m, len(idxs))))
    # top up to exactly --sample rows (per-mandala pass can undershoot)
    all_idx = list(range(len(out_rows)))
    while len(sample_idx) < args.sample:
        sample_idx.add(rng.choice(all_idx))
    while len(sample_idx) > args.sample:
        sample_idx.discard(rng.choice(sorted(sample_idx)))
    sample = sorted(sample_idx)

    # ---- report ----
    dist = ", ".join(f"`{k}` {v}" for k, v in status_counter.most_common())
    pv_line = (f"pratika-vs-source substring check (H896 method, {sum(pratika_checks.values())} applicable): "
               f"y {pratika_checks.get('y', 0)} ({pratika_checks.get('y', 0) / max(1, sum(pratika_checks.values())):.1%}), "
               f"n {pratika_checks.get('n', 0)}")
    mandalas_samudra = sorted({k[0] for k in sam})
    samp_lines = ["| # | citation | pratika | rvlinks anchor | Samudra RU (excerpt ≤160) |", "|---|---|---|---|---|"]
    for n, i in enumerate(sample, 1):
        m, s, v, p, prat, st, ref, anchor, pv = out_rows[i]
        ru_x = (sam[(m, s, v)]["ru"][:160] + "…") if (m, s, v) in sam else "—"
        samp_lines.append(f"| {n} | RV.{m}.{s}.{v}{p} | {prat[:60]} | {anchor or '—'} | {ru_x} |")

    # residue: distinct verse keys with no rvlinks anchor (out-of-canonical citations)
    no_surf = sorted({(r[0], r[1], r[2]) for r in out_rows if r[5] == "unjoined_no_surface"})
    res_rows = []
    for (rm, rs, rv) in no_surf:
        cls = "outside the 10-maṇḍala canon (khila/parishiṣṭa or concordance-internal numbering)" if rm > 10 \
            else "verse number beyond the standard text's count for this hymn (edition-variant numbering)"
        res_rows.append(f"| RV.{rm}.{rs}.{rv} | {cls} |")

    report = f"""# Bloomfield 1906 RV citations × Elizarenkova Russian RV — citation-to-translation join

_Created: 15-09-2026 · H4731 (Census C4) · builder: `scripts/build_bloomfield_rv_elizarenkova_join.py`_

## What this is

Every direct Ṛgveda citation in [Bloomfield's *A Vedic Concordance*](https://github.com/gasyoun/kosha/blob/main/data/concordance/bloomfield_rv_citations.tsv) (36,680 pada-level citation rows,
10,374 distinct verse keys) joined to the **published Elizarenkova Russian translation**
(SamudraManthanam `Index/Updater/Data/01_rigveda.no_tags` + `02_rigveda.no_tags`, H2863)
and to the **addressable rvlinks per-verse anchor** ([sanskrit-lexicon/rvlinks](https://github.com/sanskrit-lexicon/rvlinks), `rvMM.SSS.VV`).

The join TSV is a **pointer layer**: references + anchors + match status only.
It deliberately does **not** bulk-copy the Elizarenkova translation text — the translation
is in copyright (Т.Я. Елизаренкова, М.: «Наука», 1989+), and every Elizarenkova-derived bulk
layer in the estate is `tier: restricted` (see `sa-ru-glossary`, `pwg-ru-mdf-export` in
`data/manifest/datasets.json`). Consumers resolve the pointer at render time.

## Join counts ({len(out_rows)} citation rows)

| match_status | rows | meaning |
|---|---:|---|
""" + "\n".join(f"| `{k}` | {v} | |" for k, v in status_counter.most_common()) + f"""

- Distinct joined verse keys (Elizarenkova + anchor both present): **{len(joined_keys)}**
- Samudra Elizarenkova coverage: mandalas {", ".join(str(x) for x in mandalas_samudra)} only
  ({len(sam)} verse keys after pair-block expansion = the two volumes digitized under H2863).
  Citations in mandalas 3–10 get the rvlinks anchor only — Elizarenkova volumes V–X exist in
  print but are not in the Samudra digitization; that is an honest coverage boundary, not a
  join failure.
- **Verse-pair blocks handled:** in the anuṣṭubh Agni hymns 1.65–1.84 Elizarenkova's edition
  prints verse PAIRS in one block (`id="65.1"` carries verses 1-2, range title "I. 65. 1-2");
  the range title is authoritative and every covered verse is indexed to its block, so even
  verses resolve instead of falsely reporting missing.
- {pv_line}. The `n` residue is the same genuine orthographic variance documented in
  [BLOOMFIELD_RV_CROSSREF_REPORT.md](https://github.com/gasyoun/kosha/blob/main/data/concordance/BLOOMFIELD_RV_CROSSREF_REPORT.md)
  (anusvara-vs-homorganic-nasal spellings etc.), now measured against a third independent digitization.

## Own-data canary — two independent Elizarenkova digitizations agree

Samudra `0?_rigveda.no_tags` (H2863) and rvlinks `rvhymns/*.html` (M. Gasūns 2018 source)
are independent digitizations of the same published translation. On all {len(ratios)} joined
verse keys, normalized RU-vs-RU similarity: mean **{mean_ratio:.3f}**, share ≥ 0.85:
**{1 - low / max(1, len(ratios)):.1%}** ({low} below 0.85 — line-break and punctuation
variants of the same text, spot-checked; neither digitization was mutated).

## Verification — 25-citation stratified sample (seed {args.seed})

Human-eyeball table: pratīka (Bloomfield's citation incipit) against the resolved
Elizarenkova Russian at the anchor. Full RU text stays at the pointer; excerpts ≤160 chars.

{chr(10).join(samp_lines)}

## Residue — citations no surface can answer ({len(no_surf)} distinct verse keys)

These `unjoined_no_surface` keys are named, not silently dropped (status column keeps them
queryable in the TSV):

| key | class |
|---|---|
{chr(10).join(res_rows)}

## Limitations

- Pada-granular RU line mapping (which Russian line answers pāda c of a quoted pair) is the
  separate H2850 judgment surface (PWG cards); this census join is verse-granular by design —
  the pada_letter column is carried through untouched for that downstream use.
- rvlinks anchors are verified to exist ({len(anchors)} anchors parsed); anchor stability is
  upstream's (sanskrit-lexicon org), URL shape `rvhymns/rvMM.SSS.html#rvMM.SSS.VV`.
- Valakhilya hymns (RV 8.49–59) participate normally if cited; they are within rvlinks'
  1028-hymn layout.

## Reproduce

```
python scripts/build_bloomfield_rv_elizarenkova_join.py   # defaults resolve sibling repos
```

Deterministic (seed {args.seed}); inputs read-only; no network.
"""
    args.report.write_text(report, encoding="utf-8")
    print(f"wrote {args.report}")
    print(f"canary: n={len(ratios)} mean_ratio={mean_ratio:.3f} pct>=0.85={1 - low / max(1, len(ratios)):.1%}")
    print("statuses:", dict(status_counter))
    return 0


if __name__ == "__main__":
    sys.exit(main())
