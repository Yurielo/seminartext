# SeminarText Project Integrity Gate v1

Run the repository-owned, read-only gate from the repository root:

```bash
./scripts/seminartext-integrity
./scripts/seminartext-integrity --json
```

Run it after each merge and before beginning the next Issue. A real existing
deployment mismatch is expected to remain a reported failure until an explicit
deployment operation reconciles it; the gate never auto-deploys.

`integrity_contract.json` is the version-controlled invariant contract, and
`integrity_report.schema.json` defines the JSON report shape. G1, G2, G3, G7,
and the implemented G8 foundation are active. G4, G5, and G6 are explicitly
`NOT_IMPLEMENTED`; they are never rendered as PASS.

The checker observes repository, deployment, governance, tests, and product
state. It never fetches, pulls, checks out, cleans, deploys, installs packages,
updates State, or changes project data.

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

G7 uses the supported full pytest command and reports every skip. Until G4
Dependency Truth is implemented, any skip yields WARN with the dependency-policy
limitation stated explicitly.

Use `--root` and `--deploy-dir` only to inspect another controlled checkout or
an isolated deployment fixture. The default deployment observation is
`$SEMINARTEXT_DEPLOY_DIR` when set, otherwise `~/bin`.
