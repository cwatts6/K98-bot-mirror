# P02 D5c delta/player acceptance and schema worker packet

Status: delta/player native deferrals accepted. The fifth approved blocked call
is ready with five offline Python tests, 132 PowerShell checks and completed
Changes review. No runtime correction or new
scope approval is needed. D5c and later D5 slices remain incomplete.

## Accepted evidence and balance

Receipt `d5c-delta-player-blocked-result-6f8df59b68c840a4b1e847c3c77a9cdc.json`
matches SHA256 `DEA760F0AF54B109530B5947D2B8B850471FF707E3B3D94A9D8C41214EB87C90`.
Independent adjudication verified all 40 observations, 82 rows, 48 command units,
both held-first actual-worker deferrals, exact 19-field pending row and all five
worker guards NoLock/zero transaction. Candidate images, first error 15247,
other completed jobs, backup, permissions, ownership, resources and stable child
cache/counters remained intact. All actors disposed and their exact births or
unique application identities were independently absent. Session ID reuse by
the closure observer was distinguished by its different login/connection birth.

Acceptance: `.codex_artifacts/p025/d5c-delta-player-blocked-acceptance.json`.
Full host elapsed 0.8764621 seconds debits one, leaving **1,459 native seconds**,
including the unchanged 1,000-second later reserve. **21 inputs are consumed**;
zero new inputs. Four of five blocked calls are complete. The single actual
child allowance remains unused. Preserve all original receipts and intents.

## Fifth blocked call

Use the existing isolated copy and generation-2 request
`468fc60f-8424-4637-b576-99717c7ad062`. The unchanged real managed reader takes
its Shared/Transaction schema guard. Require SNAPSHOT enabled, transaction and
isolation state correct, and exact reader birth distinct from the test worker.
Invoke unchanged `dbo.usp_RunMaintenance @Kind='post_import'` exactly once on
the second actor. Require no result and no change to all 19 pending fields,
post_import plan handle/cache birth/last execution/count, all five worker guards
NoLock and transaction count zero. Close the worker connection before the reader
releases its shared guard. Then require acknowledged reader rollback, restored
isolation, cursor/connection closure and clear custody. No subsequent worker
acquisition, demand, reset or actual child is included.

The pinned child uses the existing verified Python/pyodbc files and the same six
source modules as accepted reader packets. It loads no application startup,
provider or producer. The outer metadata connection remains open during the
two child actors: three simultaneous connections maximum. The closure observer
opens only after those actors and the outer work connection are disposed.

On worker close uncertainty, retain the first error in a bounded incomplete
stdout record, then exit the owned child without unwinding the reader early.
No success is inferred from process exit. The wrapper retains the incomplete
record, independently observes unique application sessions and stops. It never
retries the worker or an unknown close. Reader cleanup uncertainty also fails.
Timeout termination applies only to the owned process, with a bounded join and
retained process handle if closure cannot be confirmed. No foreign KILL/reset.

## Bounds and metadata consolidation

Keep 24 wrapper SQL statements plus a reserved 24 command units for the actor
and connection/control path: three reader statements, four worker statements,
seven reader transaction/isolation controls, eight open/close units across the
four total connections and two cancellation reserves. Total ceiling remains 48.
Cursor object disposal is not an additional SQL command. Reserve the entire
actor allowance before starting it, including missing/failed receipts.

The wrapper combines the existing database identity and session-birth fields in
one observation and combines log/version-store values in one observation at
each boundary. It adds all 30 candidate images and paired six-child counters.
Every former protection/ownership/permission/ledger/backup/resource/session
check remains. Exact full pending/cache checks occur inside the child before
and after its sole worker call. SNAPSHOT enablement and shared guard/context are
read together inside the managed context. These are bounded query combinations,
not waived checks or raised limits.

Maximum 115 returned rows including the 12-row actor reserve; 512/result and
2,048 total absolute limits remain. One-MiB receipt; three-second statements,
zero lock wait, 20-second child watchdog, 30-second work/42-second cleanup,
45+10-second host stop/join and 60-second manual stop remain. Fixed VM/resources,
eight-GiB C:/Q: reserves, log below70percent and version store below512MiB remain.
This is packet four of the approved five maintenance packets. One actual-child
packet remains available only after adjudication; overlap is not yet proved.

## Scope, SQL validation and tests

