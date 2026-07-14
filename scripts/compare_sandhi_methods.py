#!/usr/bin/env python
"""H882 Phase 0 + H903 (method B) + H908 (method C) — sandhi split-method A/B/C harness.

The roadmap's central experiment: for a text with NO hand-annotated sandhi, three
ways to obtain the word-split that the junction-rule inducer needs, compared on
the SAME text —

  A  DCS gold splits      — read `Unsandhied=` straight from DCS CoNLL-U. The
                            ceiling: human-verified. IMPLEMENTED (dcs_sandhi_induce).
  B  Vidyut cheda         — segment raw text with the offline vidyut-cheda model
                            (vidyut-data/cheda/model.msgpack), then induce. IMPLEMENTED
                            (H903 — see method_B docstring for scope/limitations).
  C  Neural (DharmaMitra) — `unsandhied` segmentation API, cached; then induce.
                            IMPLEMENTED (H908 — --allow-network; far outperforms B,
                            near-perfect precision — see method_C docstring).

Because A uses gold splits, it is the reference; B and C are scored *against A*
on the same text (junction-level agreement + rule-inventory P/R/F1). Separately,
A's rule NOTATION is validated against the Bhagavadgītā hand table
(data/gita/gita_sandhi.tsv) — the only place where a human independently wrote
the same `X Y → Z` strings — to confirm the inducer speaks the same language.

Usage:
  python scripts/compare_sandhi_methods.py --text "Aṣṭāvakragīta" --methods AB
  python scripts/compare_sandhi_methods.py --text Hitopadeśa --methods A
"""
import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import dcs_sandhi_induce as ind  # noqa: E402

GITA_GOLD = ROOT / "data" / "gita" / "gita_sandhi.tsv"
VIDYUT_DATA_ROOT = Path("C:/Users/user/Documents/GitHub/vidyut-data")
VIDYUT_CHEDA = VIDYUT_DATA_ROOT / "cheda" / "model.msgpack"

# method C — DharmaMitra neural segmenter (API-only; contract reused from
# csl-atlas/scripts/lib/dharmamitra_infer.py). `unsandhied` mode returns one
# `_`-joined segmentation string per input text, already in IAST with visarga.
DM_API = "https://dharmamitra.org/api/tagging/"
DM_CACHE = ROOT / "data" / "sandhi" / "_cache"
DM_BATCH = 32

_chedaka = None  # lazy singleton — model load cost paid once per process


def _get_chedaka():
    global _chedaka
    if _chedaka is None:
        from vidyut.cheda import Chedaka
        _chedaka = Chedaka(str(VIDYUT_DATA_ROOT))
    return _chedaka


def _pausa_normalize(iast_word):
    """Approximate DCS's own `Unsandhied` convention: a word-final underlying
    -s/-r (vidyut's cheda returns the Pāṇinian pre-visarga citation form, e.g.
    `agnis`, `vāyus`, `dyaus`) becomes visarga `ḥ` in isolation, matching how
    DCS writes e.g. `agniḥ`. Known approximation: a handful of indeclinables
    (`punar`) keep a bare -r as part of the word itself rather than an
    inflectional ending and are mis-normalized by this rule — not corrected
    here (Phase-1 bake-off scope, see method_B docstring)."""
    if iast_word and iast_word[-1] in ("s", "r"):
        return iast_word[:-1] + "ḥ"
    return iast_word


def _sentence_units(words, mwts):
    """Reading-order list of surface units for one sentence: a plain word
    (`n=1`, carries its own gold `uns`/`surf`) or an MWT span (`n=len(components)`,
    no single `uns` — internal vowel coalescence, e.g. nāgnir = na+agniḥ). Every
    unit's `surf` is the raw observed text (gold FORM, or the MWT range surface)
    — the one thing method A and B always agree on; only the *uns* guess differs
    between methods. Mirrors the `covered`/MWT bookkeeping in
    dcs_sandhi_induce.induce_from_files, factored out so method_B can reuse it."""
    covered = set()
    for m in mwts:
        covered.update(range(m["start"], m["end"] + 1))
    by_id = {w["id"]: w for w in words}
    units = []
    seen_mwt_start = set()
    for w in sorted(words, key=lambda w: w["id"]):
        if w["id"] in covered:
            m = next(m for m in mwts if m["start"] <= w["id"] <= m["end"])
            if m["start"] in seen_mwt_start:
                continue
            seen_mwt_start.add(m["start"])
            comps = [by_id[k] for k in range(m["start"], m["end"] + 1) if k in by_id]
            units.append({"kind": "mwt", "surf": m["surface"], "n": len(comps)})
        else:
            units.append({"kind": "word", "surf": w["form"], "uns": w["uns"], "n": 1})
    return units


