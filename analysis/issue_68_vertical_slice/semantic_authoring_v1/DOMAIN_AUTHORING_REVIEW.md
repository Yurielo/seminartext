# Issue #68 — Semantic DOMAIN_AUTHORING review

The complete machine-assisted package is stored in `semantic_authoring_package.json`.
All new Topics, Concept candidates, and Topic→Concept links are provisional and
`UNREVIEWED`. Day 1 remains the previously accepted human-reviewed source.

## Package inventory

| Source | Topic proposals | Canonical words covered | Gaps | Overlaps |
| --- | ---: | ---: | ---: | ---: |
| `source_video_002` | 91 | 26823/26823 | 0 | 0 |
| `source_video_003` | 92 | 25601/25601 | 0 | 0 |
| `source_video_004` | 79 | 24935/24935 | 0 | 0 |


Concept candidates: **18**.  Provisional
Topic→Concept links: **255**.

## First review item

### 7. Претесты для нормотонизации мышц

- Source: `source_video_002`
- Time: `00:23:42.407` — `00:29:34.120`
- Words: `transcript_revision_video_002_r1:word:002202` — `transcript_revision_video_002_r1:word:002753`
- Summary: Сегмент посвящен проведению претестов – процедур очищения и перегрузки мышц – для восстановления их нормотонического состояния, особенно в начале работы с клиентом. Фрагмент проходит от «Когда мы с человеком начинаем работать, только…» к «будет вот это переключение. У нас, помните,».
- Beginning: Когда мы с человеком начинаем работать, только у нас
- Middle: как бы, да, условно, мышцу пополоскали, очищение сделали. Это первый у нас претест. Давайте мы хотя бы
- End: эта коррекция будет вот это переключение. У нас, помните,
- Machine recommendation: `ACCEPT`
- Available decisions: ACCEPT, RENAME, REALIGN, SPLIT, MERGE, EXCLUDE_NON_SEMANTIC, OTHER

Natural Russian responses are supported, for example: `Тема 7 — принять`,
`Название изменить на …`, or `Разделить после фразы …`.
