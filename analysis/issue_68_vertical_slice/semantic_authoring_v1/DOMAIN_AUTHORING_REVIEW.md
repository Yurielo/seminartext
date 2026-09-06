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

### 31. Тема требует ручной проверки

- Source: `source_video_002`
- Time: `01:48:10.640` — `01:49:28.470`
- Words: `transcript_revision_video_002_r1:word:010250` — `transcript_revision_video_002_r1:word:010402`
- Summary: Машинное резюме отсутствует; содержание требует ручной проверки. Фрагмент проходит от «У кого получился этот способ, метод одной…» к «получится? И тогда как-то, ну, все, картина».
- Beginning: У кого получился этот способ, метод одной руки? У
- Middle: случаях лучше, чтобы правое полушарие больше работало, да? То есть, очень много контроля. И вот этот контроль
- End: у меня получится? И тогда как-то, ну, все, картина
- Machine recommendation: `RENAME`
- Available decisions: ACCEPT, RENAME, REALIGN, SPLIT, MERGE, EXCLUDE_NON_SEMANTIC, OTHER

Natural Russian responses are supported, for example: `Тема 31 — принять`,
`Название изменить на …`, or `Разделить после фразы …`.
