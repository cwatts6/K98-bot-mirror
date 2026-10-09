# R02 / R03 — final recovery and integrity proposal

PREPARED, NOT EXECUTED. Exact operator approval required for these new effects. Chris Watts remains operator/reviewer/abort owner. Existing window expires 2026-09-29T09:23:23Z; no renewal requested. User confirms remaining R01 results correct. Preserve that attestation alongside complete 119 ordered successful engine Messages and aggregate R01 results; missing individual timestamp grids remain an archival limitation, not fabricated evidence or reason to rerun the successful restore.

## Target and source evidence

Development only, existing SSMS localhost\K98DEV, fresh query window in master, Windows Authentication. Guards bind server 9SX2VF4\K98DEV, machine 9SX2VF4, instance K98DEV, observed MicrosoftAccount\cwattsconsulting@outlook.com original login, sysadmin 1 and engine major 16. Clear transaction/implicit state required.

Only database ID 22, S11_G4_Recovery_20260928_97337. Exact files under C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11_G4_20260928_97337\data:

- S11_G4_Recovery_20260928_97337.mdf; logical ROK_TRACKER, ID1 ROWS, 2,226,560 pages.
- S11_G4_Recovery_20260928_97337_log.ldf; logical ROK_TRACKER_log, ID2 LOG, 8,388,608 pages.

R01 ended RESTORING, 119 sets applied, 174908 ms, 1,655,566,852,096 free bytes. Staged media is not read or recopied by this packet. R02 binds 119 ordered restorehistory rows joined to backupset, exact UUID/type/first+last LSN and recovery=0. The final expected backup LastLSN is 19088000155032800001. These are consumed-backup history comparisons, not a claim that the recovered database exposes that value as its current last LSN. No match by filenames alone.

## Commands and hashes

Commands are under C:\discord_file_downloader\.codex_artifacts\s11-g4-capture-preparation-20260926\commands.

| Operation | File | SHA256 |
|---|---|---|
| R02 | R02.sql | e42ecc27e1c0cc5b1431cac5d12fbbe356289071479d081173ddf10733a97b24 |
| R03 | R03.sql | 331a1a143fc11090abd21c2e060f38baa3c22c27327559eed0c9f060add041d4 |

### R02 — one final recovery and read-only transition

One attempt after approval, query timeout 600 seconds, operator cancel at 610 seconds, cooperative post-call budget 600 seconds, output <=64 KiB. Execute the whole unchanged file in a fresh master session. Guard database ID/name, exact two files/sizes, RESTORING, Broker disabled, 100 GiB free on C:, all 119 restorehistory rows and the 21 retained database/49 retained file identities. Existing exclusions are read-only.

Exact mutations:

```sql
RESTORE DATABASE [S11_G4_Recovery_20260928_97337] WITH RECOVERY,RESTRICTED_USER;
ALTER DATABASE [S11_G4_Recovery_20260928_97337] SET READ_ONLY WITH NO_WAIT;
```

The ALTER occurs only after ONLINE/RESTRICTED_USER/Broker-disabled postconditions pass. Recovery performs undo and writes data/log/engine metadata; it completes this historical recovery endpoint so further logs cannot simply be appended. No source media restore, overwrite, schema installation, grants, principal edits, repair, DROP, KILL, ROLLBACK IMMEDIATE or cleanup. NO_WAIT fails if the read-only transition cannot acquire access immediately; no other session is terminated. Failure can leave the database recovered but writable: preserve and report that state, do not rerun the recovery batch or assume rollback.

Service Broker remains disabled using the documented restore default; no ENABLE_BROKER, NEW_BROKER or ERROR_BROKER_CONVERSATIONS is issued. DISABLE_BROKER is not a RESTORE option and is not used. Explicit pre/post catalog checks enforce the expected disabled value. RESTRICTED_USER still permits db_owner/dbcreator/sysadmin, so it is not absolute isolation from privileged concurrent writers. Admin keeps this exact target unused during the brief recovery/read-only transition. No application connection or Agent schedule is changed. The final read-only setting is a deliberate option change on this restored copy, not a byte-identical database-options claim.

R02 rechecks retained database/file identity sets after recovery; returns restored flags including trustworthy/chaining, exact file rows, matched history count/IDs, free bytes and elapsed marker. Identity-set comparison is not original-row preservation proof. Capture all Results and Messages. Reconcile R02 before proceeding to already-approved R03; partial completion means stop.

### R03 — full CHECKDB and bounded metadata inventory

One attempt only after accepted R02 output. Fresh master session, query timeout 1800 seconds, operator cancel at 1810 seconds, cooperative elapsed check 1800 seconds, total accepted output <=128 KiB. Identity, ID22, exact file sizes/mappings and ONLINE/RESTRICTED_USER/read-only/Broker-disabled state required; 100 GiB free floor before and after.

