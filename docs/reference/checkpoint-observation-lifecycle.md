# Checkpoint and recovery observation lifecycle

Approved correction scope, 27 October 2026. Historical production evidence proved
SQL completion followed by a checkpoint timeout and successful capture recovery.
Local two-session reproduction established an opposed lock order. Retained
production traces did not identify the historical blocking session; that specific
attribution remains unconfirmed.

## Shared contract and broader conflict audit

| Path | Conflict or protection | Correction / validation |
| --- | --- | --- |
| Stats import checkpoint vs stats inspection | Writer locked resource then preparation; observer locked preparation then resource after SQL released its execution guard | Observer takes nonblocking global producer guard and account mutex before rows. Guard spans SQL-to-checkpoint/capture interval. Native tests exercise both entry orders. |
| Legacy unreceipted observer | Inherited the same unsafe snapshot ordering | Inherits corrected admission; absence of a receipt never permits bypassing an active producer. |
| All-KVK and player-report observers, including configuration producer recovery | Global guard already covered active production, but admission and teardown needed account serialization | Reuse the same observer admission rule. Native tests cover all four DAL classes. |
| All observation transactions | An initial locked read can retain rows while waiting on a later row, including broad ActivePreparationID scans | Dedicated observation connections use LOCK_TIMEOUT 0. Row timeout/deadlock becomes waiting only after rollback and close acknowledge. No mutation retry follows from observation. |
| Import adoption, settlement and producer-refusal closure | Explicit producer/execution guards plus account mutex protect mutation | Preserve guard order, owner/fence/version, exact evidence token and unknown-outcome holds. Existing lifecycle suites remain required. |
| ProcConfig/player-report atomic publication | Completion checkpoint uses the business cursor; season read uses that same cursor | Preserve same-cursor behavior. No retry policy on an external cursor. Existing producer and continuation suites cover atomic publication and cancellation. |
| Nested all-KVK admission and actual producer authorization | Inspected callers authorize before business SQL; nested ownership is revalidated | Preserve current caller order and ownership checks. No additional independent authorization may be introduced after a producer takes ownership rows on another connection. |
| Pipeline review | Account mutex precedes row snapshot, with immediate row-lock timeout | Preserve nonblocking review and ensure SQL scope ends before authority/provider work. |
| Queue admission / health withdrawal | Account-first serialization and exact non-entry evidence | Preserve bounded existing retry, actor/request identity, no-stream/no-execution proof and restart reconciliation. Previous live probe cleanup is already accepted. |
| Configuration recovery, unowned SQL hold, target containment, failed-export closeout and rollover containment | Account/resource mutexes precede locked ownership rows | Preserve ownership checks; new whole-request observation context covers initial discovery reads as well as final inspection. Mutations retain uncertainty semantics. |
| Source output pool / rollover | Mutation paths acquire account/resource/pool mutexes; initial discovery uses ordinary reads | No demonstrated inverse locked snapshot cycle. Shared nonblocking observation policy covers waits in supporting reads. Preserve exact CAS and provider proof gates. |
| Failed/replacement/rollover/configuration/target/evidence authority inspections | Process boundary loses caller context; initial selection read preceded observe_call | Explicit fixed read-only selector gets context around the whole broker dispatch. Execute, reconcile, context/sealing, malformed requests and lost replies are excluded. |
| Stage receipt observation | A newly admitted producer can make post-import inspection busy after business work returned | Retain the returned facts, persist observation_pending as unconfirmed, and never replay business work because its later observer was busy. |
| Recovery notification correlation | An interrupted caller could miss the later export association and cache readiness publication | Bind the exact pipeline before dispatch; read scoped stage receipts nonblockingly, verify current cache bytes, and require existing exact export delivery proof. |
| Monitor status | Successful 164-217 second cycles exceeded 90-second completed-check freshness | Advancing bounded cycle is operationally healthy while check_state stays stale and completed_check_age_seconds remains explicit. Genuine check failure, stall or maximum cycle duration still degrades status. |

No command, view, permission, activation flag or persistent evidence schema changes.
Existing helpers reused: transaction, observation/observe_call, retry_coordination,
_mutex, exact SQL receipt and owner/fence/version CAS. New authority selector helper
centralizes the process-boundary policy. No SQL was added to command/view modules.
Existing legacy stats orchestration remains in place; its outcome reporting now
waits for exact receipt reconciliation.

