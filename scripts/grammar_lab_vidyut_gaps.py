#!/usr/bin/env python3
"""H4795 — Grammar Lab (g1) x vidyut derivation-status gap join.

Joins the SanskritGrammar grammar-lab-g1 topic graph (Whitney + Zaliznyak root
alternation; one whitney-root exemplar root per topic) to kosha
`data/concordance/derivation_status.tsv` (401,368 AG rows, H1368 W2a) by
root/lemma, and ranks the alternation classes vidyut fails on, weighted by
corpus frequency (`data/frequency/lemma_frequency.tsv`).

Failure definition (per the W2a data statement, engine-error is dominated by
the verbal dhaatu/gaNa/lakaara mapping):
  - engine-error : candidate cells existed, none derivable — hard fail
  - ambiguous    : >1 distinct chain matches — decision fail (parked W2a gap)
Both are reported separately; the priority weight sums them with
engine-error counted once and ambiguous counted once per row, each row
weighted by the corpus frequency of its attested form (fallback: the root's
own lemma frequency, applied once per (root, status) bucket, not per row).

Outputs: data/concordance/grammar_lab_vidyut_gaps.tsv + stdout summary.
Read-only on all inputs. No network (R12).
"""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from kosha.transliterate import to_slp1_auto  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
GRAN = Path("../SanskritGrammar/data/grammar_lab/export/grammar_lab.json")
DERIV = REPO / "data/concordance/derivation_status.tsv"
FREQ = REPO / "data/frequency/lemma_frequency.tsv"
OUT = REPO / "data/concordance/grammar_lab_vidyut_gaps.tsv"
DCS_CLASS_DIR = Path(
    "../VisualDCS/derived-data/Glagolnye-formy/Klassy/"
    "Spiski-glagolnyh-kornej-po-klassam-2214/Imeyushchie-formy"
)

CLASS_NAMES = {
    "1": "bhvAdi", "2": "adAdi", "3": "juhotyAdi", "4": "divAdi",
    "5": "svAdi", "6": "tudAdi", "7": "rudhAdi", "8": "tanAdi",
    "9": "kryAdi", "10": "curAdi",
}

VERBAL_POS = {"verbal", "both"}
FAIL_STATUS = ("engine-error", "ambiguous")


def load_topics():
    """slug -> {title_ru, cluster, roots} from whitney-root anchors."""
    bundle = json.loads(GRAN.read_text(encoding="utf-8"))
    topics = {}
    for t in bundle["topics"]:
        roots = {
            s["anchor_key_slp1"]
            for s in t.get("sources", ())
            if s.get("anchor_type") == "whitney-root" and s.get("anchor_key_slp1")
        }
        topics[t["id"].rsplit(":", 1)[-1]] = {
            "title_ru": t.get("title_ru", ""),
            "cluster": t.get("cluster", ""),
            "roots": roots,
        }
    return topics


