# SeminarText Product Rules Registry v1

<!-- SEMINARTEXT_PRODUCT_RULES_REGISTRY_V1 -->

This file is the one canonical Product Rules Registry for SeminarText. It is
permanent, appendable, version-controlled, auditable repository truth. Product
Rules do not depend on conversational memory or undocumented developer
knowledge.

## Authority and control loop

The authority chain is:

`Product Owner decision -> optional task formalization -> explicitly authorized Codex persistence -> GitHub history -> mandatory agent read -> Issue/PR references -> CI and Integrity structural validation`

- The Product Owner alone adopts, changes, supersedes, or retires Product Rules.
- ChatGPT may help formalize an explicit Product Owner decision, but that
  intermediary is optional. A direct Product Owner instruction to Codex is
  authoritative for its exact scope.
- Codex persists a Product Rule only when an explicit authorized task instructs
  it to do so. Codex recommendations, implementation choices, inferred
  preferences, silence, and absence of objection are not authorization.
- GitHub stores the auditable decision history; it does not make semantic
  Product Rule decisions.
- CI and Integrity validate structure, references, lifecycle, and control-loop
  wiring. They do not claim semantic compliance proof.
- Any proposed work that conflicts with an `ACTIVE` Product Rule is a `HARD
  STOP` and requires a Product Owner decision.

## Lifecycle and stable IDs

Allowed statuses are `ACTIVE`, `SUPERSEDED`, and `RETIRED`. IDs use `PR-xxx`,
are immutable, are never reused, and remain ordered and contiguous. Historical
records are never silently deleted. A supersession must be reciprocal:
`Supersedes` on the successor and `Superseded By` on the historical rule.
`NONE` means that no rule reference applies.

## Adding or changing a Product Rule

1. The Product Owner makes an explicit durable decision.
2. The acting task-formulation agent checks this Registry, determines that the
   decision belongs here, identifies the next safe ID, and prepares one bounded
   Codex task. Direct Product Owner authorization does not require a ChatGPT
   relay.
3. Codex rereads the current Registry and fails closed on an ID collision or an
   `ACTIVE` rule conflict.
4. Codex adds or modifies only the explicitly authorized rule. Existing IDs are
   not renumbered, reused, or destructively rewritten.
5. Structural validation, focused tests, the full suite, Integrity, and exact
   diff/scope checks run.
6. Codex commits, pushes, and opens a PR. A Product Owner or domain review is
   required only when the change reaches a genuine human gate.
7. A Product Rule PR may merge only under authority already `ACTIVE` on main or
   an explicit Product Owner authorization applicable to that PR. An unmerged
   rule never self-authorizes its own merge. Runtime reconciliation follows the
   fail-closed standing policy in PR-014 when it is mechanically safe; otherwise
   it remains a human gate.

Concurrent proposals that select the same next ID must stop and rebase against
the current Registry; Codex must not resolve the semantic choice autonomously.

## Initial Product Rules

The following rules are the bounded Product Owner-approved inventory. Concept
alias outcomes described below are future semantic identity review requirements
and do not redefine the existing Topic ReviewDecision values `ACCEPT`, `RENAME`,
`SPLIT`, `MERGE`, `REJECT`, and `DEFER`.

<!-- PRODUCT_RULE_START -->
## PR-001 — Human Review Is Intrinsic

### ID
PR-001

### Title
Human Review Is Intrinsic

### Status
ACTIVE

### Normative Rule
Human semantic review is an intrinsic stage of SeminarText, not an external
workaround. The canonical semantic flow includes `Evidence -> Topic Draft ->
REVIEW_REQUIRED -> Human Review -> ReviewDecision -> accepted/rejected/revised
semantic state -> Canonical Knowledge`.

### Rationale
Semantic authority requires an explicit, supported human review stage inside
the product workflow.

### Scope
SeminarText semantic workflows and their product-facing lifecycle.

### Authority
Product Owner

### Date Adopted
2026-08-30

### Supersedes
NONE

### Superseded By
NONE

