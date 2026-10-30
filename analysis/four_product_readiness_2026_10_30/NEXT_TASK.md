# Proposed bounded implementation: BookText CDM in Integra Seminar Library

Status: PREPARED TASK, not implementation authorization or a release decision.
Recommended model: GPT-6 Codex; reasoning effort: HIGH.
Owner: Integra. Read-only providers: BookText, SeminarText, VideoText.

## Outcome

An explicitly selected current BookText `book_document.json` appears in the
existing Seminar Library preview with its document identity, page/block
provenance, review status, and truthful availability. Preserve support for the
legacy `booktext.package_manifest` / `booktext.document` 0.1 pair and the other
three product adapters. This is document-result interoperability, not completed
document-to-Canonical-Knowledge admission or semantic acceptance.

## Mandatory sources and authority

Resolve current Integra main and read AGENTS.md and all its mandatory sources,
including the complete `docs/governance/UNIFIED_CODEX_RULES.md`; record exact
commits and hashes. Read CURRENT v2, protection, Proposal/Candidate and retention
contracts before any lifecycle action. Check open work and PR #305 for overlap.
Do not overwrite or silently rebuild its pending Owner-test Candidate.

Architecture: `Yurielo/four-product-architecture`, main `docs/architecture.md`
and `ROADMAP.md`. Provider: `Yurielo/booktext`, main
`tools/canonical_document.py` and its public machine-protocol/document contract.
Consumer: `Yurielo/integra`, main `scripts/seminar_library_preview.py`,
`schemas/seminar_library_preview_v1.schema.json`, `tests/test_seminar_library.py`.
The audit baselines and reproduced gap are in the accompanying REPORT.md.

Triggered Unified Rules: A/B, C15–20, D25–26 when lifecycle/architecture applies.
Applicable SeminarText Product Rules for the planning boundary: PR-001–PR-008,
PR-010–PR-014. Product Rule conflicts: NONE. No SeminarText source change.

## Implementation scope

1. Extend the existing catalog adapter with explicit dispatch on artifact type
   and schema version. Reuse existing catalog/schema/bridge; no second catalog.
2. Read existing CDM bytes only. Preserve native document and block IDs, original
   source-page numbers, excerpt gaps, source references, original/machine/corrected
   text distinctions, unresolved review and warnings. Never infer semantic
   identity or a missing project/revision ID from a title, path or digest.
3. Bind the projection to exact selected input bytes and declared dependencies.
   A hash is content identity, not a native revision ID or human attestation.
   Reuse supported provider validation; if packaging it requires a provider pin
   change, use the accepted component procedure and its bounded dependency set.
   Do not import a developer checkout at runtime or replicate OCR/translation.
4. Make missing, unsafe, stale and unsupported resources explicit. A successful
   catalog must not relabel invalid input as empty or expose stale previous data.
5. Use existing native project/detail rendering if the applicable GUI base is
   authorized. Preserve explicit product selection and session-only state.
   Any additional UI field must be minimal and supported by actual source data.
6. Keep complete source artifacts unchanged. No ASR/OCR/model invocation, managed
   copy, persistent catalog, semantic proposal generation or knowledge admission.

## Verifiable acceptance

- A producer-generated synthetic CDM 1.0 with at least two original pages,
  an excerpt gap, block IDs and unresolved review is accepted by the existing
  catalog; its supported provenance and uncertainty survive projection.
- Legacy BookText 0.1 and synthetic SeminarText/VideoText/Integra routes regress
  cleanly. A CDM selected under the wrong product is rejected explicitly.
- Invalid JSON, unsupported version, duplicate/invalid IDs, stale declared
  hashes, absent source files, symlinks/traversal and changed-during-read inputs
  fail safely or show the precise unavailable status appropriate to the contract.
- Repeat processing of unchanged inputs is deterministic. Before/after hashes
  of the entire synthetic source tree prove no source mutation; the read-only
  operation creates no application data directory and no semantic decisions.
- Native GUI evidence, if in authorized scope, proves background loading, stale
  response protection and truthful project/details/error states. A mock is not
  GUI evidence. The old PR #305 Candidate cannot prove changed code.
- Run focused/full supported tests, governance validator, Quality Gate and
  `git diff --check`. Review scope independently as required by Integra AGENTS.

## Delivery and terminal boundary

Create one small Integra Issue/PR under the exact implementation authorization.
Do not modify the other three product repositories, real seminar decisions,
Dataset/Gold, CURRENT, existing Candidates, installed apps or running workloads.
No automatic semantic acceptance, identity merging, install, activation or
production claim. Candidate creation/handoff follows the verified native
lifecycle only; stop at an actual missing Owner authority. Report COMPLETE for
the authorized code/contract scope, READY_FOR_OWNER_TEST only with all native
pre-owner evidence, or OWNER_ACTION_REQUIRED/BLOCKED with exact evidence.
Emit the required completion sound at the terminal handoff.
