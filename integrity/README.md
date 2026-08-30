# SeminarText Project Integrity Gate

Run the repository-owned, read-only gate from the repository root:

```bash
./scripts/seminartext-integrity
./scripts/seminartext-integrity --json
```

Run it after each merge and before beginning the next Issue. A real existing
deployment mismatch is expected to remain a reported failure until an explicit
deployment operation reconciles it; the gate never auto-deploys.

`integrity_contract.json` is the gate contract,
`milestone_reconciliation.json` is the repository-owned active control-plane
contract, and `integrity_report.schema.json` defines the JSON report shape. G3
validates accepted decisions, dispositions, lifecycle truth, and the structural
governance of the one canonical Product Rules Registry at
`docs/architecture/SEMINARTEXT_PRODUCT_RULES.md`. This includes stable IDs,
allowed lifecycle values, reciprocal supersession, uniqueness, and required
operating/ChatGPT/GitHub/CI control-loop wiring; G3 does not claim semantic
compliance proof. G8 validates the current milestone, next actions, blocked
work, and runtime reconciliation.
The implemented G4 Dependency Truth remains active. The authoritative gate
inventory is:

| Gate | Name | Implementation | Blocking policy |
| --- | --- | --- | --- |
| G1 | Git Truth | IMPLEMENTED | blocking |
| G2 | Runtime Truth | IMPLEMENTED | blocking |
| G3 | Governance Truth | IMPLEMENTED | blocking |
| G4 | Dependency Truth | IMPLEMENTED | blocking |
| G5 | Canonical Contract Truth | IMPLEMENTED | blocking |
| G6 | End-to-End Truth | NOT_IMPLEMENTED | future_blocking |
| G7 | Test Truth | IMPLEMENTED | blocking |
| G8 | Product State Truth | IMPLEMENTED | blocking |

G6 remains explicitly `NOT_IMPLEMENTED` and is never rendered as PASS. G5
composes the accepted Canonical Evidence v1 and Canonical Knowledge v1
validators, lifecycle mapping, and Golden Slice compatibility checks; malformed
or incomplete evidence fails closed. This table is documentation only; the
machine-readable contract remains the sole gate definition.

The checker observes repository, deployment, governance, tests, and product
state. It never fetches, pulls, checks out, cleans, deploys, installs packages,
updates State, or changes project data.

## Control-plane reconciliation

The local gate is deterministic and offline. It reads committed JSON sources
and one marker-bounded JSON snapshot in the Roadmap; it never calls GitHub.
Historical evidence paths are presence-checked but their prose is deliberately
not interpreted as active state. The human and JSON reports expose:

- `CONTROL_PLANE_RECONCILED` / `control_plane_reconciled`;
- `NEXT_ISSUE_ALLOWED` / `next_issue_allowed`;
- the active `HUMAN_GATE` and separately reported `GITHUB_LIFECYCLE_CHECK`.

An accepted decision represented as pending, a stale State/Roadmap projection,
a completed-current milestone, a blocked next action, a human-gate bypass, an
incomplete required runtime reconciliation that permits progression, or an
accepted-disposition contradiction fails G3 or G8. A truthful pending human
gate is not itself a contradiction: the gates pass while
`NEXT_ISSUE_ALLOWED: NO` remains explicit.

## Result semantics

- `BOOTSTRAP_IMPLEMENTATION: PASS` means the v1 contract was valid and every
  declared implemented check ran to a deterministic result. It does not mean the
  project is healthy.
- `PROJECT_INTEGRITY: FAIL` means an implemented blocking invariant failed.
- `PROJECT_INTEGRITY: PARTIAL` means no implemented blocking invariant failed,
  but a WARN or future `NOT_IMPLEMENTED` gate prevents a full integrity claim.
- `PROJECT_INTEGRITY: PASS` is reserved for a future state where all contracted
  gates are implemented and pass.

Exit code `0` means no implemented blocking gate failed, even when the report is
PARTIAL because future gates remain. Exit code `1` means project-integrity
failure. Exit code `2` means the contract or checker itself failed internally.

G7 uses the supported full pytest command and reports every skip. Until the
active runtime is rebuilt from the declared development profile, any skip
yields WARN with the dependency-policy limitation stated explicitly.

Use `--root` and `--deploy-dir` only to inspect another controlled checkout or
an isolated deployment fixture. The default deployment observation is
`$SEMINARTEXT_DEPLOY_DIR` when set, otherwise `~/bin`.
