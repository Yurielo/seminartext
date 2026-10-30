# Automatic Evidence-to-Topic review v1

Issue #160, explicit Owner engineering authorization 2026-10-30.

Source-checkout CLI: existing Canonical Evidence -> existing legacy Topic Engine
-> existing Topic Draft/review v1. This adapter does not accept semantics or
extend the separate Knowledge admission contract. PR #159 is not a dependency.

## Usage

Use the supported development environment, setting `SEMINARTEXT_PYTHON` to its
Python executable. All paths below are explicit user-selected local paths.

```bash
./seminartext project-topic-review generate /work/run /work/project \
  --source-id SOURCE_ID --revision-id TRANSCRIPT_REVISION_ID --source /inputs/source.mp4
./seminartext project-topic-review status /work/run
./seminartext project-topic-review inspect /work/run
./seminartext project-topic-review replay /work/run
```

Input is one audio/video source, one assured active/verified TranscriptRevision,
exact timed Words and existing cues that partition those Words exactly. Source
bytes must match Evidence. Machine-origin transcripts retain their actual
assurance; no human verification is invented. Cue-only, unaligned, overlapping
or incomplete cue-to-Word mappings fail explicitly.

The engine receives existing cue text with deterministic integer view IDs.
Those IDs map to exact Word endpoints; the adapter creates no BenchmarkSegments
and never changes Evidence. Existing windows, boundary detection/refinement,
prompts, label generation and validators are reused without algorithm changes.
The governed engine implementation must retain its exact recorded hash.

Generation invokes only existing `gemma3:4b` through local Ollama, recording its
observed digest. It never installs models. Each raw request/response is retained
in numbered immutable call files. Invalid structured responses, duplicate or
unknown boundaries, transport failure and swallowed boundary fallbacks prevent
success. Invalid labels never become accepted substitute titles. The source
generation budget is 300 seconds, including calls/retries; selected model and
inventory are rechecked before success.

The resulting `drafts.json`, `review_package.json`, `REVIEW.md` and empty
decision template are prepared by `human_review_workflow`. Quotes and locators
are resolved by its validators from current Evidence. Use existing
`project-review-status` and governed decision/application commands for subsequent
human review. The adapter's status reports the generated pending package; it
does not consume external human ledgers or claim Knowledge acceptance.

## Persistence and errors

A process lock serializes each run. Atomic no-overwrite files retain bindings,
attempt, calls, stored producer response, package artifacts and final hash
receipt. Status/inspect require the final receipt and current matching inputs;
they never return an earlier package as current after failure or stale input.

`replay` rebuilds mechanically from the stored validated response, without model
access. An interruption after response publication can resume package publication.
An interruption before response publication cannot safely repeat inference:
use a new explicitly selected run directory. Failed runs retain diagnostics.
Identical successful retries reuse the existing response and artifacts.
Model generation itself is not promised deterministic. An empty/failed result
does not create a fake review package or human DEFER.

This is source-checkout delivery only; installed deployment inventories and
consumer bundles are unchanged. Model output remains REVIEW_REQUIRED even when
all technical checks pass.

## Verification and live limitation

`tests/test_automatic_topic_review.py` builds unrelated synthetic astronomy and
botany projects, replacing controlled fixture schema scaffolding, source bytes,
text, IDs, hashes and timing. It removes prior Topics, evidence refs and benchmark
records; synthetic timing is not claimed to be an actual alignment run.
Mock transport checks integration with the unchanged engine and validators;
fresh public CLI processes check inspect/status/replay and corruption failures.

Two actual source-level smoke runs were performed on 2026-10-30, using local
gemma3:4b digest
`a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a`.
Both failed the existing label validator: one-word titles `Звезды` and `Корни`.
No success receipt or semantic decision was created. Raw calls and errors are
retained at `/Users/yurielokhin/.codex/task-evidence/seminartext-issue160`.

These runs exposed an adapter granularity defect: the initial adapter supplied
individual Words where the engine expects transcript segments. The adapter was
corrected to use existing cues with exact Word mapping. The final corrected
adapter has regression coverage but **has not had another actual model smoke**:
the authorized maximum of two source-level live runs has been consumed.
Do not claim the live acceptance criterion or overall task COMPLETE. A bounded
authorization to repeat the two corrected-adapter smoke runs is still required;
no real seminar review or new model is required by this engineering boundary.

## Authority evidence

SeminarText baseline: `33c3ee030a1ff7b82760ac8a7dde45007e01a303`.
Unified Rules fully read at Integra
`55141b8688996a4ba19f1cffb0930bb61a9561f6`, path
`docs/governance/UNIFIED_CODEX_RULES.md`, SHA-256
`8b8e31c7620d45e1e14429e07e7b97b2adc118745ce781a55b932213c55b646b`.
Accepted architecture and coordination roadmap fully read at
`475c5f2d826a40f34f234508b83618c64aecd851`:
`docs/architecture.md` SHA-256
`61a49437994bd481d9be71bd26a7d24bfff77ae9e04abddf127e9c4c1fcbc9a0`;
`ROADMAP.md` SHA-256
`c9e25d2942c4c8c23ec69949a4671ec69462660b838769494f7987b66fc0e63e`.

PRODUCT_RULES_READ: YES

APPLICABLE_PRODUCT_RULES: PR-001, PR-002, PR-003, PR-004, PR-005, PR-006,
PR-007, PR-008, PR-010, PR-011, PR-012, PR-013, PR-014.

PRODUCT_RULE_CONFLICTS: NONE

Issue #68/S1 remains incomplete. No real evidence/ledger, Dataset/Gold, engine
freeze, models, other products, runtime or architecture policy is modified.
Exact full tests, Integrity and Quality Gate results are recorded in the PR.
