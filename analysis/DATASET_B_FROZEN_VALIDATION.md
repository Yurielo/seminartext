# Dataset B Frozen Validation

## Status

- Dataset B Gold is complete: 6/6 cases.
- Total Gold topics: 34.
- Manual Gold labels are recorded from GitHub Issue #15 authoritative Product Owner labels.
- Segments 1409-1411 are documented as a transcript glitch and are not a Gold topic.
- Dataset A Gold and production Topic Engine logic were not modified.
- No Dataset B tuning was performed before these frozen runs.

## Result Files

| File | Contents |
| --- | --- |
| `analysis/dataset_b/results/dataset_b_sliding_subwindow_frozen.json` | sliding_and_baseline raw result JSON |
| `analysis/dataset_b/results/dataset_b_bge_m3_changepoint_frozen.json` | bge_m3_local_peak raw result JSON |
| `analysis/dataset_b/results/dataset_b_bge_m3_ruptures_frozen.json` | bge_m3_ruptures_pelt raw result JSON |
| `analysis/dataset_b/results/dataset_b_frozen_validation_summary.json` | Combined machine-readable summary |

## Aggregate Metrics

### Frozen Ollama semantic baseline

| Tol | P | R | F1 | Pred | TP | FP | FN |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.179 | 0.206 | 0.192 | 39 | 7 | 32 | 27 |
| 1 | 0.308 | 0.353 | 0.329 | 39 | 12 | 27 | 22 |
| 2 | 0.333 | 0.382 | 0.356 | 39 | 13 | 26 | 21 |

Runtime/model calls: `runtime_seconds`=83.277, `model_calls`=6.

### Issue #7 sliding sub-window

| Tol | P | R | F1 | Pred | TP | FP | FN |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.228 | 0.382 | 0.286 | 57 | 13 | 44 | 21 |
| 1 | 0.351 | 0.588 | 0.440 | 57 | 20 | 37 | 14 |
| 2 | 0.368 | 0.618 | 0.462 | 57 | 21 | 36 | 13 |

Runtime/model calls: `runtime_seconds`=270.741, `model_calls`=24.

### Issue #9 bge-m3 local peak

| Tol | P | R | F1 | Pred | TP | FP | FN |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.385 | 0.294 | 0.333 | 26 | 10 | 16 | 24 |
| 1 | 0.577 | 0.441 | 0.500 | 26 | 15 | 11 | 19 |
| 2 | 0.615 | 0.471 | 0.533 | 26 | 16 | 10 | 18 |

Runtime/model calls: `runtime_seconds`=11.611, `embedding_count`=277, `embedding_batches`=12.

### Issue #11 bge-m3 + ruptures.Pelt

| Tol | P | R | F1 | Pred | TP | FP | FN |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.133 | 0.235 | 0.170 | 60 | 8 | 52 | 26 |
| 1 | 0.267 | 0.471 | 0.340 | 60 | 16 | 44 | 18 |
| 2 | 0.350 | 0.618 | 0.447 | 60 | 21 | 39 | 13 |

Runtime/model calls: `runtime_seconds`=8.866, `embedding_count`=277, `embedding_batches`=12.

## Recall By Window Position

Tolerance +/-2.

| Engine | Early | Middle | Late |
| --- | ---: | ---: | ---: |
| Frozen Ollama semantic baseline | 0.533 (8/15) | 0.364 (4/11) | 0.125 (1/8) |
| Issue #7 sliding sub-window | 0.667 (10/15) | 0.727 (8/11) | 0.375 (3/8) |
| Issue #9 bge-m3 local peak | 0.600 (9/15) | 0.545 (6/11) | 0.125 (1/8) |
| Issue #11 bge-m3 + ruptures.Pelt | 0.667 (10/15) | 0.545 (6/11) | 0.625 (5/8) |

## Per-Window Metrics

All rows include precision/recall/F1 for each tolerance.

### Frozen Ollama semantic baseline

