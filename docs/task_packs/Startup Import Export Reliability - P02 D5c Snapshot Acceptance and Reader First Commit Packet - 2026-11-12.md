# P02 D5c snapshot acceptance and reader-first commit packet

## Accepted snapshot

Receipt `d5c-config-snapshot-result-3e0e60e90d9f4b4a8a437fcf32d9959d.json`,
SHA256 `1e82e42faf1567808560aa2c5fb8bcfd169aff8f22cd90c1f2bb0fe76e67d18d`, passes
independent saved-evidence adjudication. The actual public configuration DAL
returned the complete expected preparation, membership, resources and stream,
with zero linked provider requests/events. Preparation/resource versions remain
3/22/19. Protected metadata, both resource checks, managed cleanup, owned process
exit, outer connection disposal and physical SQL absence all pass.

The packet used 46 reserved commands and 112 actual rows. Host elapsed 2.0963761
seconds debits three: **1,427 native seconds, 50 Windows-test seconds, 168
configuration-scope seconds and 110 later-configuration-test seconds remain**.
21 inputs are consumed; seven labelled fixture rows remain, with no new rows.
The final 1,000 native seconds remain reserved for later D5 slices. No maintenance
retry or repeat of the accepted writer-first test is available.
Acceptance and the actual saved snapshot are in
`.codex_artifacts/p025/d5c-config-snapshot-acceptance.json`. Synthetic closed stream
metadata does not prove provider activity. Original failed receipts stay failed.

## Already-authorized next transition

The operator's seven-row fixture approval includes one committed version change
and one later stale-action refusal. This packet performs that committed transition
once; it does not repeat writer-first or settle any work.

`scripts/p02_d5c_config_reader_first.py` uses the same 17 pinned whole production
modules and the unchanged public `ConfigPreparationRecoveryDAL.target_data`.
Its connection adapter provides the sole scheduling barrier. After the real DAL
has selected SNAPSHOT isolation, acquired its shared schema guard, executed the
preparation query and fetched the exact original preparation row, the adapter
opens the distinct writer. It records and compares the full preparation row before
any writer admission. The DAL and its SQL/guards are neither replaced nor patched.

The writer directly validates the pinned database/server/login and clean session,
begins once, then executes the same parameterized exact three-row transition:
preparation 3 to 4; private resource versions 22/19 to 23/20. Exact owner, fence,
state, scope and original-version predicates remain. It verifies all three changed
values, then commits once with a parameterless control batch and zero-transaction
postcondition. Control batches do not cross parameterized execution boundaries.

Only after commit acknowledgement does the original preparation row return to
the actual reader, whose remaining resource/stream queries must retain the exact
old 3/22/19 snapshot. The guard and observation transaction remain owned until
the real DAL acknowledges rollback, isolation restoration and physical close.

The writer cleanup runs one conditional rollback and close. After successful
commit that rollback is a no-op; it does not undo committed values and is never
reported as restoration. If commit was attempted but not acknowledged, the receipt
marks `commitOutcomeUnknown`; no dependent action or replay is permitted. Reader
failure after commit preserves the commit evidence and stops. No reset or retry.

The wrapper `scripts/run_p02_d5c_config_reader_first.ps1` retains all 23 metadata
observations, resource gates, identity/source/history pins, create-new intent,
owned process deadlines and post-disposal physical closure checks. Original
executed files and evidence remain unchanged. No installation, permissions,
isolation setting, VM, original database, retained input, provider, backup, report,
import or maintenance action is included. This is qualification only.

## Bounds and validation

Reservation: 23 metadata + six outer controls + 13 real-reader calls/controls +
six writer calls/controls = **48 units**. The actor uses nine SQL calls and at most
nine rows; total planned maximum is 146 rows. All original per-result/total row,
receipt, source, manifest, disk, log and version-store limits remain unchanged.
There are at most two actor SQL connections plus the established outer connection;
the cleanup observer opens only after joined child and disposed work are confirmed.

Existing 3-second statement timeout, zero lock wait, 20-second actor watchdog,
25-second parent wait, 30-second work, 42-second cleanup and 45+10-second host
deadlines remain. Manual ceiling is 60 seconds within the remaining 110-second
configuration-test allocation. Actual host time is rounded up and debited once.
This SQL packet does not debit the Windows file/IPC allocation.

The approved update predicates remain validated against authoritative
`C:\K98-bot-SQL-Server\sql_schema\dbo.ExportPreparation.Table.sql` and
`dbo.ExportResource.Table.sql`; the source pins are checked again before handoff.
No SQL repository or production runtime changes occur. A new versioned harness
preserves the already-executed writer-first packet; no production refactor is
introduced. Only exact connection factories and a barrier are adapted.

Eight inert-driver Python tests passed: ordering, unchanged actual reader, exact
old preparation gate, writer identity/change refusal, commit acknowledgement loss,
late drain, mixed reader output and cleanup failures. Commit-unknown tests retain
a simulated committed outcome and prove the cleanup does not claim to undo it.
213 PowerShell checks passed, including remoted values, exact account/source/pins,
all evidence flags, unknown-commit refusal, full budget and physical cleanup gates.
Ruff passed after removing unused test imports and formatting one helper;
architecture passed for two Python files and the explicit selector completed.

Full application pytest, smoke imports, command registration and deployment tests
are skipped because this isolated test tooling does not alter application/runtime,
Discord, dependencies or release paths. Offline tests are not native proof.
Changes review, Deep off, covers all four source/test files plus this plan before
handoff. Original failures and the full saved pre-commit snapshot remain pinned.

## Dependent work

Adjudicate the receipt before any further native operation. Even an acknowledged
commit and consistent old view do not replace a fresh durable read: prepare that
next, requiring 4/23/20 and unchanged other fixture fields. Then submit the saved
actual old full snapshot to the actual settlement boundary once; require
SourceConflict before mutation. Keep these in separate bounded packets if needed
to retain the command ceiling. Preserve the seven final rows as evidence.
D5c and later slices remain open; deployment needs separate release approval.

## Final review and handoff

Changes scan `92ee3b1b-022b-4507-b4d1-9b4ab24acc1d` completed with zero findings,
sealed readback verified. Independent review covered all four source/test files
and pinned supporting packet; the parent reviewed the plan and entire behavioral
delta. No concrete operational blocker was found. All five frozen files match
`e36c9402b3a2ca3a0f312954f27e81d2b464953e`; this final receipt section is added after
that byte verification. Native execution intent remains absent.

Final wrapper SHA256:
`6b165af68266311eca573bbc1c3af57baefb3c8e4d2a09a655092843889d3f8b`.
Manifest SHA256:
`a87af2a9a15b89c04c83d5fb1c5c41b017deb66bea796cea2e2beba2a2987574`.
Preparation receipt: `.codex_artifacts/p025/d5c-config-reader-first-preparation-acceptance.json`.
Review-reported token usage: 2,034,134; no native time or inputs consumed by review.
Deferred-structure and security-routing validators passed. No production/SQL
source changed and no separate SQL-repository scan is required.
