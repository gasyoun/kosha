#!/usr/bin/env python
"""GRETIL sandhi extension — roadmap Phase 3 (method C per §2 item 3), gated.

Roadmap CORPUS_SANDHI_PEDAGOGY_2026_2027 §4: "GRETIL is raw, unanalyzed,
mixed-encoding, mixed-license. Every text needs a splitter run (method B/C — no
Unsandhied= gold), so it inherits Phase-1's validated pipeline. Gate each text
through /publish-safety-check for license before ingest." §2 item 3 verdict:
**method C** (DharmaMitra neural splitter, far outperformed method B), reusing
`compare_sandhi_methods._dm_segment` verbatim (batched, retried, cached under
data/sandhi/_cache/ so re-runs never re-hit the network).

What is new here (the GRETIL-specific half DCS never needed):

  1. **License gate (fail-closed).** A text is ingestable only if
     `data/sandhi/gretil/licenses.tsv` carries a per-text verdict row whose
     license is in ALLOWED_LICENSES **and** whose verdict is
     `allowed-public-tier`, and — when the input file states its own license —
     the two must agree. kosha's data posture (LICENSE-DATA.md) forbids adding
     a non-commercial restriction to the CC BY-SA data tier, so GRETIL's
     current CC BY-NC-SA 4.0 surfaces are refused BY THE GATE, with the
     verdict recorded (this is the gate working, not a failure of it). A
     restricted-tier or permission-letter path is a human rights decision and
     is deliberately out of scope here.

  2. **GRETIL plaintext parser.** GRETIL corpustei plaintexts (the current
     canonical surface, e.g.
     `corpustei/transformations/plaintext/sa_kathopaniSad.txt`) carry a
     `# Text` marker, a license header before it, IAST-Unicode bodies with
     pāda lines ending in `/` or `//`, and inlined refs like `kau_1.1 //`.
     Units are pāda-length strings (sandhi is induced within a unit only).
     Legacy HTML and Devanagari files are accepted via `--input` too: the
     cleaner strips markup/metadata characters, and Devanagari units are
     transliterated (vidyut) to IAST. `--from-dcs <text>` instead feeds the
     raw `# text =` lines of a DCS CoNLL-U text — the license-clean
     validation path (see below).

  3. **Free-text junction aligner.** DCS mode-1/2 inducers read junctions off
     per-token FORM/Unsandhied pairs; GRETIL has only the continuous sandhied
     string. For each adjacent predicted-token pair the aligner locates the
     junction in the surface: stable head of the left token, then the smallest
     merged-output length k ≤ 4 under two hypotheses — (a) right word's first
     phoneme fully merged (vowel coalescence → `induce_coalescence`, tried
     FIRST when that phoneme is a vowel) vs (b) it survives (`induce_rule`,
     tried first for consonants — `ḥ t → s t`, `m p → ṃ p` notation). The
     hand-table avagraha class (`e a → e '`, `aḥ ā → o '`) is normalised to
     the spaced notation. A unit whose alignment does not close is skipped
     whole and counted (`align_fail`), the same skip-and-count policy as
     methods B/C.

Outputs: `data/sandhi/gretil/<slug>_sandhi.tsv` — the Gītā schema
(rule · category · count · pct · examples). The DCS-gold merged table
`data/sandhi/corpus_sandhi.tsv` is deliberately NOT extended by method-C rows:
the curriculum backbone stays gold-derived; GRETIL tables land separately
until (if) a merged GRETIL corpus is ruled in.

Validation (offline, license-clean): `--validate-dcs "Amaruśataka"` runs this
pipeline's splitter+aligner over the SAME DCS raw lines method C was scored on
(H908) and scores the induced rule inventory against method A's gold-split
inventory on the same text (rule-set precision/recall/F1) — the GRETIL-shape
path proven without ingesting any GRETIL bytes.

Public/MIT, credit Dr. Mārcis Gasūns.

Usage:
  # license verdicts currently registered (incl. refusals, with receipts)
  python scripts/gretil_sandhi_pipeline.py --check-gate

  # validation vs method A gold on license-clean DCS material (cache-only)
  python scripts/gretil_sandhi_pipeline.py --validate-dcs "Amaruśataka"

  # real GRETIL ingest — refused unless licenses.tsv clears the text
  python scripts/gretil_sandhi_pipeline.py --text-id gretil-kathopanisad \
      --input /path/to/sa_kathopaniSad.txt --allow-network
"""
import argparse
import csv
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import dcs_sandhi_induce as ind  # noqa: E402
import compare_sandhi_methods as csm  # noqa: E402

