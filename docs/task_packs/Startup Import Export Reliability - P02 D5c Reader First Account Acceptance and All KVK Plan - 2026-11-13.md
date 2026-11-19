# P02 D5c reader-first account acceptance and all-KVK plan

## Accepted account result

Receipt `d5c-stats-reader-first-account-result-2d5dc3d5183547eba8ac2cadd43d0b69.json`
has SHA256 `05b25a202bd62e6223835b42c5b2a097cee76cf70df43c0aef3c2db1ed0511dc`.
It is accepted. The actual Stats reader fetched its preparation before the
separate exact account owner acquired its lock. Global availability was one,
account availability zero, and the actual inspector refused with the expected
typed error. Reader rollback, isolation restoration and physical close preceded
verification of the still-exclusive holder and its own rollback/close.
Independent session absence, normal process exit and custody checks passed.

Protected records, original failure history, completed work, eleven fixtures,
permissions, ownership, candidate definitions and statistics remain unchanged.
Removed test accounts remain absent. The receipt contains 48 operations and 109
rows without errors. Acceptance is retained separately in
`d5c-stats-reader-first-account-acceptance.json`; the original receipt is immutable.
Host elapsed 1.3165563 seconds is charged as two seconds, leaving 1,349 native
seconds, including the protected 1,000-second later-phase reserve. Windows-test
allocation remains 50 seconds. Eleven of 64 synthetic rows and all 21 inputs
remain consumed. No accepted or failed old attempt becomes replayable.

## Next distinct all-KVK read

One fresh actual `AllKvkCaptureRecoveryDAL.inspect` reads the existing labelled
all-KVK preparation `9ceb4711-241b-52b8-aa42-16c43c0810ec`, account
`d5c_inspector_20261113`, storage `d5c_qualification_only`, season 20261113.
It must return the exact 21-column pending preparation, empty resources,
`captured=False`, action `hold`, and the explanation
`A committed producer checkpoint is required to finish capture.`
Its returned execution field is None by the actual all-KVK implementation;
this is NOT a database absence claim for StatsImportExecution, which this route
does not query. The evidence token must match its raw canonical snapshot.

The actual snapshot reader must observe the global and account locks available,
then acknowledge rollback, restored isolation and physical close. No exclusive
holder is introduced. Outer observations independently verify session absence,
fixture preservation and all existing protection gates. No recovery action is
executed: the returned action is evidence only. No input, import, report,
maintenance, backup, provider request, new row, permission or setting change.

The single disposable database and current D5cResume session remain pinned.
All 21 metadata statements and existing fixture checks are unchanged from the
accepted account packet. The actor uses 14 budget operations, six SQL statements
and four rows; total planned operations are 41 with at most 109 rows. Existing
48-operation, 2,048-row, 1 MiB receipt and 60-second packet ceilings remain.
The 20-second actor watchdog and outer cleanup limits remain unchanged. Failure
stops the packet; no automatic repeat, reset, forced termination or deletion.

## Preparation and review evidence

The bundle retains all 17 prior real modules unchanged and adds the full actual
all-KVK DAL as the eighteenth module. Expanded source is 239,281 bytes and the
compressed bundle 53,331 bytes, within unchanged 327,680/65,536-byte limits.
The manifest is 131,055 bytes within its unchanged 131,072-byte limit, with 35
lineage pins including the latest receipt and acceptance. The first offline
draft exceeded the manifest ceiling by 47 bytes and stopped before creating
packet files. Only explanatory prose was shortened; that preparation failure
is preserved in `d5c-allkvk-fresh-preparation-failure.json`. Canonical test-actor
formatting asserts exact AST equality; real application source is unchanged.

Thirteen isolated Python tests and 248 Windows PowerShell checks passed.
They cover the actual route/query shape, exact returned scope/data/token/hold,
wrong scope and values, lock conflicts, missing/changed rows, cleanup uncertainty,
source pins, bundle membership, manifest reproduction, budgets and preservation.
No SQL, VM, application startup or native business work ran during offline tests.

Changes review with Deep off covers the immutable seven-file packet: actor,
wrapper, builder, manifest, two tests and this plan, plus directly supporting
source. Independent review must finish before console handoff. Architecture,
deferred-item, security-routing validators and explicit test selection are run.
Broad pytest, startup imports, command registration and release checks are
skipped for this isolated test-only packet: they introduce unrelated startup
work and cannot prove this native observation or deployment readiness.

D5c remains seven of twelve groups closed and five partial. Stats fresh and both
global/account arrival orders are now accepted; all-KVK, other inspector routes,
coherent tuple/recovery/factory cases remain. This one fresh read does not prove
all-KVK lock orders or execute recovery. D5d physical-failure schedules, D5e
balanced comparisons and D5f final acceptance remain. D5a/D5b stay accepted.
D6 production deployment is separate and unauthorized.
