# P02 D5c demand acceptance and worker/global deferrals - 2026-11-12

Status: approved generation-2 demand accepted; first two blocked-worker cases
prepared, passing 164 offline checks and completed Changes review. No worker has
run for this new demand; the five blocked calls and one actual-child allowance
remain unused. No new scope approval is needed for this packet.

## Accepted admission

Receipt `d5c-demand-admission-result-acf18dd1139c416e946ad3984589d04c.json`
matches SHA256 `0ADF27ECE02B107FD0ADDC7E17A6AC79695B9EC1DF64BFC8995971FCF572E888`.
Independent adjudication verified all 36 statements/109 returned rows, 44 command
units, durable host-history hash and guest acknowledgement, exact 19-field before
and after row, all 30 candidate fingerprints and paired protection/ownership/
permission/backup/resource/child-counter/statistics checks. Generation 2 is
pending with request `468fc60f-8424-4637-b576-99717c7ad062`, DueUTC
`2026-11-12 11:15:04.144`. Generation 1's claim, completion and first error 15247
are unchanged. The worker guard released to NoLock, both connections disposed
and the captured work-session birth was independently absent.

Full host elapsed 0.9978464 seconds debits one, leaving **1,461 native seconds**
(461 proposed D5c allocation plus the unchanged 1,000-second later reserve).
**21 inputs remain consumed; zero new inputs.** Create-new independent acceptance:
`.codex_artifacts/p025/d5c-demand-admission-acceptance.json`. Do not repeat admission.

## Next concrete packet

On the same isolated copy, hold `K98:post-import-stats:v1` Exclusive/Session on
one labelled test connection, then invoke unchanged `usp_RunMaintenance` once
with `@Kind='post_import'` on a separate, preflighted autocommit connection.
Require return without child entry. Before releasing the test holder, verify
all 19 pending-row fields unchanged, all five worker-owned guards NoLock,
transaction count zero, and identical post_import cache plan handle/birth,
last-execution time and execution count. Release the test holder once.

Repeat that fixed sequence once for `k98-legacy-output-snapshot`. The second
case cannot start if the first return, state, cache or release is uncertain.
The unchanged worker source establishes that these cases refuse at its first
and second guard respectively, before claim or child entry. Other five completed
rows and all original failures remain intact. No demand/reset, direct child,
backup/report/import/provider call, permission/isolation or VM change occurs.

These are two of the approved five blocked-worker calls. Delta/player and real
managed-reader/schema deferral, followed by the at-most-one actual child, remain
separate. This packet does not spend that actual-child allowance intentionally;
any contrary evidence stops the sequence and must be reconciled before proceeding.

## Design and bounds

The wrapper reuses the accepted metadata, target/resource, manifest/file and
PS5.1 remoting/closure gates. It reads the existing immutable host/Q history and
pins the admission receipt. It writes only a new packet intent/result. Two SQL
actors share a unique generated application identity. The observer is opened
after actor disposal, and checks both the exact work birth and absence of every
session bearing that application. The new holder handle is retained if worker
close is uncertain; neither owned release nor a failed close is retried. Worker
disposal precedes holder disposal on all exit paths. Unknown custody is retained
in the guest session and makes the packet incomplete.

Exactly 40 planned SQL statements plus eight reserved connection/control units
fit the unchanged 48-command ceiling. Maximum 126 returned rows; the child-cache
query selects TOP(5) with a four-row cap to refuse overflow rather than truncate.
Plan identity/cached time, not a counter alone, is compared before proceeding.
All original one-MiB receipt, 512/result/2,048-total rows, three-second statements,
30/42-second work/cleanup, 45+10-second outer stop/join and 60-second manual stop
limits remain. The original fixed VM/isolation and disk/log/version-store gates
remain. No Python/native process is launched. Two actors plus one observer is
the ceiling; the observer is normally sequential, not a fourth connection.

The first packet used one of the five proposed maintenance packets. This one
covers two guard cases, leaving the planned delta/player packet, schema packet
and one actual-child packet within that five-packet sequence. No native time
has been charged for source preparation.

