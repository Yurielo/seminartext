# Human Review Workflow MVP — Issue #106

## Product contract

Human semantic review is an intrinsic SeminarText stage:

`Evidence → Topic Draft → REVIEW_REQUIRED → Human Review → ReviewDecision → reviewed Topic state → Canonical Knowledge`

Machine-assisted generation is `DOMAIN_AUTHORING` assistance. It never performs `DOMAIN_REVIEW` and never creates an accepted Topic automatically.

## CLI

```text
seminartext project-review-prepare PROJECT --drafts FILE --output DIR
seminartext project-review-status PROJECT --package FILE [--decisions FILE]
seminartext project-review-apply PROJECT --package FILE --decisions FILE --output FILE
```

`prepare` validates Topic Drafts against the project's current Canonical Evidence and writes:

- `review_package.json` — deterministic machine-readable package;
- `REVIEW.md` — sequential human-readable evidence/locator view;
- `review_decisions.template.json` — explicit human decision document.

`status` validates the current evidence and optional decisions and reports `TOTAL`, `UNREVIEWED`, `ACCEPTED`, `RENAMED`, `SPLIT`, `MERGED`, `REJECTED`, and `DEFERRED` counts.

`apply` requires every draft to have exactly one explicit human decision. It validates evidence/package/topic hashes, applies decisions mechanically, and emits `seminartext.project_knowledge_input` v1.0.0. The output is validated through the existing Canonical Knowledge bridge before it is written.

## Lifecycle semantics

| Decision | Result |
|---|---|
| `ACCEPT` | Topic becomes `ACCEPTED`; explicit human decision is mandatory. |
| `RENAME` | Stable Topic ID is preserved, content version increases, status remains `PROVISIONAL` until a later explicit `ACCEPT`. |
| `SPLIT` | Target becomes `SUPERSEDED`; explicitly supplied result Topics start `PROVISIONAL`. |
| `MERGE` | Targets become `SUPERSEDED`; explicitly supplied result Topic starts `PROVISIONAL`. |
| `REJECT` | Topic becomes `REJECTED` and remains auditable. |
| `DEFER` | Topic remains `PROVISIONAL` and non-authoritative. |

No lifecycle transition occurs merely because a JSON or Markdown file was edited.

## Fail-closed boundaries

The workflow rejects missing evidence, invalid Source/TranscriptRevision/Word references, non-contiguous ranges, duplicate IDs or decisions, orphan decisions, unsupported actions, invalid SPLIT/MERGE lineage, stale evidence, stale packages, stale Topic snapshots, incomplete review, and output collisions.

Canonical identities contain stable IDs and hashes, not machine-local paths. The committed fixture is synthetic and does not contain real seminar semantics or Product Owner/domain decisions.

## Scope

Issue #106 does not resume #68, process real Stress Code Days 2–4, access protected datasets, alter Gold, run Topic Engine experiments, implement G6, deploy, or reconcile runtime.
