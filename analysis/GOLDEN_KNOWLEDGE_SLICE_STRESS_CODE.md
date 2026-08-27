# Golden Seminar Knowledge Slice — Стресс код

Date: 2026-08-27

Issue: #44

Verdict: `GOLDEN_KNOWLEDGE_SLICE_ACCEPTED`

## Outcome

A bounded Knowledge Product vertical slice now demonstrates the complete path:

```text
Seminar → Topic → Concept → Evidence
                         ↓
Canonical Word range → Source → absolute video time
```

and reverse navigation:

```text
Concept → Topics where used → supporting Evidence → source time
```

The slice uses the accepted `Стресс код` Canonical Evidence bundle from Issue
#42. It contains one existing Dataset A Gold topic and two explicitly manual
Issue #44 topic ranges. It does not use Topic Engine output, alter Gold, or claim
that provisional Concepts are unquestionable author knowledge.

The generated artifact is deterministic, validates every canonical reference,
and preserves both known unaligned Words as explicit limitations inside one
Evidence span.

## Artifacts

| Artifact | Role | SHA-256 |
| --- | --- | --- |
| `analysis/golden_knowledge_slice/curation.json` | bounded manual/Gold curation input | `271eab587220933e490b8fcfdd4f3eac1d1ab8d549192417f09014e6584b514c` |
| `analysis/golden_knowledge_slice/build_golden_slice.py` | deterministic builder and validator | `7a51dc03ce6053572fb077bdc9ffe123d713b601aa19a417a1d185db0ce4fd7e` |
| `analysis/golden_knowledge_slice/golden_knowledge_slice.json` | machine-readable product slice | `177d030a6ac3e3dc0a28d655db0f12321e09caba8eff494c078aeb828339d4d6` |

The generated artifact type is `seminartext.golden_knowledge_slice`, version
`1.0.0`. It pins Canonical Evidence bundle SHA-256
`8b1a5b1ffced298cd21a8ede3dbe61d82a00950f2de6da1ba186ffae4cd93d14`.

## Selected scope

The slice stays inside the controlled `video_001` Canonical Evidence interval
from 600.0 to 1496.78 seconds. Three coherent ranges were selected:

| Topic | Origin | Canonical range | Source envelope |
| --- | --- | --- | --- |
| Стресс как механизм адаптации и выживания | existing Dataset A Gold | Words 0–119; clipped at bundle start | 600.140–691.518 s |
| Личное и профессиональное применение кинезиологии | manual Issue #44 | Words 553–1055 | 970.901–1258.237 s |
| Мотивация, препятствия и саботаж | manual Issue #44 | Words 1107–1433 | 1298.070–1489.194 s |

The Gold record is copied from `video_001_window_01`, Gold boundary segment 86,
in Dataset A benchmark SHA-256
`3e0e8ae09ca3523c93a70ebf57fda0aadd331e8f06216647791ba4fa9a55f803`.
Its title and summary are unchanged. Because the accepted canonical fragment
starts after that Gold topic begins, coverage is honestly marked
`partial_start_clipped_to_canonical_bundle`.

The other two structures are marked `manual_issue_44` and
`product_review_required`. They are bounded source discussions selected for
product modelling, not new Gold and not Topic Engine predictions.

## Knowledge entities

| Entity | Count | Minimum role |
| --- | ---: | --- |
| Seminar | 1 | stable container linked to canonical Project |
| Source | 1 | canonical `video_001` identity, hash and duration |
| Topic | 3 | bounded range, origin, provenance, Concepts and Evidence |
| Concept | 7 | provisional identity, label, description, Topics and Evidence |
| Evidence | 10 | exact canonical Word range, quote and source locator |

The seven provisional Concepts are:

1. `concept_adaptation_to_environment` — Адаптация к среде;
2. `concept_survival_in_changing_environment` — Выживаемость в меняющейся
   среде;
3. `concept_personal_and_professional_practice` — Личное и профессиональное
   применение кинезиологии;
4. `concept_peer_supported_correction` — Коррекция с поддержкой коллег;
5. `concept_multiple_life_problem_domains` — Несколько областей жизненных
   запросов;
6. `concept_motivation_as_condition_for_action` — Мотивация как условие
   действия;
