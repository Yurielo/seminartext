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

## Mandatory Product Rules Control Loop

The one canonical Product Rules Registry is
`docs/architecture/SEMINARTEXT_PRODUCT_RULES.md`. It is durable repository
truth. Product Rules must not depend on conversational memory, inferred intent,
or undocumented implementation knowledge.

The authority chain is:

`Product Owner decision -> ChatGPT formalization -> authorized Codex persistence -> GitHub history -> mandatory ChatGPT/Codex read -> Issue/PR references -> CI and Integrity structural validation`

The Product Owner alone adopts, changes, supersedes, or retires Product Rules.
ChatGPT may formalize an explicit Product Owner decision. Codex may persist that
decision only under an explicit bounded authorization; Codex recommendations,
architecture choices, inferred preferences, silence, and absence of objection
are not Product Rules. GitHub records decisions but does not make semantic
product decisions.

Before changing or evaluating product behavior, architecture, the knowledge
model, semantic workflow, lifecycle, user-visible behavior, or governance
contracts, Codex must read the Registry and report:

```text
PRODUCT_RULES_READ: YES
APPLICABLE_PRODUCT_RULES: PR-xxx, ...
PRODUCT_RULE_CONFLICTS: NONE
```

An `ACTIVE` Product Rule conflict is a `HARD STOP` and requires a Product Owner
decision. Structural CI and G3 validation do not claim to prove semantic
compliance.

### ChatGPT / Prompt 11 control

Before formulating a SeminarText Codex task that affects Product,
Architecture, Knowledge, semantic behavior, lifecycle, user-visible behavior,
or governance, ChatGPT must read/check the current Registry, identify the
applicable `ACTIVE` IDs, include `Applicable Product Rules: PR-...` and
`Product Rule conflicts: NONE` (or the explicit conflict) in the bounded task,
and must not rely only on conversational memory.

When the Product Owner explicitly adopts a durable new rule, ChatGPT determines
whether it belongs in the Registry and, if so, prepares a governed Codex
persistence task using the next collision-free ID. Codex validates and persists
only the authorized rule. Product Owner review and separate merge authorization
remain mandatory. Omission of Product Rule fields from an Issue or PR never
waives an `ACTIVE` Product Rule.

Prompt 11's requirement to identify exactly one next allowed step means exactly
one next authorization boundary, not one technical substep or one already
authorized Roadmap transition. A
`NEXT_TECHNICAL_SUBSTEP` is a safe, deterministic continuation already covered
by the bounded authorization and is traversed autonomously. A
`NEXT_ROADMAP_ITEM` is traversed autonomously only under the standing authority
and fail-closed conditions below. A
`NEXT_AUTHORIZATION_BOUNDARY` requires new human authority and stops execution.
Silence, an open Issue, or a merely logical but not approved Roadmap step is
never authorization.

## Standard Execution Loop

### Autonomous Until Human Gate

Inside an explicitly authorized bounded task, the default is `CONTINUE`, not
`ASK USER TO CONTINUE`:

`authorize bounded scope -> verify preconditions -> execute -> self-check ->`
`deterministic in-scope continuation -> continue -> genuine human gate -> stop`

Reading authorized inputs, deterministic transformation, schema/provenance
validation, rebuilds, self-checks, tests, Integrity, diff/scope inspection,
in-scope deterministic repair and retest, commit, push, and updating an already
authorized PR are technical substeps rather than human gates. They remain
subject to the exact Issue scope and existing Git authorization.

Codex stops at a genuine human gate: Product Owner decision, `DOMAIN_REVIEW`,
`DOMAIN_AUTHORING`, `LOCAL_ACTION`, merge authorization, deploy authorization,
separately gated runtime reconciliation, an unauthorized new Issue or scope
expansion, Dataset-role or Gold authority change, new model/algorithm choice,
new semantic interpretation, irreversible action, unresolved unexpected
FAIL/WARN/drift, material ambiguity, Product Rule conflict, or unavailable
required model. If scope remains materially ambiguous after checking Product
Rules, task authorization, Dataset firewall, semantic authority, and
merge/deploy restrictions, Codex fails closed.

Internal technical substeps do not emit completion reports or audible signals.
Codex keeps an execution ledger and returns one consolidated report, with the
PR-011 sound, when control actually returns to the user.

### Autonomous Along Approved Roadmap

`ROADMAP_EXECUTION` is distinct from `ROADMAP_CHANGE`. Execution has
`ROADMAP_EXECUTION_AUTHORITY = STANDING` only when all of the following are
true: the Roadmap is Product Owner-approved; Roadmap and machine-readable State
agree; the current item's objective DoD is satisfied; the next approved item is
singular and explicit; and no unresolved Product Owner, `DOMAIN_REVIEW`,
`DOMAIN_AUTHORING`, `LOCAL_ACTION`, merge, deploy, separately gated runtime,
Dataset, Gold, semantic, destructive-action, ambiguity, or Product Rule
conflict gate remains. In that state, routine continuation does not require a
new Product Owner dispatch decision.

