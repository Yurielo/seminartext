# Issue #68 — DOMAIN_AUTHORING packet

## Verified factual state

The controlled real seminar is `Стресс код`. The existing project evidence
passes `project-evidence-check`: JSON Schema and cross-record validation are
both `PASS`. The canonical project bundle is bound to SHA-256
`40879d5a87cd1a8ea7869d51e81aa7f93cfc48bc34cb5858e5664363ee687273`.

| Source | Canonical Evidence | Words | Aligned / unaligned | Applied reviewed Topic units |
| --- | --- | ---: | ---: | ---: |
| `source_video_001` | `COMPOSED` | 24,140 | 23,909 / 231 | 37 |
| `source_video_002` | `COMPOSED` | 26,823 | 26,555 / 268 | 0 |
| `source_video_003` | `COMPOSED` | 25,601 | 25,361 / 240 | 0 |
| `source_video_004` | `COMPOSED` | 24,935 | 24,682 / 253 | 0 |
| `source_doc_001` | `EVIDENCE_UNAVAILABLE` | 0 | 0 / 0 | 0 |
| `source_doc_002` | `EVIDENCE_UNAVAILABLE` | 0 | 0 / 0 | 0 |
| `source_doc_003` | `EVIDENCE_UNAVAILABLE` | 0 | 0 / 0 | 0 |

The 37 Day-1 units are the 36 `SEMANTIC_KNOWLEDGE` units plus one
`SEMINAR_STRUCTURE` unit produced by the applied Issue #113 Product Owner
review. They originate from 31 reviewed source Topic snapshots. This accounting
does not claim that 37 new independent human decisions were made.

All four TranscriptRevisions remain correctly typed as `machine_generated`,
`machine_unverified`, `candidate`. The current supported locator class is
`time_interval`. The last Words of Days 2–4 are explicitly unaligned; this is
preserved rather than hidden.

## Why automatic continuation stops here

No eligible Topic semantics exist for Days 2–4. The applied #113 artifact also
contains no authoritative Canonical Concepts or Topic-to-Concept links. Creating
those records would be semantic authoring, not an engineering transformation.

Therefore Codex cannot truthfully construct or accept the required path:

```text
Seminar -> Source/Topic -> Concept -> Evidence -> exact locator
```

It also cannot run the Obsidian export merely to create the appearance of a
complete Issue #68 slice. The available evidence proves a technically healthy
four-video foundation and a reviewed Day-1 Topic layer; it does not prove full
seminar knowledge coverage.

## Exact Product Owner input required

`DOMAIN_AUTHORING` must supply both:

1. eligible authoritative Topic inputs for `source_video_002`,
   `source_video_003`, and `source_video_004`, preserving exact source/revision/
   Word provenance; and
2. the minimal Canonical Concept identities/content and explicit Topic-to-
   Concept links required for the vertical-slice path.

After authoring, semantic acceptance remains `DOMAIN_REVIEW`. Codex can then
mechanically validate, compile, export, trace, and repeat-build the result.

## Options at the human gate

1. **AUTHOR THE MISSING SEMANTICS (recommended):** provide the inputs above and
   retain the accepted Issue #68 Definition of Done.
2. **CHANGE THE ROADMAP/DEFINITION OF DONE:** explicitly narrow Issue #68 to an
   evidence-plus-Topic partial slice. This is a Product Owner roadmap decision,
   not an engineering fallback.

Until one of these occurs:

```text
MULTI_SOURCE_VERTICAL_SLICE: PARTIAL
CROSS_SEMINAR_READY_NEXT: NO
HUMAN_GATE: DOMAIN_AUTHORING
```
