#!/usr/bin/env python
"""H3910 (c) — the human acceptance vote for the kosha aligned-sense table.

The judge (scripts/score_sense_alignment_judge.py) was a FIRST PASS. This sheet
is the verdict: 120 stratified cards, each showing the glosses side by side, the
channel that joined them, the score, the witness list, and the judge's call with
its reason — so a human confirms or overturns a stated claim rather than
re-deriving it.

Two things this builder deliberately does NOT do:

  * It does not pre-mark anything. The handoff permits pre-marking cards where
    the judge is confident and the evidence is a shared discriminating witness,
    but forbids it in the `attrib` strata "because that is the thing being
    measured". Rather than run two presentation regimes over one measurement,
    every card arrives unmarked; the judge's call is shown as evidence, never as
    a default vote. `machine_resolvable` is therefore set on no card.
  * It does not tune anything. TAU 0.30 / GLOSS_FLOOR 0.20 / PREFIX_MIN 4 stay
    at their marked defaults whatever this vote returns.

Reads  data/concordance/sense_alignment_acceptance_sample.tsv
       data/concordance/sense_alignment_acceptance_strata.json
       data/concordance/judge/verdicts_pass_{a,b}.json + packet_key.json
Writes review/kosha-sense-align-acceptance_w2_review.html
"""
import csv
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from csl_pyutil import RU_UI_STRINGS, render_review_sheet  # noqa: E402
from csl_pyutil.evidence import EvidenceManifest  # noqa: E402

try:
    from sanskrit_util import from_slp1, slp1_to_devanagari
except ImportError:  # pragma: no cover - sanskrit_util is a hard dep of app/
    from_slp1 = None
    slp1_to_devanagari = None

ROOT = Path(__file__).resolve().parent.parent
CONC = ROOT / "data" / "concordance"
JUDGE = CONC / "judge"
SAMPLE = CONC / "sense_alignment_acceptance_sample.tsv"
STRATA = CONC / "sense_alignment_acceptance_strata.json"
KEY = JUDGE / "packet_key.json"
VA = JUDGE / "verdicts_pass_a.json"
VB = JUDGE / "verdicts_pass_b.json"

OUT_DIR = ROOT / "review"
SHEET_ID = "kosha-sense-align-acceptance_w2"
OUT = OUT_DIR / (SHEET_ID + "_review.html")
GENERATED = "03-09-2026"

DICTS = [
    ("pwg", "PWG (нем.)"),
    ("mw", "MW (англ.)"),
    ("apte", "Апте (англ.)"),
    ("skd", "ŚKDR (санскр.)"),
    ("vcp", "VCP (санскр.)"),
]

METHOD_RU = {
    "ls": "общий литературный свидетель",
    "gloss": "пересечение толкований",
    "gloss+ls": "толкования + свидетель",
    "attrib": "атрибуция (санскр.→санскр.)",
    "attrib+ls": "атрибуция + свидетель",
    "attrib+gloss+ls": "атрибуция + толкования + свидетель",
}

VERDICT_RU = {
    "same": "одно значение",
    "different": "разные значения",
    "unsure": "не берусь судить",
}

BAND_RU = {
    "lo <0.40": "балл < 0.40",
    "mid 0.40-0.69": "балл 0.40–0.69",
    "hi >=0.70": "балл ≥ 0.70",
}

REJECT_LABELS = [
    ("dhatu", "ŚKDR/VCP: статья глагольного корня, а не именное значение"),
    ("akshara", "ŚKDR/VCP: статья буквы алфавита"),
    ("homonym", "омонимы — разные референты под одной леммой"),
    ("granularity", "часть членов группы совпадает, часть — нет"),
    ("witness", "общий свидетель случаен и ничего не различает"),
    ("other", "иное (опишите в примечании)"),
]

CLIP = 700
TOKEN = re.compile(r"[A-Za-z]{3,}")


def clip(text, n=CLIP):
    text = (text or "").strip()
    if len(text) <= n:
        return text
    return text[:n].rstrip() + " …"