## Safe pause and retry

Only the independent UPDATE_ALL2 writing-to-committed metadata checkpoint opts in
to row-lock retry. Each attempt checks preparation ownership/version and the exact
completed SQL receipt, including file identity and absence of settlement. Only
SQL 1222/42000 or 1205/40001 from the transaction body qualifies, after acknowledged
rollback and close. Existing typed application-lock retry remains supported.

The budget is five seconds of contention, at most eight attempts, with capped
backoff and a total fifteen-second horizon including credited connection setup.
Driver connection/statement timeouts retain their existing bounds. No cancellation,
cleanup failure, commit-acknowledgement loss, changed ownership or external producer
cursor is retried. Exhaustion retains work for exact receipt reconciliation.
UPDATE_ALL2 and provider delivery are never inside the retry body.

If SQL completion is exact but capture still needs reconciliation, the import
audit records completed SQL and retains the capture preparation reference. The
pipeline, queue and notification handoff show capture pending, stop dependent
stages, and neither report a failed import nor claim an export was submitted.
The notification journal binds its exact pipeline before business work. Subsequent
observation can recover the queued export association and verify current cache
bytes against that pipeline receipt, independently, without dispatching work.
Both notification SQL readers yield on contention. Changed/missing cache bytes
cannot certify readiness or block independently verified export delivery.

Recovered checkpoint logging retains the redacted native error and requester
session ID, attempt count and elapsed time at INFO level. A requester ID is not
the blocker. The SQL companion contains a bounded read-only blocker sampler;
it does not install a trace, change server settings or grant permissions.

## Verification and deployment

Automated gates include native two-connection interleavings on unique local temp
tables, exact receipt/fence rejection, timeout/deadlock classification, cleanup
acknowledgement failure, commit uncertainty, restart re-entry, external cursor
exclusion, complete authority observation coverage and monitor progress/stall
semantics. Full bot regression, architecture, deferred, security-routing, imports,
command registration, SQL validation and exact Changes security review are required.
Validation counts and final PR heads are recorded in the release handoff.

This is a source-only bot release. The SQL companion is optional read-only
diagnostics; there is no migration or reconcile apply to run. The protected updater
must first receive the reviewed checkpoint_observation_lifecycle_v1 transition.
Its sixteen runtime members are indivisible and pinned to predecessor/successor bytes;
target code cannot authorize its own installation. Use the release package's
verified installer hashes and compatibility result against the installed private
commit, then the usual Update-K98.ps1 and requested /ops graceful_restart flow.

After deployment:

1. Verify the updater's exact target, completed stages and Discord readiness.
   A fresh-import/export-evidence warning alone does not establish feature failure.
2. Perform one normally intended import/export sequence. Do not repeat previously
   completed work solely to test retries or deliberately create contention.
3. Check exact SQL completion and capture receipts, followed by export confirmation.
   Recovered checkpoint logs should say recovered/completed with import_replayed=false.
4. During active work, recovery may say waiting. Let the next automatic check run.
   Confirm no stale pending health preparation is left after cleanup, and that
   genuine unresolved outcomes remain retained rather than silently cleared.
5. Inspect the monitor: progressing/waiting can coexist with older completed-check
   evidence. A failed check, stalled cycle or repeated exhausted checkpoint needs
   investigation with the matching logs/report and optional SQL wait sample.
6. Confirm expected spreadsheet data visually where provider delivery acceptance
   requires it. Alliance Activity is complete when all supplied valid snapshot
   rows import; no comparison against another report's governor population applies.

Preserve the existing updater rollback/resume receipts; do not manually revert
live source or replay a producer. Previously reported MGE signup and unrelated
historical P0/P1 acceptance items remain separate.

## Deferred optimisation

### Deferred Optimisation
- Area: ExportResource ActivePreparationID lookup and recovery discovery
- Type: performance
- Description: Canonical schema lacks an ActivePreparationID index. Broad locked scans may increase brief contention; successful discovery cycles also exceed the old freshness interval. The correction removes observer waiting and separates progress from evidence age, but does not claim measured query-plan optimisation.
- Suggested Fix: Use bounded live index/wait observations and actual plan/row-count evidence to select a narrow index or discovery batching change if contention or latency persists.
- Impact: medium
- Risk: medium
- Dependencies: Measured production plan and row-count evidence; separate SQL schema contract and deployment review if an index is selected.
