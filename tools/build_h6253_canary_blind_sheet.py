#!/usr/bin/env python3
"""Build the LOCAL-ONLY blind MG review sheet for the H6253 canary.

15 cards = 5 held-out slp1 headwords x 3 criteria (gloss/examples/citations).
Each card shows the frozen Cologne MW v02 gold and BOTH generated articles
(GLM 5.3 Flash, DeepSeek 4.1 Flash) side by side. The reviewer records ONE
binary decision per card; the existing scorer then compares that single label
against its own per-model predictions (15 labels -> 30 scored comparisons).

BLIND BY CONSTRUCTION: this generator never reads scores_per_item.tsv,
scores_summary.json, or the decision thresholds in articlegen_score.py.
Nothing in the emitted HTML reveals what the script predicted. Adding a
prediction to a card would make the reproduction check circular.

Do NOT publish this sheet to the public vote hub: its 5 rows are held-out
eval items and would be contaminated by exposure.
"""
from __future__ import annotations

import csv
import html as H
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
DATA = REPO / "data" / "eval" / "articlegen"
OUT = REPO / "review" / "kosha-h6253-mg-canary-blind_18-11-26_review.html"
SHEET_ID = "kosha-h6253-mg-canary-blind_18-11-26"

from csl_pyutil import mark_cyrillic, render_review_sheet  # noqa: E402
from csl_pyutil.evidence import EvidenceManifest, find_slp1  # noqa: E402

CRITERIA = (
    ("gloss", "глосса", "gold_gloss", "gloss",
     "Совпадает ли смысл глоссы с эталоном? Другая формулировка при том же значении — «верно»."),
    ("examples", "примеры", "gold_examples", "examples",
     "Соответствуют ли приведённые примеры эталонным? Частичное совпадение допустимо."),
    ("citations", "цитаты", "gold_citations", "citations",
     "Соответствуют ли цитаты/источники эталону? Выдуманный источник — «неверно»."),
)
MODELS = (("glm", "GLM 5.3 Flash", "gen_glm.jsonl"),
          ("deepseek", "DeepSeek 4.1 Flash", "gen_deepseek.jsonl"))


def esc(value) -> str:
    return H.escape(str(value), quote=False)


def block(label: str, value) -> str:
    """One verbatim evidence block; lists render as a bullet list."""
    if isinstance(value, list):
        items = "".join("<li>%s</li>" % esc(v) for v in value) or "<li>— (пусто)</li>"
        body = "<ul>%s</ul>" % items
    else:
        body = "<pre style='white-space:pre-wrap'>%s</pre>" % (esc(value) or "— (пусто)")
    return "<p><b>%s</b></p>%s" % (esc(label), body)


def load():
    with open(DATA / "sample.tsv", encoding="utf-8") as fh:
        sample = [r for r in csv.DictReader(fh, delimiter="\t") if r["split"] == "canary"]
    gens = {}
    for key, _label, filename in MODELS:
        rows = {}
        with open(DATA / filename, encoding="utf-8") as fh:
            for line in fh:
                rec = json.loads(line)
                rows[rec["slp1"]] = rec
        gens[key] = rows
    return sample, gens


