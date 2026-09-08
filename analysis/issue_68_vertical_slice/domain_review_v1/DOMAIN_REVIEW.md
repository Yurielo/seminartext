# Issue #68 — exception-only DOMAIN_REVIEW

This packet is advisory and remains `PROVISIONAL_UNREVIEWED`. `REVIEW_CLEAR`
does not mean `ACCEPTED`.

## Verified inventory

- Machine Topic proposals: **262**
- Resulting authored semantic units: **182**
- Topic `REVIEW_CLEAR`: **182**
- Topic `REVIEW_EXCEPTION`: **0**
- Concept candidates: **18**
- Concept identity exceptions: **6**
- Topic→Concept input links: **254**
- Link exceptions: **62**
- Selective transcript-verification exceptions: **2**
- Coverage gaps / overlaps: **0 / 0**

The full deterministic classification and Day 2–4 semantic maps are stored in
`domain_review_qa.json`. In accordance with the exception-only UX, this human
packet exposes only the first unresolved material exception.

## First material exception — Concept identity

- Concept candidate: `issue_68_candidate_concept_nervous_system`
- Proposed label: **Нервная система**
- Source terms: Нейронные сети, Нервная сеть, Нервная Система, Нервная система, нервная система, нервной системы
- Exact evidence references: **10**
- Classification: `IDENTITY_EXCEPTION`

### Exact problem

The seed groups nervous system, neural network, and neuron-network language that may denote related but distinct Concepts.

### Recommended review

Review as RELATED versus SAME_CONCEPT before identity assignment.

### Human decision required

Choose one bounded Concept-identity outcome. No later exception is presented
until this decision is persisted and the affected Topic→Concept links are
rebuilt and re-QA'd.
