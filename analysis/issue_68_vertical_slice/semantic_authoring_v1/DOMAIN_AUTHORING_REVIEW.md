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
Topic→Concept links: **257**.

## First review item

### 23. Энергия и Эмоции

- Source: `source_video_002`
- Time: `01:27:35.634` — `01:28:59.040`
- Words: `transcript_revision_video_002_r1:word:008141` — `transcript_revision_video_002_r1:word:008319`
- Summary: Обсуждается взаимосвязь между эмоциями, тепловой энергией и звуком, а также возникли технические сложности во время записи. Фрагмент проходит от «У кого-то там что-то с микрофоном не…» к «настраиваем вот эти потоки, когда мы внятную,».
- Beginning: У кого-то там что-то с микрофоном не воды. Ага,
- Middle: перерабатываем, и какая-то энергия из нас и выходит, исходит, да. То есть, мы вот все время в
- End: мы вот настраиваем вот эти потоки, когда мы внятную,
- Machine recommendation: `EXCLUDE_NON_SEMANTIC`
- Available decisions: ACCEPT, RENAME, REALIGN, SPLIT, MERGE, EXCLUDE_NON_SEMANTIC, OTHER

Natural Russian responses are supported, for example: `Тема 23 — принять`,
`Название изменить на …`, or `Разделить после фразы …`.
