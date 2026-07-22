#!/usr/bin/env python
"""Shared PWG per-sense <ls>-loci primitives for the H1455 sense-reconciliation
layer (kosha wave-1). Owned here, imported by both select_sense_pilot.py
(Step 0) and build_sense_corpus_concordance.py (Steps 1-6) so the leaf-sense
model and the <ls> resolver exist in exactly one place.

Input contract (H1456 export, ARCHITECTURE_KOSHA_SENSE_RECONCILIATION.md):
  pwg_sense_loci.tsv  columns  slp1 \t hom \t sense_id \t gloss_de \t ls_loci
  sense_id  = microstructure sense path ('1', '1a', '1b', '3a' ...)
  ls_loci   = that sense's <ls> citation strings, ';'-joined verbatim.

Two things this module owns:

  * load_pwg_senses()  — group rows by (slp1, hom), merge PWG Nachträge
    duplicate-sense rows (same key contributes an ADDITIONAL row, per the
    H1456 leaf_senses() docstring — we UNION their loci), and mark leaf
    senses (a sense_id is a leaf iff no other sense_id in the group extends
    it, e.g. '1' is not a leaf when '1a' exists).

  * resolve_ls() — split one raw <ls> string into (source_abbrev, locus) and
    resolve the abbreviation to its bibliographic source name via the
    canonical RussianTranslation/src/pwg_sources.py (pwgbib.txt, 98.9% of PWG
    <ls> citations — REUSE, never re-derive the abbrev table). The
    <ls>-resolution rate this yields IS the wave-1 acceptance metric (A2).

No network, deterministic.
"""
import collections
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GH = ROOT.parent if (ROOT.parent / "VisualDCS").exists() else ROOT.parent.parent

# Canonical <ls> abbrev resolver — the same pwg_sources.py H1456's export and
# ARCHITECTURE step 2 name. Import it from the sibling RussianTranslation
# checkout (SanskritLexicography); fall back gracefully if unavailable so the
# build can still run the reuse-only tiers (autonomy-contract stop-condition a).
_PWG_SRC_DIRS = [
    GH / "SanskritLexicography" / "RussianTranslation" / "src",
    GH / "SanskritLexicography-h1455exp-1390" / "RussianTranslation" / "src",
]
pwg_sources = None
for _d in _PWG_SRC_DIRS:
    if (_d / "pwg_sources.py").exists():
        sys.path.insert(0, str(_d))
        try:
            import pwg_sources as _ps  # noqa: E402
            pwg_sources = _ps
            break
        except Exception:  # pragma: no cover - defensive
            pwg_sources = None

DEFAULT_INPUT = ROOT / "data" / "concordance" / "pwg_sense_loci.tsv"
SAMPLE_INPUT = GH / "SanskritLexicography" / "RussianTranslation" / "src" / "pwg_sense_loci.sample.tsv"

# A leading sense marker the export left on the gloss, e.g. "a〉 " / "1〉 " / "1. ".
_MARK = re.compile(r"^\s*(?:\d{1,2}|[a-z])[)〉.]\s*")
# The token that starts the numeric locus part of an <ls> string: contains a
# digit (12,3630 / 4,111 / t.203). Everything before it is the source abbrev.
_HAS_DIGIT = re.compile(r"\d")


class Sense:
    __slots__ = ("slp1", "hom", "sense_id", "gloss_de", "ls_raw", "is_leaf")

    def __init__(self, slp1, hom, sense_id, gloss_de, ls_raw):
        self.slp1 = slp1
        self.hom = hom
        self.sense_id = sense_id
        self.gloss_de = gloss_de
        self.ls_raw = ls_raw          # list of raw <ls> strings (deduped, order-stable)
        self.is_leaf = True

    def gloss_clean(self):
        return _MARK.sub("", self.gloss_de or "").strip()


