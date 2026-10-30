# Media-to-Evidence intake v1

`project-media-review` is the explicit local-media entry point for the future
media-to-Evidence-to-review journey.  It accepts no discovered sources and does
not accept hand-written transcript, alignment or proposal artifacts.

The manifest is versioned and contains only an entry ID, existing project,
registered source ID and selected absolute local media path.  Preparation binds
the exact media SHA-256.  Reopen, run and resume reject a changed manifest or
changed media before any expensive operation.

```json
{"artifact_type":"seminartext.media_to_review_manifest","schema_version":"1.0.0","entries":[{"id":"source-a","project":"/absolute/project","source_id":"video_001","media":"/absolute/input.mp4"}]}
```

The public commands are:

```bash
./seminartext project-media-review prepare /work/intake --manifest /work/media.json
./seminartext project-media-review run /work/intake
./seminartext project-media-review status /work/intake
./seminartext project-media-review inspect /work/intake
./seminartext project-media-review resume /work/intake
```

The current host lacks the accepted WhisperX 3.8.6 alignment profile and its
Russian alignment model.  `run` therefore records `ALIGNMENT_UNAVAILABLE` and
does not create a TranscriptRevision, Canonical Evidence, Topic Draft, review
package, timing claim or semantic decision.  This is intentional: the accepted
alignment producer is `analysis/word_alignment_decision/run_whisperx_existing_text.py`;
it is an immutable historical producer and the task forbids model download or a
replacement aligner.  Installing the approved profile is a separate runtime
authority/dependency task.  Once available, the next implementation step is to
adapt that producer's real output through existing evidence and batch-review
contracts, without changing its algorithm or provenance.
