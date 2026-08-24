# Topic Engine Error Analysis - Dataset A

Issue: #5  
Scope: read-only diagnostic analysis of the current Topic Engine on Dataset A.

## Executive Summary

Dataset A contains 6 `gold_complete` windows and 48 Gold topics. The baseline
benchmark run at tolerance +/-2 produced:

| Metric | Value |
|---|---:|
| Gold topics | 48 |
| Predicted topics | 44 |
| True positives | 22 |
| False positives | 22 |
| False negatives | 26 |
| Boundary Precision | 0.500 |
| Boundary Recall | 0.458 |
| Boundary F1 | 0.478 |
| Mean boundary distance | 0.91 segments |
| Mean topic-count error | -0.67 |

Evidence: the analysis uses
`/Users/yurielokhin/Documents/seminartext_projects/Стресс код/analysis/benchmark/results/topic_benchmark_run_20260824T180821Z.json`,
with `topic_benchmark_run.json` updated to the same run. Tolerance was `2`.

Evidence: the benchmark source SHA-256 was
`3e0e8ae09ca3523c93a70ebf57fda0aadd331e8f06216647791ba4fa9a55f803`.

Evidence: the Topic Engine source path was
`/Users/yurielokhin/bin/seminartext_topics.py`, SHA-256
`d8a14e83b877024c3e016a33e594af17d512741a77735ff3d8c7d1262628c8db`.

Main finding: the engine usually identifies a plausible start-of-window boundary
and several early transitions, but often stops tracking later transitions inside
the same 12-minute window. Misses are concentrated in the middle and late parts
of windows: 4/20 early Gold boundaries missed, 12/16 middle Gold boundaries
missed, and 10/12 late Gold boundaries missed.

Hypothesis: the primary model boundary selection is biased toward a compact set
of early salient changes, while recursive refinement only repairs blocks that
are long enough. It does not reliably split dense, late, or conversational
sections when they contain multiple short semantic transitions.

## Current Engine Path

Evidence from `/Users/yurielokhin/bin/seminartext_topics.py`:

1. `analyze_window_boundaries(window, detail="auto", model="gemma3:4b")`
   calls `run_ollama_boundaries`.
2. `run_ollama_boundaries` asks the local model for a structured JSON object
   with `boundaries`, constrained to real segment IDs and `maxItems=12` for
   `auto`.
3. If the first segment ID is absent, it is inserted.
4. The boundaries are sorted and deduplicated.
5. Stage A2 filters out boundaries that violate `DETAIL[detail]["hard_min_sec"]`
   minimum temporal distance. For `auto`, `hard_min_sec=25`.
6. Stage A3 calls `refine_boundaries` to recursively split blocks longer than
   5 minutes in `auto`.
7. Stage A4 applies minimum-distance filtering again after refinement.

Evidence: no embedding stage, smoothing threshold, PELT/Binseg change-point
algorithm, or learned scorer is present in the current boundary path. The
dominant decision point is the model's structured semantic boundary judgment,
with deterministic min-duration filtering and overlong-block refinement around
it.

## Per-Window Table

| Window | Gold | Pred | TP | FP | FN | P | R | F1 | Main observed failure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `video_001_window_01` | 7 | 8 | 3 | 5 | 4 | 0.375 | 0.429 | 0.400 | Early over-splitting, then late misses during participant introduction and stress framing |
| `video_001_window_04` | 8 | 8 | 5 | 3 | 3 | 0.625 | 0.625 | 0.625 | Best window; early transitions captured, later learning-format transitions missed |
| `video_001_window_08` | 9 | 8 | 5 | 3 | 4 | 0.625 | 0.556 | 0.588 | Captures exercise/meridian transitions, misses later catalogue-like system levels |
| `video_001_window_12` | 9 | 8 | 4 | 4 | 5 | 0.500 | 0.444 | 0.471 | Over-splits protocol enumeration, misses demonstration setup and transition after lunch |
| `video_001_window_17` | 9 | 7 | 4 | 3 | 5 | 0.571 | 0.444 | 0.500 | Captures major correction milestones, misses several numbered protocol micro-steps |
| `video_001_window_22` | 6 | 5 | 1 | 4 | 5 | 0.200 | 0.167 | 0.182 | Weakest window; conversational Q&A and day-end wrap-up are mostly missed |

