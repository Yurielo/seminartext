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
Topic→Concept links: **259**.

## First review item

### 39. Личное присутствие

- Source: `source_video_002`
- Time: `02:16:27.351` — `02:18:45.970`
- Words: `transcript_revision_video_002_r1:word:013058` — `transcript_revision_video_002_r1:word:013232`
- Summary: Участник указывает на конкретного человека, находящегося перед ним. Фрагмент проходит от «Давайте попробуйте, потренируйтесь, возьмите какого-то своего знакомого,…» к «исчезла. Давайте попробуем поработать с фантомом, то».
- Beginning: Давайте попробуйте, потренируйтесь, возьмите какого-то своего знакомого, знакомого человека,
- Middle: его можете тестировать. Да, нет, да. Сильный ответ, слабый ответ. Вот потестируйте, так, воображение. Кто угодно это
- End: она сама исчезла. Давайте попробуем поработать с фантомом, то
- Machine recommendation: `ACCEPT`
- Available decisions: ACCEPT, RENAME, REALIGN, SPLIT, MERGE, EXCLUDE_NON_SEMANTIC, OTHER

Natural Russian responses are supported, for example: `Тема 39 — принять`,
`Название изменить на …`, or `Разделить после фразы …`.
