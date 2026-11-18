# P02 D5c actual-worker diagnosis and read-only poststate packet

Status, 12 November 2026: actual worker invocation and overlap evidence verified;
durable poststate/cached-plan reconciliation incomplete. No workload retry is
available or proposed. A separate bounded read-only collector has passed offline
checks and awaits its Changes review before console handoff.

## Failed receipt preserved; actual allowance consumed

Original receipt `d5c-actual-worker-result-17b03e3cfccc4d02a709a12c2665eddd.json`
matches SHA256 `D6C5BBEEBD8DB07CF7AA4FA1150D81BF1102817A8E46C0B4FFD0FF1A565BED50`.
Original script, manifest, execution intent and all earlier failures remain unchanged.
Create-new local adjudication is `d5c-actual-worker-partial-adjudication.json`.

Full host duration 1.8966087 seconds debits two: **1,455 native seconds remain**,
including 455 D5c seconds and the unchanged 1,000 later-slice reserve.
**21 inputs remain consumed; zero new inputs. The one actual-child allowance is
consumed.** No maintenance rerun, demand/reset, import, report, backup dispatch,
permission or runtime correction is authorized by this diagnostic packet.

The exact work session was 52, login time 2026-11-12 12:33:33.847, connection
`2c0953cb-bc9b-4ac1-ad60-9008d5316fa8`. One asynchronous worker call was attempted,
returned normally and joined. The running claim was
`82334f18-8d76-47f1-a0e6-912439287cd3`, ClaimedGeneration 2, request
`468fc60f-8424-4637-b576-99717c7ad062`, StartedUTC 12:33:34.051. Its exact schema
and global Exclusive/Session guards were observed. All five zero-wait contenders
returned -1, with no contender-owned guard remaining.

The real managed reader was refused with ObservationBusy/native 51966 before its
body entered. Its distinct connection `E8704F87-E452-46AB-9089-D1FD8D15FF07` reused
session ID 53 only after the phase observer closed; birth identity prevents false
actor conflation. Reader rollback, isolation restoration, cursor/connection close
were acknowledged; custody was open/zero unconfirmed. PID 5256 joined normally,
exit 0, empty stderr. Exact work birth and unique reader/phase applications were
independently absent. Work, phase and closure connections acknowledged disposal.

The collector then failed at `ledgerAfter`: it read six rows and rejected a seventh.
`ownershipAfter` had passed. Later ledger, backup, permissions, original protection,
session context, resource and statistic poststate were not completed. Therefore
this receipt does not yet establish final generation-2 completion or full D5c
acceptance, despite normal worker return and observed overlap. The receipt records
42 reserved command units and 68 rows, including partial failed-query consumption;
these are not a claim that all reserved operations executed.

## Diagnosis and bounded correction

The failed SQL joined six unique MaintenanceWork rows directly to cached procedure
plans and capped the joined result at six. That cardinality assumption was wrong:
SQL Server exposes one row per cached procedure plan, and different plan options
can produce multiple cached plans. See Microsoft's
[procedure-statistics contract](https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-objects/sys-dm-exec-procedure-stats-transact-sql?view=sql-server-ver15)
and [plan-attribute contract](https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-views/sys-dm-exec-plan-attributes-transact-sql).
The extra plan's identity and cause are still unverified. Do not infer a duplicate
maintenance execution from the number of plans, discard an inconvenient plan,
aggregate away cache identity, or rerun work to repair evidence.

New test-only files: `scripts/collect_p02_d5c_actual_poststate.ps1`,
`tests/validate_p02_d5c_actual_poststate.ps1`, and private
`d5c-actual-poststate-execution-packet.json`. The collector contains no worker call,
child process launch, lock acquisition/release, write statement, permission change
or application startup. It reuses the fixed host/session/copy/volume guards and
retains unknown owned connection handles. Original history is verified on both
host and guest; the failed receipt is a pinned lineage prerequisite.

The concrete read-only sequence is:

1. Require the existing isolated VM, borrowed session, no unresolved custody or
   producer, exact copy/original identity, source images, permissions and resources.
2. Read the six full work rows without joining cached plans. Require the five other
   records unchanged and the exact observed claim completed at generation 2, with
   request, first-error number/time and all unaffected columns preserved. A failed,
   pending, different or incomplete claim stops with its observed rows retained.
3. Read cached records separately for each of the six fixed child procedures, each
   with the same six-row bound and a seventh-row sentinel. Retain every returned
   plan handle, cache birth, execution count/time and six selected cache-key
   attributes. Aggregate attributes within each plan only; do not aggregate or
   choose a preferred plan. Any seventh plan stops rather than expanding a limit.
4. Recheck candidate images, ownership, full work rows, backup, permissions, original
   protection, session context, resource reserves and eight physical statistics.
   Require stability during observation, original table/statistic counts and
   nondecreasing timestamps relative to the failed run's preimage.
5. Close this owned work connection, verify its captured birth absent through a
   separate bounded observer, close that observer, preserve the borrowed session
   and return a create-new receipt. Adjudicate cached-plan attribution locally
   before crediting the actual-child completion and moving on.

