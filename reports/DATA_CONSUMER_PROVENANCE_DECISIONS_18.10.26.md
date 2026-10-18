# Потребитель и провенанс данных — решения грилла 18-10-2026

_Created: 18-10-2026 · Last updated: 18-10-2026_

**Повод.** Пост [vistehno/5699](https://t.me/vistehno/5699) о [разборе Xena Project](https://xenaproject.wordpress.com/2026/10/16/how-to-formalize-all-of-mathematics/): формальный артефакт ценен использованием, а не корректностью; плохая формализация известного результата хуже отсутствия. Вопрос MG: «How to make it more actionable for us?»

**Метод.** `/grillme`, 19 решений, пять раундов интерактивом (DeepSeek Flash `deepseek-flash`, DSH). Домашка до первого вопроса: `kosha/data/manifest/datasets.json` (149 строк), [DATA_LAYERS_CENSUS.md](https://github.com/gasyoun/Uprava/blob/main/DATA_LAYERS_CENSUS.md) §6, [DATA_HUB_ROADMAP.md](https://github.com/gasyoun/kosha/blob/main/DATA_HUB_ROADMAP.md) (D-HUB-2c), [DANGER_FACTS.md](https://github.com/gasyoun/Uprava/blob/main/DANGER_FACTS.md), [PAPER_LLM_LEXICOGRAPHY.md](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/pwg_ru/PAPER_LLM_LEXICOGRAPHY.md), [AUTOMATION_LLM_ECONOMY_REPORT.md](https://github.com/gasyoun/Uprava/blob/main/AUTOMATION_LLM_ECONOMY_REPORT.md), `tests/test_dataset_catalog.py`, `interlinks_edges.tsv`, `GTD_NEXT_ACTIONS.md`.

**Что уже было сказано до грилла.** D-HUB-2c называет отказ «one-shot deliverables never wired to consumers», но механики нет. В PWG провенанс уже построчный (11 261 строка / 50 корней, 100 % штампов), в манифесте — нет.

## Решения

| № | Вопрос | Решение |
|---:|---|---|
| 1 | Скоуп гейта | Всё, включая внутренние слои репозиториев |
| 2 | Откуда провенанс для 149 строк | Парсер `builder` + ручной триаж 86 остатков |
| 3 | Поля провенанса | `made_by` + `model` + `handoff` (не enum) |
| 4 | Что считается потребителем | Репозиторий, бумага A##, публичная поверхность; агент-сессия — нет |
| 5 | Носитель для внутренних слоёв | Sidecar `<layer>.meta.json`, пишет билдер, агрегирует кроулер |
| 6 | 18 строк без потребителя | Закрыть 2 (есть кандидат высокой уверенности), 16 → `dormant` с датой и владельцем |
| 7 | Что значит «плохой слой» | Неверный > невоспроизводимый > без потребителя; гейт на первый класс |
| 8 | Overlay-гард | По защищённым путям, не по именам скриптов |
| 9 | Round-trip/length-check | Обязателен только для слоёв, идущих в human-gold |
| 10 | «Known result» | Обязательный novelty-абзац в sidecar; фиксы и регенерации не трогаем |
| 11 | Строка цены | Платные прогоны и прогоны свыше 1000 вызовов |
| 12 | Наш «13 млн строк» | Sanskrityatina-трио — кандидат в `dormant`, не в удаление |
| 13 | Где живёт правило | Спека в kosha, хелпер в `sanskrit-util` |
| 14 | Текст | Внутренняя дисциплина + строка в FINDINGS; note не пишем |
| 15 | Порядок | Sidecar + бэкфилл одним хендоффом; гард вторым; виза 18 — после |
| 16 | Стоп-лист | 30 дней: слой без sidecar не регистрируется; релизы не тормозим |
| 17 | Пилот | 3 репозитория: kosha, SanskritSpellCheck, SanskritLexicography |
| 18 | Приёмка | Негативный тест хелпера + покрытие 149 + dormant-строки с владельцем |
| 19 | Скиллы и хендоффы | Отложить до закрытия данных |

## Что из этого следует механически

**Sidecar.** Рядом с каждым производным слоем лежит `<layer>.meta.json`:

```json
{
  "layer": "dcs-compound-dictionary",
  "made_by": "human+ai",
  "model": "claude-sonnet-5",
  "handoff": "H####",
  "consumers": [{"kind": "repo", "id": "kosha", "use": "..."}],
  "status": "active",
  "novelty": "чем слой отличается от уже существующего",
  "roundtrip": {"checked": true, "rows_in": 0, "rows_out": 0}
}
```

`status` — `active | dormant | retired`, у `dormant` обязательны `owner` и `review_after`.

**Гейт.** Хелпер отказывается писать слой, если нет `made_by` или (нет `consumers`, и нет `dormant`). Тест на фикстуре обязан падать на пустом — иначе гейт не проверен.

**Бэкфилл.** 149 строк: H-ID парсится из `builder` (63 строки), модель — из `builder` (5), для 86 «только путь скрипта» поля выводятся из пути и даты первого коммита. Ручного разбора — десяток спорных.

**Dormant-лист (16).** `stenogrammy-teaching-glossary` · `stopovye-parallel-passages` · `dcs-verb-form-frequency-prelim` · `dcs-lsc-pilot` · `archive-stopword-sqlite` · `headword-overlap-matrix-ext` · `mw-defgen-eval-sample` · `gita-inflection-qa` · `gita-gold-vs-dcs-tagging` · `upasarga-atlas` · `zaliznyak-lectures-transcripts` · `sanskrityatina-reverse-index` · `sanskrityatina-sch-cases` · `sanskrityatina-reverse-vs-union16` · `bhs-mw-dcs-key2-crosswalk` · `sanskritgrammar-whitney-dcs-vidyut-crosswalk`. Закрываются как «есть потребитель»: `dcs-compound-dictionary` (names.csv, kosha) и `morphology-giveback-candidates` (csl-inflect).

**Защищённые пути.** Список файлов с human-reviewed статусом (а не 12 имён `apply_*`): писатель в такой путь падает без `ALLOW_OVERLAY_WIPE`. Список ведётся в реестре слоёв, не в коде гарда.

## Работы

1. **Sidecar + бэкфилл** ([H6979](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6979-DeepSeek_kosha_data-layer-sidecar-provenance_18.10.26.md), agent lane, ~4–5 ч). Спека в `kosha/docs/`, хелпер в `sanskrit-util`, пилот на трёх репозиториях, бэкфилл 149 строк, негативный тест. Приёмка: тест падает на пустой фикстуре; 149 строк с машинным провенансом; 16 dormant с владельцем и датой.
2. **Overlay-гард по путям** (agent lane, ~2 ч). Приёмка: новый билдер в защищённый путь падает без флага; список путей в реестре.
3. **Виза по 16 dormant** (MG, ~7 мин). Review-sheet, вердикт по строке.
4. **FINDINGS-строка** (agent lane, ~15 мин): в `Uprava/FINDINGS.md` по F1-маршруту (инфра/процесс, не в SanskritLexicography) — внешняя ссылка на разбор Xena как подтверждение нашей нормы.

## Остатки

- Порог «свыше 1000 вызовов» — проверить на первом же платном прогоне, не окажется ли он ниже реального объёма.
- `novelty` может выродиться в отписку; через месяц проверить, у скольких новых слоёв абзац содержательный, а не «новый формат того же».
- Мораторий истекает 18-11-2026 — снять или продлить решением MG.

_Гасунс_