Standing Roadmap execution authority includes mechanically closing the
completed Issue, creating the explicitly next Roadmap Issue and branch, and
executing its authorized scope through deterministic implementation, repair,
tests, commit, push, and PR. It does not include merge or deploy. An Issue whose
completion itself encodes subjective product or semantic acceptance remains at
the applicable human gate.

`ROADMAP_CHANGE` is always Product Owner-gated. It includes reordering or
skipping required milestones, selecting among materially different next paths,
adding a major initiative, changing architectural direction, Dataset or Gold
authority, or product acceptance semantics. If Roadmap and State disagree,
`NEXT_ISSUE_ALLOWED` is not explicit, or more than one material next item is
valid, Codex stops and reports the exact reconciliation or decision required.

The prohibited human-courier antipattern is: Codex finishes deterministic work,
the user transports its report to another system, that system confirms the
obvious next deterministic action, and the user transports the instruction
back. When no genuine judgment or authorization is needed, Codex continues and
returns one consolidated report at the actual human gate.

Default issue loop inside the Evidence-First Parallel Development policy:

`ROADMAP -> PO ISSUE/DoD -> CODEX IMPLEMENT -> AUTOMATED TEST/QA -> PR -> PO REVIEW -> [DOMAIN GATE only if needed] -> MERGE -> STATE/ROADMAP UPDATE -> NEXT ISSUE`

Experimental or ML loop:

`BUILD -> TEST -> BENCHMARK -> HUMAN REVIEW when semantically required -> DECISION -> MERGE`

Before starting the next Issue after every merge, run the repository-owned
Project Integrity Gate:

`./scripts/seminartext-integrity -> PASS/PARTIAL/FAIL review -> NEXT ISSUE`

The gate is read-only. `BOOTSTRAP_IMPLEMENTATION: PASS` means the observer ran;
`PROJECT_INTEGRITY: FAIL` remains a blocking finding and must be reported or
repaired under a separate governed Issue. Future gates shown as
`NOT_IMPLEMENTED` are never treated as PASS. `NEXT_ISSUE_ALLOWED: YES` plus an
approved singular next Roadmap item permits standing Roadmap execution;
`NEXT_ISSUE_ALLOWED: NO`, a pending human gate, or Roadmap/State disagreement
blocks automatic continuation.

Semantic Automation, Knowledge Product, and Data/Evaluation may advance in
parallel when their inputs and human gates permit. Topic Engine stability is a
scalability track, not a blocker for bounded knowledge prototypes that use
verified manual, Gold, or explicitly marked semi-automatic topics.

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

The policy checkpoint remains `evidence_first_parallel_v1`. Current milestone,
next actions, and transient project status are intentionally volatile and are
owned by `SEMINARTEXT_4_STATE.json` plus its marker-bounded Roadmap projection.
This static workflow document must not repeat a current milestone or next action
and is never a control-plane source of truth; read the machine-readable State
and run `./scripts/seminartext-integrity --json` when current status is needed.
At the AUDIT-R1 checkpoint, TreeSeg is an isolated challenger, the Obsidian
direction is accepted for further adaptation, and Canonical Knowledge Contract
v1 is accepted. Dataset C is closed/frozen evidence and Dataset D remains
locked until topic-agnostic preparation and the required candidate/configuration/
criteria freeze. No review-ready label is an invitation to start experiments.

Installed copies are deploy snapshots: status commands must label them as such
and must report drift instead of silently treating them as current governance.

Before beginning any subsequent Issue, run the repository-owned Integrity gate
and require the control-plane verdict from
`integrity/milestone_reconciliation.json`. `CONTROL_PLANE_RECONCILED: YES` is
necessary but not sufficient: `NEXT_ISSUE_ALLOWED: YES` must also be explicit.
A pending Product Owner/Domain gate or required incomplete runtime
reconciliation keeps the next Issue blocked. The local decision is offline;
GitHub lifecycle checks, when performed, are a separate operational extension.

## Maturity language

Use separate claims for technical evidence, architecture acceptance, product
integration, Product Review, and production stability. A stage marked
`complete` is complete only in its named scope; it does not imply an integrated
or production-stable SeminarText 4.0 product.

The authoritative product journey and product-level Definition of Done are in
`SEMINARTEXT_4_MVP_DEFINITION.md`. Its current status is
`defined_not_yet_product_integrated`.

No operating-model issue should change production Topic Engine algorithms,
benchmark Gold data, experiment configurations, or CLI behavior unless a future
Issue explicitly requires that scope.
