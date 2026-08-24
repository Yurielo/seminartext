# BGE-M3 Ruptures Experiment - Dataset A

Issue: #11

Status: controlled experiment only. This is not a production Topic Engine
change.

## Conclusion

Result: `inconclusive`.

The proper `ruptures` PELT experiment improves recall profile compared with the
Issue #9 local-peak bge-m3 baseline, and it improves middle/late recall compared
with the frozen Ollama semantic baseline. However, the precision drop is large
and aggregate F1 remains below the frozen baseline.

At tolerance +/-2:

| Engine | P | R | F1 | Predicted topics |
|---|---:|---:|---:|---:|
| Frozen Ollama semantic baseline | 0.500 | 0.458 | 0.478 | 44 |
| Issue #7 sliding sub-window | 0.383 | 0.479 | 0.426 | 60 |
| Issue #9 bge-m3 local peak | 0.577 | 0.312 | 0.405 | 26 |
| BGE-M3 + ruptures PELT | 0.381 | 0.500 | 0.432 | 63 |

Evidence: PELT increases recall to 0.500 and improves middle/late recall, but
it predicts 63 topics for 48 Gold topics and produces 39 false positives at
tolerance +/-2. This is not ready for Dataset B as-is, but it is not a clean
rejection of bge-m3 change-point features either.

## Environment

An isolated local venv was used:

`.venv-experiments`

The venv is not committed. Reproducible package pins are committed in
`requirements-experiments.txt`.

Dependency versions:

| Package | Version |
|---|---|
| `numpy` | 2.5.2 |
| `scipy` | 1.18.1 |
| `ruptures` | 1.1.9 |

Model/runtime requirements:

- Ollama running locally.
- `bge-m3:latest` installed in Ollama.
- Python venv with `requirements-experiments.txt`.

## Predeclared Configuration

One configuration was evaluated. No grid search was performed.

| Parameter | Value |
|---|---|
| Embedding model | `bge-m3:latest` |
| Embedding provider | Ollama `/api/embed` |
| Semantic block size | 15 seconds |
| Change signal | `1 - cosine(mean(left_context), mean(right_context))` |
| Left/right context | 2 blocks each |
| Smoothing | fixed 3-point kernel `[0.25, 0.5, 0.25]` |
| Change-point library | `ruptures==1.1.9` |
| Method | PELT |
| `ruptures` model | `rbf` |
| Penalty | 0.5 |
| `min_size` | 3 blocks |
| `jump` | 1 |
| Segment-ID min gap | 3 IDs |

Run command:

```bash
.venv-experiments/bin/python analysis/experiments/bge_m3_ruptures_topic_engine.py
```

Result JSON:

`/Users/yurielokhin/Documents/seminartext_projects/Стресс код/analysis/benchmark/results/bge_m3_ruptures_experiment_20260824T185128Z.json`

## Safety Evidence

| Artifact | SHA-256 |
|---|---|
| `topic_benchmark.json` | `3e0e8ae09ca3523c93a70ebf57fda0aadd331e8f06216647791ba4fa9a55f803` |
| `/Users/yurielokhin/bin/seminartext_topics.py` | `d8a14e83b877024c3e016a33e594af17d512741a77735ff3d8c7d1262628c8db` |

Safety confirmations:

- Gold benchmark data was not modified.
- Production Topic Engine was not modified.
- Production `seminartext` CLI was not modified.
- Gold labels were not tuned.
- No production model, prompt, threshold, smoothing, or change-point logic was
  changed.

## Aggregate Metrics

### Tolerance 0

| Engine | P | R | F1 | Pred | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| BGE-M3 + ruptures PELT | 0.175 | 0.229 | 0.198 | 63 | 11 | 52 | 37 |

### Tolerance 1

| Engine | P | R | F1 | Pred | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| BGE-M3 + ruptures PELT | 0.302 | 0.396 | 0.342 | 63 | 19 | 44 | 29 |

### Tolerance 2

| Engine | P | R | F1 | Pred | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| BGE-M3 + ruptures PELT | 0.381 | 0.500 | 0.432 | 63 | 24 | 39 | 24 |

## Early / Middle / Late Recall

### Tolerance 2 Comparison

