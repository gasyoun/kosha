#!/usr/bin/env python
"""Build the inline Sa->Ru gloss layer for kosha reading packs (W-RU-a / H1278).

Joins every reading-pack token to the three ranked **public site-tier** layers of
the [SanskritRussian](https://github.com/gasyoun/SanskritRussian) glossary so a
Russian-speaking learner can hover a word and read its meaning. Additive: the
existing English `gloss` on each token is left untouched; the RU layer is keyed
separately (`gloss_ru`).

RIGHTS GATE (PLAN decision 14). Published RU glosses come ONLY from SanskritRussian's
public, GitHub-Pages-served layers -- `surface_glossary.tsv` / `lemma_glossary.tsv` /
`root_glossary.tsv` (+ the public `dcs_lemma2root.tsv` map). The restricted upstream
alignment (`RussianTranslation/src/corpus_lexicon.jsonl`) is NEVER read here.

Join (per token):
  * surface_ru : to_slp1(token.form)  -> surface_glossary[form_slp1].ru
  * lemma_ru   : token.slp1 (the lemma SLP1 the pack already carries) or
                 to_slp1(token.lemma) -> lemma_glossary[lemma_slp1].ru
  * root_ru    : lemma_slp1 -> dcs_lemma2root[lemma_slp1] -> root_glossary[root_slp1].ru
                 (verbal roots only; nominal stems have no root layer by design)
Keys strip a leading avagraha/apostrophe on both sides (per the SanskritRussian
README join discipline: `'gacchat` == `gacchat`).

Outputs:
  * data/ru_gloss/ru_gloss_layer.tsv   one row per (pack, sentence, token index):
        pack, sent_n, sent_sub, tok_idx, form_slp1, surface_ru, lemma_ru, root_ru, layer_hit
  * a per-pack coverage summary on stdout (the numbers stage 5 folds into BUILD_REPORT.md)

Also importable: `load_layers()` + `ru_gloss(form_iast, lemma_iast, lemma_slp1)` are the
join primitives that `build_reading_pack.py --gloss-lang ru` consumes to inline `gloss_ru`.

Deterministic, stdlib-only, no network. Consumes `to_slp1` from concordance_core
(SHARED_CODE discipline -- never re-implement the transcoder).
"""
import argparse
import collections
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from concordance_core import to_slp1  # noqa: E402

GH = ROOT.parent if (ROOT.parent / "SanskritRussian").exists() else ROOT.parent.parent
SR = GH / "SanskritRussian"
SURFACE_TSV = SR / "surface_glossary.tsv"
LEMMA_TSV = SR / "lemma_glossary.tsv"
ROOT_TSV = SR / "root_glossary.tsv"
LEMMA2ROOT_TSV = SR / "dcs_lemma2root.tsv"

READ_DIR = ROOT / "reading" / "data"
OUT_DIR = ROOT / "data" / "ru_gloss"
OUT_TSV = OUT_DIR / "ru_gloss_layer.tsv"

_AVAGRAHA = "'’ऽ"


def _dekey(s):
    """Normalise a join key: lower avagraha/apostrophe stripped from the left."""
    return (s or "").lstrip(_AVAGRAHA)


def _load_tsv_map(path, key_col, val_col):
    """First-wins map key->val over a TSV (the glossaries are already one row per key,
    ranked; first row is the top-ranked rendering)."""
    m = {}
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        ki, vi = header.index(key_col), header.index(val_col)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) <= max(ki, vi):
                continue
            k = _dekey(p[ki])
            if k and k not in m:
                m[k] = p[vi]
    return m


def load_layers():
    """Return (surface, lemma, root, lemma2root) join maps from the public tier."""
    surface = _load_tsv_map(SURFACE_TSV, "form_slp1", "ru")
    lemma = _load_tsv_map(LEMMA_TSV, "lemma_slp1", "ru")
    root = _load_tsv_map(ROOT_TSV, "root_slp1", "ru")
    lemma2root = _load_tsv_map(LEMMA2ROOT_TSV, "lemma_slp1", "root_slp1")
    return surface, lemma, root, lemma2root


