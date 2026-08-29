# Issue #63 — Obsidian Product Review preparation

## Scope and baseline

This packet is a Product Owner `DOMAIN_REVIEW` input, not an acceptance decision. It inspects only the committed PR #54 bounded Obsidian prototype and its accepted Golden Slice/Canonical Evidence inputs. No vault regeneration, semantic edit, bidirectional sync, export implementation, Dataset C/D/E operation, Gold, prediction, or benchmark was performed.

The inspected vault contains 25 generated Markdown notes: one start/index note, one review guide, one Seminar, three Topics, seven Concepts, ten Evidence notes, one Source, and one Canonical Evidence reference. It renders one bounded Golden Slice (`golden_slice_stress_code_video_001_v1`), not the full seminar.

## User journey review

### `00_START_HERE → Seminar → Topic → Concept → Evidence → Source/time`

| Transition | Technical state | Product usability finding |
|---|---|---|
| `00_START_HERE.md` → `Seminars/seminar_stress_code.md` | Link resolves; start note states the slice is derived/disposable. | **GOOD.** Scope and source-of-truth warning are visible before navigation. |
| Seminar → Topic | Three relative links resolve; Seminar frontmatter lists stable `topic_ids`. | **GOOD.** The user retains seminar context and can return through each Topic’s explicit Seminar link. Granularity is understandable for this bounded slice. |
| Topic → Concept | Topic links resolve and frontmatter contains `concept_ids`; one Topic has `gold_complete`, two have `product_review_required`. | **QUESTIONABLE.** Mixed review statuses and the phrase “Concept” do not explain whether the linked item is accepted knowledge or a review hypothesis. |
| Concept → Evidence | Concept notes link evidence and show `derivation_status: provisional_manual_curation`; reverse “Supports provisional Concepts” links exist. | **GOOD/PARTIAL.** Provenance is visible and reversible, but the user must understand that a generated Markdown banner is not a canonical decision. |
| Evidence → Source/time | Evidence notes show Source ID, exact time range, transcript revision, Word range, and timing limitations; Source links back to all slice Evidence. | **GOOD.** `evidence_adaptive_task` resolves to `source_stress_code_video_001`, `00:10:00.140–00:10:09.950`, words `000000–000013`. No media URI/open action is provided. |
| Backtracking/context | Explicit links and normal Obsidian backlinks provide return paths; no explicit breadcrumb component is generated. | **PARTIAL.** The graph is navigable, but a non-technical user can lose context when arriving at an Evidence note because the Seminar/Topic path is not repeated as a breadcrumb. |

The chain is therefore technically complete but product-usability `PARTIAL`: provenance survives every hop, while source playback, review state, and context recovery need adaptation.

## Note-type assessment

| Note type | Classification | Evidence and reason |
|---|---|---|
| Start/index (`00_START_HERE.md`) | `USEFUL` | Stable entry point, explicit derived-view warning, links to Seminar/Source/canonical reference/review guide, and bounded counts. |
| Seminar (`Seminars/seminar_stress_code.md`) | `USEFUL` | Preserves project identity, source link, and three Topic links; clearly says it is not the full seminar. |
| Topic (`Topics/*.md`) | `NEEDS_ADAPTATION` | Useful summaries and source intervals, but review-state inconsistency (`gold_complete` vs `product_review_required`) and no explicit “derived/non-canonical” badge in the main body. `topic_personal_professional_kinesiology` also exposes two unaligned Word IDs that need a user-facing explanation. |
| Concept (`Concepts/*.md`) | `NEEDS_ADAPTATION` | Provisional banner and evidence links are valuable, but aliases are inconsistent (one alias across seven Concepts), no canonical review decision field, and no merge/split/rename identity policy. |
| Evidence (`Evidence/*.md`) | `USEFUL` | Claim, canonical excerpt, Source ID, time, transcript revision, Word range, timing limitations, and reverse links are explicit. `evidence_problem_resolution_with_unaligned_words` correctly exposes two unaligned Words rather than inventing timing. |
| Source (`Sources/source_stress_code_video_001.md`) | `NEEDS_ADAPTATION` | Immutable ID, duration, content hash, and Evidence index are clear; there is no resolver key/URI to open the actual local media and no missing-source state. |
| Review/status artifacts (review guide, frontmatter statuses, manifest) | `NEEDS_ADAPTATION` | Review is visibly pending, but statuses are strings rather than a canonical `ReviewDecision` contract with actor, timestamp, rationale, and immutable target revision. |