### Related Contracts / Issues
Issue #106; `analysis/HUMAN_REVIEW_WORKFLOW_MVP_ISSUE_106.md`
<!-- PRODUCT_RULE_END -->

<!-- PRODUCT_RULE_START -->
## PR-002 — No Automatic Semantic Acceptance

### ID
PR-002

### Title
No Automatic Semantic Acceptance

### Status
ACTIVE

### Normative Rule
Machine-generated or machine-assisted semantic content MUST NOT become
authoritative or `ACCEPTED` without an explicit human `ReviewDecision`. Machine
semantic output remains `PROVISIONAL` or `REVIEW_REQUIRED` until reviewed.

### Rationale
Automation may assist semantic work but cannot supply human semantic authority.

### Scope
All machine-generated or machine-assisted SeminarText semantic content.

### Authority
Product Owner

### Date Adopted
2026-08-30

### Supersedes
NONE

### Superseded By
NONE

### Related Contracts / Issues
Issue #106; `schemas/topic_review_workflow_v1.schema.json`
<!-- PRODUCT_RULE_END -->

<!-- PRODUCT_RULE_START -->
## PR-003 — DOMAIN_AUTHORING and DOMAIN_REVIEW Are Distinct

### ID
PR-003

### Title
DOMAIN_AUTHORING and DOMAIN_REVIEW Are Distinct

### Status
ACTIVE

### Normative Rule
`DOMAIN_AUTHORING` creates or proposes semantic content. `DOMAIN_REVIEW`
accepts, rejects, renames, splits, merges, defers, or otherwise makes semantic
review decisions. Mechanical preparation, validation, application, and
deterministic transformation remain `AUTO` where otherwise allowed.

### Rationale
Creating semantic proposals and authoritatively reviewing them are different
human responsibilities and must not be conflated.

### Scope
Human-gate classification for SeminarText semantic work.

### Authority
Product Owner

### Date Adopted
2026-08-30

### Supersedes
NONE

### Superseded By
NONE

### Related Contracts / Issues
Issue #106; `DEVELOPMENT_WORKFLOW.md`
<!-- PRODUCT_RULE_END -->

<!-- PRODUCT_RULE_START -->
## PR-004 — Concept Identity Is Independent of Label

### ID
PR-004

### Title
Concept Identity Is Independent of Label

### Status
ACTIVE

### Normative Rule
A Concept stable ID represents semantic identity and is not defined by the
current human-readable label. Renaming a Concept does not by itself create a
new Concept identity.

### Rationale
Labels can change while the underlying semantic identity remains stable.

### Scope
Canonical Knowledge Concept identity and labels.

### Authority
Product Owner

### Date Adopted
2026-08-30

### Supersedes
NONE

### Superseded By
NONE

### Related Contracts / Issues
Issue #64; `schemas/canonical_knowledge_v1.schema.json`
<!-- PRODUCT_RULE_END -->

<!-- PRODUCT_RULE_START -->
## PR-005 — Multiple Terms May Resolve to One Concept

### ID
PR-005

### Title
Multiple Terms May Resolve to One Concept

### Status
ACTIVE

### Normative Rule
Different source terms may represent the same semantic Concept. For example,
`Творец`, `Абсолют`, and `Источник` may resolve to one stable Concept ID when
context and human semantic review confirm that they represent the same Concept.

### Rationale
Terminological variation does not necessarily imply distinct semantic identity.

### Scope
Human-reviewed Concept identity resolution.

### Authority
Product Owner

### Date Adopted
2026-08-30

### Supersedes
NONE

### Superseded By
NONE

### Related Contracts / Issues
Issue #64; future governed Concept review contract
<!-- PRODUCT_RULE_END -->

<!-- PRODUCT_RULE_START -->
## PR-006 — Concept Alias Resolution Requires Human Decision

### ID
PR-006

### Title
Concept Alias Resolution Requires Human Decision

### Status
ACTIVE

### Normative Rule
Similarity, embeddings, heuristics, or LLMs may propose possible alias matches
but MUST NOT automatically merge Concept identities. Supported semantic review
outcomes must include at least `SAME_CONCEPT`, `NEW_CONCEPT`, `RELATED`,
`DISTINCT`, and `DEFER`.

