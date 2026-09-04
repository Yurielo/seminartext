# Issue #113 — Topic Engine Root-Cause and Generalization Analysis

Status: **analysis complete; no engine, prediction, Gold, Dataset, transcript,
runtime, or semantic-decision mutation**.

This report separates observed evidence, supported hypotheses, unknowns, and
future regression requirements. Product Owner decisions remain the semantic
authority. Causal labels in this report are engineering analysis, not new
semantic decisions.

## 1. Scope and source integrity

The analysis uses only `Стресс код / source_video_001` evidence already
authorized for Issue #113.

| Input | SHA-256 |
| --- | --- |
| governed V2 decisions | `32a18a6dc9d3edbd53753153f533221e9c0fe6d54856355af9d52a3db41e772e` |
| deterministic applied result | `efd62ec72ce0e45623da1bc1417d632ec982bf5be33070df2ef4f590823e4f69` |
| Human Review package | `044f4bbc74af874addc5597f677d227bac9aec642d424744b10c877f78714de1` |
| machine Topic Draft source | `b45f49b185fe1c96e7962226868cfb776a2478dfa1be846d0be0fd55538a6ecb` |
| Canonical Evidence bundle | `40879d5a87cd1a8ea7869d51e81aa7f93cfc48bc34cb5858e5664363ee687273` |
| Word Timeline | `9929686e693e653e6cd98048f401b422bb654404050281c7a2a2df714f714b6f` |

The applied result is `APPLIED`: 31/31 decisions, 57 fragments, 36
`SEMANTIC_KNOWLEDGE`, one `SEMINAR_STRUCTURE`, and four
`NON_SEMANTIC_EXCLUDED` units. The original 31 Topic Draft snapshots remain
preserved. Transcript provenance remains `machine_generated` /
`existing_machine_transcript_import` / `machine_unverified`.

Dataset D was not opened or used. Dataset E remains
`EXCLUDED_FROM_TOPIC_ENGINE_EVIDENCE`. No Gold, predictions, or model output was
created or changed.

## 2. Critical provenance finding

### Observed

The reviewed drafts identify their source as:

- Topic set: `topic_set_stress_code_video_001_legacy_gemma3_4b_v1`;
- generator: `generator_legacy_gemma3_4b_conversion_v1`;
- model: `gemma3:4b`;
- detail: `auto`.

They were **not** produced by `bge_m3_local_peak_v1`. No embedding vectors,
change scores, local peaks, or threshold decisions are stored with these 31
drafts. `topics_candidates.json` stores the 31 chosen candidates but no boundary
features/scores.

### Consequence

Issue #113 is valid evidence about the legacy Gemma Topic Draft pipeline. It is
not a scored evaluation of the frozen Local Peak candidate. Embedding semantic
similarity, peak detection, and threshold behavior are therefore `UNKNOWN` for
these 31 drafts and cannot be named as proven causes. Doing so would collapse
two different engine lifecycles and create false provenance.

The historical draft artifact also binds a generator/configuration identity but
not the exact repository implementation hash or a per-window execution ledger.
The current governed legacy implementation is relevant explanatory evidence,
but exact historical control flow remains a supported hypothesis rather than a
replayed fact.

## 3. Failure taxonomy

All 31 source Topic Drafts are mapped in
`analysis/issue_113_failure_matrix.json`. Counts overlap because one draft may
have segmentation, title, transcript, and hierarchy failures simultaneously.

