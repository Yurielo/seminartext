# SeminarText Codex operating instructions

The canonical Product Rules Registry is
`docs/architecture/SEMINARTEXT_PRODUCT_RULES.md`.

Before any work that changes or evaluates product behavior, architecture, the
knowledge model, semantic workflow, lifecycle, user-visible behavior, or
governance contracts, Codex MUST read the current Registry and identify every
applicable `ACTIVE` rule.

For each applicable task, the final report MUST contain:

```text
PRODUCT_RULES_READ: YES
APPLICABLE_PRODUCT_RULES: PR-xxx, ...
PRODUCT_RULE_CONFLICTS: NONE
```

If proposed work conflicts with an `ACTIVE` Product Rule, report the conflict,
HARD STOP, and require `PRODUCT_OWNER_DECISION_REQUIRED`. Do not continue based
on Codex interpretation.

Codex may persist, change, supersede, or retire a Product Rule only when an
explicit authorized task from the Product Owner instructs it to do so. A Codex
recommendation, implementation choice, inferred preference, silence, or absence
of objection is not Product Rule authorization. IDs are never reused and
historical rules are never silently deleted.

Follow `AUTONOMOUS UNTIL HUMAN GATE`: after a bounded task is explicitly
authorized, continue through every safe, deterministic in-scope
`NEXT_TECHNICAL_SUBSTEP`; stop only at a genuine
`NEXT_AUTHORIZATION_BOUNDARY`. This never expands scope or weakens Product
Owner, domain, local-action, merge, deploy, runtime, Dataset, Gold, semantic,
destructive-action, ambiguity, or conflict gates. Emit one consolidated report
and PR-011 sound only when returning control to the user.

The broader role, verification, GitHub, and human-gate contract remains in
`DEVELOPMENT_WORKFLOW.md`. When instructions conflict, stop and request a
Product Owner decision; neither file authorizes Codex to invent product policy.
