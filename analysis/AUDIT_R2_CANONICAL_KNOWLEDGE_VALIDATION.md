# AUDIT-R2 — Canonical Knowledge structural validation and lifecycle mapping

Issue #88 hardens validation without changing Canonical Knowledge semantics,
the Canonical Evidence contract, or the accepted Golden Slice. The existing
3 Topics, 7 Concepts, and 10 Evidence records remain unchanged.

## Validator architecture

The validator has four explicit fail-closed layers. Every error begins with its
layer identifier.

| Layer | Authority | Enforced rules |
| --- | --- | --- |
| `L1_SCHEMA` | `canonical_knowledge_v1.schema.json`, executed by `jsonschema` Draft 2020-12 | Required and unknown properties, primitive types, constants/versions, enums, stable-ID patterns, nested provenance/source/temporal/decision/relation shapes, and portable artifact-pointer paths. |
| `L2_FIELD` | Deterministic Python invariants | Globally unique stable IDs, exact relation registry, ordered source/temporal bounds, monotonic versions, rename/merge/split mechanics, and machine-specific strings outside pointer fields. |
| `L3_REFERENCE` | Deterministic Python reference checks | Project/Seminar/Topic/Concept/Relation/Decision links, external Canonical Evidence and Golden Slice identities, Evidence/Source/Transcript references, and source Topic/Concept identity preservation. |
| `L4_LIFECYCLE` | `canonical_knowledge_lifecycle_v1.json` | Source-status vocabulary, source-status/lifecycle separation, actor/action authority, explicit decisions for accepted/rejected/superseded records, and AUTO-safe defer mechanics. |

No structural field list is duplicated in Python. If `jsonschema` is missing,
Layer 1 returns a dependency error and the CLI exits invalid; it never falls
back to the former weaker handwritten shape check. The dependency is already
pinned as `jsonschema==4.25.1` in the supported `dev_test` profile.

## Source status and Knowledge lifecycle

The accepted Golden Slice exposes exactly two source Topic statuses:
`gold_complete` and `product_review_required`. The mapping contract defines only
those observed values.

- `gold_complete` certifies the accepted source Topic annotation
  (boundary/title/summary). It does not certify Concept identity, Concept text,
  Relation meaning, or Canonical Knowledge acceptance.
- `product_review_required` preserves a bounded manual source range and its
  provenance. It explicitly does not certify product or Knowledge acceptance.
- Either source status may be copied mechanically into a `PROVISIONAL`
  Canonical Knowledge Topic. This is `AUTO` because it changes no semantics.
- `ACCEPTED` requires an explicit `ACCEPT` ReviewDecision from a
  `human_domain_reviewer` or `product_owner` (`DOMAIN_REVIEW`).
- `REJECTED` requires an explicit `REJECT` decision; `SUPERSEDED` requires an
  explicit `MERGE` or `SPLIT` lineage decision. These are also `DOMAIN_REVIEW`.
- `system_validator` may only record `DEFER` with no result IDs while all targets
  remain `PROVISIONAL`. It cannot accept, reject, rename, merge, or split.

No existing record is promoted or demoted. In particular,
`gold_complete != ACCEPTED`; the Golden Slice topics and concepts remain
`PROVISIONAL` and its `review_decisions` array remains empty.

`DOMAIN_AUTHORING` is not required for this validation contract. It remains the
gate only when new authoritative semantic content must be supplied, which is
outside AUDIT-R2.

## Portability

Active Canonical Knowledge fixtures and the lifecycle contract contain no
absolute `/Users/...`, `/home/...`, `file://`, `vscode://`, Windows-drive, or
tilde paths. Artifact pointers remain repository-relative. Historical artifacts
are not rewritten.

## Requirement → implementation → evidence → test

| Requirement | Implementation | Evidence | Test |
| --- | --- | --- | --- |
| Full schema enforcement | Draft 2020-12 validator loads the committed schema | `L1_SCHEMA` errors | structural negative matrix and positive Golden Slice CLI |
| No drifting structural copy | Python contains no required/property/enum tables for record shape | schema is sole Layer 1 authority | authoritative-validator assertion |
| Stable IDs and field mechanics | Layer 2 | deterministic error paths | duplicate/order/version/lineage tests |
| Reference integrity | Layer 3 | external and cross-record checks | dangling and Golden Slice identity tests |
| Lifecycle mapping | machine-readable adjunct + Layer 4 | two observed source statuses and four existing lifecycles | valid/invalid, acceptance, AUTO defer, superseded lineage tests |
| Semantic preservation | fixture and source artifacts unchanged | frozen SHA-256 and 3/7/10 counts | Golden Slice compatibility test |
| Portability | Schema pointer pattern plus Layer 2 full-string scan | zero active absolute paths | pointer and non-pointer negative tests |
