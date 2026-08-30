# Canonical Evidence Schema v1

Date: 2026-08-27

Issue: #40

Verdict: `CANONICAL_EVIDENCE_SCHEMA_V1_ACCEPTED`

## Outcome

Canonical Evidence Schema v1 is frozen as a machine-readable architecture
contract. The canonical representation is one UTF-8 JSON bundle conforming to
`schemas/canonical_evidence_v1.schema.json`; TXT, SRT, DOCX and Markdown are
derived views and never competing sources of truth.

The contract is executable through
`schemas/validate_canonical_evidence_v1.py`. It validates reference integrity,
revision/hash consistency, ranges, locators, timing semantics and deterministic
array order without introducing a runtime dependency. A standard JSON Schema
Draft 2020-12 implementation may additionally validate record shapes.

This milestone does not ingest a production source, install WhisperX in the
production environment or build exports. Those operations belong to
`word_timeline_mvp_one_controlled_source`.

## Goals and non-goals

The goal is the smallest shared, deterministic contract that preserves semantic
authority and gives Word, benchmark, Topic and later knowledge consumers an
auditable path to a source-appropriate locator. The schema must be local-first,
diffable, migration-aware and speaker-ready.

Non-goals are production ingestion/export, diarization, full Concept/Knowledge
ontology, persistence/database selection, and any Topic Engine or Gold change.

## Frozen artifact model

One artifact has `artifact_type = seminartext.canonical_evidence` and
`schema_version = 1.0.0`. It contains one `Project` and normalized ordered
collections:

| Collection | Entity and role |
| --- | --- |
| `sources` | Source identity, media/document kind, content hash and duration where meaningful |
| `transcript_revisions` | Immutable semantic-text revisions and authority state |
| `cues` | Imported/coarse provenance units with exact transcript character spans |
| `alignment_runs` | Reproducible timing process tied to exact source and transcript hashes |
| `words` | Canonical transcript units, character spans and explicit timing state |
| `benchmark_segments` | Deterministic contiguous word ranges |
| `topics` | Ordered contiguous segment ranges with matching word bounds |
| `evidence_refs` | Forward-compatible entity-to-source locator references |

Words are records in the bundle's `words` collection, not embedded copies under
cues or topics. This avoids update ambiguity and lets every segment/topic point
to the same stable word coordinate system. JSONL may be introduced as a
lossless physical transport after v1, but is not a second canonical model.

## Entity contract

### Project

`id`, human title and lifecycle status. A v1 bundle contains exactly one
project. `Project` is the repository-level seminar container; introducing a
separate Seminar entity would be a versioned extension rather than an aliasing
copy in v1.

### Source

Every source belongs to the project and has stable ID, deterministic sequence,
kind, title, byte-content SHA-256 and lifecycle. Audio/video require positive
`duration_seconds`; PDF/PPTX/DOCX/text/image sources require it to be `null`.
Paths are deliberately absent and cannot participate in identity.

### Transcript revision

A transcript revision contains immutable `canonical_text`, its UTF-8 SHA-256,
source link, monotonically increasing revision number, optional parent,
revision kind and authority.

- `asr` is machine-produced candidate text.
- `verified` is human-verified authoritative text.
- `corrected` is a later semantic correction and creates a new revision.
- New revisions record `transcript_provenance` with origin, generation method,
  verification state, exact character ranges and reviewer. Machine-unverified
  and selectively verified revisions remain candidate/active; only a
  fully-human-verified revision may be authoritative/verified.
- `authority = authoritative` identifies the semantic source of truth.
- clean text, SRT, DOCX and Markdown are exports, not revisions.
- alignment is an `alignment_run`, not a transcript revision.

Only one revision per source may be authoritative in a bundle. A correction
never mutates an old revision in place.

### Cue / provenance unit

A cue retains imported ASR/SRT provenance with exact transcript character span,
text and optional source locator. Coarse cue time can explain where an unaligned
word came from, but cannot be copied into that word's timing fields.

### Alignment run

An alignment run is bound to:

- source ID and source-content SHA-256;
- transcript revision ID and canonical-text SHA-256;
- aligner/version;
- model/revision/model SHA-256;
- configuration SHA-256;
- `valid`, `superseded` or `stale` status.

