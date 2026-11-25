# P02 D5c configuration acceptance and isolation exception plan

## Configuration fixture accepted

Receipt `d5c-config-stale-refusal-result-808745e734504abf8cb0bbcd4b3f2188.json`
has verified SHA256 `9bc0f8c338f8db89c1c2088abbcca50c5443efa8521dc413f2024c066cb0ff67`.
Saved-evidence adjudication accepted the actual `SourceConflict` with the exact
stale-state message, current full snapshot equal to the accepted fresh 4/23/20
snapshot, zero denied SQL calls and zero commit attempts. The real transaction
acknowledged rollback and connection closure. Protected metadata, resource floors,
normal process exit and independent physical SQL absence all passed.

The packet reserved 44 commands and captured 112 rows. Host time 1.8597087 seconds
debits two. **1,421 native seconds and 50 Windows-test seconds remain; 21 inputs
are consumed.** The configuration scope has 162 seconds unused, including 104
follow-up-test seconds; this does not authorize additional attempts. The committed
transition, extra writer-first attempt and stale-refusal allowance are consumed.
No maintenance retry is available. Seven fixture rows remain as evidence.

The approved configuration fixture is complete: admission, writer-first rollback,
old full snapshot, reader-first committed transition, fresh durable snapshot and
stale-action refusal. This closes that representative case, not all C05/C06 or
D5c. Original failed receipts remain failed. Acceptance is recorded in
`.codex_artifacts/p025/d5c-config-stale-refusal-acceptance.json`.

## Remaining qualification and next proposed exception

D5a and D5b are accepted. D5c still requires wider account/season/queue/pool and
inspector/action coverage, rights/factory cases and native disabled-isolation
proof. D5d fault/restart, D5e balanced cost and D5f reconciliation remain open.
No percentage is asserted because these obligations have different sizes and
several need separately approved environment/fixture changes. D6 release and
D7 live acceptance remain distinct.

The source plan explicitly excluded disabling SNAPSHOT on the retained copy.
The proposed exception is **one OFF/test/ON cycle on the disposable database
K98_P025_D5b_20261111 only**, using the existing principal. RCSI stays OFF. The
original database K98_P021_PreImport_20261107, ownership, permissions, VM resources,
network isolation, candidate modules, retained inputs and all rows stay unchanged.
No new database, user, grant, impersonation, input or workload is included.

The only proposed setting statements are:

```sql
ALTER DATABASE [K98_P025_D5b_20261111] SET ALLOW_SNAPSHOT_ISOLATION OFF;
ALTER DATABASE [K98_P025_D5b_20261111] SET ALLOW_SNAPSHOT_ISOLATION ON;
```

They must execute from an explicitly non-transactional master-context control
connection. No SINGLE_USER, ROLLBACK IMMEDIATE, KILL or session eviction is allowed.
The target remains the existing pinned VM/server/database ID 8 and creation time.
The original read-only database ID 7 must remain unchanged.

## Concrete sequence and acceptance conditions

1. Recheck exact target identity, clean physical custody, current stable SNAPSHOT
   ON/RCSI OFF, no foreign sessions or active transactions on the copy, unchanged
   permissions/modules/protected records, existing ALTER capability and resource
   floors. Close target-bound preflight transactions before changing the option.
   Missing visibility/permission or any foreign activity refuses the test.
2. Persist a create-once host intent and original option state. Issue OFF once,
   under the existing three-second statement limit. Require acknowledged command
   completion and catalog state exactly OFF, never a transition state.
3. On one dedicated existing pyodbc factory connection, call the unchanged actual
   `require_recovery_snapshot_isolation` and require its exact prerequisite refusal.
   Then exercise the unchanged managed-reader path once against the fixed fixture;
   require native error 3952, no successful fixture read, no locking fallback and
   no automatic option enablement. Keep the first refusal distinct from cleanup.
   The factory is called once; startup and reader checks share its owned connection
   only through explicit ownership, never a borrowed producer handle.
4. Acknowledge reader rollback, isolation restoration, close and owned process
   exit before restoration. Issue the one planned ON statement after a stable OFF
   state and verified actor cleanup. Restoration is part of this approved cycle,
   including if the expected refusal assertion fails but cleanup is confirmed.
5. Require stable ON/RCSI OFF, unchanged protected metadata and fixture values,
   resource floors and independent absence of every owned session/process. Native
   refusal evidence is not accepted without confirmed restoration and cleanup.

If OFF is refused before change, stop without a second OFF. If command completion
is uncertain, use only a bounded catalog observation to distinguish stable ON,
stable OFF and transition/unknown. Do not run the reader in a transition state.
The planned restoration may proceed only from confirmed OFF after physical closure;
do not issue an opposite setting command blindly. If ON or cleanup is unconfirmed,
preserve all handles/first evidence, mark the copy unavailable for further tests,
and bring back the exact state. No automatic setting retry, restart or forced
transaction termination is authorized.

SQL Server can wait for existing transactions while this option changes, so the
absence-of-transactions gate and stable-state checks are essential. See
[Microsoft's transaction and row-versioning guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-locking-and-row-versioning-guide?view=sql-server-2017).
The existing native test in `tests/test_recovery_snapshot_native_sql.py` supplies
the expected prerequisite/3952 assertions; its database creation, grants and setup
must not run here. No application/runtime correction is proposed.

## Limits and approval gate

The whole cycle is capped at **60 host seconds**, debited from 1,421, preserving
the final 1,000-second later-phase reserve. It uses no Windows-test allocation.
All existing caps remain: 48 client-command units across every actor/control and
cleanup path, 512 rows per result, 2,048 overall, 1 MiB receipt, existing staged-file
and manifest limits, fixed 8 GiB/4 CPU VM, zero adapters, 8 GiB disk reserves,
log below 70% and version store below 512 MiB. No retry allowance is refreshed.

Before any console handoff, prepare the exact source/manifest, freeze the complete
command ledger including restoration and failure cleanup, test all transition,
timeout and restoration-refusal paths offline, and complete Changes review with
Deep off. If the ledger or cleanup cannot fit the unchanged bounds, do not execute;
report the preparation blocker. This document is a scope proposal, not an executable
packet or a claim that the proposed tests/review have already passed.

Approval is required because earlier authorization explicitly preserved database
isolation settings and reserved this exception. The requested addition is only
this one cycle and its bounded preparation. Remaining rights/fixture exceptions,
new maintenance, deployment and replay remain outside it.

This turn changes local saved-evidence adjudication and documentation only. New
security discovery and runtime tests are skipped for this source-only proposal;
the future executable packet requires its own focused Changes review. No new
runtime refactor or deferred optimisation item is introduced.