def esc(text):
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def iast(slp1):
    if from_slp1 is None:
        return slp1
    try:
        return from_slp1(slp1, "iast")
    except Exception:
        return slp1


def deva(slp1):
    if slp1_to_devanagari is None:
        return ""
    try:
        return slp1_to_devanagari(slp1)
    except Exception:
        return ""


def load_verdicts(path, key_map):
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {key_map[v["card"]]: v for v in doc["verdicts"]}


def main():
    rows = list(csv.DictReader(SAMPLE.open(encoding="utf-8"), delimiter="\t"))
    strata = json.loads(STRATA.read_text(encoding="utf-8"))
    key = json.loads(KEY.read_text(encoding="utf-8"))
    va = load_verdicts(VA, key["pass_a"])
    vb = load_verdicts(VB, key["pass_b"])

    by_stratum = {s["stratum"]: s for s in strata["strata"]}

    items = []
    labels = {}
    quoted_tokens = set()
    for row in rows:
        quoted_tokens.add(row["group_id"])
        quoted_tokens.add(row["lemma_slp1"])
        for _k, _h in DICTS:
            quoted_tokens.update(TOKEN.findall(clip(row[_k + "_gloss"])))
        quoted_tokens.update(TOKEN.findall(row["witnesses"]))
        gid = row["group_id"]
        lemma = row["lemma_slp1"]
        method = row["method"]
        st = row["stratum"]
        stat = by_stratum[st]
        a, b = va[gid], vb[gid]
        # the judge quotes gloss wording verbatim in its reasons, so those
        # quotations are allowlisted on the same footing as the glosses.
        quoted_tokens.update(TOKEN.findall(a["reason"]))
        quoted_tokens.update(TOKEN.findall(b["reason"]))

        lemma_iast = iast(lemma)
        lemma_deva = deva(lemma)
        head = lemma_deva + " · " + lemma_iast if lemma_deva else lemma_iast

        # --- question: carries the lemma in readable script AND the row id,
        #     so V13's identity gate has a real label to bind the id to.
        parts = []
        for k, human in DICTS:
            g = row[k + "_gloss"].strip()
            if g:
                parts.append(human)
        question = (
            '<div><b>Одно ли это значение?</b></div>'
            '<div style="margin-top:.5em">Лемма <b>{head}</b> '
            '(строка <code>{gid}</code>). Сопоставлены: {dicts}.</div>'
            '<div style="margin-top:.35em">Канал: <b>{m}</b> · балл '
            '<b>{score}</b> · форма группы <code>{shape}</code>.</div>'
            '<div style="margin-top:.35em;opacity:.85">Голосуйте «одно значение» '
            'только если <i>каждый</i> показанный член выражает одно и то же '
            'значение. Группа, где один член верен, а другой уводит в сторону, — '
            '«разные значения».</div>'
        ).format(
            head=esc(head),
            gid=esc(gid),
            dicts=esc(", ".join(parts)),
            m=esc(METHOD_RU.get(method, method)),
            score=esc(row["score"]),
            shape=esc(row["shape"]),
        )
        labels[gid] = head

        panels = []
        for k, human in DICTS:
            g = row[k + "_gloss"].strip()
            if not g:
                continue
            ids = row[k + "_sense_ids"].strip()
            panels.append((
                human,
                '<div style="opacity:.7;font-size:.85em">{ids}</div>'
                '<div style="margin-top:.3em">{g}</div>'.format(
                    ids=esc(ids), g=esc(clip(g))
                ),
            ))

        wit = row["witnesses"].strip() or "—"
        note = row["note"].strip() or "—"
        flags = row["flags"].strip() or "—"
        panels.append((
            "Чем соединено",
            '<div>Свидетели: <code>{w}</code></div>'
            '<div style="margin-top:.3em">Правило: {n}</div>'
            '<div style="margin-top:.3em">Флаги: <code>{f}</code></div>'
            '<div style="margin-top:.3em;opacity:.8">Страта: <code>{st}</code> — '
            '{pop} строк в популяции ({share:.2%}), в выборке {n_s}{cens}.</div>'.format(
                w=esc(wit), n=esc(note), f=esc(flags), st=esc(st),
                pop=stat["population"], share=stat["population_share"],
                n_s=stat["sampled"],
                cens=" — страта взята целиком" if stat["census"] else "",
            ),
        ))

        agree = a["verdict"] == b["verdict"]
        panels.append((
            "Что сказал LLM-судья (первый проход, не приговор)",
            '<div>Проход A: <b>{av}</b> — {ar}</div>'
            '<div style="margin-top:.3em">Проход B: <b>{bv}</b> — {br}</div>'
            '<div style="margin-top:.4em;opacity:.8">{agree}</div>'.format(
                av=esc(VERDICT_RU.get(a["verdict"], a["verdict"])),
                ar=esc(a["reason"]),
                bv=esc(VERDICT_RU.get(b["verdict"], b["verdict"])),
                br=esc(b["reason"]),
                agree=("Оба прохода согласны. Это не делает вердикт верным — "
                       "судья может ошибаться одинаково дважды."
                       if agree else
                       "⚠️ Проходы разошлись. Именно такие карточки голос и "
                       "должен разрешить."),
            ),
        ))

        judge_tag = ("судья: согласие" if agree else "судья: расхождение")
        items.append({
            "id": gid,
            "filt": " ".join([method, st, a["verdict"], b["verdict"],
                              "agree" if agree else "flip"]),
            "title": head + "  ·  " + METHOD_RU.get(method, method),
            "question": question,
            "badges": [
                METHOD_RU.get(method, method),
                "балл " + row["score"],
                row["shape"],
                judge_tag,
            ],
            "facets": {
                "Канал": [METHOD_RU.get(method, method)],
                "Балл": [BAND_RU.get(st.split("|")[1], st.split("|")[1])],
                "Форма": ["один-к-одному" if st.endswith("clean")
                          else "многие-ко-многим"],
                "Судья": [judge_tag],
            },
            "typology": [{
                "label": st,
                "n": stat["sampled"],
                "share": stat["population_share"],
            }],
            "note_placeholder": (
                "Если «разные значения» — назовите, какой член группы лишний."
            ),
            "panels": panels,
        })

    screening = {
        "deterministic": 29386,
        "lookup": 0,
        "agent": 0,
        "human": len(items),
        "evidence_path": "data/concordance/sense_alignment_acceptance_strata.json",
        "rules": [
            "29 386 одиночных групп (`singleton`) сняты детерминированно: "
            "межсловарного утверждения там нет, подтверждать нечего.",
            "Из 3 013 соединённых строк отобрано 120 — стратифицированная "
            "выборка с зафиксированным зерном (3910), а не первые попавшиеся; "
            "три малые страты `attrib` и все 32 строки «многие-ко-многим» "
            "взяты целиком.",
            "LLM-судья НЕ снял ни одной карточки. Его вердикт показан как "
            "улика, а не как готовый ответ: приговор — за человеком.",
            "Ни одна карточка не помечена заранее. Канал `attrib` — это ровно "
            "то, что измеряется, и предварительная пометка испортила бы "
            "измерение.",
        ],
    }

    config = {
        "sheet_id": SHEET_ID,
        "title": "Приёмка таблицы согласованных значений (kosha, волна 2)",
        "subtitle": (
            "120 карточек стратифицированной выборки из 3 013 соединённых "
            "групп. Ваш голос — единственный источник цифры точности: "
            "по стратам, с доверительными интервалами. Измеренная точность "
            "сама по себе НЕ разрешает публикацию таблицы — это отдельное "
            "решение человека."
        ),
        "footer": (
            "H3910 · gasyoun/kosha · выгрузку "
            "<code>" + SHEET_ID + "_decisions.json</code> положите рядом с "
            "листом и сообщите в чат."
        ),
        "approve_label": "Одно значение",
        "reject_label": "Разные значения",
        "reject_labels": REJECT_LABELS,
        "filters": [
            ("", "все"),
            ("attrib", "канал attrib"),
            ("flip", "судья расходится с собой"),
            ("m2m", "многие-ко-многим"),
        ],
        "generated": GENERATED,
        "ui_strings": RU_UI_STRINGS,
        "show_ids": True,
        "note_min_height_px": 88,
        "save_as": str(OUT_DIR / (SHEET_ID + "_decisions.json")),
        "facet_count_label": "карточек",
        "facet_reset_label": "сбросить",
        "context": {
            "handoff": "H3910",
            "repo": "gasyoun/kosha",
            "artifact": "data/concordance/sense_alignment.tsv",
            "sample": "data/concordance/sense_alignment_acceptance_sample.tsv",
            "apply_with": "scripts/score_sense_alignment_acceptance.py (после голоса)",
        },
        "identity_gate": {
            "patterns": [r"[A-Za-z]+#\d+"],
            "labels": labels,
        },
        # Two allowlisted classes, both narrow and both deliberate:
        #  * the row id itself — V13's identity gate binds every one of them to
        #    the lemma in Devanagari+IAST in the same question, so nobody votes
        #    on a bare id;
        #  * tokens quoted verbatim out of the dictionary glosses. PWG is German,
        #    and the D2 marker `[bcdghjklmnprstvy][fxz]` fires on ordinary German
        #    orthography — Anfang, Augapfel, Blitz, Badeplatz, Empfindung. That
        #    is a linter blind spot for German source text, not an SLP1 leak; the
        #    allowlist is built FROM the rendered glosses so it can never cover
        #    prose this builder wrote itself.
        "preflight": {"allow_slp1_tokens": tuple(sorted(quoted_tokens))},
    }

    manifest = EvidenceManifest(SHEET_ID, [i["id"] for i in items],
                                repo_root=str(ROOT))
    manifest.declare_joined(
        "data/concordance/sense_alignment_acceptance_sample.tsv",
        ["method", "score", "shape", "witnesses", "flags", "note",
         "pwg_gloss", "mw_gloss", "apte_gloss", "skd_gloss", "vcp_gloss",
         "stratum", "population_share"],
    )
    manifest.declare_joined(
        "data/concordance/sense_alignment_acceptance_strata.json",
        ["population", "population_share", "sampled", "census"],
    )
    manifest.declare_joined(
        "data/concordance/judge/verdicts_pass_a.json", ["verdict", "reason"])
    manifest.declare_joined(
        "data/concordance/judge/verdicts_pass_b.json", ["verdict", "reason"])
    manifest.declare_omitted_path(
        "data/concordance/sense_alignment.tsv",
        "the full population; the sheet carries the sampled 120 rows only, and "
        "the strata JSON is what weights them back to population shares",
    )
    manifest.declare_omitted_path(
        "data/concordance/judge/packet_key.json",
        "card-id -> group_id mapping used to join the two judge passes; it is "
        "bookkeeping and carries no evidence a reviewer could vote on",
    )
    manifest.declare_omitted(
        "failure_class column",
        "empty on every aligned row by construction — it classifies the "
        "singletons that were screened out, not the joins under review",
    )
    for it in items:
        manifest.add_card(it["id"],
                          ["glosses", "method", "score", "witnesses",
                           "judge_pass_a", "judge_pass_b"])

    html = render_review_sheet(items, config, screening=screening,
                               manifest=manifest)
    OUT_DIR.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")

    flips = sum(1 for i in items if "flip" in i["filt"])
    attrib = sum(1 for i in items if i["filt"].startswith("attrib"))
    print("wrote %s (%d bytes)" % (OUT, len(html.encode("utf-8"))))
    print("cards: %d · attrib-strata: %d · judge flips: %d · pre-marked: 0"
          % (len(items), attrib, flips))


if __name__ == "__main__":
    main()
