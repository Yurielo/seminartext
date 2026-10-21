# Issue #45 reproducibility

The challenge runner is hash-locked to development Datasets A and B. It has no
Dataset C/D/E input and exits if either allowed benchmark hash differs.

Create an isolated environment (Python 3.10+; the recorded run used 3.14.6 on
Apple Silicon):

```bash
python3 -m venv .venv-issue45
.venv-issue45/bin/python -m pip install -r \
  analysis/external_topic_baselines/requirements.txt
NLTK_DATA="$HOME/.cache/seminartext/issue45-nltk" \
  .venv-issue45/bin/python -m nltk.downloader \
  -d "$HOME/.cache/seminartext/issue45-nltk" stopwords
```

With local Ollama running and `bge-m3:latest` installed:

```bash
NLTK_DATA="$HOME/.cache/seminartext/issue45-nltk" \
  ./scripts/seminartext-owned-run .venv-issue45/bin/python \
  analysis/external_topic_baselines/run_baseline_challenge.py \
  --dataset-a "$SEMINARTEXT_PROJECTS/Стресс код/analysis/benchmark/topic_benchmark.json" \
  --dataset-b analysis/dataset_b/topic_benchmark_dataset_b.json \
  --output analysis/external_topic_baselines/results/baseline_challenge.json
```

The committed result SHA-256 is
`b9d199d37856ce2afb9eac1b9134276760da97f33cc8ed44ed6cf14abc760350`.
Runtime values are operational observations, so a repeat result is expected to
differ in timestamp, runtime, and whole-file hash while predictions and metrics
remain stable for the pinned model and packages.

Run the dependency-free adapter tests with:

```bash
python3 tests/test_external_topic_baseline_challenge.py
```
