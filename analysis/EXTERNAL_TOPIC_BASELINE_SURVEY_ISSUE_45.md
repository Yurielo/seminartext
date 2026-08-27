# External Topic / Semantic Segmentation Survey and Baseline Challenge

Issue: [#45](https://github.com/Yurielo/seminartext/issues/45)<br>
Survey and challenge date: 2026-08-27<br>
Evidence status: development comparison, not production promotion

## Decision

The bounded external challenge found one serious challenger:

- **Boundary Detection:** `EXTERNAL_BASELINE_SELECTED_FOR_ADAPTATION` —
  TreeSeg beat both retained SeminarText approaches on development Datasets A
  and B at tolerance ±2. It is selected for an isolated adaptation/diagnostic
  branch, not for production.
- **Current status:** `CURRENT_LOCAL_PEAK_REMAINS_PRIMARY` — A/B are already
  development evidence, external methods were not run on frozen C, and D remains
  locked. TreeSeg therefore cannot displace the current primary experimental
  candidate without new independent evidence.
- **Seminar Structure:**
  `EXTERNAL_STRUCTURE_TOOL_SELECTED_FOR_GLOBAL_STRUCTURE_POC` — TreeSeg's native
  nested partition tree is a closer fit than BERTopic for a temporal seminar
  hierarchy POC.
- **Knowledge Engine:** no selection. Cross-seminar concept and relation work is
  outside this issue.

No production Topic Engine, Gold, Roadmap, or State artifact was changed.

## Repository-grounded benchmark policy

The controlling sources are `SEMINARTEXT_4_ROADMAP.md` sections 2.5–2.12,
`SEMINARTEXT_4_STATE.json`, and
`analysis/TOPIC_ENGINE_POST_DATASET_C_REVIEW.md` section 9.

| Dataset | Current legal role | Candidate exploration | Parameter selection | New comparison in #45 | Future locked evaluation |
|---|---|---:|---:|---:|---:|
| A | Development / calibration | Yes | Yes | Yes | No |
| B | Historical validation, now development / error analysis | Yes | Yes | Yes | No |
| C | Used frozen validation; closed for tuning and architecture selection | No | No | **No new run**; historical numbers may only be cited | No |
| D | `LOCKED_TEST`, currently blocked by source quality | No | No | No inspection or run | Yes, once only after candidate/config/criteria freeze |
| E | Excluded from all Topic Engine evidence | No | No | No | No |
| F | Quarantined potential development after topic-agnostic repair | Not yet | Not yet | No | No |

Consequences for this challenge:

1. The runner accepts only the exact A/B SHA-256 values and has no generic or
   C/D/E input. A hash mismatch is fatal.
2. External candidates were never run on C. Its Local Peak `0.583` and PELT
   `0.345` ±2 F1 figures below are historical frozen references only.
3. D Gold was not located, read, or evaluated. E was not used in any form.
4. One allowed Dataset B window was used for a count-only Chonkie compatibility
   smoke test. The `0.075` percentile was then fixed from the repository's
   30–45 topics/hour product prior before aggregate scoring; no F1 search was
   performed. TreeSeg's required `K` was fixed from the same prior, never from
   per-case Gold.
5. A/B results are development evidence and must not be described as blind,
   frozen, or proof of generalization.

## Problem separation

| Layer | Required output | Evaluated here |
|---|---|---|
| Boundary Detection | Ordered local start boundaries on the transcript timeline | Yes: Chonkie, TreeSeg, TextTiling compatibility, retained Local Peak/PELT |
| Seminar Structure | Hierarchy, recurrence, merging, and grouping while respecting time | Surveyed; TreeSeg selected for a later POC |
| Knowledge Engine | Concepts and relations across topics/seminars | No; explicitly out of scope |

BERTopic is therefore not treated as a direct boundary detector. Conversely,
good flat-boundary F1 does not by itself validate TreeSeg's hierarchy.

## External survey

Activity and versions are frozen in
`analysis/external_topic_baselines/source_snapshot.json`. Activity means the
official default branch as observed on 2026-08-27, not a guarantee of support.

| Candidate | Status / license | Local, Apple Silicon, Russian | Actual problem / I/O | Integration | Classification |
|---|---|---|---|---|---|
| [Chonkie 1.7.0 SemanticChunker](https://github.com/feyninc/chonkie) | Active (2026-08-26); MIT | Local. Native arm64 core installed. Russian depends on supplied delimiters and multilingual embeddings; BGE-M3 adapter worked. | Boundary-oriented generic document chunking. Text in; offset-bearing chunks out. | Medium: custom `BaseEmbeddings` adapter and transcript-ID offset mapping. | `REJECT` for Topic Engine replacement: weaker than Local Peak on both A/B. Retain only as a generic chunking reference. |
| [TreeSeg](https://github.com/geraldthewes/topic-treeseg) / [paper](https://arxiv.org/abs/2407.12028) | Package fork quiet since 2025-05; Apache-2.0; original repo archived | Fully local with Ollama BGE-M3. NumPy/Matplotlib work on Apple Silicon. Language suitability follows embeddings; Russian run succeeded. | Both: ordered transcript units in; flat transition vector plus nested divisive partition tree out. | Medium/high: requires `K`; alpha package has an undeclared Matplotlib import, stale README config shape, and needs an explicit event loop on Python 3.14. | `ADAPT` as isolated boundary challenger and structure POC. |
| [ruptures PELT](https://github.com/deepcharles/ruptures) | Active; BSD-2-Clause; repository pins 1.1.9 | Local and practical on Apple Silicon; language-neutral once embeddings exist. | Boundary change-point primitive over ordered numeric features; no hierarchy or labels. | Already integrated and frozen. | `ADOPT` only in its current recall-comparator role; reject as standalone primary because of oversegmentation. |
| [BERTopic 0.17.4](https://github.com/MaartenGr/BERTopic) / [hierarchical topics](https://maartengr.github.io/BERTopic/getting_started/hierarchicaltopics/hierarchicaltopics.html) | Active (2026-08-27); MIT | Local modes exist but UMAP/HDBSCAN/transformer stack is heavier. Multilingual embeddings are supported; Apple Silicon is plausible but dependency-heavy. | Topic clustering, representations, and topic hierarchy over documents. It does not natively decide temporally ordered local boundaries. | High for SeminarText because temporal contiguity, recurrence, and window artifacts need separate treatment. | `REFERENCE_ONLY`; useful structure vocabulary, but TreeSeg is the more direct temporal hierarchy POC. |
| [NLTK 3.10.3 TextTiling](https://www.nltk.org/api/nltk.tokenize.texttiling.html) / [source filter](https://github.com/nltk/nltk/blob/a79356490469d741dba11b5cb97acccd12be0d8e/nltk/tokenize/texttiling.py#L108-L111) / [Hearst paper](https://aclanthology.org/J97-1003/) | NLTK active; legacy algorithm; Apache-2.0 | Lightweight/local/Apple-friendly in general. Current tokenizer produced zero lexical units for the Cyrillic A/B text and failed all 12 cases. | Lexical-cohesion boundary detector. Document in; topical text sections out. | Low for English, but a Russian tokenizer rewrite would be a new adaptation outside this baseline control. | `REJECT` for direct Russian use. |
| [Chonky multilingual neural splitter](https://github.com/mirth/chonky) | Last code activity 2025-10; MIT | Local 140M multilingual model; project reports Russian paragraph results; transformer inference is Apple-practical. | Learned semantic paragraph splitting of raw text, not seminar topic transitions. | Medium; model download and offset mapping, with task/domain mismatch. | `REFERENCE_ONLY` until transcript-topic evidence exists. |
| [Text Segmentation as a Supervised Learning Task](https://github.com/koomri/text-segmentation) / [paper](https://arxiv.org/abs/1803.09337) | Code last changed 2019; no detected repository license | Python 2.7, Torch 0.3/CUDA-era setup, English Wikipedia resources; not Apple/Russian practical. | Supervised flat topic segmentation. | Very high and legally unclear. | `REJECT`. |
| [KONVENS 2025 TextTiling/GPT-4o comparison](https://github.com/uniba-mi/text-segmentation) / [paper](https://aclanthology.org/2025.konvens-2.21/) | Recent artifact; GPL-3.0 | Docker is possible on Apple Silicon. GPT path is online/cost-bearing; study data is unavailable. No demonstrated Russian setup. | Flat text segmentation with TextTiling variants or one GPT-4o call path. | Medium/high; unavailable study data and provider/model drift limit exact reproduction. | `REFERENCE_ONLY` for LLM study design. Do not import GPL code or make it the default baseline. |

The survey deliberately avoids a benchmark zoo. Chonkie and TreeSeg were the
only new maintained candidates run end-to-end. TextTiling was kept as the
requested classical compatibility control and stopped at a reproducible failure.

## Baseline challenge design

Inputs were the existing transcript segments and Gold boundaries of A/B. Both
embedding candidates used local Ollama `bge-m3:latest`; no cloud service or LLM
judge was used.

- Chonkie 1.7.0: external `SemanticChunker`; semantic-only character capacity of
  1,000,000 prevents capacity cuts; native three-unit similarity window and
  filtering defaults; fixed local-minimum percentile `0.075`.
- TreeSeg 0.1.0 at commit `f18929a...`: documented
  `MIN_SEGMENT_SIZE=2`, `LAMBDA_BALANCE=0`, and expansion width 2. Because the
  API requires `K`, each window uses
  `round(duration_hours × 37.5)`, minimum 2. This is a product-density prior,
  not automatic topic-count inference.
- NLTK TextTiling 3.10.3: published/default `w=20`, `k=10`, HC cutoff, Russian
  NLTK stopwords. All cases raised the same zero-vector smoothing error.
- Metrics use the repository runner's exact greedy one-to-one matching at
  segment-ID tolerances 0, 1, and 2. Window-start boundaries remain included so
  historical results stay comparable.

Pinned commands, configuration, predictions, per-case metrics, runtimes, and
failures are under `analysis/external_topic_baselines/`.

## Results

### Boundary F1 by accepted tolerance

| Method | A F1 ±0 | A F1 ±1 | A F1 ±2 | B F1 ±0 | B F1 ±1 | B F1 ±2 |
|---|---:|---:|---:|---:|---:|---:|
| Local Peak (retained) | 0.243 | 0.405 | 0.405 | 0.333 | 0.500 | 0.533 |
| PELT (retained) | 0.198 | 0.342 | 0.432 | 0.170 | 0.340 | 0.447 |
| Chonkie SemanticChunker | 0.189 | 0.253 | 0.358 | 0.293 | 0.320 | 0.427 |
| **TreeSeg** | **0.295** | **0.505** | **0.632** | **0.415** | **0.537** | **0.659** |

### Tolerance ±2 operational comparison

| Method | A P / R / F1 | A predicted / Gold | A count MAE | A runtime | B P / R / F1 | B predicted / Gold | B count MAE | B runtime |
|---|---|---:|---:|---:|---|---:|---:|---:|
| Local Peak | .577 / .312 / .405 | 26 / 48 | 3.67 | 5.82 s | .615 / .471 / .533 | 26 / 34 | 1.33 | 11.61 s |
| PELT | .381 / .500 / .432 | 63 / 48 | 2.50 | 6.69 s | .350 / .618 / .447 | 60 / 34 | 4.33 | 8.87 s |
| Chonkie | .362 / .354 / .358 | 47 / 48 | **1.17** | 33.23 s | .390 / .471 / .427 | 41 / 34 | **1.50** | 31.33 s |
| **TreeSeg** | **.638 / .625 / .632** | 47 / 48 | **0.83** | 12.39 s | **.563 / .794 / .659** | 48 / 34 | 2.33 | 12.39 s |

Runtime is wall-clock time for the six windows on this Apple Silicon machine and
includes local embedding calls. It is operational context, not a portable
performance guarantee.

TreeSeg improves ±2 F1 over Local Peak by `+0.227` on A and `+0.125` on B. On B
it obtains the gain through high recall (`0.794`) while predicting 48 topics for
34 Gold topics, so oversegmentation remains material. On A it is much better
balanced and nearly matches Gold cardinality. Chonkie tracks count more closely
than PELT but is slower and loses to Local Peak on both sources. It is not a
competitive Topic Engine replacement in this configuration.

### Frozen C reference — not a new external comparison

| Method | Historical C F1 ±2 | Status |
|---|---:|---|
| Local Peak | 0.583 | Frozen historical reference |
| PELT | 0.345 | Frozen historical reference |
| Chonkie / TreeSeg | — | **Not run on C** |

It would violate policy to select or reject the external candidates by observing
new C results. D remains the only future locked evaluation.

## Human Correction Time / Hour protocol

No human correction session occurred in this issue, so no time value is claimed.
For the future locked evaluation:

1. Freeze candidate code, dependency/model hashes, global topic-count policy,
   accepted tolerance, UI, analysis plan, and success thresholds before D is
   opened.
2. Use at least two trained reviewers. Blind algorithm identity and randomize
   candidate order with a balanced crossover; do not let a reviewer's corrected
   output from one candidate seed another candidate.
3. Show transcript text, audio/timestamps when available, predicted boundaries,
   and topic spans in one fixed correction UI. Reviewers may add, delete, move,
   merge, or split boundaries and mark an ambiguity instead of guessing.
4. Record active interaction time only. Pause the timer for breaks, tool failure,
   loading, and adjudication. Log operations and final boundary IDs separately
   from elapsed time.
5. Compute `active correction minutes / source media hours` per reviewer and
   source. Primary reporting is median with source-level bootstrap intervals;
   secondary reporting includes add/delete/move operations per hour,
   disagreement, and final P/R/F1.
6. Run a short practice task on non-D material before timing. Keep D to the one
   permitted blind evaluation after all candidates and criteria are frozen.

Until timed review exists, `FP + FN` at ±2 is a reproducible minimum add/delete
proxy, not elapsed time:

| Method | A FP + FN | B FP + FN |
|---|---:|---:|
| Local Peak | 44 | 28 |
| PELT | 63 | 52 |
| Chonkie | 61 | 43 |
| **TreeSeg** | **35** | **28** |

This proxy omits cognitive inspection time, title/structure editing, and moves
within tolerance. It must never be relabeled as Human Correction Time / Hour.

## Limitations and next action

- A/B contain only two already-studied development sources. The result supports
  a challenger, not generalization or production readiness.
- TreeSeg's forced `K` couples boundary quality to the existing density prior.
  Dataset B shows that a global prior can still oversegment. Automatic topic
  count remains an unresolved separate problem.
- The package is alpha and needs small integration shims. Production adoption
  would require dependency cleanup, deterministic model pinning, and a stable
  hierarchy serialization contract.
- The flat benchmark does not measure whether TreeSeg's upper tree levels are
  semantically useful, preserve recurrence, or reduce human structure work.
- LLM segmentation was not run: the surveyed reproducible artifact uses an
  external model path, unavailable study data, and a different licensing/cost
  profile. Fabricating an LLM result would add no valid evidence.

Recommended next Semantic Automation action: Product Owner review of this
decision, then one isolated TreeSeg full-seminar hierarchy POC on the already
permitted Golden Seminar. Preserve Local Peak as primary, keep PELT as recall
comparator, and do not open D until one candidate/config plus the Human
Correction Time acceptance plan are frozen.