7. `concept_sabotage_as_internal_resistance` — Саботаж как внутреннее
   сопротивление.

Each Concept has `derivation_status = provisional_manual_curation` and
`review_status = product_review_required`. Identity rationale explains every
alias/merge decision. Only “адаптивность” is retained as an alias because that
form appears directly in evidence. No automatic synonym or ontology expansion
is performed.

## Repeated concept identity proof

`concept_survival_in_changing_environment` deliberately tests reuse across two
Topics:

- in the Gold stress/adaptation Topic, evidence at 632.791–660.280 s explicitly
  discusses survival in the surrounding/evolutionary environment;
- in the manual personal/professional Topic, evidence at
  1091.680–1128.600 s again uses “выживаемость в современной среде” while
  discussing peer practice and professional work.

The shared Concept is justified by repeated source wording, not embedding
similarity. The artifact keeps both Evidence records and both Topic IDs, so a
reviewer can reject the merge without losing either occurrence.

Semantically adjacent objects remain separate. “Саботаж” is not automatically
merged with absent motivation, procrastination, resistance, or obstacles.
Personal/professional practice is not expanded into a profession ontology.

## Evidence and navigation

Every Evidence record contains:

- stable Evidence ID and curation sequence;
- concise claim whose status remains curated/provisional through its Concept;
- canonical source and authoritative transcript revision IDs;
- inclusive canonical first/last Word IDs;
- exact quote reconstructed from immutable transcript character spans;
- source-compatible `time_interval` derived from first/last aligned Words;
- explicit timing status and list of any unaligned Words.

Examples:

| Knowledge object | Evidence | Canonical/source navigation |
| --- | --- | --- |
| Адаптация к среде | “задача быть адаптивными…” | Words 0–13 → `video_001` → 600.140–609.950 s |
| Выживаемость в меняющейся среде | “Цель повышения выживаемости…” | Words 43–76 → source → 632.791–660.280 s |
| Личное и профессиональное применение | “для профессиональной деятельности и для себя” | Words 567–600 → source → 983.557–1004.250 s |
| Коррекция с поддержкой коллег | group/colleague correction span | Words 664–735 → source → 1035.730–1074.690 s |
| Мотивация как условие действия | motivation changes readiness/circumstances | Words 1145–1221 → source → 1329.381–1376.170 s |
| Саботаж как внутреннее сопротивление | consciousness/subconscious span | Words 1329–1392 → source → 1432.000–1466.710 s |

The broad problem-domain Evidence range, Words 954–1055, contains canonical
Words 970 `думаешь,` and 971 `что`. Those Words still have null timing. The
Knowledge Evidence stores both IDs in `unaligned_word_ids` and marks timing as
`aligned_envelope_with_explicit_unaligned_words`; its 1191.892–1258.237 s
locator is only the envelope formed by aligned endpoints. It does not assign or
imply individual timestamps for the unsupported Words.

## Determinism and validation

The builder performs no extraction model call. It consumes frozen curation and
the pinned canonical bundle, then:

1. verifies the canonical bundle SHA-256 and Canonical Evidence invariants;
2. resolves the authoritative transcript, Source and every Word range;
3. reconstructs quotes only from canonical character spans;
4. derives locators only from aligned Word endpoints;
5. enumerates every internal unaligned Word;
6. rejects automatic Topic origins, orphan references, cross-source/revision
   ranges, inverted ranges, inaccurate locators and non-reciprocal links;
7. requires every Concept to have Topic and Evidence links and to remain
   provisional/Product-Review-required;
8. writes deterministic sorted-key UTF-8 JSON.

Two complete builds produce byte-identical output with SHA-256
`177d030a6ac3e3dc0a28d655db0f12321e09caba8eff494c078aeb828339d4d6`.

Focused tests cover deterministic output, the complete entity model, reverse
navigation, unchanged Gold provenance, canonical quote/locator reconstruction,
unaligned limitations, conservative repeated identity and rejection of orphan
Evidence or changed canonical hashes. The complete repository suite passes
(`44 passed`).

## Product questions

### 1. Is Topic → Concept → Evidence a useful granularity?

