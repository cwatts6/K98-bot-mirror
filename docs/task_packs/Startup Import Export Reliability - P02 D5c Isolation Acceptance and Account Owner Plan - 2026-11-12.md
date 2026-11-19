# P02 D5c isolation acceptance and account-owner-first plan

## Accepted C10 evidence

The saved receipt `d5c-isolation-off-result-331dc98e08a24d5187fe77b6611f25f3.json`
has verified SHA256 `2c806c7f73c4f564c7849c71eadfb23d334d3a80b88b20f0e4ac7be66d8523cf`.
Saved-evidence adjudication confirms exact startup refusal and actual native
SQLSTATE 42000 / 3952 at the first fixture read, followed by acknowledged reader
cleanup and one restored SNAPSHOT ON state. RCSI stayed OFF. All four option
observations preserve the complete seven-row fixture hash
`308ABE68AE0EFADA2BDA217282B0E14C03824026B377C93084DF7F9D4783042E`.
Protected records, original database protection, candidate definitions,
permissions, ownership, resource floors and independent physical SQL absence pass.

There were 47 reserved commands, 108 returned rows and a 25,889-byte receipt.
Host elapsed 1.7095893 seconds debits two: **1,419 native seconds and 50 Windows
test seconds remain; 21 inputs remain consumed.** The one isolation cycle is
consumed, with no retry. No maintenance, writer or stale-action retry is available.
Acceptance is saved in `.codex_artifacts/p025/d5c-isolation-off-acceptance.json`.
C10 closes; broader D5c, D5d-f, D6 release and D7 live acceptance remain separate.

## Next existing-scope case: C01 account owner first

Use the same pinned VM, SQL server, disposable copy and existing seven-row
configuration fixture at versions 4/23/20. This is within the already-approved
lock-only D5c scope: no new rows, settings, permissions or demand. No runtime
correction is proposed. The original no-new-input and production boundaries remain.

1. Preserve the existing 23 metadata checks, identity/resource/source pins and
   create-once intent. Require the accepted isolation receipt and original history.
2. One isolated process opens a dedicated holder connection, verifies exact
   identity and calls the unchanged `_mutex` for exactly
   `account:d5c_config_20261112`, Transaction owner and zero wait. The actual
   `coordination_lock_name` supplies its SHA256 resource. No business action runs.
3. While that holder remains open, one separate actual reader factory calls
   `ConfigPreparationRecoveryDAL.target_data` for the existing preparation and
   exact account/storage owner. Require its complete result to equal the accepted
   current fixture target. The actual helper owns SNAPSHOT and schema guard cleanup.
4. After acknowledged reader closure, the holder reads its exact APPLOCK_MODE,
   session ID and transaction state once; require Exclusive and its same captured
   identity. This proves overlap from ordered operations, not timestamp proximity.
5. Roll back and close the holder without retry. Require both distinct SQL births,
   successful physical cleanup, normal actor exit, unchanged protected records,
   and independent absence of all connections with the packet application name.

Maximum accounting is 23 metadata + six outer connection/cleanup units + 19 actor
units = **48**. The actor reserves eight SQL calls, two opens, three rollbacks,
two autocommit transitions, two isolation operations and two closes. Returned
rows are at most seven for the actor plus the existing bounded metadata. No cap
increases. Whole packet 60 host seconds; three-second SQL statements; two SQL
actors plus the existing metadata control, then a closure observer only after
work disposal. Holder duration remains below 30 seconds under the actor watchdog.
Any failure stops the case; no repeat or automatic alternate factory is allowed.

The full inspector/closure-verifier paths and reader-first account ordering are
distinct later cases. This target-data check must not be reported as complete C01.
Restricted-rights cases still lack a mapped authenticated restricted principal;
the earlier inventory showed four orphaned application users. No impersonation,
new login or grant is authorized. Season/queue/pool fixtures still require exact
separate plans before committing rows.

## Preparation and validation

Operational Python/PowerShell tooling and inert tests only, following the existing
snapshot packet. Reuse unchanged production module bytes and native bindings;
carry the reviewed uncertain-process-launch correction into the new wrapper.
Validate fixed fixture object/column names against the authoritative SQL files
already pinned in the manifest. No SQL repository modification is needed.

Tests must cover real `_mutex` and reader invocation with inert drivers, exact
key/hash/rows, wrong holder/reader identity, missed lock, dirty target, reader and
holder cleanup failures, no retry and cumulative command accounting. Review the
PowerShell remoted result shapes and both physical-closure gates. A frozen Changes
review with Deep off is required before console handoff. No native attempt is
authorized by an unreviewed generated packet. No new deferred refactor is proposed.

## Prepared packet

The packet is `scripts/run_p02_d5c_account_owner_first.ps1`, with actor
`scripts/p02_d5c_account_owner_first.py` and manifest
`.codex_artifacts/p025/d5c-account-owner-first-execution-packet.json`.
Wrapper SHA256 `388e74a7fde8067e758af22be61eef6d8ea17ff15f06b1a8fe2ff191fc3e845e`;
manifest SHA256 `efc8ecfa7d1ff484245dec5c19b28394cfade36a7fac2bb54890ac9cfa52cc29`.
The fixed account lock is
`k98-export:9bb48dc5214342dbdefc2e77221c3954044791b25461e87f52a5d1aa7a4a394e`.

Eight isolated Python tests passed against actual `_mutex`/DAL/helper modules with
inert connections; 221 PowerShell checks passed. Coverage includes both SQL births,
one factory invocation each, exact target/hash, missed owner, wrong identity,
reader/holder cleanup failure and refusal of incomplete or reordered evidence.
The validator initially retained the previous snapshot's ten-row actor expectation
instead of this seven-row expectation and stopped offline. That copied test
expectation and its old suballocation labels were corrected; limits were not raised.
The initial failed output is preserved in the tool history. No native attempt ran.

The manifest is 127,996 bytes within 128 KiB, with at most 144 planned returned
rows and a 1 MiB receipt. Actual holder acquisition uses the unchanged `_mutex`;
expected contention is not retried. The holder does not release after uncertain
reader cleanup. Process start intent/handle checks and additional failure-cancel
accounting are carried from the corrected reviewed isolation wrapper. No isolation
setting statements are copied into this packet.

Ruff and repository architecture/deferred/security-routing validators passed.
The test selector ran. Broad pytest, app smoke imports, command registration and
release/permission-repair suites are skipped because only isolated qualification
tooling changed; focused inert tests cover the actual unchanged helper behavior.
The initial five-file Changes review `0097fcc8-2de8-48ce-97da-4cb85ca50002`
completed with no reportable security findings, but identified a qualification
blocker: two lazy diagnostic imports were missing from the test bundle. An
unexpected mutex refusal would lose its native error attribution. That review,
initial immutable snapshot and original manifest remain preserved.

The correction adds the unchanged `legacy_snapshot_admission` and
`sql_lock_holder_diagnostics` modules, preserves structured first-failure facts
and up to three causes separately from cleanup errors, and tests native mutex
refusals -1/-2/-3/-999 plus native failure with uncertain cleanup. The expanded
19-module bundle is 318,932 bytes within 320 KiB. Diagnostic handling for this
exact long hashed resource returns `resource_name_truncated` without extra SQL;
the command and row caps remain unchanged. Production modules are not modified.
The corrected immutable Changes review must complete before console handoff.
