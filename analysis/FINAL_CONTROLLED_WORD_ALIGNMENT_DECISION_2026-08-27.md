# Final Controlled Word Alignment Decision — Issue #38

Date: 2026-08-27
Status: bounded experiment complete; production integration was not performed.

## Executive decision

```text
WORD ALIGNMENT TECHNOLOGY SELECTED
SELECTED TECHNOLOGY: WhisperX 3.8.6 alignment-only path
ROLE: existing verified transcript + source audio -> native word intervals
CLASSIFICATION: ADOPT
FALLBACK: preserve canonical text, mark unsupported words unaligned, and retain
          coarse source-cue provenance; never fabricate production intervals
```

WhisperX is selected for the Canonical Evidence Layer's legacy/existing-transcript
alignment role. On the frozen 14:56.780 Russian target-corpus fragment it kept the
complete 1434-word semantic transcript in its segment text, emitted native positive
intervals for 1432 words (99.8605%), and explicitly left two words unaligned after
the same deterministic backtrack failure in both runs. It produced no substitutions,
insertions, zero-duration intervals, negative intervals, ordering inversions,
overlaps, or out-of-fragment timestamps.

The two complete alignment outputs were structurally identical. Warm alignment
took 47.46 s and 43.05 s on Apple M5 CPU (0.0529x and 0.0480x realtime) with a
measured process peak RSS of 3.97 GB.

This is a technology decision, not production integration. The next milestone is
Canonical Evidence Schema v1, where the adapter contract must preserve original
characters and provenance and represent unaligned words explicitly.

## 1. Frozen source and provenance

The experiment reused the exact source and frozen fragment prepared by the prior
alignment bake-off. It did not switch sources to improve the result.

| Field | Frozen value |
|---|---|
| Dataset role | Dataset A / DEVELOPMENT-CALIBRATION |
| Project | `Стресс код` |
| Source ID | `video_001` |
| Source media | `/Users/yurielokhin/Documents/seminartext_projects/Стресс код/source/video/Стресс Код декабрь 2022 День 1.mp4` |
| Source media SHA-256 | `f4d4b81f4997a12aad5dab0890b6137387d355b24de79fe7e728b003cf0a460a` |
| Source SRT | `/Users/yurielokhin/Documents/seminartext_projects/Стресс код/transcript/video_001/transcript.srt` |
| Source SRT SHA-256 | `9614b41c5e7a9973f960338ef63e0c22967238d60b59932e96b4016b5d6cb913` |
| Requested source interval | 600.000–1500.000 s |
| Frozen complete-cue interval | 600.000–1496.780 s |
| Duration | 896.780 s / 14:56.780 |
| Frozen cues | 124 |
| Frozen reference words | 1434 |
| Frozen reference SHA-256 | `728981fc34eea6e47b6cd68c332c674a2c478b21b38f76f75fbb81d3e915c715` |
| Frozen segments SHA-256 | `3f3ab7b6cf29bc1d353ce2066eac3a049ca1d2cfcf96c6c4c360211886a7990e` |
| Experimental WAV SHA-256 | `6cd44ca07c9ba332e4285b90268f20c8329ecdae39e933ebbae7bd222a0b1217` |

Committed provenance artifacts:

- `analysis/word_alignment_decision/sample_manifest.json`;
- `analysis/word_alignment_decision/frozen_reference.txt`;
- `analysis/word_alignment_decision/frozen_segments.json`.

Dataset E (`Нумеролог`) was not read, used, regenerated, or evaluated. Dataset D,
Dataset F, Topic Engine, and all Topic Gold were outside the experiment.

## 2. Isolation and exact environment

All new runtime and model dependencies were installed below
`/tmp/seminartext-word-alignment-issue38`. The SeminarText production environment,
Homebrew packages, transcription defaults, and `requirements-experiments.txt`
were not changed.

| Component | Exact value |
|---|---|
| Hardware | MacBook Air Mac17,3; Apple M5; 10 cores; 16 GB unified memory |
| OS | macOS 26.5.2 build 25F84, arm64 |
| Isolated runtime manager | uv 0.12.6 |
| Isolated Python | CPython 3.13.15 |
| WhisperX | 3.8.6 |
| torch / torchaudio | 2.8.0 / 2.8.0 |
| transformers | 4.57.6 |
| Russian alignment model | `jonatasgrosman/wav2vec2-large-xlsr-53-russian` |
| Model revision | `2329100508896c6d9b157019803ab5601e6f3406` |
| Model SHA-256 | `d1cdb1a7921de7d363f967a9b0101a713602e109dba62b6f3f9ae2e0b2df0c1c` |
| Model size | 1,262,093,719 bytes |
| Isolated venv footprint | approximately 1.0 GB |
| Offline after cache warm-up | yes |

