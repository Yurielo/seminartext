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
Topic→Concept links: **253**.

## First review item

### 3. Оптимизация состояния клиента при тестировании мышц

- Source: `source_video_002`
- Time: `00:02:21.618` — `00:12:08.120`
- Words: `transcript_revision_video_002_r1:word:000170` — `transcript_revision_video_002_r1:word:001066`
- Summary: Сессия направлена на быстрое восстановление клиента, устранение усталости и подготовку к проведению тестирования мышц, особенно передней порции дельтовидной, для получения точной информации о его состоянии. Фрагмент проходит от «И изучили с вами такой комплекс мероприятий,…» к «передача в этих местах соединения, в нервах,».
- Beginning: И изучили с вами такой комплекс мероприятий, который называется
- Middle: это тоже важная информация. Но вообще все, о чем я говорю, каждая мысль, важна. Но здесь принципиально
- End: эта электрохимическая передача в этих местах соединения, в нервах,
- Machine recommendation: `ACCEPT`
- Available decisions: ACCEPT, RENAME, REALIGN, SPLIT, MERGE, EXCLUDE_NON_SEMANTIC, OTHER

Natural Russian responses are supported, for example: `Тема 3 — принять`,
`Название изменить на …`, or `Разделить после фразы …`.
