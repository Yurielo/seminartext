# Sliding Sub-Window Topic Engine Experiment - Dataset A

Issue: #7
Status: controlled experiment only. This is not a production Topic Engine
change.

## Conclusion

Result: `inconclusive`.

Evidence supports part of the position-effect hypothesis: middle-third recall at
tolerance +/-2 improved from 0.250 to 0.688. However, late-third recall did not
improve: it stayed at 0.167. Sliding sub-windows also increased predicted
boundary count from 44 to 60 and reduced aggregate precision from 0.500 to
0.383, lowering aggregate F1 from 0.478 to 0.426.

Interpretation: smaller overlapping windows can recover transitions that the
full-window engine misses in the middle of a 12-minute window, but this single
predeclared setup does not solve late-window under-detection and introduces too
many false positives. It should not be promoted to production.

## Experiment Design

The experiment used one predeclared parameter set, chosen to test the
position/context-budget hypothesis rather than to optimize Dataset A:

| Parameter | Value |
|---|---:|
| Sub-window duration | 300 seconds |
| Overlap | 25% |
| Merge radius | 2 segment IDs |
| Detail | `auto` |
| Model | `gemma3:4b` |

Synthetic sub-window anchor policy: the current Topic Engine always returns the
first segment of its input window. For sliding sub-windows, those local first
segments are coverage anchors, not necessarily semantic boundaries. The helper
drops a sub-window first boundary unless it is also the first segment of the
original benchmark window, then merges nearby predictions deterministically.

The helper is:

`analysis/experiments/sliding_subwindow_topic_engine.py`

The run used:

```bash
python3 analysis/experiments/sliding_subwindow_topic_engine.py \
  --subwindow-seconds 300 \
  --overlap-ratio 0.25 \
  --merge-radius 2
```

Result JSON:

`/Users/yurielokhin/Documents/seminartext_projects/Стресс код/analysis/benchmark/results/sliding_subwindow_experiment_20260824T182103Z.json`

## Safety

- Production `seminartext` CLI was not changed.
- Production Topic Engine behavior was not changed.
- Gold benchmark data was not changed.
- The experiment imports and calls the existing
  `analyze_window_boundaries()` entrypoint.
- No parameter search was performed.

Evidence:

| Artifact | SHA-256 |
|---|---|
| `topic_benchmark.json` | `3e0e8ae09ca3523c93a70ebf57fda0aadd331e8f06216647791ba4fa9a55f803` |
| `/Users/yurielokhin/bin/seminartext_topics.py` | `d8a14e83b877024c3e016a33e594af17d512741a77735ff3d8c7d1262628c8db` |

## Aggregate Metrics

### Tolerance 0

| Engine | P | R | F1 | Predicted | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline full-window | 0.205 | 0.188 | 0.196 | 44 | 9 | 35 | 39 |
| Sliding sub-window | 0.200 | 0.250 | 0.222 | 60 | 12 | 48 | 36 |

### Tolerance 1

| Engine | P | R | F1 | Predicted | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline full-window | 0.341 | 0.312 | 0.326 | 44 | 15 | 29 | 33 |
| Sliding sub-window | 0.317 | 0.396 | 0.352 | 60 | 19 | 41 | 29 |

### Tolerance 2

| Engine | P | R | F1 | Predicted | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline full-window | 0.500 | 0.458 | 0.478 | 44 | 22 | 22 | 26 |
| Sliding sub-window | 0.383 | 0.479 | 0.426 | 60 | 23 | 37 | 25 |

Evidence: sliding adds only one true positive at tolerance +/-2 while adding 15
false positives.

## Recall By Window Position

### Tolerance 2

| Engine | Early recall | Middle recall | Late recall |
|---|---:|---:|---:|
| Baseline full-window | 0.800 | 0.250 | 0.167 |
| Sliding sub-window | 0.500 | 0.688 | 0.167 |

Evidence: the middle third improves by +0.438 absolute recall, but early recall
drops by -0.300 and late recall is unchanged.

### Tolerance 0

| Engine | Early recall | Middle recall | Late recall |
|---|---:|---:|---:|
| Baseline full-window | 0.400 | 0.000 | 0.083 |
| Sliding sub-window | 0.450 | 0.188 | 0.000 |

### Tolerance 1

| Engine | Early recall | Middle recall | Late recall |
|---|---:|---:|---:|
| Baseline full-window | 0.650 | 0.062 | 0.083 |
| Sliding sub-window | 0.500 | 0.438 | 0.167 |