The model download was accepted only after its byte size and SHA-256 matched the
immutable Hugging Face LFS metadata. The WhisperX runner invokes
`load_align_model(language_code="ru")` and `whisperx.align(...)` directly. It
does not invoke WhisperX ASR.

Reproduction runner:

```text
analysis/word_alignment_decision/run_whisperx_existing_text.py
```

The full raw output remained outside Git because it is 3.6 MB generated evidence;
its SHA-256 is
`6fa19362f2273bb4db02a99bb966d914a726d0117cace38b3b017a6b15450f80`.
The compact committed metrics are in
`analysis/word_alignment_decision/experiment_summary.json`.

## 3. Candidate applicability

| Candidate | Requirement fit | Run status | Classification |
|---|---|---|---|
| WhisperX 3.8.6 | Native forced alignment of supplied Russian text using a language-specific wav2vec2 model | Two complete alignment-only runs | `ADOPT` |
| stable-ts 2.19.1 | Aligns supplied text, but produces collapsed intervals and is now archived | Prior two complete runs plus bounded built-in normalization check | `REJECT` |
| whisper.cpp 1.9.2 large-v3 DTW | Fresh ASR with experimental DTW point anchors; does not preserve the supplied transcript in the tested path | Prior complete run and deterministic smoke rerun | `REJECT` for canonical existing-text alignment |
| MLX Whisper 0.4.3 | Official path retranscribes audio and returns ASR word timestamps; no supplied-transcript forced-alignment API was identified | Prior feasibility runs only | `NOT APPLICABLE` |

No extra candidate was added because WhisperX satisfied the critical requirements.

### Maintenance and licensing

- WhisperX is active, was pushed as recently as 2026-07-13, and is BSD-2-Clause.
  Its current package declares Python `>=3.10,<3.14`; an isolated 3.13 runtime
  resolves the prior Python 3.14 blocker. The selected Russian model is
  Apache-2.0.
- stable-ts was archived by its owner on 2026-05-30 and its README states that
  development is paused indefinitely. The code is MIT, but the maintenance risk
  is unacceptable for a new foundation dependency.
- whisper.cpp is active, MIT, and first-class on Apple Silicon. Its DTW timestamp
  remains an experimental point (`t_dtw`), and the tested path produced new ASR
  text rather than aligning the verified transcript.
- MLX examples are active and MIT, but the relevant public interface is ASR
  transcription, not existing-text alignment.

Primary upstream references:

- <https://github.com/m-bain/whisperX>
- <https://huggingface.co/jonatasgrosman/wav2vec2-large-xlsr-53-russian>
- <https://github.com/jianfch/stable-ts>
- <https://github.com/ggml-org/whisper.cpp>
- <https://github.com/ml-explore/mlx-examples/tree/main/whisper>

## 4. Text preservation

The same Unicode word tokenizer used in the prior bake-off was applied to the
frozen reference and candidate output.

| Metric | WhisperX | stable-ts | whisper.cpp DTW |
|---|---:|---:|---:|
| Reference words | 1434 | 1434 | 1434 |
| Semantic words retained in segment text | 1434 | 1434 | N/A: fresh ASR |
| Timed/aligned words | 1432 | 1434 | 1557 fresh-ASR words |
| Substitutions | 0 | 0 | 46 |
| Deletions / unaligned | 2 unaligned | 0 | 55 deletions vs reference |
| Insertions | 0 | 0 | 178 |
| WER / alignment deletion rate | 0.1395% timing coverage loss; semantic text unchanged | 0.000% | 19.456% |
| Silently rewrote verified text | no | no | yes by role: new ASR transcript |

WhisperX's only failed alignment was the two-word phrase `думаешь, что` at
599.970–600.070 s. In both runs WhisperX emitted the same warning:
`backtrack failed, resorting to original`. The phrase remained present in segment
text but had no word records. This is explicit unaligned evidence, not semantic
loss and not a fabricated timestamp.

## 5. Timing validity

| Metric | WhisperX | stable-ts | whisper.cpp DTW decoder intervals |
|---|---:|---:|---:|
| Native word intervals | yes | yes, but collapsed | decoder intervals plus DTW points |
| Zero-duration words | 0 | 188 | 75 |
| Negative intervals | 0 | 0 | 0 |
| Start inversions | 0 | 0 | 0 |
| Adjacent overlaps | 0 | 0 | 0 |
| Out-of-fragment timestamps | 0 | 0 | 0 |
| Unaligned verified words | 2 | 0 records, but 188 collapsed | not applicable to supplied text |
| Median positive duration | 0.2605 s | not decisive | not decisive |
| P95 duration | 1.40995 s | not decisive | not decisive |
| Maximum duration | 9.565 s | collapsed runs include severe local distortion | not decisive |

