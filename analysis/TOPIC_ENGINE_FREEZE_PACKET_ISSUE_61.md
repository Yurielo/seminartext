# Topic Engine Freeze Decision Packet — Issue #61

Status: `DOMAIN_REVIEW_REQUIRED`

Evidence cutoff: 2026-08-29

New experiments performed for this packet: **none**

## Decision boundary

This packet records existing accepted evidence only. It does not promote an
engine, freeze a candidate, authorize Dataset D, retune Dataset C, or create a
new algorithm family. Until the Product Owner records a decision,
`governance/topic_engine_freeze.json` remains `PENDING_DOMAIN_REVIEW` and its
machine gate must return `BLOCKED`.

## Current role matrix

| Role ID | Engine ID | Accepted meaning | Production status |
|---|---|---|---|
| `production_legacy` | `legacy_ollama_gemma_runtime` | Current Ollama/Gemma CLI behavior | Current runtime; not a promoted production baseline |
| `experimental_primary` | `bge_m3_local_peak_v1` | Primary experimental Boundary candidate | Not runtime; not frozen |
| `comparator` | `bge_m3_pelt_v1` | Recall-oriented comparator | Not runtime; not frozen |
| `challenger` | `treeseg_external_adapt_v1` | External ADAPT challenger / hierarchy candidate | Isolated; not production |
| `frozen_candidate` | `null` | Reserved only for an approved freeze | Pending Product Owner decision |

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

## Product Owner decision requested

Choose exactly one disposition:

1. `FREEZE_LOCAL_PEAK_FOR_DATASET_D_CANDIDACY` — authorize preparation of an
   immutable Local Peak candidate/configuration/criteria/analysis-plan record.
   This does not promote it to production and does not open Dataset D.
2. `KEEP_TOPIC_ENGINE_UNFROZEN_AND_DEFER_DATASET_D` — keep all current roles and
   do not proceed toward a Dataset D run.

If neither disposition is acceptable, create a separate Product Owner Issue
with bounded authority. Issue #61 itself does not authorize another tournament,
new family, Dataset C retuning, or Dataset E evidence.

## Required records after an approval to freeze

Before Dataset D can become eligible, a follow-up governed change must bind:

- the selected existing engine ID and its role before freeze;
- the exact configuration and canonical SHA-256;
- an immutable acceptance-criteria artifact and SHA-256;
- an immutable analysis-plan artifact and SHA-256;
- Product Owner decision identity and timestamp.

The freeze gate also independently requires Dataset D source identity and source
quality acceptance under Issue #66, plus explicit authorization for exactly one
blind run. No freeze decision by itself satisfies those conditions.

## Exact response syntax

Respond with one line:

`ISSUE_61_DECISION: FREEZE_LOCAL_PEAK_FOR_DATASET_D_CANDIDACY`

or

`ISSUE_61_DECISION: KEEP_TOPIC_ENGINE_UNFROZEN_AND_DEFER_DATASET_D`
