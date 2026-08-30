# Issue #104 — Project Knowledge Bridge

Status: `IMPLEMENTED_PENDING_PRODUCT_OWNER_ACCEPTANCE`

This bounded implementation connects retained source-scoped Canonical Evidence
to explicitly supplied semantic records, validated Canonical Knowledge v1, and
a deterministic one-way Obsidian derived view. It does not authorize or perform
the real full-seminar Issue #68 validation.

## Supported path

```text
retained source Canonical Evidence
  -> deterministic project Canonical Evidence + coverage
  -> explicit project knowledge input v1
  -> Canonical Knowledge v1 layered validation
  -> managed Obsidian derived view
```

The bridge accepts only `gold`, `verified_manual`, or explicitly marked
`semi_automatic` Topic origins. All Topic titles/summaries, Concept identities
and descriptions, Relations, claims, lifecycle states, and review decisions
come from the input document. The compiler only validates, orders records, and
derives canonical hashes, evidence excerpts, and supported time locators.

## Outputs and safety

- `evidence/sources/<source>/revisions/<revision>/canonical_bundle.json` is the
  immutable retained revision artifact.
- `evidence/sources/<source>/canonical_bundle.json` is the selected current
  source view, bound to its source manifest and retained revision hash.
- `evidence/canonical_bundle.json`, `word_timeline.json`, and `manifest.json`
  are deterministic project aggregates with registered-source coverage.
- `knowledge/canonical_evidence.json`, `source_evidence.json`,
  `canonical_knowledge.json`, and `coverage.json` are managed compiled outputs.
- The destination vault has a `.seminartext-export.json` managed-file inventory.
- `MANAGED_GENERATED` files are hash-checked. Changed managed files, stale
  managed paths, and `USER_OWNED` collisions fail closed; no file is deleted.
- Resolver states are `AVAILABLE`, `MOVED`, `PROJECT_MOVED`, `MISSING`, and
  `RESOLVER_UNAVAILABLE`. Local paths are never canonical note identity and are
  not emitted into Markdown.

## Bounded fixture evidence

The committed fixture has two local video sources, two verified transcript
revisions, four Words, two BenchmarkSegments, two explicitly supplied Topics,
one provisional Concept, two Evidence records, and `time_interval` locators.
The full input proves a cross-source Concept path. The partial input marks the
second source `SEMANTIC_INPUT_UNAVAILABLE`, supplies no semantic entities for
it, and reports `full_seminar_coverage=false`.

Sample trace:

- beginning: `topic_source_one` -> `evidence_source_one` ->
  `source_video_001` / `transcript_revision_video_001_r1` /
  Words `000000..000001` / `0.1..0.9` seconds;
- middle/source boundary: `concept_shared_sources` links the explicitly supplied
  first and second source Topics without inferring a new relation;
- end: `topic_source_two` -> `evidence_source_two` -> `source_video_002` /
  `transcript_revision_video_002_r1` / Words `000000..000001` /
  `1.1..1.9` seconds.

## Requirement-to-evidence matrix

| Requirement | Evidence |
| --- | --- |
| Preserve the first source when adding a second | Source/revision artifacts and `test_second_source_is_retained_and_project_bundle_is_deterministic` |
| Deterministic multi-source composition | `compose_project_bundle`, source manifest/hash binding, duplicate/project conflict tests |
| Versioned explicit semantic input | `schemas/project_knowledge_input_v1.schema.json` and allowed-origin negative tests |
| Canonical Knowledge lifecycle/reference validation | `validate_knowledge` invocation and lifecycle/orphan/cross-source tests |
| Supported project CLI | `project-obsidian-export ... --knowledge-input ... --destination ... [--dry-run]` |
| Deterministic artifacts and notes | two-build byte comparison and per-file SHA-256 manifests |
| Safe ownership boundary | user-note preservation, collision, changed/stale managed-file tests |
| External source resolution | all five resolver-state tests; no local paths in notes |
| Truthful lifecycle/provenance | provisional Concept banner and exact Source/Revision/Word/time metadata |
| Truthful partial coverage | committed partial input and `full_seminar_coverage=false` test |
| Existing contracts remain valid | Evidence, Canonical Knowledge, Golden Slice, Obsidian, governance, and full-suite regressions |

## Human gates and exclusions

- Final Product Owner acceptance remains pending.
- Real missing Topic/Concept/Relation content requires `DOMAIN_AUTHORING`.
- Acceptance, rename, split, merge, reject, and defer require `DOMAIN_REVIEW`.
- Merge and any installed-runtime reconciliation retain their normal separate
  Product Owner gates.
- No Dataset C/D/E access, Gold mutation, Topic prediction/tuning, TreeSeg work,
  G6 implementation, real project mutation, deployment, or Issue #68 run is
  part of this implementation.

`SAFE_TO_START_ISSUE_68: NO` until Product Owner acceptance, merge, governed
runtime reconciliation where required, and separate Issue #68 authorization.