No note type is wholly redundant. Some provenance text is intentionally repeated for readability; the repetition is acceptable until a stable UI contract exists.

## Concept usability

**Finding: `CONCEPT_MODEL_USABILITY = PARTIAL`.** The seven Concepts are explicitly `provisional_manual_curation`, carry stable IDs, link back to Topics and Evidence, and display “PROVISIONAL — Product Review required.” This prevents silent promotion but does not fully prevent a polished note from being mistaken for confirmed knowledge.

- Labels are understandable in several cases (`concept_adaptation_to_environment`, `concept_sabotage_as_internal_resistance`) but not consistently sufficient for search. Only `concept_adaptation_to_environment` has an alias (`адаптивность`); six Concepts have empty alias arrays.
- Provenance is readable: `concept_survival_in_changing_environment` links to two Topics and two Evidence notes. The identity rationale explicitly says it is a manual grouping, which is good evidence hygiene.
- Safe rename is not defined. A filename is not canonical identity, but there is no redirect/alias/rename ledger to preserve incoming links.
- Duplicate, merge, split, and erroneous-concept handling is absent. A future workflow needs stable Concept ID, supersedes/superseded-by links, retained evidence membership, and a human decision record. Autonomous semantic merge/split must remain prohibited.

## Human review workflow

The current `product_review_required`/`provisional_manual_curation` markers are a useful warning, but **`REVIEW_WORKFLOW_READY = NO`** for production use. The minimum canonical contract should record:

`ReviewDecision = {target_stable_id, action, reviewer_role, decision_at, rationale, evidence_refs, source_revision, supersedes}` where `action ∈ {ACCEPT, RENAME, SPLIT, MERGE, REJECT, DEFER}`.

These actions are recommendations for a Product Owner/domain reviewer only. Codex performed none of them.

## Generated versus user-edited ownership

Current exporter behavior is deterministic and writes stable-ID filenames, but it overwrites every managed Markdown file on the next export. It refuses to delete unmanaged Markdown, which is a good safety boundary, yet it does not preserve edits inside managed files or detect content collisions. All prototype notes carry `generated_by` and `lifecycle_status: derived_view`, but there is no explicit managed/unmanaged marker or edit policy in the manifest.

Recommended ownership contract (not implemented):

- Canonical JSON/evidence, manifest, and generated Markdown are fully generated and read-only from the vault’s perspective.
- User annotations must live in separate unmanaged notes keyed by stable ID, or in an explicitly reserved non-generated section that the exporter never rewrites.
- Re-export may replace only byte-identical or explicitly managed generated files; it must refuse changed managed files unless `--force` is separately approved.
- Stable IDs survive renames; old filenames become redirect stubs or manifest aliases. Unmanaged deletion is never performed. Collisions stop the export and produce a report.
- No bidirectional synchronization is authorized by this review.

Therefore **`GENERATED_VS_USER_OWNERSHIP_READY = NO`**.

## `project-obsidian-export` contract

The existing `export_obsidian_vault.py` proves bounded deterministic generation, manifest hashes, stable IDs, portable relative links, and refusal to delete unmanaged Markdown. It accepts explicit slice/canonical/output/manifest paths, but it is not a project-level product command.

Required contract elements not yet accepted/implemented: `input project`, `dry-run`, managed-file markers, collision report, changed-managed-file protection, rename/deletion policy, and a portable Source resolver. Consequently:

**`PROJECT_OBSIDIAN_EXPORT = BLOCKED`** — blocker is the missing Product Owner-approved ownership/collision/source-resolution contract, not a missing copy routine. Do not create the command merely to close this issue.

## Portable Source resolver

The vault is portable in the narrow sense that it contains no personal absolute paths. A Source note has `source_stress_code_video_001`, duration, and SHA-256, but no local media/document URI or resolver invocation. `Evidence` can identify `00:10:00.140–00:10:09.950`, yet cannot open the video from the note.

Recommended contract: keep `source_id` and immutable content hash in the vault; resolve them through a project-local, user-specific resolver/config outside generated notes (for example `project_sources.json` ignored from publication). A moved project supplies a new resolver root; missing sources render `SOURCE_UNAVAILABLE` with the exact ID/hash and never silently retarget. The vault remains portable and must not contain personal absolute paths. Because this contract is not implemented or Product Owner-approved, **`SOURCE_RESOLVER_CONTRACT_READY = NO`**.

## Required limitation examples

### `GOOD`