| Tol | Case | P | R | F1 | Pred | Gold | TP | FP | FN |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | `dataset_b_video_001_window_01` | 0.143 | 0.250 | 0.182 | 7 | 4 | 1 | 6 | 3 |
| 0 | `dataset_b_video_001_window_06` | 0.286 | 0.333 | 0.308 | 7 | 6 | 2 | 5 | 4 |
| 0 | `dataset_b_video_001_window_11` | 1.000 | 0.167 | 0.286 | 1 | 6 | 1 | 0 | 5 |
| 0 | `dataset_b_video_001_window_15` | 0.083 | 0.200 | 0.118 | 12 | 5 | 1 | 11 | 4 |
| 0 | `dataset_b_video_001_window_20` | 0.200 | 0.200 | 0.200 | 5 | 5 | 1 | 4 | 4 |
| 0 | `dataset_b_video_001_window_25` | 0.143 | 0.125 | 0.133 | 7 | 8 | 1 | 6 | 7 |
| 1 | `dataset_b_video_001_window_01` | 0.143 | 0.250 | 0.182 | 7 | 4 | 1 | 6 | 3 |
| 1 | `dataset_b_video_001_window_06` | 0.286 | 0.333 | 0.308 | 7 | 6 | 2 | 5 | 4 |
| 1 | `dataset_b_video_001_window_11` | 1.000 | 0.167 | 0.286 | 1 | 6 | 1 | 0 | 5 |
| 1 | `dataset_b_video_001_window_15` | 0.250 | 0.600 | 0.353 | 12 | 5 | 3 | 9 | 2 |
| 1 | `dataset_b_video_001_window_20` | 0.200 | 0.200 | 0.200 | 5 | 5 | 1 | 4 | 4 |
| 1 | `dataset_b_video_001_window_25` | 0.571 | 0.500 | 0.533 | 7 | 8 | 4 | 3 | 4 |
| 2 | `dataset_b_video_001_window_01` | 0.143 | 0.250 | 0.182 | 7 | 4 | 1 | 6 | 3 |
| 2 | `dataset_b_video_001_window_06` | 0.286 | 0.333 | 0.308 | 7 | 6 | 2 | 5 | 4 |
| 2 | `dataset_b_video_001_window_11` | 1.000 | 0.167 | 0.286 | 1 | 6 | 1 | 0 | 5 |
| 2 | `dataset_b_video_001_window_15` | 0.250 | 0.600 | 0.353 | 12 | 5 | 3 | 9 | 2 |
| 2 | `dataset_b_video_001_window_20` | 0.400 | 0.400 | 0.400 | 5 | 5 | 2 | 3 | 3 |
| 2 | `dataset_b_video_001_window_25` | 0.571 | 0.500 | 0.533 | 7 | 8 | 4 | 3 | 4 |

### Issue #7 sliding sub-window

| Tol | Case | P | R | F1 | Pred | Gold | TP | FP | FN |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | `dataset_b_video_001_window_01` | 0.111 | 0.250 | 0.154 | 9 | 4 | 1 | 8 | 3 |
| 0 | `dataset_b_video_001_window_06` | 0.222 | 0.333 | 0.267 | 9 | 6 | 2 | 7 | 4 |
| 0 | `dataset_b_video_001_window_11` | 0.200 | 0.333 | 0.250 | 10 | 6 | 2 | 8 | 4 |
| 0 | `dataset_b_video_001_window_15` | 0.091 | 0.200 | 0.125 | 11 | 5 | 1 | 10 | 4 |
| 0 | `dataset_b_video_001_window_20` | 0.400 | 0.800 | 0.533 | 10 | 5 | 4 | 6 | 1 |
| 0 | `dataset_b_video_001_window_25` | 0.375 | 0.375 | 0.375 | 8 | 8 | 3 | 5 | 5 |
| 1 | `dataset_b_video_001_window_01` | 0.111 | 0.250 | 0.154 | 9 | 4 | 1 | 8 | 3 |
| 1 | `dataset_b_video_001_window_06` | 0.333 | 0.500 | 0.400 | 9 | 6 | 3 | 6 | 3 |
| 1 | `dataset_b_video_001_window_11` | 0.400 | 0.667 | 0.500 | 10 | 6 | 4 | 6 | 2 |
| 1 | `dataset_b_video_001_window_15` | 0.273 | 0.600 | 0.375 | 11 | 5 | 3 | 8 | 2 |
| 1 | `dataset_b_video_001_window_20` | 0.400 | 0.800 | 0.533 | 10 | 5 | 4 | 6 | 1 |
| 1 | `dataset_b_video_001_window_25` | 0.625 | 0.625 | 0.625 | 8 | 8 | 5 | 3 | 3 |
| 2 | `dataset_b_video_001_window_01` | 0.111 | 0.250 | 0.154 | 9 | 4 | 1 | 8 | 3 |
| 2 | `dataset_b_video_001_window_06` | 0.333 | 0.500 | 0.400 | 9 | 6 | 3 | 6 | 3 |
| 2 | `dataset_b_video_001_window_11` | 0.400 | 0.667 | 0.500 | 10 | 6 | 4 | 6 | 2 |
| 2 | `dataset_b_video_001_window_15` | 0.364 | 0.800 | 0.500 | 11 | 5 | 4 | 7 | 1 |
| 2 | `dataset_b_video_001_window_20` | 0.400 | 0.800 | 0.533 | 10 | 5 | 4 | 6 | 1 |
| 2 | `dataset_b_video_001_window_25` | 0.625 | 0.625 | 0.625 | 8 | 8 | 5 | 3 | 3 |