| Failure class | Count | Topic numbers |
| --- | ---: | --- |
| `OVER-MERGE` | 6 | 4, 5, 6, 11, 12, 14 |
| `FALSE SPLIT` | 5 | 18, 20, 22, 26, 27 |
| `BOUNDARY_OFFSET` | 16 | 5, 6, 8–12, 19, 21, 23–25, 27, 28, 30, 31 |
| `BOUNDARY_OFFSET / TRANSITION_SPLIT` | 6 | 9, 10, 23, 27, 28, 30 |
| `BOUNDARY_OFFSET_BOTH_SIDES` | 5 | 5, 6, 8, 11, 21 |
| `BOUNDARY_OFFSET / SENTENCE_SPLIT` | 3 | 12, 19, 25 |
| `BOUNDARY_OFFSET / Q&A_SPLIT` | 2 | 24, 31 |
| `FALSE SPLIT / SENTENCE_OR_ARGUMENT_SPLIT` | 2 | 26, 27 |
| `DISCOURSE_FUNCTION_BOUNDARY_MISSED` | 1 | 14 |
| `NON_SEMANTIC_CONTENT_CONTAMINATION` | 3 | 8, 9, 23 |
| `NON_SEMANTIC_TRANSITION_AS_TOPIC` | 1 | 22 |
| `PROTOCOL_STEP_AS_FALSE_TOPIC` | 2 | 18, 20 |
| `FALSE SPLIT / PROCEDURAL_FRAGMENTATION` | 2 | 18, 20 |
| `FALSE SPLIT / CONTINUOUS_TOPIC_FRAGMENTATION` | 1 | 22 |
| `TITLE_LOCAL_FRAGMENT_BIAS` | 24 | 2, 3, 5–7, 9–11, 14, 16–30 except 31 |
| `TITLE_EARLY_FRAGMENT_BIAS` | 8 | 4, 8, 12, 15, 21, 22, 29, 31 |
| `MALFORMED_TITLE / VERBATIM_FRAGMENT_AS_TITLE` | 6 | 1, 4, 8, 12, 15, 31 |
| `TRANSCRIPT_DUPLICATION_SIGNAL` | 1 | 22 |
| `SEMINAR_STRUCTURE_VS_KNOWLEDGE_TOPIC / INSTRUCTIONAL_TRANSITION` | 1 | 28 |
| `PROCEDURAL_HIERARCHY / DO_NOT_SPLIT_STEPS_INTO_TOPICS` | 4 | 26, 27, 29, 30 |

Controls are equally important:

| Control | Topic numbers |
| --- | --- |
| `VALID_LONG_TOPIC` | 7, 13 |
| `VALID_SHORT_TOPIC / DISCOURSE_FUNCTION_CHANGE` | 23 |
| `VALID_SHORT_TOPIC / Q&A_SEMANTIC_UNIT` | 24 |
| `VALID_SHORT_TOPIC / SECTION_OVERVIEW` | 25 |
| `PROCEDURAL_CONTINUITY / DO_NOT_OVERSPLIT` | 16 |
| `NARRATIVE_CONTINUITY / DO_NOT_OVERSPLIT` | 17 |
| `DO_NOT_FIX_OVERMERGE_BY_BLIND_OVERSPLITTING` | 16, 17, 29, 30 |
| `Q&A_SEMANTIC_UNIT` | 24, 31 |

## 4. Boundary error analysis

`BOUNDARY_ERROR_COUNT=29` has an explicit definition: 26 changed authoritative
human anchors plus three unmatched machine-only boundaries. Of the 26 changed
anchors, 15 have a semantically corresponding machine boundary and 11 were
entirely missing.

- early machine boundaries: **10**;
- late machine boundaries: **5**;
- missing machine boundaries: **11**;
- extra machine-only boundaries: **3**.

For paired boundaries, displacement is `machine - human`; negative means the
machine boundary was early.

| Human boundary | Machine topic start | Words | Seconds | Class |
| --- | --- | ---: | ---: | --- |
| `04c_05b` 2449 | Topic 5, 2328 | -121 | -120.323 | early |
| `05d_06a` 3072 | Topic 6, 3168 | +96 | +71.169 | late |
| `07_08` 5125 | Topic 8, 5126 | +1 | +0.420 | late |
| `09_left` 6290 | Topic 9, 6128 | -162 | -92.481 | early |
| `10_left` 7263 | Topic 10, 7180 | -83 | -81.272 | early |
| `10_11a` 8317 | Topic 11, 8268 | -49 | -31.780 | early |
| `11b_12a` 9468 | Topic 12, 9445 | -23 | -15.529 | early |
| `19_left` 16347 | Topic 19, 16356 | +9 | +4.867 | late |
| `21_left` 18872 | Topic 21, 17768 | -1104 | -687.010 | early |
| `21_22_nonsemantic` 19578 | Topic 22, 18925 | -653 | -458.288 | early |
| `23_left` 19671 | Topic 23, 19592 | -79 | -42.045 | early |
| `25_left` 20014 | Topic 25, 20026 | +12 | +7.701 | late |
| `28_left` 20490 | Topic 28, 20443 | -47 | -32.080 | early |
| `30_left` 21687 | Topic 30, 21642 | -45 | -21.732 | early |
| `31_left` 22680 | Topic 31, 22821 | +141 | +75.069 | late |

Missing anchors are 1517, 2065, 2529, 2756, 3443, 3895, 6096, 8603,
10501, 12386, and 20482. Machine-only extras are Topic 18 at 16177, Topic
20 at 16519, and Topic 27 at 20280. Exact IDs, timestamps, transition types,
and all 29 records are in the matrix JSON.

### Dominant problem

The verdict is **E. mixed**. Boundary existence/non-existence is substantial
(11 missing + 3 extra), localization is independently substantial (15 paired
offsets), and discourse/structure/hierarchy errors explain why some boundaries
should or should not exist. A single distance or threshold metric is
insufficient.