1. `00_START_HERE.md` → `Seminars/seminar_stress_code.md` → `Topics/topic_stress_adaptation_survival.md` is a clear bounded path; Topic interval is `00:10:00.140–00:11:31.518`.
2. `Concepts/concept_adaptation_to_environment.md` visibly says provisional, links to its Topic and `Evidence/evidence_adaptive_task.md`.
3. `Evidence/evidence_adaptive_task.md` exposes a short quote, Source ID, exact time, transcript revision, Word range, and canonical JSON pointer.

### `QUESTIONABLE`

1. `Concepts/concept_survival_in_changing_environment.md` is reused by two Topics, but the vault gives no review decision explaining whether this is intentional reuse or a duplicate candidate.
2. `Topics/topic_personal_professional_kinesiology.md` shows two unaligned Word IDs (`...:word:000970`, `...:word:000971`) and an aligned envelope `00:16:10.901–00:20:58.237`; this is truthful but not easily actionable for a reader.
3. Topic `review_status` differs (`gold_complete` versus `product_review_required`) without a status legend on the Topic note.

### `MISLEADING`

1. Concept notes look like polished knowledge cards while their only visible caveat is a banner; a casual user may miss `provisional_manual_curation`.
2. `Sources/source_stress_code_video_001.md` is titled as a source and has a hash/duration, but clicking it does not open or locate the actual media.
3. `PRODUCT_OWNER_REVIEW_GUIDE.md` is itself generated and says “Product Review has not been completed”; manually editing it would be overwritten on export, which is not obvious from the note alone.
4. Frontmatter is emitted as JSON/YAML and contains internal artifact hashes/IDs; this preserves auditability but creates information density that can obscure the user-facing claim.

### `MISSING_FOR_REAL_USE`

1. Canonical ReviewDecision records for Concept actions.
2. Stable rename/redirect and duplicate/merge/split ledger.
3. Managed/unmanaged markers and changed-managed-file collision handling.
4. Dry-run and project-level export contract.
5. Portable Source resolver and explicit `SOURCE_UNAVAILABLE` state.
6. Breadcrumb/context component from Evidence back to Seminar/Topic.
7. User-editable annotation area that export never overwrites.
8. Full-seminar/multi-source coverage and a product-level acceptance status.

## Product options (no Codex decision)

| Option | User value | Risks | Remaining work | 4.0 MVP / export / #64 impact | Further DOMAIN_REVIEW |
|---|---|---|---|---|---|
| `ADOPT` | Immediate bounded knowledge browsing with strong evidence traceability. | Provisional Concepts, no source resolver, and overwrite risk can mislead or lose edits. | Accept review contract, ownership rules, resolver, and UX safeguards first. | High MVP risk; `project-obsidian-export` still blocked until prerequisites land; #64 should wait. | Yes, required before production use. |
| `ADAPT FURTHER` | Addresses Concept decisions, ownership, collisions, and source playback before adoption. | More design effort and delayed value. | Implement the contracts above and validate on broader sources without changing canonical truth. | Medium/high cost; enables a safer future export and allows #64 planning after review. | Yes. |
| `KEEP AS PROTOTYPE` | Preserves a useful, reproducible derived UI with minimal operational risk. | No supported user editing/export workflow; limited slice value. | Retain artifacts, document limitations, revisit after canonical contract work. | Low MVP impact; export remains blocked; #64 can proceed only as a separate contract review if dependencies are satisfied. | Yes for any expansion. |
| `REJECT` | Avoids maintenance and semantic-authority confusion. | Loses a readable evidence view and prototype learnings. | Archive immutable artifacts and rely on canonical JSON/other views. | Low implementation cost; export not implemented; #64 is unaffected. | Only to record rejection rationale. |

Product Owner must choose one option. Codex selects none.

## Product Owner disposition and adaptation contract

`ISSUE_63_DECISION: ADAPT_FURTHER` is recorded as a Product Owner disposition. `OBSIDIAN_DIRECTION: ACCEPTED` means Obsidian remains the target derived UI / knowledge workspace; it does not make the current prototype production-ready.

Machine-readable companion: `analysis/obsidian_knowledge_prototype/product_review_disposition.json`.

### A. Canonical ReviewDecision (handoff to #64)

The canonical semantic decision must be recorded outside the vault:

`ReviewDecision = {target_stable_id, action, reviewer_role, decision_at, rationale, evidence_refs, source_revision, supersedes}` with `action ∈ {ACCEPT, RENAME, SPLIT, MERGE, REJECT, DEFER}`.

The Obsidian note is never authoritative. The canonical record is the source for a rebuild. Concept identity, aliases, merge/split/rename semantics, relation versioning, and provenance references belong to #64. This contract is specified (`REVIEW_DECISION_CONTRACT: READY`) but not implemented here.

