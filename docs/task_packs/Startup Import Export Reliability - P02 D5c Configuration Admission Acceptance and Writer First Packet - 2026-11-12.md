# P02 D5c configuration admission acceptance and writer-first packet

## Accepted seven-row admission

Receipt `d5c-config-admission-result-9e314f7af97e457aad6ff21deb32f1e8.json`, SHA256
`60FC6285CE9A26265ACB43DE1C377729C79FD1D41767EA48A6C0158A70801FED`, passes
independent saved-evidence adjudication. All 24 metadata observations and 16
successful fixture steps are present. Exact absence and enabled-constraint gates,
seven inserted keys, two resource activations, all seven full row values and the
COMMIT acknowledgement match the approved proposal. No rollback was attempted.
The receipt used 47 reserved command units and 125 rows. Both SQL connections
closed and the exact work-session birth was absent. Paired original protection,
ownership, permissions, maintenance/error history, backup demand, candidate
definitions and physical statistics match the accepted preservation baseline.
Resource checks and borrowed-session/isolation preservation passed.

The full host duration 1.6311375 seconds debits two. **1,437 native seconds and
50 Windows-test seconds remain; 21 inputs remain consumed; no maintenance retry.**
Seven of the 64 fixture rows are now consumed, leaving 57 under future separately
reviewed proposals. The approved configuration scope has 178 of 180 seconds left;
its later tests retain their separate combined 120-second ceiling. Do not replay
admission or delete the seven evidence rows. Saved acceptance is
`.codex_artifacts/p025/d5c-config-admission-acceptance.json`.

## Exact next test

The existing approval covers one writer-first rolled-back transition, one later
reader-first committed transition and one stale-action refusal. This packet runs
only the first case. The unchanged public
`ConfigPreparationRecoveryDAL.target_data` opens the actual guarded recovery
snapshot while an independent writer holds the approved uncommitted versions.
It must return the complete old preparation, two resource versions/owners and
exact stream membership. The fuller `snapshot` and stale settlement boundaries
remain for later packets; this test does not stand in for those cases.

The writer binds the exact preparation/account/storage/owner and two resource
keys. It begins a transaction, changes only preparation Version 3 to 4 and resource
versions 22/19 to 23/20, requiring exact update counts and returning all three
new versions. The reader must still see 3/22/19. After reader cleanup, one owned
ROLLBACK returns the restored three-version tuple. There is no COMMIT, insert,
delete, reset, provider request, import, report, maintenance or permission change.
All seven fixture rows remain as evidence. Failure never authorizes a retry.

SQL names, types, constraints and target-data columns were checked against the
authoritative ExportPreparation, ExportResource and ExportExecutionStream schema
files, the captured installed catalog and the accepted fixture. Production Bot
and SQL sources are unchanged. Test SQL belongs only in this labelled packet.

## Source and startup isolation

The actor uses 17 whole, byte-pinned production modules, including the actual
DAL, row mapping, serialization, identity, observation and custody helpers.
It does not extract or reimplement those paths. Namespace packages have empty
search paths; the workbook parser's two unused imports are fail-closed adapters.
No workbook, input, provider or application startup module is loaded. The verified
existing pyodbc extension is loaded before the production diagnostic module.
The standard-library runner uses `-I -S -B`; no installation is required.

The initial zlib packaging was 79,304 bytes and correctly failed the unchanged
64 KiB staged-file cap. The complete source now uses bounded BZ2 compression:
60,975 stored bytes, exactly 306,980 expanded bytes, with both hashes and exact
framing checked. Expansion is bounded to the pinned size and a 320 KiB ceiling;
no runtime code or guard is omitted to fit. The 128 KiB manifest cap remains.
The first offline startup test then exposed the missing driver-before-diagnostics
ordering. The runner and isolated test setup were corrected, and a full-startup
regression proves the ordering without any ambient driver module. Original
drafts and failed output remain preserved; neither failure ran native SQL.

## Bounds, preservation and cleanup

One SQL-only child process holds two actors; the existing metadata connection is
the observer and is idle during their overlap. Three-second SQL timeouts,
zero lock wait, 20-second child watchdog, 25-second parent wait and the existing
30/42/45+10-second work/cleanup/outer limits remain. Manual cap is 60 seconds,
within the combined 120-second later-test scope and final 1,000-second reserve.
This SQL test does not debit the separate Windows file/IPC allocation.

