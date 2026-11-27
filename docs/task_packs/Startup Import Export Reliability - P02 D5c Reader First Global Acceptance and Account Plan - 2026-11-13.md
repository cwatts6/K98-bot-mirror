# P02 D5c reader-first global acceptance and account plan

## Accepted global result

Receipt `d5c-stats-reader-first-global-result-c10e82da53314678935bd6a76b1eb7cf.json`
has SHA256 `2d7773843292eb42cd66e97af635956bd0e1ca22eb721dec5c5b7050f09a4689`.
It is accepted. The actual snapshot reader fetched its exact preparation before
the separate global holder acquired its lock. The actual full Stats inspector
then refused with `ImportExecutionActive`. Reader rollback, isolation restoration
and close were acknowledged; the global holder remained exclusive until its own
rollback and close. Normal process exit and independent SQL absence checks passed.

All protected records, original failures, completed work, eleven fixture rows,
permissions, ownership, candidate definitions and statistics remain unchanged.
Removed test accounts remain absent. The receipt recorded 47 operations and 108
rows without errors. Equal monotonic timestamps reflect clock resolution; the
fixed control flow and actual fetch/acquisition acknowledgements establish order.

Host elapsed 1.6944976 seconds is charged as two seconds. The create-only
acceptance is `d5c-stats-reader-first-global-acceptance.json`. There are 1,351
native seconds remaining, including the protected 1,000-second later-phase
reserve, and 50 Windows-test seconds. Eleven of 64 synthetic rows and all 21
retained inputs remain consumed. No accepted attempt becomes replayable.

## Next distinct account schedule

Run one new full Stats reader-first/account-owner case on the same labelled
preparation. The real snapshot reader fetches that preparation first. The
qualification wrapper then opens one separate connection and acquires the exact
account lock derived by the unchanged production `coordination_lock_name`.
The actual inspector continues its normal queries. Its global availability must
be one, followed by account availability zero and the expected typed refusal.
A global conflict cannot count as passing this account case.

The reader must physically close before checking that the account owner remains
exclusive. Only then does the holder roll back and close. Unknown reader cleanup
blocks holder release and fails the packet. A failure before the exact preparation
fetch creates no holder. The outer observer independently proves actor/work
session absence and preserved records. No recovery action is selected or executed.

This scheduling hook changes only the qualification connection wrapper. The
actual inspector, snapshot profile, SQL strings and production guards are
unchanged. The existing four inspector rows and seven earlier fixture rows are
read only. No import, report, maintenance, backup, provider request, input replay,
new row, permission, isolation or VM setting change is included.

## Bounds and preservation

The packet reserves 48 operations: 21 metadata, six outer control/cleanup and
21 actor operations (ten SQL statements, seven rows). Planned maximum rows are
112 under the unchanged 2,048 cap. The manifest is 130,827 bytes under 131,072.
The receipt cap remains 1 MiB; packet ceiling 60 seconds; actor watchdog 20 seconds.
Existing resource floors, bounded outer wait/cancellation, process custody,
session birth checks and create-only one-attempt intent remain mandatory.

Every metadata statement, fixture expectation, source bundle and original
preservation gate is byte-identical to the accepted global reader-first packet.
Both permission observations require zero other copy sessions. Two new lineage
pins retain the accepted global receipt and acceptance; all prior pins remain.

## Preparation, checks and review

The first source-only draft exceeded the manifest limit by 484 bytes and stopped
before creating executable packet files. Canonical formatting of the test actor
reduced JSON escaping, with exact Python AST equality asserted before and after.
Unused inherited constants and stale explanatory prose were removed or corrected;
no executable operation, SQL text, numeric limit or source module was relaxed.

A builder replacement assertion stopped before output when an earlier rename had
already changed a later replacement target. The first emitted pre-review draft's
inherited application prefix was then corrected. Its three original files remain
under `d5c-stats-reader-first-account-pre-review-draft`. No native attempt occurred.
The builder now reproduces the final manifest exactly, and tests require the
account-specific prefix and absence of the old prefix.

Sixteen isolated Python tests passed, including actual query order, each relevant
failure, wrong-global versus exact-account refusal, cleanup uncertainty, source
pins, AST preservation and exact manifest reproduction. 254 Windows PowerShell
5.1 checks passed, including parser/remoting, missing or changed order evidence,
wrong-guard refusal, unchanged metadata, fixture and real source bundle, budgets
and pins. No live SQL, VM or application startup ran during these checks.

Changes review, Deep off, covers the immutable seven-file packet (actor, wrapper,
builder, manifest, two tests and this plan), with independent review before
handoff. Run architecture/deferred/security-routing validators and explicit test
selection. Broad pytest, smoke imports, command registration and release checks
remain outside this isolated test-only pass because they add unrelated startup
work and are not evidence of this native schedule or deployment readiness.

D5c remains seven of twelve groups closed, five partial. This closes another
specific C01 ordering only after native adjudication; it does not close other
inspectors, C04/C05/C06/C09, D5d physical-failure schedules, D5e comparisons or D5f
final acceptance. D5a and D5b remain accepted. D6 production deployment remains
separate and unauthorized.
