# Issue #68 — exception-only DOMAIN_REVIEW

This packet is advisory and remains `PROVISIONAL_UNREVIEWED`. `REVIEW_CLEAR`
does not mean `ACCEPTED`.

## Verified inventory

- Machine Topic proposals: **262**
- Resulting authored semantic units: **182**
- Topic `REVIEW_CLEAR`: **182**
- Topic `REVIEW_EXCEPTION`: **0**
- Concept candidates after review decisions: **23** (baseline: **18**)
- Concept identity exceptions: **1**
- Topic→Concept QA results after review decisions: **261** (baseline: **254**)
- Link exceptions: **64**
- Selective transcript-verification exceptions: **2**
- Coverage gaps / overlaps: **0 / 0**

The full deterministic classification and Day 2–4 semantic maps are stored in
`domain_review_qa.json`. In accordance with the exception-only UX, this human
packet exposes only the first unresolved material exception.

## First material exception — Concept identity

- Concept candidate: `issue_68_candidate_concept_self_regulation`
- Proposed label: **Саморегуляция**
- Source terms: Управление стрессом
- Exact evidence references: **2**
- Classification: `IDENTITY_EXCEPTION`

### Exact problem

The candidate is generated from a broad summary phrase and has no matching exact source expression in the current authored ranges.

### Recommended review

Defer or define the identity only with explicit human evidence review.

### Human decision required

Choose one bounded Concept-identity outcome. No later exception is presented
until this decision is persisted and the affected Topic→Concept links are
rebuilt and re-QA'd.