# --- method A: DCS gold splits (implemented) --------------------------------
def method_A(text, dcs_root):
    """Induce rules from DCS gold Unsandhied splits (mode 1 edge + mode 2 MWT
    coalescence). Returns Counter(rule -> n)."""
    files = sorted((Path(dcs_root) / text).glob("*.conllu"))
    counts, _examples, _st, _flagged, _dbg = ind.induce_from_files(files)
    return counts


# --- method B: Vidyut cheda segmenter (H903 Phase 1) -------------------------
def method_B(text, dcs_root, stats_out=None):
    """Segment each DCS sentence's raw text with the offline vidyut-cheda
    model, then feed the predicted (pre-sandhi) split through
    ind.induce_rule() exactly as method A does — so only the SPLIT SOURCE
    differs, isolating splitter quality from the (shared, already-validated)
    rule-induction notation.

    Per sentence: transliterate `# text =` (IAST → SLP1), run Chedaka, get an
    ordered list of predicted pre-sandhi tokens (SLP1 → IAST, then
    `_pausa_normalize`d). Chedaka.run() returns only `text`/`lemma`/`data` —
    no character offsets — so a predicted token can't be re-anchored to an
    arbitrary span of the raw surface in general. What CAN be done exactly:
    consume the predicted-token stream `n` at a time per `_sentence_units`
    unit (n=1 for a plain word, n=len(components) for an MWT span) and check
    the stream fully accounts for every unit; if it doesn't (cheda
    over/under-split relative to DCS's own word count), the WHOLE sentence is
    skipped rather than guessed at (`skipped_count_mismatch`).

    SCOPE (Phase-1, documented limitation, not a silent gap): rules are only
    induced at mode-1 junctions between two ADJACENT PLAIN-WORD units (n=1 on
    both sides) — an MWT-internal coalescence (e.g. nāgnir=na+agniḥ) has no
    independently observable surface span per predicted sub-word without
    offsets, so both the MWT's own internal junction and its two flanking
    junctions are skipped (`skipped_mwt_adjacent`). Method A's mode-1 junction
    count is the dominant share of total junctions (H900: MWT/mode-2
    boundaries are a minority), so this still yields a real, comparable rule
    inventory — see `method_A_mode1_strict` for the matching gold slice.
    """
    ch = _get_chedaka()
    import vidyut.lipi as lipi
    IAST, SLP1 = lipi.Scheme.Iast, lipi.Scheme.Slp1

    files = sorted((Path(dcs_root) / text).glob("*.conllu"))
    counts = Counter()
    examples = defaultdict(list)
    st = Counter()

    for f in files:
        for ref, words, mwts in ind.read_sentences(f):
            if not ref:
                continue
            st["sentences"] += 1
            units = _sentence_units(words, mwts)

            # gold-independent bookkeeping: how many mode-1 (word-word) junctions
            # in THIS sentence have no gold Unsandhied on either side at all —
            # positions method A structurally cannot induce a rule for, counted
            # whether or not cheda's own alignment below succeeds.
            for i in range(len(units) - 1):
                u, nx = units[i], units[i + 1]
                if u["n"] != 1 or nx["n"] != 1:
                    continue
                st["mode1_total"] += 1
                if u["uns"] is None or nx["uns"] is None:
                    st["no_gold_total"] += 1

            try:
                pred = [lipi.transliterate(t.text, SLP1, IAST)
                        for t in ch.run(lipi.transliterate(ref, IAST, SLP1))]
            except Exception:
                st["cheda_fail"] += 1
                continue

            idx, aligned, drift = 0, [], False
            for u in units:
                if idx + u["n"] > len(pred):
                    drift = True
                    break
                pu = _pausa_normalize(pred[idx]) if u["n"] == 1 else None
                aligned.append((pu, u))
                idx += u["n"]
            if drift or idx != len(pred):
                st["skipped_count_mismatch"] += 1
                continue

            for i in range(len(aligned) - 1):
                pu, u = aligned[i]
                nu, nx = aligned[i + 1]
                if u["n"] != 1 or nx["n"] != 1:
                    st["skipped_mwt_adjacent"] += 1
                    continue
                st["junctions"] += 1
                gold_no_gold = u["uns"] is None or nx["uns"] is None
                rule, flag = ind.induce_rule(pu, u["surf"], nu, nx["surf"])
                if rule is None:
                    st["no_sandhi"] += 1
                    continue
                if flag == "empty-side":
                    continue
                counts[rule] += 1
                if gold_no_gold:
                    st["no_gold_recovered"] += 1
                if len(examples[rule]) < 4:
                    examples[rule].append("%s %s+%s" % (ref, u["surf"], nx["surf"]))

    st["distinct_rules"] = len(counts)
    st["events"] = sum(counts.values())
    if stats_out is not None:
        stats_out.update(st)
        stats_out["examples"] = examples
    return counts


