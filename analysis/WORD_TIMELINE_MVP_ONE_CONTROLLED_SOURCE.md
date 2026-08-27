# Word Timeline MVP on One Controlled Source

Date: 2026-08-27

Issue: #42

Verdict: `WORD_TIMELINE_MVP_ACCEPTED`

## Outcome

SeminarText now has a real, deterministic population path from one immutable
verified target-corpus transcript plus frozen WhisperX alignment-only evidence
to a valid `seminartext.canonical_evidence` v1 bundle.

The path preserves all 1434 semantic tokens and exact character spans. It maps
1432 WhisperX native intervals as `forced_alignment` and preserves the two known
unsupported words as explicitly `unaligned` with null timing. No ASR,
retranscription, interpolation or semantic normalization occurs.

The generated artifact passes both JSON Schema Draft 2020-12 and the repository
cross-record validator. Two complete population runs are byte-identical.

## Controlled source and frozen provenance

The MVP reuses the exact Issue #38 target-author fragment; no new dataset or
speaker was selected.

| Property | Value |
| --- | --- |
| Project | `Стресс код` / `project_stress_code` |
| Existing source identity | `video_001` |
| Canonical source ID | `source_stress_code_video_001` |
| Full source | `Стресс Код, декабрь 2022, День 1` |
| Full-source duration | 16357.56 s |
| Full-source SHA-256 | `f4d4b81f4997a12aad5dab0890b6137387d355b24de79fe7e728b003cf0a460a` |
| Controlled interval | `[600.0, 1496.78]` s in the full source |
| Extracted audio SHA-256 | `6cd44ca07c9ba332e4285b90268f20c8329ecdae39e933ebbae7bd222a0b1217` |
| Verified transcript SHA-256 | `728981fc34eea6e47b6cd68c332c674a2c478b21b38f76f75fbb81d3e915c715` |
| Frozen cues SHA-256 | `3f3ab7b6cf29bc1d353ce2066eac3a049ca1d2cfcf96c6c4c360211886a7990e` |

The full source hash and duration were rechecked against the local controlled
source during this milestone. Canonical data contains no local or temporary
filesystem path.

Alignment evidence is the Issue #38 result produced by WhisperX 3.8.6
alignment-only with model
`jonatasgrosman/wav2vec2-large-xlsr-53-russian` at revision
`2329100508896c6d9b157019803ab5601e6f3406`. The model SHA-256 is
`d1cdb1a7921de7d363f967a9b0101a713602e109dba62b6f3f9ae2e0b2df0c1c`.

`analysis/word_timeline_mvp/frozen_whisperx_alignment.json` is a deterministic
151 KB evidence projection of the preserved 3.6 MB experimental output. It
retains all 1432 aligned Word records, fragment/source/transcript hashes,
alignment configuration and both repeat-run result hashes. Its SHA-256 is
`c68ad139278edb81daeaa7f22b7f233fa2cf1ca89e682f53cdfcdc4cadf17786`;
the original experimental output SHA-256 remains recorded as
`6fa19362f2273bb4db02a99bb966d914a726d0117cace38b3b017a6b15450f80`.

Dataset E was not used. Dataset D and Dataset F were not opened or changed.

## Implementation path

The narrow developer runner is
`analysis/word_timeline_mvp/build_canonical_evidence.py`. Inputs are pinned by
`analysis/word_timeline_mvp/population_manifest.json`.

The runner:

1. verifies the transcript, cue and alignment-evidence file hashes;
2. verifies source/fragment/transcript/alignment/model/config provenance;
3. requires at least two identical frozen WhisperX result hashes;
4. tokenizes the immutable transcript only as exact non-whitespace spans;
5. accepts alignment words only as an exact transcript-token subsequence;
6. rejects insertions/substitutions and checks the frozen unaligned-token set;
7. maps each Word to its exact cue and character span;
8. converts fragment-relative native intervals to full-source time by the
   frozen +600.0 s offset;
9. creates deterministic 50-Word benchmark ranges without Topic semantics;
10. creates five distributed Word-to-source EvidenceRefs;
11. runs the cross-record validator and, when requested, Draft 2020-12 schema
    validation;
12. emits sorted-key, two-space UTF-8 canonical JSON with one trailing LF.

It does not import WhisperX and does not run ASR. Reproducing the upstream
alignment itself remains the isolated Issue #38 runner/environment described by
ADR 0003; population from the frozen accepted alignment is dependency-light.

## Generated canonical artifact

Artifact:
`analysis/word_timeline_mvp/canonical_evidence_bundle.json`

Canonical SHA-256:
`8b1a5b1ffced298cd21a8ede3dbe61d82a00950f2de6da1ba186ffae4cd93d14`

| Entity collection | Count |
| --- | ---: |
| Project | 1 |
| Source | 1 |
| TranscriptRevision | 1 |
| Cue | 124 |
| AlignmentRun | 1 |
| Word | 1434 |
| BenchmarkSegment | 29 |
| Topic | 0 |
| EvidenceRef | 5 |

No Topic was invented. The 29 benchmark records are deterministic contiguous
technical ranges of 50 Words (last range: 34) and cover every Word exactly once.
They prove range consumption only; they are not Gold boundaries.

## Semantic conservation

