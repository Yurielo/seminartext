# Issue #68 — exception-only DOMAIN_REVIEW

This packet is advisory and remains `PROVISIONAL_UNREVIEWED`. `REVIEW_CLEAR`
does not mean `ACCEPTED`.

## Verified inventory

- Machine Topic proposals: **262**
- Resulting authored semantic units: **182**
- Topic `REVIEW_CLEAR`: **182**
- Topic `REVIEW_EXCEPTION`: **0**
- Concept candidates after review decisions: **20** (baseline: **18**)
- Concept identity exceptions: **4**
- Topic→Concept QA results after review decisions: **259** (baseline: **254**)
- Link exceptions: **64**
- Selective transcript-verification exceptions: **2**
- Coverage gaps / overlaps: **0 / 0**

The full deterministic classification and Day 2–4 semantic maps are stored in
`domain_review_qa.json`. In accordance with the exception-only UX, this human
packet exposes only the first unresolved material exception.

## First material exception — Concept identity

- Concept candidate: `issue_68_candidate_concept_eye_movement`
- Proposed label: **Движения глаз и ДПДГ**
- Source terms: Глазодвигательная, Глазодвигательные, глазодвигательные, движения глаз, ДПДГ
- Exact evidence references: **11**
- Classification: `IDENTITY_EXCEPTION`

### Exact problem

Generic eye movements and the named ДПДГ method are related but not automatically identical.

### Recommended review

Review SAME_CONCEPT versus RELATED/hierarchical identities.

### Human decision required

Choose one bounded Concept-identity outcome. No later exception is presented
until this decision is persisted and the affected Topic→Concept links are
rebuilt and re-QA'd.
