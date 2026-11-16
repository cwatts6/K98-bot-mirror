# P02 D5c schema-worker acceptance and actual-worker packet

Status, 12 November 2026: the fifth blocked-worker receipt passed independent
adjudication. The one approved actual-child packet is prepared and has passed
offline checks; Changes review and native execution remain pending. No runtime
correction, additional native operation or deployment occurred in preparation.

## Accepted fifth result

Receipt `d5c-schema-worker-blocked-result-b95a2f17f5e349acb8867ac78c94790a.json`
matches SHA256 `7C9754383143C80454AB2941B78834CC074972914DF631EFDE71194641F0B087`.
The create-new acceptance record is
`.codex_artifacts/p025/d5c-schema-worker-blocked-acceptance.json`.
All 24 wrapper observations, source pins, paired state and resource checks passed.
The real managed reader held Shared/Transaction protection and SNAPSHOT isolation;
the actual worker returned once without entering its child. The full pending row,
old claim, first error 15247, all six child counters and five other completed jobs
remain unchanged. Worker close preceded reader rollback/release. PID 5608 joined
normally; both distinct SQL births and the outer work connection were independently
absent. The original history files remain hash-identical on host and guest.

Actual usage was 31 SQL statements/73 rows; reserved totals were 48 command units
and 80 rows. Full host time 1.9621169 seconds debits two. **1,457 native seconds
remain**, including 457 for D5c and the unchanged 1,000-second later-slice reserve.
**21 inputs remain consumed, zero new inputs. All five blocked calls are complete;
the single actual-child allowance is unused.**

## Scope and architecture

This implements only step 4/5 of the already-approved
[actual-worker plan](Startup%20Import%20Export%20Reliability%20-%20P02%20D5c%20Global%20Orders%20Acceptance%20and%20Actual%20Worker%20Plan%20-%202026-11-12.md).
Files are `scripts/run_p02_d5c_actual_worker.ps1`,
`scripts/p02_d5c_actual_worker_reader.py`, their two isolated tests and the private
`d5c-actual-worker-execution-packet.json`. Existing production helpers are embedded
unchanged with their six accepted hashes. No Bot runtime, SQL source, command,
view, permission, installation, ownership, database or VM setting changes occur.
No new request, import, report, backup dispatch, replay or reset is included.

The target remains the one disposable `K98_P025_D5b_20261111` copy on Q: in the
isolated MINI_AMD VM. The fixed request is
`468fc60f-8424-4637-b576-99717c7ad062`, DueGeneration 2, pending. Preflight requires
all 19 pending columns, the old claim, first-failure history, accepted child cache
identity/count, five completed rows, backup state, permissions, candidate images,
original read-only/restricted database and resource checks to match.

Authoritative SQL source was re-read in `C:\K98-bot-SQL-Server\sql_schema`:
`dbo.MaintenanceWork.Table.sql`, `dbo.usp_RunMaintenance.StoredProcedure.sql` and
`dbo.usp_MaintenancePostImport.StoredProcedure.sql`. The unchanged worker owns five
Session guards, generates the new claim, dispatches only post_import and updates
completion. The owner-executed child invokes `sys.sp_updatestats`. Direct child
calls and guard bypass are absent. No schema ambiguity is inferred from Python.

## One-attempt execution and evidence

1. Hash-pin the packet, preserve all prior receipts and require create-new intent.
   Verify the exact borrowed authenticated session and host/guest/volume identities.
2. Collect bounded preimages, including all six full maintenance rows and cache
   records, candidate fingerprints, ownership/permissions and eight table/statistic
   summaries. Missing/duplicate cache rows or any drift stop before the worker.
3. Open one phase observer. On the existing work connection launch exactly one
   asynchronous `ExecuteNonQueryAsync` for the fixed post_import worker. This uses
   the established D5b result-drain approach, without a direct child call.
4. Make exactly one scheduled phase observation. Match the worker session birth,
   connection ID, request and generation. Require running/new claim plus exact
   granted Exclusive/Session schema and global short-resource identities before
   any contender or fresh reader. Do not infer a long-resource holder from its
   truncated name, and do not poll SQL for a preferred phase.
5. If that phase is observed, issue one fixed batch of five zero-wait contenders.
   Preserve each original return. Release only an accidentally acquired owned
   guard, once. A grant means the window ended and that case is unexercised.
   Close the phase connection before the single real managed-reader attempt.
   Refusal must retain ObservationBusy/native 51966 and acknowledged rollback,
   isolation restoration and physical close. Safe late reader admission is
   explicitly unexercised, never a successful actual-worker overlap.
6. Join the one worker task, then require exactly generation 2 completed with a
   new claim, exactly one child counter increment under the same cache identity,
   original first error/time retained and five other full records/caches unchanged.
   The completed claim must match the phase claim when observed. Verify all five
   owned guards are NoLock, session options restored, resources and physical table
   counts preserved, statistic timestamps nondecreasing, and all owned actors absent.

