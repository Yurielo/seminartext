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

Follow `AUTONOMOUS ALONG APPROVED ROADMAP`: when the approved Roadmap and
current verified truth unambiguously establish a singular
`NEXT_ROADMAP_ITEM`, `ROADMAP_EXECUTION_AUTHORITY = STANDING`. Perform
`MECHANICAL_STATE_RECONCILIATION = AUTO`, `ISSUE_LIFECYCLE = AUTO`, and all
deterministic work without routine dispatch. `SAFE_MERGE = AUTO` and
`SAFE_RUNTIME_RECONCILIATION = AUTO` apply only after every fail-closed
condition in PR-014 and `DEVELOPMENT_WORKFLOW.md` is mechanically proven. A
governance PR never self-authorizes from its own unmerged rule. Roadmap changes,
Product Owner/domain/local-action decisions, Dataset/Gold or semantic authority,
high-risk or irreversible operations, security decisions, unknown runtime
targets, ambiguity, and Product Rule conflicts remain genuine human gates.
Routine completion reports are not gates, and the user must not be used as a
command courier between deterministic stages.

The broader role, verification, GitHub, and human-gate contract remains in
`DEVELOPMENT_WORKFLOW.md`. When instructions conflict, stop and request a
Product Owner decision; neither file authorizes Codex to invent product policy.

## Unified four-product rules

Before drafting or executing work in this repository, explicitly resolve and read the complete canonical rules document:
`Yurielo/integra` `main:docs/governance/UNIFIED_CODEX_RULES.md`.

A URL or filename is not automatic instruction loading. Resolve `main` to a full Git commit using GitHub or Git, then read that exact blob and record the commit and SHA-256 in material task evidence. If GitHub is unavailable, use only a local Integra checkout whose commit identity has already been verified; otherwise fail closed on the missing source access.

This directive adds no runtime dependency. Repository-specific instructions, Product Rules, governance, lifecycle, and terminal-state requirements remain applicable and take precedence as required by unified rule 0.
