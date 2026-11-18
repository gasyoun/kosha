#!/usr/bin/env python3
"""Assemble and score the H6253 article-generation eval, with canary + negative control.

Reference solution = frozen Cologne MW gold; negative class = mutated wrong article
(H6714). The MG-labeled 5-article canary is a human act: without labels the script
reports INCONCLUSIVE and refuses any PASS.
Executed under H6253 by Hy4 flash Free (opencode-go/hy4-flash-free).
"""
import argparse
import ast
import csv
import difflib
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from indic_transliteration import sanscript

MODELS = ("glm", "deepseek")
SHORT = {"glm": "glm-5.3-flash (opencode-go)", "deepseek": "deepseek-v4.1-flash (opencode-go)"}
GLYPH = re.compile(r"[^\w\s]+", re.UNICODE)


def plain(s):
    return "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c)).lower()


def tokens(s):
    return re.findall(r"[a-z]+", plain(s))


def phrase(s):
    return re.sub(r"\s+", " ", GLYPH.sub(" ", plain(s))).strip()


def grams(s, n=3):
    t = re.sub(r"\s+", " ", plain(s)).replace(" ", "_")
    return {t[i : i + n] for i in range(max(0, len(t) - n + 1))}


def to_iast(s):
    """Cologne gold is SLP1; generated articles are IAST. Compare one script."""
    try:
        return sanscript.transliterate(str(s), sanscript.SLP1, sanscript.IAST)
    except Exception:
        return str(s)


def example_match(gen, gold):
    """Near-exact reproduction: char-3 overlap >= 0.5 after script normalisation."""
    a, b = phrase(gen), phrase(gold)
    return bool(a and b and set_f1(grams(a), grams(b)) >= 0.5)


def f1(a, b):
    if not a or not b:
        return 0.0
    hit = len(a & b)
    if not hit:
        return 0.0
    p, r = hit / len(a), hit / len(b)
    return 2 * p * r / (p + r)