class RuGlosser:
    """Loaded-once join primitive; call `.gloss(form_iast, lemma_iast, lemma_slp1)`."""

    def __init__(self):
        self.surface, self.lemma, self.root, self.lemma2root = load_layers()

    def gloss(self, form_iast, lemma_iast=None, lemma_slp1=None):
        surf_key = _dekey(to_slp1(form_iast or ""))
        surface_ru = self.surface.get(surf_key)
        lem_slp1 = _dekey(lemma_slp1 or to_slp1(lemma_iast or ""))
        lemma_ru = self.lemma.get(lem_slp1)
        root_ru = None
        root_slp1 = self.lemma2root.get(lem_slp1)
        if root_slp1:
            root_ru = self.root.get(_dekey(root_slp1))
        hits = [name for name, v in (("surface", surface_ru), ("lemma", lemma_ru),
                                     ("root", root_ru)) if v]
        return {
            "surface_ru": surface_ru,
            "lemma_ru": lemma_ru,
            "root_ru": root_ru,
            "layer_hit": "+".join(hits) if hits else "none",
        }


def pack_files():
    """The reading-pack JSONs (skip any non-pack json in the dir)."""
    out = []
    for p in sorted(READ_DIR.glob("*.json")):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(obj, dict) and "sentences" in obj and "slug" in obj:
            out.append((p, obj))
    return out


def token_rows(pack, glosser):
    """Yield (sent_n, sent_sub, tok_idx, form_slp1, tok, rugloss_dict) for each token."""
    for sent in pack.get("sentences", []):
        for i, tok in enumerate(sent.get("tokens", [])):
            form = tok.get("form", "")
            rg = glosser.gloss(form, tok.get("lemma"), tok.get("slp1"))
            yield (sent.get("n"), sent.get("sub"), i, to_slp1(_dekey(form)), tok, rg)


COVERAGE_MD = ROOT / "reading" / "RU_GLOSS_COVERAGE.md"


def write_coverage_report(per_pack, uncovered):
    """Durable RU-coverage report. NOT reading/BUILD_REPORT.md: that file is regenerated
    per-pack by build_reading_pack.py (single-pack, overwritten), so a RU section appended
    there is lost on the next pack build. A dedicated, self-identifying file survives."""
    L = ["# Reading packs — Russian gloss coverage (W-RU-a / H1278)", "",
         "_Auto-generated by `scripts/build_ru_gloss_layer.py` (Opus 4.8 `claude-opus-4-8`). "
         "RU glosses from the SanskritRussian **public site-tier** subset only "
         "(surface/lemma/root glossaries); the restricted `corpus_lexicon` is not read._", "",
         "_Created: 19-07-2026 · Last updated: 19-07-2026_", "",
         "Coverage = share of pack tokens carrying a **lemma-layer** RU gloss (the layer a "
         "learner reads); the surface and root layers add nuance where present. High coverage "
         "here is the measurable finding that the public subset suffices — no rights unlock "
         "is needed for these texts.", "",
         "| Pack | tokens | lemma-RU | coverage |", "|---|---:|---:|---:|"]
    tot_all = hit_all = 0
    for slug, (tot, hit) in per_pack.items():
        tot_all += tot
        hit_all += hit
        L.append("| `%s` | %d | %d | %.1f%% |" % (slug, tot, hit, 100.0 * hit / tot if tot else 0.0))
    L.append("| **all** | **%d** | **%d** | **%.1f%%** |"
             % (tot_all, hit_all, 100.0 * hit_all / tot_all if tot_all else 0.0))
    L += ["", "## Top-20 uncovered lemmas (no lemma-layer RU gloss)", "",
          "The residue is the rare long tail (proper names, sandhi-altered stems, "
          "causatives) SanskritRussian's own failure typology already characterises.", "",
          "| Lemma (IAST) | SLP1 | occurrences |", "|---|---|---:|"]
    for (lem, slp1), cnt in sorted(uncovered.items(), key=lambda x: (-x[1], x[0]))[:20]:
        L.append("| %s | `%s` | %d |" % (lem or "∅", slp1, cnt))
    L += ["", "_Dr. Mārcis Gasūns_"]
    COVERAGE_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote coverage report -> %s" % COVERAGE_MD, file=sys.stderr)