def main() -> int:
    sample, gens = load()
    assert len(sample) == 5, "canary must hold 5 held-out headwords"
    items = []
    for row in sample:
        slp1, iast = row["slp1"], row["iast"]
        for ckey, crussian, gold_field, gen_field, rule in CRITERIA:
            gold = (json.loads(row[gold_field])
                    if gold_field in ("gold_examples", "gold_citations")
                    else row[gold_field])
            parts = [
                "<p><b>Слово:</b> %s (<code>%s</code>) · эталон: Cologne MW v02, строка %s</p>"
                % (esc(iast), esc(slp1), esc(row["mw_line"])),
                "<p><b>Правило критерия:</b> %s</p>" % mark_cyrillic(esc(rule)),
                block("ЭТАЛОН — Cologne MW v02", gold),
            ]
            for key, label, _fn in MODELS:
                gen = gens[key].get(slp1, {})
                parts.append(block("СГЕНЕРИРОВАНО — %s" % label, gen.get(gen_field, "")))
            parts.append(mark_cyrillic(
                "<p class='muted'>Оцените пару сгенерированных текстов относительно эталона. "
                "Одно решение на карточку; оно будет применено к обеим моделям.</p>"))
            items.append({
                "id": "h6253-canary-%s-%s" % (slp1, ckey),
                "filt": ckey,
                "title": mark_cyrillic("%s · %s — %s верна?" % (iast, "GLM / DeepSeek", crussian)),
                "badges": [crussian, "H6253", "canary", "held-out"],
                "question": "".join(parts),
                "panels": [(
                    mark_cyrillic("Что делает решение"),
                    mark_cyrillic(
                        "<p><b>«1 — верно»</b> ставит 1 в ячейку <code>%s</code> файла "
                        "<code>mg_labels.tsv</code>: скрипт должен считать этот критерий совпадающим.</p>"
                        "<p><b>«0 — неверно»</b> ставит 0: скрипт должен считать критерий несовпадающим.</p>"
                        "<p><b>«не знаю»</b> оставляет ячейку незаполненной — конвертер откажется "
                        "писать файл, пока не заполнены все 15 решений.</p>"
                        "<p>Оценки скрипта, пороги и <code>scores_per_item.tsv</code> намеренно "
                        "не показаны: проверка воспроизводимости должна быть слепой.</p>" % ckey)),
                ],
                "note_placeholder": mark_cyrillic("Почему верно / неверно — коротко"),
            })

    manifest = EvidenceManifest(sheet_id=SHEET_ID, row_ids=[it["id"] for it in items],
                                repo_root=str(REPO))
    for it in items:
        manifest.add_card(it["id"], [
            "data/eval/articlegen/sample.tsv",
            "data/eval/articlegen/gen_glm.jsonl",
            "data/eval/articlegen/gen_deepseek.jsonl",
        ])
    manifest.declare_joined("data/eval/articlegen/sample.tsv",
                            fields=["slp1", "iast", "gold_gloss", "gold_examples",
                                    "gold_citations", "mw_line"])
    manifest.declare_joined("data/eval/articlegen/gen_glm.jsonl",
                            fields=["slp1", "gloss", "examples", "citations"])
    manifest.declare_joined("data/eval/articlegen/gen_deepseek.jsonl",
                            fields=["slp1", "gloss", "examples", "citations"])
    manifest.declare_omitted(
        "data/eval/articlegen/scores_per_item.tsv",
        because="contains the script's own per-item predictions; withheld so MG's "
                "reproduction check stays blind (a visible prediction makes agreement circular)")
    manifest.declare_omitted(
        "scripts/articlegen_score.py decision thresholds",
        because="gloss_token_f1>=0.15 / example_recall>=0.34 / citation_gold_match>0 are the "
                "thing being checked; showing them would bias the gold labels")
    manifest.declare_omitted(
        "data/eval/articlegen/sample.meta.json",
        because="provenance only (union + Cologne sha256); no judgment-relevant field")

    config = {
        "sheet_id": SHEET_ID,
        "title": mark_cyrillic("H6253 — слепая разметка канарки: 5 слов × 3 критерия"),
        "subtitle": mark_cyrillic(
            "15 решений MG против замороженного золота Cologne MW v02. Оценки скрипта скрыты "
            "намеренно: это проверка воспроизводимости, а не подтверждение предсказаний."),
        "footer": mark_cyrillic(
            "✅ «1 — верно» = критерий совпадает с эталоном → 1 в mg_labels.tsv · "
            "❌ «0 — неверно» = не совпадает → 0 · ⏸ «не знаю» = ячейка остаётся пустой, "
            "конвертер не даст написать файл. Заметка — комментарий к решению."),
        "approve_label": mark_cyrillic("1 — верно"),
        "reject_label": mark_cyrillic("0 — неверно"),
        "filters": [("gloss", "глоссы"), ("examples", "примеры"),
                    ("citations", "цитаты"), ("all", "все")],
        "generated": "2026-11-18",
        "show_ids": True,
        "note_min_height_px": 88,
        "save_as": "kosha/review/kosha-h6253-mg-canary-blind_18-11-26_decisions.json",
        "identity_gate": {
            "patterns": [r"h6253-canary-[a-z0-9-]+", "H6253"],
            "labels": {"H6253": "H6253"},
        },
        "non_decision_share": 0.0,
    }
    # The gold text is quoted verbatim for citation accuracy (review-sheet language
    # rule), so its SLP1-shaped tokens are source quotes, not human-facing jargon.
    flat = "\n".join(it["question"] + "".join(b for _h, b in it.get("panels", []))
                     for it in items)
    config["preflight"] = {
        "allow_slp1_tokens": sorted({r["slp1"] for r in sample} | set(find_slp1(flat)))
    }
    screening = {
        "deterministic": 0,
        "lookup": 0,
        "agent": 0,
        "human": len(items),
        "evidence_path": "https://github.com/gasyoun/kosha/blob/main/data/eval/articlegen/REPORT.md",
        "rules": [
            "canary-labels-are-the-human-act (H6253 gate human:MG; script verdict INCONCLUSIVE without labels)",
            "no-machine-resolvable-cards: any agent-supplied label would make the reproduction check circular/false-green",
            "blind-source-set: scores and thresholds deliberately omitted via EvidenceManifest",
        ],
    }
    html_out = render_review_sheet(items, config, extras=True,
                                   screening=screening, manifest=manifest)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html_out, encoding="utf-8")
    print("sheet: %s (%d cards, %d bytes)" % (OUT.relative_to(REPO), len(items), len(html_out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
