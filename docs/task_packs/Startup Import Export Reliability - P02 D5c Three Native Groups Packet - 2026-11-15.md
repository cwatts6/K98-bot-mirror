# P02 D5c: three remaining native groups

Status: prepared for frozen review; no native execution or acceptance claimed here.

The accepted baseline is 73/73 scoped offline recovery routes and 9/12 D5c families. The remaining native packet contains 18 scenarios: six C04 configuration schedules, nine C05 coordinated/discovery reads, and three C06 stale final-action refusals. Native evidence and physical cleanup must be adjudicated before these families close.

## Authorization and preservation

The operator requested completion of all three groups, authorized needed limit extensions and additional bounded passes, and specifically selected a separate clean test database for the unowned-hold check. The canonical retained owner cannot be disturbed to manufacture an unowned state.

Use the existing isolated VM and disposable database `K98_P025_D5b_20261111` only for labelled configuration, queue, pool and discovery fixtures. Create one new empty database `K98_P025_D5c_Hold_20261115` on the existing qualification disk solely for the pure stale-hold refusal. Do not copy retained data to the new database, change the original database, retry maintenance/writers/isolation tests, import/replay inputs, call providers, execute business recovery, deploy, or modify existing permissions.

The new database retains 32 source tables, 25 indexes and all 81 transitive foreign keys, with original CHECK constraints and the original import-lock procedure. Foreign keys are applied WITH CHECK after tables exist. No constraint is disabled or omitted. The new empty database receives its own lock role and SNAPSHOT setting; existing database settings and permissions remain unchanged. Data/log files start at 16/8 MiB, have no automatic growth, and remain evidence; there is no deletion path.

The copy receives 55 exact labelled metadata rows under `d5c_final_20261115`; the clean database receives one hold row. The historical consumed total remains 11 until acknowledged creation; successful setup raises it to 67. The exact required synthetic ceiling is extended from64 to67 under the operator's broad extension approval. The original21-input allowance remains consumed, with zero new inputs.

## Frozen limits and sequence

- Native allowance before execution:1260 seconds; later-D5 reserve:1000 seconds.
- Whole host packet:240 seconds, leaving at least1020 if fully consumed. Worker230 seconds plus10-second stop/join ceiling. No retry.
- Child absolute startup-relative work ends by180 seconds, cleanup by190 seconds and process watchdog by200 seconds. Start is refused after15 guest seconds. Guest work/cleanup ceilings220/225 seconds. Each scenario30 seconds, statement3 seconds, connection5 seconds; admission reserves the longest call before case expiry.
- Combined2448 SQL/control operations:2400 reserved for child (including512 cleanup),48 outer. Failed/unreadable child output does not refund reservations.
- Combined4096 returned rows: child1536, outer at most2048, each command512. The extension retains the full original catalog checks rather than dropping evidence.
- Manifest768 KiB, each staged native file256 KiB, encoded source bundle128 KiB, expanded source512 KiB, stdout/stderr600 KiB each, combined final receipt1 MiB. Files and sources are pinned by SHA256. The manifest measures approximately560 KiB.
- VM8 GiB/4 CPUs/no network unchanged. Host/guest disk reserves8 GiB, log under70%, version store below512 MiB. Windows-test allocation remains50 seconds.

The wrapper verifies exact session/VM, prior receipts, source hashes, original history, old fixtures, candidate definitions, ownership, ledger, permissions, resources, canonical retained owner and full captured catalog before launching one isolated child. Setup identities and files must be absent. The new schema is built and verified before copy fixture admission. Copy admission is atomic; cyclic membership is filled before commit and every proposed column is checked. Unknown commit or failure stops the sequence without replay.

C04 runs season, routing and weights in both orders. C05 runs queue, pool, recovery and hold snapshots in both orders, then standalone discovery under a rolled-back writer. Reader-first cases commit only proposed version changes after a first-fetch barrier and require both the old consistent view and a fresh new view. C06 changes one version before each original guarded action and requires its exact stale refusal. A transport firewall rejects unexpected write/commit paths and treats reaching them as failure, never as a valid stale refusal.

The hold stale-token test proves eligibility before and at the action, a changed digest, exact refusal, no disposition and unchanged fresh state. It cannot use the retained copy because that owner would cause an earlier refusal. The copy's canonical owner and original producer remain exact; only the new labelled producer may be added and versioned.

The original DAL source bodies and recovery-snapshot guard are bundled unchanged. Scheduling barriers are confined to transport adapters. Dependency stubs deny workbook parsing/default connections; they do not substitute query results. Metadata fixtures are not provider-publication or imported-payload proof.

Every case checks original custody, closed owned connections, absence of transport/barrier failures, writer completion and deadline. Original errors, cleanup errors, masked exception chains and swallowed writer-barrier failures remain in receipts. The wrapper joins the exact owned process, disposes its own SQL connection, then independently checks captured SQL birth and all child application sessions absent through master. No unrelated process or SQL session can be terminated. Failure retains evidence and custody, never admits another case.

## Validation and review

Focused checks cover original source bootstrap, fixture mandatory columns/types/keys/FK relationships, original complete-selection validation, guard denial, deadline/cleanup boundaries, failure preservation, transport errors, exact case sequence, process identity, uncertain commit and session closure. The first offline wrapper failure is preserved in `d5c-native-final-offline-initial-failure.json`; scalar handling was corrected without weakening comparisons. SQL CHECK expressions are additionally reviewed against authoritative sources; source-only validation does not claim engine execution.

Run the architecture, deferred-item, test-selection and security-routing validators on this packet. Full application startup, command registration and unrelated runtime suites are skipped because this is isolated qualification tooling and unchanged original-source packaging; importing live application setup is outside this offline pass. No production behavior changes.

Security routing: Changes review of the immutable packet and supporting test/build files, Deep off, Bot repository only. SQL repository source files are read and pinned, not edited. Required review covers exact-target SQL setup/mutation scope, runtime/package integrity, owned-process deadline/cleanup, preserved evidence and false-pass prevention. Native handoff follows completed review, never merely test success.

No deferred optimisation items were introduced. No runtime correction, deployment or unrelated refactor is included.
