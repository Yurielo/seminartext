# AUDIT-R3 — Milestone Reconciliation / Control-Plane Integrity Gate

Issue #87 repairs the repeat-audit defect in which accepted, merged work could
coexist with an obsolete current milestone or next-action sequence. It changes
repository governance and Integrity checks only; product algorithms, semantic
contracts, datasets, Gold, predictions, and production runtime are unchanged.

## Authority and lifecycle

`integrity/milestone_reconciliation.json` is the offline reconciliation
contract. `SEMINARTEXT_4_STATE.json#control_plane` and the marker-bounded JSON
snapshot under Roadmap `CURRENT NEXT ACTION` are exact active projections. The
validator reads committed JSON sources through declared JSON Pointers. It does
not infer active truth from prose and does not call GitHub.

AUDIT-R1 and AUDIT-R2 are recorded `COMPLETE_ACCEPTED`. AUDIT-R3 is
`IMPLEMENTED_PENDING_PRODUCT_OWNER_REVIEW`: implementation is complete, but
acceptance is not claimed. Its Product Owner gate and incomplete post-merge
runtime reconciliation both keep `NEXT_ISSUE_ALLOWED` false.

## Integrity split

- G3 owns accepted decisions, dispositions, lifecycle assertions, and the
  machine-readable State projection.
- G8 owns the current milestone, ordered prerequisites, Roadmap projection,
  blocked actions, human gates, and runtime-reconciliation progression rules.
- The runner exposes `CONTROL_PLANE_RECONCILED`, `NEXT_ISSUE_ALLOWED`,
  `HUMAN_GATE`, and the separate offline-safe `GITHUB_LIFECYCLE_CHECK`.

Historical files are only presence-checked as evidence. Terms such as
`pending`, `candidate`, or `ready_for_product_review` inside those files cannot
be mistaken for active state.

## Requirement → implementation → evidence → test

| Requirement | Implementation | Evidence | Test |
| --- | --- | --- | --- |
| Machine-readable model | Typed milestone records and source assertions | `integrity/milestone_reconciliation.json` | contract/current-state positive tests |
| Accepted decision not pending | accepted/status/human-gate invariant | `CP_ACCEPTED_PENDING` | stale accepted milestone fixture |
| Completed milestone not current | current lifecycle invariant | `CP_COMPLETED_STILL_CURRENT` | completed-current fixture |
| Ordered progression | prerequisite milestone validation | `CP_SEQUENCE_VIOLATION` | incomplete predecessor fixture |
| Blocked work stays blocked | blocked/next-action intersection | `CP_BLOCKED_ACTION_EXECUTABLE` | Dataset D next-action fixture |
| Human gate blocks next Issue | pending-gate progression rule | `CP_HUMAN_GATE_BYPASS` | Product Owner gate fixture |
| Runtime state explicit | required/complete booleans | `CP_RUNTIME_RECONCILIATION_BYPASS` | pending, completed, and not-required fixtures |
| Dispositions stay consistent | JSON Pointer assertions | `CP_ASSERTION_FAILED` | TreeSeg, freeze, Canonical Knowledge fixtures |
| State/Roadmap agreement | exact generated projections | `CP_STALE_STATE`, `CP_STALE_ROADMAP` | independent stale projections |
| Historical wording safe | active snapshot isolation | historical evidence inventory | stale historical wording fixture |
| Offline operation | repository paths only | `GITHUB_LIFECYCLE_CHECK=NOT_RUN` | real-state positive test |
| Visible progression verdict | runner human + JSON fields | Integrity output/schema | report-output test |

## Preserved accepted decisions

TreeSeg remains a non-production challenger without expansion authorization.
Obsidian remains `ADAPT_FURTHER` with production export blocked. Local Peak
remains the frozen, non-promoted Dataset D candidate. Canonical Knowledge v1
remains accepted with strict schema enforcement and accepted lifecycle mapping.
Dataset C remains closed/frozen, Dataset D remains locked, Dataset E remains
excluded, and Issue #65 remains unauthorized.