# --- method A, mode-1-only slice (fair baseline for method B's Phase-1 scope)
def method_A_mode1_strict(text, dcs_root):
    """Same mode-1-only restriction as method_B (word-word junctions with
    neither side touching an MWT), but using GOLD Unsandhied — the fair
    apples-to-apples comparison target, since method A's full rule set
    (returned by method_A) also includes mode-2/2b MWT-boundary rules B never
    attempts in Phase 1."""
    files = sorted((Path(dcs_root) / text).glob("*.conllu"))
    counts = Counter()
    for f in files:
        for ref, words, mwts in ind.read_sentences(f):
            if not ref:
                continue
            units = _sentence_units(words, mwts)
            for i in range(len(units) - 1):
                u, nx = units[i], units[i + 1]
                if u["n"] != 1 or nx["n"] != 1:
                    continue
                if u["uns"] is None or nx["uns"] is None:
                    continue  # no gold Unsandhied here — the exact gap method_B's no_gold_recovered targets
                rule, flag = ind.induce_rule(u["uns"], u["surf"], nx["uns"], nx["surf"])
                if rule is None or flag == "empty-side":
                    continue
                counts[rule] += 1
    return counts


# --- method C: neural DharmaMitra segmenter (STUB) --------------------------
def _dm_segment(sentences, text_id, allow_network):
    """Return {sentence: [pre-sandhi tokens]} via the DharmaMitra `unsandhied`
    API, cached to data/sandhi/_cache/dharmamitra_<id>.json so re-runs never
    re-hit the network. Only uncached sentences are sent (batched); if any are
    uncached and allow_network is False, raises so the caller SKIPS method C."""
    DM_CACHE.mkdir(parents=True, exist_ok=True)
    cache_path = DM_CACHE / ("dharmamitra_%s.json" % ind.slug(text_id))
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    todo = [s for s in dict.fromkeys(sentences) if s not in cache]
    if todo:
        if not allow_network:
            raise NotImplementedError(
                "%d/%d sentences uncached; pass --allow-network to query DharmaMitra"
                % (len(todo), len(set(sentences))))
        import time
        import requests
        for i in range(0, len(todo), DM_BATCH):
            chunk = todo[i:i + DM_BATCH]
            # the API occasionally drops the TLS connection under sustained load;
            # retry with backoff, and persist the cache after EVERY batch so a
            # later failure never loses completed work.
            for attempt in range(4):
                try:
                    resp = requests.post(DM_API, json={"texts": chunk, "mode": "unsandhied",
                                                       "human_readable_tags": True}, timeout=120)
                    resp.raise_for_status()
                    break
                except Exception as e:
                    if attempt == 3:
                        cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
                        raise RuntimeError("DharmaMitra batch failed after 4 tries "
                                           "(%d cached so far); rerun to resume: %s" % (len(cache), e))
                    time.sleep(2 ** attempt)
            for sent, seg in zip(chunk, resp.json()["results"]):
                cache[sent] = [t for t in seg.split("_") if t]
            cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            print("  DharmaMitra: %d/%d sentences queried" % (min(i + DM_BATCH, len(todo)), len(todo)))
            time.sleep(0.3)  # be polite to a free academic API
    return cache


