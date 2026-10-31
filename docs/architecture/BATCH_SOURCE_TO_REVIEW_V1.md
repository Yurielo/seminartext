# Batch source-to-review orchestration v1

Issue #162 provides the reusable batch layer over the source-checkout adapter
from Issue #160.  It is an explicit selection tool, not a semantic classifier,
knowledge compiler, discovery service, or a substitute for human review.

## Supported boundary

Every selected entry is one existing audio/video source, its exact active
TranscriptRevision, exact timed Words and cues that partition those Words.  A
JSON manifest is supplied by the caller; no proposal JSON, title matching,
filesystem discovery, cross-source accumulation or inferred relationships are
accepted.

```json
{
  "artifact_type": "seminartext.topic_review_batch_manifest",
  "schema_version": "1.0.0",
  "entries": [
    {
      "id": "course-1-source-a",
      "project": "/absolute/path/to/project",
      "source": "/absolute/path/to/source.mp4",
      "source_id": "source-a",
      "revision_id": "revision-a",
      "run_directory": "source-a-review"
    }
  ]
}
```

The paths are explicit, absolute, regular local paths.  Entry IDs,
source/revision pairs and run directories must be unique.  `run_directory` is
a single safe directory component.  The batch layer validates every source's
current Canonical Evidence binding before it invokes the first model call.

## CLI journey

Use the supported development/runtime Python as with the single-source command.
The selected batch directory is the only output location.

```bash
./seminartext project-topic-review-batch prepare /work/topic-review-batch \
  --manifest /work/selected-sources.json
./seminartext project-topic-review-batch run /work/topic-review-batch
./seminartext project-topic-review-batch status /work/topic-review-batch
./seminartext project-topic-review-batch inspect /work/topic-review-batch
# In a new process, after an interruption:
./seminartext project-topic-review-batch resume /work/topic-review-batch
```

Sources run sequentially.  Each successful entry delegates directly to the
existing `project-topic-review generate` mechanism and creates its own
immutable `REVIEW_REQUIRED` package.  The aggregate command never applies a
decision: zero decisions remain attached to every generated package.  Continue
with the existing governed review commands only when an authorized human
semantic decision is actually available.

## Persistence, recovery and failure behavior

`prepare` records the exact manifest digest and one current source/evidence
binding per entry.  The batch directory has an immutable, hash-linked state
snapshot chain.  A new snapshot is written after each source outcome, so a
completed source is not repeated after interruption.

If the single-source response was committed but package publication was
interrupted, `resume` uses its existing mechanical replay path and never calls
the model again.  If inference started but no response was committed, the
entry is recorded `FAILED`; it is not silently re-run.  Other explicitly
selected entries can still finish.  A source/evidence change, changed manifest,
invalid/corrupt receipt, unavailable file or unsupported contract makes status
fail closed rather than presenting an earlier result as current.

The model output itself is not declared deterministic.  Determinism applies to
manifest validation, source binding, response replay, journal persistence and
the aggregate result from identical stored inputs.

## Authority and provenance

The batch state contains the source-checkout binding, exact child receipt and
package hashes, model digest reported by the child workflow, source path, and
the child package location.  It creates no Dataset/Gold record,
BenchmarkSegment, Concept, Relation, Canonical Knowledge object, decision, or
new semantic authority.  A technically valid package is still
`REVIEW_REQUIRED`; confidence, coverage, successful calls and batch completion
are never acceptance.

## Verification boundary

`tests/test_batch_topic_review.py` constructs two unrelated synthetic Russian
multi-cue sources (astronomy and botany) and exercises preparation, sequential
run, fresh reopening/status, resume, immutable journal checks, stale-input
preflight, interrupted child replay, retained failure and strict manifest
rejection.  The tests use no real seminar or human decision.  Bounded live
smoke evidence, if performed, is retained outside source projects and remains
synthetic; it is not semantic evidence.

This stacked work depends on PR #161 as implementation evidence only.  It does
not merge, deploy or change that predecessor, Issue #68/S1, Dataset/Gold, the
Topic Engine, other products or installed runtime.