### Rationale
Concept identity merging is a semantic decision that requires explicit human
authority.

### Scope
Future governed Concept alias/identity review; not the Topic ReviewDecision
enum accepted by Issue #106.

### Authority
Product Owner

### Date Adopted
2026-08-30

### Supersedes
NONE

### Superseded By
NONE

### Related Contracts / Issues
Issue #64; Issue #106; future governed Concept review contract
<!-- PRODUCT_RULE_END -->

<!-- PRODUCT_RULE_START -->
## PR-007 — Original Terminology Remains Traceable

### ID
PR-007

### Title
Original Terminology Remains Traceable

### Status
ACTIVE

### Normative Rule
If source terminology differs from the canonical Concept label, the original
source term MUST remain preserved and traceable to its exact evidence
provenance. For example, when the source mention is `Абсолют` and the canonical
Concept label is `Источник`, the original mention MUST NOT be rewritten out of
provenance.

### Rationale
Canonicalization must not erase source language or its evidence trail.

### Scope
Concept labels, source mentions, and Canonical Evidence provenance.

### Authority
Product Owner

### Date Adopted
2026-08-30

### Supersedes
NONE

### Superseded By
NONE

### Related Contracts / Issues
Issue #64; `schemas/canonical_evidence_v1.schema.json`; `schemas/canonical_knowledge_v1.schema.json`
<!-- PRODUCT_RULE_END -->

<!-- PRODUCT_RULE_START -->
## PR-008 — Product Rules Are Repository Truth

### ID
PR-008

### Title
Product Rules Are Repository Truth

### Status
ACTIVE

### Normative Rule
Product Rules MUST NOT depend on ChatGPT conversational memory, Codex memory,
or undocumented developer knowledge. This canonical Registry is the
authoritative durable source.

### Rationale
Durable product governance must survive task, session, and participant changes.

### Scope
All SeminarText Product Rules and task formulation that may affect them.

### Authority
Product Owner

### Date Adopted
2026-08-30

### Supersedes
NONE

### Superseded By
NONE

### Related Contracts / Issues
Issue #108; `DEVELOPMENT_WORKFLOW.md`; `AGENTS.md`
<!-- PRODUCT_RULE_END -->

<!-- PRODUCT_RULE_START -->
## PR-009 — Product Rules Registry Is Extensible and Historical

### ID
PR-009

### Title
Product Rules Registry Is Extensible and Historical

### Status
ACTIVE

### Normative Rule
The Registry is a living appendable governance artifact. New rules receive new
stable IDs. Superseded and retired rules remain historically traceable. IDs are
never reused, and rules are never silently deleted or destructively rewritten.

### Rationale
Stable historical records make product governance auditable and prevent old
meanings from being silently reassigned.

### Scope
Registry maintenance and Product Rule lifecycle.

### Authority
Product Owner

### Date Adopted
2026-08-30

### Supersedes
NONE

### Superseded By
NONE

### Related Contracts / Issues
Issue #108; `scripts/validate_product_rules.py`
<!-- PRODUCT_RULE_END -->

<!-- PRODUCT_RULE_START -->
## PR-010 — Codex Cannot Autonomously Create Product Rules

### ID
PR-010

### Title
Codex Cannot Autonomously Create Product Rules

### Status
ACTIVE

### Normative Rule
Codex MUST NOT convert its own recommendation, architectural judgment,
implementation choice, or inferred Product Owner preference into a Product
Rule. A Product Rule requires explicit Product Owner authority.

### Rationale
Engineering execution and product authority are separate responsibilities.

### Scope
All Codex work that might persist, change, supersede, or retire Product Rules.

### Authority
Product Owner

### Date Adopted
2026-08-30

### Supersedes
NONE

### Superseded By
NONE

### Related Contracts / Issues
Issue #108; `AGENTS.md`; `DEVELOPMENT_WORKFLOW.md`
<!-- PRODUCT_RULE_END -->

