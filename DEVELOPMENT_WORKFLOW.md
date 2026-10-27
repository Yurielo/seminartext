# SeminarText 4.0 Operating Model

## Governing Principle

Do not minimize Yuri's participation. Minimize Yuri's participation in operations
where his expertise is not needed.

Yuri is the Domain Owner and author-methodology authority. He is not a message
courier between AI systems.

## Roles

### Product Owner

The Product Owner owns product direction, Roadmap priorities, Definitions of
Done, reserved acceptance decisions, and genuine human gates. A Product Owner
instruction may be given directly to Codex; ChatGPT may help formalize it but is
not a mandatory intermediary. The Product Owner is not a routine GitHub
operator, merge/deploy dispatcher, Issue lifecycle dispatcher, control-plane
synchronizer, test-retry dispatcher, or command courier.

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
commits, pushes, maintains PRs, and continues across approved Roadmap work.
Codex may merge and reconcile the governed local runtime only under the
fail-closed standing policies below. Codex does not redefine product
requirements, bypass human gates, tune benchmarks without authorization, or
let an unmerged governance rule authorize its own merge.

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

`Product Owner decision -> optional task formalization -> authorized Codex persistence -> GitHub history -> mandatory agent read -> Issue/PR references -> CI and Integrity structural validation`

The Product Owner alone adopts, changes, supersedes, or retires Product Rules.
ChatGPT may formalize an explicit Product Owner decision, but direct Product
Owner authorization to Codex is equally valid for its exact scope. Codex may
persist that decision only under explicit authorization; Codex recommendations,
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

When the Product Owner explicitly adopts a durable new rule, the acting
task-formulation agent determines whether it belongs in the Registry and, if
so, prepares a governed Codex persistence task using the next collision-free
ID. Codex validates and persists only the authorized rule. A governance PR may
merge only under authority already `ACTIVE` on main or an explicit Product
Owner instruction applicable to that PR; it cannot self-authorize from its own
unmerged text. Omission of Product Rule fields from an Issue or PR never waives
an `ACTIVE` Product Rule.

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

Codex stops at a genuine human gate: Product Owner product direction or Roadmap
change, `DOMAIN_REVIEW`, `DOMAIN_AUTHORING`, `LOCAL_ACTION`, an unsafe or
unclassifiable merge/runtime operation, scope expansion, Dataset-role or Gold
authority change, new model/algorithm choice, new semantic interpretation,
irreversible/high-risk action, security or credential decision, uncovered
external production release, unresolved unexpected FAIL/WARN/drift, material
architectural choice, unresolvable ambiguity, Product Rule conflict, or
unavailable required authority/model. A merge or governed local-runtime
reconciliation is not a human gate when every PR-014 standing-policy condition
is mechanically proven. If scope remains materially ambiguous after checking
Product Rules, task authorization, Dataset firewall, semantic authority, and
merge/runtime restrictions, Codex fails closed.

Internal technical substeps do not emit completion reports or audible signals.
Codex keeps an execution ledger and returns one consolidated report, with the
PR-011 sound, when control actually returns to the user.

### Autonomous Along Approved Roadmap

`ROADMAP_EXECUTION` is distinct from `ROADMAP_CHANGE`.
`ROADMAP_EXECUTION_AUTHORITY = STANDING` when the Product Owner-approved Roadmap
and current verified repository, GitHub, runtime, and State truth establish one
objective current milestone and one singular approved next item. The current
item's objective DoD and every required gate must be satisfied. Silence, an
open Issue, historical advice, or a merely plausible next step is not Roadmap
authority.

`ROADMAP_CHANGE` remains Product Owner-gated. It includes reordering or skipping
milestones, selecting among materially different next paths, adding a major
initiative, changing architecture/product direction, changing Dataset or Gold
authority, or changing product/semantic acceptance. Execution never invents or
changes priority.

### Mechanical State Reconciliation

`MECHANICAL_STATE_RECONCILIATION = AUTO`. When authoritative evidence admits
exactly one factual result, Codex updates stale Roadmap, State, and control-plane
projections without asking the Product Owner to approve facts. Examples include
verified open-to-closed Issue state, open-to-merged PR state, accepted milestone
status, exact merge/runtime SHA, completed reconciliation, and the pointer to
the objectively completed milestone. The update must preserve historical
evidence and all approved ordering. Any change to priority, acceptance meaning,
or a choice between valid paths is `ROADMAP_CHANGE`, not reconciliation.

### Autonomous Issue Lifecycle

`ISSUE_LIFECYCLE = AUTO` when the Issue is the singular approved Roadmap item or
already belongs to the authorized scope. Codex may create it, create its branch,
and maintain its lifecycle. Codex closes it when the objective DoD is proven,
all required checks pass, its accepted changes are merged/reconciled where
required, and no subjective product/domain acceptance remains. Issue creation
or closure that would encode a new decision fails closed.

### Safe Automatic Merge

`SAFE_MERGE = AUTO` only when all conditions below are mechanically proven:

- the PR maps to an already authorized Issue and exact bounded scope;
- exact base, head SHA, changed-file inventory, and branch identity are known;
- mergeability is clean and no material review or human decision is pending;
- required focused/full tests, GitHub Quality Gate, diff/scope checks, and
  applicable Integrity gates pass without an unexplained new FAIL/WARN;
- no unexpected scope expansion, Product Rule conflict, semantic-authority
  change, Dataset/Gold authority change, destructive migration, security change,
  credential operation, or other high-risk/external effect exists;
- merge does not itself enact a Product Owner, domain, or architectural choice.

