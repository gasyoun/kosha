# H4046 — re-cut applied after the 3/3 approve vote (regen-recuts sheet, 04-09-2026)

**Date:** 04-09-2026 · **Tier:** OxAlpha `zai-coding-plan/glm-5.3-flash` · **Box:** Mac

MG проголосовал [лист](https://gasyoun.github.io/vote/sheets/h4046_regen_recuts_3.html) **3/3 approve**
(chat-declared, «voted all yes at uprava-h4046-regen-recuts_04-09-26_decisions»). Применено:

1. **D1 sandhi-curriculum**: committed
   [data/sandhi/sandhi_curriculum.tsv](https://github.com/gasyoun/kosha/blob/main/data/sandhi/sandhi_curriculum.tsv)
   перерезан 2,181 → **2,634 правил** (билдер не менялся с H902; 0 правил потеряно, +453 новых на
   сегодняшнем corpus_sandhi.tsv). Каскад: sandhi-drills 396 → **399** (tsv/json/apkg).
2. **D3 gita-inflection-qa**: ledger
   [data/gita/gita_inflection_divergences.tsv](https://github.com/gasyoun/kosha/blob/main/data/gita/gita_inflection_divergences.tsv)
   перерезан 1,279 → **661** против проверенного нового kosha.db (согласие 93.0 → 98.7 %); QA-отчёт обновлён.
3. **D2 dcs-cdsl-xref**: v2 построен и сверен — **98,606 attested лемм, 56,377 linked (57.2 %)**
   (v1: 15,902 / 81.4 % на pre-conllu-rewrite мастере). Сам файл закоммичен в kosha как
   [data/xref/dcs_cdsl_xref_v2__pending-upstream.tsv](https://github.com/gasyoun/kosha/tree/main/data/xref)
   — **апстрим-коммит в csl-apidev ОЧЕРЕДНОЙ**: csl-apidev под Cologne-fence (DANGER_FACTS,
   «csl-orig + all Cologne upstreams are fenced»), прямые PR запрещены. GTD `@DO` на batch-PR путь.

Manifest rows обновлены (rows + size_bytes + `regen_checked` → «VOTED re-cut applied») для всех
четырёх затронутых датасетов. Остальные 12 устаревших счётчиков из H4046-аудита остаются на
GTD-строке «refresh 15 manifest-каунтов» (не голосовались).
