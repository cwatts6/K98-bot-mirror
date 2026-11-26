# P02 D5c ambiguity acceptance and metadata access plan

## Accepted evidence

The receipt `d5c-holder-ambiguous-result-b252b833ceb14475bdb9cf68c1083690.json`
matches SHA256 `4d1395b377066e5d6b273e52bf1386686154812b696cf800c24777f3de6c56de`.
The actual diagnostic returned unavailable/holder_disappeared_or_ambiguous for
two ownership records on the same resource and holder connection: SESSION and
TRANSACTION, both shared. It did not name a guessed owner. The original timeout
refusal remained unchanged. This is ambiguity of ownership records, not proof
of two different people or two holder sessions.

The transaction rollback and session-lock release were acknowledged. Actor exit,
both SQL actor connection births absent, outer connection cleanup, all protected
records, seven fixture rows, original permissions and removed restricted account
were verified. The wrapper used 46 command units, 118 reserved rows and 25,539
receipt bytes. The one ambiguity attempt is consumed; no repeat is available.
Acceptance is saved in `.codex_artifacts/p025/d5c-holder-ambiguous-acceptance.json`.

Full host elapsed 1.3075594 seconds debits two: **1,398 native seconds remain**.
The Windows-test balance remains **50 seconds**; the **21-input allowance is
consumed**, with zero new inputs. Preserve the later-slice 1,000-second reserve.

The pinned actual `services/sql_lock_holder_diagnostics.py` also passed a bounded
offline check for 32-character unsupported, 33-character truncated and 75-character
hashed coordination-style resources. All three returned the exact expected
unavailable reason before accessing any cursor or connection. Original error
arguments/notes and connection custody were unchanged. This used no native time.
Saved evidence: `.codex_artifacts/p025/d5c-long-resource-offline-acceptance.json`;
checker: `.codex_artifacts/p025/check_d5c_long_resource_offline.py`.
This proves the implemented long-resource limitation only, not native attribution
for those resources or a restricted-authentication scenario.

## Next scope: metadata unavailable through a restricted database context

Approval is pending for one new temporary database user **P02_D5c_Metadata_20261112**
WITHOUT LOGIN in **K98_P025_D5b_20261111** only. No password or server login is
created. The previous P02_D5c_Reader_20261112 scope is consumed and that account
remains absent. This proposal is a new exception for database-user creation,
one temporary impersonation, and exact cleanup; it does not reuse the old scope.

One test must establish a real lock refusal, invoke the unchanged optional
diagnostic under this restricted context on the same requester connection, and
require unavailable/permission_unavailable while retaining the first refusal.
No extra credential, alternate connection or administrator diagnostic fallback
is permitted. Impersonation occurs only in the labelled test harness, never in
production runtime. This proves the diagnostic's missing-metadata branch, not a
new authenticated-reader factory or historic holder attribution.

The four proposed principal/context statements are fixed:

```sql
CREATE USER [P02_D5c_Metadata_20261112] WITHOUT LOGIN;
EXECUTE AS USER = N'P02_D5c_Metadata_20261112';
REVERT;
DROP USER [P02_D5c_Metadata_20261112];
```

They are a scope definition, not an executable packet. No GRANT, DENY, role
membership, ownership, existing-account or authentication-mode change is allowed.
Inherited public permissions must be inspected; absence of explicit grants alone
does not establish restriction. Unexpected authority blocks the test.

## Ordered stages and stop conditions

1. **Setup, once, at most 60 seconds.** Recheck exact host, VM, copy, resources,
   no competing copy activity and existing authority. Require the proposed user
   and same-name server principal absent. Never adopt or delete an existing name.
   Record the original permission/principal state, create only the new user,
   capture its SID, principal ID and creation metadata, and verify no login,
   explicit grant, role or owned object was added. Preserve the generated identity
   on host and guest for cleanup even if the console closes. Stop on uncertain
   creation; do not reissue CREATE or drop by name alone.
2. **Diagnostic, once, at most 60 seconds.** Verify the exact setup identity.
   Establish two non-pooled actors with independently observed connection births.
   Holder takes the fixed public `k98-legacy-output-snapshot` Session/Exclusive
   lock. Requester must receive exactly the ended -1 refusal with no held lock.
   On that same requester connection, enter the exact temporary user context once,
   verify database/user/original-login identity and absence of required server
   metadata permission, then call the actual pinned helper once. Require exactly
   permission_unavailable, unchanged first error, no guessed holder, no fallback.
   Revert once, verify original context, release the owned holder lock and close
   both actors. Independently verify births absent and preservation. A missing
   permission check, unexpected exception or unknown result fails the test.
3. **Cleanup, at most 60 seconds, included on failure when safe.** Only after
   exact actor closure and principal identity match, remove the owned new user.
   Verify absence, unchanged server principals, original permission fingerprint,
   seven fixture rows, original failures, other completed work and SQL cleanup.
   Never kill unrelated sessions, repair permissions or remove a mismatched user.

