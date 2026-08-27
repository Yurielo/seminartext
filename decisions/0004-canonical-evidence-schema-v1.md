# 0004 - Canonical Evidence Schema v1

Date: 2026-08-27

## Status

Accepted

## Context

ADR 0003 selected WhisperX alignment-only for existing verified transcript text.
The next architecture gate requires one source-of-truth representation that can
preserve semantic text, source/cue provenance, native and unavailable word
timing, benchmark ranges, topics and evidence links across timed and non-timed
sources.

TXT, SRT and DOCX currently exist as useful outputs, but cannot be independent
authoritative stores. Word alignment also cannot be allowed to rewrite a
verified transcript or manufacture timing for unsupported words.

## Decision

Adopt Canonical Evidence Schema v1 as specified by:

- `schemas/canonical_evidence_v1.schema.json`;
- `schemas/validate_canonical_evidence_v1.py`;
- `analysis/CANONICAL_EVIDENCE_SCHEMA_V1.md`.

The v1 canonical artifact is one deterministic UTF-8 JSON bundle for one Project
snapshot. Entities are normalized collections; Word is a first-class record,
not an embedded copy. TXT, SRT, DOCX and Markdown are derived views.

Stable IDs are deterministic, namespaced and independent of local paths and
run time. Transcript semantic revisions are immutable. ASR, verified and later
corrected text are distinct revision kinds; clean output is an export; alignment
is a separate hash-bound run. A text or source-content change makes an old
alignment stale/superseded for the changed artifact.

Timing provenance is controlled as `source_exact`, `forced_alignment`,
`derived_estimate` or `unavailable`. WhisperX maps to `forced_alignment`.
Unaligned words preserve ID, text, character span, order and cue provenance,
while word start/end remain null.

Benchmark segments are contiguous Word ranges. Topics are contiguous segment
ranges with matching Word bounds. EvidenceRef uses source-compatible typed
locators for time, PDF pages, PPTX slides, DOCX/text characters and image
regions; non-timed sources never receive synthetic timestamps.

JSON Schema Draft 2020-12 defines record shapes. The dependency-free companion
validator defines cross-record and deterministic-order invariants. Schema
versions follow semantic versioning, and future migrations must be deterministic,
idempotent, auditable, non-destructive and provenance-preserving.

## Consequences

Positive:

- verified text and timing provenance have an explicit authority boundary;
- Word, segment, topic and evidence coordinates are stable and auditable;
- unaligned data remains complete without false precision;
- timed and document evidence share one reference model;
- the Word Timeline MVP has a machine-checkable target contract.

Costs:

- producers must calculate hashes, stable IDs and exact character spans;
- cross-record validation is required in addition to JSON Schema validation;
- semantic transcript corrections create a new coordinate revision and require
  dependent data regeneration or explicit invalidation;
- v1 uses a JSON bundle, so a large-scale JSONL/storage profile remains future
  work.

## Alternatives

### Keep SRT/TXT/DOCX as peer sources of truth

Rejected. Independent edits cannot reliably preserve identity, character spans,
revision authority or non-video evidence provenance.

### Embed Words inside cues, segments and topics

Rejected. Repeated mutable copies create ambiguity and prevent stable shared
ranges. Normalized first-class Words provide one coordinate system.

### Store cue-derived timing for unsupported words

Rejected. Coarse provenance is not a native word interval and would create false
precision. Unaligned timing is explicitly unavailable.

### Make alignment output a transcript revision

Rejected. Alignment enriches timing for exact semantic text and has no authority
to replace that text.

## Scope boundary

This ADR freezes an architecture/schema contract only. It does not implement
production ingestion/export, install WhisperX in production, change Topic Engine
algorithms or Gold A/B/C, access Dataset D/F, alter Dataset E policy, implement
Obsidian/Knowledge Engine, or select a database/graph store.