<!-- PRODUCT_RULE_START -->
## PR-011 — Distinct Audible Completion and Error Signals

### ID
PR-011

### Title
Distinct Audible Completion and Error Signals

### Status
ACTIVE

### Normative Rule
At the end of every Codex task, Codex MUST emit an audible notification. Normal
successful completion, normal STOP, or an expected HUMAN_GATE uses a SUCCESS
completion sound. FAIL or HARD STOP caused by an error uses an ERROR sound.
SUCCESS and ERROR sounds MUST be clearly distinguishable. Reports use exactly
one of `AUDIBLE_ALERT: SUCCESS_SOUND_SENT` or `AUDIBLE_ALERT:
ERROR_SOUND_SENT`; the same sound must not be used for both outcomes.

### Rationale
Distinct signals make unattended task completion and failure unambiguous.

### Scope
Every Codex task executed for the SeminarText repository.

### Authority
Product Owner

### Date Adopted
2026-08-30

### Supersedes
NONE

### Superseded By
NONE

### Related Contracts / Issues
Issue #108; `AGENTS.md`
<!-- PRODUCT_RULE_END -->

<!-- PRODUCT_RULE_START -->
## PR-012 — Machine Transcript Evidence Has Explicit Assurance

### ID
PR-012

### Title
Machine Transcript Evidence Has Explicit Assurance

### Status
ACTIVE

### Normative Rule
Full-transcript human verification is optional for downstream automatic
SeminarText processing. Machine-generated TranscriptRevisions MAY contribute
to Canonical Evidence when their origin, generation method, verification state,
and exact source provenance are explicit. Human verification SHOULD be
selective when transcript quality materially affects a semantic decision or a
potentially critical transcription error is found. Machine-origin evidence
MUST NOT be represented as fully human-verified without an actual human
verification record.

### Rationale
Machine transcripts can support traceable downstream processing without
claiming human semantic authority, while selective verification provides a
bounded way to improve important evidence and preserve correction lineage.

### Scope
Transcript ingestion, TranscriptRevision, Canonical Evidence, Word Timeline,
and downstream Topic Draft preparation. This rule does not authorize semantic
acceptance or bypass Human Review.

### Authority
Product Owner

### Date Adopted
2026-08-30

### Supersedes
NONE

### Superseded By
NONE

### Related Contracts / Issues
Issue #111; Issue #110; Issue #68; `schemas/canonical_evidence_v1.schema.json`
<!-- PRODUCT_RULE_END -->

<!-- PRODUCT_RULE_START -->
## PR-013 — Autonomous Until Human Gate

### ID
PR-013

### Title
Autonomous Until Human Gate

### Status
ACTIVE

### Normative Rule
After the Product Owner authorizes a bounded task or Issue scope, Codex MUST
autonomously perform all safe, deterministic, mechanically implied technical
substeps that remain inside the same authorized task, product intent, Git
workflow, Dataset permissions, semantic authority, and merge/deploy/runtime
restrictions. Codex MUST NOT stop merely because one technical substep is
complete. It MUST stop at the next authorization boundary: a Product Owner,
`DOMAIN_REVIEW`, `DOMAIN_AUTHORING`, `LOCAL_ACTION`, merge, deploy, separately
gated runtime-reconciliation, new-Issue, scope-expansion, Dataset/Gold,
model-selection, semantic-interpretation, destructive-action, unresolved
unexpected-state, material-ambiguity, Product-Rule-conflict, or unavailable-
required-model gate. Autonomy never expands authorization and remains
fail-closed.

### Rationale
Human control belongs at genuine decision and authorization boundaries, not at
routine deterministic transitions that unnecessarily turn the Domain Owner
into a courier between systems.

### Scope
All Codex execution inside an explicitly authorized SeminarText task or Issue.

### Authority
Product Owner

### Date Adopted
2026-09-04

### Supersedes
NONE

### Superseded By
NONE

### Related Contracts / Issues
Issue #115; `AGENTS.md`; `DEVELOPMENT_WORKFLOW.md`
<!-- PRODUCT_RULE_END -->

