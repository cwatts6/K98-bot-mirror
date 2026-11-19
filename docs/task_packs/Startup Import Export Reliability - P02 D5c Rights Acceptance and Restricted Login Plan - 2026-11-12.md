# P02 D5c rights acceptance and restricted login plan

## Accepted inventory

Receipt `d5c-rights-inventory-v2-result-33ee325f8a8647f8be0dbaee79bd5373.json`
matches SHA256 `94f912389e63ece1b9d533c971934d66eeb5af88074ba56e4a959bda8ddc7af6`.
All 27 observations were captured: 33 reserved command units, 231 returned rows,
51,091 receipt bytes. The three rights queries returned four principals,
17 membership rows and 108 permission rows. All paired protected metadata,
resource and session checks passed; both SQL connections disposed, the exact
work connection birth was absent and no other copy session was observed.
The observer reused the work SPID with a different connection birth; SPID alone
is not used to establish closure. Original failure history is unchanged.

Whole host elapsed 0.8848786 seconds debits one: **1,413 native seconds and
50 Windows-test seconds remain; 21 inputs consumed, zero new inputs**. Preserve
the final 1,000 native seconds for later slices. No isolation, writer or
maintenance retry is available. The original failed rights receipt remains
incomplete. This inventory did not read the seven fixture payload rows.

Immutable acceptance: `.codex_artifacts/p025/d5c-rights-inventory-v2-acceptance.json`.
The local saved-file adjudicator initially expected an absent copyFiles observation;
that local error and its correction are recorded separately. No native rerun occurred.

| Existing user | Observed roles relevant to this decision | Login mapping |
| --- | --- | --- |
| SHEETS_USER | db_owner, db_datareader, two KVK roles | None returned |
| rok_user | db_owner | None returned |
| ImportProcUser | db_datareader and db_datawriter | None returned |
| S11_ExportApplication | ExportExecutionAuthority, ExportLegacyEntryReader | None returned |

The administrator can impersonate these users, but that is metadata only and was
not exercised. Explicit grants/denies are not a complete effective-rights proof.
None of these records supplies a verified restricted authenticated connection.
Do not repair their mappings, alter their roles or reuse their credentials.

## Scope and chosen approach — approval pending

Propose one temporary SQL-authenticated login and corresponding database user,
both named `P02_D5c_Reader_20261112`, only in the isolated MINI_AMD SQL instance
and disposable `K98_P025_D5b_20261111` copy respectively. Require both names absent
before creation; never adopt or remove a pre-existing same-name principal.
Record generated SID, principal IDs and creation evidence before dependent work.

Use the unchanged `ConfigPreparationRecoveryDAL.target_data` and unchanged
`recovery_snapshot` through one dedicated, non-pooled authenticated factory per
case. Its three data queries read dbo.ExportPreparation, dbo.ExportResource and
dbo.ExportExecutionStream. Validate returned data against the already accepted
fixture target, including versions 4/23/20, exact preparation, account and storage
owner. Do not invoke the full inspector, recovery mutation or a business producer.

This proves one representative real restricted-factory path. It does not by
itself close wrong-account/storage/identity cases, other inspectors, D5c as a
whole, later D5 slices or production credential/deployment acceptance.

Alternatives considered: existing admin/owner users cannot demonstrate restricted
rights; unmapped users cannot authenticate; EXECUTE AS would test a substituted
database context rather than the requested authenticated factory. A new isolated
principal avoids changing retained accounts. If SQL authentication is unavailable,
stop and return the finding; changing authentication mode or restarting SQL is
not part of this proposal.

## Exact authority and ordered work

1. Read-only preflight: pin existing host/VM/copy/session identities and budgets;
   require `SERVERPROPERTY('IsIntegratedSecurityOnly') = 0`, no competing copy
   activity, sufficient current creation authority, both proposed names absent,
   and no unresolved custody. Inventory relevant public/guest and inherited
   permissions; unexplained broader access or column-level grants blocks setup.
   No new Windows account, authentication-mode change or service restart.
2. Create the exact new login with a cryptographically generated strong password,
   password-policy checks enabled and default database set to the copy. Create
   its mapped user with default schema dbo. Grant only CONNECT and object-level
   SELECT on the three tables above; no fixed-role membership, schema ownership,
   DML, DDL, impersonation or server-admin grant. Public membership is inherent
   and must be inspected, not silently treated as empty. Capture exact new
   permission delta while requiring all pre-existing entries unchanged.
3. Positive case, once: authenticate with that login, verify original login,
   database user and target identity, then invoke the actual target reader once.
   Require exact expected data, one factory call, acknowledged rollback, restored
   connection isolation and physical close. No extra query grants for observer
   convenience: an administrator observer must correlate the application name,
   SPID and connection birth if restricted DMV visibility is insufficient.
