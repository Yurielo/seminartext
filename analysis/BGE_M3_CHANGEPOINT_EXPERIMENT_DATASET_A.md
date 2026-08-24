# BGE-M3 Change-Point Experiment - Dataset A

Issue: #9

Status: controlled experimental baseline only. This does not change production
Topic Engine behavior.

## Conclusion

Result: `not promising`.

This repo-contained bge-m3 + deterministic change-point baseline has controlled
precision, but recall is too low and it does not improve the middle/late recall
profile that motivated the experiment.

At tolerance +/-2:

| Engine | P | R | F1 | Predicted topics |
|---|---:|---:|---:|---:|
| Frozen Ollama semantic baseline | 0.500 | 0.458 | 0.478 | 44 |
| Issue #7 sliding sub-window | 0.383 | 0.479 | 0.426 | 60 |
| BGE-M3 change-point experiment | 0.577 | 0.312 | 0.405 | 26 |

Evidence: the bge-m3 experiment improves precision over both comparison
targets, but it misses too many Gold boundaries. Middle recall is unchanged
against the frozen baseline, and late recall is unchanged against both
comparison targets.

## Predeclared Configuration

The experiment used one small baseline configuration. No broad parameter search
was performed on Dataset A.

| Parameter | Value |
|---|---|
| Embedding model | `bge-m3:latest` |
| Embedding provider | Ollama `/api/embed` |
| Embedding dimensions observed | 1024 |
| Semantic block size | 15 seconds |
| Change signal | `1 - cosine(mean(left_context), mean(right_context))` |
| Left/right context | 2 blocks each |
| Smoothing | fixed 3-point kernel `[0.25, 0.5, 0.25]` |
| Change-point method | deterministic local peak selection |
| Threshold | median smoothed score * 1.15 |
| Minimum gap | 3 blocks |
| Maximum boundaries | 11 per benchmark window |
| Segment-ID min gap | 3 IDs |

The helper is:

`analysis/experiments/bge_m3_changepoint_topic_engine.py`

Run command:

```bash
python3 analysis/experiments/bge_m3_changepoint_topic_engine.py
```

Result JSON:

`/Users/yurielokhin/Documents/seminartext_projects/Стресс код/analysis/benchmark/results/bge_m3_changepoint_experiment_20260824T183855Z.json`

## Implementation Assumptions

- The roadmap names bge-m3 + 15-second semantic blocks + ruptures as the
  prospective path, but `numpy`, `scipy`, `sklearn`, and `ruptures` were not
  available in the local Python environment.
- To keep the experiment repo-contained and dependency-light, this baseline uses
  a deterministic peak-based change-point detector implemented with Python
  stdlib rather than importing `ruptures`.
- The method is intentionally simple and inspectable: it embeds semantic blocks,
  computes adjacent left/right semantic distance, smooths the signal, selects
  local maxima above a robust threshold, and maps selected block boundaries back
  to transcript segment IDs.
- This is not silently falling back to Ollama semantic boundary generation:
  Ollama is used only for bge-m3 embeddings, not for boundary prompts.

## Runtime And Dependencies

Evidence from the run:

| Metric | Value |
|---|---:|
| Runtime | 5.8 seconds |
| Embeddings | 280 |
| Ollama embedding batches | 12 |
| `prompt_eval_count` | 11,660 |

Dependency/model requirements:

- Ollama running locally.
- `bge-m3:latest` installed in Ollama.
- Python 3 stdlib only for the helper.

## Safety Evidence

| Artifact | SHA-256 |
|---|---|
| `topic_benchmark.json` | `3e0e8ae09ca3523c93a70ebf57fda0aadd331e8f06216647791ba4fa9a55f803` |
| `/Users/yurielokhin/bin/seminartext_topics.py` | `d8a14e83b877024c3e016a33e594af17d512741a77735ff3d8c7d1262628c8db` |

Safety confirmations:

- Gold benchmark data was not modified.
- Production Topic Engine was not modified.
- Production `seminartext` CLI was not modified.
- No model/prompt/threshold/smoothing/change-point logic was changed in
  production.

## Aggregate Metrics

### Tolerance 0

| Engine | P | R | F1 | Pred | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| BGE-M3 change-point | 0.346 | 0.188 | 0.243 | 26 | 9 | 17 | 39 |

### Tolerance 1

| Engine | P | R | F1 | Pred | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| BGE-M3 change-point | 0.577 | 0.312 | 0.405 | 26 | 15 | 11 | 33 |

### Tolerance 2

| Engine | P | R | F1 | Pred | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| BGE-M3 change-point | 0.577 | 0.312 | 0.405 | 26 | 15 | 11 | 33 |