<!-- PRODUCT_RULE_START -->
## PR-014 — Autonomous Along Approved Roadmap

### ID
PR-014

### Title
Autonomous Along Approved Roadmap

### Status
ACTIVE

### Normative Rule
Codex MUST execute an approved, unambiguous SeminarText Roadmap autonomously
until a genuine human gate. `ROADMAP_EXECUTION_AUTHORITY = STANDING` applies
when current repository, GitHub, runtime, Roadmap, and machine-readable State
truth mechanically establish the completed item and a singular approved next
item. It includes deterministic state reconciliation, Issue and branch
lifecycle, implementation or analysis inside the approved scope, tests,
in-scope repair, commit, push, PR maintenance, constrained safe merge,
constrained safe runtime reconciliation, verification, objective Issue closure,
and transition to the next approved item.

`MECHANICAL_STATE_RECONCILIATION = AUTO`: Codex MUST synchronize stale factual
Roadmap, State, and control-plane projections when authoritative evidence
determines exactly one truth. Factual synchronization MUST NOT add, remove,
reorder, or reinterpret product priorities and is not a `ROADMAP_CHANGE`.

`ISSUE_LIFECYCLE = AUTO`: Codex MAY create the singular Issue already authorized
by the Roadmap and MUST close an Issue when its objective Definition of Done is
mechanically satisfied and no subjective acceptance remains.

`SAFE_MERGE = AUTO` only when the PR belongs to an already authorized scope;
its exact head, base, changed-file scope, clean mergeability, required tests,
GitHub Quality Gate, and Integrity result are verified; no unexplained
FAIL/WARN, review requirement, scope expansion, Product Rule conflict, reserved
product/domain/semantic decision, Dataset/Gold authority change, destructive
migration, or security/high-risk effect exists. Classification uncertainty
fails closed to a human gate. A governance or Product Rule PR MUST NOT use its
own unmerged policy as merge authority; its authority must already be `ACTIVE`
on main or come from an explicit Product Owner instruction applicable to that
PR.

`SAFE_RUNTIME_RECONCILIATION = AUTO` only for the known governed local runtime
when the source is exact verified `main`, the working tree is clean, required
tests and preflight gates pass, a verified backup and mechanically safe rollback
exist, and the operation performs no destructive migration, Dataset/Gold or
semantic mutation, credential/security change, unknown-target write, or
externally consequential production release. Codex MUST use only the governed
deployment mechanism, then verify hashes, functional smoke, tests, Integrity,
and source/runtime identity. It may perform one mechanically safe governed
rollback after failure; uncertainty or failed recovery is a hard stop.

Ordinary deterministic technical failures are repaired and reverified
autonomously when the repair remains in scope. Codex stops only for a genuine
Product Owner or domain decision, Roadmap change, semantic authority,
Dataset/Gold authority, high-risk irreversible operation, security/credential
decision, uncovered external production release, material architectural choice,
unresolvable ambiguity, unavailable required authority, or Product Rule
conflict. Reports and completed technical stages do not themselves create a
gate, and the user MUST NOT be used as a courier between deterministic steps.

### Rationale
An approved and unambiguous Roadmap already supplies the dispatch decision for
routine transitions. Objective reconciliation, administration, verification,
merge, and reversible local-runtime synchronization add no product judgment
when their fail-closed conditions are proven. Requiring the Domain Owner to
relay those deterministic operations adds no governance and makes the human a
courier.

### Scope
The SeminarText execution loop from observed truth through the next explicitly
approved Roadmap work and its first genuine human gate. It does not authorize a
Roadmap or product-priority change, semantic acceptance or authoring,
Dataset/Gold authority changes, destructive or irreversible operations,
security decisions, unknown runtime targets, or external production releases
outside the standing policy.

### Authority
Product Owner

### Date Adopted
2026-09-04

### Supersedes
NONE

### Superseded By
NONE

### Related Contracts / Issues
Issue #117; `AGENTS.md`; `DEVELOPMENT_WORKFLOW.md`
<!-- PRODUCT_RULE_END -->