## Offset Analysis

Matched signed offsets are `predicted_id - gold_id`.

| Offset | Count |
|---:|---:|
| -2 | 6 |
| -1 | 2 |
| 0 | 9 |
| +1 | 4 |
| +2 | 1 |

Evidence: 9/22 matched boundaries are exact. The mean signed offset is -0.36
segments and the median signed offset is 0.

Interpretation: when the engine finds the right transition region, it usually
places the boundary acceptably within +/-2. The primary quality problem is not
large boundary displacement; it is boundary selection coverage. False negatives
outnumber successful late hits, especially after the first third of a window.

## False-Negative Analysis

### By Window

| Window | Missed Gold boundaries | Evidence-backed reading |
|---|---|---|
| `window_01` | 54, 60, 86, 100 | Misses the shift into participant self-introduction, Larisa's personal/professional context, stress as adaptation, and the handoff to the next participant. |
| `window_04` | 321, 331, 351 | Misses later training-format guidance, warning about high information volume, and the philosophical transition to well-being/health. |
| `window_08` | 706, 721, 739, 752 | Misses several later levels in a catalogue: energetic level/meridians, chakras/aura, primary elements/spiritual kinesiology, subtle planes/reflexes. |
| `window_12` | 1101, 1110, 1114, 1135, 1149 | Misses demonstration setup, practice-topic list, stress-on-learning explanation, decision to demonstrate before more teaching, and the post-lunch start. |
| `window_17` | 1640, 1653, 1675, 1695, 1703 | Misses several numbered protocol steps: return to present, retest, homework/recommendations, completion permission, and post-correction insights. |
| `window_22` | 2062, 2068, 2075, 2098, 2130 | Misses binary yes/no testing, stress-by-imagining method, work-stress Q&A, homework practice, and the first-day summary. |

### Correlations

Evidence:

- Median topic length for hits: 10.5 segments.
- Median topic length for misses: 13.0 segments.
- Short topics are not the only problem. Misses include short boundaries
  (`54 -> 60`, `1110 -> 1114`, `1666 -> 1670`) and long later topics
  (`2098 -> 2130`, `2130 -> end`).
- Position is the strongest observed correlation:
  - early third: 4 misses / 20 Gold boundaries;
  - middle third: 12 misses / 16 Gold boundaries;
  - late third: 10 misses / 12 Gold boundaries.

Hypothesis: the model allocates its boundary budget and attention to early
salient transitions in the prompt, then under-detects later transitions unless
they are very explicit or the refinement stage is forced by a long block.

Hypothesis: list-like teaching sections cause semantic compression. For example,
`window_08` describes many "levels" of the system. The engine treats multiple
Gold topics as one broader conceptual region after `733`.

Hypothesis: numbered protocol steps are semantically similar and repeated, so
the model often keeps them inside a single "correction protocol" block instead
of recognizing every Gold step boundary.

## False-Positive Analysis

| Window | False positives | Likely cause |
|---|---|---|
| `window_01` | 6, 12, 23, 29, 33 | Early over-splitting of introduction, course scope, attendance rules, breaks, and camera presence. These are real local subtopics but below Gold granularity. |
| `window_04` | 291, 294, 298 | Over-splitting of one story about successful remote/online work. The model marks narrative beats as topic starts. |
| `window_08` | 660, 671, 711 | One transcript artifact at 660 (`кем-то.`), one internal exercise instruction, and one mid-explanation meridian detail. |
| `window_12` | 1077, 1088, 1092, 1095 | Over-splitting of protocol overview into individual protocol actions before the Gold boundary at 1101. |
| `window_17` | 1611, 1623, 1706 | One fragment/artifact-like segment, one internal neuroplasticity explanation beat, and a late continuation of post-correction insights. |
| `window_22` | 2049, 2053, 2112, 2155 | Over-splitting inside the same practical example, one late homework-detail boundary, and a sign-off boundary. |

Evidence: many false positives are near a Gold boundary but outside tolerance:
`window_01` has false positives 6/12 around Gold 1/16 and 23/29/33 around Gold
16/38; `window_12` has false positives 1077/1088/1092/1095 while the Gold topic
is the whole protocol overview from 1084 to 1101.

