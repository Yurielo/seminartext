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

### 5. Тема требует ручной проверки

- Source: `source_video_002`
- Time: `00:18:19.464` — `00:19:13.789`
- Words: `transcript_revision_video_002_r1:word:001713` — `transcript_revision_video_002_r1:word:001789`
- Summary: Машинное резюме отсутствует; содержание требует ручной проверки. Фрагмент проходит от «Вот это видео у вас остается, как…» к «говорил, да, на что мы мышца и».
- Beginning: Вот это видео у вас остается, как и видео
- Middle: важно относительно кинезиологии. У нас может быть только два варианта ответа мышцы. Мышца либо сильная, либо слабая.
- End: как я говорил, да, на что мы мышца и
- Machine recommendation: `RENAME`
- Available decisions: ACCEPT, RENAME, REALIGN, SPLIT, MERGE, EXCLUDE_NON_SEMANTIC, OTHER

Natural Russian responses are supported, for example: `Тема 5 — принять`,
`Название изменить на …`, or `Разделить после фразы …`.
