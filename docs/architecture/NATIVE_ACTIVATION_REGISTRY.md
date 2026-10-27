# Native activation receipts and central publication

Issue [#149](https://github.com/Yurielo/seminartext/issues/149) implements the
Owner-authorized SeminarText adapter to `Yurielo/four-product-architecture`.
Product Rules and the existing deployment, QA, Integrity, Owner and rollback
authority remain unchanged. These commands do not grant deployment permission.

## Existing deployment and completion

`scripts/seminartext-dev deploy` retains its check, tracked-cleanliness guard,
backup, temporary-file replacement, hash verification and functional smokes.
It additionally saves an operation record before runtime replacement and an
`installation-verified.json` after its existing checks. Neither is an activation
receipt. A pre-deployment backup manifest or matching hashes alone is insufficient.

Complete the already required post-deployment Integrity/full tests and publish:

```sh
# Only when the native deployment itself already has applicable authority:
SEMINARTEXT_DEV_REPO=/exact/governed/source scripts/seminartext-dev deploy --complete

# Or finish that same instrumented deployment later, without reinstalling:
SEMINARTEXT_DEV_REPO=/exact/governed/source \
  scripts/seminartext-dev activation-complete /exact/deployment/backup-directory
```

The completion command invokes the existing `scripts/seminartext-integrity`
once; G7 runs the existing full test command. It requires every currently
blocking gate to PASS, complete matching G2 inventory and functional smoke,
clean source identity, and tests without hidden skips. Existing G6
NOT_IMPLEMENTED remains visible; it is not promoted to PASS or made a new gate.
This automates existing post-checks, not a second QA or Owner Acceptance process.

The same source commit, contract and installed component hashes must remain
unchanged throughout completion. A previous successful receipt is reused without
rerunning checks. Failed verification attempts retain their reports but never
produce a successful receipt. Historical uninstrumented backup directories
cannot be converted into success by this command.

## Durable native receipt

`activation-receipt.json` in the existing backup/operation directory contains:

- schema version, product, technical SUCCEEDED status and deployment target;
- actual activation completion time (after required post-checks);
- exact source commit, installed version and all declared component hashes/paths;
- immutable installation record, original backup-manifest hash and mutation ID;
- the native Integrity report, its byte hash and its source contract;
- an explicit limit: technical activation does not grant semantic acceptance or
  claim integrated product MVP acceptance.

Evidence files use atomic, no-overwrite creation. A private mutation epoch and
lock in the existing backup root prevent an old receipt being published after
a newer deploy or rollback, including restoration of identical bytes. The epoch
contains only a random operation token, no version/current pointer. It is a native
mutation interlock, not another product-version registry. Registry publication
and mutation-start share the lock; product processing does not depend on it.

## Publisher integration and independent operation

`SEMINARTEXT_REGISTRY_REPO` selects the existing central checkout; default:
`~/Documents/four-product-architecture`. It must have the exact approved GitHub
origin and an unmodified publisher/schema. `SEMINARTEXT_REGISTRY_PYTHON` may
select its supported Python; otherwise its existing `.venv/bin/python` is used,
then the caller's interpreter. No dependencies are installed by this adapter.

At deployment start, a bounded read-only lookup captures the central predecessor
before runtime mutation. Offline operation falls back to a known cached commit,
or explicitly records no available baseline. This never prevents standalone
deployment or product use. Rollback does not contact the registry.

After native success, the adapter uses the central module's existing encoding,
schema validation, event identity and `publish()` implementation. It builds a
SeminarText event with its 24 native artifacts and no invented upstream product
dependency, binds the entire native receipt, retains the exact event/proof in the
operation directory, resolves central main, and invokes the existing atomic
publisher. Publication runs in a bounded owned process group; timeout never
stops another workload.

No Git push/CAS implementation or authoritative current-version register is
copied into SeminarText. The central publisher checks the predecessor/generation,
atomically commits event/evidence/current, and verifies its remote read-back.
Actual consumer identities are not changed by SeminarText registration.

## Pending publication and retry

Exit 0 means the requested step succeeded. Exit 2 means native activation
evidence is incomplete. Exit 3 means `PUBLICATION_PENDING`: preserve the
successful native deployment and its evidence; do not roll it back merely
because registration failed.

```sh
scripts/seminartext-dev registry-retry /exact/deployment/backup-directory
```

Retry does not reinstall or rerun native tests. Once prepared, event bytes,
predecessor, generation and proof are never regenerated to bypass a newer
activation or rollback. Other-product publication may advance central HEAD;
the unchanged event remains retryable if its own predecessor still matches.
A stale same-product predecessor is rejected. Confirmation records retain the
actual returned current pointer, including a superseded idempotent event.

If the central checkout/interpreter/initial snapshot was unavailable before
preparation, the native receipt remains durable and the report explicitly says
`event_prepared: false` (when reported by the publication worker). It does not
invent a generation. With no deployment-time baseline, preparation is permitted
only for an unregistered SeminarText; replacing an existing record requires
separately verified reconciliation. A stale cached baseline fails closed.

The existing `rollback` command keeps its file restoration and guard backup.
It invalidates older pending activation operations before changing runtime bytes
and explicitly reports `REGISTRY: RECONCILIATION_REQUIRED`. It does not infer the
restored source from a backup's forward-deployment manifest or fabricate a
central rollback event. Any central rollback still needs exact restored release
identity and successful native evidence under the central rollback contract.

The central registry remains the sole published current-version authority.
Until read-back succeeds, report native success separately from pending registry
publication; never claim VideoText/Integra or the whole architecture synchronized.

## Verification

Native fixtures cover incomplete gates/evidence, immutable receipts, runtime
drift, retry, stale predecessors, rollback invalidation and actual isolated
deploy/rollback byte preservation. The ordinary suite has no GitHub dependency.
The explicit `tests/registry_adapter_integration.py --registry-root PATH` check
uses the real central publisher on a local bare Git repository with synthetic
native evidence, preserving the original two product histories. Run it through
`scripts/seminartext-owned-run`. Native and central required suites remain their
existing repository checks; no production deployment is part of these tests.
