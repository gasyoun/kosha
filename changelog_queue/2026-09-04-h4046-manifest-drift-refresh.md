# H4046 — manifest drift-refresh: 11 счётчиков приведены к замерам 04-09-2026

**Date:** 04-09-2026 · **Tier:** OxAlpha `zai-coding-plan/glm-5.3-flash` · **Box:** Mac

Второй PR из GTD-строки H4046 «refresh 15 manifest-каунтов» (4 из 15 уже ушли в
[#522](https://github.com/gasyoun/kosha/pull/522): sandhi-curriculum 2634, sandhi-drills 399,
gita-inflection-qa 661, dcs-cdsl-xref 98,606). Здесь оставшиеся 11 — из evidence-JSON
[аудита](https://github.com/gasyoun/Uprava/blob/main/docs/REPORT_H4046_kosha_derived-datasets-regen-audit_04-09-2026.md)
и прямых замеров ночи:

**Обновлённые rows/size (артефакт действительно пересобран или манифест врал против своего же файла):**

1. `samudra-corpus-db` — rows 580,552 → **744,151**, size → 648,073,216 (corpus.db пересобран ночью; корпус рос).
2. `kosha-db` — size → 1,767,456,768; в regen_checked зафиксированы полные счётчики DAG
   (entries 444,773 / lemmas 323,425 / senses 692,404 / forms 1,378,401 exact; **inflections 6,930,902**,
   +14,380 против винтажной ноты 6,916,522).
3. `pwg-scan-index-campaign` — rows 82 → **80**: манифест противоречил собственному закоммиченному трекеру.

**Только regen_checked-ноты (закоммиченный артефакт НЕ тронут — перерезка = решение владельца, не голосование):**
markup-tag-census (679 vs 671; csl-orig 44→45 словарей) · correction-loci (61,571 vs 39,540; ~22k поздних
MW-записей, selftest green) · sense-corpus-concordance (85,763; −1.5 % churn) ·
defgen-heritage-second-reference (3,663; −2.1 %) · pwg-ru-mdf-export (2,449; стор растёт) ·
pwg-de-edition-v1 (11,499; −0.7 %) · pwg-ru-data-workingset (11,519; −0.72 %) ·
pwg-mw-ap-sense-coverage (2,128; −23.1 % store-state drift, детерминированный скрипт зелен).
