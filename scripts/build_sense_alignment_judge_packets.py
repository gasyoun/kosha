#!/usr/bin/env python
"""H3910 — emit judge packets for the aligned-sense acceptance sample.

One packet per sampled row. A packet carries exactly what the judge is allowed
to see: the glosses that were joined, the method, the score, the witness list,
and nothing else — no `note`, no stratum label, no hint of which cards are the
suspected false-positive classes. The judge answers one question, *are these
the same meaning?*, and gives a short reason. It does not score, rank or repair.

Two presentation orders are emitted so the sample can be judged twice without
the second pass simply following the first:

  pass A — stratum order (the order the sampler produced)
  pass B — shuffled with a different seed, and card ids re-numbered, so the
           judge cannot align card N of B with card N of A by position

Writes data/concordance/judge/packets_pass_a.md
       data/concordance/judge/packets_pass_b.md
       data/concordance/judge/packet_key.json   (card id -> group_id, per pass)

The key file is what turns two verdict sets back into a per-row comparison; it
is deliberately a separate artifact so the judge sees the packets, not the key.
"""
import csv
import json
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "concordance" / "sense_alignment_acceptance_sample.tsv"
OUT_DIR = ROOT / "data" / "concordance" / "judge"

DICTS = [
    ("pwg", "PWG (de)"),
    ("mw", "MW (en)"),
    ("apte", "Apte (en)"),
    ("skd", "ŚKDR (sa)"),
    ("vcp", "VCP (sa)"),
]
# ŚKDR/VCP entries run to thousands of characters of Sanskrit; the judge needs
# the opening of the entry (where the sense sits), not the whole citation train.
CLIP = {"skd": 420, "vcp": 420}
DEFAULT_CLIP = 320
SHUFFLE_SEED = 19103  # 3910 reversed — deliberately not the sampler's seed


def clip(text, key):
    limit = CLIP.get(key, DEFAULT_CLIP)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit].rstrip() + " […]"


def card_md(cid, row):
    lines = [f"### card {cid}", ""]
    lines.append(f"- lemma: `{row['lemma_slp1']}`")
    lines.append(f"- method: `{row['method']}`  score: `{row['score']}`")
    lines.append(f"- witnesses: `{row['witnesses'] or '—'}`")
    if row["flags"]:
        lines.append(f"- flags: `{row['flags']}`")
    lines.append(f"- shape (pwg-mw-apte-skd-vcp): `{row['shape']}`")
    lines.append("")
    for key, label in DICTS:
        gloss = row.get(f"{key}_gloss") or ""
        if not gloss.strip():
            continue
        lines.append(f"**{label}** ({row.get(f'{key}_sense_ids') or '—'}): {clip(gloss, key)}")
        lines.append("")
    return "\n".join(lines)


HEADER = """# H3910 judge packets — pass {pass_name}

Question, asked once per card: **are the glosses below the same meaning?**

Answer `same` · `different` · `unsure`, plus one short reason. Do not score,
rank, repair or rewrite anything. Judge only what the card shows. `unsure` is a
real answer — use it when the entry shown is too truncated or too structural to
tell, and say so.

Cards: {n}

"""


def emit(path, pass_name, rows):
    parts = [HEADER.format(pass_name=pass_name, n=len(rows))]
    key = {}
    for i, row in enumerate(rows, 1):
        cid = f"{pass_name}{i:03d}"
        key[cid] = row["group_id"]
        parts.append(card_md(cid, row))
        parts.append("---\n")
    path.write_text("\n".join(parts), encoding="utf-8")
    return key


def main():
    with SRC.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    key_a = emit(OUT_DIR / "packets_pass_a.md", "A", rows)

    rows_b = list(rows)
    random.Random(SHUFFLE_SEED).shuffle(rows_b)
    key_b = emit(OUT_DIR / "packets_pass_b.md", "B", rows_b)

    (OUT_DIR / "packet_key.json").write_text(
        json.dumps(
            {"shuffle_seed": SHUFFLE_SEED, "n": len(rows), "pass_a": key_a, "pass_b": key_b},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"cards: {len(rows)}")
    for name in ("packets_pass_a.md", "packets_pass_b.md", "packet_key.json"):
        p = OUT_DIR / name
        print(f"wrote {p.relative_to(ROOT)}  ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