def method_C(text, dcs_root, stats_out=None, allow_network=False):
    """Segment each DCS sentence's raw text with the DharmaMitra neural
    segmenter (API-only), then feed the predicted split through the SAME
    induce_rule() tail as methods A/B — so C is directly comparable to B, only
    the splitter differs (neural vs vidyut-cheda's finite-state). Structure
    mirrors method_B verbatim (see its docstring for the units/alignment/skip
    scope); the only change is `pred` comes from `_dm_segment` (already IAST
    with visarga, so no transliteration/pausa-normalize needed)."""
    files = sorted((Path(dcs_root) / text).glob("*.conllu"))
    # gather every raw sentence first, so the API is queried in cached batches
    sents = [ref for f in files for ref, _w, _m in ind.read_sentences(f) if ref]
    dm = _dm_segment(sents, text, allow_network)

    counts = Counter()
    examples = defaultdict(list)
    st = Counter()
    for f in files:
        for ref, words, mwts in ind.read_sentences(f):
            if not ref:
                continue
            st["sentences"] += 1
            units = _sentence_units(words, mwts)
            for i in range(len(units) - 1):
                u, nx = units[i], units[i + 1]
                if u["n"] != 1 or nx["n"] != 1:
                    continue
                st["mode1_total"] += 1
                if u["uns"] is None or nx["uns"] is None:
                    st["no_gold_total"] += 1

            pred = dm.get(ref)
            if pred is None:
                st["dm_fail"] += 1
                continue

            idx, aligned, drift = 0, [], False
            for u in units:
                if idx + u["n"] > len(pred):
                    drift = True
                    break
                pu = _pausa_normalize(pred[idx]) if u["n"] == 1 else None
                aligned.append((pu, u))
                idx += u["n"]
            if drift or idx != len(pred):
                st["skipped_count_mismatch"] += 1
                continue

            for i in range(len(aligned) - 1):
                pu, u = aligned[i]
                nu, nx = aligned[i + 1]
                if u["n"] != 1 or nx["n"] != 1:
                    st["skipped_mwt_adjacent"] += 1
                    continue
                st["junctions"] += 1
                gold_no_gold = u["uns"] is None or nx["uns"] is None
                rule, flag = ind.induce_rule(pu, u["surf"], nu, nx["surf"])
                if rule is None:
                    st["no_sandhi"] += 1
                    continue
                if flag == "empty-side":
                    continue
                counts[rule] += 1
                if gold_no_gold:
                    st["no_gold_recovered"] += 1
                if len(examples[rule]) < 4:
                    examples[rule].append("%s %s+%s" % (ref, u["surf"], nx["surf"]))

    st["distinct_rules"] = len(counts)
    st["events"] = sum(counts.values())
    if stats_out is not None:
        stats_out.update(st)
        stats_out["examples"] = examples
    return counts


# --- scoring ----------------------------------------------------------------
def load_rule_set(tsv_path):
    if not tsv_path.exists():
        return {}
    out = {}
    for row in csv.DictReader(open(tsv_path, encoding="utf-8"), delimiter="\t"):
        out[row["rule"]] = int(row["count"])
    return out


