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
Topic→Concept links: **254**.

## First review item

### 1. Введение в Стресс-код

- Source: `source_video_002`
- Time: `00:00:04.950` — `00:01:13.200`
- Words: `transcript_revision_video_002_r1:word:000000` — `transcript_revision_video_002_r1:word:000066`
- Summary: Начало второго дня обучения по программе Стресс-код, с повторным рассмотрением кинезиологии и ее преимуществ. Фрагмент проходит от «Здравствуйте! Начинаем второй день нашего обучения по…» к «кинезиологом. И кинезиологию отличает от других практик.».
- Beginning: Здравствуйте! Начинаем второй день нашего обучения по программе Стресс-код.
- Middle: ее преимуществах перед другими технологиями. Мы начали вчера переходить к практике. Нам по итогу, у нас не
- End: уметь делать кинезиологом. И кинезиологию отличает от других практик.
- Machine recommendation: `ACCEPT`
- Available decisions: ACCEPT, RENAME, REALIGN, SPLIT, MERGE, EXCLUDE_NON_SEMANTIC, OTHER

Natural Russian responses are supported, for example: `Тема 1 — принять`,
`Название изменить на …`, or `Разделить после фразы …`.
