# Issue #68 — exception-only DOMAIN_REVIEW

This packet is advisory and remains `PROVISIONAL_UNREVIEWED`. `REVIEW_CLEAR`
does not mean `ACCEPTED`.

## Verified inventory

- Machine Topic proposals: **262**
- Resulting authored semantic units: **182**
- Topic `REVIEW_CLEAR`: **182**
- Topic `REVIEW_EXCEPTION`: **0**
- Concept candidates after review decisions: **19** (baseline: **18**)
- Concept identity exceptions: **5**
- Topic→Concept QA results after review decisions: **256** (baseline: **254**)
- Link exceptions: **64**
- Selective transcript-verification exceptions: **2**
- Coverage gaps / overlaps: **0 / 0**

The full deterministic classification and Day 2–4 semantic maps are stored in
`domain_review_qa.json`. In accordance with the exception-only UX, this human
packet exposes only the first unresolved material exception.

## First material exception — Concept identity

- Concept candidate: `issue_68_candidate_concept_brain`
- Proposed label: **Мозг и полушария**
- Source terms: Мозг, мозг, мозга, полушарий, полушария
- Exact evidence references: **12**
- Classification: `IDENTITY_EXCEPTION`

### Exact problem

«Мозг» and «полушария» mix a whole structure with one of its organizational distinctions.

### Recommended review

Choose one umbrella identity or separate hierarchical Concepts.

### Human decision required

Choose one bounded Concept-identity outcome. No later exception is presented
until this decision is persisted and the affected Topic→Concept links are
rebuilt and re-QA'd.
