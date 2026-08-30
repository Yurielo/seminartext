# Machine Transcript Evidence + Selective Human Verification v1

Issue #111 records the Product Owner decision that full-transcript human
verification is optional for downstream automatic processing. A machine
transcript may enter Canonical Evidence only as explicitly typed evidence:
`machine_generated` origin, non-empty generation method,
`machine_unverified` state, exact source/transcript hashes and candidate
authority. Native timing is still required for a Word Timeline; the foundation
never invokes ASR as a substitute for alignment.

Selective verification creates an immutable child TranscriptRevision with a
parent revision, reviewer and sorted character ranges. The child remains
candidate/active and is marked `selectively_verified`; corrections outside the
declared ranges fail closed. Full verification is the only path to
authoritative/verified lifecycle.

Every downstream Topic Draft remains `REVIEW_REQUIRED` and carries the
transcript assurance metadata into the human review package. No machine
transcript can become accepted semantic knowledge without an explicit human
ReviewDecision.

The Stress Code project is not ingested by this issue: it currently lacks a
native alignment artifact and a Canonical Evidence bundle. It therefore remains
blocked for product processing without changing project data or creating
semantic output.
