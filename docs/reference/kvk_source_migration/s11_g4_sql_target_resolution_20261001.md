# S11 G4 SQL target resolution — 2026-10-01

The database-name mismatch is explained by real source dependencies. Retain the production guards. Continue full legacy validation on a separately bound disposable SQL Server 2022 instance with its own `ROK_TRACKER` database. This is the selected preparation direction, not an installed target or completed G4 proof.

This finding narrows the two alternatives in [the runtime configuration packet](s11_g4_runtime_config_packet_20261001.md). Removing the two Python comparisons is not a sufficient development-target fix. No Bot or SQL runtime source was changed in this investigation; all earlier pending changes and seals remain intact.

## Evidence and implications

The new finite offline audit is `.codex_artifacts/s11-sql-target-resolution-20261001/source-audit.json`. It verifies every member of the 540-object application inventory against authoritative SQL source. The canonical source-list digest remains `f082cd0cbf28261cddf966a954a4564d34a81a552d796707eb90dc75a6baf3cf`.

Beyond SQL export `USE` headers, three source objects contain literal database references:

- `dbo.GOVERNOR_NAMES_PROC` reads `ROK_TRACKER.dbo.KingdomScanData4`.
- `dbo.UPDATE_ALL` reads multiple `ROK_TRACKER.dbo` delta objects.
- `dbo.CaptureLogHealth` assigns `ROK_TRACKER` as its database target.

The Bot lifecycle DAL also has an explicit `ROK_TRACKER.dbo.kingdomscandata4` query. Legacy permission validation binds database names in certificate/principal/grant expectations as well as its initial guard. The signing migration `20260924_002_export_legacy_module_permissions.sql` requires `ROK_TRACKER`, SQL major version 16, separately supplied signatures and an exact deployment binding.

The retained legacy manifest's seven roots reach 37 declared modules. Its external calls include `master.dbo.xp_cmdshell`, `master.dbo.xp_fileexist`, dynamic SQL and application locks. This is a manifest call-graph observation, not a full dependency or side-effect analysis. It is sufficient to reject a validator-only database-name amendment. Do not globally replace `ROK_TRACKER`, install source snapshots en masse, enable xp_cmdshell, configure a proxy or run an import root as a metadata check.

The opt-in legacy SQL fixture already describes a separate disposable instance. Its current string-based target gate must be reconciled with the eventual exact instance identity before use; it is not authorization or proof of isolation. No gated fixture ran.

## Bounded continuation

1. **Bind the instance.** An exact existing disposable instance has been requested from Chris. If none exists, prepare an engine installation proposal using identified, verified installation media, exact service identity, dedicated data/log/temp/backup paths, storage allowance and resource limits. No instance name, path or media is presently reserved. Do not adopt `9SX2VF4\K98DEV`, its existing `ROK_TRACKER`, DB22 or DB23 for this full legacy route.
2. **Review a target preflight.** `working/target-preflight.sql` is an inert draft with null expected server/login. It refuses execution before any catalog query until those bindings are filled. Its later checks require master, SQL major version 16, the exact server/login, no existing transaction, complete database visibility and zero user databases. This is only one prerequisite: it does not establish filesystem isolation, instance settings, permissions, signing material or writer exclusion.
3. **Build the installation subset.** Derive prerequisite tables, UDTs, modules, dynamic outputs and configuration from the chosen report/import path and reviewed sources. Preserve the successful minimal DB23 rehearsal. The 540-object inventory remains an application comparison contract, not an installation list. Do not weaken full-runtime acceptance to make a minimal subset appear complete. Full application acceptance and a limited process demonstration must remain separate scopes.
4. **Bind signed-module prerequisites.** Exact public certificate pins, exported signature blobs, login/role/grant expectations and the signing migration's deployment inputs remain required before installation. No new Google identity/key is involved. Local-only TrustServerCertificate remains a connection-specific exception; it does not imply a production TLS change.
5. **Run only the later exact approved packet.** Installation, rehearsals and actual exports need complete executable commands and budgets tied to the new target. No engine installer or migration invocation is supplied here because their required identities, paths and inputs are unresolved.

## Commands, budgets and outputs

Executed locally, once:

```powershell
& 'C:\Program Files\Python311\python.exe' -I -S -B .codex_artifacts/s11-sql-target-resolution-20261001/working/audit_target.py
```

The audit reads the fixed 540-member inventory, its listed SQL files, the legacy manifest, four named Python source/test files and one named migration. Each read is capped at 4 MiB. It does not import application modules, open credentials, inspect a running service, connect to SQL or call a provider. It writes one exclusively created JSON report containing source hashes, literal-reference line locations, manifest graph results and explicit limitations. Observed shell duration was approximately 0.89 seconds; no resource watchdog or global memory quota is claimed. SQL rows/locks, network requests and target storage effects were zero. The literal scan is not a SQL parser and must not be used as a complete installation dependency resolver.

The preflight SQL draft has **not run**. Before any later execution, seal a fully bound copy and its launcher. Proposed launcher limits: one connection attempt, 5-second connection timeout, 10-second command timeout, 15-second external deadline, 2-second SQL lock timeout, at most one returned row, 64 KiB stdout and 16 KiB stderr, 1 MiB evidence storage. These are proposed limits, not controls implemented by the SQL file. Stop on timeout, identity/version/visibility mismatch, any user database, truncation, unexpected result or unknown child outcome. Do not retry blindly. It performs no DDL/DML; on failure preserve receipts and close the connection. No rollback is needed for its catalog reads. Engine provisioning and installation need their own materially larger reviewed budgets.

Complete working and sealed command copies, per-file SHA256/size bindings and this document are listed in `result-seal.json` under the artifact root. All historical command copies, failed attempts, source seals, DB23 rows, DB22 and its 119 media files are preserved. No active configuration was edited.

## Remaining acceptance

This completes the source investigation of the target-name issue. It does not complete installation or the overall validation. The exact disposable instance is the immediate missing fact. Installation source closure/signing, cloud IAM/key metadata, both known credential holders and writer closure, actual runtime identities, complete protected-file references and independent report expectations remain open as recorded in the runtime configuration worksheet. They are not questions to re-ask about already settled preferences.

The seven typed G4 proofs remain incomplete. Historical provider reads, restored database integrity, source tests and this static audit are not current installation/provider/G5 acceptance. Real two-export execution, production rollout and G5 remain separate decisions. No production or provider action occurred.

Skills: K98 architecture scope, SQL validation and test selection. For this new source-only audit/documentation scope, no application tests were rerun; the offline audit checks hashes and Python syntax without importing source. Architecture/deferred/security-routing validators and a new Changes scan are skipped because there is no new runtime, SQL, permission or deployment implementation change and no PR handoff. The unbound SQL file is review material, not an approved operational command. Earlier review limitations and test failures remain retained.