GRE_DIR = ROOT / "data" / "sandhi" / "gretil"
LICENSES_TSV = GRE_DIR / "licenses.tsv"
OUT_DIR = GRE_DIR

# Licenses a kosha ingest can accept into the public data tier. kosha data
# releases are CC BY-SA 4.0 and LICENSE-DATA.md forbids adding a
# non-commercial restriction, so anything -NC is structurally out.
ALLOWED_LICENSES = {
    "public domain",
    "publicdomain",
    "cc0",
    "cc by",
    "cc by 4.0",
    "cc by 3.0",
    "cc by-sa",
    "cc by-sa 3.0",
    "cc by-sa 4.0",
    "odbl",
}
VERDICT_ALLOWED = "allowed-public-tier"

# units are cleaned to Sanskrit letters + whitespace + avagraha only
_CLEAN_RE = re.compile(
    r"[^A-Za-zāīūṛṝḷḹṅñṭḍṇśṣḥṃṁ'’ ]+")
_DEVA_RE = re.compile(r"[\u0900-\u097F]")
MAX_MERGE = 4  # merged output longer than 3 phonemes is never a real junction


class LicenseRefused(Exception):
    """Raised by gate() — carries the receipt lines the run prints."""

    def __init__(self, text_id, reasons):
        self.text_id = text_id
        self.reasons = reasons
        super().__init__("%s: %s" % (text_id, "; ".join(reasons)))


