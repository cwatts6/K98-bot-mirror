# P02 D5c scope refusal execution packet

## Scope and authority

The operator approved preparing and reviewing the wrong-account and wrong-storage
packet. Existing D5 native authorization covers these two distinct read-only
cases on the existing seven-row fixture. The preceding source plan and accepted
restricted-account Finish remain binding. No account recreation, permission,
fixture, writer, isolation or maintenance retry is included. Original evidence
and the consumed 21-input allowance remain unchanged.

`run_p02_d5c_scope_refusal.ps1` takes Stage WrongAccount or WrongStorage. Each
has a separate create-only host intent and guest admission flag. WrongStorage
requires verified WrongAccount; the operator receives its handoff only after
independent receipt adjudication. There is no automatic second case or retry.
The existing D5bReportSession is borrowed, never recreated or removed.

## Actual reader and preservation

One fresh isolated Python process per case loads nineteen pinned unchanged
production modules and the existing pyodbc binary. It calls the actual
ConfigPreparationRecoveryDAL.target_data through recovery_snapshot exactly once.
The factory authenticates as the existing MINI_AMD\K98LabAdmin on database 8,
K98_P025_D5b_20261111; no new credential or impersonation is used. This verifies
application scope, not another SQL-permission test.

WrongAccount uses d5c_foreign_account_20261112 with the correct storage owner.
WrongStorage uses the correct account with d5c_foreign_storage_20261112. Both
pin preparation 7afa9c30-00b0-5626-a866-604e921dfd35. Exact query and argument
allowlisting requires an empty preparation fetch and actual SourceConflict.
Unexpected success or another exception fails. Resource/stream queries, commits,
fallback and second factory/call are excluded. Accounting wrappers observe
transport; they do not fabricate rows or the expected exception.

Before dispatch the administrator independently matches actor SID, PID,
application, SPID and connection birth. Original 23 metadata observations are
unchanged from the accepted account-owner packet. Added reads prove the temporary
restricted account absent and the exact seven-row fingerprint before and after.
Candidate, permission, ownership, original-database protection, completed work,
history, backup, statistics and resource guards remain unchanged. Final queries
prove the work connection birth and unique actor application absent. Unknown
physical cleanup retains custody and prevents a subsequent case.

## Exact bounds

- 1,406 native seconds before the first case; final 1,000 reserved for later slices.
- At most two 60-second host packets. The receipt's 1,286-second lower bound
  conservatively includes both ceilings; exact host elapsed is debited separately.
- 50 Windows-test seconds unchanged; 21 inputs consumed, zero new inputs.
- Each normal case: 23 common queries, six reserved open/close/cancel units,
  three fixture/account-absence reads, one actor-birth read and eleven actor
  units = 44/48. Extra cancellation attempts consume the remaining ceiling.
- Planned maximum 142 rows, maximum 512 per command, 2,048 total; receipt 1 MiB,
  manifest 128 KiB and existing source/actor-output caps retained.
- Actor: eleven units, three statements, one returned identity row; first data
  query returns no rows. Twelve-second self-deadline and bounded anonymous pipes.
- Guest ordinary admission stops at 20 seconds, cleanup at 42; host waits 45
  seconds then at most ten seconds for stop acknowledgment. An owned handle or
  SQL session is never deemed closed merely because its waiter stopped.

No new SQL schema or application runtime changes. ExportPreparation's primary
key, account/storage varchar(128) binary-collated predicates and actual query
were checked against the authoritative SQL repository. The existing seven rows
remain labelled evidence. No production/provider/backup operation occurs.

## Offline validation and review requirements

Eight Python tests exercise both actual-DAL refusals through inert transport,
wrong identity/factory/barrier/guard/native errors, unexpected returned data,
cleanup failure, exact argument checks, downstream SQL rejection and source pins.
The PS5.1 validator exercises one-shot stage order, preservation SQL equivalence,
manifest/lineage/source pins, absent-account and failure stop gates, exact command
and row planning, physical-identity refusal and exhausted-budget behavior.
No existing native fixture setup is executed.

The generated actor, wrapper, Python/PowerShell tests, manifest and this document
form the complete immutable Bot Changes review target; Deep is off. Authoritative
SQL files are unchanged, so there is no SQL-repository diff target. No new
refactor or deferred optimisation is warranted. Focused tests and architecture,
deferred/security-routing checks apply. Broad pytest, startup imports, Discord
registration and production release/repair suites are skipped because only the
isolated test harness changes; no application source or deployment is modified.
No native handoff until review is complete and the final hashes remain pinned.