WhisperX's long upper-tail intervals occur around pause-heavy speech and must be
retained as an explicit known limitation. They do not violate ordering or bounds,
but the future schema should retain confidence and allow QA flags for unusually
long or low-score intervals.

## 6. Frozen manual timing audit

Five probes were fixed at beginning, first quarter, middle, difficult/pause-heavy
speech, and end. Because this Codex runtime cannot audition local audio, the audit
was performed manually at signal level: the frozen 16 kHz clips were rendered as
waveform/spectrogram evidence; phrase identity came from frozen transcript order;
and phrase onsets were marked only where a signal transition was distinguishable.
The claimed precision is deliberately limited to ±0.20–0.25 s. This is a bounded
QA sample, not new Gold and not millisecond ground truth.

| Probe | Manual phrase onset | Uncertainty | WhisperX error | stable-ts error | whisper.cpp error |
|---|---:|---:|---:|---:|---:|
| `быть` (beginning) | 2.50 s | ±0.20 s | 0.10 s | 0.02 s | 0.24 s |
| `вопросом` (25%) | 222.50 s | ±0.20 s | 0.03 s | 0.19 s | 0.08 s |
| `есть вы с коллегами` (middle) | 449.70 s | ±0.25 s | 0.06 s | 1.02 s | 2.26 s |
| `И, возможно` (difficult) | 668.95 s | ±0.20 s | 0.02 s | 1.24 s | not scoreable: phrase rewritten |
| `Хорошо` (end) | 869.55 s | ±0.20 s | 0.01 s | 0.27 s | 0.15 s |

Summary:

| Candidate | Scored anchors | Median absolute error | Worst observed error |
|---|---:|---:|---:|
| WhisperX | 5 | 0.03 s | 0.10 s |
| stable-ts | 5 | 0.27 s | 1.24 s |
| whisper.cpp DTW | 4 | 0.20 s | 2.26 s |

These numbers are interpreted at the stated manual uncertainty, not as precision
beyond it. The audit distinguishes WhisperX's locally plausible native intervals
from stable-ts collapse and from whisper.cpp's lexical/timing failures.

## 7. Point-to-interval policy

### WhisperX

WhisperX natively provides `start` and `end`; no point-to-interval conversion is
required. The canonical adapter must preserve the native interval and score.

For an unaligned word, the invariant is:

1. keep the exact original word/character span and stable word ID;
2. set `alignment_status = unaligned` and leave native start/end absent;
3. retain source cue/segment bounds as coarse provenance, not as a word interval;
4. route the word to a review queue;
5. never interpolate or synthesize an interval silently.

### stable-ts

The prior output contained 188 zero-duration words in 91 runs, with a longest run
of seven. Twenty-nine runs had no free gap between adjacent intervals. A bounded
repeat of stable-ts's own deterministic
`adjust_by_silence(min_word_dur=0.1, word_level=True)` produced identical output
in two runs but left all 188 zero-duration words. Repair would therefore require
moving neighbouring word boundaries or introducing a new allocation heuristic.
That is not a safe semantics-preserving normalization to adopt in this Issue.

### whisper.cpp DTW

`t_dtw` is a point anchor, while the tested decoder word intervals included 75
zero-duration words. Converting points to intervals would require a new frozen
heuristic, and the candidate already fails the more important existing-transcript
preservation requirement. No conversion is selected.

## 8. Reproducibility

| Candidate/configuration | Repeat evidence |
|---|---|
| WhisperX alignment-only | Two complete results structurally identical; SHA-256 `cc4fcd6eff2a7b029694a67ab19794f7d023d6ddc0752a1858fa97b508dc8674` |
| stable-ts original alignment | Two complete semantic payloads identical; SHA-256 `e082fec4322051ada795e1afed39cfed9e230e6c5658accbd4d7926e23648270` |
| stable-ts built-in normalization check | Two outputs identical; all 188 zero intervals remained; SHA-256 `7a12270963966ec86d102b2cbf05a62416e61de7a0a2060b3a36a787cf585ad6` |
| whisper.cpp DTW | Two 60-second raw outputs byte-identical; SHA-256 `f64d05f096ba5a4d7e5853ca723dd16b5f69d476ce9c01349b3b58fd68e824f` |

