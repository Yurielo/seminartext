# Obsidian Knowledge Prototype on Golden Seminar

Date: 2026-08-28

Issue: #51

Verdict: `OBSIDIAN_KNOWLEDGE_PROTOTYPE_READY_FOR_PRODUCT_REVIEW`

Product Review status: **pending**

## Outcome

The accepted Issue #44 Golden Seminar Knowledge Slice can be rendered as a
bounded, useful Obsidian-ready view while Canonical Evidence remains the source
of truth. The prototype provides a working human navigation chain:

`Seminar → Topic → Concept → Evidence → Source + exact time + canonical Word IDs`

Topic, Concept and Evidence notes also link back to their related entities, so
ordinary Obsidian backlinks support reverse navigation. No Obsidian plugin is a
hard dependency.

The export contains only the accepted bounded `Стресс код` slice: one Seminar,
one Source, three Topics, seven provisional Concepts and ten Evidence items. It
does not expand to the full seminar.

## Authoritative inputs and derived-view boundary

| Input | Frozen identity |
| --- | --- |
| Golden Slice | `golden_slice_stress_code_video_001_v1` |
| Golden Slice SHA-256 | `177d030a6ac3e3dc0a28d655db0f12321e09caba8eff494c078aeb828339d4d6` |
| Canonical Evidence | `artifact_stress_code_video_001_fragment_600_1496_r1` |
| Canonical SHA-256 | `8b1a5b1ffced298cd21a8ede3dbe61d82a00950f2de6da1ba186ffae4cd93d14` |
| Canonical Source | `source_stress_code_video_001` |
| Canonical TranscriptRevision | `transcript_stress_code_video_001_fragment_600_1496_r1` |

The exporter hash-checks both JSON inputs before rendering. It copies no
canonical JSON into the vault and creates no second knowledge database. A
generated `_meta/canonical_evidence_reference.md` note stores only the artifact
identity, hash and repository-relative link to the canonical bundle. Markdown
is disposable and rebuildable.

## Generated vault

Location: `analysis/obsidian_knowledge_prototype/vault`

```text
vault/
├── 00_START_HERE.md
├── PRODUCT_OWNER_REVIEW_GUIDE.md
├── Seminars/                         1 note
├── Sources/                          1 note
├── Topics/                           3 notes
├── Concepts/                         7 notes
├── Evidence/                        10 notes
└── _meta/                            1 canonical pointer note
```

Total generated notes: **25**.

Every note has machine-readable frontmatter with:

- `stable_id`;
- `note_type`;
- `lifecycle_status=derived_view`;
- `derived_from_artifact_id` and frozen SHA-256;
- `export_schema_version` and deterministic generator identity;
- entity-specific review, canonical identity and provenance fields.

Frontmatter is emitted as a JSON object, a strict valid YAML 1.2 mapping. This
keeps validation dependency-free while remaining Obsidian-compatible.

## Navigation and evidence contract

Seminar links to the Source and all three bounded Topics. Each Topic links to
its supported Concepts and Evidence. Each Concept links to every Topic where it
is used and to supporting Evidence. Each Evidence note links to its Source, the
canonical reference, using Topics and supported provisional Concepts.

An Evidence note displays:

- the bounded Golden Slice claim;
- a short exact canonical excerpt;
- canonical Source ID;
- human-readable and numeric start/end seconds;
- canonical TranscriptRevision ID;
- exact canonical Word ID range;
- timing status and every unaligned Word limitation;
- a link to the hash-locked canonical artifact reference.

The evidence span containing Words 970–971 remains
`aligned_envelope_with_explicit_unaligned_words`. Those Words are named and no
synthetic timing is created.

## Product assessment

### 1. Is the representation genuinely usable?

**Yes, for this bounded Product Review.** The Start note exposes one clear entry
point; the entity folders keep the mental model visible; links and backlinks
support the intended traversal without a plugin. Exact source/time is available
at the Evidence layer without overloading Topic and Concept cards.

This is not yet evidence that the same layout scales to a full seminar or
multiple seminars.

### 2. Which note granularity works best?