Classification uncertainty means `MERGE = HUMAN_GATE`. A governance/Product
Rule PR cannot use its own unmerged rule as authority. It may merge only under
authority already `ACTIVE` on main or an explicit Product Owner instruction
applicable to the exact PR. After merge, Codex records the merge SHA,
synchronizes local main by fast-forward-safe workflow, and verifies the actual
push-to-main Quality Gate before relying on the merge.

### Safe Automatic Runtime Reconciliation

`SAFE_RUNTIME_RECONCILIATION = AUTO` only for the known SeminarText governed
local runtime and only when all conditions below are mechanically proven:

- source branch is exact verified `main`, equal to `origin/main`, and the
  working tree is clean;
- repository checks pass and runtime drift is fully explained by the accepted
  merge being reconciled;
- `./scripts/seminartext-dev deploy` is the known governed path;
- the built-in backup succeeds, target scope is known, the operation is
  reversible, and a governed rollback path exists;
- no destructive/data migration, real project data, Dataset/Gold, semantic,
  credential/security, dependency/model/environment, unknown target, or
  externally consequential production-release mutation is involved.

Use exactly one governed deploy attempt for a reconciliation. After it, verify
the deployment inventory and hashes, functional smoke, required tests,
Integrity, and exact source/runtime identity. On failure, attempt at most one
governed rollback only when its target and safety are mechanically proven;
otherwise hard stop. A destructive, irreversible, unknown-target, or external
production deployment remains `HIGH_RISK_IRREVERSIBLE_OPERATION` or
`EXTERNAL_PRODUCTION_RELEASE` and is always a human gate unless a later explicit
policy covers that exact operation.

### Autonomous Failure Recovery

The existing post-deploy checks can be completed and durably recorded through
the [native activation/central registry adapter](docs/architecture/NATIVE_ACTIVATION_REGISTRY.md).
It does not authorize a deployment or replace any gate above; publication failure
is reported separately from native activation success.

Deterministic unit-test, lint/type, CI, generated-artifact, branch-drift,
runtime-hash, documentation-state, and mechanically unambiguous merge-conflict
failures are investigated and repaired autonomously when the repair remains in
scope and does not change product or semantic meaning. Rerun the complete
required verification after repair. Escalate only when repair requires a
product/semantic/Dataset/Gold choice, materially different architectures,
scope expansion, unavailable evidence, or non-mechanical safety judgment.

### Genuine Human Gates and Consolidated Reporting

Allowed escalation classes are `PRODUCT_DIRECTION`, `ROADMAP_CHANGE`,
`ARCHITECTURE_CHOICE`, `SEMANTIC_AUTHORITY`, `DOMAIN_REVIEW`,
`DOMAIN_AUTHORING`, `DATASET_AUTHORITY`, `GOLD_AUTHORITY`,
`HIGH_RISK_IRREVERSIBLE_OPERATION`, `SECURITY_OR_CREDENTIAL_DECISION`,
`EXTERNAL_PRODUCTION_RELEASE`, `UNRESOLVABLE_AMBIGUITY`, and
`PRODUCT_RULE_CHANGE` unless explicitly authorized.

Issue/branch/commit/push/PR mechanics, objective lifecycle updates, routine
review preparation, tests/CI retries, deterministic repair, mechanical state
reconciliation, a proven `SAFE_MERGE`, a proven
`SAFE_RUNTIME_RECONCILIATION`, backup/smoke/hash verification, and selection of
the singular approved next Roadmap item are not human gates by themselves.

The prohibited user-courier antipattern is: Codex finishes deterministic work,
the user transports its report to another system, that system confirms the
mechanically implied next action, and the user transports the instruction back.
Reports are not authorization boundaries. Codex keeps an execution ledger and
returns one consolidated report only at a genuine gate, hard stop, explicit
status request, or meaningful autonomous terminal milestone.

Default issue loop inside the Evidence-First Parallel Development policy:

`APPROVED ROADMAP -> OBSERVE/RECONCILE -> ISSUE/BRANCH -> IMPLEMENT -> TEST/REPAIR -> PR/QUALITY -> SAFE MERGE -> SAFE RUNTIME RECONCILIATION if required -> VERIFY/CLOSE -> STATE/ROADMAP -> NEXT APPROVED ITEM`

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

## Dataset, Gold, and Semantic Firewall

Autonomy never weakens Dataset or Gold governance. Dataset roles are read from
the current governed Registry; Dataset E remains
`EXCLUDED_FROM_TOPIC_ENGINE_EVIDENCE`, Dataset D remains locked until its
explicit gates are satisfied, and no open file, historical artifact, Issue, or
Roadmap position grants access. Role reassignment, Gold authoring/promotion,
evaluation contamination, and forbidden Topic Engine tuning remain reserved to
their established authority.

Codex may prepare machine proposals and review packets, but machine-generated
semantics never become authoritative merely because an autonomous loop can
continue. Human Review, `DOMAIN_REVIEW`, and `DOMAIN_AUTHORING` rules remain in
force at every transition.

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

## Disposable development workspaces

For temporary test/build/render/research subprocess work use
`scripts/seminartext-owned-run COMMAND [ARGS...]`. It supplies an owned TMPDIR,
cleans the exact workspace after exit/error/cancellation, and safely recovers
crash leftovers on the next run. The full CI suite and Integrity use this
mechanism. Hash-locked historical research adapters remain byte-identical;
execute them through this runner rather than modifying their historical bytes.
Use an explicit persistent output for deliberately retained diagnostic evidence;
do not place venvs, exports, candidate builds or evidence archives in system TMP.
Foreign/unknown/busy workspaces are retained, and exhausted owned capacity
blocks new work. No global prefix/age cleanup is allowed.
