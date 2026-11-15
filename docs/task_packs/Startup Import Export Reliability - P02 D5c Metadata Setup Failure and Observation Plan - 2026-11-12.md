# P02 D5c metadata Setup failure and read-only observation

The Setup attempt created the approved database user, then failed its identity
validation. This is not an uncertain CREATE and must never be repeated. The user
remains on the disposable copy. The diagnostic did not start. Both outer SQL
connections disposed and the captured work session birth was absent.

## Preserved evidence and exact cause

Receipt `d5c-metadata-access-result-632b8ee50ca4411587c16c8e180680f0.json`,
SHA256 `d11f448fe12c59ac13d5742b77e3bf8b1fc5fa654738edb1cad2c8429be9c5f2`,
records acknowledged creation, principal ID 15, creation timestamp
`2026-11-12T22:02:45.210`, SQL-user type S, authentication NONE and SID
`0105000000000009030000008D895FA507D33D40B5926264219625EB`.
The SID is 56 hexadecimal characters; the Setup validator requires 32. This is
the first failing predicate. The later zero-direct-permissions predicate would
also fail: the receipt reports one direct permission. Its identity and state
were not captured, so this plan does not classify or accept it as harmless.

The validator failed before assigning principal custody or writing either custody
file. The returned principal observation still preserves its exact birth identity.
The original Setup remains incomplete; no state is fabricated to mark it verified.
Final fixture and protected-record checks were skipped. Pre-creation evidence and
unchanged existing-account fingerprints are useful but do not replace poststate.
All original scripts, manifests, receipts, first failures and review records stay
unchanged. Local failure adjudication is recorded separately.

## Next bounded action

Prepare one read-only observation using the existing reviewed inventory wrapper.
It checks the exact recorded principal and existing-account fingerprints, captures
every direct permission tuple for that user (16-row ceiling, no truncation), and
compares the original permission fingerprint excluding only that exact user's
grantee rows. The principal identity is checked before the exclusion. All new-user
permission rows are independently captured and compared before/after; this is
observation, not approval of those permissions.

It verifies the seven test rows, original protected database, completed maintenance
and original error history, backup demand, candidate definitions, ownership,
resources, absence of the former restricted login/user and physical SQL cleanup.
It uses no actor process, impersonation, CREATE, DROP, GRANT, DENY, REVOKE, permission
repair, business workload, new input or guest-state adoption. It reads no password.
Guest custody variables and prior Setup status are untouched. Any identity drift,
extra session, changed preservation evidence or incomplete cleanup stops the packet.

The exact follow-up is `scripts/collect_p02_d5c_metadata_setup_observation.ps1`
with `d5c-metadata-setup-observation-execution-packet.json`. Every handoff is pinned
by SHA256 and protected by a create-new intent. The user runs it only after offline
validation and completed Changes review. Receipt review precedes any corrected
diagnostic or exact-user cleanup; neither is enabled by this follow-up.

## Bounds and accounting

The observed host time 1.6438154 seconds charges two seconds, leaving 1,396 native
seconds and 178 seconds in the approved 180-second account scope. Windows-test
time remains 50 seconds. All 21 inputs remain consumed; no maintenance, isolation
or writer retry is available. The later-phase 1,000-second reserve is preserved.

The new packet has 31 metadata statements plus six reserved connection/cancellation
units, for 37 of the unchanged 48-command ceiling. Maximum planned rows are 175;
512 per result and 2,048 total remain hard caps. Queries retain three-second
timeouts, guest work/cleanup deadlines 30/42 seconds, host wait/stop 45/10 seconds,
and a 60-second overall operator ceiling. Receipt cap stays 1 MiB; manifest cap
128 KiB; disk reserves, VM resources and isolation remain unchanged.

## Scope, validation and review

Changes are standalone Bot qualification tooling, one exact manifest, offline
validator and this plan. No production service, DAL, runtime, SQL repository or
existing packet is edited. Existing SQL repository WITHOUT LOGIN precedent is
in `performance_remediation/kingdomscandata4/phase3/22_verify_import_lock_authorization.sql`.
The inherited fixture and preservation SQL is unchanged except the explicit
new-grantee exclusion in the two permission fingerprints. SQL system-catalog
fields are checked against Microsoft catalog documentation before handoff.
The [database-principals catalog](https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/sys-database-principals-transact-sql?view=sql-server-ver17)
defines SID as varbinary(85), not a fixed 16-byte identifier. The
[permissions catalog](https://learn.microsoft.com/en-us/sql/relational-databases/system-catalog-views/sys-database-permissions-transact-sql?view=sql-server-ver15)
defines the exact class, object/column, grantee/grantor, type and state fields used
by the new fixed query. This does not establish what the unobserved permission is.

Offline checks exercise extracted real helper and switch predicates: exact native
SID, missing/mismatched identity fields, remoted collection shape, unexpected
permission observation without acceptance, empty-result refusals, fixed targets,
query preservation, budgets, immutable evidence and absence of mutations/actors.
No runtime SQL test or principal change occurs during preparation. Whole application
pytest, startup imports and Discord registration are skipped because no application
source or startup route changes. Architecture, deferred-item, test-selection and
security-routing validators run or receive explicit applicability notes.
The first offline validator over-rejected the inherited local-table-variable
operations in candidate-definition capture. Its bytes and failure are preserved;
the test now checks new statements for mutations while comparing all inherited
SQL and parameters against the reviewed packet. This preparation failure used no
native time or input allowance.

Security routing is Changes review, Deep off, for the exact immutable four-file
packet. The SQL repository has no change to review. This is a diagnostic follow-up
to known operational validation defects, not a new production vulnerability fix.
Any future correction must capture identity independently of eligibility before
validation can fail; retain the known full native SID instead of guessing a SID
length. Permission acceptance awaits the read-only result. D5c and deployment
remain open and separate.