| Engine | Early | Middle | Late |
|---|---:|---:|---:|
| Frozen Ollama semantic baseline | 0.800 | 0.250 | 0.167 |
| Issue #7 sliding sub-window | 0.500 | 0.688 | 0.167 |
| Issue #9 bge-m3 local peak | 0.450 | 0.250 | 0.167 |
| BGE-M3 + ruptures PELT | 0.650 | 0.438 | 0.333 |

Evidence: PELT improves middle recall versus frozen baseline and Issue #9, and
it is the first tested architecture here to improve late recall above 0.167.

### BGE-M3 + Ruptures Across Tolerances

| Tolerance | Early | Middle | Late |
|---:|---:|---:|---:|
| 0 | 0.400 | 0.125 | 0.083 |
| 1 | 0.600 | 0.188 | 0.333 |
| 2 | 0.650 | 0.438 | 0.333 |

## Per-Window Metrics At Tolerance 2

| Window | P | R | F1 | Pred | Gold |
|---|---:|---:|---:|---:|---:|
| `video_001_window_01` | 0.250 | 0.429 | 0.316 | 12 | 7 |
| `video_001_window_04` | 0.700 | 0.875 | 0.778 | 10 | 8 |
| `video_001_window_08` | 0.400 | 0.444 | 0.421 | 10 | 9 |
| `video_001_window_12` | 0.400 | 0.444 | 0.421 | 10 | 9 |
| `video_001_window_17` | 0.333 | 0.333 | 0.333 | 9 | 9 |
| `video_001_window_22` | 0.250 | 0.500 | 0.333 | 12 | 6 |

Per-window predicted boundaries:

| Window | Predicted boundaries | False negatives at +/-2 |
|---|---|---|
| `video_001_window_01` | `1, 7, 19, 25, 36, 45, 51, 57, 63, 78, 86, 97` | `16, 54, 60, 100` |
| `video_001_window_04` | `288, 294, 302, 307, 313, 323, 331, 339, 352, 359` | `310` |
| `video_001_window_08` | `656, 670, 679, 685, 691, 697, 704, 711, 721, 727` | `666, 688, 733, 739, 752` |
| `video_001_window_12` | `1073, 1079, 1093, 1099, 1111, 1117, 1126, 1138, 1154, 1162` | `1084, 1114, 1135, 1145, 1149` |
| `video_001_window_17` | `1606, 1620, 1636, 1650, 1657, 1663, 1676, 1688, 1700` | `1640, 1653, 1666, 1670, 1695, 1703` |
| `video_001_window_22` | `2044, 2053, 2058, 2074, 2079, 2087, 2094, 2103, 2112, 2124, 2131, 2142` | `2062, 2068, 2098` |

Evidence: the window-level profile is uneven. `window_04` is excellent, but
`window_01`, `window_17`, and `window_22` over-segment heavily.

## Runtime

| Metric | Value |
|---|---:|
| Runtime | 6.7 seconds |
| Embeddings | 280 |
| Ollama embedding batches | 12 |
| `prompt_eval_count` | 11,660 |

## Evidence, Hypotheses, Limitations

Evidence:

- Actual `ruptures.Pelt` was used.
- Dataset A all 6 gold windows ran.
- Tolerance 0/1/2 results were produced.
- Middle recall improved from 0.250 to 0.438 versus the frozen baseline.
- Late recall improved from 0.167 to 0.333 versus all three comparison targets.
- Precision fell to 0.381 at tolerance +/-2.

Hypothesis:

- PELT is more recall-friendly than the Issue #9 peak-only detector because it
  segments the whole signal globally rather than selecting isolated local maxima.
- The high false-positive count suggests the 15-second bge-m3 change signal sees
  many real local shifts below Gold granularity.

Limitations:

- Only one predeclared penalty/configuration was run.
- The result should not be used to tune Dataset A.
- It does not prove the architecture is ready for Dataset B; it only shows that
  proper PELT has a different and more recall-friendly error profile than the
  peak-only bge-m3 baseline.

## Recommendation

Do not promote to production.

Do not continue tuning on Dataset A. The result is `inconclusive`: it shows a
real middle/late recall improvement, but precision collapse is too large for a
clean go decision. The next Product Owner decision should be whether this
recall-oriented bge-m3 + PELT profile is worth one frozen Dataset B validation,
or whether to stop the bge-m3 change-point branch because the precision risk is
too high.
