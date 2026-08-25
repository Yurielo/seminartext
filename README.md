# seminartext
SeminarText 4.0 — seminar processing, transcription, topic analysis and knowledge extraction pipeline

## Operating model

The project operating model is documented in
[`DEVELOPMENT_WORKFLOW.md`](DEVELOPMENT_WORKFLOW.md). Future Issues should state
their human-gate classification: `AUTO`, `DOMAIN_REVIEW`, `DOMAIN_AUTHORING`, or
`LOCAL_ACTION`.

## Codex GitHub workflow

Local Codex work should use GitHub Issues and Pull Requests directly, without
manual copy/paste of issue text or PR reports through the user.

### One-time local setup

Install and authenticate GitHub CLI for the `Yurielo` account:

```bash
gh auth login
gh auth setup-git
```

Do not store GitHub tokens, passwords, SSH keys, or credential output in this
repository.

### Verification

From the repository root, verify that private GitHub access and HTTPS git
credentials work without interactive prompts:

```bash
gh auth status
gh issue view 3 --repo Yurielo/seminartext
git fetch origin
gh pr list --repo Yurielo/seminartext
```

The final branch push for a task is the push-capability check for that task.

### Task workflow

For each GitHub Issue:

1. Read the Issue directly with `gh issue view ISSUE --repo Yurielo/seminartext`.
2. Start from an up-to-date `main` branch.
3. Create a dedicated branch for the Issue.
4. Implement only the requested scope.
5. Run the relevant tests and verification commands.
6. Commit only files that belong to the Issue.
7. Push the branch to `origin`.
8. Open a Pull Request against `main` with `gh pr create`.
9. Do not merge the PR from local Codex.

ChatGPT/Product Owner reviews the PR through GitHub and either requests changes
or merges it.

### Safety

- Do not change product code for setup-only workflow issues.
- Do not change Topic Engine logic or benchmark data unless an Issue explicitly
  requires it.
- Do not expose credentials in logs, documentation, commits, PR descriptions, or
  comments.