## 5. Topic 4–6 deep dive

### Observed machine result

| Draft | Machine words | Machine time | Window relation |
| --- | --- | --- | --- |
| Topic 4 | 1135–2327 | 731.310–1449.592 | begins fixed window 2 at SRT 105 |
| Topic 5 | 2328–3167 | 1451.340–2171.629 | begins fixed window 3 at SRT 206 |
| Topic 6 | 3168–4060 | 2172.411–2898.819 | begins fixed window 4 at SRT 288 |

The Product Owner result instead contains 4A 1135–1516, 4B 1517–2064,
4C 2065–2448, 5B 2449–2528, 5C 2529–2755, 5D 2756–3071, 6A
3072–3442, 6B 3443–3894, and 6C 3895–4060. Thus 4C crosses the machine
window boundary at 2328, and 6A crosses the machine boundary at 3168.

Across the whole file, 20 of 22 fixed analysis-window starts are also final
machine Topic starts. Topics 4–17 form **14 consecutive** window-start-anchored
Topics. The historical `topics_window_02_raw.txt` violates the current
Russian-JSON contract, and Topic 4's title exactly equals the legacy
`fallback_row` first-eight-word title for window 2.

### Supported causal assessment

| Candidate cause | Finding |
| --- | --- |
| embedding similarity | **not applicable/proven**: these drafts are legacy Gemma, not BGE Local Peak |
| local peak behavior | **not applicable/proven**: no peak/score artifact exists |
| thresholding | **unknown**: no scored threshold decision is recorded; mixed missing/extra errors argue against one global adjustment |
| minimum/maximum duration | hard minimum alone does not explain 12-minute Topics; current refinement has a maximum but historical execution is not ledger-bound |
| local-window effects | **high-confidence likely cause**: exact 720-second window alignment dominates Topics 4–17 |
| discourse/speaker transitions | **medium-confidence missed signal**: participant→instructor and procedure→question transitions are authoritative missing anchors |
| sentence-boundary effects | contributes to individual offsets, not the central 4–6 over-merge |
| long-form narrative continuation | machine windows split 4C and 6A despite continuity across the window edge |
| seminar procedural structure | contributes to which changes deserve hierarchy rather than top-level splitting |
| title generation | separate defect; it cannot explain missing boundaries but makes Topic 4 look like a transcript fragment |

**Root-cause classification:** factual origin is the legacy Topic Draft boundary/
grouping path. The most supported explanation is
`TOPIC_DRAFT_GROUPING_DEFECT + EXPECTED_MODEL_LIMITATION`, with a
high-confidence local-window anchoring interaction and likely
`POST_PROCESSING_OVERMERGE` when contract recovery/fallback yields only a window
anchor. `SEGMENTATION_ALGORITHM_MISSED_BOUNDARY` describes the observed result;
`THRESHOLD_TOO_CONSERVATIVE` is not proven.

## 6. Raw model contract and title/summary analysis

Post-hoc application of the current contract checker marks all **22/22**
historical `topics_window_NN_raw.txt` files as contract violations. Most begin
with English explanatory prose; JSON-looking responses retain terminal/control
noise. This does not prove which retry was selected in every historical window,
because no `topics_qa.json` execution ledger accompanies the result. It does
prove that raw contract reliability was poor.

Additional observations:

- 31/31 machine titles were changed or eliminated by the accepted review;
- 23/31 drafts also had segmentation changes, so bad boundaries often polluted
  title evidence;
- the eight unchanged-boundary controls (1, 2, 3, 7, 13, 15, 16, 17) still
  required title changes, proving an independent label-quality problem;
- 24 drafts show local-fragment bias, eight early-fragment bias, and six
  malformed/verbatim-title behavior under the accepted taxonomy;
- five titles (Topics 4, 8, 12, 15, 31) exactly match the deterministic legacy
  first-eight-word fallback;
- 9/31 machine summaries are empty; many non-empty summaries contain repeated
  partial tokens/control-stream corruption.

The current two-stage implementation passes the complete in-window
`segment_range` to the label prompt. The historical artifact does not bind a
per-range prompt/response/implementation ledger, so truncation versus fallback
cannot be assigned per title beyond the five exact fallback matches.

### Title regression requirements

1. Run title QA independently from boundary QA.
2. Bind each title/summary to its exact evidence range and generation attempt.
3. Reject first-N-word/verbatim fallbacks as accepted titles; fallback must
   remain explicitly `REVIEW_REQUIRED`.
4. Assert whole-span coverage on unchanged-boundary controls before attributing
   title failure to segmentation.
