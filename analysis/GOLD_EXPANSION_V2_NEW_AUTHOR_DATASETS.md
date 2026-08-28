# Gold Expansion v2 — new author datasets

Issue: #50

Milestone scope: prediction-independent preparation of two new author-corpus
video candidates for later human Gold annotation.

Decision date: 2026-08-28

## Executive decision

Both supplied files pass the provenance/speaker and topic-agnostic Source
Quality gates. Their semantic transcripts remain machine-generated ASR and are
therefore **provisional, not verified**. Canonical Evidence Schema v1 bundles
and six deterministic annotation packets per candidate are prepared without
running a Topic Engine candidate. The packets contain no machine-authored topic
boundaries, titles, or summaries.

The resulting milestone verdict is:

- G1 `Лечебные ножи. Введение`: **READY_FOR_GOLD_ANNOTATION**;
- G2 `Магия сигил декабрь 2022`: **READY_FOR_GOLD_ANNOTATION**.

The recommended role scheme for Product Owner review is **OPTION A**:

- G1 -> proposed `DEVELOPMENT`;
- G2 -> proposed `FROZEN_VALIDATION_CANDIDATE`.

These are proposals only. Neither role is frozen by this report. G2 is the
stronger independent-validation candidate because it is substantially longer,
has greater speech/workshop and topic diversity, and is thematically farther
from the existing A/B/C set. G1 is shorter and cheaper to review iteratively,
with more conceptual overlap with the health/emotion/energy vocabulary already
represented by A and B. No algorithm output or performance informed this
assessment.

## Gates and method shared by G1/G2

The Product Owner supplied both exact source paths explicitly as target
author-corpus candidates. That provenance, the created SeminarText project and
source metadata, and transcript content are mutually consistent. No voice
biometrics were performed. No matching pre-existing project, transcript, SRT,
or canonical artifact was found, so each source was registered in a new project
through the normal `seminartext init` / `project-add --video-link` workflow.
Both project integrity checks pass.

The normal SeminarText 3.0 transcription workflow produced Russian SRT using
whisper.cpp `large-v3` with Silero VAD. Fresh, bounded 25-second ASR checks at
the beginning, middle, and end confirmed that each SRT belongs to its source.
The canonical semantic text is exactly the SRT text; WhisperX did not replace
or revise it.

Word intervals were populated by WhisperX 3.8.6 in its accepted alignment-only
role using `jonatasgrosman/wav2vec2-large-xlsr-53-russian`, revision
`2329100508896c6d9b157019803ab5601e6f3406`, model artifact SHA-256
`d1cdb1a7921de7d363f967a9b0101a713602e109dba62b6f3f9ae2e0b2df0c1c`.
Every unaligned token retains its exact character span and cue provenance with
null timing. No word interval was synthesized.

The population runner validates input hashes, builds deterministic IDs and
exact character spans, validates against Canonical Evidence Schema v1 and its
cross-record validator, then repeats population and requires byte-identical
output. Transcript revisions and all derived records remain `draft`, with
`revision_kind=asr`, `authority=candidate`, and nullable `speaker_id`.

## G1 — Лечебные ножи. Введение

### 1–5. Source identity, provenance, and project

- Exact path: `/Users/yurielokhin/Копия с Transcend/Видео/Лечебные ножи. Введение.mp4`
- Filename: `Лечебные ножи. Введение.mp4`
- Size: 279,145,404 bytes
- SHA-256: `dbc6b6e438593ec91a93a1150f786c0bb046e0d5cca54b2f570a293ecedd4546`
- Duration: 5,436.400 seconds (`01:30:36.400`)
- Media: QuickTime/MOV MP4; H.264 High 1760x900 at 25 fps; AAC-LC mono,
  32 kHz, 126,250 bit/s
- Language: Russian
- SeminarText project: `/Users/yurielokhin/Documents/seminartext_projects/Лечебные ножи`
- Project source: `video_001`, symlink registration; integrity check `PASS`
- Prior matching project/artifacts: none found before creation
- Target-corpus/speaker status: `TARGET_AUTHOR_CORPUS_CONFIRMED` from Product
  Owner provenance and project/source context; no biometric inference

### 6–9. Transcript and Source Quality Gate

The full SRT is new machine ASR, lifecycle
`ASR_PROVISIONAL_HUMAN_REVIEW_REQUIRED`; SRT SHA-256
`c6f63022991ff8cf50621c6b25d82b6154b7fce3bb719fc68982546723e471c3`.
It contains 707 cues and ends at 5,434.760 seconds, giving 0.999698 source-end
coverage. Cue duration statistics are median 7.550 s, p90 11.034 s, p95
12.591 s, maximum 26.360 s. There are 15 overlaps (maximum 0.130 s), four
positive gaps (maximum 1.620 s), and no gap over 30 s. All 707 normalized cues
are unique. No repeated ASR loop, collapse, large missing span, or obvious
semantic corruption was observed.

