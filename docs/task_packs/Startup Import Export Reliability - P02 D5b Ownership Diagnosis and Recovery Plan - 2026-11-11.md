# P02 D5b ownership diagnosis and recovery plan — 2026-11-11

Status: diagnosis complete; **ownership alignment and one targeted retry require
operator approval**. No ownership, permission, procedure or ledger change has
been made by this review. D5b remains incomplete; reports are still outstanding.

**Later checkpoint:** the operator explicitly approved ownership alignment and
one targeted retry. The bounded packet below is now prepared, tested and reviewed;
native execution is pending. Earlier approval-required wording is retained as the
decision history, not a second approval requirement.

## Adjudicated result

Diagnostic receipt `d5b-failure-observation-result-a089921e02f74641ae5dc92cd1c15dc8.json`
has SHA-256 `bfd4cf94a8a1bdd100e60a07e4954baa2c4a1d53861d3796f33a583df5534674`.
The original failure remains byte-identical at SHA-256
`e92dc35bcfcdc82748e7aa603164953b32fa22d717b9de3e521d5086b8803462`.
A separate private adjudication records the comparisons without rewriting either.

- Import, configuration, player_report, kvk_output and final_stats each have a
  distinct completed generation-1 claim with no recorded error. All six children
  have one observed cached procedure entry; entry alone is not completion.
- Seven physical target statistics advanced within the recorded work period.
  Their data row counts remain unchanged. Configuration completed all 415 rows
  at scan 1245 and added exactly one DeltaProcessingLog row (544 to 545).
- KVK16 completed for the original object ID 2072823638/header revision 538.
- Post_import remains failed: due 1, completed 0, claimed 1, claim
  `3cc4e222-9a32-43c6-8a58-f3aafa249c5b`, first/last error **15247**, first error
  UTC `2026-11-11T17:55:28.565Z`. DeltaProcessingLog statistics did not advance.
- Final-summary completion is 1 while backup requested generation remains 0.
  Latent backup demand remains outstanding; no backup dispatch/completion is claimed.
- Original database protection is unchanged before/after. No other copy user
  session or application lock was observed. The diagnostic work connection was
  disposed, exact session absence verified, and its observer disposed.
- The read-only diagnostic used 24 commands, 38 rows and 1.0425934 seconds.
  Conservative native allowance is now **1526 seconds**. All 21 inputs remain
  consumed; zero additional inputs were accessed/consumed by this diagnostic.

## Cause and confidence

The copy's `sys.databases.owner_sid` resolves to the existing Windows login
`MINI_AMD\K98LabAdmin`, SID
`010500000000000515000000CFC07A55BB14094237A8F0CFE9030000`.
Its restored `dbo` database principal still has SID `01`.
The unchanged `usp_MaintenancePostImport` executes as owner, resolves to dbo/SID01,
and calls `sys.sp_updatestats` after all five application-lock checks.

The installed system-procedure definition checks effective sysadmin status or
equality between `SUSER_SID()` and the database owner SID (with a separate Azure
edition exception). Its explicit error 15247 is raised before the statistics
cursor and any UPDATE STATISTICS statement. This matches the observed mismatch,
failed claim and unchanged DeltaProcessingLog statistics. The failing session's
impersonated token was not captured directly; the conclusion combines the
installed code, ownership metadata and recorded failure rather than claiming a
new impersonation experiment.

Both candidate procedure bodies match authoritative SQL source after declaration
normalization. This establishes a restored-copy ownership inconsistency, not a
reason to remove EXECUTE AS OWNER or weaken the candidate's production guards.
Production ownership/effective-permission qualification remains separate.

Microsoft's [restored-database ownership example](https://learn.microsoft.com/en-us/sql/relational-databases/errors-events/mssqlserver-15517-database-engine-error?view=sql-server-ver17)
shows that restoring under a different login can leave the two ownership records
different, and reasserting authorization to the current valid owner updates dbo.
That article illustrates error 15517; this run's actual error is 15247, whose
specific gate is established by the captured system definition. The proposed
[ALTER AUTHORIZATION operation](https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-authorization-transact-sql?view=sql-server-ver17)
targets the database only, not schemas, objects, users or server roles.

