# Topic Engine Freeze Decision Packet — Issue #61

Status: `DOMAIN_REVIEW_COMPLETED`

Evidence cutoff: 2026-08-29

New experiments performed for this packet: **none**

## Decision boundary

This packet records existing accepted evidence only. Product Owner disposition:
`FREEZE_LOCAL_PEAK_FOR_DATASET_D_CANDIDACY`. It freezes Local Peak as a future
Dataset D candidate, but does not promote an engine, authorize Dataset D,
retune Dataset C, or create a new algorithm family. The machine gate reports
candidate freeze `COMPLETE` while Dataset D access remains `BLOCKED`.

## Current role matrix

| Role ID | Engine ID | Accepted meaning | Production status |
|---|---|---|---|
| `production_legacy` | `legacy_ollama_gemma_runtime` | Current Ollama/Gemma CLI behavior | Current runtime; not a promoted production baseline |
| `experimental_primary` | `bge_m3_local_peak_v1` | Primary experimental Boundary candidate | Not runtime; not frozen |
| `comparator` | `bge_m3_pelt_v1` | Recall-oriented comparator | Not runtime; not frozen |
| `challenger` | `treeseg_external_adapt_v1` | External ADAPT challenger / hierarchy candidate | Isolated; not production |
| `frozen_candidate` | `bge_m3_local_peak_v1` | Frozen for future Dataset D candidacy | Not runtime; not production; Dataset D blocked |

The exact configurations and provenance are recorded in
`governance/topic_engine_lifecycle.json`.

## Existing evidence

- Local Peak tolerance ±2 F1: Dataset A `0.405`, B `0.533`, C `0.583`.
  On C it produced 24 predictions for 24 Gold boundaries; this is positive
  transfer evidence, not a production decision.
- PELT tolerance ±2 F1: A `0.432`, B `0.447`, C `0.345`. On C its recall was
  `0.625`, but precision was `0.238` with 63 predictions for 24 Gold boundaries;
  it remains the recall comparator.
- TreeSeg boundary challenge F1 at tolerance ±2: A `0.632`, B `0.659`.
  The separate hierarchy POC is ready for Product Owner review, but explicitly
  supplies neither hierarchy Gold nor production Boundary promotion evidence.
- Dataset C is closed frozen evidence. It may not be used for further tuning or
  architecture selection. Dataset E is excluded from Topic Engine evidence.

Sources: `analysis/DATASET_B_FROZEN_VALIDATION.md`,
`analysis/DATASET_C_BLIND_VALIDATION.md`,
`analysis/EXTERNAL_TOPIC_BASELINE_SURVEY_ISSUE_45.md`, and
`analysis/TREESEG_GLOBAL_STRUCTURE_POC_ISSUE_52.md`.

## Product Owner decision record

Recorded disposition:
`FREEZE_LOCAL_PEAK_FOR_DATASET_D_CANDIDACY`.

The exact candidate, configuration, code digest, acceptance criteria and analysis
plan are immutable and hash-bound in `governance/topic_engine_freeze.json`.
Issue #61 does not authorize a Dataset D run, another tournament, a new family,
Dataset C retuning, or Dataset E evidence.

## Frozen records

The approved freeze binds:

- the selected existing engine ID and its role before freeze;
- the exact configuration and canonical SHA-256;
- an immutable acceptance-criteria artifact and SHA-256;
- an immutable analysis-plan artifact and SHA-256;
- Product Owner decision identity and timestamp.

The freeze gate also independently requires Dataset D source identity and source
quality acceptance under Issue #66, plus explicit authorization for exactly one
blind run. No freeze decision by itself satisfies those conditions.

No further candidate choice is pending in Issue #61. Dataset D remains blocked
pending Issue #66 source acceptance and a later explicit one-run authorization.

## Issue #61 requirement → evidence self-check

| Requirement | Evidence | Result |
|---|---|---|
| Explicit lifecycle roles | `governance/topic_engine_lifecycle.json` | PASS |
| Result engine/version/model/config/dataset provenance | governed result writers and `tests/test_topic_benchmark_run.py` | PASS |
| Runtime does not imply research promotion | CLI `runtime-identity`, State and lifecycle | PASS |
| Accepted Local Peak/PELT/TreeSeg/legacy roles preserved | lifecycle role matrix above | PASS |
| Candidate/config/criteria/plan frozen before D | hash-bound `governance/topic_engine_freeze.json` | PASS |
| New custom Boundary families denied | lifecycle policy and validator | PASS |
| 50-word BenchmarkSegments are topic-neutral | lifecycle, State and Roadmap | PASS |
| Product Owner packet uses existing evidence only | this packet; no experimental result changes | PASS |
| Dataset C tuning denied | Dataset Registry guard test | PASS |
| Dataset D prediction access denied | Dataset Registry and freeze-gate tests | PASS |
| Dataset E Topic evidence denied | Dataset Registry guard test | PASS |

Self-check conclusion: the Topic candidate freeze is complete. Dataset D access
is independently blocked; production runtime remains
`legacy_ollama_gemma_runtime`.
