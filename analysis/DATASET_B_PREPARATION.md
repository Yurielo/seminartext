# Dataset B Candidate Benchmark Preparation

Dataset B is prepared from `Заблокированные эмоции`, a seminar separate from Dataset A (`Стресс код`).

The generated artifact is `analysis/dataset_b/topic_benchmark_dataset_b.json`.

## Sampling Policy

Split the completed transcript into sequential 12-minute windows, keep windows that are at least 10 minutes long, then select six evenly spaced positions from first eligible to last eligible. Topic Engine predictions are not read.

No Topic Engine predictions, experiment outputs, or automatic boundaries are used to choose or adjust these windows.

## Candidate Windows

| Case | Window | Segments | Timestamps | Status |
| --- | ---: | --- | --- | --- |
| dataset_b_video_001_window_01 | 1 | 1-107 | 00:00:02.420-00:12:03.970 | needs_review |
| dataset_b_video_001_window_06 | 6 | 508-588 | 01:00:18.780-01:12:42.310 | needs_review |
| dataset_b_video_001_window_11 | 11 | 948-1035 | 02:01:04.720-02:13:10.480 | needs_review |
| dataset_b_video_001_window_15 | 15 | 1325-1411 | 02:49:30.090-03:01:31.550 | needs_review |
| dataset_b_video_001_window_20 | 20 | 1776-1878 | 03:49:46.280-04:01:50.620 | needs_review |
| dataset_b_video_001_window_25 | 25 | 2286-2384 | 04:50:06.540-05:02:11.450 | needs_review |

## Manual Gold Review Workflow

1. Open each candidate case in the JSON artifact and read only its transcript segments.
2. Mark true semantic topic starts as segment IDs in `gold.boundaries`.
3. Add one `gold.topics` entry per boundary with `start_id`, `title`, and optional `summary`.
4. Keep `review.status` as `needs_review` until both boundaries and topics are checked by a human reviewer.
5. Change `review.status` to `gold_complete` only after the reviewer confirms the labels were created without viewing Topic Engine predictions.
6. Confirm all six cases are `gold_complete`; only then run the frozen Dataset B validation configs.

## Guardrails

- Dataset A benchmark data is not modified.
- Production Topic Engine logic is not modified.
- Dataset B Gold labels are not fabricated or auto-generated.
- No parameter tuning is performed on Dataset B before frozen validation.
