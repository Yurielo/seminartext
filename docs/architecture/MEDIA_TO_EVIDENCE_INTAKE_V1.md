# Selected media to pending Topic review v1

`project-media-review` processes explicitly selected registered local media:

`project-transcribe → accepted WhisperX alignment-only producer → assured TranscriptRevision → Canonical Evidence → existing batch Topic review → REVIEW_REQUIRED`.

The manifest remains version 1.0.0. Every source must already be registered in
its project's `sources.json`, and its selected path must equal that registered
local media path. IDs, source hashes and registry bytes are bound at preparation.
No discovery, semantic acceptance, Concept/Knowledge admission, Issue #68 or S2
advancement is performed.

```json
{"artifact_type":"seminartext.media_to_review_manifest","schema_version":"1.0.0","entries":[{"id":"source-a","project":"/absolute/project","source_id":"video_001","media":"/absolute/project/source/video/input.mp4"}]}
```

```bash
./seminartext project-media-review prepare /work/intake --manifest /work/media.json
./seminartext project-media-review run /work/intake
./seminartext project-media-review status /work/intake
./seminartext project-media-review inspect /work/intake
./seminartext project-media-review resume /work/intake
./seminartext project-media-review retry /work/intake --entry source-a
```

## Existing runtimes and producer reuse

Core uses its existing Python 3.14.6 environment. Alignment selects
`SEMINARTEXT_ALIGNMENT_PYTHON` or `~/.seminartext-alignment-venv/bin/python` and
probes that interpreter's own CPython 3.13.15 identity and all ten accepted
pinned package versions. It never checks for WhisperX in the Core interpreter.
No installation, environment creation, dependency change or model download is
performed.

`media_alignment.py` is a thin runtime/model selection and I/O adapter. A child
process executes the unchanged historical
`analysis/word_alignment_decision/run_whisperx_existing_text.py` with one run.
It supplies its existing model-loader call with the exact already-cached
Russian model snapshot and `model_cache_only=True`; the producer's alignment
algorithm is unchanged. HF/Transformers offline flags are set. Russian NLTK
Punkt data is required before inference, and the child forbids NLTK downloads.

The model is `jonatasgrosman/wav2vec2-large-xlsr-53-russian`, revision
`2329100508896c6d9b157019803ab5601e6f3406`, weight SHA-256
`d1cdb1a7921de7d363f967a9b0101a713602e109dba62b6f3f9ae2e0b2df0c1c`.
Required cached configuration/tokenizer files are hashed as well. Runtime
absence, incompatible runtime, missing cache, wrong model identity, model-load
failure and alignment-execution failure retain distinct error codes.

## Provenance and supported boundaries

Original ASR TXT and SRT bytes are retained and hashed. The Canonical
TranscriptRevision copies the original TXT exactly, including its line breaks
and trailing whitespace; it remains machine-generated/machine-unverified and
candidate, never human-verified. SRT display padding is removed only from the
producer's cue input view. Each cue content must match an exact slice of the
original TXT, with only whitespace between cues. Native original SRT time
ranges and exact content character spans are retained in Canonical Evidence.
No time range is derived from whitespace or text length.

The adapter validates the historical producer envelope, original audio and
segment hashes, actual producer runtime/package identity, single-run result
hash and exact token order. Positional tokens without native positive
intervals stay explicitly unaligned; repeated words cannot shift a later
word's timing onto an earlier unaligned occurrence. Wholly failed native
segments are retained as unaligned tokens. No timestamp interpolation or word
repair is introduced.

Existing Evidence importer/validator and supported project aggregate contracts
compose selected sources. Every selected source finishes Evidence before the
Topic batch freezes its aggregate input hashes. Existing Topic review accepts
only fully timed exact cue/Word partitions: an unaligned result remains
inspectable Evidence and fails Topic processing explicitly; no timed Word is
invented to bypass that contract.

## Persistence and recovery

Intake and sorted per-project locks serialize mutations. State snapshots are
atomic, immutable and hash-linked. Stage receipts bind original source,
ASR completion/configuration, original TXT/SRT, producer input/output,
model/runtime/profile/lock identity, revision and Evidence bytes.

Resume validates current source/registry/manifest, runtime and completed
artifacts. Completed review returns without inference or new snapshots.
A durable compatible raw alignment is revalidated and reused after a
receipt-publication interruption. A partially published deterministic Evidence
import can finish missing outputs only after retained immutable records match
recomputation. Corrupted published projections are rejected rather than
replaced. An ambiguous/incomplete inference attempt is not silently repeated;
`retry --entry ID` is explicit and preserves older attempts. Topic retries
use new retained batch/run directories for failed entries and preserve already
successful children's packages. No intermediate JSON editing is required.

## Verified live evidence (2026-10-31)

Parent task evidence:
`~/.codex/task-evidence/seminartext-issue164/completion-20261031/live-results.json`.
Three fresh task-owned Russian playable-media scenarios used actual existing
ASR, offline WhisperX/model inference and the existing local Topic engine:

| Scenario | Sources | Native Words | Native cues | Topics |
|---|---:|---|---|---|
| Astronomy | 1 | 30 | 4 | 1 |
| Unrelated botany project | 1 | 32 | 4 | 1 |
| Multi-source project | 2 | 30 + 35 | 4 + 4 | 1 + 1 |

Every result remains REVIEW_REQUIRED, with zero decisions, zero unaligned
Words and zero label fallbacks in these bounded live samples. Exact original
TXT, native interval equality, Canonical Evidence validation and fresh-process
status/inspect/resume passed. Entire intake inventories were byte-identical
after completed resume, proving no duplicate inference/artifact/state writes.
The initial failed padding diagnostic is retained separately; the corrected
run reused its accepted ASR completion instead of repeating ASR.
These bounded samples establish integration, not full-corpus quality or
semantic acceptance. Synthetic unit tests are separate evidence and run no
inference. Installed SeminarText, dependency/model stores and other products
are not modified by this source-checkout workflow.

## Governed installed-runtime closure

The existing `scripts/seminartext-dev` deployment includes the public review
commands' fixed source closure in its existing hash inventory: automatic/batch/
media adapters, the existing reviewed-admission helper and schema, the same Topic
Engine at its package import path, the unchanged historical alignment producer,
and existing alignment requirement/profile/lock metadata. This copies source
files only; Python environments and model caches are never copied or changed.
The existing Integrity inventory now contains 36 components.

The governed backup retains each added file's old bytes or an explicit prior
absence. Its closure manifest is hash-bound into the existing backup manifest.
Rollback validates the complete backup and every current target before any
restoration, rejects symlinks/foreign changed bytes/staging collisions, and
removes a newly added file only when both its authenticated prior absence and
its current governed bytes are proven. Legacy backups lacking this closure
manifest never authorize removal of these files. Native rollback publication
remains independently fail-closed; no receipt or central-publisher validation is
weakened to accommodate a historical inventory.

Deployment additionally smoke-dispatches the three public review commands with
`--help`, without loading models or creating semantic output. This packaging
support grants no deployment authority: the caller must still prove PR-014's
clean merged-main, required checks, known-target, backup and rollback conditions.