def pr_f1(ref_rules, hyp_rules):
    """Rule-inventory precision/recall/F1 (set overlap on rule strings)."""
    ref, hyp = set(ref_rules), set(hyp_rules)
    tp = len(ref & hyp)
    prec = tp / len(hyp) if hyp else 0.0
    rec = tp / len(ref) if ref else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1, tp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--dcs-root", default=str(ind.DEFAULT_DCS))
    ap.add_argument("--methods", default="A", help="subset of ABC, e.g. 'A' or 'ABC'")
    ap.add_argument("--allow-network", action="store_true",
                    help="permit method C to query the DharmaMitra API (else C uses cache only)")
    args = ap.parse_args()

    results = {}
    stats = {"B": {}, "C": {}}
    for m in args.methods.upper():
        if m == "B":
            fn = lambda text, root: method_B(text, root, stats_out=stats["B"])  # noqa: E731
        elif m == "C":
            fn = lambda text, root: method_C(text, root, stats_out=stats["C"],  # noqa: E731
                                             allow_network=args.allow_network)
        else:
            fn = {"A": method_A}[m]
        try:
            results[m] = fn(args.text, args.dcs_root)
            print("method %s: %d distinct rules over %d junctions"
                  % (m, len(results[m]), sum(results[m].values())))
        except NotImplementedError as e:
            print("method %s: SKIPPED — %s" % (m, e))

    for m, failkey in (("B", "cheda_fail"), ("C", "dm_fail")):
        st = stats[m]
        if m in results and st:
            print("  %s coverage: %d sentences · %d junctions scored · skipped "
                  "%d (MWT-adjacent) + %d (count mismatch) + %d (splitter failure)"
                  % (m, st.get("sentences", 0), st.get("junctions", 0),
                     st.get("skipped_mwt_adjacent", 0),
                     st.get("skipped_count_mismatch", 0), st.get(failkey, 0)))
            mode1_total = st.get("mode1_total", 0)
            no_gold_total = st.get("no_gold_total", 0)
            if no_gold_total:
                print("  %s no-gold recovery: of %d mode-1 junctions, %d (%.1f%%) have NO "
                      "gold Unsandhied either side (A can't induce there) — %s produced a "
                      "rule for %d (%.1f%%)"
                      % (m, mode1_total, no_gold_total,
                         100.0 * no_gold_total / mode1_total if mode1_total else 0.0, m,
                         st.get("no_gold_recovered", 0),
                         100.0 * st.get("no_gold_recovered", 0) / no_gold_total))

    # B/C scored against A (the gold-split ceiling) on the same text
    if "A" in results:
        for m in ("B", "C"):
            if m in results:
                p, r, f, tp = pr_f1(results["A"], results[m])
                print("  %s vs A (full): P=%.3f R=%.3f F1=%.3f (%d shared rules)" % (m, p, r, f, tp))

    # fair baseline: B/C only attempt mode-1 word-word junctions (Phase-1 scope),
    # so also score against the SAME slice of gold A rather than A's full set
    if ("B" in results or "C" in results) and "A" in results:
        a_mode1 = method_A_mode1_strict(args.text, args.dcs_root)
        for m in ("B", "C"):
            if m in results:
                p, r, f, tp = pr_f1(a_mode1, results[m])
                print("  %s vs A (mode-1-only, apples-to-apples): P=%.3f R=%.3f F1=%.3f "
                      "(%d shared; A mode-1-only has %d rules)"
                      % (m, p, r, f, tp, len(a_mode1)))

    # validate method-A notation against the Gītā hand table
    gita = load_rule_set(GITA_GOLD)
    if "A" in results and gita:
        p, r, f, tp = pr_f1(gita, results["A"])
        print("\nnotation check — method A rules vs Gītā hand table (%s):" % GITA_GOLD.name)
        print("  shared rule strings: %d   (A covers %.0f%% of Gītā's %d hand rules)"
              % (tp, 100.0 * tp / len(gita), len(gita)))
        shared = sorted(set(gita) & set(results["A"]),
                        key=lambda k: -gita[k])[:10]
        print("  top shared:", ", ".join(shared))
        only_gita = sorted(set(gita) - set(results["A"]), key=lambda k: -gita[k])[:8]
        if only_gita:
            print("  in Gītā not (yet) here:", ", ".join(only_gita))


if __name__ == "__main__":
    main()
