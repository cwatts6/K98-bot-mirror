# D5c capture resumption group

Existing approval covers preparation, review, execution and related test-only
corrections. Countdown before this group: 28/73 final-action routes accepted,
45 remaining; 25/25 inspectors and 9/12 D5c families accepted.

## Scope and actual boundaries

Exercise four `resume_capture` routes together: stats import, all-KVK, player
report and configuration producer. The 193 checks comprise 186 behavior cases
and seven runner controls. Reuse the accepted queue fixture without changing it.
Original service/adapter, producer-session guard, adoption transaction, ownership
authorization, generation transition, serialization, retained snapshot persistence
dispatch, captured checkpoint/release and final queue admission remain loaded.

Only database/file transport and output-reading effects are inert. A labelled
in-memory output reader supplies deterministic rows. The store's `put` transport
retains verified canonical bytes in memory; real filesystem creation/fsync is not
claimed. The original `LegacySnapshot.persist` dispatches that store write.
The original store read/hash/length checks and queue admission are reused.
Retry scheduling remains disabled. `execution_evidence=False` explicitly selects
ownership-only producer-cursor verification; installation/profile validation is
separate, not bypassed in application code. No runtime code is modified.

The producer resource is the canonical snapshot name in this isolated model.
The real retained reservation, database and original failure evidence are never
accessed or changed. Real SQL guard scheduling, driver/session cleanup, filesystem
durability, deployment compatibility and business outputs remain separate proof.

## Cases and assertions

For each route test stale tokens, versions, account/storage, owners/fences,
missing/extra/wrong resources, active jobs/operations, changed generation/request,
closed capture, foreign action marker, producer/account refusal, missing guard,
and lost adoption/resource CAS. These cases require unchanged model state.

After adoption, test changed preparation/resource versions, output-read failure,
lost generation CAS, mismatched pre-existing complete output proof, storage failure,
changed versions after storage, lost captured-checkpoint CAS and lost release CAS.
Require the original execution receipt and owner to remain intact, no queue job,
and retained orphan bytes when persistence preceded a failed checkpoint. Commit
uncertainty and physical cleanup failure remain a separate fault/custody group.

Success cases cover pending and already complete proof, same action marker,
already captured acknowledgement, idempotent completion, known/current/stale
reconciliation and capture-only pipeline handoff. The handoff association is an
explicit inert seam; actual pipeline-link validation remains separately open.
Player/configuration no-export cases must capture without queuing spreadsheet work.
Successful cases verify exact marker, retained bytes, single read/write, queue
cardinality, resource release, and no second output read/write on acknowledgement.

## Review and bounds

Changes security review, Deep off, exact five-file snapshot: test, renamed runner,
preparer, manifest and this plan. Parent and independent static review precede
execution. Preserve the prior queue receipt and every inherited pin; recheck the
authoritative preparation/resource/job SQL definitions and bindings. No SQL source
or ordinary Git branch/index change is part of the group.

Use the dedicated isolated/no-site/no-bytecode runner, 300 seconds and 1 MiB
combined intent/result, stopping at the first failure. The accepted runner changes
only its group-specific names. Any corrected attempt retains the original attempt
and uses new evidence. Full pytest/import smoke/registration and repository-wide
PR validators are deferred to PR readiness because they would exceed this bounded
test startup scope. No unrelated refactor or optimisation is introduced.

1260 native seconds remain, including 1000 protected later-D5 seconds; 50 Windows
test seconds, 21 consumed inputs and 11/64 synthetic database rows remain unchanged.
This group consumes zero native seconds, new inputs or database rows. No extension
is required. Acceptance updates the route count only after receipt adjudication.
C04/C05 native work, remaining C06 routes and D5d/e/f remain open.
