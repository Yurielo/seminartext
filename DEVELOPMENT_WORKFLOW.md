# SeminarText 4.0 Operating Model

## Governing Principle

Do not minimize Yuri's participation. Minimize Yuri's participation in operations
where his expertise is not needed.

Yuri is the Domain Owner and author-methodology authority. He is not a message
courier between AI systems.

## Roles

### Product Owner

The Product Owner, currently ChatGPT, owns roadmap, priorities, issue sequencing
and Definitions of Done. The Product Owner reviews experiment evidence and PRs,
accepts or rejects work, makes merge and next-step decisions, and escalates to
Yuri only when a domain, product, business, or human decision is actually needed.

### Yuri, Domain Owner

Yuri is required for high-value human gates:

- semantic Gold labeling and disputed topic boundaries;
- authoritative terminology and meaning of the author's methodology;
- genuinely ambiguous interpretations;
- product or business decisions that cannot be inferred safely;
- acceptance of changes to the conceptual model;
- local-machine, UI, or account actions unavailable to connected tools.

Yuri should not normally be required for routine relay or operations:

- copying requirements between ChatGPT, GitHub, and Codex;
- routine coding, test execution, branch, commit, push, or PR mechanics;
- routine benchmark aggregation;
- routine documentation updates;
- technical QA that can be automated.

### Codex

Codex is the engineering executor. Codex reads the GitHub Issue as the task
contract, implements within scope, runs tests and QA, documents evidence,
commits, pushes, and opens PRs. Codex does not redefine product requirements,
bypass human gates, tune benchmarks without authorization, or merge its own PRs.

### Specialist Roles

Specialist roles are used only when relevant: backend/ML, database or knowledge
architect, QA, PR reviewer, CI/CD, frontend, documentation, and sprint planning.
The Product Owner coordinates specialist involvement. Do not invoke every role
mechanically.

## GitHub Source Of Truth

Use GitHub and the repository as the technical source of truth:

- `SEMINARTEXT_4_ROADMAP.md` records direction, stages, and quality gates.
- `SEMINARTEXT_4_STATE.json` records current machine-readable project state.
- GitHub Issues are task contracts and Definitions of Done.
- Pull Requests contain implementation, evidence, review, and merge decisions.
- Tests and benchmarks are executable evidence.
- `decisions/` records lightweight architecture and operating decisions.

## Standard Execution Loop

Default issue loop:

`ROADMAP -> PO ISSUE/DoD -> CODEX IMPLEMENT -> AUTOMATED TEST/QA -> PR -> PO REVIEW -> [DOMAIN GATE only if needed] -> MERGE -> STATE/ROADMAP UPDATE -> NEXT ISSUE`

Experimental or ML loop:

`BUILD -> TEST -> BENCHMARK -> HUMAN REVIEW when semantically required -> DECISION -> MERGE`

## Human-Gate Classification

Every future Issue may state a `Human gate` value. Default to `AUTO`; escalate
only when justified.

| Classification | Meaning |
| --- | --- |
| `AUTO` | Codex and automated QA can proceed without Yuri. |
| `DOMAIN_REVIEW` | Yuri reviews prepared evidence/options before acceptance. |
| `DOMAIN_AUTHORING` | Yuri must supply authoritative semantic content, such as Gold labels. |
| `LOCAL_ACTION` | Yuri must perform a local/UI/account action unavailable to tools. |

If the classification changes during work, the PR should explain why.

## Current Technical Direction

The current technical direction remains Stage 2 Hybrid Topic Engine. Dataset A
and Dataset B have been validated; the next independent validation step is
Dataset C. Manual Gold is required only where semantic authoring is needed.
Frozen A/B/C validation should precede the architecture decision checkpoint
before Stage 3.

No operating-model issue should change production Topic Engine algorithms,
benchmark Gold data, experiment configurations, or CLI behavior unless a future
Issue explicitly requires that scope.
