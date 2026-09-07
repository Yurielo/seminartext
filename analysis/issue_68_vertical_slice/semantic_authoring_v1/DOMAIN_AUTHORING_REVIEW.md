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
Topic→Concept links: **240**.

## Human-decision policy

The 262 machine proposals are evidence units, not
262 mandatory human gates. Codex first triages every unresolved
proposal. Straightforward cases may be prepared as provisional authoring without
a per-item human decision. A human decision is requested only for a genuine
semantic ambiguity, material evidence/provenance conflict, uncertain exclusion,
Concept identity choice, or semantic acceptance/rejection. Nothing becomes
accepted automatically; one explicit consolidated `DOMAIN_REVIEW` remains
required after provisional authoring.

Policy mode: `EXCEPTION_ONLY_WITH_CONSOLIDATED_DOMAIN_REVIEW`.

## Next Codex triage item

### 119. Психосоматика и Стресс

- Source: `source_video_003`
- Time: `01:34:01.977` — `01:43:40.287`
- Words: `transcript_revision_video_003_r1:word:008014` — `transcript_revision_video_003_r1:word:008838`
- Summary: Семинар рассматривает связь между эмоциональными переживаниями и физическими заболеваниями, используя термины психосоматика и теорию стресса, сформулированную Гансом Елье. Фрагмент проходит от «И следующая у нас тема с вами…» к «То есть мышцы начинают, становятся, условно говоря,».
- Beginning: И следующая у нас тема с вами это теория
- Middle: все, то есть, ну, например, специфический эффект, там, эмоции, да, появились, специфический эффект, там, если порезались, как
- End: АТФ происходит. То есть мышцы начинают, становятся, условно говоря,
- Machine recommendation: `ACCEPT`
- Available decisions: ACCEPT, RENAME, REALIGN, SPLIT, MERGE, EXCLUDE_NON_SEMANTIC, OTHER

This item is not automatically a human gate. If Codex finds a genuine ambiguity,
the evidence and bounded alternatives are presented to the Product Owner.