def load_pwg_senses(path=None):
    """-> OrderedDict {(slp1, hom): [Sense, ...]} with is_leaf marked.

    Rows are grouped by (slp1, hom). Duplicate sense_ids within a group (PWG
    Nachträge back-references) are merged: glosses concatenated once, <ls>
    loci unioned order-stably. Leaf marking is per group."""
    if path is None:
        path = DEFAULT_INPUT if DEFAULT_INPUT.exists() else SAMPLE_INPUT
    path = Path(path)
    groups = collections.OrderedDict()
    by_id = {}  # (slp1,hom,sense_id) -> Sense, for Nachträge merge
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        idx = {c: i for i, c in enumerate(header)}
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 5:
                p += [""] * (5 - len(p))
            slp1, hom, sid = p[idx["slp1"]], p[idx["hom"]], p[idx["sense_id"]]
            gloss, ls = p[idx["gloss_de"]], p[idx["ls_loci"]]
            key = (slp1, hom)
            ls_list = [s for s in (ls.split(";") if ls else []) if s.strip()]
            mk = (slp1, hom, sid)
            if mk in by_id:                       # Nachträge merge (union loci)
                s = by_id[mk]
                for x in ls_list:
                    if x not in s.ls_raw:
                        s.ls_raw.append(x)
                if gloss and gloss not in s.gloss_de:
                    s.gloss_de = (s.gloss_de + " / " + gloss) if s.gloss_de else gloss
                continue
            s = Sense(slp1, hom, sid, gloss, ls_list)
            by_id[mk] = s
            groups.setdefault(key, []).append(s)
    # mark leaves per group
    for senses in groups.values():
        ids = [s.sense_id for s in senses]
        for s in senses:
            sid = s.sense_id
            s.is_leaf = not any(o != sid and o.startswith(sid) and len(o) > len(sid)
                                for o in ids)
    return groups


def leaves(senses):
    return [s for s in senses if s.is_leaf]


def split_ls(ls_raw):
    """Split one raw <ls> string into (source_abbrev, locus).

    'MBH. 12,3630' -> ('MBH.', '12,3630'); 'PAÑCAT. 116,19' -> ('PAÑCAT.',
    '116,19'); 'H. an. 4,111' -> ('H. an.', '4,111'); 'MED' -> ('MED', '')."""
    toks = ls_raw.split()
    src, loc = [], []
    hit = False
    for t in toks:
        if not hit and _HAS_DIGIT.search(t):
            hit = True
        (loc if hit else src).append(t)
    return " ".join(src).strip(), " ".join(loc).strip()


def resolve_ls(ls_raw):
    """-> dict(raw, source_abbrev, locus, resolved, source_name).

    resolved is True iff pwg_sources.resolve() maps the abbrev to a
    bibliographic source (the A2 acceptance signal)."""
    abbrev, locus = split_ls(ls_raw)
    name = None
    if pwg_sources is not None:
        try:
            name = pwg_sources.resolve(abbrev if abbrev else ls_raw)
        except Exception:  # pragma: no cover
            name = None
    return {
        "raw": ls_raw,
        "source_abbrev": abbrev or ls_raw.strip(),
        "locus": locus,
        "resolved": name is not None,
        "source_name": name,
    }


# Content-token extraction for the gloss-overlap tier (Step 3 (ii)). We key on
# high-precision, language-agnostic shared tokens — capitalised proper names,
# Latin botanical/zoological binomials, and digits — which are IDENTICAL across
# PWG's German gloss and DCS's English `meanings`, plus lower-cased alpha
# content words >=4 chars that are not stop-words in either language. This
# keeps the overlap tier honest across the DE/EN gloss-language gap
# (VERIFICATION risk row 2).
_STOP = set("""
und der die das ein eine einer eines von zu im in mit auf als oder aber auch
nach bei ist sind war dem den des durch fuer für über unter vor nur noch wie
the and for with from that this name kind sort adj comp masc fem neutr pra
einer eines etwas welche welches hier statt dieser diese dieses sich nach
""".split())
_WORD = re.compile(r"[A-Za-zĀāĪīŪūṚṛṜṝḶḷṄṅÑñṬṭḌḍṆṇŚśṢṣḤḥṂṃ]{2,}")
_NUM = re.compile(r"\b\d{1,4}\b")


def content_tokens(text):
    """High-signal tokens for overlap: proper-noun/binomial tokens (capitalised
    or containing IAST diacritics), digits, and >=4-char non-stop alpha words."""
    if not text:
        return set()
    out = set()
    for m in _WORD.finditer(text):
        w = m.group(0)
        wl = w.lower()
        cap = w[0].isupper()
        diac = any(ord(c) > 127 for c in w)
        if cap or diac:
            out.add(wl)                      # proper noun / binomial / IAST term
        elif len(w) >= 4 and wl not in _STOP:
            out.add(wl)
    for m in _NUM.finditer(text):
        out.add(m.group(0))
    return out - _STOP
