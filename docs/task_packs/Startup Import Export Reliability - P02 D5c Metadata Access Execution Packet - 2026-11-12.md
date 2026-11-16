# P02 D5c metadata access execution packet

The operator approved the bounded test-user scope on 2026-11-12. This implements
the prior Ambiguity Acceptance and Metadata Access Plan; the original plan,
receipts and consumed allowances remain unchanged. No native stage has run.

## Exact stages

Target: existing isolated MINI_AMD instance, disposable K98_P025_D5b_20261111,
database ID 8, the pinned VM/session and original read-only database. Only the new
user P02_D5c_Metadata_20261112 WITHOUT LOGIN may be created and removed. There is
no server login, password, explicit grant/deny, role, ownership or setting change.

| Stage | Command units including reserves | Maximum rows | Native ceiling |
| --- | ---: | ---: | ---: |
| Setup | 36 | 143 | 60 seconds |
| Diagnostic | 48 | 152 | 60 seconds |
| Cleanup | 35 | 142 | 60 seconds |

The unchanged common wrapper reserves six units for two SQL opens/closes and two
cancellations, plus 23 existing observations: 29 units. Setup adds old-account
absence, two fixture hashes, two principal observations, public-rights check and
one CREATE. Diagnostic adds old-account absence, two fixture hashes, principal
observation, actor-birth observation and 14 reserved actor units. Cleanup adds
old-account absence, two fixture hashes, two principal observations and one DROP.
The diagnostic actor's 14 units are two opens, ten fixed statements and two closes;
it returns exactly eight rows on success and reserves nine for the three-row
unexpected-diagnostic failure followed by restoration. Failure paths do not repeat statements.

Setup refuses a pre-existing same-name user or login. It requires current authority,
unchanged original permissions and safe inherited public permissions. It records
the generated SID, principal ID and creation timestamp on the guest qualification
disk, in the returned receipt and in a new host custody file. It checks zero direct
permissions, role memberships and owned schemas/objects. Existing user and server
principal fingerprints are captured before and after setup and compared again
before diagnostic and before/after cleanup. Diagnostic changes no principal.

The diagnostic holds the fixed short resource in one administrator connection and
requires a -1/NoLock refusal in a second. Only then may that same requester enter
the exact new database-user context once. It verifies database, original login,
user SID/ID, SPID, zero transaction count, absent server metadata rights and no
database CONTROL. The actual pinned diagnostic must return permission_unavailable
without replacing the original refusal. It uses one diagnostic cursor with the
existing one-second timeout and restores the three-second parent timeout.
An explicit REVERT and original identity check precede acknowledged lock release.
There is no administrator fallback or alternate diagnostic connection.

Process exit, both actor connection births, source/runtime pins, unchanged fixture
and protected metadata, and final SQL absence are independently checked. No
application data query or business producer is admitted by the actor allowlist.
Only the diagnostic helper and its two pure custody/lifecycle dependencies are
bundled; all three source images remain unchanged.

Cleanup requires the captured principal identity, acknowledged actor closure,
no active producer and no other copy session. DROP additionally checks exact
database, ID, zero transaction count, SID, creation timestamp and principal kind
inside its own command. It never adopts/deletes by name alone. It verifies the
user absent and original user/login fingerprints, permissions and fixture retained.

## Failures and custody

Each stage has a create-new host intent and a guest one-shot admission gate.
The diagnostic needs a fully verified Setup state. Cleanup may follow Setup or
Diagnostic where owned identity and closure are established, including a failed
test; it is not a second diagnostic. Unknown creation, missing identity, unknown
actor closure or principal drift stops for evidence review. It never resets the
account, retries a context switch, replays REVERT, or kills an unrelated session.

After an acknowledged switch, a failure before restoration permits one cleanup
REVERT and identity check only while diagnostic custody remains confirmed. If the
actual helper retains the requester after uncertain cursor/timeout cleanup, no
further SQL, REVERT or close is attempted on that connection; custody and context
uncertainty remain explicit. An uncertain ENTER does not retry or infer success;
physical connection closure must establish that context is gone. An uncertain
REVERT is not repeated. Any cleanup error keeps the test failed and retains custody
where appropriate. The pinned actor has its own 12-second deadline; the host and
guest wrappers retain their existing bounded stop/ownership handling. A lost
console cannot recreate a principal or infer an unrecorded outcome.

Every native stage is handed off separately after receipt adjudication. Setup does
not run the diagnostic or remove the user automatically. The complete sequence
must pass tests and a frozen Changes review before the first setup handoff.

## Limits and validation

Initial balance remains 1,398 native seconds, 50 Windows-test seconds and 21 inputs
consumed. All three stage ceilings fit the approved 180 seconds, leaving at least
1,218 native seconds, above the later-phase reserve of 1,000. No new input,
fixture row, maintenance demand, report, import, backup, provider request,
isolation change or runtime correction is authorized. Original failures remain
immutable. The 48-command, 512-row/result, 2,048-total-row, 1 MiB receipt, 128 KiB
manifest, runtime file, VM and storage limits are unchanged.

Focused offline validation: 14 Python tests exercise the real diagnostic against
inert transport, including all 12 token fields, incorrect refusal, unknown switch,
unknown revert, bad restoration, diagnostic failure, closed-cursor uncertainty,
no fallback and exact accounting. 151 Windows PowerShell 5.1 checks parse the
wrapper and exercise extracted controls, stage ordering, identity drift, inherited
access, mutation order, full budgets, source/receipt pins and preservation gates.

The first PowerShell validator failed because its generated expected reason string
was renamed incorrectly. This was a test-only preparation defect, corrected before
native work. Its exact original validator and failure record remain under
`.codex_artifacts/p025/d5c-metadata-offline-first-*`. No native allowance was used.

The first frozen review, revision 685cb33447896f79fe150e845ea48529c4ba8857,
scan 2dcef837-5bb6-4b55-834c-e4162a511bf8, found two operational blockers: restoration
SQL after retained diagnostic custody and an unreserved ninth failure-path row.
Both are corrected with focused regressions; the original six frozen files and
blocker record remain in `.codex_artifacts/p025/d5c-metadata-first-review-preserved`.
The corrected packet requires its own completed review before handoff. The original
scan reported no vulnerability but did not authorize native execution.

No production module or authoritative SQL file changes. SQL-facing assumptions
were reviewed against the SQL repository and the Microsoft references in the
approved plan. This packet requires Bot Changes review, Deep off, for its exact
six frozen files. The SQL repository has no diff to review. Full startup/command
registration, release/schema repair suites and full pytest are skipped: this is
standalone qualification tooling with no production installation or startup change.
Architecture, deferred, security-routing and focused test-selection checks apply.

Passing this packet supplies the remaining C07 denied-metadata branch. It does
not close D5c's other groups, D5d/e/f, production credentials or D6 deployment.
