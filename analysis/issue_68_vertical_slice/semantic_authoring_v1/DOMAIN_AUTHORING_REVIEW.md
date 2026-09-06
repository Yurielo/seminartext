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

### 30. Тема требует ручной проверки

- Source: `source_video_002`
- Time: `01:44:23.173` — `01:48:26.090`
- Words: `transcript_revision_video_002_r1:word:009833` — `transcript_revision_video_002_r1:word:010277`
- Summary: Машинное резюме отсутствует; содержание требует ручной проверки. Фрагмент проходит от «Ваша задача, повторюсь, да, вам выбрать один…» к «Елена, вы не этот, у вас прямо,».
- Beginning: Ваша задача, повторюсь, да, вам выбрать один из методов
- Middle: Да, нет. Всего два пальца участвуют. То есть мы другие, они просто... Никуда не денешь. Да, нет.
- End: да, отлично. Елена, вы не этот, у вас прямо,
- Machine recommendation: `RENAME`
- Available decisions: ACCEPT, RENAME, REALIGN, SPLIT, MERGE, EXCLUDE_NON_SEMANTIC, OTHER

Natural Russian responses are supported, for example: `Тема 30 — принять`,
`Название изменить на …`, or `Разделить после фразы …`.
