# 0001 - Operating Model And Human Gates

Date: 2026-08-25

## Status

Accepted

## Context

SeminarText 4.0 work now involves Product Owner planning, Codex execution,
GitHub Issues and PRs, benchmark evidence, and occasional domain-authoring work
from Yuri. The project needs a clear operating model so Yuri participates where
his author-methodology expertise improves correctness, while routine technical
operations stay automated and reviewable.

## Decision

Document the operating model in `DEVELOPMENT_WORKFLOW.md` and use GitHub as the
technical source of truth for roadmap, state, Issues, PRs, tests, benchmarks, and
decision records.

Adopt this governing principle:

Do not minimize Yuri's participation. Minimize Yuri's participation in operations
where his expertise is not needed.

Adopt these human-gate classifications for future Issues:

- `AUTO`
- `DOMAIN_REVIEW`
- `DOMAIN_AUTHORING`
- `LOCAL_ACTION`

Default to `AUTO`; escalate only when justified.

## Consequences

- Future Issues can state their human-gate classification explicitly.
- Codex can proceed through routine implementation/test/PR work without asking
  Yuri to relay requirements that are already available in GitHub.
- Yuri remains the required authority for Gold labels, disputed semantics,
  terminology, conceptual-model acceptance, and unavailable local actions.
- This decision does not change production Topic Engine logic, benchmark Gold
  data, experiment configurations, or CLI behavior.