5. Preserve raw response and selected attempt without terminal-stream
   corruption.

No title was regenerated in this task.

## 7. Semantic Knowledge, Seminar Structure, and non-semantic content

The reviewed result contains 36 Knowledge Topics, one structural unit, and four
excluded units. The legacy output had only a flat Topic type, so local changes
were forced into Topic-like units or contaminated adjacent Topics.

Representative evidence:

- 6096–6127: technical audio/break fragment;
- 6128–6289: technical transition;
- 19578–19591: gratitude/end-of-demo transition;
- 19592–19670: initial thanks;
- 20490–20586: instructional preparation retained as `SEMINAR_STRUCTURE`, not
  Canonical Knowledge.

Required separation is a disposition decision after boundary localization:
`SEMANTIC_KNOWLEDGE`, `SEMINAR_STRUCTURE`, or `NON_SEMANTIC_CONTENT`. Silence,
break language, logistics, gratitude, and viewing instructions are useful
signals but are not sufficient rules by themselves. Classification still
requires reviewed semantic/discourse context.

## 8. Procedural and narrative hierarchy

Topics 18 and 20 were protocol steps incorrectly promoted to peer Topics.
Topics 26/27 split one theory/argument block at 20280; the authoritative
theory→practice transition is 20482. Topics 29/30 establish one useful
top-level procedural transition at 21687 while explicitly rejecting a Topic per
pretest step. Topics 16 and 17 are negative controls for procedural and
narrative continuity.

The engineering requirement is a representation capable of:

`Topic -> subtopic / procedural step / narrative continuation`

without assuming that numbered steps, speaker changes, questions, duration, or
local lexical change are top-level boundaries. This is a future fix class, not
an implementation or Product Owner hierarchy choice in this task.

## 9. Transcript-signal limitations

Topic 22 begins with a phrase repeated many times in the machine transcript.
The reviewed boundary outcome remains valid, but the repetition is a
`TRANSCRIPT_ARTIFACT` signal that can distort local similarity, grouping, and
label salience. Whether the source audio actually repeats is unresolved and
requires selective verification under PR-012 before using this neighborhood to
diagnose model behavior precisely.

At word 21687 the machine transcript says `Мирьяны, передняя средина мирьян`.
The human-reviewed terminology correction is `Меридианы, передне-срединный
меридиан`. It is preserved as correction provenance; TranscriptRevision was not
rewritten. This is a TranscriptRevision error with a possible title/semantic
interaction, not proof of a boundary-engine error.

Other machine-unverified transcript imperfections and partial-token corruption
make attribution ambiguous where model output and input transcript are both
noisy. The correct classification is `TRANSCRIPT_ARTIFACT + EXPECTED_MODEL_LIMITATION`
until selectively verified, not silent evidence correction.

## 10. Root-cause priorities

### P0 — blocks trustworthy semantic automation

1. **Engine provenance must not be conflated.**
   - EVIDENCE: all 31 drafts bind legacy Gemma; no BGE scores are attached.
   - LIKELY_CAUSE: legacy evidence was later viewed beside a frozen candidate
     lifecycle without a per-prediction implementation/score binding.
   - CONFIDENCE: high.
   - POTENTIAL_FIX_CLASS: bind prediction sets to implementation/config/model
     digest plus raw boundary features and selected attempt.
   - REGRESSION_TEST: reject a diagnostic report that attributes a prediction
     to an engine absent from its provenance.
   - RISK_OF_OVERFIXING: low; provenance binding changes no semantics.

2. **Fixed-window anchoring under model-contract failure dominates a major
   region.**
   - EVIDENCE: 20/22 window starts are Topic starts; Topics 4–17 are 14
     consecutive window-aligned Topics; 4C and 6A cross those edges; all 22 raw
     files violate the current contract; five final titles match fallback.
   - LIKELY_CAUSE: local-window boundary generation plus recovery/fallback or
     aggregation that preserves the mandatory first window anchor and loses
     internal semantic boundaries.
   - CONFIDENCE: high for window effect, medium for the exact historical retry
     path because the QA ledger is absent.
   - POTENTIAL_FIX_CLASS: separate coverage windows from semantic boundaries;
     fail closed on contract failure; persist attempt-selection QA.
   - REGRESSION_TEST: R001–R005.
   - RISK_OF_OVERFIXING: high if solved by unconditional smaller windows.

