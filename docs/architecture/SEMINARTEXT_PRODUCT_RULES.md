# SeminarText Product Rules Registry v1

<!-- SEMINARTEXT_PRODUCT_RULES_REGISTRY_V1 -->

This file is the one canonical Product Rules Registry for SeminarText. It is
permanent, appendable, version-controlled, auditable repository truth. Product
Rules do not depend on conversational memory or undocumented developer
knowledge.

## Authority and control loop

The authority chain is:

`Product Owner decision -> ChatGPT formalization -> explicitly authorized Codex persistence -> GitHub history -> mandatory ChatGPT/Codex read -> Issue/PR references -> CI and Integrity structural validation`

- The Product Owner alone adopts, changes, supersedes, or retires Product Rules.
- ChatGPT may formalize an explicit Product Owner decision into precise wording
  and prepare a bounded persistence task.
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
2. ChatGPT checks this Registry, determines that the decision belongs here,
   identifies the next safe ID, and prepares one bounded Codex task.
3. Codex rereads the current Registry and fails closed on an ID collision or an
   `ACTIVE` rule conflict.
4. Codex adds or modifies only the explicitly authorized rule. Existing IDs are
   not renumbered, reused, or destructively rewritten.
5. Structural validation, focused tests, the full suite, Integrity, and exact
   diff/scope checks run.
6. Codex commits, pushes, and opens a PR. The Product Owner reviews it.
7. Merge requires separate authorization. Runtime reconciliation occurs only
   when actually required and separately authorized.

Concurrent proposals that select the same next ID must stop and rebase against
the current Registry; Codex must not resolve the semantic choice autonomously.

## Initial Product Rules

The following eleven rules are the bounded Product Owner-approved initial
inventory. Concept alias outcomes described below are future semantic identity
review requirements and do not redefine the existing Topic ReviewDecision
values `ACCEPT`, `RENAME`, `SPLIT`, `MERGE`, `REJECT`, and `DEFER`.

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
