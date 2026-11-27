# P02 D5c fresh snapshot acceptance and stale refusal packet

## Accepted durable state

The fresh snapshot receipt `d5c-config-fresh-snapshot-result-5fa08b8aaf16463b8c3ef638631a8d62.json`
has verified SHA256 `032bf791e11216f23742a3566d7905d0f24126aa467b1a14e3a0f7ee2fa40244`.
Independent adjudication accepted the complete actual snapshot at 4/23/20,
protected metadata, resources, process exit, rollback and physical SQL cleanup.
It used 46 reserved commands and 112 actual rows. Host time 1.2966131 seconds
debits two: **1,423 native seconds, 50 Windows-test seconds, 164 configuration-scope
seconds and 106 follow-up test seconds remain**. The final 1,000 native seconds
remain reserved for later D5 slices. Inputs remain 21 consumed. Seven fixture rows
remain; no writer or maintenance retry is available. The committed transition
must not be repeated or restored. Original failures remain preserved.

Acceptance is `.codex_artifacts/p025/d5c-config-fresh-snapshot-acceptance.json`.

## Authorized next check

The seven-row fixture approval includes one stale-action refusal. The next packet
calls the unchanged real `ConfigPreparationRecoveryDAL.settle` once with the saved
old full snapshot (3/22/19). The actor loads the same 17 pinned whole production
modules and existing verified Python/ODBC runtime. The old snapshot comes from
the accepted pre-commit native result, not a fabricated partial object. The current
expected full state comes from the accepted fresh read, differing only in the
three approved version fields.

The real transaction takes the account and sorted resource locks, selects the
current full state with its existing update/hold locks, compares it to the saved
old snapshot and must raise the exact `SourceConflict` stating no claims were
released. No production function or comparison is replaced. The connection
adapter permits only the exact ordered SQL text and parameters for identity,
transaction setup, three real mutex calls and seven existing read queries.
Any additional or changed SQL is refused before dispatch. Commit is also refused.
Either adapter refusal is a test failure, never accepted as the real stale refusal.
The duplicate account lock is intentional existing DAL behavior, preserved here.

The adapter records rows actually fetched by the production DAL, using its existing
row mapping and wire conversion. The assembled current snapshot must match the
accepted fresh state exactly. The real transaction must acknowledge rollback and
close; no commit may be attempted. Existing protected metadata and physical
connection-absence checks follow. The accepted unchanged full snapshot plus zero
mutation dispatch and acknowledged rollback establish fixture preservation; there
is no claim that a successful settlement or provider operation was exercised.

All names, ownership, fence and input parameters are fixed to the approved private
fixture on the single disposable database. There is no new row, import, report,
maintenance, backup dispatch, provider request, permission grant, installation,
database/VM or persistent isolation change. A connection-local zero lock wait
and three-second statement timeout remain. No automatic repeat is included.

## Bounds and preparation evidence

Reservation is 23 metadata observations + six outer connection/cancellation units
+ 12 actor SQL calls + connect/rollback/close = **44 commands**, below the unchanged
48-command ceiling. Actor rows remain ten and planned total rows remain 147.
Per-result/total row limits, 1 MiB receipt, 128 KiB manifest, 64 KiB staged files,
320 KiB expanded bundle and all resource floors remain unchanged. The 20-second
actor, 25-second process wait, 30-second work, 42-second cleanup and 45+10-second
host limits are retained. Manual ceiling is 60 seconds within the remaining
106-second configuration-test allocation. No Windows-test allocation is used.

Offline preparation initially exposed a stale budget-ledger assertion and a
duplicated expected-data payload exceeding the manifest cap. The ledger now
counts the actual settlement path; duplicate expectations are carried only in
the compressed pinned bundle. No limit increased. An inert-driver test then caught
row-mapping normalization missing from the evidence adapter; it now uses the same
existing mapping function as the real DAL. No native attempt occurred during these
corrections. The first failure record is retained in
`.codex_artifacts/p025/d5c-config-stale-preparation-first-failure.json`.

Eight offline Python tests cover exact real refusal, full-state drift, wrong
identity/lock refusal, cleanup uncertainty, ordered lock/read calls, source pins,
matching-snapshot write prevention and direct commit prevention. 200 PowerShell
checks cover actual receipt gates, remoting, immutable metadata, accounting,
refusal type/message, forbidden dispatch, process custody and cleanup.

SQL contracts were checked against authoritative `C:\K98-bot-SQL-Server\sql_schema`
definitions for ExportPreparation, ExportResource, ExportPreparationResource,
ExportExecutionStream, ExportProviderRequest and ExportProviderRequestEvent.
No SQL source or application runtime changes occur. Existing module and SQL source
pins remain enforced. Test harness isolation preserves previously executed packets;
there is no production refactor or new deferred runtime item.

## Review gate and remaining work

Security routing: **Changes review required, Deep off**, covering this new actor,
PowerShell wrapper, two test files and this plan in one frozen Git range. The
changed surface is the test-only call to the real settlement transaction and its
SQL dispatch guard. No Codebase or Deep audit is requested. Native handoff requires
completed review and final file pins. This plan is not a claim that review or
native refusal has already passed.

Full application pytest, smoke imports, registration and deployment tests are
skipped because application/runtime, Discord, dependencies and release behavior
are unchanged. Focused harness tests and architecture/routing/deferred validation
apply. D5c still has other obligations; D5d/e/f and production release remain open.
After one native attempt, adjudicate the exact refusal, durable preservation and
cleanup before proceeding. On uncertainty preserve evidence and do not replay.