### Issue #9 bge-m3 local peak

| Tol | Case | P | R | F1 | Pred | Gold | TP | FP | FN |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | `dataset_b_video_001_window_01` | 0.250 | 0.250 | 0.250 | 4 | 4 | 1 | 3 | 3 |
| 0 | `dataset_b_video_001_window_06` | 1.000 | 0.333 | 0.500 | 2 | 6 | 2 | 0 | 4 |
| 0 | `dataset_b_video_001_window_11` | 0.500 | 0.333 | 0.400 | 4 | 6 | 2 | 2 | 4 |
| 0 | `dataset_b_video_001_window_15` | 0.400 | 0.400 | 0.400 | 5 | 5 | 2 | 3 | 3 |
| 0 | `dataset_b_video_001_window_20` | 0.200 | 0.200 | 0.200 | 5 | 5 | 1 | 4 | 4 |
| 0 | `dataset_b_video_001_window_25` | 0.333 | 0.250 | 0.286 | 6 | 8 | 2 | 4 | 6 |
| 1 | `dataset_b_video_001_window_01` | 0.500 | 0.500 | 0.500 | 4 | 4 | 2 | 2 | 2 |
| 1 | `dataset_b_video_001_window_06` | 1.000 | 0.333 | 0.500 | 2 | 6 | 2 | 0 | 4 |
| 1 | `dataset_b_video_001_window_11` | 0.500 | 0.333 | 0.400 | 4 | 6 | 2 | 2 | 4 |
| 1 | `dataset_b_video_001_window_15` | 0.600 | 0.600 | 0.600 | 5 | 5 | 3 | 2 | 2 |
| 1 | `dataset_b_video_001_window_20` | 0.400 | 0.400 | 0.400 | 5 | 5 | 2 | 3 | 3 |
| 1 | `dataset_b_video_001_window_25` | 0.667 | 0.500 | 0.571 | 6 | 8 | 4 | 2 | 4 |
| 2 | `dataset_b_video_001_window_01` | 0.500 | 0.500 | 0.500 | 4 | 4 | 2 | 2 | 2 |
| 2 | `dataset_b_video_001_window_06` | 1.000 | 0.333 | 0.500 | 2 | 6 | 2 | 0 | 4 |
| 2 | `dataset_b_video_001_window_11` | 0.500 | 0.333 | 0.400 | 4 | 6 | 2 | 2 | 4 |
| 2 | `dataset_b_video_001_window_15` | 0.800 | 0.800 | 0.800 | 5 | 5 | 4 | 1 | 1 |
| 2 | `dataset_b_video_001_window_20` | 0.400 | 0.400 | 0.400 | 5 | 5 | 2 | 3 | 3 |
| 2 | `dataset_b_video_001_window_25` | 0.667 | 0.500 | 0.571 | 6 | 8 | 4 | 2 | 4 |

### Issue #11 bge-m3 + ruptures.Pelt

