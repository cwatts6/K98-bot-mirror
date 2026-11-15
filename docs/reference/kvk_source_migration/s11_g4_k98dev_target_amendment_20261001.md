# S11 G4 target amendment — existing K98DEV instance

Chris selected `localhost\K98DEV` on the development machine for a newly created `ROK_TRACKER` database and confirmed that no database of that name currently exists there. This supersedes the separate-instance recommendation in `s11_g4_sql_target_resolution_20261001.md`. No new SQL Server instance is required solely to satisfy the database-name contract.

The previous note incorrectly referred to an existing `ROK_TRACKER` on K98DEV. That was an unsupported assistant assumption, not an observed fact. Its requirement for zero user databases also belonged to the proposed empty-instance route and does not apply to the selected shared development instance. Preserve the old sealed packet as historical; do not execute its preflight for this route.

## Current target binding

- Connection endpoint: `localhost\K98DEV`.
- Expected host/instance from retained context: `9SX2VF4\K98DEV`; compare the actual server identity before any mutation rather than assuming that an endpoint alias proves it.
- New database name: `ROK_TRACKER`.
- Name absence: operator-confirmed in this conversation, not independently observed this turn. Recheck immediately before creation and stop on any existing database, including an offline or inaccessible one. Do not attach, rename, restore over, drop or adopt it.
- Operator/reviewer: Chris; existing single-account application model retained.
- DB22 `S11_G4_Recovery_20260928_97337`, DB23 `K98_S11_Disposable_20260929_CV01`, every other existing database and all retained files/receipts remain protected.
- Database ID, data/log paths, collation, file sizing/growth/MAXSIZE, installed metadata and application principal are not inferred from the proposed name.

Keep the production database-name guards. The SQL source's explicit references can resolve to the newly created local `ROK_TRACKER` without changing production procedure bodies. This settles target selection; it does not establish installation acceptance.

## Shared-instance effects to bind

Source review of `20260924_002_export_legacy_module_permissions.sql` confirms that full legacy signing is not database-local. It requires a public-only `S11LegacyImport` certificate in master and creates `S11LegacyImportUser` in master plus certificate-mapped server login `S11LegacyImportLogin`. Its grants include ADMINISTER BULK OPERATIONS, VIEW SERVER PERFORMANCE STATE and EXECUTE on master `xp_cmdshell`/`xp_fileexist`. The migration does not enable xp_cmdshell, configure a proxy or provide private signing keys.

Before this part of installation, use a bounded exact-name metadata read to check those certificate/principal names and relevant grants on K98DEV. Unknown or conflicting existing objects stop that step; do not replace or adopt them automatically. Record any new instance-level objects separately from database-local objects. Dropping the new database would not remove them and is not a complete rollback. Any later reversal must bind original object identities and the reviewed rollback migration; existing objects remain protected.

Import/archive procedures also call filesystem helpers. Review the exact source/staging/archive paths and identities for the selected operation before invoking them. The availability of an unused database name does not authorize shared configuration changes, root procedure execution or file moves. No SQL engine installation, global certificate-trust change or production action follows from this amendment.

## Continuation and evidence

Replace the obsolete empty-instance preflight with a K98DEV-specific packet covering exact server/login identity, complete visibility sufficient to prove `ROK_TRACKER` absence, named signing-object collisions and selected filesystem prerequisites. Existing disposable databases are expected, not a reason to fail. Keep read-only checks distinct from database creation, signing installation and import/export execution, with explicit effects and recovery boundaries for each.

Do not run the opt-in legacy fixture unchanged: its old server-name substring requirement represents the earlier separate-instance assumption. Amend that test gate to a reviewed exact target binding with negative cases before any target-bound execution; do not relax production contract checks or set the fixture's authorization variables merely to make it pass.

All other unresolved installation, cloud/writer, registration/reference and report-expectation bindings remain as listed in the runtime configuration packet. The missing-instance question is resolved and must not be repeated. No live observation, provisioning, SQL/provider operation or gated fixture ran for this amendment. No runtime source changed. The seven typed G4 proofs and G5 remain incomplete.

This is a documentation/target-binding correction based on explicit operator input and authoritative SQL source. Prior sealed documents remain unchanged. New runtime tests and security scans are not warranted for this inert amendment; any later fixture or installation implementation needs its own focused validation and security-routing decision.
