# Dataset Governance Firewall

Status: enforced repository policy (Issue #60).

`dataset_registry.json` is the authoritative machine-readable inventory for
Dataset/Gold roles. `seminartext_modules/dataset_governance.py` is the single
fail-closed policy evaluator used before governed benchmark or experiment code
may access Gold, predictions, or Topic Engine execution.

An unregistered or ambiguous project is denied. A file existing on disk, an
open historical Issue, or an old experiment artifact never grants permission.

## Current role matrix

| ID | Role | Gold | Tuning / validation | Lock |
|---|---|---|---|---|
| A | development calibration | complete/frozen | accepted development lifecycle | open development |
| B | development error-analysis history | complete/frozen | historical/frozen reproduction only | frozen evidence |
| C | closed frozen evidence | complete/frozen | denied; no rerun | closed/frozen |
| D | locked test | not created | denied | locked; source-quality blocked |
| E | excluded from Topic Engine evidence | prohibited | denied | excluded |
| F | potential development after repair | not created | denied pending repair/acceptance | quarantined |
| G1 | proposed development | not authored | denied pending human gates | pending |
| G2 | proposed frozen-validation candidate | not authored | denied pending human gates | pending |

Dataset D's selected project/date are recorded, but source ID, media reference,
duration and SHA-256 remain explicitly incomplete. Issue #66 must establish them
topic-agnostically; incompleteness is a lock condition, never an invitation to
inspect predictions.

Dataset E artifacts are historical transcript-engineering evidence only. Their
lifecycle is indexed in
`analysis/HISTORICAL_ARTIFACT_LIFECYCLE_INDEX.json`.

## G1/G2 human sequence

The only allowed future sequence is:

1. Product Owner role acceptance (`DOMAIN_REVIEW`);
2. human transcript verification;
3. domain-authored Topic Gold (`DOMAIN_AUTHORING`);
4. Product Owner acceptance;
5. immutable role/Gold freeze;
6. registry update enabling only the accepted use;
7. evaluation or development, if explicitly permitted.

Predictions must not be read to decide roles or author Gold.

## Guard use

```bash
seminartext dataset-policy-check D benchmark_run --json
python3 seminartext_modules/dataset_governance.py validate
```

Adding a benchmark or experiment entry point requires calling the central guard
before opening benchmark, Gold, prediction, or result files. Tests must prove
both its permitted role and every relevant forbidden role.