## Exact proposed recovery scope

Only after approval, prepare and review a separate hash-pinned operator packet.
The following is a reviewable operation plan, **not a command to run manually**.

1. Bind both receipts above, current installation/manifest pins, exact isolated
   VM/session/Q volume, copy ID8/create time/files/settings, all 30 candidate
   structural postimages and existing owner SID. Require the same five completed
   claims and exact failed post_import claim/generation/error. Require no other
   copy session, unchanged source protection and existing resource headroom.
   Preserve every original receipt and create exclusive new intent/result records.
2. Reassert the copy's existing database owner with exactly:
   `ALTER AUTHORIZATION ON DATABASE::[K98_P025_D5b_20261111] TO [MINI_AMD\K98LabAdmin];`
   First verify that this exact existing login resolves to the pinned Windows SID.
   No principal selection fallback, new account or server role/grant is allowed.
   This repairs dbo's SID to the already-recorded owner; it does not select a new
   database owner. Nevertheless it changes the security context used by owner
   modules, so it is an explicit exception to the unchanged-ownership boundary.
3. Verify database owner SID remains the pinned Windows SID and dbo now matches
   it; database settings, module bodies, explicit permissions and source protection
   remain unchanged. TRUSTWORTHY and database chaining remain off. A bounded
   metadata-only owner-context probe may use EXECUTE AS USER=dbo and REVERT on a
   separately owned connection to prove the captured permission predicate; no
   maintenance/system procedure executes in that probe. Verify physical closure.
   Any mismatch stops before requeue. Do not automatically reverse/repeat a repair
   whose result is uncertain.
4. Under the existing release/maintenance/publication guards, revalidate the
   failed claim and all five completed claims. In one short transaction, change
   **only State from failed to pending on the exact post_import row**, with a
   compare-and-set predicate on claim ID, due=1/completed=0/claimed=1,
   first/last error15247 and first-error timestamp. Require exactly one affected
   row. Preserve FirstErrorNumber, FirstErrorUTC, LastErrorNumber, generations,
   request provenance and old claim until the real worker replaces its claim.
   No Due call or new generation, no clear/reset of the ledger, and no edit to
   any completed child. This is a labelled lab recovery adapter, not a production
   recovery API. The worker intentionally does not retry failed rows automatically.
5. Release and acknowledge all fixture guards, then invoke unchanged
   `usp_RunMaintenance @Kind='post_import'` **once**. Do not invoke the other five
   kinds or original six-child packet. Stop after any error/uncertain outcome.
6. Require completed generation1 and a new actual claim, LastErrorNumber NULL,
   **original FirstErrorNumber15247/FirstErrorUTC retained**, newer physical
   DeltaProcessingLog statistics with row count still545, unchanged five completed
   claims and unchanged backup demand. Require source protection and owned SQL
   closure. Preserve both the failed and recovered outcomes; never rewrite the
   first attempt as successful. Cached entry counts supplement these durable and
   physical observations; do not rely on cache retention alone.
7. Adjudicate before continuing the already-approved 42-state/14-export report
   recomputation and independent numeric/name/clock checks. No import replay or
   new input is permitted. Full D5b closeout remains contingent on those results.

This exception requests only the copy's ownership alignment and the single
reviewed failed-child recovery. No production/source database change, procedure
correction, privilege grant, new VM resources, backup dispatch, deletion or
recreation is included. All existing limits remain: 1526 seconds remaining, at
most 300 seconds per recovery packet, bounded work commands inside that envelope,
metadata three seconds/zero lock wait, 48 commands/2048 rows/1 MiB receipt,
8 GiB disk reserves, version store below512MiB, optional-work log below70%,
4 CPU/fixed8GiB/zero adapters and the consumed21-input allowance. Preparation must
prove the precise statement/receipt budget before issuing a native packet.

## Validation and approval boundary

