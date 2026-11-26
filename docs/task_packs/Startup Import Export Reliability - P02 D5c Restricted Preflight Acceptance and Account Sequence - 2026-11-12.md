# P02 D5c restricted preflight acceptance and account sequence

## Accepted result and outstanding authority gate

The preflight receipt `d5c-restricted-preflight-result-365a95f41a924ec8b4c483d78197ef7a.json`
matches SHA256 `e7dbe05582846e5ea1694f0295addf22a35a7ac2a1ae8adfcdb48044e9bb8c36`.
All 27 observations, protected metadata and both SQL connection closures were
verified from the saved receipt. It used 33 command units, 383 rows and 80,536
receipt bytes. No account or credential was created. Whole host time 0.8842991
seconds debits one: **1,412 native seconds, 179 restricted-scope seconds,
50 Windows-test seconds; 21 inputs consumed, zero new inputs**.

SQL authentication is already enabled and both proposed names are absent.
The server permission lookup incorrectly supplied `SERVER` as its class and
returned NULL. This is not creation authority. Setup uses
`HAS_PERMS_BY_NAME(NULL,NULL,'ALTER ANY LOGIN')` and requires exactly 1 before
generating a password or changing rights. The original collector, receipt and
NULL result remain unchanged. No inventory rerun is proposed. See Microsoft's
[permission lookup contract](https://learn.microsoft.com/en-us/sql/t-sql/functions/has-perms-by-name-transact-sql?view=sql-server-ver16).

Five public server permissions and 275 database public/guest permission rows were
reviewed. The server entries grant database-name visibility and connection to
the four existing TSQL endpoints. Database entries comprise two encryption-key
definition grants, 217 system-view SELECT grants and 56 dbo denies. No public
dbo grant, guest grant, column override or public/guest role membership was
observed. These are inherited metadata rights, not proof of a restricted login.

Saved-file acceptance is `d5c-restricted-preflight-adjudication.json`. No native
work after this receipt has occurred during preparation.

## Complete remaining sequence within existing approval

The approved named login/user remains `P02_D5c_Reader_20261112`, on MINI_AMD and
`K98_P025_D5b_20261111` only. The common wrapper has exactly three stages; the
completed preflight is the first of the maximum four packets. No additional
account, fixture row, writer, isolation cycle or maintenance retry is included.

| Stage | Authorized action | Command ceiling | Row ceiling | Whole-host ceiling |
| --- | --- | ---: | ---: | ---: |
| Setup | Corrected authority gate; one new login/user; CONNECT and SELECT on the three fixed tables | 40 | 156 | 45 seconds |
| Positive | One authenticated actual target reader; exact fixture and cleanup checks | 47 | 161 | 45 seconds |
| Finish | One first-query permission denial; disable and remove the exact owned account | 48 | 156 | 60 seconds |

The three maxima total 150 seconds, within 179 remaining. Before the denied case,
even the preceding stages at their maxima leave 89 seconds; its actor is limited
to 12 seconds, preserving at least 45 seconds for cleanup. Worst-case native
balance remains 1,262, above the final 1,000-second reserve. Actual whole-host
elapsed times are adjudicated separately; no budget is refunded on failure.
Per-result 512, total 2,048 rows, 1 MiB receipt, 128 KiB manifest, source/output
caps and all VM/disk/log/version-store limits remain unchanged.

Each stage retains 23 common observations and six reserved outer connection and
cancellation units. Setup adds two account-state queries, two fixture hashes,
the authority query and six mutations. Positive adds two account-state queries,
two fixture hashes, one administrator birth observation and 13 actor units.
Finish adds two account-state queries, one final fixture hash, one administrator
birth observation, 11 actor units and four mutations. Finish does not claim a
fresh initial seven-row read; its final exact hash is compared with the accepted
immutable seven-row baseline. No query packs extra result sets or raises a cap.

## Identity, secret handling and failure cleanup

Setup refuses existing names, records a fresh random SID in a create-only
non-secret custody file, then creates the login with that explicit SID and a
cryptographically generated strong password. The password remains in guest
memory and is sent to the one owned Python process through anonymous stdin.
It never enters command-line arguments, environment, receipts or files. SQL
mutation failures retain only the operation name and acknowledgement state;
exception messages and command text containing credentials are not published.

The exact login/user SID, IDs and creation times, default database/schema,
absence of roles or owned objects, and exactly four direct grants are verified.
Existing database permission fingerprints exclude only the independently
verified new grantee; they include every original entry. Public server grants
and public/guest inheritance are checked again. Final cleanup restores the full
original database permission fingerprint with the new account absent.

The actual unchanged `ConfigPreparationRecoveryDAL.target_data` and snapshot
helper use a dedicated authenticated factory, no pooling or administrator
fallback. Before allowing the reader to proceed, the administrator observes the
owned process PID, unique application name, restricted SID, SPID and connection
birth. The positive case must return the accepted target. The denied case must
raise native 229 at its first preparation read; resource and stream reads must
not occur. Rollback, isolation restoration, physical close and final absence
are verified. All nineteen production source images remain pinned and unchanged.

The Finish stage includes `-CleanupOnly` for a failed earlier stage. It performs
no denied test in that mode. Every disable/drop action independently requires
the exact generated SID and zero sessions belonging to the named login. Existing
or uncertain identities are never adopted or removed. Unknown actor custody
blocks deletion. The actor has its own deadline; the wrapper does not kill SQL
sessions or arbitrary processes. A lost console does not authorize recreation,
password reset, repeated readers or blind removal. Preserve custody and return
for an exact recovery plan if identity or closure cannot be established.

Host create-only intents and guest used-stage flags reject repeats. Positive
requires a fully verified setup; normal Finish requires a verified positive.
The user returns each receipt for adjudication before the next handoff. A failed
case is not converted into success by cleanup, and there is no automatic repeat.

## Source placement, validation and handoff gate

Operational files only: `scripts/run_p02_d5c_restricted_sequence.ps1`,
`scripts/p02_d5c_restricted_reader.py` and focused tests. Authoritative three-table
definitions were checked in `C:/K98-bot-SQL-Server/sql_schema`. No production
module, SQL source, runtime configuration, service, import, provider request or
deployment changes. No out-of-scope refactor/deferred item is introduced.

Seven offline Python tests exercise the actual loaded DAL/helper against inert
transport, including successful data, native denial, missing identity,
authentication/guard errors, cleanup failures, source pins and credential
redaction. PowerShell tests exercise the actual admission/principal helpers,
inert full-stage control flow, command arithmetic, immutable lineage, bounded
pipe handling and preservation. They run under Windows PowerShell 5.1 as well as
the local shell. Local preparation caught and corrected a sorted-string wrapper
comparison before any native attempt. Failed local preparation outputs remain
in the chat/tool record; original native receipts are untouched.

Architecture, deferred-item and security-routing validators passed. The selector
suggested full pytest, startup imports, command registration and release/schema
repair suites by path keywords. These are skipped: this packet changes only an
isolated operational harness, and importing application startup would exceed the
offline-only scope. Focused actual-source and orchestration checks cover the
changed behavior. These tests do not establish native SQL syntax, authentication
or permission outcomes; those remain the purpose of the approved qualification.

Security decision: **Changes review, Deep off**, covering the complete remaining
account/credential/reader/cleanup packet and tests plus the pinned manifest. A
separate SQL review is unnecessary because that repository has no changes.
No native Setup handoff until the complete frozen sequence passes this review.
Review and final hashes will be recorded in a separate handoff receipt. D5c
remains partial; D5d/e/f and separate D6 release approval remain outstanding.