This uses 30 metadata statements plus four connection open/close operations and
two cancellation reserves: **36 units within the unchanged 48-unit cap**. Planned
maximum 171 rows remains within 512 per statement/2,048 total; individual work
and per-procedure cache result caps remain six. The original one-MiB receipt,
three-second observation timeout, zero lock wait, 30-second work/42-second cleanup,
45+10 outer watchdog/manual stop before 60 seconds, disk/log/version-store reserves,
fixed VM resources and original 1,800-second budget remain unchanged. No Python
actor starts; at most one work connection or its subsequent closure observer opens.

## Tests, source validation and review decision

374 offline Windows PowerShell 5.1 checks passed. These reproduce six work rows
becoming seven joined rows, preserve rejection of that original shape, and prove
separate six-work/per-procedure results accept multiple plans without hiding any.
Negative cases cover seventh-plan overflow, missing/wrong/completed claims,
original failure/request changes, other work changes, physical statistics drift,
remoting, command/row caps, no workload entrypoints and retained uncertain custody.

The first expanded serialization check found an empty-object handling issue in
the new collector's comparison helper. Its first source/tests/log are preserved as
`d5c-actual-poststate-first.ps1`, `d5c-actual-poststate-first-tests.ps1` and
`d5c-actual-poststate-offline.txt`. The new collector now enumerates object property
names safely under strict mode; the original executed worker remains untouched.
Corrected evidence is `d5c-actual-poststate-offline-corrected.txt`. No native attempt
occurred during this correction.

Authoritative MaintenanceWork and worker/child SQL definitions remain the source
for exact columns/claim lifecycle. The SQL repository has no patch. Security route:
**Changes**, Deep off, exact new Bot collector/test plus two documentation paths,
base previous sealed review `5970724300a6e2d662960e60966bd970e681306e`. Fixed data
access and receipt/custody handling require this review. Architecture/deferred/
routing/selector and whitespace checks apply. Full app startup, native fixtures,
release and command-registration tests are skipped: no app/runtime surface changes
and those operations exceed read-only diagnostic scope. No new deferred refactor
is justified. D5c/d/e/f, separate D6 release and D7/P05 acceptance remain open.

## Read-only handoff ready

Changes review `3a4a9102-3228-4f70-8f8b-4ace9ad731e1` completed and sealed with
zero findings across all four paths. Range `5970724300a6e2d662960e60966bd970e681306e`
to `0de81220d360898aaa7cee8299559884037a77c3`. Independent complete collector/test
review also found no concrete handoff blocker. Canonical completed results were
read back. Reported usage: 2,764,932 total tokens, 2,752,128 cached input tokens.
The private manifest remained hash-pinned supporting evidence, not a Git file.

Architecture (zero changed Python), deferred (two Markdown), security routing
(zero errors/warnings), explicit-path test selection and snapshot whitespace
checks passed. One trailing blank line was removed after the first snapshot's
whitespace refusal; immutable draft `d8c892473691216a626c847d15e52e1b62edea44`
remains available. Executable validation remains 374 passing offline checks.
All four paths matched the completed review before this status-only appendix.
No additional security scan or runtime test is needed for this evidence appendix.

One native read-only invocation is ready, with pins:

- Collector SHA256: `0174C25003ED6E8848450F0FD85215AB2AF571723CCC5978D06B23CC81CE97F7`.
- Manifest SHA256: `b67928ab520e28ea06a3e12be303610574d46c9e21c34f741158ae05e2908dfc`.

The diagnostic intent did not exist at final readiness verification. Use the same
elevated console and borrowed session, stop on error/incomplete output without
retry, and report full host duration. Balance before that invocation is **1,455
native seconds**, **21 inputs consumed**, **zero actual-child attempts available**.
No new native work has occurred in this preparation; completion/cache adjudication
remains pending the diagnostic receipt.

## Native poststate adjudicated

Receipt `d5c-actual-poststate-result-f18ca1a3eabf4a20969d5ac624336e3a.json`
SHA256 `F951EF8C93DED11C038010E97AB8BBFC1E7B8E8884ADA35D844741C13445F3A7`
passed local assertions against the consumed worker's evidence. The exact new
claim is complete, all original failure history and five other full work records
are preserved, and physical cleanup and protected metadata pass. The original
post_import cached plan still has two executions; a distinct new plan records
one execution in the observed call window, with different connection options.
This is not evidence of a repeated worker invocation. The original failed query
and receipt are retained unchanged; no runtime correction is needed.

Full host elapsed time 1.4352494 seconds debits two, leaving **1,453 native seconds**.
The 21-input allowance remains consumed and no actual-child retry is available.
Create-new acceptance: `d5c-actual-worker-completion-acceptance.json`. The accepted
scope includes the observed worker-first overlap, five contender refusals and
managed-reader 51966 refusal, durable completion and cleanup. D5c overall and
D5d/e/f remain open. This appendix records evidence only and changes no executable
behavior; no repeat security scan or native test is required for the appendix.
