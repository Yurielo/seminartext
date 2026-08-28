# Gold Expansion v2 preparation tooling

This directory implements Issue #50 as a separate data/evaluation track. It
does not import or run any Topic Engine candidate.

Workflow:

1. Register each Product Owner-provided source with the normal `seminartext
   init` and `project-add --video-link` workflow.
2. Produce provisional Russian ASR with `seminartext project-transcribe`.
3. Run `align_existing_transcript.py` in the isolated accepted WhisperX 3.8.6
   environment. The runner invokes alignment only and preserves the supplied
   SRT semantic text unchanged. Repeat alignment is supported where bounded;
   deterministic population is always verified separately.
4. Run `prepare_gold_expansion_v2.py` to validate source/SRT/alignment hashes,
   populate Canonical Evidence Schema v1, and create six evenly spaced blank
   human annotation packets per eligible source.

Canonical transcript revisions and all derived records remain `draft` with
`revision_kind=asr` and `authority=candidate`. Alignment does not make machine
text verified. Final Gold boundaries, titles and summaries require Domain Owner
authoring and Product Owner acceptance after the proposed dataset roles are
reviewed.

The window policy is the existing A/B/C-compatible protocol: sequential
12-minute transcript windows, at least 10 minutes of content, then six evenly
spaced selections from the first eligible window to the last. Selection reads
no predictions, embeddings, automatic boundaries or algorithm difficulty.