Runtime metadata was excluded from semantic/timing hashes.

## 9. Operational fit

| Dimension | WhisperX | stable-ts | whisper.cpp DTW | MLX Whisper |
|---|---|---|---|---|
| Apple Silicon | CPU works; no Metal acceleration in this run | CPU works | native Metal/Accelerate | native MLX |
| Runtime / 896.78 s | 43.05–47.46 s warm | 101.81–103.63 s | 256.64 s | 13–15 s with base ASR, but irrelevant role |
| Peak RSS | 3.97 GB | ~1.05 GB | 4.15 GB | ~0.82 GB RSS |
| Install footprint | ~1.0 GB venv + 1.262 GB model | ~871 MiB venv + model | existing 3.095 GB model | ~1.16 GiB venv + model |
| Offline/local | yes after model cache | yes | yes | yes |
| Existing transcript | yes | yes | no in tested path | no relevant path identified |
| Maintenance | active | archived / paused | active | active |
| License | BSD-2; model Apache-2.0 | MIT | MIT | MIT |
| Integration complexity | isolated Python component; medium/high dependency surface | medium, but unsupported | low incremental, wrong role | wrong role |

The selected component should remain an isolated Evidence Foundation worker rather
than be injected into the current transcription environment. Cached-model offline
operation is required for production packaging.

## 10. Candidate classifications

### WhisperX — `ADOPT`

Adopt as the existing-verified-transcript aligner. Add only a SeminarText adapter
for immutable character spans, stable IDs, source provenance, explicit unaligned
status, configuration/model hashes, and QA flags. Do not fork or modify the forced
alignment algorithm.

### stable-ts — `REJECT`

It preserves text, but 13.11% of words have zero duration, the built-in bounded
normalization did not repair them, manual probes show local collapse, and upstream
is archived with development paused indefinitely.

### whisper.cpp large-v3 DTW — `REJECT`

Reject for the Canonical Evidence Layer's existing-transcript alignment role. It
rewrites text as fresh ASR with 19.456% WER, exposes experimental DTW points rather
than complete native intervals, and still has zero-duration decoder words. It may
remain the unchanged coarse-SRT transcription fallback, not the selected aligner.

### MLX Whisper — `NOT APPLICABLE`

The available MLX path performs ASR transcription with word timestamps. It does
not provide the required existing-transcript forced alignment path, so no forced
bake-off run or large-model download was justified.

## 11. Selected architecture role and limitations

Canonical role:

```text
verified transcript + source media
  -> WhisperX alignment-only worker
  -> native word intervals + confidence + explicit unaligned records
  -> Canonical Evidence Layer adapter
```

Required adapter contract for the next milestone:

- original transcript SHA and original character span per word;
- stable word ID and source cue/segment IDs;
- native `start`, `end`, and score when aligned;
- `alignment_status` and absence of fabricated timestamps when unaligned;
- aligner/package/model revision and hashes;
- source media hash and fragment transform provenance;
- deterministic output normalization for storage only;
- QA flags for unaligned, very long, or low-confidence intervals;
- nullable `speaker_id` in the future canonical schema, without diarization now.

Known limitations:

1. two words in one 100 ms constrained segment were unaligned;
2. some intervals include long pause-heavy spans; maximum observed duration was
   9.565 s and requires QA visibility;
3. the Python dependency surface and model footprint are larger than whisper.cpp;
4. Apple Silicon used CPU, not Metal;
5. a language-specific alignment model is required;
6. overlapping speech and characters outside the model dictionary remain upstream
   limitations;
7. one target-corpus fragment does not prove all future seminar conditions.

Fallback policy:

- keep every verified transcript word unchanged;
- mark unsupported words `unaligned` and queue review;
- never derive a source-exact word interval from SRT or proportional text position;
- if WhisperX cannot run, retain the existing whisper.cpp large-v3 coarse-SRT
  production path and do not claim that a canonical word timeline exists;
- do not silently fall back to stable-ts or whisper.cpp DTW points.

## 12. Scope and next milestone

- No production algorithm or dependency was changed.
- No transcription defaults or pipeline behavior was changed.
- Topic Engine and all Topic Gold were untouched.
- Dataset E was not used.
- Dataset D remained locked and unopened for Topic evaluation.
- Dataset F was not repaired.
- Canonical Evidence Schema v1 and Word Timeline MVP were not implemented.
- No custom forced aligner or production heuristic was built.

The alignment decision is closed. The next milestone is
**Canonical Evidence Schema v1**, followed by the one-source Word Timeline MVP.
