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

### 4. Ионное растворение

- Source: `source_video_002`
- Time: `00:13:40.091` — `00:17:44.090`
- Words: `transcript_revision_video_002_r1:word:001219` — `transcript_revision_video_002_r1:word:001645`
- Summary: Процесс может возникать при растворении ионов, таких как калий, кальций и натрий, в воде. Фрагмент проходит от «И вот на видео, которое вы вчера…» к «возможность? Хорошо. Тогда обязательно вот это потренируйте.».
- Beginning: И вот на видео, которое вы вчера смотрели, я
- Middle: ну, чуть побольше, да, и мы должны уловить, вот, есть такое понимание, да, точка запирания, когда, если
- End: неделе будет возможность? Хорошо. Тогда обязательно вот это потренируйте.
- Machine recommendation: `ACCEPT`
- Available decisions: ACCEPT, RENAME, REALIGN, SPLIT, MERGE, EXCLUDE_NON_SEMANTIC, OTHER

Natural Russian responses are supported, for example: `Тема 4 — принять`,
`Название изменить на …`, or `Разделить после фразы …`.
