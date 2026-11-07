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


Concept candidates: **15**.  Provisional
Topic→Concept links: **179**.

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

## Codex triage status

All machine proposals have a provisional DOMAIN_AUTHORING disposition. No
per-proposal semantic acceptance was inferred. The complete package remains
`UNREVIEWED` and requires the explicit consolidated `DOMAIN_REVIEW` defined by
the human-decision policy before any semantic result can become accepted.