One note per stable Seminar, Source, Topic, Concept and Evidence entity is the
smallest useful granularity. Evidence must remain a separate note: embedding all
quotes in Topic/Concept cards would duplicate provenance and make many-to-many
reuse harder to inspect. A single canonical pointer note avoids copying the
canonical bundle.

### 3. Essential metadata versus noise

Essential for every note:

- stable identity and note type;
- derived lifecycle and frozen source-artifact hash;
- review/provisional status.

Essential where applicable:

- canonical Source/TranscriptRevision/Word IDs;
- source locator and timing status;
- explicit unaligned limitations;
- Topic/Concept/Evidence relationship IDs;
- Topic structure origin and coverage.

Sequence numbers, full canonical records, large transcript blocks, runtime
timestamps and machine paths are excluded from the portable view because they
add noise or create false authority.

### 4. Are Evidence links understandable?

The static contract is understandable: each Evidence card shows a short quote,
plain source title, Source ID, `HH:MM:SS.mmm` interval, numeric seconds and Word
range. The canonical reference is one additional hop. Product Owner review must
confirm whether this amount of detail feels natural in Obsidian.

### 5. Which Concept decisions still require review?

All seven Concepts remain `provisional_manual_curation` with
`product_review_required`. In particular, Product Owner must decide whether:

- `Выживаемость в меняющейся среде` is correctly reused across two Topics;
- `Личное и профессиональное применение кинезиологии` should stay one Concept;
- `Несколько областей жизненных запросов` is a useful Concept rather than a
  loose list;
- motivation and sabotage remain separate entities with suitable names;
- the supported alias `адаптивность` should be retained.

Rendering does not promote any Concept to an accepted ontology fact.

### 6. Minimum next step after Product Review

Record Product Owner findings against this exact fixture: accept/revise the note
contract and classify each provisional Concept as accept, rename, split, merge,
reject or defer. Only after that review should a narrowly scoped production
export command or a second bounded seminar be considered.

### 7. What should not be automated yet?

Do not implement automatic Concept acceptance/merge, full-seminar expansion,
bidirectional sync, preservation/merging of manual Markdown edits, graph/RAG,
cross-seminar ontology, website integration, or automatic Topic input. Product
Review must first validate naming, density and evidence usability.

## Determinism, rebuild and portability

`export_obsidian_vault.py` builds an in-memory stable path→bytes mapping, writes
the same stable-ID filenames and emits a hash manifest. Two builds from the same
inputs are byte-identical. Rebuilding the same directory overwrites the same 25
files and creates no duplicates. The exporter refuses to delete unmanaged
Markdown rather than treating a generated vault as authority over user notes.

Export manifest SHA-256:
`cf58d447bd832804a4e5478f61f581d0f681e6bba847e2de46f5384c56b5d374`.

The fixture and manifest contain no `/Users/...`, `/tmp/...`, `file://` or
editor-specific absolute URI. Canonical navigation uses repository-relative
identity/path plus stable IDs and hashes.

## Validation summary

- all 25 note frontmatter mappings parse as JSON and valid YAML 1.2 mappings;
- all stable IDs are present and unique;
- every generated wikilink resolves inside the vault;
- every entity note participates in navigation;
- all Topic and Concept claims link to their accepted Evidence set;
- all ten Evidence records resolve to canonical Source/TranscriptRevision/Word
  ranges and exact source intervals;
- canonical artifact link resolves from the committed fixture;
- provisional/review statuses are preserved visibly and in frontmatter;
- repeated build is byte-identical and idempotent;
- unmanaged Markdown is protected;
- portable-path checks pass.

## Scope safeguards

No Topic Engine, TreeSeg, Gold, Dataset C/D/E, RAG, vector/graph database,
bidirectional Obsidian sync, full-seminar expansion or website integration was
used or changed. The Semantic and Data/Evaluation tracks remain independent.

## Product Owner review required

Open `analysis/obsidian_knowledge_prototype/vault` as an Obsidian vault and begin
at `00_START_HERE.md`. Complete the seven tasks in
`PRODUCT_OWNER_REVIEW_GUIDE.md`, then provide decisions on navigation,
granularity, metadata density, provenance clarity and the seven provisional
Concepts.

This report declares the fixture ready to be reviewed. It does **not** declare
Product Review passed.
