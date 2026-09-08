# Issue #68 — real multi-source vertical-slice readiness

This directory contains the Issue #68 readiness checkpoint and the subsequent
authorized machine-assisted `DOMAIN_AUTHORING` package for the real `Стресс
код` seminar. All four video sources have valid, hash-bound Canonical Evidence
and Word Timelines. Day 1 remains the applied Issue #113 Product Owner review;
Days 2–4 are represented only by provisional, `UNREVIEWED` proposals. Their
machine-assisted `DOMAIN_AUTHORING` pass is complete, and the deterministic
exception-only QA entry point is now
`domain_review_v1/DOMAIN_REVIEW.md`.

The package is deliberately fail-closed. It prepares Topics, Concept candidates,
and Topic→Concept links for review without promoting any of them to Canonical
Knowledge. The mandatory accepted `Seminar -> Source/Topic -> Concept ->
Evidence` path therefore remains blocked until human authoring/review decisions
are recorded.

Run the deterministic inventory with explicit local inputs:

```bash
python analysis/issue_68_vertical_slice/build_readiness_manifest.py \
  --project "/path/to/Стресс код" \
  --review-result "/path/to/topic_review_result_v2.json" \
  --output analysis/issue_68_vertical_slice/readiness_manifest.json
```

The committed manifest contains hashes and counts, not media or full transcript
content. Absolute local paths are intentionally excluded.

Build the deterministic semantic package from the same governed inputs:

```bash
python analysis/issue_68_vertical_slice/build_semantic_authoring_package.py \
  --project "/path/to/Стресс код" \
  --review-result "/path/to/topic_review_result_v2.json" \
  --output-dir analysis/issue_68_vertical_slice/semantic_authoring_v1
```

Build the exception-only DOMAIN_REVIEW QA package without promoting semantics:

```bash
python analysis/issue_68_vertical_slice/build_domain_review_qa.py \
  --repository . \
  --project "/path/to/Стресс код" \
  --review-result "/path/to/topic_review_result_v2.json" \
  --semantic-package \
    analysis/issue_68_vertical_slice/semantic_authoring_v1/semantic_authoring_package.json \
  --output-dir analysis/issue_68_vertical_slice/domain_review_v1
```

Explicit Product Owner decisions for individual exceptions are stored in
`domain_review_v1/domain_review_decisions.json`. The builder validates their
exact Canonical Word partition, preserves `NON_SEMANTIC_EXCLUDED` lineage,
re-QA's both neighboring boundaries, and then exposes the next unresolved
exception. A decided exception does not promote the remaining package.

## Current gate

- Engineering evidence validation: `PASS`
- Full Canonical Word coverage by provisional Topic proposals: `PASS`
- Days 2–4 authoring: `262/262 COMPLETED_PROVISIONAL`
- Resulting semantic units classified by QA: `182`
- Persisted exact DOMAIN_REVIEW decisions: `10` (`4` Topic, `6` Concept)
- Days 2–4 Topic authority: `UNREVIEWED`
- Concept candidates and Topic→Concept links: `PROVISIONAL_UNREVIEWED`
- Obsidian export: `NOT_RUN_BLOCKED_SEMANTIC_INPUT`
- Issue #68 result: `PARTIAL`

The next gate is the first material exception in
`domain_review_v1/DOMAIN_REVIEW.md`. The full QA manifest preserves the
original `18` Concept-candidate and `254` Topic→Concept-link input inventories;
the smaller preview-derived projections in the authored package are not
treated as semantic deletion. `REVIEW_CLEAR` does not imply acceptance;
semantic acceptance remains an explicit `DOMAIN_REVIEW` decision.
