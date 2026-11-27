# P02 D5c player reader-global acceptance and reader-account plan

## Accepted result

Receipt `d5c-player-reader-first-global-result-edac3b1e04bb438189cf45a5c43d92ef.json`
has SHA256 `2a2f4eda6a77f05c5142bd05ee2d8e55e217e1d6473a590d3a17d53a77325ce2`.
The actual player preparation snapshot preceded separate global-holder acquisition.
The inspector refused with exact ImportExecutionActive. Physical reader closure
preceded surviving-holder verification and release. Actor exit, independent SQL
absence, protected records/history/permissions, all eleven fixtures, removed
account absence and resources passed. No cancellation or recovery action ran.

Acceptance is `d5c-player-reader-first-global-acceptance.json`. The receipt used
47 operations/108 rows. Host time 2.1307209 seconds is charged as three, leaving
1,329 native seconds, including the protected 1,000-second later reserve.
Windows allowance remains 50 seconds, fixtures 11/64 and inputs 21 consumed.

## Final planned player lock order

Start actual PlayerReportRecoveryDAL.inspect for existing preparation
`b17c3d27-dff1-5a23-b164-418ca42c9360`, account `d5c_inspector_20261113`, storage
`d5c_qualification_only`, on disposable database `K98_P025_D5b_20261111`.
After its actual preparation fetch establishes the snapshot reader, the test-only
cursor hook acquires the existing account lock on a separate owned connection.
Require global availability followed by account unavailability and exact
ImportExecutionActive. Global contention cannot pass as the account-specific case.
Reader rollback, restored isolation and physical close must precede surviving
holder verification/release. Any cleanup uncertainty stops dependent work.

The accepted 21-module player bundle and authoritative ExportPreparation,
ExportResource and StatsImportExecution contracts are unchanged. All 21 metadata
statements, fixture predicates, expected preservation values, SQL source pins
and runtime bindings are identical. No production Bot or SQL source changes exist.
This is test tooling, not command/view business logic or deployment.

Reservation is exactly 48 operations: 21 metadata, six outer lifecycle/control,
21 actor, with maximum 112 rows under the unchanged 2,048 ceiling. Actor allowance
is ten SQL statements/seven rows. The final observer absence query reaches 48;
successful disposal/receipt creation requires no extra admission. Manifest size
129,235 bytes is within 131,072; actor size 17,971. The accepted bounded decoder,
65,536 encoded/327,680 expanded source limits, 60-second packet, 20-second actor
watchdog, 1 MiB receipt and all resource/process/VM/log/session/isolation gates stay.

No new row, input, import/replay, report production, maintenance, backup, provider
request, permission/setting change, cancellation or recovery action is included.
Only the exact owned actor may be stopped and joined on timeout. No SQL KILL,
unowned termination, automatic repeat, reset or evidence deletion is allowed.

## Validation and review

Nineteen Python tests and 293 PowerShell 5.1 checks passed on the first pass.
Coverage includes actual player inheritance, exact query ordering, cross-file
preparation identity, account-specific refusal, wrong scope, failed acquisition,
lost owner, cleanup uncertainty, native error cause, remoting, bounded decoder,
preservation and full actor/manifest/wrapper reproduction. Earlier packet failures
remain preserved; none were replayed.

Run architecture/deferred/security-routing validation and explicit test selection.
Broad pytest, smoke imports, Discord registration and deployment tests are skipped
because those runtime paths are unchanged and do not establish this schedule.
No new production refactor or deferred optimisation is introduced.

Security routing is Changes, Deep off, for the seven frozen files (actor, wrapper,
manifest, builder, two tests and this plan), plus supporting code. No SQL diff
exists. Complete independent review and pin checks before one console handoff.
Adjudicate the native receipt before dependent work; readiness is not acceptance.

This completes preparation of the planned player lock orders, not D5c as a whole.
D5c remains seven groups closed/five partial, with other inspector routes and
consistency/recovery/access cases outstanding. D5d faults, D5e balanced cost
comparisons and D5f final acceptance follow. D6 production deployment is separate
and unauthorized by this packet.