- authoritative transcript bytes and SHA-256 are unchanged;
- 1434/1434 canonical Word texts equal their exact transcript substrings;
- Word sequence is exactly the transcript non-whitespace token order;
- WhisperX output is an exact 1432-token subsequence;
- substitutions: 0;
- insertions: 0;
- semantic deletions from canonical data: 0;
- alignment omissions: exactly 2 (`думаешь,`, `что`);
- `normalized_text` remains null, so no alignment normalization can replace
  original text;
- all `speaker_id` values are null; diarization was not introduced.

## Timing integrity

| Check | Result |
| --- | --- |
| Aligned Words | 1432 |
| Unaligned Words | 2 |
| Coverage | 99.8605% |
| Negative/zero intervals | 0 / 0 |
| Inversions | 0 |
| Adjacent overlaps | 0 |
| Outside full source / controlled fragment | 0 / 0 |
| Minimum positive duration | 0.02 s |
| Maximum duration | 9.565 s |
| First aligned source time | 600.14 s |
| Last aligned source time | 1489.194 s |

The two unaligned Words retain stable IDs, text, spans, order and cue links.
Their `start_seconds`, `end_seconds` and confidence are null; provenance is
`unavailable`; QA contains `unaligned_review_required`. The enclosing cue time
is provenance only and is never copied into Word timing.

WhisperX intervals are explicitly `forced_alignment`, not `source_exact`.
There are 155 low-confidence QA flags and three unusually-long-interval flags;
these preserve review signals without invalidating otherwise native positive
intervals.

## Referential integrity

The bundle passes all Canonical Evidence v1 cross-record checks:

- stable IDs are globally unique and deterministically ordered;
- every Source, TranscriptRevision, Cue, AlignmentRun, Word, segment and
  EvidenceRef link resolves;
- full-source, fragment, transcript, cue, model and configuration hashes agree;
- all cue and Word character ranges resolve to exact semantic substrings;
- all 29 benchmark ranges are contiguous and count-exact;
- EvidenceRef locator types match the video source and source bounds;
- no Topic references exist because Topic content was intentionally omitted.

## Determinism

The original WhisperX evidence contains two complete runs with the same result
hash:
`cc4fcd6eff2a7b029694a67ab19794f7d023d6ddc0752a1858fa97b508dc8674`.

The complete population runner was executed twice from the same pinned inputs.
Both outputs are byte-identical, including semantic text, IDs, ordering, hashes,
references and serialized bytes. Both equal the committed artifact SHA-256
`8b1a5b1ffced298cd21a8ede3dbe61d82a00950f2de6da1ba186ffae4cd93d14`.
There are no intentionally variable fields or timestamps.

## Evidence-navigation proof

Five refs span the controlled fragment. Timecodes are absolute positions in the
full `video_001` source.

| Word sequence / text | Evidence path | Full-source interval |
| --- | --- | --- |
| 3 / `быть` | Word → `source_stress_code_video_001` | 602.603–602.763 s |
| 299 / `вопросом,` | Word → source | 822.531–823.695 s |
| 696 / `есть` | Word → source | 1049.640–1049.800 s |
| 1070 / `И,` | Word → source | 1268.930–1269.090 s |
| 1393 / `Хорошо,` | Word → source | 1469.557–1469.857 s |

Each EvidenceRef locator exactly equals its target Word interval and carries the
same Source and TranscriptRevision identity. The distributed anchors are the
same positions used in the Issue #38 manual signal audit.

## Automated verification

`tests/test_word_timeline_mvp.py` covers:

- byte-identical repeat population and committed-artifact hash;
- Draft 2020-12 plus cross-record validation;
- entity counts and full semantic/span conservation;
- positive monotonic non-overlapping source timing;
- explicit null timing for both unaligned Words;
- complete non-overlapping benchmark range coverage;
- five exact distributed navigation refs;
- rejection of alignment substitutions;
- rejection of changed verified-transcript hashes;
- two CLI runs producing identical bytes.

The existing Canonical Evidence tests remain unchanged and pass with the new
tests. The full repository suite passes (`36 passed`).

## Limitations and deferred production concerns

- This is one frozen target-corpus source fragment, not general project
  migration or batch processing.
- The source media and 27 MB extracted WAV are not duplicated in Git; content
  hashes and frozen compact alignment evidence make identity auditable.
- WhisperX packaging remains isolated; no heavy ML dependency was added to the
  production environment.
- The adapter is not wired into `project-transcribe` or a broad public CLI.
- Benchmark ranges are technical MVP chunks, not Topic Gold or automatic Topic
  output.
- Diarization, document ingestion, exports, Obsidian, Knowledge Engine,
  databases and multi-source population remain deferred.
- Dataset D stays locked; Dataset E stays excluded; Dataset F stays quarantined.

## Final verdict

`WORD_TIMELINE_MVP_ACCEPTED`

The accepted alignment and schema foundations work together on real controlled
evidence without semantic change or false timing. The minimum canonical
Evidence Foundation is sufficient to advance to the parallel split already
defined by ADR 0002:

- Golden Seminar Knowledge Slice → Obsidian Knowledge Prototype → Product
  Review;
- External Topic/Semantic Segmentation Survey → Baseline Challenge → Topic
  Engine improvement.

These are parallel tracks; neither becomes a new linear prerequisite for the
other.
