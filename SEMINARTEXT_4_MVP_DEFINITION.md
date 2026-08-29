# SeminarText 4.0 MVP — User Journey and Definition of Done

This document is the single product-level Definition of Done for the SeminarText
4.0 MVP. It consolidates the already accepted Evidence-First architecture; it
does not promote pending prototypes or expand product scope.

## User journey

1. A user creates a seminar project and registers a local or supported external
   source.
2. SeminarText produces a reviewable transcript while preserving source and
   time provenance.
3. The verified transcript is aligned into the Canonical Evidence / Word
   Timeline contract without silently dropping unaligned text.
4. The user works with verified manual, Gold, or explicitly marked
   semi-automatic topics. Automation maturity is visible and never presented as
   human-verified evidence.
5. SeminarText produces the accepted knowledge-package/export form with stable
   Seminar, Source, Topic, Concept, and Evidence identifiers.
6. The user can navigate from knowledge output back to the exact source locator
   and can distinguish technical evidence, product-review status, integration
   status, and production stability.

## Product-level Definition of Done

The 4.0 MVP is done only when all of the following are true:

- the journey above runs end to end from a fresh, repository-governed install;
- Canonical Evidence and Word Timeline artifacts validate against their accepted
  schemas and cross-record invariants;
- no transcript text or evidence provenance is silently lost;
- topic inputs carry an explicit verification/maturity class and satisfy the
  accepted Topic Automation usability gate where automation is used;
- the accepted knowledge output is deterministic, source-linked, reviewable,
  and passes its Product Owner review;
- failures are actionable and do not silently substitute stale deployed
  Roadmap, State, code, or models;
- automated regression and consistency checks pass;
- product integration is complete and the supported journey has explicit
  production-stability evidence.

## Current maturity

`defined_not_yet_product_integrated`

Completed technical experiments, accepted architecture contracts, and
review-ready prototypes remain evidence toward this DoD. None of those labels by
itself means that the 4.0 MVP is product-integrated or production-stable.