This review changed documentation and separate private adjudication only. Python
locally verified both receipt hashes, five exact completed claims, the failed
claim, source protection, cleanup, seven statistics advances/unchanged data counts,
one upkeep log row, unchanged post-import target statistics, system gate ordering
and the two candidate bodies against authoritative source. No native call ran.
Security routing for this documentary delta is a precise skip; the eventual
ownership/recovery executable must receive its own Changes review and inert
negative tests before execution. Required negative cases include changed SID,
claim/generation/error, altered completed rows, non-acknowledged release,
post-repair mismatch, rejected requeue, failed retry and uncertain cleanup.

Approval is required because prior native D5b authorization excluded permission
changes and the diagnostic handoff explicitly promised findings before ownership
change or workload retry. Existing authorization still covers report preparation;
it does not silently authorize this newly identified recovery exception.

## Approved execution packet

- `scripts/recover_p02_d5b_post_import.ps1`, SHA-256
  `dea93228eba597588f89a8229f8fc7c5c2d1e00764f155f2cd057bee24140388`.
- `.codex_artifacts/p025/d5b-recovery-manifest.json`, SHA-256
  `d94c1611fdd0b9e1afbfb69a8e2b7c32fed3a017aae95ea17fad834e9fd6a10c`.
- `tests/validate_p02_d5b_recovery.ps1`, SHA-256
  `9f6d2797cf7ac535c1f2f3f732c847c8c4133394b9ae654083be3d0d7d2f498d`.

The packet implements the approved plan with 34 client commands including closure.
Explicit permissions are bounded at512 rows per observation, with a513th sentinel
causing refusal before ownership change. Their before/after hashes must match.
The optional impersonation probe is omitted: exact matching SID readback and the
unchanged real child establish the intended gate without an extra security-context
probe. There are exactly three work calls: owner alignment, exact CAS re-admission,
and one post_import worker. All existing bounds remain, starting at1526 seconds.
The exact Q intent path is CreateNew and no original marker is changed/deleted.

Actual PS5.1 inert tests pass identity/visibility/budget/image refusal; changed
failed-claim fields; preserved first-error/new-claim completion; changed completed
claim refusal; SID/owner/trust/chaining checks; physical refresh/no extra log-row
checks; exact three-work-call/rooted-marker assertions; and pending/fault/settled
async cleanup-owner tests. Routing and whitespace checks pass. All11 prior source
files remain byte-identical to their reviewed pins.

Independent review found no security or correctness blocker. Changes review
`f82bfad0-1b3a-46cd-9737-81b0b1a8ba1f` completed with zero reportable findings,
Deep off, all12 source inventory files accounted for. Snapshot
`b06caee023315ec125c357d5f7891db115ec578fe3f202330b1c9cec76b895c9`.
Findings SHA-256 `e1ab0656b90da98eda01a0ebc9ccebac09af7f73c92529bb942e9502ea0458ed`;
coverage SHA-256 `16248b61e9993dd732be3d815b5365b457fc658a194ce1905bf323425fc75e2d`.
Adjudicate the native result before the already-approved report/oracle work.

## Pre-work refusal and corrected V2 packet

The first recovery attempt stopped at the explicit-permission export cap, before
owner alignment, re-admission or the child retry. Preserve its source, manifest
and receipt `d5b-recovery-result-3a04905536ee42abbc32163a81ee7258.json`, SHA-256
`ecc340a3001de2218cd7b223ffa3139cb8307ef73458412f2af3efc256d4b578`.
The receipt contains zero work steps, no last action, unchanged mismatched owner
metadata and verified work-session absence/observer disposal. Its separate
adjudication records 1525 native seconds remaining. The approved actual retry
remains unused; no additional approval is needed for this metadata correction.

V2 keeps the complete permission representation inside SQL and returns one row
containing count, canonical byte length and SHA-256. All permission rows are
included in deterministic order; there is no TOP truncation. A 512 KiB canonical
byte ceiling and exact before/after comparison fail closed. This changes neither
the returned-row allowance nor the 48-command, 2048-total-row, 1 MiB receipt or
time/resource limits. The same three mutations, six guards, exact failed claim,
five completed rows, first-error history and exclusive guest intent are preserved.

- Source: `scripts/recover_p02_d5b_post_import_v2.ps1`, SHA-256
  `9af95de3ebed086b13caa4996ba65a2697992a75588ef402d0611b5cd8d7a7f4`.
