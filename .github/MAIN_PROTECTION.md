# `main` protection contract

This document records the required GitHub configuration for SeminarText. It is
not evidence that the settings are currently enabled.

## Required rule

Configure a branch protection rule or repository ruleset targeting `main` with:

- pull requests required before merge;
- at least one approving review;
- stale approvals dismissed when new commits are pushed;
- all review conversations resolved before merge;
- the branch required to be up to date before merge;
- required status check `Quality Gate` (shown in the GitHub UI as
  `SeminarText CI / Quality Gate`);
- force pushes and branch deletion blocked;
- direct pushes blocked, with bypass disabled except for a documented emergency
  action by the repository administrator.

The Product Owner or repository administrator must enable and verify this rule
after the repository has access to GitHub branch protection/rulesets. For the
current private repository, the GitHub API reports that this capability requires
GitHub Pro or a public repository. Changing the plan, repository visibility, or
GitHub settings is outside Issue #89 implementation authorization.

## CI boundary

The `Quality Gate` job is deterministic and intentionally excludes model
downloads, heavy ML runs, Topic Engine experiments, Dataset D access, deployment,
and runtime mutation. It installs the pinned `dev_test` dependency profile and
runs repository checks, focused governance/integrity tests, the full test suite,
and both Integrity report formats.

GitHub-hosted runners do not contain the accepted deployed SeminarText runtime.
Consequently, G2 may be `WARN`/unverified in CI when no deployed runtime exists;
it must not be represented as synchronized. Governed deployment and acceptance
of runtime truth remain a separate, locally authorized post-merge operation.
G5 and G6 retain their explicit `NOT_IMPLEMENTED` status until their own Issues
are authorized. Every implemented repository-side gate must otherwise pass.