def _norm_lic(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


# --- license gate (fail-closed, /publish-safety-check for the pipeline) ------
def load_registry():
    if not LICENSES_TSV.exists():
        return {}
    out = {}
    with open(LICENSES_TSV, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            out[row["text_id"]] = row
    return out


def gate(text_id, stated_license=None, registry=None):
    """Raise LicenseRefused unless text_id is cleared for public-tier ingest."""
    reg = registry if registry is not None else load_registry()
    row = reg.get(text_id)
    if row is None:
        raise LicenseRefused(text_id, [
            "no licenses.tsv verdict row — run the /publish-safety-check "
            "license verdict for this text and record it in %s before ingest"
            % (LICENSES_TSV.relative_to(ROOT),)])
    reasons = []
    lic = _norm_lic(row["license"])
    if row["verdict"] != VERDICT_ALLOWED:
        reasons.append("verdict=%r is not %r — %s"
                       % (row["verdict"], VERDICT_ALLOWED, row["note"]))
    if lic not in ALLOWED_LICENSES:
        reasons.append("license %r is not in the public-tier allow-list" % lic)
    stated_n = _norm_lic(stated_license)
    if stated_n and ("noncommercial" in stated_n or "-nc" in stated_n
                     or "nc-" in stated_n):
        reasons.append("input file itself states a NonCommercial license "
                       "(%r) — kosha's data tier is CC BY-SA and may not "
                       "carry an NC restriction (LICENSE-DATA.md)" % stated_n)
    elif stated_n and stated_n != lic:
        reasons.append("input file states license %r but the verdict row "
                       "records %r — refuses a verdict/source mismatch"
                       % (stated_n, lic))
    if reasons:
        raise LicenseRefused(text_id, reasons)
    return row


def check_gate(registry=None):
    reg = registry if registry is not None else load_registry()
    for tid, row in sorted(reg.items()):
        try:
            gate(tid, registry=reg)
            ok = "ALLOWED"
        except LicenseRefused as e:
            ok = "REFUSED (%s)" % e.reasons[0]
        print("%-38s %-28s %s" % (tid, row["license"], ok))
    print("%d registry rows; allow-list: %s" % (len(reg), sorted(ALLOWED_LICENSES)))


# --- GRETIL plaintext parsing ------------------------------------------------
def _clean_unit(chunk):
    """Keep Sanskrit letters + whitespace + avagraha; drop refs/metadata."""
    s = _CLEAN_RE.sub(" ", chunk)
    s = unicodedata.normalize("NFC", re.sub(r"\s+", " ", s)).strip()
    toks = [t for t in s.split(" ") if t]
    if len(toks) < 2:
        return ""
    return s


def parse_gretil_plain(text):
    """Corpustei-plaintext (and tolerant generic) GRETIL parsing.
    Returns (header_text, [units]). Units are pāda-length strings."""
    if "# Text" in text:
        header, body = text.split("# Text", 1)
    else:
        lines = text.splitlines()
        cut = 0
        while cut < len(lines) and lines[cut].lstrip().startswith(("#", "%")):
            cut += 1
        header, body = "\n".join(lines[:cut]), "\n".join(lines[cut:])
    header = header if "# " in header or "%" in header else ""
    units, seen = [], set()
    for chunk in re.split(r"[/|\n]+", body):
        u = _clean_unit(chunk)
        if u and u not in seen:
            seen.add(u)
            units.append(u)
    return header, units


def _to_iast(unit):
    """Devanagari (or already-IAST) unit → IAST via vidyut."""
    if not _DEVA_RE.search(unit):
        return unit
    import vidyut.lipi as lipi
    return lipi.transliterate(unit, lipi.Scheme.Devanagari, lipi.Scheme.Iast)


# --- the free-text junction aligner (the GRETIL-specific inducer) ------------
def _stable_tail_key(word, first_len):
    """Right word minus its first phoneme, minus its (possibly next-junction-
    changed) last phoneme — the stable anchor searched after the merged output."""
    rest = word[first_len:]
    if not rest:
        return ""
    lp = ind.last_phoneme(rest)
    return rest[: len(rest) - len(lp)] or rest


def _head_lens(word):
    """Candidate stable-head lengths for the left token, longest first: minus
    its final phoneme, then minus one more, then one more. The extra fallbacks
    cover merges that eat MORE than the final phoneme — the avagraha class
    (`devaḥ ā → devo 'ste`: `aḥ` → `o` is a two-into-one merge)."""
    out, end = [], len(word)
    for _ in range(3):
        if end <= 0:
            break
        end -= len(ind.last_phoneme(word[:end]))
        out.append(end)
    return out


def _rule_from_merge(lp, rp, merged, st):
    """Assemble the junction rule from the merged surface segment, following
    the hand-table conventions the shared inducer writes (dcs_sandhi_induce.
    induce_coalescence lines 183-197): passthrough = no sandhi; output ending
    in the surviving right phoneme = spaced (`i e → y e`); genuine
    coalescence merged (`a a → ā`, `a e → ai`); the avagraha class spaced per
    the Gītā hand table (`e a → e '`, `aḥ ā → o '`)."""
    merged = re.sub(r"\s+", "", merged)
    if not merged or len(merged) > 3:
        st["induce-skip" if merged else "align_fail"] += 1
        return None
    if merged == lp + rp:
        st["no-sandhi"] += 1
        return None
    if merged.endswith("'") and rp in ("a", "ā") and len(merged) <= 4:
        # e.g. merged "o'" → `ḥ ā → o '`; "e'" → `e a → e '`
        return "%s %s → %s '" % (lp, rp, merged[:-1].strip() or "Ø")
    if merged != rp and len(merged) > len(rp) and merged.endswith(rp):
        return "%s %s → %s %s" % (lp, rp, merged[: len(merged) - len(rp)], rp)
    return "%s %s → %s" % (lp, rp, merged)


def align_induce(tokens, surface, st):
    """Induce junction rules for one unit. `tokens` = predicted pre-sandhi
    tokens (DharmaMitra, IAST); `surface` = the sandhied unit text (whitespace
    removed by the caller). Greedy left-to-right: for each adjacent pair,
    anchor the left token's stable head in the surface (progressively shorter
    fallbacks for multi-phoneme merges, and one more fallback — the left token
    MINUS its first phoneme — right after a hypothesis-(a) junction, whose
    merge consumed that phoneme), then take the smallest merged-output length
    under two hypotheses — (a) right word's first phoneme fully merged (vowel
    coalescence, tried FIRST when that phoneme is a vowel) vs (b) it survives
    (`induce_rule`, first for consonants — `ḥ t → s t`, `m p → ṃ p`). A unit
    that fails to align is skipped whole (returns None) and counted, like
    methods B/C."""
    pos = 0
    rules = []
    prev_absorbed = False
    for i in range(len(tokens) - 1):
        L, R = tokens[i], tokens[i + 1]
        lp, rp = ind.last_phoneme(L), ind.first_phoneme(R)
        if not lp or not rp:
            st["empty-side"] += 1
            return None
        rrest = R[len(rp):]
        key = _stable_tail_key(R, len(rp))
        default_head = len(L) - len(lp)
        found = None
        # after a coalescence junction the surface carries this token minus
        # its first phoneme, so the head anchor retries against that form
        forms = [L]
        if prev_absorbed:
            short = L[len(ind.first_phoneme(L)):]
            if short:
                forms.append(short)
        for form in forms:
            for head_len in _head_lens(form):
                if not surface.startswith(form[:head_len], pos):
                    continue
                base = pos + head_len
                dropped = default_head - head_len
                for k in range(MAX_MERGE + max(dropped, 0) + 1):
                    at = base + k
                    # hypothesis order follows the hand table: vowel
                    # coalescence first for vowel-initial right words
                    # (`a a → ā`), edge-split first otherwise
                    # (`ḥ t → s t`, `m p → ṃ p`). Caps: a real coalescence
                    # merges ≤2 phonemes; a split reading whose merge is EMPTY
                    # with a vowel left phoneme (`a u → Ø u`, `a ā → Ø ā`) is
                    # compound morphology, not sandhi — the hand table's Ø
                    # rows are visarga-only (`ḥ i → Ø i`).
                    hypos = ("a", "b") if rp in ind.VOWELS else ("b", "a")
                    for h in hypos:
                        if h == "a" and k <= 2 and rrest and surface.startswith(key, at):
                            found = (base, k, "a")
                            break
                        if (h == "b" and not (k == 0 and lp in ind.VOWELS)
                                and surface.startswith(rp + key, at)):
                            found = (base, k, "b")
                            break
                    if found:
                        break
                if found:
                    break
            if found:
                break
        if not found:
            st["align_fail"] += 1
            return None
        base, k, hyp = found
        if hyp == "b":
            L_surf = surface[pos:base + k]
            R_surf = surface[base + k: base + k + len(R) + MAX_MERGE]
            rule, flag = ind.induce_rule(L, L_surf, R, R_surf)
            st["junctions"] += 1
            if rule is None:
                st["no-sandhi" if flag == "no-sandhi" else "induce-skip"] += 1
            elif flag == "empty-side":
                st["induce-skip"] += 1
            else:
                rules.append(rule)
        else:
            merged = surface[base:base + k]
            st["junctions"] += 1
            rule = _rule_from_merge(lp, rp, merged, st)
            if rule:
                rules.append(rule)
        pos = base + k
        prev_absorbed = hyp == "a"
    return rules


# --- run the splitter+inducer over units -------------------------------------
_TOKEN_JUNK_RE = re.compile(r"[^a-zāīūṛṝḷḹṅñṭḍṇśṣḥṃṁ']+")


def run_text(units, text_id, allow_network, st, examples):
    sents = list(dict.fromkeys(units))
    dm = csm._dm_segment(sents, text_id, allow_network)
    rules = Counter()
    for u in sents:
        st["units"] += 1
        tokens = dm.get(u)
        if tokens is None:
            st["dm_fail"] += 1
            continue
        # DharmaMitra occasionally echoes verse markers / capitals
        # (`R nāryaḥ`) — sanitize each token to Sanskrit letters, drop empties
        toks = [_TOKEN_JUNK_RE.sub("", t) for t in tokens]
        toks = [t for t in toks if t]
        st["tokens"] += len(toks)
        if len(toks) < 2:
            st["short-unit"] += 1
            continue
        got = align_induce(toks, re.sub(r"\s+", "", u), st)
        if got is None:
            continue
        for rule in got:
            rules[rule] += 1
            if len(examples[rule]) < 4 and rule not in examples[rule]:
                examples[rule].append(u)
    st["distinct_rules"] = len(rules)
    st["events"] = sum(rules.values())
    return rules


def write_tsv(path, rules, examples):
    total = sum(rules.values())
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["rule", "category", "count", "pct", "examples"])
        for rule, n in rules.most_common():
            w.writerow([rule, ind.categorise(rule), n,
                        round(100.0 * n / total, 2) if total else 0,
                        " · ".join(examples[rule])])


# --- entry modes --------------------------------------------------------------
def validate_dcs(dcs_text, allow_network):
    """License-clean end-to-end proof of the GRETIL-shape path: run splitter+
    aligner over the raw `# text =` lines of a DCS text and score the induced
    rule inventory against method A's gold-split inventory on the same text."""
    files = sorted((ind.DEFAULT_DCS / dcs_text).glob("*.conllu"))
    units = [ref for f in files for ref, _w, _m in ind.read_sentences(f) if ref]
    st, examples = Counter(), defaultdict(list)
    mine = run_text(units, ind.slug(dcs_text), allow_network, st, examples)
    gold, _gex, _gst, _fl, _dbg = ind.induce_from_files(files)
    p, r, f1, tp = csm.pr_f1(gold, mine)
    print("=== validate-dcs %s — GRETIL-shape path (method C + aligner) vs "
          "method A gold" % dcs_text)
    print("units %d · tokens %d · junctions %d · events %d · rules %d"
          % (st["units"], st["tokens"], st["junctions"], st["events"],
             st["distinct_rules"]))
    print("skips: align_fail %d · dm_fail %d · no-sandhi %d · induce-skip %d"
          % (st["align_fail"], st["dm_fail"], st["no-sandhi"],
             st["induce-skip"]))
    print("rule inventory vs method A: P=%.3f R=%.3f F1=%.3f (%d shared of "
          "A=%d, mine=%d)" % (p, r, f1, tp, len(gold), len(mine)))
    top = ", ".join("%s(%d)" % (rule, n)
                    for rule, n in mine.most_common(10))
    print("top rules:", top)
    return mine, gold, st


def main():
    ap = argparse.ArgumentParser(
        description="GRETIL sandhi extension — Phase 3, method C, license-gated")
    ap.add_argument("--check-gate", action="store_true",
                    help="print every licenses.tsv verdict and its gate result")
    ap.add_argument("--text-id", help="registry id of the text to ingest")
    ap.add_argument("--input", help="GRETIL plaintext file for --text-id")
    ap.add_argument("--validate-dcs", metavar="DCS_TEXT",
                    help="run over a DCS text's raw lines (no GRETIL bytes) "
                         "and F1-score against method A gold")
    ap.add_argument("--allow-network", action="store_true",
                    help="allow DharmaMitra API calls beyond the committed cache")
    args = ap.parse_args()

    if args.check_gate:
        check_gate()
        return
    if args.validate_dcs:
        validate_dcs(args.validate_dcs, args.allow_network)
        return
    if args.text_id:
        if not args.input:
            ap.error("--text-id needs --input")
        raw = Path(args.input).read_text(encoding="utf-8", errors="replace")
        header, units = parse_gretil_plain(raw)
        stated = None
        m = re.search(r"## Licence:\s*\n(.*?)\n\s*\n", header, re.S)
        if m:
            for lic_line in m.group(1).splitlines():
                mm = re.search(r"Creative Commons ([^.\n]+)", lic_line)
                if mm:
                    stated = "CC " + mm.group(1).strip()
                    break
                if re.search(r"public domain", lic_line, re.I):
                    stated = "Public Domain"
                    break
        try:
            row = gate(args.text_id, stated_license=stated)
        except LicenseRefused as e:
            print("GATE REFUSED — %s" % args.text_id)
            for rsn in e.reasons:
                print("  - %s" % rsn)
            print("  registry: %s" % (LICENSES_TSV.relative_to(ROOT),))
            sys.exit(2)
        print("gate: ALLOWED — %s (%s, verdict %s)"
              % (args.text_id, row["license"], row["verdict"]))
        units = [_to_iast(u) for u in units]
        if not units:
            ap.error("no usable units parsed from %s" % args.input)
        st, examples = Counter(), defaultdict(list)
        rules = run_text(units, args.text_id, args.allow_network, st, examples)
        out = OUT_DIR / ("%s_sandhi.tsv" % ind.slug(args.text_id))
        write_tsv(out, rules, examples)
        print("units %d · junctions %d · events %d · rules %d"
              % (st["units"], st["junctions"], st["events"], st["distinct_rules"]))
        print("skips: align_fail %d · dm_fail %d" % (st["align_fail"], st["dm_fail"]))
        print("wrote", out.relative_to(ROOT))
        return
    ap.error("nothing to do — pass --check-gate, --validate-dcs, or "
             "--text-id/--input")


if __name__ == "__main__":
    main()
