# Exact reviewed-fragment Canonical Knowledge admission v1

Authority: Product Owner's
`AUTHORIZE_BOUNDED_SEMINARTEXT_CANONICAL_KNOWLEDGE_ADMISSION_EXTENSION`,
2026-10-09, supporting Integra Issue #227 (Knowledge K2).

SeminarText remains the Canonical Knowledge owner. Integra prepares proposals
and collects explicit human semantic decisions, invokes this owner admission,
and reads the returned canonical revision. K1 fragment review does not supply
K2 semantic authority. No Product Rule is added or changed.

Applicable ACTIVE Product Rules: PR-001, PR-002, PR-003, PR-004, PR-005,
PR-006, PR-007, PR-008, PR-010, PR-011, PR-012, PR-013, PR-014.
Product Rule conflicts: NONE.

## Additive boundary

`seminartext_modules/reviewed_knowledge_admission.py` and
`schemas/reviewed_knowledge_admission_v1.schema.json` define a versioned
admission separate from the existing complete-BenchmarkSegment compiler.
The Canonical Evidence/Knowledge v1 schemas, their validators and lifecycle,
existing compiler, and accepted historical artifacts remain unchanged.

The input includes exact current Evidence bytes; the applied V2 result bytes;
a package binding source/project/revision/hash, notebook/review identity,
producer/runtime/contract identity, enumerated proposals and optional parent;
and a separate enumerated semantic decision ledger. Runtime identity and current
source/notebook bindings must be independently checked by the invoking adapter.
Caller labels and paths cannot establish identity.

The owner validates exact Word or cue ranges and derives quotes/locators from
the unchanged Evidence. It never adds semantic Topics to the Evidence bundle,
manufactures BenchmarkSegments, extends fragments or runs upstream processing.
Cue-only evidence retains cue precision. K1 v1 itself currently admits only
word-timed notebooks; the admission must not invent Word precision for other
future compatible callers.

Only existing Topic, Concept and controlled Relation records are admitted.
Terms remain projections. CREATE or UPDATE proposals must remain PROVISIONAL;
every proposal has a separate explicit ACCEPT, EDIT, REJECT or DEFER choice and
the user confirms the exact package/list/hash. Editable fields are bounded to
Topic title/summary, Concept label/description/aliases and supported Relation
type. IDs do not depend on labels. Identity merge/redirect is unsupported.
REJECT/DEFER persist in the receipt and do not introduce new canonical entities.
An existing record remains unchanged when its update is rejected/deferred.

## Owner interaction by exception

The admission also accepts an explicitly marked
`MACHINE_DERIVED_FRAGMENTS_V1` K1 binding.  It is a narrow non-authoritative
input path for exact source fragments that have been mechanically prepared but
not human reviewed.  It preserves the same Canonical Evidence binding, exact
fragment ranges, and machine provenance, while expressly recording
`NONAUTHORITATIVE_MACHINE_DERIVED` and `semantic_authority: NONE`.

For this input, `system_validator` may only submit the enumerated
`SYSTEM_NONAUTHORITATIVE_DEFER` ledger: every proposal is a new provisional
record, every action is `DEFER`, no fields are edited, and no canonical entity
or accepted semantic decision is produced.  This is a useful, persistent
machine-derived result, not human review, Product Owner acceptance, or Canonical
Knowledge acceptance.

Explicit human semantic decisions remain required for ACCEPT, EDIT, REJECT,
identity change, replacement, or any other authoritative outcome.  A human
decision may be made later against exact machine-derived evidence; its
decision provenance remains distinct from the source's machine-derived K1
provenance.  Thus absence of a human decision never becomes acceptance,
rejection, human review, or author authority.

## Immutable revision and validation

The output is `seminartext.canonical_knowledge_revision`, containing the
unchanged Canonical Knowledge v1 payload, a source Evidence artifact preserving
reviewed fragment identities, all proposal/decision provenance and hashes, and
the exact parent receipt. The canonical artifact ID stays stable across
revisions; revision identity is content-addressed and entity versions increase
on accepted updates. Previous receipts are never overwritten.

`validate_revision` deterministically recompiles the receipt against the
supplied current Evidence bytes and compares the complete result. An adapter
must additionally compare the receipt's source/notebook/producer bindings to
current persisted inputs before invoking it. Schema validation alone is not
source attestation. `persist_revision` uses an atomic no-overwrite operation;
the standalone CLI accepts `--evidence`, `--reviewed`, `--package`, `--decisions`,
optional `--parent`, and `--output`.

## Baseline and standalone protection

Audited source main: `c6f681891b2004d1ccb46dc1457f6fae63f78649`.
Baseline full suite: 318 passed, 0 skipped. G1/G3/G4/G5/G7/G8 PASS;
G6 NOT_IMPLEMENTED. Local installed runtime already has a CLI-only G2 drift
before this extension. This task does not deploy or repair that unrelated
runtime. The extension is a library/CLI in the source checkout, consumed as an
exact accepted component by Integra after merge.

Existing complete-segment admission, canonical fixtures and standalone product
tests must pass alongside exact-boundary, semantic firewall, parent/revision,
corruption and interrupted-write tests. No Dataset, Gold, algorithm or model
change is part of this extension.