Evidence: tolerance 1 and tolerance 2 are identical in this run, which means
matched bge-m3 change points generally fall within +/-1 when they match at all.
The weakness is selection coverage, not boundary offset size.

## Early / Middle / Late Recall

### Tolerance 2

| Engine | Early | Middle | Late |
|---|---:|---:|---:|
| Frozen Ollama semantic baseline | 0.800 | 0.250 | 0.167 |
| Issue #7 sliding sub-window | 0.500 | 0.688 | 0.167 |
| BGE-M3 change-point | 0.450 | 0.250 | 0.167 |

Evidence: this bge-m3 configuration does not improve middle recall over the
frozen baseline and does not improve late recall over either comparison target.

### All Tolerances

| Tolerance | Early | Middle | Late |
|---:|---:|---:|---:|
| 0 | 0.350 | 0.062 | 0.083 |
| 1 | 0.450 | 0.250 | 0.167 |
| 2 | 0.450 | 0.250 | 0.167 |

## Per-Window Metrics At Tolerance 2

| Window | P | R | F1 | Pred | Gold |
|---|---:|---:|---:|---:|---:|
| `video_001_window_01` | 0.500 | 0.286 | 0.364 | 4 | 7 |
| `video_001_window_04` | 0.667 | 0.250 | 0.364 | 3 | 8 |
| `video_001_window_08` | 0.600 | 0.333 | 0.429 | 5 | 9 |
| `video_001_window_12` | 0.500 | 0.222 | 0.308 | 4 | 9 |
| `video_001_window_17` | 0.800 | 0.444 | 0.571 | 5 | 9 |
| `video_001_window_22` | 0.400 | 0.333 | 0.364 | 5 | 6 |

Per-window predicted boundaries:

| Window | Predicted boundaries | False negatives at +/-2 |
|---|---|---|
| `video_001_window_01` | `1, 49, 60, 103` | `16, 38, 54, 86, 100` |
| `video_001_window_04` | `288, 306, 337` | `302, 310, 313, 321, 331, 351` |
| `video_001_window_08` | `656, 659, 689, 701, 707` | `666, 684, 721, 733, 739, 752` |
| `video_001_window_12` | `1073, 1115, 1159, 1165` | `1084, 1101, 1110, 1128, 1135, 1145, 1149` |
| `video_001_window_17` | `1606, 1609, 1618, 1695, 1704` | `1640, 1653, 1666, 1670, 1675` |
| `video_001_window_22` | `2044, 2099, 2124, 2142, 2154` | `2062, 2068, 2075, 2130` |

Evidence: the detector is conservative, predicting 26 boundaries for 48 Gold
topics. This reduces false positives but misses many boundaries in every window.

## Signal Observations

Top smoothed signal peaks often occur near large transcript shifts or end-window
changes:

| Window | Block count | Top signal peaks `(block_index, score)` |
|---|---:|---|
| `video_001_window_01` | 48 | `(47, 0.4104), (1, 0.3910), (46, 0.3882)` |
| `video_001_window_04` | 42 | `(27, 0.3804), (28, 0.3649), (10, 0.3632)` |
| `video_001_window_08` | 46 | `(24, 0.3710), (23, 0.3603), (15, 0.3505)` |
| `video_001_window_12` | 48 | `(20, 0.3615), (41, 0.3571), (1, 0.3547)` |
| `video_001_window_17` | 48 | `(46, 0.3656), (5, 0.3595), (1, 0.3458)` |
| `video_001_window_22` | 48 | `(47, 0.4347), (24, 0.3779), (46, 0.3712)` |

Hypothesis: the pure adjacent embedding-distance signal highlights large local
semantic changes, but many Gold boundaries are discourse/protocol granularity
changes rather than large vector-space jumps. This explains the higher
precision/lower recall pattern.

## Limitations

- This is not a faithful `ruptures` PELT/Binseg implementation because the local
  Python environment lacked `ruptures` and numeric dependencies.
- The detector is a deterministic peak baseline, not a learned or tuned
  candidate-count scorer.
- Only one predeclared configuration was evaluated.
- Dataset A remains useful for controlled comparison, but it must not be used to
  choose production parameters without Dataset B validation.

## Recommendation

Do not proceed to Dataset B with this exact peak-only bge-m3 change-point
baseline.

The bge-m3 embedding signal still looks useful as a high-precision feature, but
the next architecture should not rely on simple local peak selection alone. A
more promising next controlled experiment would combine bge-m3 candidate
generation with a separate count/scoring stage, while keeping parameters frozen
before Dataset B.
