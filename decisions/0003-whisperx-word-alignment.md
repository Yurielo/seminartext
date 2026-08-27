# 0003 - WhisperX for Existing-Transcript Word Alignment

Date: 2026-08-27

## Status

Accepted

## Context

The Canonical Evidence Layer needs a local-first word-level temporal coordinate
system for an existing verified transcript of the Product Owner's seminar corpus.
The prior bake-off did not select a technology: stable-ts preserved text but
collapsed 188 of 1434 word intervals to zero duration, while whisper.cpp
large-v3 DTW produced fresh ASR text with 19.456% WER and experimental point
anchors rather than a complete existing-transcript alignment.

Issue #38 repeated the same frozen Dataset A target-corpus fragment and closed
the decision with a bounded comparison. Dataset E, Topic Engine, Topic Gold, and
production dependencies were not used or changed.

## Decision

Adopt **WhisperX 3.8.6 alignment-only** as the technology for aligning an
existing verified transcript to source audio.

The selected reference configuration is:

- isolated CPython 3.13 environment;
- CPU execution on Apple Silicon;
- WhisperX `load_align_model(language_code="ru")` and `align(...)`;
- Russian model `jonatasgrosman/wav2vec2-large-xlsr-53-russian` at revision
  `2329100508896c6d9b157019803ab5601e6f3406`;
- model SHA-256
  `d1cdb1a7921de7d363f967a9b0101a713602e109dba62b6f3f9ae2e0b2df0c1c`;
- no WhisperX ASR pass and no replacement of transcript semantic text.

WhisperX is an isolated Evidence Foundation component. It is not added directly
to the current production transcription environment by this decision.

## Evidence

On the frozen 896.780-second Russian fragment:

- the complete 1434-word semantic transcript remained present with zero
  substitutions, deletions, or insertions at segment-text level;
- 1432 words received native positive intervals (99.8605% coverage);
- two words remained explicitly unaligned after a deterministic backtrack
  failure, without semantic rewrite;
- zero-duration, negative, overlapping, inverted, and out-of-bounds intervals
  were all zero;
- two complete runs produced the same semantic/timing hash;
- warm runs took 47.46 s and 43.05 s on Apple M5 CPU;
- measured peak RSS was 3.97 GB;
- five bounded signal-level manual anchors had median absolute error 0.03 s and
  worst observed error 0.10 s at stated reference uncertainty ±0.20–0.25 s.

Full evidence is recorded in
`analysis/FINAL_CONTROLLED_WORD_ALIGNMENT_DECISION_2026-08-27.md` and
`analysis/word_alignment_decision/experiment_summary.json`.

## Canonical adapter invariants

The future Canonical Evidence Schema adapter must:

1. preserve original transcript text and character spans exactly;
2. assign stable word IDs and retain source cue/segment provenance;
3. store native start/end and score only when alignment succeeded;
4. store an explicit `alignment_status`;
5. leave start/end absent for unaligned words rather than synthesize them;
6. retain source media, transcript, aligner, model, and configuration hashes;
7. preserve ordering and source bounds;
8. expose QA flags for unaligned, unusually long, or low-confidence intervals;
9. remain speaker-ready through a nullable `speaker_id`, without requiring
   diarization in this milestone.

## Point-to-interval policy

WhisperX supplies native intervals; no point-to-interval normalization is
selected.

For an unaligned word, coarse SRT/source-cue bounds may be retained only as
provenance. They must not be presented as a word interval. The word is queued for
review with absent native timing.

No stable-ts zero-duration repair and no whisper.cpp DTW point conversion is
adopted. Both would require a new timing heuristic that this decision explicitly
avoids.

## Fallback

If WhisperX cannot run:

- preserve the verified transcript unchanged;
- retain the existing whisper.cpp large-v3 coarse-SRT production path;
- mark the canonical word timeline unavailable or affected words unaligned;
- never silently fall back to stable-ts or derived word timing;
- never claim source-exact word coordinates from SRT or proportional estimates.

## Consequences

Positive:

- the architecture has a maintained external forced-alignment solution;
- existing verified text remains authoritative;
- native intervals avoid a custom point-to-interval algorithm;
- deterministic and local/offline operation is practical after model caching;
- the Word Alignment milestone is closed, allowing Canonical Evidence Schema v1
  to proceed.

Costs and risks:

- the isolated Python environment and language model add roughly 2.3 GB before
  cache overhead;
- the measured CPU process can use about 4 GB RSS;
- a language-specific model and non-trivial Python dependency stack must be
  packaged and pinned;
- unaligned and long/low-confidence intervals require explicit QA handling;
- CPU execution does not use Apple Metal acceleration;
- the decision is based on one controlled target-corpus fragment and does not
  eliminate future operational monitoring.

## Alternatives

### stable-ts 2.19.1

Rejected. It preserved all text but emitted 188 zero-duration intervals. Its own
bounded deterministic silence adjustment left all 188 unchanged, 29 collapsed
runs had no free adjacent gap for a local repair, and upstream was archived on
2026-05-30 with development paused indefinitely.

### whisper.cpp large-v3 DTW

Rejected for this role. The tested path retranscribed audio with 19.456% WER,
its DTW value is an experimental point anchor, and decoder intervals included 75
zero-duration words. It remains an operational coarse-SRT ASR fallback, not the
canonical existing-transcript aligner.

### MLX Whisper

Not applicable. The available path performs ASR transcription with word
timestamps and does not expose a relevant supplied-transcript forced-alignment
path.

### Build a custom forced aligner

Rejected. WhisperX satisfies the requirement, so custom algorithm development
would violate the accepted `ADOPT -> ADAPT -> BUILD` principle.