- Manifest: `.codex_artifacts/p025/d5b-recovery-v2-manifest.json`, SHA-256
  `0ae5b0e0211d495932b54e3fe5a81a4c3e7f1f18c5b30121797782425fd8646f`.
- Test: `tests/validate_p02_d5b_recovery_v2.ps1`, SHA-256
  `94a85ebdf8a4286292344e56a99b2739bf89dab453db3d36e2c7c4a3ab88b3e8`.

PS5.1 inert tests passed, including over-512 permission counts represented by one
fingerprint, malformed/oversized fingerprint refusal, original claim/identity
checks and exact-source asynchronous cancellation/cleanup tests. Routing and
whitespace checks passed. Broader Python suite and PR architecture/deferred/test
selection gates are skipped here: no Python/runtime change or PR handoff; this
bounded correction is covered by its PS5.1 tests and source/SQL review.

Independent review found no blocker. Changes scan
`f2b89ce1-d269-4412-8a3d-a5b097d9be75` completed with zero reportable findings,
Deep off, all 13 source inventory files accounted for. The prior 12 source hashes
remain unchanged. Snapshot
`07dedd093fc81f7c0de16d7b8409b8d5be7f10a661ae5262194bffb30cfdd1cf`;
findings SHA-256 `64e3ce3b5461d4da05fc63f972f64d8f237d017a0788194a47fb1f753bf52887`;
coverage SHA-256 `87e24249cfc6b7cf974549bf0551ffc4e9012b685dd5a35ef8364771be17379f`.
V2 native execution remains pending; adjudicate it before report execution.

## V2 result and read-only session observation

V2 subsequently ran and stopped. Preserve receipt
`d5b-recovery-v2-result-a4efb435bbbc4ebc9cad74214917ae82.json`, SHA-256
`e80420ceb0c1b6158751333dc1bdb6f046f41d36fc2b0f6f6095d536d4d73fcb`.
The owner-alignment command returned successfully and dbo matched the existing
Windows owner on readback. All 799 explicit permissions had unchanged count,
38,472 canonical bytes and SHA-256
`3a1048abe7ef3e76fe49b05a4de65970aabc86d2470c450f4ab8ea741dc85301`.
All 30 candidate postimages also remained unchanged.

The re-admission command then raised SQL 52991, line 1, `Wrong recovery session.`
This is its first guard, before BEGIN TRANSACTION or UPDATE. No re-admission
mutation or post_import retry was reached. The guard combines database identity,
@@TRANCOUNT and XACT_STATE; the receipt does not identify which operand refused.
Do not assume the cause or relax/remove that guard. The earlier ownership
readback is not yet independent proof of durable ownership after session closure.
Work disposal, exact session absence and observer disposal passed. Elapsed time
was 2.1163637 seconds, 23 commands/92 rows; 1522 native seconds remain. The
exclusive recovery intent now exists and must not be deleted or bypassed by
rerunning V1/V2. All original receipts and scripts remain unchanged.

The next packet is read-only:

- `scripts/collect_p02_d5b_session_observation.ps1`, SHA-256
  `52a57e30eb333b8598cda06608b0ed3be8f7b2a07c402800882aec8427cce7cc`.
- `.codex_artifacts/p025/d5b-session-observation-manifest.json`, SHA-256
  `b08e0b63c2168d2a30d0bc1d3aef18d8985bae5f0b49d5075ef1bde92db20ca7`.
- `tests/validate_p02_d5b_session_observation.ps1`, SHA-256
  `503862558bad45e58443f5a343a04be8d00076e3f78840817bd27838359b36cb`.

It reads current ownership, six claims, physical statistics, backup demand,
bounded session/lock metadata and server user options. It captures fresh session
DB/transaction/options before configuring the same options as V2, then observes
the exact first guard inside TRY/CATCH, without any re-admission SQL. It repeats
the already-reviewed canonical metadata query into local table variables and the
complete permission fingerprint, with guard observations before/after. No change
to ownership, permissions, business data, work state or inputs occurs. Other copy
sessions stop the reproduction. The existing command/row/receipt/time/resource
limits and consumed 21-input allowance remain; success uses 29 client commands
including closure. The result requires adjudication before any continuation.

