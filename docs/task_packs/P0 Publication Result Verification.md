# P0 publication result verification

## Scope and acceptance

After a publication check completes, show its saved outcome independently of the
original export delivery. Bind a successful display to the latest scoped recovery
action and that action's settled proof in the export's retained provenance.
Pending, failed and unmatched actions must never reuse an older successful check.
Reopening the view after restart reads existing evidence and does not contact Sheets.
Locate the matching recovery actor throughout retained reconciliation history;
an unrelated later direct-operator reconciliation must not hide the saved result.
Before admission completes, the confirmation message must not claim acceptance.

The admin sees **Published output check**, **Publication check outcome**, the
completion timestamp in UTC, and total elapsed seconds. Confirmed means the
publication matched at that check; it does not cover later edits. Damaged or absent
results retain their separate guided recovery decisions. Export recovery status and
recorded export outcome remain separately labelled.

## Guided verification

1. After deployment, open the retained publication and use **Recheck** to display
   the already completed check. Do not repeat a completed check merely to test the
   new screen.
2. Confirm that the saved outcome and completion time appear. A missing matching
   proof must show unverified, even if the original export is confirmed.
3. Download the recovery report and compare its `publication_check` section.
4. On the next naturally required check, confirm once and follow progress with
   Recheck. A slow check is not permission for another check or restart.
5. If the outcome is damaged or absent, review the separate repair action and its
   evidence before deciding. This display change does not authorize a rebuild.

## Delay investigation

The supplied trace records a closed 170-request publication stream lasting
495.096 seconds. The bounded timing sample includes its first 149 requests:
306.936 seconds before dispatch and 104.102 seconds in provider calls.
The code enforces at least 2.1 seconds of durable request spacing. No pacing,
ownership, history, sealing, proof or settlement check is weakened here.

The trace also places proof creation about 171.813 seconds after stream closure.
It does not attribute that interval to individual steps. Add bounded phase timing
logs for retained history, provider readback, sealed history, sealed response
replay and final origin verification. These timings contain no response bodies
and are diagnostic only. A performance improvement is not yet demonstrated.

The supplied diagnostic encoded unspecified SQL UTC DateTime values through
PowerShell's local-time conversion. Absolute epoch-derived times need that
qualification; differences between them remain valid. Its action filter also
needs canonical UUID casing for the BIN2 source identity. Empty action results
are not evidence that no action ran.

## Boundaries and remaining work

No SQL migration, configuration flag, dependency, provider write or automatic
retry is introduced. RecoveryAction columns and scope filtering are checked
against the authoritative SQL repository definitions and disposable SQL tables.
The protected updater must include the complete publication-result transition.
An additional fixed nine-member transition supports the combined report/cache
handoff and publication-result release directly from its deployed predecessor.
Both complete before/after bundles are pinned; partial or foreign sets are refused.

This is a focused successor to the report/cache handoff release. Local validation,
security review, private promotion, protected package rehearsal and production
acceptance remain distinct gates. All F01–F05 items in
[P0 Final Recovery Acceptance](P0%20Final%20Recovery%20Acceptance.md) remain required.
Neither this result display nor a zero incident count completes P0.