3. **Over-merge and false split coexist.**
   - EVIDENCE: six over-merged drafts, five false-split drafts, 11 missing and
     three extra boundaries, plus long/short continuity controls.
   - LIKELY_CAUSE: discourse/hierarchy representation and recovery behavior,
     not one monotonic global threshold.
   - CONFIDENCE: high for symptom, medium for implementation mechanism.
   - POTENTIAL_FIX_CLASS: multi-signal boundary/disposition model with positive
     and negative controls.
   - REGRESSION_TEST: all R and N cases must pass together.
   - RISK_OF_OVERFIXING: critical; lowering one threshold may fix missing
     boundaries while breaking Topics 7, 13, 16, and 17.

### P1 — major quality issues

1. **Title/summary generation is independently unreliable.** Evidence and
   regression: five exact fallbacks, nine empty summaries, unchanged-boundary
   rename controls; T001–T003. Potential fix class: evidence-bound two-stage
   labeling with explicit fallback status. Risk: cosmetic title scoring can
   hide semantic-span failure.
2. **Discourse/structure classification is absent from the flat output.**
   Evidence: four exclusions and one structural unit. Regression: R006, R009,
   R012. Potential fix class: post-boundary disposition with fail-closed human
   review. Risk: over-filtering useful short Topics.
3. **Procedure steps are confused with Topic hierarchy.** Evidence: Topics 18,
   20, 26–30. Regression: R008, R011, N003, N008. Potential fix class:
   top-level Topic plus subordinate step representation. Risk: hiding real
   theory→practice transitions.
4. **Q&A must be grouped by question+answer, not local form.** Evidence: Topics
   24 and 31. Regression: R013, N006. Potential fix class: discourse-pair span
   features. Risk: merging unrelated follow-up questions.

### P2 — useful improvements

- sentence-complete boundary localization (R010 and Topic 19);
- raw response/attempt ledger and boundary-feature observability;
- selective transcript verification for Topic 22 and critical terminology;
- separate structural and semantic quality metrics.

### P3 — minor

- spelling/orthographic title defects that do not change semantic identity;
- presentation formatting after semantic-span and provenance requirements pass.

## 11. Generalization verdict

Likely general across seminar videos: fixed-window artifacts, model JSON/language
contract failures, title local/early bias, non-semantic transitions,
lecture/Q&A discourse boundaries, and procedure-step hierarchy. Potentially
Stress-Code-specific: named methods, the exact Topic 22 duplication, the
meridian terminology error, and the particular correction protocol sequence.

Issue #113 can immediately define regression fixtures for the exact reviewed
source, but it cannot prove cross-video error rates or the frozen Local Peak
candidate's behavior.

```text
GENERALIZATION_VERDICT: SYSTEMATIC_RISK_SUPPORTED_SINGLE_VIDEO_RATE_UNVERIFIED
ADDITIONAL_VIDEO_EVIDENCE_REQUIRED: YES
ADDITIONAL_MODEL_TRAINING_REQUIRED: INCONCLUSIVE
CROSS_VIDEO_GENERALIZATION_TEST_REQUIRED: YES
ADDITIONAL_CROSS_VIDEO_EXPERIMENT_REQUIRED: YES
```

No training decision is justified yet. The dominant proven problems include
pipeline/provenance, recovery, disposition, and title generation; they are not
evidence of learned-model insufficiency by themselves.

Minimum future design (not authorized or executed here):

1. one additional video from the same seminar and one from a different seminar;
2. predeclared coverage of lecture, Q&A, demonstration, procedure, transitions,
   long coherent Topics, and short discourse-function Topics;
3. human review only of predeclared boundary neighborhoods and should-not-split
   spans;
4. measure class counts, exact/tolerance boundary precision/recall, missing vs
   extra, disposition accuracy, long/short control preservation, and title
   whole-span coverage;
5. keep development/calibration evidence separate from untouched validation;
   do not use Dataset D and keep Dataset E excluded;
6. decide whether model training is justified only after the same defect
   remains when deterministic pipeline/contract defects are separated.

## 12. Regression packet

`analysis/issue_113_regression_design.json` defines 24 bounded cases:

- 13 positive behavior cases (`SHOULD_SPLIT`, `SHOULD_MOVE_BOUNDARY`, remove
  false boundaries, exclude non-semantic content, or classify structure);
- eight negative controls (`SHOULD_NOT_SPLIT` / `VALID_EXISTING_TOPIC`);
- three independent title-generation cases.

These are review-derived development fixtures, not automatic Gold and not a
Dataset-role change. Exact accepted anchors are used only for this source.

## 13. Recommended next authorization boundary

The deterministic Issue #113 analysis is complete. The next boundary is
Product Owner review of PR #114 and selection/authorization of a future fix or
cross-video validation task. Do not merge, deploy, tune, retrain, access Dataset
D/E, or begin another Issue under this analysis authorization.
