# Reusable semantic processing workflow v1

Issue #158; direct Owner authorization, 2026-10-30. Implemented source-checkout
CLI, not installed-runtime activation, automatic extraction, or S1 acceptance.

## Supported input boundary

`./seminartext project-semantic-workflow` orchestrates the existing
`reviewed_knowledge_admission.py` compiler. It accepts prepared **admission v1**
proposals and machine-derived exact fragments for one source/transcript revision.
Word and cue precision remain distinct. New CREATE proposals for Topics,
Concepts and controlled Relations are supported. Arbitrary draft formats,
UPDATE proposals, reviewed K1 V2 input and other producers are not supported by
this first workflow; their existing independent admission API is unchanged.

There is no new producer or inference call. Admission v1 restricts the proposal
producer to `integra`; this wrapper preserves that identity rather than claiming
that SeminarText generated the proposals. No schemas, compiler or historical
receipts are rewritten to widen this restriction. Prepared fixture input proves
the lifecycle, not automatic semantic extraction or a live Integra integration.

Six explicit files are required:

| Flag | Binding checked |
| --- | --- |
| `--evidence` | Existing Canonical Evidence v1, exact bytes and source/revision references |
| `--fragments` | Existing `seminartext.machine_derived_fragment_result` v1; exact quotes, Word/cue endpoints and machine authority |
| `--proposals` | `schemas/reviewed_knowledge_admission_v1.schema.json`, exact contract hash, provisional records, fragment/producer hashes |
| `--source` | Original source bytes matching `source_sha256`; streamed hashing, no media processing/copy |
| `--notebook` | JSON containing the exact `notebook_id`; SHA-256 of its bytes equals `k1_binding.notebook_sha256` |
| `--producer-runtime` | Existing producer artifact whose bytes match `producer.runtime_sha256`; never executed |

The source, notebook and runtime files are independent current input checks,
not assertions synthesized from the proposal labels. Byte checks do not prove
that the producer actually executed, authenticate a human's identity, or make
machine statements authoritative. These are local explicit inputs and decisions,
not a remote identity/authorization service. Paths are recorded as local locators;
moving inputs requires a new explicitly prepared workflow. Symlinks are rejected.

## CLI journey

Run from the source checkout with its supported development dependencies:

```bash
./seminartext project-semantic-workflow prepare /work/review \
  --evidence /inputs/evidence.json --fragments /inputs/fragments.json \
  --proposals /inputs/proposals.json --source /inputs/source.mp4 \
  --notebook /inputs/notebook.json --producer-runtime /inputs/producer-artifact
./seminartext project-semantic-workflow inspect /work/review
./seminartext project-semantic-workflow status /work/review
```

Use the exact `package_sha256` returned by status/inspect when recording a
decision. This is an explicit confirmation of the displayed package:

```bash
./seminartext project-semantic-workflow decide /work/review \
  --proposal proposal_example --action ACCEPT \
  --reason 'Explicit decision after source review' --reviewer reviewer_example \
  --confirm-package-sha256 EXACT_PACKAGE_HASH
```

`ACCEPT`, `EDIT`, `REJECT`, `DEFER` retain admission v1 meanings. `EDIT` accepts
`--edited-fields FILE`, with only the fields allowed by admission. IDs, evidence
and provenance are not editable. An omitted timestamp uses the current UTC time;
an exact retry reuses the existing timestamp. A different historical choice is
a conflict, not an overwrite. One reviewer owns each round.

Alternatively, `submit WORKFLOW --decisions FILE` accepts the existing human
decision envelope (`schema_version`, `package_id`, `package_sha256`, `reviewer`,
`explicit_confirmation: true`, sorted `confirmed_proposal_ids`, `decisions`;
optional `execution_mode: HUMAN_REVIEW`). A submission may enumerate a subset;
confirmation must cover exactly that subset. Each decision includes the exact
proposal hash, action, reason and timezone-aware timestamp. Dependent accepted
Relations need their accepted endpoints in the same batch or an earlier choice.
An invalid batch adds no decision snapshot and creates no canonical artifact.

```bash
./seminartext project-semantic-workflow submit /work/review --decisions /inputs/decisions.json
./seminartext project-semantic-workflow apply /work/review
./seminartext project-semantic-workflow validate /work/review
./seminartext project-semantic-workflow result /work/review > /outputs/revision.json
```

`apply` requires explicit choices for the entire current round. A missing choice
is pending, not a fabricated human DEFER. Rejected/deferred proposals never
create accepted entities. An all-reject result is valid with zero canonical
entities; it is distinct from an invalid or missing input.