Microsoft's [implicit transaction documentation](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-implicit-transactions-transact-sql?view=sql-server-ver17)
describes why transaction mode is relevant to metadata reads and provides the
@@OPTIONS bit check. This is a diagnostic hypothesis, not evidence that implicit
transactions caused this failure. Native observation must establish the facts.

Actual PS5.1 inert tests, routing and whitespace checks passed. Independent review
found no blocker. Broader Python tests and PR-only architecture/deferred/test
selection gates remain inapplicable to this standalone PS observer handoff.
Changes scan `44f22085-37a8-47ce-bdde-4a56f1c90d56` completed with zero findings,
Deep off, all 14 source inventory files accounted for; prior 13 hashes unchanged.
Snapshot `6b54aa0e4d7030a04bee6ecf859dac52ba01b63aa709ceb996571ab01c782f1f`;
findings SHA-256 `7a9591a5565122845282e1361209834b9c8a32a46d102c2ae04622496c31b47d`;
coverage SHA-256 `9de407e49bd6892a964481f8896ecfdda39280dd412ba525ef6fb9f752578c1b`.
No native observation has run during preparation; D5b remains incomplete.

## Session result and remaining approved retry

The diagnostic subsequently completed: receipt
`d5b-session-observation-result-433a9da3547e46088d9ff2e907e9b977.json`, SHA-256
`17f74c8268eec091c9dcb94e1f6d30cf95d459f0276b961303bcaed1c810b278`.
Independent fresh-session ownership matches the existing Windows owner, proving
the alignment persisted. All 799 explicit permissions retain the prior digest;
all observed claim fields, physical statistics and backup demand match V2's
pre-requeue observations. No foreign copy sessions or application locks were
observed. Five claims remain complete; the same post_import claim remains failed,
with original error 15247 and unchanged timestamp. No child retry occurred.
Work-session absence and observer disposal passed. Native budget is now 1521
seconds; the original input allowance remains consumed at 21.

Every session observation showed exact copy DB_NAME, @@TRANCOUNT=0, implicit
transactions off and XACT_STATE=1, including the fresh connection before metadata.
The original guard refused before and after metadata reproduction. Thus the
refusal is specifically the lab adapter's XACT_STATE<>0 condition, not evidence
of a wrong database or metadata-created explicit transaction. We do not infer a
general SQL Server defect or claim that XACT_STATE universally behaves this way.
Authoritative `dbo.usp_RunMaintenance` line 11 and
`dbo.usp_MaintenancePostImport` line 10 require @@TRANCOUNT=0 and implicit mode off;
their production guards remain unchanged.

The continuation plan, within the existing approval, is:

1. Revalidate exact copy, source protection, resource limits, candidate images,
   already-aligned owner, pinned full permission fingerprint and exact failed
   claim/five completed claims. Capture DB/transaction/options explicitly.
2. Read and verify the existing recovery intent from V2 run
   `c5ed458a563b44f9933638ef98fa0211`; preserve it. Create a separate exclusive
   `Q:\D5b-20261111\post-import-continuation-intent.json`. Repeat no ownership change.
3. Under all six original guards, require the production autocommit entry
   conditions and reject a doomed XACT_STATE=-1. Run the exact same failed-row CAS
   inside an owned transaction; require depth 1 and committable state before UPDATE,
   exactly one row affected, and zero depth after COMMIT. Preserve original error,
   request, generations and completed claims. Roll back only when a transaction
   remains open; never commit an inherited transaction.
4. Recheck autocommit state, release/acknowledge all fixture guards and invoke
   unchanged post_import once. Verify new completion claim with first error
   preserved, unchanged five completed rows, newer DeltaProcessingLog statistics
   with 545 rows, unchanged backup demand/source protection and physical closure.
5. Adjudicate before the outstanding report/oracle work. Stop on any uncertainty;
   neither the old recovery script nor this continuation is automatically rerun.

