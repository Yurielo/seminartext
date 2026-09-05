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
Topic→Concept links: **256**.

## First review item

### 13. Детское тестирование

- Source: `source_video_002`
- Time: `00:47:36.931` — `00:49:38.260`
- Words: `transcript_revision_video_002_r1:word:004431` — `transcript_revision_video_002_r1:word:004643`
- Summary: Разговор о том, как ребенок должен реагировать на указания взрослого во время тестирования. Фрагмент проходит от «Юрий, ну у меня вопрос такой, не…» к «вот вчера с Ларисой, да, у нас».
- Beginning: Юрий, ну у меня вопрос такой, не совсем. А
- Middle: на ребенке делать. А это про тестирование. Вот, обратите внимание, о чем я говорил, да? Мы тестировать,
- End: подсознавать. Как вот вчера с Ларисой, да, у нас
- Machine recommendation: `ACCEPT`
- Available decisions: ACCEPT, RENAME, REALIGN, SPLIT, MERGE, EXCLUDE_NON_SEMANTIC, OTHER

Natural Russian responses are supported, for example: `Тема 13 — принять`,
`Название изменить на …`, or `Разделить после фразы …`.