No new data was introduced, so unchanged statistic timestamps may legitimately
mean no modified statistics needed updating. They are not fabricated into a
physical update claim: child execution and durable completion are separate proof.
The controlled worker may finish too quickly for overlap. That remains an open
qualification row; no artificial pause, second demand or rerun is authorized.

## Bounds and failure custody

The worst-case client ledger is exactly 48 units: 24 metadata statements, one
worker command, one phase statement, one five-resource contender batch, three
reader statements, seven reader transaction/isolation controls, eight open/close
operations for four sequentially used connections and three cancellation reserves.
Control/cancellation capacity is reserved before opening any connection; reader
SQL capacity is reserved before process admission. At most three SQL connections
can overlap. Rows are capped at 117 planned, 512 per result/2,048 total; receipt
one MiB. A batch counts as one client command, consistent with earlier packets.

Metadata statements retain three-second limits and zero lock wait. The actual
producer gets a reduced 20-second command ceiling, within its existing D5b budget;
there is no producer-timeout increase. Keep 30-second work/42-second cleanup,
45+10-second outer watchdog and manual stop before 60 seconds. All guest C:/Q:
eight-GiB reserves, log below 70%, version store below 512 MiB, fixed 8-GiB/four-CPU
zero-NIC VM and original 1,800-second rehearsal cap remain binding. Debit full
rounded-up host duration; do not refund refusals or failures.

Uncertain task cancellation, command disposal or connection close retains exact
handles in guest custody and blocks the final observer/new dependent work.
No foreign KILL, reset, release, deletion or second dispatch is used. The Python
watchdog/process join cannot substitute for acknowledged reader cleanup. A failed
or incomplete receipt stops for adjudication, preserving the create-new intent.

## Offline validation and review gate

Five isolated fake-driver tests passed with the unchanged managed helper bundle:
expected refusal, late admission, wrong identity, unknown cleanup and other busy
codes. 151 offline Windows PowerShell 5.1 checks passed: parser/remoting, row and
command ceilings, exact before/after work and cache records, first-error retention,
phase/contender race classification, reader evidence, resource registration,
physical-custody retention and final observer admission. No app bootstrap, native
extension, SQL, VM operation or child process was run by these tests.

Security decision: **Changes**, Deep off, exact Bot packet delta from prior sealed
review head `16ff8f6dcf67c4fdcfae6d7c7c2745361d6d389d`. SQL has no changed target.
Review is required for fixed SQL execution, local process/file handling and custody.
The test-only source and these docs are the complete intended diff. Architecture,
deferred/routing and explicit-path selector gates remain required. Full application
smoke/command-registration/native fixture suites are skipped because this packet
does not alter those surfaces and their startup/fixture mutations exceed its scope.
No justified new deferred refactor arose. Existing unrelated runtime changes remain
untouched. Offline checks alone never qualify actual overlap or authorize D6.

## Remaining programme position

D5a and D5b are accepted within their recorded evidence boundaries. D5c is still
in progress; this packet closes neither its other inspector/account/Windows/coherent
tuple cases nor an unobserved overlap. D5d failure/restart, D5e measured cost and
D5f final reconciliation remain. D6 is the separate production release decision;
D7/P05 live acceptance and the P03/P04 prerequisites remain explicit.

## Preparation accepted; one console handoff ready

Changes review `28c91f4e-b9b0-47e8-8191-a280a07b0cef` completed and sealed with
zero findings across all six changed paths. Range:
`16ff8f6dcf67c4fdcfae6d7c7c2745361d6d389d` to
`5970724300a6e2d662960e60966bd970e681306e`. Independent review also found no concrete
lab execution blocker. The private manifest was checked as hash-pinned supporting
evidence, not represented as a Git artifact. Completed canonical artifacts were
read back. Reported usage: 2,413,757 total tokens, 2,388,992 cached input tokens.
An unsupported draft metadata field was rejected before writing; it was removed
and the same draft/scan was finalized once. No packet source correction or native
attempt resulted from that review-record error.

All six paths matched the reviewed snapshot before this status-only appendix.
Architecture (two Python files), deferred (two Markdown files), routing (zero
errors/warnings), selector and snapshot whitespace checks passed. The five Python
tests and 151 PowerShell checks remain the final executable validation. The
selector's full app/native/release suites retain the skip rationale above.
This evidence-only appendix needs no additional security scan or runtime test.

Handoff pins:

- PowerShell SHA256: `E007AB79280F7F19A5CB4364EF679522695A76C609D430D1A622DF95DE2CC663`.
- Manifest SHA256: `282c82093a946dcccd8d710f1baff6716f4469be7da359b8f8f31dd56d9db867`.

Native intent was absent at final readiness verification. One manual invocation
is ready in the existing elevated console holding `$global:D5bReportSession`.
Stop on error/incomplete output, preserve the receipt, never rerun/reset, and
report full HostPacketElapsedSeconds. The native balance is still **1,457 seconds**,
with **21 inputs consumed**. Actual worker/overlap acceptance remains pending.