The media fully decodes with zero errors. Mean/max volume are -23.1/-4.4 dB;
45 silences of at least two seconds total 155.616 seconds, with a 13.598-second
maximum. Speech remains available throughout. Beginning/middle/end fresh-ASR
checks match the SRT (token Jaccard 0.7692, 0.4091, and 0.4510). No transcript
repair or production-default change was required.

**Source Quality Gate: `SOURCE_READY`.**

### 10–13. Canonical Evidence, Word Timeline, and determinism

- Bundle: `analysis/gold_expansion_v2/healing_knives/canonical_evidence_bundle.json`
- Canonical bundle SHA-256:
  `1ade5a9de967e38ea94e05ace21d34064e1aebe4e35a0fc5f1a85e4f91c925f3`
- Canonical words: 7,934
- Native forced-alignment intervals: 7,841 (98.8278%)
- Explicit unaligned words: 93 (1.1722%), null timing retained
- JSON Schema validation: `PASS`
- Cross-record validation: `PASS`
- Repeated population: byte-identical `PASS`
- Bounded repeated alignment result SHA-256:
  `7bedeabcc5e2559d2c5bf290ba322b080316361e7c4c9b90a918667cd76497db`
  in both runs

Canonical readiness means the provisional transcript is reviewable with native
word evidence. It does not promote ASR semantics to verified or Gold.

### 14–19. Independence, proposed role, windows, and remaining work

G1 is a previously untuned source and was not used by any Topic Engine
candidate. It introduces artifact-centred instruction around therapeutic
knives, diagnostics, practical use, safety, and seminar logistics. This is
distinct from A (`Стресс код`), B (`Заблокированные эмоции`), and C (`И Цзин`),
although its health/emotion/energy vocabulary is closer to A/B than G2 is.
Its 90-minute duration is suitable for lower-cost iterative annotation and
development diagnostics. Proposed role: **`DEVELOPMENT`**, subject to Product
Owner acceptance.

The existing A/B/C-compatible objective policy splits completed cues into
sequential 12-minute windows, keeps windows at least 10 minutes long, and
chooses six evenly spaced positions. It selected source windows 1, 2, 3, 5, 6,
and 7:

| Packet | Absolute interval |
|---|---|
| `g1_video_001_window_01` | 00:00:03.900–00:12:06.250 |
| `g1_video_001_window_02` | 00:12:06.250–00:24:10.060 |
| `g1_video_001_window_03` | 00:24:10.060–00:36:17.560 |
| `g1_video_001_window_05` | 00:48:20.580–01:00:26.100 |
| `g1_video_001_window_06` | 01:00:26.100–01:12:26.930 |
| `g1_video_001_window_07` | 01:12:26.930–01:24:33.910 |

All six packets are in
`analysis/gold_expansion_v2/healing_knives/gold_annotation_packets.json` and
contain the source ID, absolute timestamps, word range, readable cue transcript
and cue provenance. Boundary/title/summary fields are blank and status is
`GOLD_ANNOTATION_REQUIRED`.

Remaining Product Owner work is to accept or change the proposed role, arrange
human transcript verification as needed for Gold, complete Domain Owner topic
annotation, review/accept the Gold, and then freeze the role and windows before
any benchmark. **Final verdict: `READY_FOR_GOLD_ANNOTATION`.**

## G2 — Магия сигил декабрь 2022

### 1–5. Source identity, provenance, and project

- Exact path: `/Users/yurielokhin/Копия с Transcend/Видео/Магия сигил декабрь 2022.mp4`
- Filename: `Магия сигил декабрь 2022.mp4`
- Size: 1,671,180,535 bytes
- SHA-256: `79acf478b5036f3ca831a87af9eaa72826a7b48c6f7a9a25b3c81ecdf46404ee`
- Duration: 17,876.320 seconds (`04:57:56.320`)
- Media: QuickTime/MOV MP4; H.264 High 1760x900 at 25 fps; AAC-LC mono,
  32 kHz, 126,250 bit/s
- Language: Russian
- SeminarText project: `/Users/yurielokhin/Documents/seminartext_projects/Магия сигил`
- Project source: `video_001`, symlink registration; integrity check `PASS`
- Prior matching project/artifacts: none found before creation
- Target-corpus/speaker status: `TARGET_AUTHOR_CORPUS_CONFIRMED` from Product
  Owner provenance and project/source context; no biometric inference

### 6–9. Transcript and Source Quality Gate

The full SRT is new machine ASR, lifecycle
`ASR_PROVISIONAL_HUMAN_REVIEW_REQUIRED`; SRT SHA-256
`8666d61e1dc5580fedd8d3cb169ba8aaf77125339977beb8a7ec8165de59e41b`.
It contains 2,421 cues and ends at 17,875.880 seconds, giving 0.999975
source-end coverage. Cue duration statistics are median 7.010 s, p90 10.590 s,
p95 12.540 s, maximum 173.930 s. There are 39 overlaps (maximum 0.130 s), 25
positive gaps (maximum 9.840 s), and no gap over 30 s. 2,382 of 2,421 normalized
cues are unique (0.983891). Eleven cues exceed 30 seconds; the longest is
02:20:52.000–02:23:45.930 across a documented long pause. This is a cue-level
timing anomaly, not a semantic loop; native word alignment avoids assigning
synthetic per-word coverage across that interval. No ASR collapse or large
missing transcript span was observed.

