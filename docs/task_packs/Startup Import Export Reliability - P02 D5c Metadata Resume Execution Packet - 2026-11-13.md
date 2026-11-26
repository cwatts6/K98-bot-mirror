# P02 D5c existing metadata user continuation

## Scope and authority

Continue the approved temporary WITHOUT LOGIN user test after the operator restart.
The original Setup acknowledged CREATE, then failed before the diagnostic because
the harness expected a 32-hex SID and no direct permissions. The accepted read-only
follow-up recorded the actual 56-hex SID and one exact CONNECT tuple. Setup is
consumed and remains incomplete; its source, receipt and history are preserved.
There is no new account, explicit permission change, runtime correction or deployment.
Existing approval covers the still-unused diagnostic and exact-user removal.

Affected files are a new PowerShell continuation, a new test-only Python actor,
their two offline regression suites, the fixed execution manifest, and this plan.
Production modules, the original wrappers, and the SQL repository are unchanged.
Operational tooling remains in scripts; there is no command/view SQL or new shared
abstraction. No unrelated refactor or deferred optimisation is introduced.

## Exact target and custody

Use only host 9SX2VF4, elevated Desktop PowerShell 5.1, VM
2ac1b401-7076-4965-af71-de36ee0f9f9c / K98-MGE-Qualification-20261029,
four CPUs, static 8 GiB and zero network adapters. The operator's fresh session is
0273a292-0961-4cda-bbce-15de9eaead0e, Name D5cResume, in
`$global:D5bReportSession`. Guest MINI_AMD and copy K98_P025_D5b_20261111
(ID 8, creation 2026-11-11 17:00:42.830) must match current observations.

The only permitted user is P02_D5c_Metadata_20261112, principal ID 15,
created 2026-11-12T22:02:45.210, SID
0105000000000009030000008D895FA507D33D40B5926264219625EB, type S,
authentication NONE. No same-name server login, roles or owned schemas/objects.
The sole recorded direct permission is class 0, major/minor 0, grantee 15,
grantor 1, type `CO  `, CONNECT, state G/GRANT.

Identity derives from these hash-verified receipts, not a name or old session variable:

- Failed Setup: d5c-metadata-access-result-632b8ee50ca4411587c16c8e180680f0.json,
  d11f448fe12c59ac13d5742b77e3bf8b1fc5fa654738edb1cad2c8429be9c5f2.
- Accepted observation: d5c-metadata-setup-observation-result-219fbf6683d449b5b717d9f00733fc0a.json,
  f781075b13c4f722f16781bdcbb5e831c9587eaf93bd308c0e24538f2abe26cc.

The new manifest and wrapper pin the fresh session. Each stage revalidates current
database identity/options, protected original database, owner, candidate definitions,
accepted maintenance/history, fixture, backups, resources and connection closure.
The permissions statement proves the exact birth and CONNECT tuple before excluding
that single grantee from the original 799-permission fingerprint. It never accepts
an arbitrary extra grant. Absence is accepted only after the Cleanup stage's
acknowledged exact DROP. The same query count and row limits are preserved.
The existing principal query also checks inherited public rights without an extra
statement. SQL catalog usage follows the existing authoritative SQL repository's
WITHOUT LOGIN test precedent; application SQL/schema queries are unchanged.

## Reviewed sequence to execute after tests and Changes review

1. **Diagnostic**, once. Revalidate the post-restart state and exact principal,
   save its verified birth to a new CreateNew custody file on Q: and the host,
   then apply the remaining eligibility checks. Use the unchanged production
   diagnostic through the pinned test actor on two verified connections. Require
   the original lock refusal, restricted token, metadata-unavailable result,
   restored execution context, lock release and physical connection cleanup.
   Unknown cursor/timeout custody prevents subsequent requester SQL or close.
   No fallback, permission grant or automatic repeat is available.
2. Review the resulting receipt before handing off **Cleanup**, once. Revalidate
   the same identity, permissions and protected state. Only acknowledged actor
   closure permits removal; the DROP statement matches ID, SID, creation, type,
   authentication and exact database. Prove user absence, original accounts and
   permissions, preserved records and physical cleanup. If closure or outcome is
   uncertain, retain custody and stop rather than blindly retry or recreate.

The original guest-owned-user file was never written. The new file is
`Q:\D5b-20261111\d5c-metadata-resume-owned-user.json`, mirrored under
`.codex_artifacts/p025`. Its identity is saved before later eligibility assertions,
and included even in a failed receipt. New per-stage execution-intent files are
CreateNew. No account password or login is introduced. Another restart between
these stages requires review; a missing in-memory state is not automatic adoption.

## Bounds and tests

Before Diagnostic: 1,365 native seconds, 175 seconds in this account scope,
50 Windows-test seconds; 21 inputs consumed and zero new inputs. The two stages
each have a 60-second ceiling, collectively at most 120, leaving at least 1,245
native seconds and 55 account-scope seconds. The later-phase reserve stays 1,000.
No maintenance, writer or isolation retry exists. Seven fixture rows remain unchanged.

Diagnostic reserves 48 command units and 152 rows; Cleanup reserves 35 and 142.
Both retain 512 rows per result, 2,048 total rows, 1 MiB receipt, 128 KiB manifest,
64 KiB source/output, 320 KiB expanded bundle, three-second SQL and one-second
diagnostic timeouts. Actor watchdog 12 seconds, host wait 45 seconds and stop
acknowledgement 10 seconds. Operator cancels/reports a hang before 60 seconds.
Original CPU, memory, disk reserve, version store, log and isolation limits stay fixed.

Focused tests exercise the real bundled diagnostic with inert transports, exact
56-hex identity, wrong identity refusal before connection, all restricted token
fields, one attempt, unknown context-switch/revert outcomes, cursor/timeout custody,
permission-state gates, pre-eligibility custody capture, persistence failure,
command accounting and exact cleanup. Native VM/SQL work is not part of offline tests.
Two preparation-only validation failures were corrected: a test-array concatenation
error and a stale historical session field in the new manifest. Neither ran native
work or changed an original artifact.

Run focused Python and Desktop PowerShell checks, architecture, deferred and security
routing validators, plus path-based test selection. Full pytest, bot imports and
Discord registration are skipped: this packet changes no application code or command
registration and must not start the application. Security gate is **Changes**, Deep
off, on the immutable six-file packet; no repository-wide audit. Review all six
files and directly supporting custody/diagnostic code before any console handoff.
Record the completed review and final hashes separately, without rewriting this
reviewed plan. Offline success does not constitute native D5c acceptance.
