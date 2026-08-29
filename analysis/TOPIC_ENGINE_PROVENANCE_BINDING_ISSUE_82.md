# Topic Engine Provenance Binding — Issue #82

This blocking repair closes the deployed-validation defect found after Issue
#61. It does not change the Product Owner freeze decision, candidate
configuration, thresholds, or Dataset D state.

## Provenance matrix

| Engine ID | Role | State | Authoritative implementation | External pin | Deployment verification |
|---|---|---|---|---|---|
| `legacy_ollama_gemma_runtime` | `production_legacy` | `ACTIVE_IMPLEMENTATION` | `seminartext_modules/seminartext_topics.py` + SHA-256 | Ollama `gemma3:4b` runtime-selectable identity | Runtime file hash |
| `bge_m3_local_peak_v1` | `experimental_primary`, `frozen_candidate` | `ACTIVE_IMPLEMENTATION` | `analysis/experiments/bge_m3_changepoint_topic_engine.py` + SHA-256 | Ollama `bge-m3:latest`, digest `790764…` | Governed hash attestation; repository predeploy hash required |
| `bge_m3_pelt_v1` | `comparator` | `ACTIVE_IMPLEMENTATION` | `analysis/experiments/bge_m3_ruptures_topic_engine.py` + SHA-256 | `ruptures==1.1.9`, pinned BGE-M3 digest | Governed hash attestation |
| `treeseg_external_adapt_v1` | `challenger` | `EXTERNAL_PINNED_IMPLEMENTATION` | `run_hierarchy_poc.py` + SHA-256 and config manifest | `topic-treeseg@f18929a…`, pinned BGE-M3 digest | Governed hash attestation |
| `legacy_ollama_sliding_subwindow_experiment` | historical | `HISTORICAL_IMPLEMENTATION` | sliding adapter + SHA-256 and frozen A/B evidence hashes | Historical `gemma3:4b` | Governed hash attestation |
| `external_chonkie_baseline` | historical rejected | `NON_EXECUTABLE_HISTORICAL_RECORD` | adapter/result/source-snapshot provenance hashes | Chonkie `1.7.0` / surveyed commit | Non-executable record; no runtime file required |
| `external_texttiling_baseline` | historical rejected | `NON_EXECUTABLE_HISTORICAL_RECORD` | adapter/result/source-snapshot provenance hashes | NLTK `3.10.3` / surveyed commit | Non-executable record; no runtime file required |

All paths are repository-relative. No personal absolute path is accepted.

## Deployment closure

Research directories are intentionally not copied into installed runtime. The
governed deploy preflight validates source implementation hashes on `main`, then
deploys the lifecycle/freeze records and validator atomically. G2 verifies every
deployed component is byte-identical to that source. In the installed snapshot,
the validator uses `GOVERNED_HASH_ATTESTATION` for repository-only research
implementations; this is an attestation of the predeploy hash chain, not a claim
that the research files are executable runtime modules.

## Requirement → evidence matrix

| Requirement | Evidence | Result |
|---|---|---|
| Active implementation exists and hash matches | lifecycle validator repository mode | PASS |
| Frozen candidate binds Local Peak implementation/config/model digest | freeze gate implementation binding checks | PASS |
| Historical records do not require runnable code | explicit historical states and provenance artifacts | PASS |
| External pins remain immutable | TreeSeg/Chonkie/NLTK package, version and commit fields | PASS |
| Deployed and repository validation agree | `--deployed` attestation mode plus deploy/G2 smoke | PASS |
| No absolute personal paths | recursive lifecycle validator | PASS |
| Dataset D/C/E safeguards unchanged | Dataset Registry and regression tests | PASS |
| No benchmark, Gold, prediction, model or dependency mutation | exact diff and test inventory | PASS |

## Scope stop

After the repair PR, Product Owner review is required. Do not self-merge, deploy
the feature branch, open Dataset D, run predictions, create Gold, or begin Issue
#62.
