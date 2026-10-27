#!/usr/bin/env python
"""Build the Ayodhyā 1 DCS syntax reading pack (26-10-2026 grill D0–D7).

Additive sibling of build_reading_pack.py, not a replacement for the 23 existing
packs. Consumes the canonical VisualDCS master, kosha WordSem decode inventory,
and SamudraManthanam's Grincer alignment. Russian translation is link-only:
no Grincer text is read into the emitted pack or copied to the public dataset.
"""
import argparse
import difflib
import html
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_reading_pack import (  # noqa: E402
    DCS, KOSHA_DB, LINK_TIERS, build_matcher, card_token, gloss_of, morph_str,
)
from concordance_core import citable_locus, form_key, human_locus, to_slp1  # noqa: E402

SAMUDRA = ROOT.parent / "SamudraManthanam" / "web" / "corpus_builder" / "jsonl" / "02_ramayana-ayodhyakanda.jsonl"
WORDSEM = ROOT / "data" / "frequency" / "wordsem_inventory.tsv"
GRINCER_URL = "https://samskrtam.ru/parallel-corpus/02_ramayana-ayodhyakanda.html"
TEXT_ID = 143
REF = "Rām, Ay, 1"
SLUG = "ayodhya-1"
MATCH_FLOOR = 0.45

CASE_LABELS = {
    "Nom": "Именительный", "Acc": "Винительный", "Ins": "Творительный",
    "Dat": "Дательный", "Abl": "Аблатив", "Gen": "Родительный",
    "Loc": "Локатив", "Voc": "Звательный", "Cpd": "Член композита",
}
ROLE_LABELS = {
    "root": ("predicate", "Сказуемое"),
    "nsubj": ("subject", "Подлежащее"),
    "obj": ("object", "Дополнение"),
    "iobj": ("object", "Дополнение"),
    "cop": ("predicate_support", "Связка"),
    "aux": ("predicate_support", "Вспомогательный глагол"),
}


def norm_text(value):
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    value = form_key(to_slp1(value))
    return "".join(c for c in value if c.isalpha())


def load_grincer():
    """Return Sanskrit source rows after validating every sa/ru pair."""
    source = {}
    ru_groups = set()
    with SAMUDRA.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row.get("chapter") != "1" or row.get("deleted"):
                continue
            if row.get("seg") == "ru":
                ru_groups.add(row["group"])
            elif row.get("seg") == "sa" and row.get("slp1"):
                source[row["passage"]] = row
    paired = {p: r for p, r in source.items() if r["group"] in ru_groups}
    if len(paired) != 51:
        raise ValueError(f"expected 51 validated Grincer pairs, got {len(paired)}")
    return paired


