# P0 publication check progress

## Approved scope and evidence

Continue the operator-authorized publication-check stall repair, with guided
verification and all P0-F01–F05 acceptance remaining mandatory. No production
replay, merge or deployment is authorized by this task pack.

The operator's read-only trace shows two closed 170-request publication streams
lasting approximately 497 and 507 seconds. Both later produced confirmed proofs.
The bounded request sample contains successful requests and substantial pacing
time; it is truncated and does not establish every source of delay. A snapshot
with no current SQL waits does not exclude historical waits.

Offline reproduction established an additional orchestration race: a concurrent
Recheck can classify the original action as not applied after its own probe stream
changes the evidence token, although the original execution is still running and
later settles successfully. Before stream registration, concurrent reconciliation
can instead attempt duplicate execution.

## Current focused implementation

A process-shared, nonblocking incident guard excludes receipt reconciliation and
repeat execution while the original recovery call remains active. Service objects
are rebuilt per interaction, so an instance-only guard is insufficient. Other
incidents remain independently available. Exceptions release the local guard.
Concurrent review returns the stored incident and local progress without entering
an authority-backed inspection. Fresh dispatch by the guard owner still performs
its normal domain inspection and evidence check.

This is scheduling, not authority. Durable action claims, actor permissions,
fresh evidence, domain ownership and receipt verification remain mandatory.
Restart loses the scheduling guard and retains the existing durable reconciliation
path; no completion or release is inferred from local process state.

The authority accepts a fixed publication/retirement-recovery proof selector and
returns bounded progress while one owned proof thread runs. The Bot polls the same
request; polling never dispatches a proof. A missing request after authority restart
returns unavailable, retaining durable SQL/private evidence for recovery. The proof
producer, membership checks, private readback and SQL settlement remain unchanged.
Only readiness and exact progress polling are served alongside the proof.
Effective-registration reads share the proof's authority lock and are refused as
busy before dispatch, so they cannot block the serial control connection.
Other actions are also refused as busy before dispatch; local
observational calls made by the proof itself retain the existing typed broker.
Authority shutdown joins its owned proof before draining the execution session.
An already-owned mutation delivery waits on the exact authenticated pre-dispatch
busy response, retaining its claim and attempt. It retries only the refused
message, not an unknown acknowledgment or dispatched provider request. Read-only
probes still return busy promptly. This prevents publication checks from turning
unrelated queued exports into uncertain failures.

The admin receives an immediate private explanation of the wait. Recheck and the
downloadable report show the live call's elapsed time without treating that
transient observation as a success receipt. Monitoring classifies a known busy
authority as waiting and retains any failed checks until independently verified.

## Required acceptance before this patch ships

- Concurrent Recheck and repeat confirmation leave the running action pending,
  both before and after its own probe stream appears.
- Exactly one original execution settles; only its durable receipt verifies it.
- Concurrent monitor reconciliation does not dispatch the same action twice.
- Another incident remains accessible; exceptions do not retain a local guard.
- Guided recovery, report, permission and persistent-action regression tests pass.
- Changes security review, private promotion parity and protected updater
  qualification complete before a release handoff.
- Slow proof execution leaves readiness and progress responsive; conflicting
  actions do not enter the authority; selector substitution is rejected.
- Restart/missing progress never replays work; shutdown waits for the owned proof.
- Final acknowledgements still require the exact snapshot and immutable ProofID.

Initial validation: 229 race/recovery tests passed, followed by 493 affected
private-tree tests for the first progress implementation. Final validation,
security review and package qualification remain release gates.

## Operator verification after qualified deployment

Use **Check published outputs**, select one known retained output, review its
identity and links, then confirm **Check published output** once. Keep the bot
running. Recheck should show the existing check and elapsed time while status and
the complete report remain available. The final incident must reflect the saved
proof; a successful read is not permission to rebuild or replay an import.
If verification is unavailable, inspect the report and retain the evidence.
No automatic redispatch follows loss of the authority's local progress.

No SQL migration or dependency change is required. The installed updater must
carry the complete exact publication-progress transition. All remaining
P0-F01–F05 work stays in the final acceptance checklist.