The complete command reservation is **48**: 24 existing metadata statements,
four outer connection opens/closes, two outer cancellation requests, five reader
SQL calls, eight reader connection/isolation/rollback controls, three writer SQL
calls and two writer open/close controls. The full 18-unit actor reservation and
12 returned rows are charged before process admission, even if its receipt is
missing. Maximum total rows are 149/2,048, with the unchanged per-result 512-row,
1 MiB receipt and 64 KiB actor output/source-file ceilings.

All 24 metadata statements are retained; only the final absence query expands
its predicate to include both actors' unique application identity alongside the
captured outer session birth. Its result cap becomes three within the existing
global cap. All paired original-protection/ownership/ledger/backup/permission,
candidate-image/statistics, resource and session-context checks remain intact.
The observer cannot open until the outer connection is disposed and the owned
child is joined. Uncertain process, job, runspace or connection custody is kept;
only this packet's owned child may be terminated on deadline. Forced exit never
counts as success. Closure evidence requires all relevant sessions absent.

## Offline validation and review gate

Nine isolated Python tests pass: actual DAL old-version read, mixed/dirty tuple
refusal, both wrong identities, update/guard failures, rollback/close uncertainty,
exact source bundle/framing, denied parser and full startup order. They use only
an inert driver; no application imports outside the pinned closure or native calls.
The 188 PowerShell checks cover inherited guards, all retained observations,
pins, remoting, exact actor evidence, invalid outcomes, command/row/time limits
and closure admission. Architecture validation passed for both Python files.
The installed project Ruff passed after two unused-import fixes. The system
interpreter lacked Ruff; no dependency was installed.

The explicit selector ran. Full pytest, application smoke imports, command
registration and release tests are skipped because this is an isolated test
packet with no production runtime, command or deployment delta. Executing broad
startup would not validate this packet and would violate its isolation intent.
No production refactor or new deferred optimisation is introduced.

Security decision: focused **Changes review, Deep off**, covering the new actor,
wrapper, two validators, this document and the obligation reconciliation update.
SQL source is read-only, so no SQL-repository diff exists. Complete review and
final pins are required before one console handoff. Review the returned evidence
before any committed transition or stale action. D5c/d/e/f and deployment remain
open; the synthetic closed stream/session still proves no real provider outcome.

## Reviewed representation correction

Full Changes review `de9599aa-f111-47bd-a9ae-d2a73e356346` at `4a80760b` completed
with zero security findings and one operational blocker: SQL-converted GUID text
can be uppercase, while the version-tuple comparison expected lowercase. The
first fake driver returned expected tuples directly and concealed this mismatch.
No writer-first native attempt occurred. Original reviewed files, manifest and
passing/failed offline evidence remain preserved.

The correction canonicalizes only the preparation GUID field in both returned
version tuples. Raw tuples remain in the receipt. Resource-key case, foreign
identities, row order, duplicates and versions remain strictly checked. SQL,
production modules, fixture values and all bounds are unchanged. The fake driver
now returns uppercase GUIDs by default; the ninth test checks normalization while
rejecting foreign GUIDs, changed resource-key case and duplicates. Nine Python
tests and 188 PowerShell checks pass. A focused correction Changes review and
final pins remain required before the one-time handoff.

## Correction review completed; one attempt ready

Correction Changes review `23a14768-48c0-4420-901a-c0796fb327af` at `4c501c3b`
completed and its sealed result was read back: zero findings, all four changed
files covered, and the prior operational blocker resolved. Independent review
confirmed raw evidence and strict identity/resource/row checks remain intact.
Measured review usage: original 2,628,716 tokens; correction 1,414,345 tokens.

The final script SHA256 is
`aa40b2430e2c5aa6e7c5ff1dfcb5ec049bafcf628d799e1a257b034ceebdcec6`;
manifest SHA256 is
`035db87ff7357a1d8715afa243e2da93bf73342cef0a2abd8162a289d9d6cd0f`.
One manual writer-first attempt is ready under the existing approval. No native
attempt has occurred. Its receipt must be accepted before the committed change
and stale-action packets. Balance remains 1,437 native seconds, 50 Windows-test
seconds, 21 inputs consumed and no maintenance retry.