### B. Generated/user ownership (owned by #63)

Use exactly two ownership classes:

- `MANAGED_GENERATED`: exporter-owned files, replaceable only when generated content is unchanged or an explicit safe rebuild is authorized.
- `USER_OWNED`: notes/annotations never overwritten or deleted by export.

Every export must be idempotent, preserve stable IDs, detect collisions, refuse changed managed files by default, retain rename aliases/redirects, and never delete unmanaged notes. User edits are kept in `USER_OWNED` notes keyed by stable ID. Bidirectional synchronization is out of scope. Contract is specified (`GENERATED_USER_OWNERSHIP_CONTRACT: READY`), implementation is not.

### C. Portable Source resolver (owned by #63)

`source_id → project/local resolver → actual local media/document URI` remains external to generated Markdown. Resolver states are explicit: `AVAILABLE`, `MOVED`, `PROJECT_MOVED`, `MISSING`, and `RESOLVER_UNAVAILABLE`. A moved project supplies a new local resolver root; a missing source reports ID/hash and never silently retargets. Personal absolute paths are not canonical vault identity. Contract is specified (`SOURCE_RESOLVER_CONTRACT: READY`), implementation is not.

### D. Future `project-obsidian-export` contract (owned by #63)

Required inputs/behavior: project input, destination, `--dry-run`, manifest, managed-file inventory, stable IDs, collision detection, idempotency, no deletion of unmanaged notes, Source resolver integration, and safe fail-closed behavior. The contract is specified (`EXPORT_CONTRACT: READY`), but `PROJECT_OBSIDIAN_EXPORT = BLOCKED` until Product Owner accepts the ownership/resolver/collision prerequisites. No command is created in Issue #63.

## Eight missing-for-real-use findings mapped to contracts

| # | Finding | Root cause | Required contract | Target issue | BLOCKS_MVP |
|---:|---|---|---|---|---|
| 1 | No canonical Concept review decisions | Vault statuses are presentation strings; no immutable decision record exists. | Canonical `ReviewDecision` with six actions, reviewer, rationale, evidence and source revision. | #64 | YES |
| 2 | No stable rename/duplicate/merge/split ledger | Filename stability is documented, but semantic identity transitions are undefined. | Concept identity/alias/supersession ledger with redirect links and retained provenance. | #64 | YES |
| 3 | No managed/unmanaged collision protection | Exporter overwrites generated Markdown and only refuses unmanaged deletion. | Two-class ownership markers, changed-managed-file refusal, collision report, no unmanaged deletion. | #63 | YES |
| 4 | No project-level dry-run export contract | Current script accepts bounded slice paths and writes directly; it has no project input or dry-run. | `project-obsidian-export` input/destination/dry-run/manifest/idempotency/safe-failure contract. | #63 | YES |
| 5 | No portable Source resolver | Source notes contain ID/hash/time but no resolver key or local media URI. | Project/local resolver with AVAILABLE/MOVED/PROJECT_MOVED/MISSING/RESOLVER_UNAVAILABLE states. | #63 | YES |
| 6 | No breadcrumb/context component | Backlinks exist, but Evidence does not repeat Seminar → Topic context. | Presentation breadcrumb/context links that preserve stable IDs and return path. | #63 | NO |
| 7 | No protected user annotation ownership | There is no user-owned note class or reserved non-generated area. | `USER_OWNED` annotation notes keyed by stable ID, never overwritten by rebuild. | #63 | YES |
| 8 | Bounded one-source coverage only | Export is hard-coded to one Golden Slice and one source; no multi-source acceptance state exists. | Project scope/coverage manifest and explicit acceptance status before broader export. | #63 | YES |

All eight findings now have a root cause, required contract, target issue, and MVP impact. None was fixed by editing real knowledge.

## Technical self-check boundary

The accepted pre-review baseline was verified on `main` at `451fce016f0346511b3fc0eb88ad39392c534b4a`: G1–G4/G8 PASS, G5/G6 NOT_IMPLEMENTED, G7 known WARN with `141 passed, 2 skipped`, and PROJECT_INTEGRITY PARTIAL. Dataset D remains BLOCKED with blind run authorization NO. No implementation, export command, canonical contract change, semantic edit, or Dataset operation was performed.

`HUMAN_GATE: DOMAIN_REVIEW` is required. `SAFE_TO_COMPLETE_#63: NO`; `SAFE_TO_START_#64: NO`.
