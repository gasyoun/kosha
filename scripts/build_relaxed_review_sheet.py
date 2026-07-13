#!/usr/bin/env python
"""Generate the /review-sheet HTML for H836 Task A -- MG's human-gated
adjudication of the 2,171 relaxed-tier dict<->corpus link candidates
quarantined by the Q1 (H380) concordance build.

Reads data/concordance/relaxed_candidates_classified.tsv (produced by
scripts/classify_relaxed_candidates.py) and emits a self-contained,
Russian-language voting sheet to review/kosha-concordance-relaxed_q2_review.html
(gitignored -- a personal working artifact, not a repo deliverable, per the
org's /review-sheet convention).

worth-a-closer-look items (740, the a/ā gender-stem pattern) are listed
first since they need the most attention; likely-spurious (1,431, the
default per the Q1 golden sample) follow. Nothing here is pre-approved --
MG's votes, exported as kosha-concordance-relaxed_q2_decisions.json, are
the only path to asserting a link into the concordance.
"""
import csv
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "concordance" / "relaxed_candidates_classified.tsv"
OUT_DIR = ROOT / "review"
OUT = OUT_DIR / "kosha-concordance-relaxed_q2_review.html"
SHEET_ID = "kosha-concordance-relaxed_q2"

AXIS_RU = {
    "vowel-length": "долгота гласного",
    "sibilant": "сибилянт (s/ś/ṣ)",
    "retroflex-dental": "ретрофлексный/дентальный (t/ṭ, d/ḍ)",
    "nasal": "носовой (n/ṇ/ṅ/ñ/ṃ)",
    "liquid-vocalic": "плавный/слогообразующий (r/ṛ, l/ḷ)",
    "other": "иное",
    "length-mismatch": "несовпадение длины",
    "none": "нет различий",
}


def axis_ru(axis):
    return " + ".join(AXIS_RU.get(a, a) for a in axis.split("+"))


def rationale_ru(row):
    cls = row["pre_classification"]
    axis = row["axis"]
    n_diff = int(row["n_diff"])
    pos = int(row["first_diff_pos"])
    wl = int(row["word_len"])
    axis_txt = axis_ru(axis)
    if n_diff < 0:
        return ("Несовпадение длины SLP1-ключей после транслитерации — нетипично для уровня "
                "«relaxed», требуется ручная проверка.")
    if cls == "worth-a-closer-look":
        return ("Единственное различие — {axis} в конце {wl}-буквенного слова (позиция {pos}). "
                "Правдоподобно объясняется вариантом словарной формы основы (напр. муж./ср. род "
                "на -a против жен. рода на -ā у того же слова), а не двумя разными словами. "
                "Это НЕ предварительное одобрение — только более вероятный кандидат для approve."
                ).format(axis=axis_txt, wl=wl, pos=pos)
    if n_diff == 0:
        return "Ключи SLP1 совпадают после транслитерации (неожиданно) — проверить edge case to_slp1()."
    if wl <= 4:
        return ("Короткое слово ({wl} симв.) с различием «{axis}» — высокий риск случайного "
                "совпадения (по золотой выборке Q1: похожий уровень «relaxed» оказался неверным "
                "в 3 случаях из 3).").format(wl=wl, axis=axis_txt)
    if n_diff > 1:
        return ("{n} различающихся позиций ({axis}) — расхождение сразу по нескольким осям, "
                "типично для двух разных слов, а не варианта написания.").format(n=n_diff, axis=axis_txt)
    return ("Единичное различие «{axis}» внутри слова (позиция {pos} из {wl}) — та же ось, что "
            "золотая выборка Q1 признала семантически неверной (напр. vikarṣaṇa ‘волочение’ vs "
            "vikarśana ‘истощение’).").format(axis=axis_txt, pos=pos, wl=wl)


