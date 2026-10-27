# Issue #149 — activation evidence assessment and integration scope

Date: 2026-10-27. Authority: the direct Product Owner task
**Four-Product Architecture — SeminarText Registry Integration**.
This is bounded authorization, not advancement of the standing product Roadmap.

## Resolved authority

| Source | Exact commit | Document SHA-256 |
|---|---|---|
| Integra `docs/governance/UNIFIED_CODEX_RULES.md` | `86e0801963e85e8d8b121c569fe624bb64ede5df` | `8b8e31c7620d45e1e14429e07e7b97b2adc118745ce781a55b932213c55b646b` |
| SeminarText `AGENTS.md` | `48cabde2ddd7918480b4a6bb05ed39f774665c20` | `fa47a9b923a6ae19da76f31723164a3d41b3ee3e5f4c15410621ff9190f2bc79` |
| SeminarText `DEVELOPMENT_WORKFLOW.md` | same SeminarText base | `9b4652588066c1456a6641342a2955ae852215474393fdb741bfad4a174d3197` |
| SeminarText Product Rules Registry | same SeminarText base | `b59ba7205120ec1a0dd8fe0f881c26c8056ba7feb61bebd27c7100b59b899492` |
| Central `AGENTS.md` | `66c6a5128922f65c1993b59f5ba38923683aeb1e` | `d97fff57c37671d4f904f04e9723f06c7364e911aff534b58ec1ca8bea5da536` |
| Central `docs/architecture.md` | same central base | `61a49437994bd481d9be71bd26a7d24bfff77ae9e04abddf127e9c4c1fcbc9a0` |
| Central publication contract `README.md` | same central base | `cc50ac0a524370678bf0115d65b9dc6de24972ea624f191963e7c267a20f4b2b` |

PRODUCT_RULES_READ: YES
APPLICABLE_PRODUCT_RULES: PR-008, PR-009, PR-010, PR-011, PR-013, PR-014
PRODUCT_RULE_CONFLICTS: NONE

All ACTIVE rules were read. Product Rules, semantic authority and Dataset/Gold
content are unchanged. Native lifecycle requirements are reused, not replaced.

## Existing installed 4.0.0

Known target: `/Users/yurielokhin/bin/seminartext_4.0_work`.
Deployment backup:
`/Users/yurielokhin/.seminartext-deploy-backups/20261021_232456__a34bc84/manifest.txt`.
It records source `a34bc84`, source worktree
`/Users/yurielokhin/.codex/worktrees/group-runtime/seminartext`, and an empty
branch field. The script writes this manifest **before** runtime replacement.
It does not attest later completion or identify the authority for that old run.

[PR #145](https://github.com/Yurielo/seminartext/pull/145) records 368 passing
tests on its implementation and a successful Quality Gate, completed at
2026-10-21T20:24:27Z. The backup manifest is dated 23:24:56 local time (UTC+3),
later than that CI completion. PR body and discussion contain no post-deployment
Integrity/activation completion record. The bounded known worktree/backup
inspection found source/schema files and backup material, not that final record.

The current baseline Integrity run at exact main
`48cabde2ddd7918480b4a6bb05ed39f774665c20` again established:

- G1–G5, G7, G8 PASS; installed G2 inventory 24/24 SYNC and bounded functional smoke PASS;
- G7: 368 passed, 0 skipped;
- G6: existing NOT_IMPLEMENTED; aggregate PARTIAL with exit 0;
- next-issue Roadmap projection remains false; this direct Owner-authorized
  task does not reinterpret that projection or advance its semantic milestone.

This fresh read-only verification is **not** a fabricated historical
post-deployment run. The missing evidence is an exact successful native
installation completion record linked to its source/target, together with the
subsequent required native post-check result for that same operation. Neither
the earlier CI, a pre-deployment manifest nor present matching hashes proves it.

Initial registration is therefore **not performed**. SeminarText remains
explicitly unregistered; Integra remains unregistered. Existing VideoText and
BookText activation records and their evidence are not modified. No production
deployment is justified solely to generate a receipt.

## Implementation and completion boundary

See [native activation integration](../docs/architecture/NATIVE_ACTIVATION_REGISTRY.md)
for the exact receipt format, lifecycle commands and pending/retry semantics.
Only source-side deployment tooling, documentation and tests change; the 24
deployed component sources are unchanged, so a runtime reinstall is unnecessary.

Repository verification results and exact implementation/merge commits are
recorded on the associated PR and consolidated task report. The independent
implementation can complete while historical initial registration remains
blocked by the specific evidence gap above. No new Owner decision is invented
to conceal that distinction.