All new files are test orchestration, tests and qualification artifacts. Existing
reader helpers and candidate procedures are unchanged. Worker guard order and
19-column schema were checked against authoritative SQL definitions in
`C:\K98-bot-SQL-Server\sql_schema\dbo.usp_RunMaintenance.StoredProcedure.sql`
and `dbo.MaintenanceWork.Table.sql`. No command/view/DAL runtime changes,
permissions, deployment, import/export, backup dispatch or synthetic rows.
Reuse existing isolated-reader wrapper and source bundle; preserve old packets
as evidence rather than refactor historical versions. No new deferred item.

Five isolated Python tests cover success, preflight refusal, wrong schema/isolation,
row overflow, worker/error/result/poststate failures, no retry, worker-before-reader
closure and unknown worker/reader close. They use the actual unchanged helper
bundle with fake connections; no SQL, VM, native extension or child process.
The 132 PS5.1 checks cover parsing, remoting/list shape, manifest/source hashes,
budget/row overflow, identity, fixed registry reads, merged metadata fields,
single invocation boundary, cleanup and positive/negative child receipts.

The first PowerShell check caught case-insensitive duplicate manifest keys
`maxSQLStatements`/`maxSqlStatements`; the first manifest, wrapper and failed log
are preserved under `.codex_artifacts/p025/d5c-schema-worker-*first*` and
`d5c-schema-worker-powershell-offline.txt`. The correction retains only the
existing field name with seven SQL statements. Corrected log:
`d5c-schema-worker-powershell-corrected.txt`. No native attempt occurred.

Security decision: Changes, Deep off, six-file immutable delta based on
`9377de7dd2a08def407c1224313561ee4b21e964`: Python runner, PowerShell wrapper,
both tests, manifest and this plan. SQL access, embedded pinned source and owned
process/connection cleanup warrant review. No broad codebase audit. Run focused
architecture/deferred/routing/test-selection checks; skip full application and
historical native fixtures because they bootstrap unrelated or unauthorized work.
No deployment or production acceptance is claimed.

After completed review, hand off once to the same elevated console, capture full
host elapsed time, stop on any error/incomplete result and adjudicate all evidence
before further native work. No permission or setting change is included.

## Review correction before execution

Initial Changes scan `5b814bd7-86f8-478b-b56c-9124763b7e95`, base
`9377de7dd2a08def407c1224313561ee4b21e964` to
`43c1daff53f6dda2a6be7b9c422d6f204b87f04c`, completed with no security findings
and all six files covered. It identified a non-security correctness blocker:
unconfirmed outer SQL disposal could lose the handle and admit an observer while
an unjoined child still held two connections. Native handoff was held. Measured
usage: 1,872,919 total tokens, including 1,860,224 cached input tokens.

The corrected wrapper retains uncertain outer SQL ownership in the authenticated
session and refuses subsequent packets while it remains. It opens no observer
unless outer work disposal and any started child join are confirmed. Unconfirmed
cleanup remains incomplete, with no receipt-based success or retry. New injected
tests cover all work-close/process-join combinations and exact retained-handle
identity. The corrected suite passes 132 checks; Python/manifest bytes and all
limits remain unchanged. Pre-correction wrapper/validator copies and the original
review snapshot are preserved. The narrow correction requires completed Changes
review before handoff; no native attempt has occurred.

## Final handoff record

Correction scan `027aea58-970f-49ac-88d8-88dc6d019837` completed with zero findings
and all three changed files covered, base `43c1daff53f6dda2a6be7b9c422d6f204b87f04c`
to `16ff8f6dcf67c4fdcfae6d7c7c2745361d6d389d`, Deep off. Independent review
confirmed the prior correctness blocker resolved. Final draft saved before
completion; sealed completed findings/coverage read back. Measured usage:
1,735,834 total tokens, including 1,729,792 cached input tokens.

Architecture (two Python files), deferred documentation, security routing
(zero errors/warnings), explicit test selection and snapshot whitespace checks
passed. The broader suites remain skipped for the bounded reasons above.
Reviewed working files matched immutable snapshots before this status addition;
runner, manifest, approved source bundle, history hashes and all limits verified.
No native execution intent or result existed at handoff. Original branch/index
and unrelated runtime work remain unchanged.

Final wrapper SHA256:
`E43A18B3A9FFC40134D87784EDA6B69733F41AFD316406FF03B89D79F7584027`.
Manifest SHA256:
`54b869d8dccc30a68448080636deec67a617547f97dae18d5732e3b8a50a7920`.
Run once in the existing D5bReports console and retain full host elapsed time.
This status-only record changes no executable/security boundary and needs no
further Changes scan. Adjudication remains required before the actual-child step.
