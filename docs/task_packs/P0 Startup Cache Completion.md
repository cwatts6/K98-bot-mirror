# P0 startup cache completion and saved timing collection

## Scope and authorization — 21 October 2026

Implementation, disposable validation, focused PRs, security Changes reviews and
protected updater packaging are authorized. Merge, deployment and production
repairs remain operator actions. The finite checklist in
[P0 Final Recovery Acceptance](P0%20Final%20Recovery%20Acceptance.md), the P0b
monitor/admission closeout and both original guided-recovery packs remain binding.
P0 is not complete; no remaining P0 work moves to P1.

The supplied complete report at 06:38 UTC contains all 17,526 records, all resolved,
and a successful new publication check lasting 851.2 seconds. That saved check is
the natural timing sample. Do not repeat it. The report/log do not independently
establish exact deployed source bytes or cover every recovery failure family.

## Focused fix

The startup player-cache deadline cancelled its coroutine after 20 seconds.
The existing protected thread drain waited for the SQL worker but preserved
cancellation, hiding the actual returned cache result from startup diagnostics.
The deadline now leaves this task pending. Its original worker finishes once,
then an off-loop readback under the existing cache lock verifies the complete
saved payload against that returned result. The report records a bounded hash,
source quality, row count and verification time. It contains no player rows.

Failed, absent, malformed or changed results do not become completion. A valid
last-known-good or refresh-skipped result retains that source classification;
it is not proof of a fresh SQL calculation. The check performs no SQL operation
and does not invoke the builder again. Shutdown still cancels and drains the
original worker, preserving uncertainty. Observations are process-local; restart
does not turn an older observation into a current completion or a business receipt.

Ownership remains in the startup wrapper and cache service. No SQL is introduced
into commands/views. Existing `drain_thread`, `acquire_lock`, cache error types,
cache path and diagnostic recording are reused. No schema, procedure, dependency
or configuration-flag change is required. Authoritative `dbo.SP_Stats_for_Upload`
and `dbo.STATS_FOR_UPLOAD` definitions were inspected in the SQL repository;
their existing calculation and payload contract are unchanged.

## Saved publication timing

`scripts/Read-K98PublicationTiming.ps1` resolves the installed scheduled-task
startup gate, its hash-bound policy, current incarnation and pinned authority
manifest. It reads only the three fixed rotating timing files under the manifest's
evidence root, with shared access and size bounds. Output is restricted to the
five known phase names, completion flags, durations and UTC end times for the
successful check's window. It does not run application code, SQL or a provider
check, and it does not export manifests or other private logs. Missing phases
remain missing evidence; no performance cause is inferred from source inspection.

## Validation and release gates

Tests cover original-worker completion past deadline, failed/missing/changed cache
readback, preservation of old bytes, last-known-good classification, shutdown and
repeated cancellation, and no reuse of an older process observation. Collector
fixtures cover active-file shared reads, bounded output, partial records, time
window, redaction and checksum refusal. The exact three-runtime-file updater
transition rejects partial, foreign and renamed transitions; an absent predecessor
is allowed only for the explicitly pinned new service file.

Security target: Changes, Deep off, exact mirror/private diffs from their separately
verified main histories. SQL has no diff. Local tests and review do not establish
production admission, provider outcomes or deployed process bytes.

After operator deployment through the protected updater, inspect the ordinary
startup observation via `/ops dl_bot_status` and its complete report. A slow build
should move from `deadline_elapsed_pending` to `completed_after_deadline` with
`completion.kind=player_cache_readback`. A failure remains failed with bounded
diagnostics. Do not request a separate stats calculation to prove this fix.

## Remaining P0 obligations

| Family | Required remaining work |
| --- | --- |
| F01 | Attribute the saved 851.2-second sample against request timings before optimization; finish absence/damage, replacement and repeated-repair-failure acceptance. |
| F02 | Guided all-copy-loss evidence/verified backup restoration or independently qualified successor; unattributed holds, configuration and ownership conflicts. Preserve unknown originals and foreign/live work. |
| F03 | Validate this startup fix through normal deployment; finish historical partial configuration, UPDATE_ALL2, durable pipeline stages and pre-request failures with continuation/supersession/disposition. |
| F04 | Preserve the prior disposable rollover qualification; natural production acceptance remains a separate evidence class. |
| F05 | Finish the cross-family permission, stale/concurrent action, restart, lost acknowledgement, changed config, live writer and repeated repair failure matrix; qualify updater and separately verify natural admission and outcomes. |

The tracked-view startup deadline remains the separately scoped P1 item. Zero
open incidents does not close the remaining P0 obligations above.