```sql
DBCC CHECKDB ([S11_G4_Recovery_20260928_97337])
WITH DATA_PURITY,NO_INFOMSGS,ALL_ERRORMSGS,MAXDOP=2;
```

No repair, PHYSICAL_ONLY, NOINDEX or TABLOCK shortcut. This is standard full CHECKDB with data-purity checks, not a claim that every specialized extended logical check runs. MAXDOP2 bounds requested parallelism, not total memory or I/O. CHECKDB reads database pages, uses tempdb/work memory and may create engine-managed internal sparse snapshot files alongside the data file; normal engine cleanup of its own transient artifacts is expected, no manual cleanup is authorized. It can update internal diagnostic metadata and engine logs. Existing database allocation is ~81 GiB; actual checked content and tempdb/snapshot usage differ. The 100 GiB floor is a sampled guard, not a quota or mid-call resource watchdog. Blocking calls may outlast cancellation; wait for control return, do not kill SQL Server.

After CHECKDB returns, capture exact object presence/type and column metadata (names/types/length/precision/scale/nullability) for 13 source-confirmed tables only: dbo.ExportJob, ExportAttempt, ExportAttemptPart, ExportResource, ExportExecutionSession, ExportExecutionStream, ExportManagedFileOrigin, ExportProviderRequest, ExportProviderRequestEvent, ExportReconciliationProof; KVK.SourcePublication, SourceDelivery, SourceExportIntent. Missing objects are returned as absent; do not create them. No business rows, receipt payloads, keys, passwords, provider credentials or module bodies are selected. These observed shapes support the later preservation-baseline query; no schema inferred from Python.

The completion marker says inspect Messages. A returned command is not proof of zero corruption: all errors/warnings and Messages must be retained and reviewed. Accept integrity only after complete error-free output; do not treat suppressed informational output as a missing successful command. No repair on error.

## Shared stop / retention requirements

Wrong identity, changed database/path/size/history/state, retained identity drift, unexpected writer, error/warning, time/space/output ceiling or incomplete evidence stops the affected group. No automatic retry, cleanup, recovery reversal, repair, DROP, restore-over-existing or permission workaround. A timeout can leave a completed or partial effect with no receipt: reconcile state with separately approved exact reads. Keep files, media, prior evidence and the restored copy. Reset SSMS query timeout to 10 seconds after each operation returns. Capture/save all Results and Messages immediately, including client completion time.

## Remaining acceptance boundary

Successful R02 and R03 would establish actual final recovery and standard integrity-check evidence for this historical copy. They do not prove byte-exact preservation against a missing historical business-row baseline, or installed S11 capabilities. Before installation/tests, prepare source- and observed-shape-bound row/receipt/fence fingerprints with a concrete output/runtime budget, retain original values/uncertain publication identities, and compare around later authorized changes. No current-production comparison is substituted for this historical endpoint. All seven typed G4 proofs, provider/writer/identity gaps, rollout and G5 remain incomplete/unapproved. Memory cause stays deferred and the collector withdrawn; KVK report and view warning remain separate retained issues.

## Local validation / review

Checked exact 119 manifest UUID/LSN pairs and sequence, one RECOVERY/RESTRICTED_USER statement, one no-wait READ_ONLY transition and one non-repair CHECKDB. Exact two file paths appear in both guarded commands. No GO, destructive cleanup, backup, overwrite, repair or server/process termination. SQL not compiled/executed live; source/static review is not runtime proof.

Authoritative SQL restore source: performance_remediation/kingdomscandata4/phase1/update_all2_rehearsal/15_restore_update_all2_benchmark_database.sql uses msdb.restorehistory/backupset for consumed-media binding; phase2/05_restore_preflight_backup_to_recovery.sql confirms restore mapping/history conventions. Thirteen table names verified in C:\K98-bot-SQL-Server\sql_schema; only system catalog shapes queried here. No predecessor script executed or SQL-repo edit made.

Security routing: preparation-only documented skip for generated exact operator-review artifacts; no deployed runtime/config/permission change by authoring. No broad security audit, PR or publication. Runtime tests and PR validators skipped for this local operational proposal; static allowlist/sequence checks performed. Prior sealed proposals/receipts remain unchanged.

[Microsoft RESTORE arguments](https://learn.microsoft.com/en-us/sql/t-sql/statements/restore-statements-arguments-transact-sql?view=sql-server-ver16) documents restricted recovery and Broker-disabled default. [Microsoft CHECKDB](https://learn.microsoft.com/en-us/sql/t-sql/database-console-commands/dbcc-checkdb-transact-sql?view=sql-server-ver16) documents data-purity, parallelism and internal snapshot behavior.