def inline_token_ru(tok, glosser):
    """Add an additive `gloss_ru` object to ONE pack token (surface/lemma/root, only
    the non-null keys). Leaves the English `gloss` untouched. Returns True if a gloss
    was attached. Idempotent: recomputed and overwritten on every pass, so a re-run is
    byte-stable."""
    rg = glosser.gloss(tok.get("form", ""), tok.get("lemma"), tok.get("slp1"))
    obj = {}
    if rg["surface_ru"]:
        obj["surface"] = rg["surface_ru"]
    if rg["lemma_ru"]:
        obj["lemma"] = rg["lemma_ru"]
    if rg["root_ru"]:
        obj["root"] = rg["root_ru"]
    if obj:
        tok["gloss_ru"] = obj
        return True
    tok.pop("gloss_ru", None)
    return False


def inline_packs_ru(glosser=None):
    """Additive post-pass: read every committed reading pack, attach `gloss_ru` to each
    token, and rewrite its `.json` + `.js` byte-for-byte the way build_reading_pack.py
    does (indent=1, the two-line window.READING_DATA wrapper). This is what
    `build_reading_pack.py --gloss-lang ru` calls; the English layer is never touched."""
    glosser = glosser or RuGlosser()
    touched = []
    for path, pack in pack_files():
        n_glossed = 0
        for sent in pack.get("sentences", []):
            for tok in sent.get("tokens", []):
                if inline_token_ru(tok, glosser):
                    n_glossed += 1
        pack["gloss_langs"] = sorted(set((pack.get("gloss_langs") or []) + ["ru"]))
        body = json.dumps(pack, ensure_ascii=False, indent=1)
        # Match build_reading_pack.py byte-for-byte: LF blob (newline="\n"), body + "\n".
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(body + "\n")
        js = path.with_suffix(".js")
        with open(js, "w", encoding="utf-8", newline="\n") as f:
            f.write("window.READING_DATA = window.READING_DATA || {};\n")
            f.write('window.READING_DATA["%s"] = %s;\n' % (pack["slug"], body))
        touched.append((pack["slug"], n_glossed))
        print("inlined gloss_ru into %-18s (%d tokens)" % (pack["slug"], n_glossed),
              file=sys.stderr)
    return touched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_TSV))
    ap.add_argument("--inline", action="store_true",
                    help="also write gloss_ru into the pack .json/.js in place (additive)")
    args = ap.parse_args()

    glosser = RuGlosser()
    print("layers: surface=%d lemma=%d root=%d lemma2root=%d"
          % (len(glosser.surface), len(glosser.lemma), len(glosser.root),
             len(glosser.lemma2root)), file=sys.stderr)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    header = ["pack", "sent_n", "sent_sub", "tok_idx", "form_slp1",
              "surface_ru", "lemma_ru", "root_ru", "layer_hit"]
    packs = pack_files()
    n_rows = 0
    per_pack = collections.OrderedDict()
    uncovered = collections.Counter()
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(header) + "\n")
        for path, pack in packs:
            slug = pack["slug"]
            tot = lemma_hit = 0
            for sent_n, sent_sub, ti, form_slp1, tok, rg in token_rows(pack, glosser):
                tot += 1
                if rg["lemma_ru"]:
                    lemma_hit += 1
                else:
                    uncovered[(tok.get("lemma"), _dekey(tok.get("slp1") or to_slp1(tok.get("lemma") or "")))] += 1
                f.write("\t".join([
                    slug, str(sent_n or ""), str(sent_sub or ""), str(ti), form_slp1,
                    rg["surface_ru"] or "", rg["lemma_ru"] or "", rg["root_ru"] or "",
                    rg["layer_hit"]]) + "\n")
                n_rows += 1
            per_pack[slug] = (tot, lemma_hit)
    print("wrote %d rows -> %s" % (n_rows, args.out), file=sys.stderr)
    write_coverage_report(per_pack, uncovered)
    print("\n%-20s %8s %8s %8s" % ("pack", "tokens", "lemma_ru", "cov%"), file=sys.stderr)
    for slug, (tot, hit) in per_pack.items():
        print("%-20s %8d %8d %7.1f%%"
              % (slug, tot, hit, 100.0 * hit / tot if tot else 0.0), file=sys.stderr)

    if args.inline:
        inline_packs_ru(glosser)


if __name__ == "__main__":
    main()