Hypothesis: the model sees discourse markers and local examples as "real topic
starts" even when Gold labels treat them as substructure inside one topic.

## Boundary Classifications

### `video_001_window_01`

| Gold | Classification | Evidence |
|---:|---|---|
| 1 | exact hit | Opening and seminar introduction. |
| 16 | near hit +1 | Predicted 17, still inside group-format/rules transition. |
| 38 | near hit -1 | Predicted 37, immediately before "Second moment". |
| 54 | missed | Start of participant self-introductions. |
| 60 | missed | Larisa begins professional background. |
| 86 | missed | Teacher reframes stress as adaptation. |
| 100 | missed | Handoff from Larisa to Lyubov. |

False positives: 6/12 split seminar scope and method applicability; 23/29/33
split attendance and camera rules into local subtopics.

### `video_001_window_04`

| Gold | Classification | Evidence |
|---:|---|---|
| 288 | exact hit | Remote/online client-work story begins. |
| 302 | near hit +1 | COVID/restrictions increase online-work demand. |
| 306 | near hit +1 | Technical audio interruption. |
| 310 | exact hit | Return from technical pause and online-work effectiveness. |
| 313 | near hit +1 | Next learning task: correction protocol. |
| 321 | missed | How training will proceed, theory and questions. |
| 331 | missed | Large volume of new information. |
| 351 | missed | Well-being, health, happiness frame. |

False positives: 291/294/298 split one remote-work success narrative into
several narrative beats.

### `video_001_window_08`

| Gold | Classification | Evidence |
|---:|---|---|
| 656 | exact hit | Exercise completion continues. |
| 666 | exact hit | Front/back central meridians. |
| 684 | near hit -2 | Application of brain gym in life and study. |
| 688 | near hit -1 | Return to seminar and complex approach. |
| 706 | missed | Energetic level and meridians. |
| 721 | missed | Chakras, aura, energy flows. |
| 733 | exact hit | Structural level and brain structures. |
| 739 | missed | Primary elements and spiritual kinesiology. |
| 752 | missed | Subtle planes, resonance, reflexes. |

False positives: 660 appears to be a transcript fragment; 671 is an internal
instruction inside the meridian exercise; 711 is an internal definition of
meridians.

### `video_001_window_12`

| Gold | Classification | Evidence |
|---:|---|---|
| 1073 | exact hit | Protocol as the structure of work. |
| 1084 | near hit -2 | General correction protocol steps. |
| 1101 | missed | Setup for recorded demonstration session. |
| 1110 | missed | Themes for training corrections. |
| 1114 | missed | Stress on learning as a correction topic. |
| 1128 | near hit -2 | Trust in testing and online work. |
| 1135 | missed | Decision to run demonstration before further teaching. |
| 1145 | near hit +2 | Lunch break. |
| 1149 | missed | Post-lunch demonstration begins. |

False positives: 1077/1088/1092/1095 split the protocol overview into separate
procedural beats. These are meaningful local steps but below Gold topic
granularity.

### `video_001_window_17`

| Gold | Classification | Evidence |
|---:|---|---|
| 1606 | exact hit | Positive image formation. |
| 1619 | near hit -2 | Neuroplasticity explanation. |
| 1640 | missed | Return to the present with positive anchoring. |
| 1653 | missed | Retest of correction result. |
| 1666 | near hit -2 | Projection into future and topic retest. |
| 1670 | near hit -2 | Re-rating subjective discomfort. |
| 1675 | missed | Homework and recommendations. |
| 1695 | missed | Completion permission and accepting result. |
| 1703 | missed | Post-correction insights. |

False positives: 1611 is a fragment-like utterance; 1623 is an internal
neuroplasticity beat; 1706 is a continuation inside the post-correction insight
discussion.

### `video_001_window_22`

| Gold | Classification | Evidence |
|---:|---|---|
| 2044 | exact hit | Testing whether a concrete job choice is favorable. |
| 2062 | missed | Binary yes/no interpretation of muscle test. |
| 2068 | missed | Testing stress through mental representation. |
| 2075 | missed | Question about stress on work and labor activity. |
| 2098 | missed | End-of-day home practice instructions. |
| 2130 | missed | Summary of first training day. |