Yes for this bounded slice. Topic provides enough conversational context,
Concept provides reusable identity, and Evidence prevents the Concept label or
description from becoming an unsupported summary. The repeated survival Concept
shows useful cross-Topic reuse without requiring a graph database.

The granularity fails if Topic alone is treated as evidence or if every phrase
is promoted to a Concept. The practical unit is a provisional Concept with one
or more bounded Evidence spans.

### 2. Can a reviewer reliably return from a Concept to exact source evidence?

Yes. Every Concept resolves to Evidence IDs, each Evidence resolves to canonical
Word IDs, transcript spans, Source ID and absolute time. Quotes are regenerated
from canonical text and cannot drift independently. Internal unaligned Words
remain visible, so navigation does not manufacture precision.

### 3. Are stable Concept identities feasible without premature ontology complexity?

Yes within one curated seminar. Deterministic descriptive IDs plus explicit
identity rationale are sufficient. Cross-seminar identity is not yet safe to
automate: the same label may carry narrower or author-specific meanings, and a
future reviewer must choose existing/new/duplicate/ambiguous.

### 4. What ambiguities require Product Owner/domain review?

- Whether “выживаемость” in evolutionary explanation and modern professional
  practice is one author Concept or two contextual uses.
- Whether “адаптивность” should remain an alias of adaptation or a distinct
  capability/process.
- Whether “личное и профессиональное применение” should be one Concept or two
  linked usage modes.
- Whether “саботаж” is accurately described as internal resistance or needs the
  author's narrower seminar-specific definition.
- Whether claims about techniques solving broad health/life problems should be
  retained as author statements, narrowed, or flagged with a stronger claim
  type/disclaimer.
- Whether the two manual Topic boundaries and summaries are useful for product
  navigation.
- Speaker attribution is unavailable because `speaker_id` is null; review may
  require manual speaker metadata before publication.

### 5. What minimum fields are needed for the next Obsidian prototype?

Seminar card:

- stable ID, title, Source IDs, ordered Topic IDs.

Source card:

- canonical Source ID, title, kind, content hash/duration and navigation base.

Topic card:

- stable ID, title/summary, structural origin/provenance, coverage/review state,
  Concept IDs, Evidence IDs and canonical range/locator.

Concept card:

- stable ID, preferred label, evidence-supported aliases, concise description,
  derivation/review state, identity rationale, Topic IDs and Evidence IDs.

Evidence block/card:

- stable ID, claim, canonical Source/Transcript/Word IDs, exact quote, typed
  locator, timing status and unaligned limitations.

These fields map directly to Markdown frontmatter and wikilinks. A graph DB,
embedding, RAG metadata, bidirectional sync state and broad ontology type system
are not minimum fields.

### 6. What remains manual/human-reviewed?

- Topic selection/boundaries unless an already accepted Gold structure exists;
- promotion of phrases to Concepts;
- preferred labels, aliases and evidence-grounded descriptions;
- concept merge/split and cross-Topic identity decisions;
- claim framing and domain/publication suitability;
- speaker attribution where needed;
- final acceptance/rejection/defer decisions in Product Review.

Automation may enforce identity, ordering, reference and rendering mechanics. It
must not silently convert provisional curation into verified author knowledge.

## Limitations and non-goals

- This is a deliberately incomplete seminar slice, not full-seminar extraction.
- One Gold Topic is clipped by the canonical bundle start; that limitation is
  explicit rather than hidden.
- Two manual Topics and all Concepts require Product Review.
- No Topic Engine run, tuning, Gold modification or automatic boundary creation
  occurred.
- No automatic semantic entity resolution occurred.
- No full Concept ontology, graph DB, RAG, Knowledge Assistant, Obsidian sync,
  site, Marketing Passport, learning architecture or multi-seminar resolution
  was added.
- Dataset D remains locked; Dataset E remains excluded; Dataset F remains
  quarantined.

## Final verdict and next Knowledge Product milestone

`GOLDEN_KNOWLEDGE_SLICE_ACCEPTED`

The vertical slice is useful and auditable enough to feed the next bounded
Knowledge Product milestone: **Obsidian Knowledge Prototype**, followed by
Product Review. The parallel Semantic Automation track remains unchanged at
**External Topic/Semantic Segmentation Survey / Baseline Challenge**.
