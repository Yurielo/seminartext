# 0002 - Evidence-First Parallel Development

Date: 2026-08-26

## Status

Accepted

## Context

The previous SeminarText 4.x roadmap was effectively linear: Evidence Foundation
fed Topic Engine, `TOPIC SEGMENTATION STABLE` gated Seminar Structure, and only
then could Knowledge/Obsidian work begin. Two independent architecture/product
audits found that this dependency confused the automation mechanism with the end
product and delayed product learning that can be obtained from verified topics.

Accepted evidence also advanced beyond the machine-readable State: Dataset C
blind validation is complete and closed, Dataset E is excluded, Dataset D remains
locked, Dataset F is quarantined, and the first Word Alignment bake-off requires
one additional controlled decision experiment.

SeminarText's product objective remains an evidence-grounded, maintainable
knowledge system for the Product Owner's seminar corpus. Topic Engine, Gold, Word
Alignment, Obsidian, and related tools are enabling components.

## Decision

Adopt **Evidence-First Parallel Development** with the Canonical Evidence Layer
as the shared foundation.

Two tracks proceed in parallel after their minimum evidence prerequisites:

1. **Semantic Automation** — Word Timeline, benchmark segments, Boundary Engine,
   Topic Draft, and Seminar Structure. Topic Engine remains critical for scale.
2. **Knowledge Product** — evidence plus verified manual, Gold, or explicitly
   marked semi-automatic topics, then concepts, relations, and a bounded Obsidian
   Knowledge Prototype.

The tracks converge into a Verified Knowledge Layer and later multi-seminar and
product outputs.

`TOPIC SEGMENTATION STABLE` is not a prerequisite for the Golden Seminar
Knowledge Slice or Obsidian Knowledge Prototype. Their prerequisite is the
minimum Canonical Evidence contract needed to preserve stable identity and
auditable provenance.

The first Golden Seminar Vertical Slice defaults to the controlled target-corpus
project `Стресс код`. Its minimum entities are:

- `Seminar`;
- `Source`;
- `Topic`;
- `Concept`;
- `Evidence`.

The prototype does not require full bidirectional Obsidian sync, a graph database,
production RAG, site integration, or Marketing Passport.

Canonical machine-readable data is primary. TXT, SRT, DOCX, and Markdown evolve
toward views/exports. The canonical evidence schema is speaker-ready with an
optional/nullable `speaker_id`; diarization implementation is deferred.

Before substantial custom work, apply **ADOPT → ADAPT → BUILD**: perform a bounded
external survey and classify viable options as `ADOPT`, `ADAPT`, `REJECT`, or
`BUILD`. This is mandatory before substantial new custom Topic Engine algorithms
and applies to alignment, diarization, semantic segmentation, retrieval/RAG,
Obsidian integration, and graph technology.

Keep these layer responsibilities distinct:

- Boundary Detection finds local semantic transitions.
- Seminar Structure handles hierarchy, merge, and recurrence of local topics.
- Knowledge Engine handles concepts and relations across topics and seminars.

Topic automation readiness will eventually be assessed as
`TOPIC AUTOMATION USABLE`, using Boundary F1 plus over/under-segmentation, human
correction time per source hour, semantic usefulness, cross-seminar
generalization, and provenance quality.

## Dataset guardrails

- Dataset A remains DEVELOPMENT / CALIBRATION evidence; Gold unchanged.
- Dataset B remains DEVELOPMENT / ERROR-ANALYSIS HISTORY; Gold unchanged.
- Dataset C is complete, frozen, and closed for tuning/architecture selection.
- Dataset D remains an untouched LOCKED TEST, blocked by source quality and
  repairable only topic-agnostically before candidate/config/criteria freeze.
- Dataset E remains `EXCLUDED_FROM_TOPIC_ENGINE_EVIDENCE`; historical
  resegmentation is engineering history only.
- Dataset F remains quarantined/potential DEVELOPMENT until source/ASR repair and
  controlled target-corpus confirmation.

## Consequences

- Product usefulness and evidence-schema assumptions can be tested before
  automatic boundaries are perfect.
- Manual/Gold topics are an explicit bootstrap input, not a hidden substitute
  for automation.
- Topic Engine remains an active, measurable scalability track rather than a
  blocker for all downstream learning.
- Global Seminar Structure can be tested separately with verified topics.
- The team must maintain provenance and lifecycle labels so verified knowledge
  cannot be confused with machine drafts.
- Roadmap and State must share a policy checkpoint and be reviewed together when
  dataset roles, blockers, or next actions change.
- This decision does not implement Word Alignment, canonical schema, Obsidian,
  Knowledge Engine, new algorithms, experiments, or Gold changes.

## Alternatives considered

### Keep the strictly linear Topic Engine gate

Rejected. It postpones product validation even though verified topics can safely
exercise the knowledge workflow and provenance model.

### Demote or abandon Topic Engine

Rejected. Manual bootstrap is not a scalable production strategy; Semantic
Automation remains essential.

### Build all components custom-first

Rejected. It ignores mature external options and raises maintenance risk before
requirements are validated.

### Adopt an enterprise graph/RAG architecture immediately

Rejected. The bounded local-first prototype does not yet justify that complexity.

## Consistency

Human-readable strategy is maintained in `SEMINARTEXT_4_ROADMAP.md`.
Machine-readable operational state is maintained in `SEMINARTEXT_4_STATE.json`.
Both use checkpoint `evidence_first_parallel_v1`. The review for this decision is
`analysis/ROADMAP_STATE_CONSISTENCY_REVIEW_2026-08-26.md`.