Scope-specific metadata choices: retain all paired original protection, owner,
permission, six-row ledger, backup and resource checks; all 30 installed images,
full pending-row identity and six-child entry counters. Independent full-row and
post_import plan/counter checks run after each worker call before the next case.
File census, principal/object discovery and physical statistics are omitted here:
the accepted readiness/admission pins supply those preimages, no such setting
changes occur, and this packet must refuse before child entry. Full physical
statistics evidence remains required for the actual-child packet.

## Source validation, tests and review route

The SQL authority remains `C:\K98-bot-SQL-Server\sql_schema`: unchanged
`dbo.usp_RunMaintenance`, `dbo.MaintenanceWork` and `dbo.usp_MaintenancePostImport`
define guards, exact pending fields, dispatch and child ownership. The new cache
metadata uses the same existing `sys.dm_exec_procedure_stats` source with explicit
plan/cached-time identity. No SQL repository or Bot runtime change is made.
No new service/DAL framework, command/view logic or deferred refactor is needed.

The isolated PS5.1 validator passed 164 checks. It extracts only bounded functions
and uses fake actors; no SQL/VM/registry/history write runs. Cases cover both
successful deferrals, wrong holder identity, refused grant, unknown worker return,
generation/request/first-error drift, leaked guard/transaction, child entry,
cache eviction/missing cache, uncertain release, replay and worker/holder close
failure. Each failure blocks the second case; worker-close uncertainty retains
the holder. Complete manifest remoting and inherited statement/parameter equality
are checked. A first validator failure and source snapshot are preserved: a
generic DELETE check matched existing table-variable cleanup in the unchanged
metadata collector. The correction restricts the no-mutation check to new case
SQL and separately verifies all inherited collector bytes/parameters unchanged.
No execution control or limit was weakened.

Security route: Changes, Deep off, four new files against the reviewed admission
snapshot: wrapper, validator, manifest and this document. Include independent
wrapper/validator review and authoritative SQL context; no full repository audit.
Architecture/deferred/routing checks and explicit-path test selection apply.
Full pytest/application smoke/command registration/native release suites are
skipped for this bounded qualification packet; they would bootstrap unrelated
application/native fixtures. No deployment action or promotion check is involved.

After completed review, run the hash-pinned packet once in the existing elevated
PS5.1 console. On any failure/incomplete result preserve it and do not retry,
reset pending work, delete history or advance to another case. Independently
adjudicate the full receipt before preparing the next native handoff.

## Completed review and handoff

Changes scan `e086bdcc-7012-48c4-9e31-43e17e63fb85` completed with zero findings
and all four files covered, including independent full wrapper/validator review.
Immutable range `2d0e0f4a8acf85410c3cc236ca5106245296371a` to
`c876d4037a77cee57560e70f234b3e7362a9a152`; Deep off. The final draft save was
verified before completion and the sealed completed coverage was read back.
Measured usage: 2,106,749 total tokens, including 2,096,384 cached input tokens.

Architecture (zero changed Python files), deferred (one Markdown file), routing
(zero errors/warnings), explicit-path test selection and snapshot whitespace
checks passed. Suggested application/full/native suites are skipped for the
bounded reasons above. All four files matched the reviewed snapshot before this
status-only addition. No execution intent or result existed at handoff.

Inherited manifest descriptive `metadataScope`/driver-readiness text remains
historical provenance; the current `status`, `blocked`, `qualificationScope`,
actual 40-statement ledger and this packet define the execution. No Python actor
or read-only-only assertion is made about these two actual worker calls.

Final script SHA256:
`05CC42146D4F3613FF04789F4B558E52FFB15A46665AB7EA7D0AFF8D343E0CB2`.
Manifest SHA256:
`f2bc2bc05f3826bf225ea2b53615b38ffde6020a13eaa7f2171d947af7556a3d`.

Run once in the existing D5bReports console, retain full outer host elapsed time,
and adjudicate before further native work. This status-only review record changes
no executable or security boundary and needs no second Changes scan.
