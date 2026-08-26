# Dataset E Topic Engine evidence exclusion

Date: 2026-08-26  
Authority: Product Owner decision, Issue #34  
Status: ACTIVE / source-of-truth policy

## Decision

Dataset E — «Нумеролог» is **EXCLUDED FROM TOPIC ENGINE EVIDENCE**.

The source contains another person's voice/speech rather than the Product Owner's
own seminar/audio. Speaker-dependent speech rate, pauses, phrasing, discourse
structure, and ASR behavior would introduce an uncontrolled variable into
conclusions about the target SeminarText corpus.

## Prohibited uses

Dataset E must not be used for:

- Topic Engine Gold creation;
- Topic Engine parameter tuning;
- Topic Engine architecture selection;
- model or configuration comparison;
- `TOPIC SEGMENTATION STABLE` acceptance evidence;
- performance conclusions about the Product Owner's seminar corpus;
- Word Timeline / Alignment candidate selection or validation.

Gold E is not planned.

## Permitted historical use

Existing Dataset E artifacts, including the deterministic 189 → 704
topic-agnostic resegmentation prototype, may be retained as **historical
transcript-segmentation engineering evidence only**.

They may support the general architectural lesson that arbitrary SRT cue
granularity is unsuitable as the canonical coordinate system. They must not be
counted, aggregated, or cited as Topic Engine benchmark evidence.

Historical artifacts are preserved rather than deleted or rewritten. Existing
labels such as `READY FOR GOLD`, where present in historical records, are
superseded for all current and future Topic Engine work by this policy.

## Dataset policy after Issue #34

| Dataset | Current role | Policy |
|---|---|---|
| A | DEVELOPMENT / CALIBRATION | Existing Gold remains unchanged. |
| B | DEVELOPMENT / ERROR-ANALYSIS HISTORY | Existing Gold remains unchanged. |
| C | CLOSED FROZEN EVIDENCE | No tuning or architecture selection; existing Gold remains unchanged. |
| D | LOCKED TEST | Use only after source repair and without development leakage. |
| E | EXCLUDED FROM TOPIC ENGINE EVIDENCE | Historical transcript-segmentation engineering evidence only. |
| F | Potential DEVELOPMENT source | Requires source/ASR quality repair and target-corpus confirmation. |

## Downstream rules

1. Near-term plans must not contain Gold E creation or Dataset E timing upgrades
   for Topic Engine evaluation.
2. Word Alignment bake-offs must use controlled target-corpus Russian audio, not
   Dataset E.
3. Development evidence expansion after A/B must use eligible target-corpus
   sources; Dataset F remains only a potential source until repaired.
4. Dataset D remains isolated as LOCKED TEST.
5. Reports and experiment manifests must identify Dataset E as excluded whenever
   historical artifacts are mentioned.

## Superseded roadmap wording

This policy supersedes earlier current-state wording that described:

- Dataset E/F jointly as `DEVELOPMENT`;
- Dataset E resegmentation as `READY FOR GOLD`;
- Gold E as a planned post-alignment task;
- Dataset E timing upgrade as a prerequisite for Topic Engine development;
- Dataset E as eligible cross-dataset acceptance evidence.

The numerical and reproducibility facts of the historical resegmentation
prototype are not revoked; only their admissibility as Topic Engine evidence is
revoked.