def load_deriv():
    """root -> {status: n_rows}, root -> {status: Counter(form)} (verbal/both only)."""
    per_root = defaultdict(Counter)
    fail_forms = defaultdict(lambda: defaultdict(Counter))
    with DERIV.open(encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        col = {c: i for i, c in enumerate(header)}
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if f[col["pos_tried"]] not in VERBAL_POS:
                continue
            root, status, form = (
                f[col["lemma_slp1"]],
                f[col["derivation_status"]],
                f[col["attested_form"]],
            )
            per_root[root][status] += 1
            if status in FAIL_STATUS:
                fail_forms[root][status][form] += 1
    return per_root, fail_forms


def load_freq():
    freq = {}
    with FREQ.open(encoding="utf-8") as fh:
        fh.readline()
        for line in fh:
            f = line.rstrip("\n").split("\t")
            # tail rows with empty count_all (known lemma_frequency artifact) — skip
            if len(f) >= 2 and f[1].isdigit():
                freq[f[0]] = int(f[1])
    return freq


def load_classes():
    """root(SLP1) -> {'3', '9', ...} present classes, from the DCS M9 CSVs (IAST).

    Read-only sibling pin per the dcs-verb-roots-by-class manifest row; roots
    not attested in DCS class lists get an empty set (reported as
    not-in-dcs-class-list, never guessed).
    """
    by_root = defaultdict(set)
    if not DCS_CLASS_DIR.is_dir():
        return by_root
    for p in sorted(DCS_CLASS_DIR.glob("*.csv")):
        k = p.stem
        with p.open(encoding="utf-8-sig") as fh:
            for row in csv.reader(fh):
                if row and row[0]:
                    by_root[to_slp1_auto(row[0])].add(k)
    return by_root


def main():
    topics = load_topics()
    per_root, fail_forms = load_deriv()
    freq = load_freq()
    root_class = load_classes()
    cls = lambda r: "+".join(CLASS_NAMES[k] for k in sorted(root_class.get(r, ()))) or "not-in-dcs-class-list"

    rows = []
    for slug, t in sorted(topics.items()):
        agg = Counter()
        weight = 0
        missing_roots = set()
        for root in sorted(t["roots"]):
            status_counts = per_root.get(root)
            if not status_counts:
                missing_roots.add(root)
                continue
            agg.update(status_counts)
            for status in FAIL_STATUS:
                for form, n in fail_forms[root][status].items():
                    w = freq.get(form)
                    if w is None:  # fallback: root lemma once per bucket
                        w = freq.get(root, 0)
                        weight += w if w else 0
                    else:
                        weight += w * n
        rows.append(
            {
                "topic": slug,
                "title_ru": t["title_ru"],
                "cluster": t["cluster"],
                "roots": "|".join(sorted(t["roots"])),
                "verbal_rows": sum(agg.values()),
                "ok": agg.get("ok", 0),
                "ambiguous": agg.get("ambiguous", 0),
                "engine_error": agg.get("engine-error", 0),
                "no_derivation": agg.get("no-derivation", 0),
                "fail_weight": weight,
                "root_class": "|".join(cls(r) for r in sorted(t["roots"])),
                "missing_roots": "|".join(sorted(missing_roots)),
            }
        )

    # Priority: engine-error rows first, then corpus-weighted failure.
    rows.sort(key=lambda r: (-r["engine_error"], -r["fail_weight"], -r["ambiguous"]))

    with OUT.open("w", encoding="utf-8", newline="") as fh:
        cols = list(rows[0])
        fh.write("\t".join(cols) + "\n")
        for r in rows:
            fh.write("\t".join(str(r[c]) for c in cols) + "\n")

    # --- engine-error root roster with structural alternation flags ---
    ee_roots = sorted(r for r, c in per_root.items() if c.get("engine-error"))
    print(f"topics={len(rows)}  engine_error_roots={len(ee_roots)}")
    print("\n## Topics ranked (top 15 by engine-error/frequency weight)")
    for r in rows[:15]:
        print(
            f"{r['topic']:<28} root={r['roots']:<6} rows={r['verbal_rows']:>5} "
            f"ok={r['ok']:>4} amb={r['ambiguous']:>5} ee={r['engine_error']:>4} "
            f"w={r['fail_weight']:>8}"
        )
    print("\n## Engine-error roots (rows, features)")
    for root in ee_roots:
        c = per_root[root]
        feats = []
        if "N" in root:
            feats.append("set/nasal-infix(N)")
        if "f" in root or "F" in root:
            feats.append("vocalic-r(f)")
        if "y" in root or "Y" in root:
            feats.append("y-class")
        if len(root) <= 2:
            feats.append("short")
        w = sum(
            (freq.get(f, freq.get(root, 0)) * n)
            for f, n in fail_forms[root]["engine-error"].items()
        )
        print(f"{root:<8} ee={c['engine-error']:>4} ok={c.get('ok', 0):>4} "
              f"amb={c.get('ambiguous', 0):>4} w={w:>7} cls={cls(root)} {','.join(feats)}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