| Tol | Case | P | R | F1 | Pred | Gold | TP | FP | FN |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | `dataset_b_video_001_window_01` | 0.200 | 0.500 | 0.286 | 10 | 4 | 2 | 8 | 2 |
| 0 | `dataset_b_video_001_window_06` | 0.143 | 0.167 | 0.154 | 7 | 6 | 1 | 6 | 5 |
| 0 | `dataset_b_video_001_window_11` | 0.125 | 0.167 | 0.143 | 8 | 6 | 1 | 7 | 5 |
| 0 | `dataset_b_video_001_window_15` | 0.083 | 0.200 | 0.118 | 12 | 5 | 1 | 11 | 4 |
| 0 | `dataset_b_video_001_window_20` | 0.083 | 0.200 | 0.118 | 12 | 5 | 1 | 11 | 4 |
| 0 | `dataset_b_video_001_window_25` | 0.182 | 0.250 | 0.211 | 11 | 8 | 2 | 9 | 6 |
| 1 | `dataset_b_video_001_window_01` | 0.300 | 0.750 | 0.429 | 10 | 4 | 3 | 7 | 1 |
| 1 | `dataset_b_video_001_window_06` | 0.571 | 0.667 | 0.615 | 7 | 6 | 4 | 3 | 2 |
| 1 | `dataset_b_video_001_window_11` | 0.125 | 0.167 | 0.143 | 8 | 6 | 1 | 7 | 5 |
| 1 | `dataset_b_video_001_window_15` | 0.250 | 0.600 | 0.353 | 12 | 5 | 3 | 9 | 2 |
| 1 | `dataset_b_video_001_window_20` | 0.250 | 0.600 | 0.353 | 12 | 5 | 3 | 9 | 2 |
| 1 | `dataset_b_video_001_window_25` | 0.182 | 0.250 | 0.211 | 11 | 8 | 2 | 9 | 6 |
| 2 | `dataset_b_video_001_window_01` | 0.300 | 0.750 | 0.429 | 10 | 4 | 3 | 7 | 1 |
| 2 | `dataset_b_video_001_window_06` | 0.571 | 0.667 | 0.615 | 7 | 6 | 4 | 3 | 2 |
| 2 | `dataset_b_video_001_window_11` | 0.250 | 0.333 | 0.286 | 8 | 6 | 2 | 6 | 4 |
| 2 | `dataset_b_video_001_window_15` | 0.417 | 1.000 | 0.588 | 12 | 5 | 5 | 7 | 0 |
| 2 | `dataset_b_video_001_window_20` | 0.333 | 0.800 | 0.471 | 12 | 5 | 4 | 8 | 1 |
| 2 | `dataset_b_video_001_window_25` | 0.273 | 0.375 | 0.316 | 11 | 8 | 3 | 8 | 5 |

## Dataset A vs Dataset B

Tolerance +/-2 comparison.

| Engine | A P | A R | A F1 | A Pred | B P | B R | B F1 | B Pred | ΔF1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Frozen Ollama semantic baseline | 0.500 | 0.458 | 0.478 | 44 | 0.333 | 0.382 | 0.356 | 39 | -0.122 |
| Issue #7 sliding sub-window | 0.383 | 0.479 | 0.426 | 60 | 0.368 | 0.618 | 0.462 | 57 | +0.036 |
| Issue #9 bge-m3 local peak | 0.577 | 0.312 | 0.405 | 26 | 0.615 | 0.471 | 0.533 | 26 | +0.128 |
| Issue #11 bge-m3 + ruptures.Pelt | 0.381 | 0.500 | 0.432 | 63 | 0.350 | 0.618 | 0.447 | 60 | +0.015 |

## Generalization Analysis

### Evidence

- The frozen Ollama baseline drops from Dataset A F1 0.478 to Dataset B F1 0.356 at tolerance +/-2.
- Sliding sub-windows improve on their Dataset A F1, from 0.426 to 0.462, and improve Dataset B recall to 0.618, but with 57 predicted topics and 36 false positives at tolerance +/-2.
- BGE-M3 local peak shows the strongest Dataset B aggregate F1, 0.533 at tolerance +/-2, with 26 predictions and the best precision, 0.615.
- BGE-M3 + ruptures.Pelt matches the best Dataset B recall, 0.618, but produces 60 predictions and precision falls to 0.350.
- Dataset B late recall differs sharply from Dataset A: PELT improves late recall to 0.625, sliding reaches 0.375, while baseline and local peak remain at 0.125.

### Interpretation

- The Dataset A baseline advantage does not generalize: its F1 and middle/late recall are weaker on Dataset B.
- The middle-recall benefit of sliding does generalize directionally, but at the cost of many extra false positives.
- Local-peak BGE-M3 appears more robust out-of-sample than it looked on Dataset A: it keeps the same prediction count and gains both precision and F1 on Dataset B.
- PELT generalizes as a recall-oriented architecture, especially for late-window boundaries, but its precision risk remains material.

### Limitations

- Dataset B has only six windows and 34 Gold topics; conclusions are evidence for next steps, not production proof.
- One baseline/sliding run emitted a transient invalid JSON warning from Ollama boundary detection but completed and produced full result JSON.
- The validation is frozen out-of-sample, so no parameters were adjusted after seeing Dataset B scores.

### Recommendation

Do not promote any architecture to production automatically.

Recommended next step: run one more independent Dataset C frozen validation before production decisions. Prioritize BGE-M3 local peak as the leading precision/F1 candidate, and keep BGE-M3 + PELT as a recall-oriented comparator. Sliding sub-windows remain useful as evidence for the position-effect hypothesis but are too false-positive-heavy for production promotion in this form.
