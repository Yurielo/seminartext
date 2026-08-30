## Goal

<!-- What should change, and why? -->

## Human gate

Classification: `AUTO`

Choose one:

- `AUTO` - Codex and automated QA can proceed without Yuri.
- `DOMAIN_REVIEW` - Yuri reviews prepared evidence/options before acceptance.
- `DOMAIN_AUTHORING` - Yuri supplies authoritative semantic content, such as Gold labels.
- `LOCAL_ACTION` - Yuri performs a local/UI/account action unavailable to tools.

Justification:

## Requirements

-

## Requirement-to-evidence mapping

| Requirement | Evidence (file, test, or command) |
| --- | --- |
| | |

## Verification plan

### Focused tests

Commands and expected result:

### Full tests

Command and expected result:

### Integrity

Record both `./scripts/seminartext-integrity` and
`./scripts/seminartext-integrity --json` results:

## Changed-file scope

List every file this Issue may change and confirm that no unrelated product,
algorithm, dataset, semantic, or runtime files are included:

## Post-merge acceptance

- [ ] Post-merge verification owner and acceptance criteria are explicit.
- [ ] The Issue is not considered complete from local tests alone.

## Deploy or runtime reconciliation

Required: `YES` / `NO`
If `YES`, identify the governed deployment command, authorization owner, and
post-deploy verification required:

## Definition of Done

-

## Guardrails

- Do not change production Topic Engine, benchmark Gold data, experiment configs,
  or CLI behavior unless this Issue explicitly requires it.