Prepared `scripts/resume_p02_d5b_post_import.ps1`, SHA-256
`578a4fb71d5e61ad1f064ded9e95e199e91008d2a0174e4bb5dcce187bfa9b9f`;
manifest `.codex_artifacts/p025/d5b-continuation-manifest.json`, SHA-256
`063e2f01f4bdb07c4140d589533dcc6a6b148da51219534f6703d0155fb603ec`;
test `tests/validate_p02_d5b_continuation.ps1`, SHA-256
`f0d8b97dac39c763688449b02653129569e91fe501b4c1a36ce1c5495d76163d`.
There are two work calls and 36 client commands including closure, within the
unchanged 48/2048/1 MiB/300-second packet limits. Actual PS5.1 inert tests passed,
including active/implicit/doomed/missing state rejection, observed autocommit-state
acceptance, exact prior-intent rejection cases, claim/history/physical checks and
exact-source faulted/pending/settled cleanup ownership tests. No native execution
has occurred during preparation. Independent review is recorded below when sealed.

Independent review found no blocker. Changes scan
`d4f83259-411c-4ab0-8827-fae4c62ae91d` completed with zero findings, Deep off,
all 15 source inventory files accounted for and prior 14 source hashes unchanged.
Snapshot `3d9d4fbbb8b9177e29616826e0ca5cb0d3eac47a9ce26207f061ccab94f28dce`;
findings SHA-256 `42c2adace343400fa7aadfc46bec9c59ba8e0069d04178364c085abc82d15cf0`;
coverage SHA-256 `7a73fc97e912a61751ac40122f7faf35453293f4c1fc6ab99dd3a9b5bc04b220`.
Routing and whitespace checks passed. Broader Python and PR-only gates remain
skipped for this bounded PS/SQL lab adapter; production code and SQL repo were not
changed. Existing approval covers the remaining single actual retry. Operator
execution and receipt adjudication remain necessary; no D5b completion is claimed.

## Successful continuation and console closure

The continuation completed before the reported console closure. Host receipt
`d5b-continuation-result-715c675f474c4d2aae0517dbfacf4f10.json`, SHA-256
`dbfc23fb7687ed4cd5952a1d9fd31ac4e5b6382710fdeb96bf5348cf8ac7601b`,
was saved at 19:26:11 UTC. Exact script/manifest hashes match the reviewed packet.
Both work calls completed; no errors, 7.1891456 seconds, 36 commands and 119 rows.
The approved actual retry is now consumed and must not be repeated.

Post_import completed generation 1 with new claim
`3e723a45-4471-424c-aacf-f0afeb85c748`; original FirstErrorNumber 15247 and
FirstErrorUTC 2026-11-11 17:55:28.565 remain unchanged, LastErrorNumber is NULL.
All five previously completed rows are byte-equivalent as parsed to their
pre-continuation rows. DeltaProcessingLog statistics advanced to 19:26:06.370 UTC,
with row count still 545; all eight observed data row counts remain unchanged.
Thirty candidate images, aligned ownership and all 799 explicit permissions
passed verification. Backup demand remains outstanding and was not dispatched.
Original source protection, VM isolation, owned work-session absence and observer
disposal passed. Remaining native allowance is 1513 seconds; 21 inputs remain
consumed. The six-child maintenance portion is qualified with the original
failure retained separately; report/oracle qualification is still outstanding.

Host-only adjudication is saved beside the receipt. The adjudicator initially
expected ISO dates, then was corrected to validate the receipt's original PS5.1
`/Date(milliseconds)/` representation; no native operation was repeated or receipt
rewritten. All assertions then passed.

Windows Application event 1001 at 19:26:53.588 UTC reports AppHangB1 for
`conhost.exe`, report ID `628005bb-d9da-47be-8c20-c7801690b3b0`. This is evidence
of a console-host hang after the successful receipt, not proof of its underlying
cause or which interaction triggered it. A bounded recent System log lookup found
no matching restart/shutdown event. No PowerShell 5.1 process was present in the
subsequent process check. The continuation source contains no console/process
termination command. Do not rerun maintenance or reuse the old session identity;
re-establish and verify an authenticated elevated console for the next reviewed
report packet. No additional SQL/VM operation was performed during this check.
