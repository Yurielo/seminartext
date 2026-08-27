# Roadmap / State consistency review

Date: 2026-08-26  
Issue: #36  
Checkpoint: `evidence_first_parallel_v1`

## Scope

This review compares the human-readable `SEMINARTEXT_4_ROADMAP.md` with the
machine-readable `SEMINARTEXT_4_STATE.json` after adoption of Evidence-First
Parallel Development. It does not reinterpret historical experiments or modify
algorithms, predictions, or Gold.

## Dataset roles

| Dataset | Roadmap | State | Consistent |
|---|---|---|---|
| A | DEVELOPMENT / CALIBRATION; 6/6 Gold, 48 topics | `DEVELOPMENT_CALIBRATION`; 6/6, 48 | Yes |
| B | DEVELOPMENT / ERROR-ANALYSIS HISTORY; 6/6 Gold, 34 topics | `DEVELOPMENT_ERROR_ANALYSIS_HISTORY`; 6/6, 34 | Yes |
| C | blind validation complete; 6/6 Gold, 24 topics; frozen/closed | `FROZEN_CLOSED_EVIDENCE`; complete; tuning and architecture selection false | Yes |
| D | untouched `LOCKED TEST`; source quality insufficient; topic-agnostic repair only | `LOCKED_TEST`; source-quality blocked; Topic Engine access false | Yes |
| E | `EXCLUDED FROM TOPIC ENGINE EVIDENCE`; history only | `EXCLUDED_FROM_TOPIC_ENGINE_EVIDENCE`; development and Gold false | Yes |
| F | quarantined/potential DEVELOPMENT after source/ASR repair | `POTENTIAL_DEVELOPMENT_AFTER_REPAIR`; development false until repair | Yes |

## Architecture and blockers

| Fact | Roadmap | State | Consistent |
|---|---|---|---|
| Shared foundation | Canonical Evidence Layer | `canonical_evidence_layer` | Yes |
| Development model | Semantic Automation and Knowledge Product in parallel | `evidence_first_parallel_development`; two active/planned tracks | Yes |
| Topic Engine | Critical scalability track, not abandoned | `critical_parallel_scalability_track`; in progress | Yes |
| Knowledge prototype gate | Minimum Canonical Evidence foundation | `blocked_by: minimum_canonical_evidence_foundation` | Yes |
| `topic_engine.stable` gate | Explicitly not required for prototype | `not_blocked_by: topic_engine.stable` | Yes |
| Word Alignment | Final controlled decision required | prior verdict `ADDITIONAL_ALIGNMENT_EXPERIMENT_REQUIRED`; final experiment next | Yes |
| Golden Slice | `Стресс код`; verified/manual/Gold/semi-auto topics allowed | same project and allowed inputs | Yes |
| Global Structure POC | allowed with verified/manual topics before perfect boundaries | not blocked by perfect automatic boundaries | Yes |

## Near-term sequence

Roadmap and State record the same ordered milestones:

1. architecture and State consistency repair;
2. final controlled Word Alignment decision;
3. Canonical Evidence Schema v1;
4. Word Timeline MVP on one controlled source;
5. parallel Knowledge Slice and Topic baseline/survey tracks;
6. Global Seminar Structure POC;
7. Topic Engine candidate freeze;
8. topic-agnostic Dataset D repair/preparation;
9. Dataset D blind evaluation;
10. define/assess `TOPIC AUTOMATION USABLE`;
11. expand Knowledge Engine;
12. multi-seminar Knowledge MVP;
13. later cross-seminar and product outputs.

State marks step 1 complete and step 2 next. Obsolete State actions for manual
Dataset C Gold, frozen A/B/C validation, and waiting for Topic Engine stability
before Obsidian have been removed.

## Contradictions repaired

- Dataset C changed from `candidates_prepared_needs_review` and 0 Gold to complete,
  6/6 Gold, 24 topics, frozen/closed.
- Dataset D/E/F now have explicit machine-readable roles and firewalls.
- Word Alignment now records the prior additional-experiment verdict.
- Obsidian MVP changed from blocked by `topic_engine.stable` to blocked only by the
  minimum Canonical Evidence foundation needed by the vertical slice.
- Architecture checkpoint changed from pending Dataset C to accepted
  Evidence-First Parallel Development.
- The current stage and next actions now match the Roadmap.

## Lightweight consistency-check proposal

Do not add a governance subsystem now. A later small CI check can:

1. validate `SEMINARTEXT_4_STATE.json` against a compact JSON Schema;
2. require the same `policy_checkpoint` token in Roadmap and State;
3. assert invariant dataset roles for C/D/E;
4. compare an ordered milestone identifier list generated from one small policy
   source.

For this Issue, JSON parsing plus explicit invariant checks are sufficient and
are reported in the PR. State should eventually be validated/generated rather
than independently edited without review.