WhisperX alignment-only is recorded as `forced_alignment`. If source bytes or
transcript text change, a prior run cannot remain valid for the changed object.
Alignment output can enrich the exact revision it was run against; it cannot
replace or silently edit semantic text.

### Word

Every Word has:

- stable `id` (the entity's `word_id`), source and transcript links, and
  zero-based `sequence`;
- exact `text`, `char_start`, `char_end` in original canonical text;
- optional `normalized_text` that never replaces original text;
- one or more `source_cue_ids`;
- nullable `start_seconds`, `end_seconds`, `confidence`, `speaker_id`;
- explicit `alignment_status`;
- controlled `timing_provenance`;
- deterministic `qa_flags` and lifecycle status.

Timing combinations are closed:

| `alignment_status` | Timing | Provenance | Required detail |
| --- | --- | --- | --- |
| `source_timed` | positive interval | `source_exact` | no alignment run |
| `aligned` | positive interval | `forced_alignment` | valid exact-hash alignment run |
| `estimated` | positive interval | `derived_estimate` | named estimation method |
| `unaligned` | both values `null` | `unavailable` | no alignment run |

An unaligned word preserves ID, text, character span, order and cue provenance.
It gets `unaligned_review_required`; no cue bound, midpoint or proportional
interval may be fabricated as word timing.

### BenchmarkSegment

A segment belongs to one transcript revision and stores ordered inclusive
`word_start_id` / `word_end_id` plus exact `word_count`. The range must be
contiguous in Word sequence. Segment records are deterministic coordinate
groups; they do not duplicate text or timing.

### Topic

A topic belongs to one transcript revision and topic set. It references an
ordered contiguous list of benchmark segments and repeats only the first/last
word IDs as an auditable range assertion. The word bounds must exactly equal
the referenced segment bounds. `origin` distinguishes Gold, verified manual,
explicit semi-automatic and automatic draft topics.

### EvidenceRef

EvidenceRef is the minimal forward-compatible link from a canonical entity to a
Project, Source, optional transcript revision and typed source locator. Its
target can be a source, transcript revision, cue, word, segment or topic.

Locators are discriminated and source-compatible:

- audio/video: `time_interval`;
- PDF: `pdf_page_range`;
- PPTX: `pptx_slide_range`;
- DOCX/plain text: `text_char_range`;
- image: normalized `image_region`.

Non-timed sources never receive fake timestamps. New locator kinds require a
schema-version change, while additional optional metadata can be introduced by
a backward-compatible minor revision.

## Stable ID and lifecycle rules

IDs use lowercase ASCII namespaced strings and are globally unique within a
bundle. Producers derive them from persistent domain keys, content identity and
deterministic ordinals—never temporary paths, machine names or wall-clock time.

Recommended recipes are:

```text
project_<persistent-project-key>
source_<project-key>_<persistent-source-key>
transcript_<source-key>_r<revision-number>
<transcript-id>:cue:<zero-padded-sequence>
<transcript-id>:word:<zero-padded-sequence>
segment_<transcript-key>_<zero-padded-sequence>
topic_<transcript-key>_<topic-set-key>_<zero-padded-sequence>
evidence_<persistent-target-and-locator-key>
```

Re-exporting the same revision preserves IDs. Timing-only re-alignment preserves
Word IDs and creates/replaces an alignment-run reference. Semantic correction
creates a new transcript revision; because its character coordinate system may
change, its cue/word/segment/topic IDs are newly derived. Old records remain
addressable as `superseded`/`invalidated`, not silently repointed.

Moving/renaming a file or changing descriptive metadata preserves Source ID.
Replacing source bytes creates a new Source ID in v1 and supersedes the old
Source; an equivalent-byte re-import preserves both ID and content hash. This
keeps source identity unambiguous without adding a SourceRevision entity.

Lifecycle is explicit: `draft`, `active`, `verified`, `superseded`,
`invalidated`, `archived`. Removal from a current view does not authorize ID
reuse.

## Machine-checkable invariants

The schema and companion validator enforce:

1. required record shapes, enums, stable-ID syntax and SHA-256 syntax;
2. globally unique entity IDs and no orphan/cross-source references;
3. canonical text hashes and valid parent/revision order;
4. at most one authoritative transcript revision per source;
5. exact cue/word text-to-character-span equality;
6. contiguous zero-based sequence inside every ordered entity group;
7. positive, non-inverted timed intervals within source bounds;
8. strictly null word timing for `unaligned`;
9. alignment run hashes equal the referenced source/transcript hashes;
10. no valid alignment attached to superseded text;
11. segment word ranges are contiguous, ordered and count-consistent;
12. topic segment references are contiguous and match topic word bounds;
13. typed source-compatible EvidenceRef locators;
14. deterministic collection ordering and sorted-key canonical serialization.

The canonical writer uses UTF-8, two-space indentation, lexicographically sorted
object keys and one trailing newline. Collection order is defined by parent,
sequence and ID as encoded in the validator. Hashing or signing a bundle uses
those canonical bytes.

## Concrete examples

The complete internally consistent example is
`tests/fixtures/canonical_evidence_v1/valid_bundle.json`. It includes:

- aligned Russian word `Сегодня` at original span `[0, 7)` with WhisperX
  `forced_alignment` provenance;
- unaligned Russian word `о` with preserved text/span/cue, null timing and QA;
- two contiguous benchmark segment ranges and one topic over both;
- a video EvidenceRef with a real time interval;
- a PDF EvidenceRef with page 3 and no timestamp.

Focused negative cases are declared in
`tests/fixtures/canonical_evidence_v1/invalid_cases.json` and executed by
`tests/test_canonical_evidence_schema_v1.py`.

## Resolved design questions

1. **Artifact/model:** one versioned Canonical Evidence JSON bundle per project
   snapshot; no competing canonical transcript file.
2. **Embedded vs JSONL:** normalized record collections; Words are not embedded.
   JSONL is deferred as a lossless transport/profile.
3. **IDs:** deterministic namespaced IDs from persistent keys/revisions/ordinals;
   never temp paths or timestamps.
4. **Revisions:** semantic ASR/verified/corrected text is immutable revision
   history; clean formats are exports; alignment is a separate run.
5. **Stale alignment:** exact source/text hashes gate validity; changed text
   requires a new revision and invalidates/supersedes the old run.
6. **Unaligned:** retain text, ID, spans and cue provenance; native timing stays
   null and is never inferred silently.
7. **Segment mapping:** inclusive first/last Word IDs plus exact count over a
   contiguous sequence.
8. **Topic mapping:** ordered contiguous segment IDs plus asserted matching Word
   range.
9. **EvidenceRef:** typed target plus typed source-compatible locator, supporting
   media, PDF, PPTX, DOCX/text and image evidence without fake time.
10. **Documentation:** this report is normative rationale, JSON Schema is the
    shape contract, the companion validator defines cross-record invariants, and
    ADR 0004 freezes the architectural decision.

## Versioning and migration contract

`schema_version` follows semantic versioning:

- patch: clarification or validator bug fix that does not change accepted data;
- minor: backward-compatible optional fields/enums only when old readers can
  safely ignore them;
- major: required-field, identity, timing, locator or semantic changes.

A migration must be deterministic and idempotent, declare source/target schema
versions, preserve original IDs and provenance where semantics are unchanged,
emit an audit report, validate the result, and never overwrite its input. No
migration implementation is part of v1.

Legacy transcripts may later import as `asr` or `verified` revisions, with cue
provenance retained. Their Words remain `unaligned` unless source-native exact
timing or a valid forced-alignment run exists; legacy SRT interpolation does not
upgrade timing guarantees. Active machine revisions may use a native alignment
run, but their evidence lifecycle remains `active` and `review_required`.
`speaker_id` is already nullable, so adding speaker
records/metadata can be a backward-compatible minor extension while legacy
values remain null.

## Acceptance and next milestone

The schema artifact, executable validator, valid/invalid fixtures, tests and ADR
agree on the frozen contract. Therefore this architecture milestone is complete.
The next milestone is `word_timeline_mvp_one_controlled_source`, where an adapter
may populate this schema for one controlled target-corpus source.

Explicitly unchanged: Topic Engine algorithms, Gold A/B/C, Dataset D/F policy,
Dataset E exclusion, production WhisperX dependencies, Obsidian/Knowledge
Engine, database/graph choices and production export commands.