4. Only after positive acceptance, DENY SELECT on dbo.ExportPreparation to this
   exact new user. Open a new restricted connection and invoke the same reader
   once. Require native permission error 229 at its first data query, preserved
   as the first error; no resource/stream read, administrator fallback, legacy
   fallback, busy reclassification or retry. Verify rollback and physical close.
   A different failure is evidence, not a successful permission-refusal test.
5. Disable the exact owned login, verify its sessions gone, drop only its mapped
   user and login, then verify absence and restored original permission state.
   Cleanup is included on failure where exact identity and closed-session proof
   allow it. Do not kill sessions or delete an uncertain/pre-existing principal.
   On uncertainty, retain evidence/custody and stop for a concrete cleanup plan.

The password stays in guest memory and is passed to the owned actor through an
anonymous input pipe; never command-line arguments, environment dumps, chat,
receipts or evidence files. Each actor has an exact process identity. SQL text
or exceptions containing the password must not be logged. Losing the console
does not authorize account recreation, password reset or another test attempt.
The non-secret SID/name receipt is the recovery reference. Credential handling
and safe parameterization/quoting must pass review before execution.

## Bounds and preservation

Four staged packets at most: preflight/setup, positive read, denied read, cleanup.
Total native ceiling **180 seconds**, each packet at most 60 seconds; reserve
at least 45 seconds of the 180 for cleanup before admitting either read case.
All stage host times, including failures, count against existing native balance.
Worst-case balance after the scope is 1,233 seconds, preserving the 1,000 reserve.
No automatic repeat; one positive and one denied call maximum. A setup refusal
does not authorize broadening privileges or switching authentication methods.

Each packet must fit the existing 48 command, 512 rows/result, 2,048 rows total,
1 MiB receipt, 128 KiB manifest and existing source/output caps. Count setup,
identity checks, grants/deny, actor calls, cancellation, rollback, close and
cleanup; no packed queries or cap increase to make it fit. Freeze exact per-stage
command/row budgets before handoff. If the design cannot fit, report that before
any account creation. This is not yet an executable or reviewed packet.

Preserve VM 8 GiB/4 CPU/zero NICs, C/Q disk reserves, log and version-store limits,
the original read-only database, all failed evidence, seven fixture rows and
accepted work. No new application rows, import, replay, maintenance demand,
report recomputation, backup dispatch, provider request or runtime correction.
Only the named new principal and its explicitly listed permissions may differ
temporarily; final original permission fingerprint must match. No Windows-test
allocation is consumed by these SQL reader cases.

## Architecture, SQL and review

Operational actor/wrapper and focused tests belong in scripts/tests; no command,
view, service, core helper, production config or authoritative SQL source change.
Reuse reviewed account-reader actor loading/custody patterns, remove its holder
hook, and preserve actual DAL/helper source images. The three object definitions
are authoritative in C:/K98-bot-SQL-Server/sql_schema. No schema migration.
No unrelated refactor/deferred optimisation is introduced.

Offline tests must cover exact new identity, existing-name refusal, SQL-auth mode
refusal, secret redaction/transport, role/public/column-right guards, exact grants,
one factory call, native 229 preservation, no fallback, unchanged fixtures and
existing permissions, failed cleanup/custody, budget exhaustion and no retry.
Validate architecture, deferred/security routing and test selection. Complete a
frozen Bot Changes review, Deep off, of every new executable before handoff.
No SQL-repository diff review is needed unless SQL source files actually change.

Current documentation/evidence-only acceptance does not change runtime or rights;
a fresh discovery scan is skipped for this plan. The proposed executable account
and secret-handling changes require Changes review before native work.

Current plan checks: architecture validation passed (48 Python files), deferred
validation passed (80 Markdown files), security-routing validation passed with
zero warnings/errors. Saved-receipt adjudication passed. No application runtime
test applies to this documentation and saved-file acceptance step.
The explicit selector ran on this plan and recommended smoke imports, command
registration and four release/schema/permission-repair suites by path keywords.
Those are skipped here: no release identity, schema, permission repair,
registration or importable application source changed. They do not adjudicate
the saved native receipt or authorize the future test-account packet.

Microsoft references checked while scoping: [authentication-mode property](https://learn.microsoft.com/en-us/sql/t-sql/functions/serverproperty-transact-sql?view=sql-server-ver16),
[CREATE LOGIN](https://learn.microsoft.com/en-us/sql/t-sql/statements/create-login-transact-sql?view=sql-server-ver17),
and [object DENY precedence](https://learn.microsoft.com/en-us/sql/t-sql/statements/deny-object-permissions-transact-sql?view=sql-server-ver17).
In particular, column grants can override a table-level deny; the packet must
check them rather than assuming a DENY alone establishes the intended boundary.

## Approval needed

Earlier scope expressly prohibited new accounts and permission changes. Request
one exception for this named temporary login/user, listed grants and denial,
two one-shot reader cases and identity-checked cleanup under the 180-second cap.
No such mutation or executable packet preparation has occurred yet. After approval,
prepare, test and review the complete sequence before its first native setup step.