def set_f1(a, b):
    return f1(set(a), set(b))


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def read_sample(data):
    rows = []
    with open(data / "sample.tsv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            r["gold_examples"] = json.loads(r["gold_examples"])
            r["gold_citations"] = json.loads(r["gold_citations"])
            rows.append(r)
    return rows


PIPE = re.compile(
    r"^([^|]+?)\s*\|\s*gloss=(.*?)\s*\|\s*examples=(\[.*?\])\s*\|\s*citations=(\[.*?\])\s*\|\s*root=(.*)$"
)


def parse_line(line):
    """Accept strict JSONL and the model's pipe-format drift, never silent drop."""
    line = line.strip()
    if not line:
        return None
    if line.startswith("{"):
        try:
            obj = json.loads(line)
            return obj if obj.get("slp1") else None
        except json.JSONDecodeError:
            # One observed drift: {"slp1":vEDAtaki",...} — unquoted key value.
            m = re.match(r'\{"slp1"\s*:\s*"([^",{}\s]+)"|\{"slp1"\s*:\s*([^",{}\s]+)', line)
            if m:
                try:
                    bad = m.group(1) or m.group(2)
                    fixed = re.sub(r'^\{"slp1"\s*:\s*"?[^",{}\s]+"?', f'{{"slp1":"{bad}"', line, count=1)
                    obj = json.loads(fixed)
                    return obj if obj.get("slp1") else None
                except json.JSONDecodeError:
                    return None
            return None
    m = PIPE.match(line)
    if not m:
        return None
    try:
        examples = ast.literal_eval(m.group(3))
        citations = ast.literal_eval(m.group(4))
    except (ValueError, SyntaxError):
        return None
    return {"slp1": m.group(1).strip(), "gloss": m.group(2).strip(),
            "examples": examples, "citations": citations, "root": m.group(5).strip()}


def canonical_key(candidate, expected, iast_map):
    """Map model-side SLP1/IAST/typo key drift back onto a frozen sample key."""
    candidate = str(candidate).strip()
    if candidate in expected:
        return candidate, False
    try:
        slp1 = sanscript.transliterate(candidate, sanscript.IAST, sanscript.SLP1)
    except Exception:
        slp1 = candidate
    if slp1 in expected:
        return slp1, True
    near = difflib.get_close_matches(plain(candidate), list(iast_map), n=1, cutoff=0.7)
    if near:
        return iast_map[near[0]], True
    return None, False


def assemble(data, rows):
    """Parse model transcripts (JSONL + pipe drift) into gen[model][slp1]."""
    expected = {r["slp1"] for r in rows}
    iast_map = {plain(r["iast"]): r["slp1"] for r in rows}
    gen = {m: {} for m in MODELS}
    parse_fail = {m: 0 for m in MODELS}
    recoveries = {m: [] for m in MODELS}
    for m in MODELS:
        for p in sorted((data / "raw").glob(f"{m}_batch_*.txt")):
            saw_payload = False
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                obj = parse_line(line)
                if obj is None:
                    if line.strip() and not line.strip().startswith(">"):
                        parse_fail[m] += 1
                    continue
                key, recovered = canonical_key(obj.get("slp1"), expected, iast_map)
                if key is None:
                    parse_fail[m] += 1
                    continue
                if recovered:
                    recoveries[m].append({"file": p.name, "from": obj.get("slp1"), "to": key})
                saw_payload = True
                obj["slp1"] = key
                obj["_source"] = p.name
                gen[m][key] = obj
            if not saw_payload and p.stat().st_size:
                parse_fail[m] += 1
    return gen, parse_fail, recoveries


def root_ok(root, iast):
    r = plain(root).replace("√", "").strip()
    r = re.sub(r"\b(upa|sam|pra|vi|su|ati|anu|ni|apa|abhi|ud|vi)\b", "", r).strip()
    h = plain(iast)
    if len(r) < 2 or not h:
        return False
    return r in h or h in r or any(len(r) >= 3 and r[i : i + 3] in h for i in range(len(r) - 2))


def score_one(row, obj, inv_norm):
    ge_raw = [to_iast(x) for x in row["gold_examples"]]
    ge = {phrase(x) for x in ge_raw}
    gc = {phrase(x) for x in row["gold_citations"]}
    examples = [str(x) for x in (obj.get("examples") or []) if str(x).strip()]
    citations = [str(x) for x in (obj.get("citations") or []) if str(x).strip()]
    gloss = str(obj.get("gloss") or "")
    gold_gloss = to_iast(row["gold_gloss"])
    pe = {phrase(x) for x in examples}
    pc = {phrase(x) for x in citations}
    attested = sum(1 for c in pc if c in inv_norm) / len(pc) if pc else 0.0
    gold_match = sum(1 for c in pc if c in gc) / len(pc) if pc else 0.0
    covered = sum(any(example_match(g, e) for e in examples) for g in ge_raw)
    ex_recall = covered / len(ge_raw) if ge_raw else 0.0
    ex_prec = sum(any(example_match(e, g) for g in ge_raw) for e in examples) / len(examples) if examples else 0.0
    ex_f1 = 2 * ex_prec * ex_recall / (ex_prec + ex_recall) if ex_prec + ex_recall else 0.0
    return {
        "slp1": row["slp1"],
        "split": row["split"],
        "gloss_token_f1": set_f1(tokens(gloss), tokens(gold_gloss)),
        "gloss_chr3_f1": set_f1(grams(gloss), grams(gold_gloss)),
        "example_f1": ex_f1,
        "example_recall": ex_recall,
        "citation_attestation": attested,
        "citation_gold_match": gold_match,
        "root_ok": int(root_ok(str(obj.get("root") or ""), row["iast"])),
        "n_citations": len(pc),
        "n_examples": len(pe),
        "has_gloss": int(bool(gloss.strip())),
        "has_examples": int(bool(pe)),
        "_examples": examples,
        "_gold_examples": sorted(ge),
        "_citations": citations,
        "_gold_citations": sorted(gc),
        "_root": str(obj.get("root") or ""),
    }


def taxonomy(rows, scored, inv_norm):
    out = []
    bykey = {r["slp1"]: r for r in rows}
    for m in MODELS:
        for s in scored[m]:
            row = bykey[s["slp1"]]
            if not s["has_gloss"] or not s["has_examples"]:
                out.append((m, s["slp1"], "empty_field", f"gloss={s['has_gloss']} examples={s['has_examples']}"))
            for c in s["_citations"]:
                cn = phrase(c)
                if cn not in inv_norm:
                    out.append((m, s["slp1"], "unattested_citation", f"generated citation {c!r} not in Cologne MW inventory"))
                elif cn not in {phrase(x) for x in s["_gold_citations"]}:
                    out.append((m, s["slp1"], "citation_not_in_entry", f"{c!r} attested corpus-wide but absent from {s['slp1']} entry"))
            for e in s["_examples"]:
                if not any(example_match(e, g) for g in s["_gold_examples"]):
                    out.append((m, s["slp1"], "example_not_in_gold", f"example {e!r} not in frozen Cologne entry"))
            if not s["root_ok"]:
                out.append((m, s["slp1"], "root_headword_mismatch", f"root {s['_root']!r} vs headword {row['iast']!r}"))
    return out


def aggregate(scored, parse_fail, rows):
    out = {}
    n_main = sum(1 for r in rows if r["split"] == "main")
    for m in MODELS:
        main = [s for s in scored[m] if s["split"] == "main"]
        assert len(main) == n_main, f"{m}: {len(main)} main rows, expected {n_main}"
        keys = ["gloss_token_f1", "gloss_chr3_f1", "example_f1", "example_recall",
                "citation_attestation", "citation_gold_match", "root_ok", "has_gloss", "has_examples"]
        out[m] = {"n_main": len(main), "parse_failures": parse_fail[m],
                  **{k: round(sum(s[k] for s in main) / len(main), 4) for k in keys}}
    return out


def write_outputs(data, rows, scored, tax, agg, meta_extra):
    cols = ["slp1", "split", "gloss_token_f1", "gloss_chr3_f1", "example_f1", "example_recall",
            "citation_attestation", "citation_gold_match", "root_ok", "n_citations", "n_examples",
            "has_gloss", "has_examples"]
    with open(data / "scores_per_item.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(cols)
        for m in MODELS:
            for s in scored[m]:
                w.writerow([m] + [round(s[c], 4) if isinstance(s[c], float) else s[c] for c in cols])
    counts = Counter(t[2] for t in tax)
    summary = {
        "eval": "H6253 — LLM article generation vs Cologne MW gold",
        "created": date.today().isoformat(),
        "executor": "Hy4 flash Free (opencode-go/hy4-flash-free)",
        "filename_tier_provenance": "OxAlpha",
        "reference_solution": "frozen Cologne MW gold (sample.tsv, hashed inputs)",
        "negative_class": "mutated wrong article — see --self-test (H6714)",
        "models": {m: SHORT[m] for m in MODELS},
        "aggregate": agg,
        "taxonomy_counts": dict(sorted(counts.items())),
        "taxonomy_examples": len(tax),
        "canary": "INCONCLUSIVE — 5 articles await MG manual gold labels (human act)",
        **meta_extra,
    }
    (data / "scores_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with open(data / "hallucination_taxonomy.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["model", "slp1", "category", "evidence"])
        for row in sorted(tax):
            w.writerow(row)
    lines = [
        "# Article generation vs Cologne gold — metrics report",
        "",
        "_Created: 18-11-2026 · Last updated: 18-11-2026_",
        "",
        "**Executed under H6253 by Hy4 flash Free (`opencode-go/hy4-flash-free`);",
        "filename tier OxAlpha retained as provenance (H3688).**",
        "",
        f"**Sample:** {agg['glm']['n_main']} main headwords × 2 models + 5 MG-canary rows.",
        "Reference = frozen Cologne MW v02 gold; negative class = mutated wrong article.",
        "",
        "## Metrics (main split, csl-observatory table format)",
        "",
        "| Metric | GLM 5.3 Flash | DeepSeek 4.1 Flash |",
        "|---|---:|---:|",
    ]
    labels = {"gloss_token_f1": "Gloss token F1", "gloss_chr3_f1": "Gloss char-3 F1",
              "example_f1": "Example F1", "example_recall": "Example recall",
              "citation_attestation": "Citation attestation (Cologne inventory)",
              "citation_gold_match": "Citation gold-entry match", "root_ok": "Root–headword ok",
              "has_gloss": "Gloss present", "has_examples": "Examples present"}
    for k, label in labels.items():
        lines.append(f"| {label} | {agg['glm'][k]:.4f} | {agg['deepseek'][k]:.4f} |")
    lines += ["", f"Parse failures: GLM {agg['glm']['parse_failures']} · DeepSeek {agg['deepseek']['parse_failures']}",
              "", "## Hallucination taxonomy", "", "| Category | Instances |", "|---|---:|"]
    for k, v in counts.most_common():
        lines.append(f"| {k} | {v} |")
    lines += [
        "",
        "Full per-item evidence: [hallucination_taxonomy.tsv](hallucination_taxonomy.tsv).",
        "",
        "## Canary (MG human act)",
        "",
        "5 canary rows are held out. The scoring script reproduces the evaluation only after",
        "MG fills `canary/mg_labels.tsv`; until then the canary verdict is **INCONCLUSIVE**",
        "and no PASS is claimed.",
        "",
        "_Dr. Mārcis Gasūns_",
    ]
    (data / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def self_test(data, rows, inv_norm):
    """Positive control (gold-substituted article) must beat mutated negative control."""
    bykey = {r["slp1"]: r for r in rows}
    items = [r for r in rows if r["split"] == "main"][:10]
    pos, neg = [], []
    for i, r in enumerate(items):
        good = {"slp1": r["slp1"], "gloss": to_iast(r["gold_gloss"]),
                "examples": [to_iast(x) for x in r["gold_examples"]],
                "citations": r["gold_citations"], "root": r["iast"]}
        bad = {"slp1": r["slp1"], "gloss": items[(i + 1) % len(items)]["gold_gloss"],
               "examples": ["garbage phrase xyz"], "citations": ["ZZZ."], "root": "√zzz"}
        pos.append(score_one(r, good, inv_norm))
        neg.append(score_one(r, bad, inv_norm))
    pg = sum(s["gloss_token_f1"] for s in pos) / len(pos)
    ng = sum(s["gloss_token_f1"] for s in neg) / len(neg)
    badtax = taxonomy(rows, {"glm": neg, "deepseek": []}, inv_norm)
    has_unattested = any(t[2] == "unattested_citation" for t in badtax)
    ok = pg - ng > 0.2 and has_unattested
    print(json.dumps({"control": "positive_vs_mutated", "positive_gloss_f1": round(pg, 4),
                      "negative_gloss_f1": round(ng, 4), "negative_unattested_citation": has_unattested,
                      "verdict": "PASS" if ok else "FAIL"}, indent=2))
    return 0 if ok else 1


def canary_check(data, rows, inv_norm, gen):
    labels = data / "canary" / "mg_labels.tsv"
    if not labels.exists():
        print(json.dumps({"canary": "INCONCLUSIVE", "reason": "MG manual labels absent",
                          "template": str(data / "canary" / "mg_labels_template.tsv")}, indent=2))
        return 2
    gold = {}
    with open(labels, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            gold[r["slp1"]] = r
    bykey = {r["slp1"]: r for r in rows if r["split"] == "canary"}
    agree, total = 0, 0
    for m in MODELS:
        for key, row in bykey.items():
            if key not in gen[m]:
                continue
            s = score_one(row, gen[m][key], inv_norm)
            pred = {"gloss_match": int(s["gloss_token_f1"] >= 0.15),
                    "examples_match": int(s["example_recall"] >= 0.34),
                    "citations_match": int(s["citation_gold_match"] > 0)}
            lab = gold.get(key, {})
            for k, v in pred.items():
                if k in lab:
                    total += 1
                    agree += int(int(lab[k]) == v)
    if total < 30:
        print(json.dumps({"canary": "INCONCLUSIVE", "reason": "fewer than 30 labeled decisions", "total": total}, indent=2))
        return 2
    rate = agree / total
    verdict = "PASS" if rate >= 0.8 else "FAIL"
    print(json.dumps({"canary": verdict, "agreement": round(rate, 4), "agree": agree, "total": total}, indent=2))
    return 0 if verdict == "PASS" else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/eval/articlegen")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--canary", action="store_true")
    args = ap.parse_args()
    data = Path(args.data)
    rows = read_sample(data)
    inv_norm = {phrase(x) for x in json.loads((data / "citation_inventory.json").read_text(encoding="utf-8"))}
    gen, parse_fail, recoveries = assemble(data, rows)
    if args.self_test:
        raise SystemExit(self_test(data, rows, inv_norm))
    if args.canary:
        raise SystemExit(canary_check(data, rows, inv_norm, gen))
    scored = {m: [score_one(r, gen[m][r["slp1"]], inv_norm) for r in rows if r["slp1"] in gen[m]] for m in MODELS}
    missing = {m: [r["slp1"] for r in rows if r["slp1"] not in gen[m]] for m in MODELS}
    for m in MODELS:
        for key in missing[m]:
            r = next(x for x in rows if x["slp1"] == key)
            dummy = {"slp1": key, "gloss": "", "examples": [], "citations": [], "root": ""}
            scored[m].append(score_one(r, dummy, inv_norm))
    tax = taxonomy(rows, scored, inv_norm)
    for m in MODELS:
        for key in missing[m]:
            tax.append((m, key, "response_parse_failure", "no JSON object for this headword"))
    agg = aggregate(scored, parse_fail, rows)
    # Persist normalised, canonical-key generations for downstream consumers.
    for m in MODELS:
        with open(data / f"gen_{m}.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                if r["slp1"] in gen[m]:
                    f.write(json.dumps(gen[m][r["slp1"]], ensure_ascii=False) + "\n")
    extra = {"input_sha256": {"sample": sha(data / "sample.tsv"),
                              "citation_inventory": sha(data / "citation_inventory.json")},
             "missing": missing, "key_recoveries": recoveries}
    summary = write_outputs(data, rows, scored, tax, agg, extra)
    print(f"PASS: {agg['glm']['n_main']} items/model scored; taxonomy instances {summary['taxonomy_examples']}")
    print(f"canary: {summary['canary']}")


if __name__ == "__main__":
    main()
