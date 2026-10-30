# Four-product engineering readiness — bounded reconciliation, 2026-10-30

## Result and authority

The next proposed coding task is **support current BookText CDM 1.0 in the
existing Integra Seminar Library adapter**. It has a reproduced producer/consumer
format gap and can be developed using synthetic inputs without a real seminar
semantic decision. [Executable task scope](NEXT_TASK.md).

Owner direction in this conversation: develop the source-processing system
across all four products; human review is necessary, but real seminar review
should not consume this engineering phase. The Owner then approved a bounded
code/integration reconciliation and preparation of one next implementation task.
This report completes that planning scope. It does not authorize another
repository's implementation, adopt a new Product Rule, or accept real content.

The Roadmap and State now distinguish this engineering priority from S1's
unfinished content acceptance. Their existing S1 control-plane projection is
preserved: S1 is not complete, and S2/S3 are not implicitly authorized. The
central roadmap is not edited, and its real-content S1→checkpoint→S2→S3
acceptance sequence is not presented as a prerequisite for separately authorized
synthetic development. This is not the post-S1 Release/Integration Readiness
checkpoint and makes no installed-runtime or production-readiness claim.

## Verified source identities

Remote `main` identities resolved through GitHub on 2026-10-30:

| Repository | Exact commit |
| --- | --- |
| Yurielo/seminartext | `33c3ee030a1ff7b82760ac8a7dde45007e01a303` |
| Yurielo/videotext | `f715f11df72f8e4e806b70b2a2f86cf097a6bf6c` |
| Yurielo/booktext | `7219d0e6eee74c2c2f90e8cff6e9da624b6cb52a` |
| Yurielo/integra | `55141b8688996a4ba19f1cffb0930bb61a9561f6` |
| Yurielo/four-product-architecture | `475c5f2d826a40f34f234508b83618c64aecd851` |

Initial workspace was clean at `2c232f05bdfa9d907a6954e4c017d36054622e17`,
branch `codex/issue-155-vertical-roadmap`. A new branch in the same workspace,
`codex/four-product-engineering-readiness`, starts from the verified SeminarText
main above. No reset, other-worktree checkout, installed-runtime change or
archive/Candidate operation was performed. Provider snapshots were read by
exact Git objects; their active working copies were not used as source truth.

Read: each product's current AGENTS; SeminarText Registry/Workflow/active
Roadmap and State; complete canonical Unified Rules; central architecture and
roadmap; Integra's six AGENTS-mandated product/architecture/state/workflow/policy/
team sources. Integra CURRENT v2 retains explicit promotion authority. PR #305
has a pending Candidate-bound Proposal and does not grant permission to replace
its Candidate. These lifecycle gates are included in the proposed coding task.

SHA-256 of exact read source blobs (commit is the corresponding row above):

| Source | SHA-256 |
| --- | --- |
| SeminarText `AGENTS.md` | `fa47a9b923a6ae19da76f31723164a3d41b3ee3e5f4c15410621ff9190f2bc79` |
| SeminarText `docs/architecture/SEMINARTEXT_PRODUCT_RULES.md` | `b59ba7205120ec1a0dd8fe0f881c26c8056ba7feb61bebd27c7100b59b899492` |
| SeminarText `DEVELOPMENT_WORKFLOW.md` | `cc449a7f1e187d48f0b2742e930ae212eb1b996fc9d11c92eed8805d7ef41c27` |
| Integra `docs/governance/UNIFIED_CODEX_RULES.md` | `8b8e31c7620d45e1e14429e07e7b97b2adc118745ce781a55b932213c55b646b` |
| Four-product `docs/architecture.md` | `61a49437994bd481d9be71bd26a7d24bfff77ae9e04abddf127e9c4c1fcbc9a0` |
| Four-product `ROADMAP.md` | `c9e25d2942c4c8c23ec69949a4671ec69462660b838769494f7987b66fc0e63e` |
| Integra `scripts/seminar_library_preview.py` | `b5f79082f80ad4b8b171c5d257c1d82b77b0a5e33d0e05275ac6b9985ceb8a0b` |
| BookText `tools/canonical_document.py` | `09798d4dcd4dda09c49ebd7b4cc0bc2f97cffb416c68a47b1b3ea0bbd886c039` |

## Existing chain and bounded gaps