def content_align(sentences, grincer):
    """Monotone content alignment; never use null sent_counter or row position."""
    passages = sorted(grincer, key=lambda p: tuple(map(int, p.split("."))))
    a = [norm_text(s["text_sandhied"]) for s in sentences]
    b = [norm_text(grincer[p]["slp1"]) for p in passages]
    sim = [[difflib.SequenceMatcher(None, x, y).ratio() for y in b] for x in a]
    n, m = len(a), len(b)
    neg = -1e9
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    take = [[False] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            skip = max(dp[i - 1][j], dp[i][j - 1])
            match = dp[i - 1][j - 1] + (sim[i - 1][j - 1] if sim[i - 1][j - 1] >= MATCH_FLOOR else neg)
            if match > skip:
                dp[i][j], take[i][j] = match, True
            else:
                dp[i][j] = skip
    matches = []
    i, j = n, m
    while i and j:
        if take[i][j]:
            matches.append((i - 1, j - 1, sim[i - 1][j - 1]))
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    matches.reverse()
    out = {}
    for i, j, score in matches:
        out[sentences[i]["sent_id"]] = {
            "passage": passages[j], "url": GRINCER_URL,
            "credit": "П. А. Гринцер, «Рамаяна», кн. II, 2006",
            "mode": "link-only", "match_score": round(score, 3),
        }
    return out


def read_wordsem():
    import csv
    with WORDSEM.open(encoding="utf-8", newline="") as f:
        return {r["synset_id"]: r for r in csv.DictReader(f, delimiter="\t")}


def surface_fields(deprel):
    role, label = ROLE_LABELS.get(deprel, (None, None))
    return role, label


def build(built):
    if not DCS.exists():
        raise FileNotFoundError(f"real DCS master missing: {DCS}")
    if not KOSHA_DB.exists():
        raise FileNotFoundError(f"kosha.db missing: {KOSHA_DB}")
    if not SAMUDRA.exists():
        raise FileNotFoundError(f"Grincer alignment missing: {SAMUDRA}")
    if not WORDSEM.exists():
        raise FileNotFoundError(f"WordSem inventory missing: {WORDSEM}")

    grincer = load_grincer()
    wordsem = read_wordsem()
    dcon = sqlite3.connect(f"file:{DCS}?mode=ro", uri=True)
    dcon.row_factory = sqlite3.Row
    kcon = sqlite3.connect(f"file:{KOSHA_DB}?mode=ro", uri=True)
    chapter = dcon.execute(
        "SELECT chapter_id FROM chapter WHERE text_id=? AND ref=?", (TEXT_ID, REF)).fetchone()
    if not chapter:
        raise ValueError(f"missing target chapter {REF}")
    text_name = dcon.execute("SELECT name FROM text WHERE text_id=?", (TEXT_ID,)).fetchone()[0]
    sentences = dcon.execute(
        "SELECT id,sent_id,sent_counter,sent_subcounter,text_sandhied FROM sentence "
        "WHERE chapter_id=? ORDER BY sent_counter,sent_subcounter,id", (chapter[0],)).fetchall()
    links = content_align(sentences, grincer)
    matcher = build_matcher(kcon)

    out_sents = []
    lemma_meta = {}
    unresolved = {}
    tier_counts = {}
    n_tok = n_link = n_dep = n_wordsem = n_gloss_missing = 0
    role_tokens = {"predicate": 0, "subject": 0, "object": 0, "predicate_support": 0}
    for s in sentences:
        toks = dcon.execute(
            "SELECT idx,form,lemma,lemma_id,upos,head,deprel,feat_case,feat_gender,"
            "feat_number,feat_person,feat_tense,feat_mood,feat_voice,m_wordsem,m_unsandhied "
            "FROM token WHERE sentence_id=? ORDER BY idx", (s["id"],)).fetchall()
        otoks = []
        sentence_has_dep = False
        for t in toks:
            n_tok += 1
            lemma_id = t["lemma_id"]
            if lemma_id not in lemma_meta:
                tier, keys = matcher.match(t["lemma"])
                mrow = dcon.execute("SELECT meanings FROM lemma WHERE lemma_id=?", (lemma_id,)).fetchone()
                lemma_meta[lemma_id] = (tier, keys[0] if keys else None,
                                        gloss_of(mrow["meanings"] if mrow else ""))
            tier, key, lemma_gloss = lemma_meta[lemma_id]
            linked = tier in LINK_TIERS and key is not None
            tier_counts[tier or "none"] = tier_counts.get(tier or "none", 0) + 1
            ws = t["m_wordsem"] or None
            if ws:
                n_wordsem += 1
                if ws not in wordsem:
                    raise ValueError(f"undecoded WordSem {ws} at {s['sent_id']}:{t['idx']}")
                gloss = wordsem[ws]["gloss"] or wordsem[ws]["concept"]
                gloss_source = "WordSem"
            else:
                gloss = lemma_gloss
                gloss_source = "lemma-fallback"
            if not gloss:
                n_gloss_missing += 1
            dep = t["head"] is not None and t["head"] != "_" and t["deprel"] not in (None, "_")
            if dep:
                n_dep += 1
                sentence_has_dep = True
            role, role_label = surface_fields(t["deprel"] if dep else None)
            if role:
                role_tokens[role] += 1
            case = t["feat_case"] or None
            tok = {
                "idx": t["idx"], "form": t["form"], "lemma": t["lemma"],
                "upos": t["upos"], "morph": morph_str(t),
                "gloss": gloss, "gloss_source": gloss_source,
                "case": case, "case_label": CASE_LABELS.get(case),
                "surface_role": role, "surface_label": role_label,
                "head": int(t["head"]) if dep else None,
                "deprel": t["deprel"] if dep else None,
                "unsandhied": t["m_unsandhied"] or None,
            }
            if ws:
                tok["wordsem"] = ws
            if linked:
                n_link += 1
                tok.update({"slp1": key, "href": "../w/%s.html" % card_token(key), "tier": tier})
            else:
                tok["resolved"] = False
                if t["lemma"]:
                    unresolved[t["lemma"]] = unresolved.get(t["lemma"], 0) + 1
            otoks.append(tok)
        sent = {
            "n": s["sent_counter"], "sub": s["sent_subcounter"] or None,
            "locus": human_locus(text_name, REF, s["sent_counter"], s["sent_subcounter"]),
            "dcs": citable_locus(s["sent_id"]), "text": s["text_sandhied"],
            "has_dependencies": sentence_has_dep, "tokens": otoks,
        }
        if s["sent_id"] in links:
            sent["parallel"] = links[s["sent_id"]]
        out_sents.append(sent)

    dep_sentences = sum(bool(s["has_dependencies"]) for s in out_sents)
    payload = {
        "slug": SLUG, "title": "Ayodhyā 1 — Rāmāyaṇa, Ayodhyākāṇḍa 1",
        "ref": REF, "text_name": text_name,
        "source": "DCS (Digital Corpus of Sanskrit) — CC BY 4.0",
        "built": built,
        "syntax": {
            "schema": "dcs-ud-v1 + school-surface-v1",
            "default_view": "surface", "case_labels": CASE_LABELS,
            "role_labels": {k: v[1] for k, v in ROLE_LABELS.items()},
            "note": "Surface roles are reversible projections of DCS UD; Cpd is a compound member, not a ninth case.",
        },
        "translation": {
            "credit": "П. А. Гринцер, «Рамаяна», кн. II, 2006",
            "mode": "link-only", "url": GRINCER_URL,
            "note": "No Grincer text is embedded; only validated passage references are emitted.",
        },
        "stats": {
            "sentences": len(out_sents), "tokens": n_tok,
            "linked_tokens": n_link, "link_rate_pct": round(100 * n_link / n_tok, 1),
            "tier_counts": tier_counts, "dependency_tokens": n_dep,
            "dependency_sentences": dep_sentences,
            "unannotated_tokens": n_tok - n_dep,
            "wordsem_tokens": n_wordsem, "lemma_fallback_tokens": n_tok - n_wordsem,
            "gloss_missing_tokens": n_gloss_missing,
            "role_tokens": role_tokens,
            "grincer_links": sum("parallel" in s for s in out_sents),
            "grincer_unlinked_sentences": sum("parallel" not in s for s in out_sents),
        },
        "sentences": out_sents,
    }
    dcon.close()
    kcon.close()
    return payload


def validate(payload):
    errors = []
    st = payload["stats"]
    toks = [t for s in payload["sentences"] for t in s["tokens"]]
    checks = {
        "sentences": (len(payload["sentences"]), 46),
        "tokens": (len(toks), 476),
        "dependency_tokens": (sum(t["head"] is not None for t in toks), 468),
        "dependency_sentences": (sum(s["has_dependencies"] for s in payload["sentences"]), 44),
        "unannotated_tokens": (sum(t["head"] is None for t in toks), 8),
        "wordsem_tokens": (sum(t["gloss_source"] == "WordSem" for t in toks), 217),
        "lemma_fallback_tokens": (sum(t["gloss_source"] == "lemma-fallback" for t in toks), 259),
        "grincer_links": (sum("parallel" in s for s in payload["sentences"]), 26),
    }
    for key, (actual, expected) in checks.items():
        if actual != expected or st[key] != expected:
            errors.append(f"{key}: actual/stats {actual}/{st[key]} != {expected}")
    for t in toks:
        expected_role, _ = surface_fields(t["deprel"])
        if t["surface_role"] != expected_role:
            errors.append(f"role mismatch at token {t['idx']}: {t['surface_role']} != {expected_role}")
        if t["case"] == "Cpd" and t["case_label"] != "Член композита":
            errors.append("Cpd leaked into case legend")
    links = [(s["dcs"], s["parallel"]) for s in payload["sentences"] if "parallel" in s]
    for sent_id, passage in (("dcs:116062_1", "1.2"), ("dcs:116065_1", "1.3"), ("dcs:116126_1", "1.50")):
        if not any(d == sent_id and p["passage"] == passage for d, p in links):
            errors.append(f"missing alignment canary {sent_id} -> {passage}")
    for sent_id in ("dcs:116053_1", "dcs:116054_1", "dcs:116055_1", "dcs:116057_1", "dcs:116059_1", "dcs:116061_1", "dcs:116061_2"):
        if any(d == sent_id for d, _ in links):
            errors.append(f"unsupported opening link {sent_id}")
    if any("text" in s.get("parallel", {}) for s in payload["sentences"]):
        errors.append("Grincer text leaked into link-only payload")
    if errors:
        raise ValueError("\n".join(errors))


def emit(payload):
    out = ROOT / "reading" / "data"
    out.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, indent=1)
    (out / f"{SLUG}.js").write_text(
        'window.READING_DATA = window.READING_DATA || {};\n'
        f'window.READING_DATA["{SLUG}"] = {body};\n', encoding="utf-8", newline="\n")
    (out / f"{SLUG}.json").write_text(body + "\n", encoding="utf-8", newline="\n")

    st = payload["stats"]
    lines = [
        "# Ayodhyā 1 syntax pack — build report", "",
        "_Generated by `scripts/build_ayodhya_syntax_pack.py`; 26-10-2026._", "",
        f"- DCS: `{REF}` · **{st['sentences']} sentences / {st['tokens']} tokens**",
        f"- Dependencies: **{st['dependency_tokens']} tokens / {st['dependency_sentences']} sentences**; {st['unannotated_tokens']} unannotated tokens retained",
        f"- Surface roles: {st['role_tokens']}",
        f"- Gloss: **{st['wordsem_tokens']} WordSem + {st['lemma_fallback_tokens']} lemma-fallback**; missing gloss {st['gloss_missing_tokens']}",
        f"- Dictionary cards: {st['linked_tokens']} tokens ({st['link_rate_pct']}%)",
        f"- Grincer links: **{st['grincer_links']} validated / {st['grincer_unlinked_sentences']} unlinked**; link-only, no Russian text embedded",
        "", "## Honest residue", "",
        "- `sent_counter` is null for 44/46 DCS sentences, so the existing verse-number mapper cannot be used.",
        "- Seven opening DCS sentences have no counterpart in Grincer's opening; no link is invented.",
        "- Content alignment is monotone and accepts only score ≥ 0.45. The other unmatched sentences stay unlinked because recension and annotation differences make a forced join unsafe.",
        "- `Case=Cpd` means compound member, not a case.", "",
        "## Alignment ledger", "",
        "| DCS sentence | Grincer passage | score |", "|---|---:|---:|",
    ]
    for s in payload["sentences"]:
        p = s.get("parallel")
        lines.append(f"| {s['dcs']} | {p['passage'] if p else '—'} | {p['match_score'] if p else '—'} |")
    lines += ["", "## Unresolved dictionary lemmas", ""]
    counts = {}
    for s in payload["sentences"]:
        for t in s["tokens"]:
            if t.get("resolved") is False:
                counts[t["lemma"]] = counts.get(t["lemma"], 0) + 1
    for lemma, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{lemma}` ×{count}")
    (ROOT / "reading" / "AYODHYA_SYNTAX_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--built", default="2026-10-26")
    ap.add_argument("--check", action="store_true", help="validate the emitted JSON without rebuilding")
    args = ap.parse_args()
    if args.check:
        payload = json.loads((ROOT / "reading" / "data" / f"{SLUG}.json").read_text(encoding="utf-8"))
    else:
        payload = build(args.built)
    validate(payload)
    if not args.check:
        emit(payload)
    st = payload["stats"]
    print(f"PASS {SLUG}: {st['sentences']} sentences / {st['tokens']} tokens; "
          f"deps {st['dependency_tokens']}; WordSem {st['wordsem_tokens']}; "
          f"Grincer links {st['grincer_links']}")


if __name__ == "__main__":
    main()
