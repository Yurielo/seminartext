# Canonical Knowledge Contract v1

Issue #64 defines an additive, versioned semantic layer over the accepted
Canonical Evidence v1 and Golden Knowledge Slice. The dependency direction is:

`Canonical Evidence → Topic → Concept → Relation → Canonical Knowledge → derived UI/Obsidian`.

Obsidian remains a derived view and is never a canonical source. This change
does not alter the Canonical Evidence schema, the Golden Slice semantics, the
frozen Local Peak candidate, or any production/export workflow.

## Contract

`schemas/canonical_knowledge_v1.schema.json` defines stable IDs and records for
Project, Seminar, contextual Topic, reusable Concept, controlled Relation, and
ReviewDecision. `schemas/validate_canonical_knowledge_v1.py` uses the committed
JSON Schema as the authoritative structural layer through `jsonschema` and adds
deterministic field, cross-record and lifecycle checks: unique IDs,
non-dangling references, version ordering, rename/merge/split mechanics,
controlled relation types, provenance, external evidence links, and rejection
of absolute machine paths. Source-status/lifecycle policy is data-driven by
`schemas/canonical_knowledge_lifecycle_v1.json`; AUDIT-R2 details are recorded
in `analysis/AUDIT_R2_CANONICAL_KNOWLEDGE_VALIDATION.md`.

Topics are source-scoped structural intervals and are not reusable identities.
Concepts are reusable identities whose identity is their stable ID, not their
label. The four required lifecycle states are available: PROVISIONAL, ACCEPTED,
REJECTED, and SUPERSEDED. Automatic extraction and the Golden Slice fixture
remain provisional; no human semantic decision is recorded here.

ReviewDecision supports only the mechanics of ACCEPT, RENAME, SPLIT, MERGE,
REJECT, and DEFER. Rename requires identical target/result IDs. Merge and split
require lineage IDs and preserve historical records through `supersedes` and
`redirects`; the contract does not perform a semantic merge or split. Versioned
corrections are represented by immutable version numbers and decisions, with
old IDs remaining discoverable. `contradicts` and `supports` relations allow
competing claims without collapsing them.

## Golden Slice and #63 interoperability

`tests/fixtures/canonical_knowledge_v1/golden_slice_knowledge.json` references,
but does not duplicate, the existing Golden Slice evidence and Canonical
Evidence source/transcript identities (3 Topics, 7 Concepts, 10 Evidence).
Descriptions, labels, and source status are copied without semantic rewriting;
all Concepts and Topics are PROVISIONAL and `review_decisions` is empty.
The validator checks the external artifact IDs and every evidence/source scope.

The shape is sufficient for the Issue #63 Obsidian boundary: generated/user
ownership can be represented by provenance and ReviewDecision records, and
stable source references are resolvable. No Obsidian export or bidirectional
sync is implemented by Issue #64.

## Requirement → evidence matrix

| Requirement | Implementation/evidence |
| --- | --- |
| Project/Seminar distinction | Separate IDs and `seminar.project_id`; validator enforces the reference. |
| Contextual Topic | `source_scope`, temporal/order scope, evidence and concept refs. |
| Reusable Concept | Stable ID, aliases, scope, provenance, evidence/topic refs, lineage. |
| Lifecycle | Four required states; invalid values fail closed. |
| Review mechanics | Six actions, actor/timestamp/versions/provenance and lineage checks. |
| Relations and conflicts | Closed five-type registry; `supports`/`contradicts` are non-collapsing. |
| Corrections | Version fields plus immutable decision and redirect/supersession links. |
| Canonical Evidence compatibility | External artifact pointer and fixture validation; v1 schema untouched. |
| Golden Slice compatibility | Exact 3/7/10 identity/evidence links; no decisions or semantic changes. |
| Determinism/safety | Schema-authoritative validator in the pinned `dev_test` profile, stable IDs, no absolute paths, fail-closed refs. |

Human gates remain explicit: semantic identity, final naming, relation meaning,
conflict resolution, and real merge/split decisions require DOMAIN_REVIEW;
missing definitions or new claims require DOMAIN_AUTHORING. Those gates are
not exercised by this implementation.