Reserve cleanup capacity before setup. A failed or uncertain context switch or
REVERT cannot be replayed; retain custody/evidence and use acknowledged physical
connection closure to establish that context is gone. If closure or ownership
cannot be verified, stop with the exact remaining state for a cleanup plan.
Do not proceed to another test with unresolved custody or a leftover test user.

## Fixed bounds and execution prerequisites

The entire scope is at most **180 seconds**, including failures and cleanup,
inside the existing native budget; worst-case remainder is **1,218 seconds**.
Reserve at least 60 of these seconds for final cleanup. No Windows-test time,
input allowance, maintenance demand or fixture-row allowance is consumed.
No isolation, writer, maintenance, authentication or diagnostic retry is included.

Every stage retains 48 total command units, 512 rows per result, 2,048 total rows,
1 MiB receipt, 128 KiB manifest and existing source/output caps. At most two SQL
actors plus one observer, one-second optional diagnostic, three-second observation,
30-second lock holds and all existing VM, disk, log and version-store limits apply.
Preparation must count every identity/context statement, cursor operation,
open/close, failure cleanup and cancellation reserve in a per-stage ledger. No
batch packing, truncation or dropped preservation check may make a packet fit.
If it cannot fit, return findings before setup rather than enlarge a limit.

Freeze and review the complete setup/test/removal sequence before creating the
user. Native handoffs must use the existing elevated console's authenticated
session, exact script/manifest hashes and full host stopwatch accounting.
After each receipt, adjudicate before the dependent stage; failure never permits
an automatic repeat. Current scope approval would not itself certify executable
readiness. There is no native command to run from this document.

## Architecture, SQL validation and checks

Standalone operational scripts and focused tests own this lab-only schedule.
Reuse the reviewed lock-only actor's loading, original-error preservation and
connection custody; keep production helper, application modules and SQL source
unchanged. No command/view, startup hook, schema, report or provider behavior is
changed. No new application table/object or row is needed; no unrelated refactor.

The authoritative SQL repository contains a WITHOUT LOGIN/EXECUTE AS precedent in
`performance_remediation/kingdomscandata4/phase3/22_verify_import_lock_authorization.sql`.
Its delete-if-present behavior is specifically not adopted. The new plan refuses
pre-existing identities. Required server metadata permission is also documented
in its `deploy/recovery/Observe-CheckpointBlocking.sql`.

Microsoft documents that database-user impersonation is restricted to the current
database and does not inherit server-level permissions; WITHOUT LOGIN users cannot
authenticate. These support the proposed approach but do not replace the native
token check: [EXECUTE AS](https://learn.microsoft.com/en-us/sql/t-sql/statements/execute-as-transact-sql?view=sql-server-ver16),
[CREATE USER](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-user-transact-sql?view=sql-server-ver16).
SQL Server 2022 lock metadata requires VIEW SERVER PERFORMANCE STATE:
[lock metadata permissions](https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-objects/sys-dm-tran-locks-transact-sql?view=sql-server-ver16).

Offline tests before handoff must cover existing-name/mismatched-SID refusal,
public rights, create/switch/revert unknown outcomes, exact original-error retention,
helper timeout restoration, no fallback, actor cleanup, exact user removal,
original permissions/fixtures, no retry and full command/row/deadline accounting.
Review all new executable files through a frozen Bot **Changes** scan, Deep off,
and independent review before native setup. No SQL repository diff is proposed.

For this acceptance/plan-only change, fresh security discovery is skipped: no
production or native executable is changed. The offline checker loads the pinned
pure diagnostic and uses a cursor that rejects every access; it opens no SQL,
network or guest process. Targeted assertions cover this new local evidence.
Architecture/deferred/security-routing/test-selection checks apply. Full pytest,
startup smoke, command-registration and release/schema/permission-repair suites
are skipped for this receipt/plan step: no corresponding runtime surface changed.

Observed validation: three offline actual-helper cases passed; architecture
validation passed for both local evidence scripts; deferred validation passed for
this plan; security routing reported zero errors/warnings; test selection completed
and its broad recommendations have the explicit skip rationale above.

## Remaining D5c and deployment boundary

C07 now accepts known-holder, disappeared-holder, ambiguous ownership and offline
long-resource limitation evidence; denied metadata remains unproven. Other partly
open groups remain C01 full inspectors, C04 season/weights, C05 queue/pool/unowned
hold, C06 adapter-specific action/count boundaries, C09 additional identity/factory
routes and C12 full presentation integration. These are unequal work groups, not
a meaningful percentage. D5d fault/restart, D5e balanced cost qualification and
D5f final evidence/release readiness remain. Production deployment is D6 and is
not authorized by this lab plan.
