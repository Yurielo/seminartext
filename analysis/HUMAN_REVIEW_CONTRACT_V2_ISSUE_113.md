# Human Review Contract V2 — Issue #113 representation gate

## Status and authority

- Contract: `seminartext.topic_review_decisions` / `2.0.0`.
- Source package remains the immutable v1 package `review_package_topic_drafts_stress_code_video_001_legacy_v1`.
- The Product Owner's Issue #113 semantic decisions define **what** the reviewed units mean.
- Exact word anchors prepared by `project-review-boundary-prepare` are machine proposals with `REVIEW_REQUIRED` authority. They do not define **where** an accepted boundary is until Product Owner `DOMAIN_REVIEW`.
- V2 application fails closed unless `boundary_authority` is `PRODUCT_OWNER_DOMAIN_REVIEW`.

No Issue #113 decision is applied by this implementation task.

## Minimum coherent extension

V1 remains readable and executable without migration. V2 adds a separate schema and commands while using the same governed Human Review module:

```text
original Topic Draft snapshots
  → complete source-fragment partition
  → one ReviewDecision with one or more operations
  → each fragment consumed exactly once
  → typed result units
```

Each V2 decision carries immutable expected Topic hashes. Each source fragment identifies its original Topic Draft, Source, TranscriptRevision, exact canonical word range, and inherited evidence references. Validation resolves exact timestamps and copies Canonical Evidence and transcript-assurance provenance. The output retains every original Topic snapshot instead of rewriting machine history.

The validator rejects:

- stale package or Topic hashes;
- gaps or overlaps in a source Topic partition;
- fragments outside the original Topic range;
- changed Source or TranscriptRevision;
- duplicate fragment consumption;
- non-contiguous composed results;
- evidence not present in the reviewed package;
- application while exact boundaries remain `REVIEW_REQUIRED`.

## Result dispositions

- `SEMANTIC_KNOWLEDGE`: eligible for the existing semantic path, subject to its existing gates.
- `SEMINAR_STRUCTURE`: retained as instructional/seminar structure and kept out of Canonical Knowledge by construction.
- `NON_SEMANTIC_EXCLUDED`: excluded from semantic knowledge while retaining exact source lineage.

The V2 application result stores these dispositions in three separate collections. It does not compile the structural or excluded collections into Canonical Knowledge.

## Compatibility

Existing V1 `ACCEPT`, `RENAME`, `SPLIT`, `MERGE`, `REJECT`, and `DEFER` documents continue through the original v1 schema, status command, and application path. V2 is opt-in through `project-review-v2-status` and `project-review-v2-apply`; there is no implicit migration or reinterpretation of v1 artifacts.

## Issue #113 pattern coverage

| Accepted pattern | Representative Topics | V2 representation |
|---|---|---|
| Rename, unchanged range | 1–3, 7, 13, 15–17, 24, 29 | One full-range fragment → one semantic result; `RENAME` |
| Split one Draft | 4, 6, 11, 12 | Complete fragment partition → multiple results; `SPLIT` |
| Merge Drafts | 18, 20 | Full-range fragments → one contiguous result; `MERGE` |
| Trim / one-sided realignment | 8–10, 19, 23, 25, 30 | Explicit retained and excluded fragments; `TRIM`/`REALIGN` |
| Both-side realignment | 21–22 | Cross-Draft fragment partition and composition; `REALIGN`/`MERGE` |
| Split + merge composition | 4–6, 11–12, 14 | One decision may partition multiple Drafts and compose adjacent fragments into multiple results |
| One Draft → several results | 4–6, 11–12, 14 | Multiple fragments from one source Topic consumed by different results |
| Several Drafts → one result | 4C/5, 5/6A, 11B/12, 21/22, 26/27, 30/31 | One result references contiguous fragments from adjacent Drafts |
| Explicit non-semantic exclusion | 8–10, 22–23 | Fragment → `NON_SEMANTIC_EXCLUDED` |
| Instructional seminar structure | 28 | Fragment → `SEMINAR_STRUCTURE` |
| Q&A crossing a machine boundary | 31 | Question and answer fragments → one `SEMANTIC_KNOWLEDGE` result |
| Transcript duplication signal | 22 | Original fragment and machine transcript assurance remain traceable; no silent transcript correction |

## Exact-boundary proposal workflow

`project-review-boundary-prepare` accepts a bounded request manifest containing candidate canonical Word IDs and mechanical rationales. It verifies the current review-package hash, Canonical Evidence, Word existence, Source/TranscriptRevision identity, aligned timestamps, and Word Timeline presence. It emits:

- `boundary_proposals.json` — machine-readable, deterministically serialized, globally and individually `REVIEW_REQUIRED`;
- `BOUNDARY_REVIEW.md` — only unresolved exact boundaries, with short before/after evidence and alternatives.

One candidate produces `AMBIGUITY: NONE`; multiple candidates remain `MULTIPLE_CANDIDATES`; no candidate requires an explicit blocker and produces `INSUFFICIENT_EVIDENCE`. None of these states grants semantic or boundary authority.

## Determinism and provenance

Canonical JSON serialization sorts keys and terminates with one newline. Tests rebuild both V2 application output and boundary proposals byte-for-byte. Fragment lineage preserves:

- original Topic Draft and Topic hash;
- source and TranscriptRevision;
- canonical Word start/end and sequences;
- exact aligned timestamps;
- Canonical Evidence locator provenance;
- transcript assurance;
- ReviewDecision ID and decision-artifact hash.

## Remaining representational gaps

None for the Issue #113 patterns listed above. This statement is bounded to same-source, same-TranscriptRevision, contiguous semantic/structural units. Cross-source or cross-revision result composition remains deliberately unsupported and fail-closed because Issue #113 does not require it.

## Human gate

The current boundary proposal set must be reviewed by the Product Owner. Only a later, separately authorized task may encode approved anchors in a complete V2 ledger and apply the 31 decisions.

`HUMAN_GATE: PRODUCT_OWNER_DOMAIN_REVIEW`