The media fully decodes with zero errors. Mean/max volume are -24.8/-0.1 dB;
280 silences of at least two seconds total 1,190.840 seconds, with a
167.828-second maximum. The near-peak maximum and long pauses are documented,
but no corruption blocks speech review. Beginning/middle/end fresh-ASR checks
match the SRT (token Jaccard 0.6905, 0.3714, and 0.6939). No semantic repair or
production-default change was required.

**Source Quality Gate: `SOURCE_READY`.**

### 10–13. Canonical Evidence, Word Timeline, and determinism

- Bundle: `analysis/gold_expansion_v2/sigil_magic_december_2022/canonical_evidence_bundle.json`
- Canonical bundle SHA-256:
  `144935de132654947298c38c3fc8b081d346afaebe97301a94443780f0064ff6`
- Canonical words: 28,795
- Native forced-alignment intervals: 28,429 (98.7289%)
- Explicit unaligned words: 366 (1.2711%), null timing retained
- JSON Schema validation: `PASS`
- Cross-record validation: `PASS`
- Repeated population: byte-identical `PASS`
- Full-source alignment result SHA-256:
  `a54fc99d1d2eea360f87110736fd09061fc2fe67a07441caa375cd3011e1df83`
  (one bounded run; determinism is enforced by repeated byte-identical
  population from this hash-locked evidence)

Canonical readiness means the provisional transcript is reviewable with native
word evidence. It does not promote ASR semantics to verified or Gold.

### 14–19. Independence, proposed role, windows, and remaining work

G2 is a previously untuned source and was not used by any Topic Engine
candidate. Its sigil theory, construction practice, extended worked exercises,
participant interaction, and almost five-hour seminar structure differ strongly
from A (`Стресс код`), B (`Заблокированные эмоции`), and C (`И Цзин`). Its
duration and mixed lecture/workshop/question speech provide the broader
independent evidence surface. Proposed role:
**`FROZEN_VALIDATION_CANDIDATE`**, subject to Product Owner acceptance and later
manual-Gold completion. It is not yet `FROZEN_VALIDATION`.

The same fixed 12-minute, minimum-10-minute, evenly-spaced policy selected
source windows 1, 6, 10, 15, 19, and 24:

| Packet | Absolute interval |
|---|---|
| `g2_video_001_window_01` | 00:00:05.400–00:12:11.920 |
| `g2_video_001_window_06` | 01:00:19.810–01:13:02.420 |
| `g2_video_001_window_10` | 01:49:14.600–02:01:29.590 |
| `g2_video_001_window_15` | 02:49:50.090–03:01:53.120 |
| `g2_video_001_window_19` | 03:38:04.280–03:50:08.630 |
| `g2_video_001_window_24` | 04:38:29.400–04:50:30.000 |

All six packets are in
`analysis/gold_expansion_v2/sigil_magic_december_2022/gold_annotation_packets.json`
and contain the source ID, absolute timestamps, word range, readable cue
transcript and cue provenance. Boundary/title/summary fields are blank and
status is `GOLD_ANNOTATION_REQUIRED`.

Remaining Product Owner work is to accept or change the proposed role, arrange
human transcript verification as needed for Gold, complete Domain Owner topic
annotation, review/accept the Gold, and freeze G2 before any benchmark. If
accepted for independent validation, parameters must not change after its
result is viewed. **Final verdict: `READY_FOR_GOLD_ANNOTATION`.**

## Contamination safeguards and freeze policy

Preparation code reads only the supplied media, provisional SRT, accepted
alignment evidence, and fixed time-window policy. It does not import or invoke
TreeSeg, Local Peak, PELT/ruptures, Chonkie, LLM boundary prediction, embeddings,
or any other Topic Engine candidate. Window selection reads neither predictions
nor perceived algorithm difficulty. No final Gold boundary was authored by
Codex/LLM.

Gold A/B/C and Dataset C/D/E artifacts were neither inputs nor modified. Dataset
C remains frozen/closed, Dataset D remains `LOCKED_TEST` and unused, and Dataset
E remains excluded. The production Topic Engine is unchanged. The first G1/G2
algorithm run remains a separate future milestone after manual Gold completion,
Product Owner acceptance, and role/window freeze.

Gold Expansion v2 is recorded as a third, parallel Data/Evaluation track. It
does not replace or reorder the two primary next actions: Obsidian Knowledge
Prototype and the bounded TreeSeg adaptation / Global Seminar Structure POC.