False positives: 2049/2053 are details inside the same job-choice example;
2112 is a homework-detail continuation; 2155 is only a sign-off.

## `window_04` vs `window_22`

Evidence: `window_04` is the strongest case with F1 0.625. It has clear
discourse discontinuities: remote-work narrative, pandemic demand, explicit
technical interruption, return from the pause, and transition into seminar plan.
The engine captured 5/8 Gold boundaries.

Evidence: `window_22` is the weakest case with F1 0.182. It has conversational
Q&A, repeated practical examples, multiple uses of the same muscle-testing
concept, end-of-day instructions, and a final summary. The engine captured only
the first Gold boundary.

Hypothesis: `window_04` is easier because several boundaries have strong lexical
or situational markers: "period of illness", a technical pause, "next task".
`window_22` is harder because multiple Gold topics share vocabulary around
testing, stress, work, examples, and practice. The model collapses them into
fewer broad themes and treats late homework/summary material as continuation.

## Failure-Mode Taxonomy

| Failure mode | Evidence | Likely engine stage |
|---|---|---|
| Early over-splitting | `window_01`, `window_04`, `window_12` create several false positives before the first half of the window. | Stage A1 model semantic judgment; it marks local narrative/procedural beats as topic starts. |
| Middle/late under-detection | Misses concentrate after the first third of the window. | Stage A1 likely omits later boundaries; Stage A3 only repairs overlong blocks and may not force enough splits in dense sections. |
| Catalogue compression | `window_08` misses several system-level topics after meridians. | Stage A1 treats a list of related system levels as one broader theme. |
| Protocol-step compression | `window_17` misses several numbered correction protocol steps. | Stage A1 sees repeated protocol vocabulary as continuation; Stage A3 may not split because blocks are not always long enough or because refinements remain broad. |
| Transcript artifact sensitivity | False positives at `660`, `1611`, and sign-off `2155`. | Stage A1 reacts to fragmentary or standalone utterances as potential boundaries. |
| Granularity mismatch | False positives are often meaningful local subtopics but not Gold topics. | Prompt/model calibration issue, not large offset error. |

## Architecture Options For Next Experiment

### Option 1: Two-pass recall-first candidate generation plus classifier

Expected benefit: raise recall by generating many candidate boundaries first,
then classifying/merging them against Gold-like granularity.

Risk: could increase false positives unless the second stage has strong
granularity rules.

### Option 2: Sliding sub-window analysis with merge

Expected benefit: reduce late-window attention decay by analyzing smaller
overlapping chunks, then merging nearby boundaries.

Risk: overlap stitching can create duplicates and boundary jitter.

### Option 3: Explicit discourse-marker and transition-type annotation

Expected benefit: separate true topic transitions from local examples,
technical pauses, sign-offs, and procedural substeps.

Risk: hand-authored transition categories may overfit Dataset A if validated
only on these six windows.

### Option 4: Post-hoc gap audit for suspicious long spans

Expected benefit: specifically targets the observed late under-detection by
asking the model to audit spans with few or no boundaries.

Risk: may still miss dense short topics if the audit prompt uses the same
semantic frame as the primary prompt.

## Recommended Next Experiment Only

Recommendation: run a controlled sliding sub-window experiment with overlap and
merge, without changing Gold data and without tuning on final Dataset A scores.

Why this next:

- Evidence points to position-related misses more strongly than short-topic
  misses.
- Smaller windows should directly test whether late-window misses are an
  attention/context-budget artifact.
- The experiment can be evaluated read-only against the same benchmark runner.

Guardrails:

- Freeze current production Topic Engine.
- Implement the experiment as a separate candidate engine or diagnostic script,
  not as a production replacement.
- Report precision/recall/F1 and a separate duplicate-boundary count.
- Do not select parameters solely to maximize Dataset A; use the result only to
  decide whether this architecture deserves Dataset B validation.

## Safety Confirmation

- Gold benchmark data was not modified.
- Topic Engine behavior was not modified.
- No prompt, model, threshold, smoothing, change-point logic, or benchmark label
  was changed.
- The only repository deliverable for Issue #5 is this diagnostic report.
