# ProcConfig admission and attempt reporting

## Approved change and cause

A ProcConfig invocation can fail in the initial coordination request before an
ExportPreparation row exists. Preparation-based recovery discovery therefore
cannot discover that failure. Returning `(False, report)` also previously let the
startup observer label the coroutine completed. Both reporting defects are
corrected independently of the identity of the historical lock holder.

A separately captured natural collision showed two sessions from the same bot
process competing for the account application lock. The holder retained it for
about 22 ms. The refused caller was recovery discovery's unowned SQL snapshot;
that snapshot previously had no safe retry wrapper. Configuration preflight was
strongly correlated with the holder's resources and timing. This does not prove
who held the lock during the earlier ProcConfig failure. Two connections alone
are not a defect and are not a reason to remove coordination protection.

## Implementation boundary

- Each non-dry-run ProcConfig invocation saves an independent UUID attempt and
  its producer operation UUID before admission. Receipts live in
  `data/proc_config_attempts/<account-and-storage-scope-hash>/`. Atomic replacement
  includes a flushed file; per-attempt files preserve earlier failures. These
  private runtime files are excluded from Git and must survive deployment.
- Phase changes are saved before inputs and before SQL writes can start. A failed
  pre-input attempt explicitly states that it retained prior configuration.
  Later failures and interrupted attempts make no such assertion.
- A begin-recording failure refuses to start the import and reports `unrecorded`.
  A final-recording failure returns failure even if the import reported success;
  the last durable unconfirmed phase remains for recovery. Verify that original
  operation before retrying. An exception or cancellation never fabricates a
  terminal success record.
- A passive `configuration_attempt` adapter exposes receipts in the existing
  recovery centre and downloaded incident reports. It has no repair/replay or
  ownership-release actions. Missing/corrupt evidence is unavailable, never
  resolved. A successful attempt resolves only its own observation. Later
  successes and health probes cannot resolve a previous failed attempt.
- Discovery rotates through at most 100 receipt payloads per page; receipts are
  retained without age-based expiry. Directory enumeration remains proportional
  to retained filenames, a possible future optimisation if measured necessary.
- Startup's ProcConfig completion check treats false as failed. Process-worker
  summaries retain attempt identity, outcome and recording status.

## Safe pause and retry

Only the publishing ProcConfig **initial DAL request**, and the read-only unowned
SQL snapshot, opt into a five-second retry budget with at most eight attempts.
All other coordination calls retain their existing one-second default. A shorter
inherited deadline still wins. Pauses start at 25 ms and increase to at most
250 ms, bounded by remaining budget. The budget is cooperative: a slow database
call or required cleanup may exceed it; no unsafe cancellation is introduced.

Retry requires the exact classified application-lock timeout (`result=-1`) and
acknowledged rollback **and** connection close. The retry uses a fresh connection;
no failed transaction is retained during the pause. Cancellation, deadlock or
other refusal results, unknown commit, failed rollback/close, generic SQL errors,
and an externally supplied transaction are not replayed. The same request
identity is retained. No provider read, import callback, writer execution or
whole import is enclosed in this new retry scope.

Existing admission diagnostics retain requesting-session identity separately
from blocker identity. The refused transaction now records connect, cursor acquisition, transaction-body,
rollback and close durations. Transaction-body time includes DAL Python work and
SQL execution; it is not a measurement of lock-held time. The startup operation now has an explicit
configuration-import label. Persisted lock facts contain no driver prose or SQL.

## SQL and deployment contract

Validated against the authoritative SQL repository: existing ExportPreparation,
ExportResource and RecoveryIncident contracts are unchanged. No table, stored
procedure, index, permission, ProcConfig row, migration or activation change is
required. The existing RecoveryIncident SourceKind accepts the passive adapter's
name, with bounded JSON evidence and the existing account/storage/guild scope.

The protected updater must authenticate the complete nine-file runtime bundle.
The new transition is `procconfig_admission_recovery_v1`; previous transitions
remain unchanged. Upgrade the installed updater from the reviewed release
package before using the ordinary update command. A new transition in target
source alone cannot authorize installation. Publish through the scrubbed mirror,
then apply only reviewed changed files to a branch based on private main. Deploy
only private main through the protected source/seed/drain/start/readiness path.
Preserve attempt files, all existing receipts and retained work. A code rollback
requires a reviewed reverse transition; do not bypass the source guard or delete
attempt history to make rollback appear healthy.

## Verification and acceptance

Development tests cover failure before inputs, late failure, interrupted work,
recording failures, restart discovery, separate later success, scoped history,
corrupt evidence, false startup completion, bounded retry, inherited deadlines,
rollback/close failures and unknown commit. Transition tests authenticate every
member and reject missing, changed, duplicate or widened bundles.

After an authorized deployment:

1. Retain the updater's exact private source, matching policy, successor and
   readiness receipts. Discord online is connectivity evidence only.
2. Let ordinary startup and monitoring run. Retain the ProcConfig attempt UUID,
   operation UUID, phase and final recording status. Compare the startup result
   with the attempt and import report. Do not deliberately fail production or
   replay old imports to exercise the negative path.
3. If a natural admission collision occurs, verify recovered/exhausted structured
   diagnostics and acknowledged cleanup. After exhaustion, require the failed
   attempt in recovery with the correct pre-input/late/unknown distinction.
4. Download a fresh recovery report across a later healthy monitoring cycle.
   Prior failures must remain visible; the monitor's success cannot clear them.
   A missing receipt is an unavailable check. No new success is inferred from
   the old absence of a preparation or from zero outstanding incidents.
5. No historical attempt is fabricated by this release. Retain the original
   incident's supplied logs as historical evidence where no receipt existed.

### Carry-forward scope ledger

| Area | Evidence already held | Remaining acceptance |
| --- | --- | --- |
| Source and startup | Previous protected deployment and Discord readiness | New release's source/policy/successor receipt |
| Monitoring reliability | Active checks precede a bounded history slice; healthy cycles observed | Fresh report retains original failed cycle through recovery; real sweep coverage/latency |
| Profile and names | 2,444 profiles and names refreshed; profile save confirmed | No claim about every unexercised race |
| Stats cache | 415-row KVK16 last-known-good cache; expected off-season provenance | New import/execution and delivery evidence remain separate |
| Persistent views | 21/21 attachments observed | Visible controls/callback acceptance where not already accepted |
| Empty event cache | Valid loaded-empty state; registration-only work running | Natural populated transition, reminders/DMs and Overview lifecycle |
| Existing callbacks | Previously accepted Location and eligible Ark callback evidence | Preserve acceptance; do not repeat accepted business operations |
| Import/export | Previous runtime's individual receipts retained | Fresh end-to-end proof for the new runtime; degraded readiness is not delivery |
| Wider programme | WS1-WS6 and R01-R18 remain tracked | P0 F04 natural rollover and final F01-F05 reconciliation remain open |

The separate SQL diagnostic capture may remain enabled after a bot restart.
Review its bounded files and stop it through its existing approved stop script
when the investigation no longer needs it. Do not infer that this application
release stopped the SQL session or established the original holder.