## Per-Window Metrics At Tolerance 2

| Window | Engine | P | R | F1 | Pred | Gold |
|---|---|---:|---:|---:|---:|---:|
| `video_001_window_01` | Baseline | 0.375 | 0.429 | 0.400 | 8 | 7 |
| `video_001_window_01` | Sliding | 0.375 | 0.429 | 0.400 | 8 | 7 |
| `video_001_window_04` | Baseline | 0.625 | 0.625 | 0.625 | 8 | 8 |
| `video_001_window_04` | Sliding | 0.500 | 0.625 | 0.556 | 10 | 8 |
| `video_001_window_08` | Baseline | 0.625 | 0.556 | 0.588 | 8 | 9 |
| `video_001_window_08` | Sliding | 0.375 | 0.333 | 0.353 | 8 | 9 |
| `video_001_window_12` | Baseline | 0.500 | 0.444 | 0.471 | 8 | 9 |
| `video_001_window_12` | Sliding | 0.417 | 0.556 | 0.476 | 12 | 9 |
| `video_001_window_17` | Baseline | 0.571 | 0.444 | 0.500 | 7 | 9 |
| `video_001_window_17` | Sliding | 0.429 | 0.667 | 0.522 | 14 | 9 |
| `video_001_window_22` | Baseline | 0.200 | 0.167 | 0.182 | 5 | 6 |
| `video_001_window_22` | Sliding | 0.125 | 0.167 | 0.143 | 8 | 6 |

Best evidence for the hypothesis: `window_17` recall improves from 0.444 to
0.667, and `window_12` recall improves from 0.444 to 0.556.

Counter-evidence: `window_08` degrades sharply, `window_22` remains weak, and
the strongest baseline window (`window_04`) loses precision.

## Duplicate And Merge Behavior

| Window | Sub-windows | Raw predictions after anchor drop | Duplicates before merge | Synthetic anchors dropped | Duplicates after merge |
|---|---:|---:|---:|---:|---:|
| `video_001_window_01` | 4 | 9 | 1 | 3 | 0 |
| `video_001_window_04` | 4 | 11 | 1 | 3 | 0 |
| `video_001_window_08` | 4 | 10 | 2 | 3 | 0 |
| `video_001_window_12` | 4 | 14 | 2 | 3 | 0 |
| `video_001_window_17` | 4 | 16 | 2 | 3 | 0 |
| `video_001_window_22` | 4 | 9 | 1 | 3 | 0 |
| **Total** | **24** | **69** | **9** | **18** | **0** |

Evidence: overlap created duplicate nearby predictions, but the deterministic
merge radius handled them. The main issue after merge is not duplicate
boundaries; it is new false positives from sub-window-local semantic decisions.

## Runtime And Model Calls

| Engine | Model calls | Runtime |
|---|---:|---:|
| Baseline full-window | 6 | 89.2 seconds |
| Sliding sub-window | 24 | 206.8 seconds |

The sliding helper used 4x as many model calls and about 2.3x runtime in this
run. Runtime did not scale linearly because sub-window prompts are shorter.

## Evidence vs Hypothesis

Evidence:

- Baseline tolerance +/-2 reproduces the frozen result:
  P 0.500 / R 0.458 / F1 0.478.
- Sliding tolerance +/-2 gives:
  P 0.383 / R 0.479 / F1 0.426.
- Middle recall improves materially:
  0.250 -> 0.688.
- Late recall does not improve:
  0.167 -> 0.167.
- Predicted topic count increases:
  44 -> 60.
- False positives increase:
  22 -> 37.

Hypothesis supported:

- Some middle-window misses are likely related to full-window context or
  position effects.

Hypothesis not supported:

- This setup does not show that sliding sub-windows fix late-window misses.
- This setup does not show a viable production improvement, because precision
  drops and aggregate F1 falls.

## Next Experiment Recommendation

Do not promote sliding sub-windows to production.

Recommended next controlled experiment: keep the full-window baseline and test a
recall-first candidate generator with a separate precision-oriented merge/filter
stage. The filter should explicitly classify local examples, transcript
artifacts, sign-offs, and procedural substeps, because this run shows that
shorter context increases recall but creates too many local-boundary false
positives.

Guardrails:

- Keep Dataset A frozen.
- Do not tune Topic Engine production behavior.
- Do not select parameters by maximizing Dataset A F1.
- If a candidate/filter architecture looks promising, validate the architecture
on Dataset B before production promotion.