`next-round WORKFLOW` reopens only explicitly deferred proposals, referencing
the prior canonical revision as parent and preserving original proposal bytes.
It derives a new package ID/hash without pretending to run the original producer
again. New decisions use that new hash. Existing accepted entities and previous
decisions remain in the immutable parent. Rejected items stay traceable in the
previous snapshots; reconsidering them or authoring new proposals is a new input
workflow, not silent rewriting. Cross-source/revision updates remain unsupported.

## Persistence and semantic authority

Each successful mutation publishes one immutable numbered, hash-linked JSON
snapshot containing the entire current review state and, after apply, the exact
canonical revision returned by the existing compiler. No mutable head pointer or
database is introduced. All operations take a nonblocking process lock. The
existing atomic no-overwrite JSON writer publishes snapshots; incomplete staging
files cannot become committed state. A retry after interruption before publication
uses the previous snapshot; a retry after publication discovers the committed
snapshot. Source inputs are rechecked before publication and on reopening.

For mechanical validation only, the wrapper invokes existing admission using
its system-only or mixed system-DEFER mode for missing choices. The temporary
result and placeholder choices are discarded. They never enter workflow choices,
human decision history or canonical output. Only a fully explicit human ledger
is passed to actual `apply`. Canonical output and derived quotes use the existing
compiler/validators, not copied semantic rules.

`inspect` includes original proposals, generation provenance, transcript assurance,
source locators and actual choices. `status`, `inspect`, `validate` and `result`
recheck current inputs. Missing/stale/malformed input or corrupt history returns
a nonzero error, never an earlier successful result presented as current.

The CLI is available in this source checkout. This task does not extend the
installed deployment inventory or execute deployment. A deployed CLI without
the module reports that the source-checkout workflow is unavailable there.
Future packaging must include the workflow, admission module and admission
schema through the governed deployment procedure; no deployment readiness is
claimed by these source tests.

## Evidence and governance

`tests/fixtures/semantic_workflow/cases.json` supplies unrelated astronomy/Word
and botany/cue examples. The test builder reuses only existing schema scaffolding,
replaces original content/identities, removes semantic/benchmark records and
labels simulated producer and reviewer data explicitly as synthetic. Fresh CLI
processes exercise prepare, inspect, restart, partial submit, mixed outcomes,
apply, validate, exact replay and deferred re-review with immutable parent history.
Negative cases cover stale inputs, malformed/duplicate/unsupported data, forged
producer labels, unsupported edits/actions, unconfirmed/system submissions,
source changes before commit, locks and interrupted publication.

Source baseline: SeminarText `33c3ee030a1ff7b82760ac8a7dde45007e01a303`.
Canonical Unified Rules were resolved and fully read at Integra
`55141b8688996a4ba19f1cffb0930bb61a9561f6`, path
`docs/governance/UNIFIED_CODEX_RULES.md`, SHA-256
`8b8e31c7620d45e1e14429e07e7b97b2adc118745ce781a55b932213c55b646b`.
Product Rules SHA-256:
`b59ba7205120ec1a0dd8fe0f881c26c8056ba7feb61bebd27c7100b59b899492`.
Central architecture/roadmap read at
`475c5f2d826a40f34f234508b83618c64aecd851`; `docs/architecture.md` SHA-256
`61a49437994bd481d9be71bd26a7d24bfff77ae9e04abddf127e9c4c1fcbc9a0`,
`ROADMAP.md` SHA-256
`c9e25d2942c4c8c23ec69949a4671ec69462660b838769494f7987b66fc0e63e`.

PR #121's batch code was inspected for exact confirmation, whole-batch validation
and retry behavior. It remains unmodified and is not imported as a second engine.
Existing human review v1/v2 and project knowledge bridge APIs are unchanged.
PR #157's BookText-first recommendation is superseded by this explicit task;
its audit remains historical evidence, not this task's authority.

PRODUCT_RULES_READ: YES

APPLICABLE_PRODUCT_RULES: PR-001, PR-002, PR-003, PR-004, PR-005, PR-006,
PR-007, PR-008, PR-010, PR-011, PR-012, PR-013, PR-014.

PRODUCT_RULE_CONFLICTS: NONE

Real Issue #68 review, S1 acceptance, S2/S3, Dataset/Gold, models, other products
and installed runtimes are unchanged. Verification results and exact delivery
SHA are recorded in the implementation PR.