def load_rows():
    with open(SRC, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        return list(r)


def main():
    rows = load_rows()
    print("loaded", len(rows), "candidate rows")

    items = []
    for row in rows:
        cls = row["pre_classification"]
        badge_ru = "Требует внимания" if cls == "worth-a-closer-look" else "Вероятно ошибочно"
        item_id = "%s|%s" % (row["anchor_key_slp1"], row["dcs_lemma_id"])
        title = "%s (%s) ↔ DCS «%s» (lemma %s)" % (
            row["anchor_iast"], row["anchor_key_slp1"], row["dcs_lemma_iast"], row["dcs_lemma_id"])
        context = (
            "<div class=\"badge %s\">%s</div>"
            "<div class=\"kv\"><b>Словарный заголовок:</b> %s <span class=\"slp\">(%s)</span></div>"
            "<div class=\"kv\"><b>Лемма DCS:</b> %s <span class=\"slp\">(id %s)</span></div>"
            "<div class=\"kv\"><b>Частота леммы в корпусе (evidence_count):</b> %s токенов</div>"
            "<div class=\"rationale\">%s</div>"
        ) % (
            "worthlook" if cls == "worth-a-closer-look" else "spurious", badge_ru,
            row["anchor_iast"], row["anchor_key_slp1"],
            row["dcs_lemma_iast"], row["dcs_lemma_id"],
            row["evidence_count"],
            rationale_ru(row),
        )
        items.append({
            "id": item_id, "title": title, "context": context,
            "links": [], "default": None,
            "_sort_cls": 0 if cls == "worth-a-closer-look" else 1,
            "_evidence": int(row["evidence_count"]),
        })

    # worth-a-closer-look first, then likely-spurious; within each, higher evidence first
    items.sort(key=lambda x: (x["_sort_cls"], -x["_evidence"]))
    for it in items:
        del it["_sort_cls"], it["_evidence"]

    n_worthlook = sum(1 for r in rows if r["pre_classification"] == "worth-a-closer-look")
    n_spurious = len(rows) - n_worthlook
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    items_json = json.dumps(items, ensure_ascii=False)

    html = HTML_TEMPLATE.format(
        sheet_id=SHEET_ID,
        generated=generated,
        n_total=len(items),
        n_worthlook=n_worthlook,
        n_spurious=n_spurious,
        items_json=items_json,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("wrote:", OUT, "(%d items)" % len(items))


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>kosha — проверка relaxed-кандидатов (Q2, H836)</title>
<style>
:root {{ --ink:#222; --mut:#667; --line:#ddd; --bg:#faf9f6; --card:#fff;
        --ok:#0a7a2f; --no:#b3261e; --defer:#a05a00; --worthlook:#8a4baf; --spurious:#888; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font:15px/1.5 Georgia,'Times New Roman',serif; color:var(--ink); background:var(--bg); }}
header {{ background:#2b3a4a; color:#fff; padding:14px 20px; position:sticky; top:0; z-index:5; }}
header h1 {{ margin:0; font-size:18px; font-weight:normal; }}
header .sub {{ font-size:12.5px; opacity:.8; margin-top:3px; }}
#tally {{ position:sticky; top:64px; z-index:4; background:#eef0f3; border-bottom:1px solid var(--line);
          padding:8px 20px; font-size:13.5px; display:flex; gap:16px; flex-wrap:wrap; align-items:center; }}
#tally b {{ font-size:15px; }}
#savebar {{ position:sticky; top:64px; z-index:4; }}
main {{ max-width:880px; margin:0 auto; padding:14px 20px 80px; }}
#toolbar {{ display:flex; gap:10px; margin:10px 0 16px; flex-wrap:wrap; }}
#toolbar button {{ font-size:13px; padding:7px 12px; border:1px solid var(--line); border-radius:6px;
                    background:var(--card); cursor:pointer; }}
#toolbar button:hover {{ background:#eef2f6; }}
.item {{ background:var(--card); border:1px solid var(--line); border-radius:8px;
         padding:14px 18px; margin:12px 0; }}
.item.voted-approve {{ border-left:5px solid var(--ok); }}
.item.voted-reject {{ border-left:5px solid var(--no); }}
.item.voted-defer {{ border-left:5px solid var(--defer); }}
.item h3 {{ margin:0 0 8px; font-size:16px; font-weight:normal; }}
.badge {{ display:inline-block; font-size:11px; color:#fff; border-radius:8px; padding:2px 9px; margin-bottom:6px; }}
.badge.worthlook {{ background:var(--worthlook); }}
.badge.spurious {{ background:var(--spurious); }}
.kv {{ font-size:14px; margin:2px 0; }}
.slp {{ color:var(--mut); font-family:Consolas,monospace; font-size:12.5px; }}
.rationale {{ font-size:13.5px; color:#444; margin-top:8px; padding-top:7px; border-top:1px dashed var(--line); }}
.votebar {{ margin-top:10px; display:flex; gap:8px; align-items:center; flex-wrap:wrap; }}
.votebar button {{ font-size:13px; padding:6px 14px; border-radius:6px; border:1px solid var(--line);
                    cursor:pointer; background:#f7f7f5; }}
.votebar button.approve.active {{ background:var(--ok); color:#fff; border-color:var(--ok); }}
.votebar button.reject.active {{ background:var(--no); color:#fff; border-color:var(--no); }}
.votebar button.defer.active {{ background:var(--defer); color:#fff; border-color:var(--defer); }}
.votebar input[type=text] {{ flex:1; min-width:160px; font-size:13px; padding:5px 8px;
                              border:1px solid var(--line); border-radius:5px; font-family:inherit; }}
#legend {{ border-top:2px solid var(--line); margin-top:30px; padding-top:12px; font-size:12.5px; color:var(--mut); }}
#legend b {{ color:var(--ink); }}
a {{ color:#1a6fb0; }}
kbd {{ background:#eee; border-radius:3px; padding:0 5px; font-size:11.5px; border:1px solid #ccc; }}
</style>
</head>
<body>
<header>
  <h1>Проверка relaxed-кандидатов дict↔corpus <span style="opacity:.6">· Q2 (H836) · kosha concordance program</span></h1>
  <div class="sub">2 171 связь уровня «relaxed» (Q1/H380), помещённая в карантин после того как золотая выборка
  Q1 признала этот уровень семантически неверным в 3 случаях из 3. Только одобренные здесь связи будут
  добавлены в конкорданс. Сгенерировано {generated}.</div>
</header>
<div id="tally">
  <span>Всего: <b id="t-total">{n_total}</b></span>
  <span style="color:var(--ok)">Одобрено: <b id="t-approve">0</b></span>
  <span style="color:var(--no)">Отклонено: <b id="t-reject">0</b></span>
  <span style="color:var(--defer)">Отложено: <b id="t-defer">0</b></span>
  <span style="color:var(--mut)">Без решения: <b id="t-unvoted">{n_total}</b></span>
  <span id="save-status" style="margin-left:auto; color:var(--mut)"></span>
</div>
<main>
  <div id="toolbar">
    <button id="btn-save-picker">💾 Сохранить в папку (авто)…</button>
    <button id="btn-download">⬇ Скачать {sheet_id}_decisions.json</button>
    <button id="btn-clear">Очистить голоса (localStorage)</button>
    <span style="font-size:12.5px;color:var(--mut);align-self:center">
      Клавиши: <kbd>a</kbd> одобрить · <kbd>r</kbd> отклонить · <kbd>d</kbd> отложить ·
      <kbd>&darr;</kbd>/<kbd>&uarr;</kbd> следующий/предыдущий пункт
    </span>
  </div>
  <div style="font-size:13px;color:var(--mut);margin-bottom:10px">
    Требует внимания: <b>{n_worthlook}</b> (сортированы первыми — единственное различие: долгота
    гласного в конце слова, вероятный вариант основы муж./ср. -a vs жен. -ā). Вероятно ошибочно:
    <b>{n_spurious}</b> (значение по умолчанию по итогам золотой выборки Q1).
  </div>
  <div id="items"></div>
  <div id="legend">
    <b>Одобрить (✅)</b> — принять предложенную связь как есть (одобрение = согласие добавить связь
    в конкорданс именно в этом виде; отдельного «одобрить с правкой» нет — для частичной правки
    используйте поле заметки и Отложить).<br>
    <b>Отклонить (❌)</b> — оставить связь в карантине, не добавлять в конкорданс.<br>
    <b>Отложить (⏸)</b> — пока не уверены, решить позже.<br>
    Поле заметки — для пометки о частичной правке или сомнении, а не только для причины отказа.
  </div>
</main>
<script>
var SHEET_ID = "{sheet_id}";
var ITEMS = {items_json};
var votes = {{}};
var notes = {{}};
var fileHandle = null;
var saveTimer = null;

function loadLocal() {{
  try {{
    var raw = localStorage.getItem("reviewsheet_" + SHEET_ID);
    if (raw) {{ var d = JSON.parse(raw); votes = d.votes || {{}}; notes = d.notes || {{}}; }}
  }} catch (e) {{}}
}}
function saveLocal() {{
  try {{ localStorage.setItem("reviewsheet_" + SHEET_ID, JSON.stringify({{votes: votes, notes: notes}})); }} catch (e) {{}}
}}

function esc(t) {{ var d = document.createElement("div"); d.textContent = t || ""; return d.innerHTML; }}

function renderItems() {{
  var host = document.getElementById("items");
  host.innerHTML = ITEMS.map(function(it, i) {{
    var v = votes[it.id];
    var cls = v ? ("voted-" + v) : "";
    return '<div class="item ' + cls + '" data-idx="' + i + '" data-id="' + esc(it.id) + '">' +
      '<h3>' + esc(it.title) + '</h3>' +
      it.context +
      '<div class="votebar">' +
        '<button class="approve' + (v === "approve" ? " active" : "") + '" data-v="approve">✅ Одобрить</button>' +
        '<button class="reject' + (v === "reject" ? " active" : "") + '" data-v="reject">❌ Отклонить</button>' +
        '<button class="defer' + (v === "defer" ? " active" : "") + '" data-v="defer">⏸ Отложить</button>' +
        '<input type="text" placeholder="заметка (необязательно)" value="' + esc(notes[it.id] || "") + '">' +
      '</div>' +
    '</div>';
  }}).join("");
  Array.prototype.forEach.call(host.querySelectorAll(".item"), function(div) {{
    var id = div.dataset.id;
    Array.prototype.forEach.call(div.querySelectorAll(".votebar button"), function(btn) {{
      btn.onclick = function() {{ setVote(id, btn.dataset.v, div); }};
    }});
    var inp = div.querySelector("input[type=text]");
    inp.oninput = function() {{ notes[id] = inp.value; saveLocal(); scheduleAutoSave(); }};
  }});
}}

function setVote(id, v, div) {{
  votes[id] = (votes[id] === v) ? null : v;
  if (votes[id] === null) delete votes[id];
  saveLocal();
  updateTally();
  Array.prototype.forEach.call(div.querySelectorAll(".votebar button"), function(b) {{
    b.classList.toggle("active", votes[id] === b.dataset.v);
  }});
  div.className = "item" + (votes[id] ? (" voted-" + votes[id]) : "");
  scheduleAutoSave();
}}

function updateTally() {{
  var a=0,r=0,d=0;
  ITEMS.forEach(function(it) {{
    var v = votes[it.id];
    if (v === "approve") a++; else if (v === "reject") r++; else if (v === "defer") d++;
  }});
  document.getElementById("t-approve").textContent = a;
  document.getElementById("t-reject").textContent = r;
  document.getElementById("t-defer").textContent = d;
  document.getElementById("t-unvoted").textContent = ITEMS.length - a - r - d;
}}

function buildDecisions() {{
  return {{
    sheet_id: SHEET_ID,
    generated: "{generated}",
    decided: Object.keys(votes).length,
    items: ITEMS.map(function(it) {{
      return {{ id: it.id, decision: votes[it.id] || null, note: notes[it.id] || "" }};
    }})
  }};
}}

function downloadDecisions() {{
  var blob = new Blob([JSON.stringify(buildDecisions(), null, 2)], {{type: "application/json"}});
  var a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = SHEET_ID + "_decisions.json";
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
}}

function scheduleAutoSave() {{
  if (!fileHandle) return;
  clearTimeout(saveTimer);
  saveTimer = setTimeout(writeToHandle, 1000);
}}
function writeToHandle() {{
  if (!fileHandle) return;
  fileHandle.createWritable().then(function(w) {{
    w.write(JSON.stringify(buildDecisions(), null, 2)).then(function() {{
      w.close();
      document.getElementById("save-status").textContent = "сохранено " + new Date().toLocaleTimeString();
    }});
  }}).catch(function() {{}});
}}

document.getElementById("btn-download").onclick = downloadDecisions;
document.getElementById("btn-clear").onclick = function() {{
  if (confirm("Удалить все голоса из localStorage на этой странице?")) {{
    votes = {{}}; notes = {{}}; saveLocal(); renderItems(); updateTally();
  }}
}};
document.getElementById("btn-save-picker").onclick = function() {{
  if (!window.showSaveFilePicker) {{
    alert("File System Access API недоступен в этом браузере (Chromium-based только). Используйте кнопку «Скачать».");
    return;
  }}
  window.showSaveFilePicker({{suggestedName: SHEET_ID + "_decisions.json"}}).then(function(h) {{
    fileHandle = h;
    document.getElementById("save-status").textContent = "автосохранение включено";
    writeToHandle();
  }}).catch(function() {{}});
}};

// keyboard shortcuts: a/r/d act on the item currently in viewport center; arrows scroll
document.addEventListener("keydown", function(ev) {{
  if (ev.target.tagName === "INPUT") return;
  var items = document.querySelectorAll(".item");
  var mid = window.innerHeight / 2;
  var closest = null, closestDist = Infinity;
  items.forEach(function(div) {{
    var r = div.getBoundingClientRect();
    var dist = Math.abs(r.top + r.height/2 - mid);
    if (dist < closestDist) {{ closestDist = dist; closest = div; }}
  }});
  if (!closest) return;
  var id = closest.dataset.id;
  if (ev.key === "a") setVote(id, "approve", closest);
  else if (ev.key === "r") setVote(id, "reject", closest);
  else if (ev.key === "d") setVote(id, "defer", closest);
  else if (ev.key === "ArrowDown") closest.nextElementSibling && closest.nextElementSibling.scrollIntoView({{block:"center", behavior:"smooth"}});
  else if (ev.key === "ArrowUp") closest.previousElementSibling && closest.previousElementSibling.scrollIntoView({{block:"center", behavior:"smooth"}});
}});

loadLocal();
renderItems();
updateTally();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
