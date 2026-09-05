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

### 2. Мануальное мышечное тестирование

- Source: `source_video_002`
- Time: `00:01:13.600` — `00:02:39.568`
- Words: `transcript_revision_video_002_r1:word:000067` — `transcript_revision_video_002_r1:word:000193`
- Summary: Кинезиологическое тестирование позволяет получать информацию о состоянии мышц в виде двоичного ответа: либо мышца сильная, либо слабая. Фрагмент проходит от «Мы про это говорили. Собственно, кинезиологический тест.…» к «подробно про это поговорим. Это комплекс мероприятий,».
- Beginning: Мы про это говорили. Собственно, кинезиологический тест. Мануальное мышечное
- Middle: Мы говорим, что это стресс, реакция на стресс. Стресс бывает разный. Бывает эмоциональный, бывает химический. Ну и
- End: еще раз подробно про это поговорим. Это комплекс мероприятий,
- Machine recommendation: `ACCEPT`
- Available decisions: ACCEPT, RENAME, REALIGN, SPLIT, MERGE, EXCLUDE_NON_SEMANTIC, OTHER

Natural Russian responses are supported, for example: `Тема 2 — принять`,
`Название изменить на …`, or `Разделить после фразы …`.