| Transition | Verified implementation | Limitation relevant to the system |
| --- | --- | --- |
| Audio/video → transcript and timing | SeminarText project transcription, `evidence_foundation.py`; VideoText `SelectedTimingVerticalSlice.swift` consumes canonical SeminarText timing and refuses a hidden ASR rerun for translation. | This audit inspects code; it does not certify installed ASR quality or run models. |
| Documents → structured result | BookText `tools/canonical_document.py`: `booktext.canonical_document` 1.0, source pages, ordered block IDs, review provenance, excerpt gaps and asset references. | Native result exists independently of semantic acceptance. OCR agreement is not human verification. |
| Provider results → shared library | Integra `scripts/seminar_library_preview.py` has four explicit product adapters. | Its BookText adapter accepts the legacy 0.1 manifest/document pair, not CDM 1.0. This is the selected first repair. |
| Evidence → review | SeminarText `human_review_workflow.py`; Integra `knowledge_notebook.py` and topic-review runtime. | K1 `source_inputs` requires a completed Process source with transcript, Topics and Word Timeline. It is not a generic page/block document review path. |
| Reviewed proposals → Canonical Knowledge | SeminarText `reviewed_knowledge_admission.py`, `reviewed_knowledge_admission_v1.schema.json`, `docs/architecture/REVIEWED_KNOWLEDGE_ADMISSION_V1.md`. | Exact source/notebook-bound admission already exists. Machine system-DEFER can retain provisional output without accepted entities. Do not build a second admission engine. |
| Canonical Knowledge → viewing/export | SeminarText `project_knowledge_bridge.py` and Obsidian path; Integra `knowledge.py` has source-bound graph/diff/navigation contracts. | Integra's older view contains pinned Golden Slice validation. Library browsing is not universal Concept/history navigation; document-to-knowledge and cross-seminar accumulation remain separate work. |
| Issue-specific batch → reusable review | PR #121 `analysis/issue_68_vertical_slice/batch_review.py` uses the governed ledger/QA builder and contains issue-specific recommendations and IDs. | It is evidence of a working bounded batch workflow, not a universal four-product semantic classifier. Extracting/generalizing it is not part of this first adapter task. |

This is a capability/contract map, not a claim that every format, UI operation,
failure path or installed product was exercised. The selected task fixes the
earliest reproduced document-result handoff in this bounded inspection; it is
not a claim that it is the only remaining integration gap.

## Reproduced gap and checks

Using clean archived copies of the pinned Git trees in an owned temporary
workspace, without models or real seminar/book input:

- Integra `test_seminar_library.py`: **8 tests passed**.
- BookText `test_canonical_document.py`: **13 tests passed**.
- A minimal synthetic CDM 1.0 passes BookText's `validate_document`.
- The same file explicitly routed as BookText into Integra's existing `build`
  produces zero projects and `unsupported_manifests: 1`, with diagnostic
  `unsupported BookText package manifest version or type`.
- Two catalog builds on the same paths are byte-identical; input bytes remain
  unchanged. This is a supported format gap, not evidence of source corruption.
- The probe is intentionally a minimal validator-valid CDM, not a complete
  producer E2E. The implementation task requires a producer-generated richer
  synthetic package with pages, gaps and review provenance.

Reproduce without changing supplied repositories:

```bash
./scripts/seminartext-owned-run python3 \
  analysis/four_product_readiness_2026_10_30/reproduce_contract_gap.py \
  --integra-repo /path/to/integra \
  --booktext-repo /path/to/booktext
```

The script reads pinned Git objects, so both commits must be present locally.
No assertion of cross-location catalog hash stability is made: input paths are
part of this preview's existing catalog representation.

## Pending work preserved

- [SeminarText PR #121](https://github.com/Yurielo/seminartext/pull/121): open,
  draft; head `eac0d004d63923f46205a2721775458e891140e0`. Exact-head QA has
  182 Topic results, 22 Concept candidates, 246 links, 7 deferred links and
  2 selective transcript verification exceptions. The older PR description's
  52 active cases is not current artifact truth. This task applies no decisions,
  changes no source evidence and does not close #68 or claim S1 accepted.
- [Integra PR #305](https://github.com/Yurielo/integra/pull/305): open, draft;
  head `6fa1e1f218293a563b13ece0d7a61b851e87b315`. It already implements the
  native project/source/artifact browser and has a Candidate awaiting Owner
  acceptance. Its UI must be reused through its lifecycle, not reimplemented.
- Open Issue/PR inventory was checked in SeminarText, Integra and BookText;
  no duplicate CDM-library implementation PR was found. VideoText was inspected
  at main only; no broad release/readiness conclusion is drawn from its backlog.

## Rules and self-review

PRODUCT_RULES_READ: YES

APPLICABLE_PRODUCT_RULES: PR-001, PR-002, PR-003, PR-004, PR-005, PR-006,
PR-007, PR-008, PR-010, PR-011, PR-012, PR-013, PR-014.

PRODUCT_RULE_CONFLICTS: NONE

PR-009 adds no action because the Registry is unchanged. Human semantic authority
is retained; a technical proposal and synthetic decisions do not become real
acceptance. Provider/consumer ownership remains adapter-first. No source product
code, Dataset/Gold, archive, CURRENT, Candidate or installed runtime is changed.

Self-review distinguishes implemented code, executed synthetic tests, reported
Candidate lifecycle and unverified deployment. The next task stays at one
versioned artifact boundary and does not attempt OCR, document Knowledge
admission, cross-seminar merging or all four products at once. No new Product
Rule or architecture is proposed. Repository validation and Integrity results
are recorded in the delivery PR/report, including any pre-existing limitations.
