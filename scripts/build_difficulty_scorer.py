#!/usr/bin/env python
"""Reading-pack difficulty scorer — pedagogy Wave 2, surface W2a (H949).

The field (§3.4/§6) names a **text difficulty scorer** as a gap: given a passage,
how hard is it to read? This scores every kosha reading pack on four corpus-grounded
axes and orders the packs into a graded reading sequence ("read these in this order").

    difficulty = w_vocab·VOCAB + w_sandhi·SANDHI + w_morph·MORPH + w_compound·COMPOUND

Each axis is a per-token load in [0,1], averaged over the pack's content tokens (or,
for sandhi, measured per sentence), so the composite is also in [0,1]:

  VOCAB     vocabulary rarity. Each content lemma → its corpus rank in
            data/frequency/lemma_frequency.tsv (the W1b signal); load =
            log10(rank)/log10(maxrank). A lemma the corpus never lists is treated as
            maximally rare (1.0). Rare words make a text hard.
  SANDHI    sandhi density. Per sentence, the fraction of word-boundaries FUSED by
            sandhi = (tokens − whitespace-chunks in the sandhied surface) / tokens.
            A densely-sandhied line is hard to segment. Measured off the pack itself.
  MORPH     morphological-form rarity. Each token's "<upos>|<morph>" → its corpus
            share in data/difficulty/morph_signature_freq.tsv (build_difficulty_signals.py);
            load = surprisal −log10(share) normalised by the rarest signature. A
            locative-dual or optative-middle form is harder than a nominative singular.
  COMPOUND  compound load. Fraction of content tokens that are compound members
            (DCS feat_case='Cpd', carried in the pack's morph field). Compounds must
            be decomposed before they can be parsed.

**This is ONE estimator, not "the" difficulty** (VERIFICATION R5). The weighting is a
modelling choice: the weights live in data/difficulty/difficulty_weights.json and are
meant to be tuned — a human should confirm them. The four axes and their normalisations
are documented above and in the emitted methods note so the score is legible, not a
black box.

Scoring reads only small TSVs + the pack JSON — no 878 MB DCS DB (that is needed only
by build_difficulty_signals.py, run once). Determinism: pure file reads, no clock, no
network.

Usage:
  python scripts/build_difficulty_scorer.py [--packs reading/data] [--emit-page]
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
sys.path.insert(0, str(ROOT / "scripts"))
from concordance_core import to_slp1  # noqa: E402  (reuse the canonical transcoder)

FREQ_TSV = ROOT / "data" / "frequency" / "lemma_frequency.tsv"
MORPH_TSV = ROOT / "data" / "difficulty" / "morph_signature_freq.tsv"
WEIGHTS_JSON = ROOT / "data" / "difficulty" / "difficulty_weights.json"
OUT_TSV = ROOT / "data" / "difficulty" / "reading_pack_difficulty.tsv"
OUT_JSON = ROOT / "data" / "difficulty" / "reading_pack_difficulty.json"
METHODS_MD = ROOT / "data" / "difficulty" / "METHODS.md"
PAGE_HTML = ROOT / "reading" / "difficulty" / "index.html"

# Default weights — a defensible starting point, NOT a truth. Vocabulary is the
# heaviest because unknown words block comprehension most directly; morphology and
# sandhi are the next parsing hurdles; compound load is real but partly correlated
# with morphology (a Cpd member is also a morph signature). A human should confirm
# (VERIFICATION R5); tune in difficulty_weights.json without touching code.
DEFAULT_WEIGHTS = {
    "vocab": 0.40,
    "sandhi": 0.20,
    "morphology": 0.25,
    "compound": 0.15,
}

# upos values that are structural, not "vocabulary" to be learned. Function words are
# still counted for sandhi/morph (they participate in the surface), but the vocab axis
# down-weights them: a text is not "hard vocabulary" because it uses `ca` and `tad`.
FUNCTION_UPOS = {"PART", "ADP", "CCONJ", "SCONJ", "PRON", "DET", "AUX"}
PUNCT_UPOS = {"PUNCT"}


def load_weights():
    if WEIGHTS_JSON.exists():
        w = json.loads(WEIGHTS_JSON.read_text(encoding="utf-8"))["weights"]
    else:
        w = dict(DEFAULT_WEIGHTS)
    s = sum(w.values())
    if s <= 0:
        sys.exit("difficulty weights sum to 0")
    return {k: v / s for k, v in w.items()}, w  # normalised for scoring, raw for report


def write_default_weights():
    if WEIGHTS_JSON.exists():
        return
    WEIGHTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    WEIGHTS_JSON.write_text(json.dumps({
        "_comment": "Difficulty-scorer weights (W2a, H949). ONE estimator, not 'the' "
                    "difficulty — tune these; a human should confirm. Axes: vocab "
                    "(lemma rarity), sandhi (boundary fusion), morphology (form "
                    "rarity), compound (Cpd-member share). They are re-normalised to "
                    "sum to 1 at score time, so relative sizes are what matter.",
        "weights": DEFAULT_WEIGHTS,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_vocab_ranks():
    ranks = {}
    maxrank = 1
    with open(FREQ_TSV, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            try:
                r = int(row["rank_all"])
            except (ValueError, KeyError):
                continue
            ranks[row["lemma_slp1"]] = r
            maxrank = max(maxrank, r)
    return ranks, maxrank


def load_morph_shares():
    shares = {}
    minshare = 1.0
    with open(MORPH_TSV, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            sh = float(row["share_pct"]) / 100.0
            shares[row["signature"]] = sh
            if sh > 0:
                minshare = min(minshare, sh)
    return shares, minshare


def whitespace_chunks(text):
    return len([c for c in re.split(r"\s+", text.strip()) if c])


def load_pack(path):
    """Read a reading pack from .json, or from the .js viewer payload
    (window.READING_DATA["slug"] = {...};)."""
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    txt = path.read_text(encoding="utf-8")
    i = txt.find("= {")
    j = txt.rfind("};")
    if i < 0 or j < 0:
        raise ValueError(f"cannot parse pack payload from {path}")
    return json.loads(txt[i + 2:j + 1])


def ud_coverage(pack):
    """Fraction of tokens carrying a UD upos. The morphology + compound axes both
    read the UD `morph`/`upos` fields; packs built by build_reading_pack_gita.py
    from a non-UD source leave them empty, so scoring them would fabricate
    morph=1.0 / compound=0 from missing data. Such packs are SKIPPED, not
    silently mis-scored (the 'no fabricated signal' rule)."""
    toks = [t for s in pack["sentences"] for t in s["tokens"]]
    if not toks:
        return 0.0
    return sum(1 for t in toks if (t.get("upos") or "").strip()) / len(toks)


def score_pack(pack, vocab_ranks, maxrank, morph_shares, minshare):
    log_maxrank = math.log10(maxrank + 1)
    max_surprisal = -math.log10(minshare)
    v_sum = v_n = 0.0            # vocab, over content tokens
    m_sum = m_n = 0.0            # morph, over all non-punct tokens
    c_hit = c_n = 0             # compound, over all non-punct tokens
    lost = tok_total = 0        # sandhi, per sentence
    for s in pack["sentences"]:
        toks = s["tokens"]
        n = len(toks)
        tok_total += n
        chunks = whitespace_chunks(s.get("text", ""))
        # boundaries fused = tokens that did not survive as their own whitespace chunk
        lost += max(0, n - chunks)
        for t in toks:
            upos = t.get("upos") or "-"
            if upos in PUNCT_UPOS:
                continue
            morph = t.get("morph", "") or ""
            # MORPH axis
            sh = morph_shares.get(f"{upos}|{morph}")
            surprisal = max_surprisal if sh is None else -math.log10(sh)
            m_sum += min(1.0, surprisal / max_surprisal)
            m_n += 1
            # COMPOUND axis (DCS Cpd member)
            c_n += 1
            if morph == "Cpd" or morph.split(" ")[0] == "Cpd":
                c_hit += 1
            # VOCAB axis — content words only
            if upos not in FUNCTION_UPOS:
                lemma = t.get("lemma") or ""
                r = vocab_ranks.get(to_slp1(lemma)) if lemma else None
                v = 1.0 if r is None else min(1.0, math.log10(r) / log_maxrank)
                v_sum += v
                v_n += 1
    return {
        "vocab": round(v_sum / v_n, 4) if v_n else 0.0,
        "sandhi": round(min(1.0, lost / tok_total), 4) if tok_total else 0.0,
        "morphology": round(m_sum / m_n, 4) if m_n else 0.0,
        "compound": round(c_hit / c_n, 4) if c_n else 0.0,
        "content_tokens": v_n,
        "tokens": tok_total,
        "sentences": len(pack["sentences"]),
    }


def composite(sub, w):
    return round(
        w["vocab"] * sub["vocab"] + w["sandhi"] * sub["sandhi"]
        + w["morphology"] * sub["morphology"] + w["compound"] * sub["compound"], 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--packs", default=str(ROOT / "reading" / "data"))
    ap.add_argument("--emit-page", action="store_true", default=True)
    args = ap.parse_args()

    write_default_weights()
    w, w_raw = load_weights()
    vocab_ranks, maxrank = load_vocab_ranks()
    morph_shares, minshare = load_morph_shares()

    pack_dir = Path(args.packs)
    # Prefer .json; fall back to .js for packs that only ship the viewer payload
    # (the Gītā packs). One row per slug, never both formats.
    seen, paths = set(), []
    for p in sorted(pack_dir.glob("*.json")):
        seen.add(p.stem)
        paths.append(p)
    for p in sorted(pack_dir.glob("*.js")):
        if p.stem not in seen:
            paths.append(p)

    rows, skipped = [], []
    for p in paths:
        pack = load_pack(p)
        cov = ud_coverage(pack)
        if cov < 0.5:
            skipped.append((pack.get("slug", p.stem), round(cov, 3)))
            continue
        sub = score_pack(pack, vocab_ranks, maxrank, morph_shares, minshare)
        rows.append({
            "slug": pack.get("slug", p.stem),
            "title": pack.get("title", p.stem),
            "difficulty": composite(sub, w),
            **sub,
        })
    rows.sort(key=lambda r: r["difficulty"])
    for i, r in enumerate(rows, 1):
        r["order"] = i

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    cols = ["order", "slug", "difficulty", "vocab", "sandhi", "morphology",
            "compound", "content_tokens", "tokens", "sentences", "title"]
    with open(OUT_TSV, "w", encoding="utf-8", newline="") as f:
        wtr = csv.DictWriter(f, fieldnames=cols, delimiter="\t", lineterminator="\n")
        wtr.writeheader()
        for r in rows:
            wtr.writerow({k: r[k] for k in cols})
    OUT_JSON.write_text(json.dumps(
        {"weights": w_raw, "weights_normalised": w, "packs": rows},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    write_methods(w_raw, w, rows, maxrank, len(morph_shares))
    if args.emit_page:
        write_page(w_raw, rows)

    print(f"scored {len(rows)} reading packs -> {OUT_TSV.name}")
    if skipped:
        print(f"skipped {len(skipped)} pack(s) lacking UD morphology "
              f"(non-UD source, would fabricate morph/compound): "
              + ", ".join(f"{s}({c})" for s, c in skipped))
    print(f"weights (normalised): {w}")
    print(f"{'ord':>3}  {'slug':<16} {'diff':>6}  {'voc':>5} {'san':>5} {'mor':>5} {'cpd':>5}")
    for r in rows:
        print(f"{r['order']:>3}  {r['slug']:<16} {r['difficulty']:>6}  "
              f"{r['vocab']:>5} {r['sandhi']:>5} {r['morphology']:>5} {r['compound']:>5}")


def write_methods(w_raw, w, rows, maxrank, n_sigs):
    lines = [
        "# Reading-pack difficulty scorer — methods\n",
        "_Auto-generated by `scripts/build_difficulty_scorer.py` (W2a, H949)._\n",
        "This scores each kosha reading pack for **reading difficulty** and orders the",
        "packs into a graded sequence. It is **one estimator, not a ground truth** —",
        "the weighting is a modelling choice and a human should confirm it "
        "(VERIFICATION R5).\n",
        "## Formula\n",
        "```",
        "difficulty = w_vocab·VOCAB + w_sandhi·SANDHI + w_morph·MORPH + w_compound·COMPOUND",
        "```",
        "Each axis is a load in [0,1]; the composite is therefore in [0,1]. Current "
        "weights (normalised to sum to 1):\n",
        "| axis | weight | what it measures |",
        "|---|---:|---|",
        f"| VOCAB | {w['vocab']:.3f} | mean `log10(rank)/log10({maxrank})` of content "
        "lemmas, from `lemma_frequency.tsv` (W1b); unseen lemma = 1.0 |",
        f"| SANDHI | {w['sandhi']:.3f} | fraction of word-boundaries fused by sandhi "
        "= (tokens − whitespace chunks)/tokens, per sentence |",
        f"| MORPH | {w['morphology']:.3f} | mean surprisal of each token's "
        f"`upos\\|morph` form over {n_sigs} corpus signatures "
        "(`morph_signature_freq.tsv`) |",
        f"| COMPOUND | {w['compound']:.3f} | share of tokens that are compound members "
        "(DCS `feat_case=Cpd`) |",
        "",
        f"Raw (pre-normalisation) weights as stored: `{json.dumps(w_raw)}`. "
        "Tune them in [`difficulty_weights.json`](difficulty_weights.json).\n",
        "## Limitations (honest)\n",
        "- **Frequency ≠ learnability** (VERIFICATION R6): a rare lemma is not always a "
        "hard one, and this measures *text properties*, not measured learning gain.",
        "- **Sandhi is a boundary-fusion proxy**, not the induced-rule density the sandhi "
        "programme computes; it needs no per-text sweep, so it works on any new pack, "
        "but it cannot tell an easy vowel-coalescence from a hard consonant cluster.",
        "- **Vocab and compound partly correlate** — a compound member is also counted "
        "in its form signature; the weights account for this only crudely.",
        "- **Ordering is relative** to the packs scored; adding packs can shift ranks.\n",
        "## Current ordering (easiest → hardest)\n",
        "| # | pack | difficulty | vocab | sandhi | morph | compound |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['order']} | {r['slug']} | **{r['difficulty']}** | {r['vocab']} | "
            f"{r['sandhi']} | {r['morphology']} | {r['compound']} |")
    lines += ["", "_Dr. Mārcis Gasūns_"]
    METHODS_MD.write_text("\n".join(lines), encoding="utf-8")


def write_page(w_raw, rows):
    PAGE_HTML.parent.mkdir(parents=True, exist_ok=True)
    tr = []
    for r in rows:
        bar = int(round(r["difficulty"] * 100))
        tr.append(
            f'<tr><td class="ord">{r["order"]}</td>'
            f'<td class="slug">{r["slug"]}</td>'
            f'<td class="ti">{r["title"]}</td>'
            f'<td class="num"><span class="bar" style="--p:{bar}%"></span>'
            f'<b>{r["difficulty"]:.3f}</b></td>'
            f'<td class="num">{r["vocab"]:.3f}</td><td class="num">{r["sandhi"]:.3f}</td>'
            f'<td class="num">{r["morphology"]:.3f}</td><td class="num">{r["compound"]:.3f}</td>'
            f'<td class="num">{r["tokens"]}</td></tr>')
    html = PAGE_TEMPLATE.replace("{{ROWS}}", "\n".join(tr)).replace(
        "{{WEIGHTS}}", ", ".join(f"{k} {v}" for k, v in w_raw.items()))
    PAGE_HTML.write_text(html, encoding="utf-8", newline="\n")


PAGE_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reading packs by difficulty — kosha</title>
<style>
:root{--bg:#fff;--fg:#1a1a1a;--mut:#666;--line:#e2e2e2;--bar:#c9def5;--accent:#2b6cb0}
@media(prefers-color-scheme:dark){:root{--bg:#15171a;--fg:#e8e8e8;--mut:#9aa0a6;--line:#2c2f34;--bar:#274b6d;--accent:#7fb0e0}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:960px;margin:0 auto;padding:2rem 1rem}
h1{font-size:1.5rem;margin:0 0 .25rem}
p.sub{color:var(--mut);margin:.25rem 0 1.5rem}
.wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{padding:.5rem .55rem;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}
th{font-weight:600;color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.03em}
td.num{text-align:right;font-variant-numeric:tabular-nums;position:relative}
td.ord{color:var(--mut);text-align:right}
td.ti{white-space:normal;color:var(--mut);font-size:13px}
td.slug{font-weight:600}
.bar{position:absolute;left:0;top:50%;transform:translateY(-50%);height:70%;width:var(--p);
     background:var(--bar);border-radius:3px;z-index:0}
td.num b{position:relative;z-index:1}
.note{color:var(--mut);font-size:13px;margin-top:1.5rem;border-top:1px solid var(--line);padding-top:1rem}
code{background:rgba(128,128,128,.15);padding:.1em .35em;border-radius:4px;font-size:.9em}
</style></head>
<body><main>
<h1>Reading packs by difficulty</h1>
<p class="sub">kosha pedagogy · W2a difficulty scorer — a graded reading sequence, easiest first.
Score is one estimator on four axes (weights: {{WEIGHTS}}), not a ground truth.</p>
<div class="wrap"><table>
<thead><tr><th>#</th><th>pack</th><th>title</th><th>difficulty</th><th>vocab</th>
<th>sandhi</th><th>morph</th><th>compound</th><th>tokens</th></tr></thead>
<tbody>
{{ROWS}}
</tbody></table></div>
<p class="note">Axes — <b>vocab</b>: lemma corpus-rarity · <b>sandhi</b>: word-boundary
fusion density · <b>morph</b>: morphological-form rarity · <b>compound</b>: share of
compound members (DCS <code>Cpd</code>). Method + limitations:
<code>data/difficulty/METHODS.md</code>. Weights are tunable in
<code>data/difficulty/difficulty_weights.json</code> — a human should confirm them.</p>
</main></body></html>
"""


if __name__ == "__main__":
    main()
