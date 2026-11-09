# RP01 / R01 — exact development restore proposal

PREPARED FOR OPERATOR APPROVAL. Not executed. Chris Watts is operator, reviewer and abort owner under the settled single-account model. Preparation approval does not authorize this new restore effect. Existing window expires 2026-09-29T09:23:23Z; no scheduling question is reopened.

## Current evidence and scope

ST04 matched all 119 staged files to source hashes (2,815,180,800 physical bytes). M02 matched 119 headers and 238 file rows, including full UUID, database/family/fork and chain LSNs. V01 accepted 119 media verifications with original-path warning qualification; V02 approved repeat at 16:52:52Z verified the exact two development MOVE destinations, valid backup message and no supplied warning. PD01 created the data directory; its later inherited local-account ACE is retained in the PD01 reconciliation, not silently normalized to ST02. Original incomplete V02 output remains preserved. Nothing here upgrades these observations into actual recovery or typed G4 proof.

One read-only filesystem preflight followed by one SQL batch restores the full and all 118 logs WITH NORECOVERY. This is real database/file creation and redo work. It intentionally ends RESTORING: no final recovery, user access, application execution, migration or tests. No production access. The separate final-recovery/integrity decision is described below and not included in this approval.

## Exact target / commands

Connection: existing development SSMS localhost\K98DEV, Windows Authentication, fresh query window in master. Expected server 9SX2VF4\K98DEV, machine 9SX2VF4, instance K98DEV, original login MicrosoftAccount\cwattsconsulting@outlook.com, sysadmin 1, engine major 16. Existing transaction/implicit state must be clear.

Database: S11_G4_Recovery_20260928_97337 (must be absent).

Root: C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11_G4_20260928_97337

Files only:
- data\S11_G4_Recovery_20260928_97337.mdf mapped from ROK_TRACKER, file ID 1.
- data\S11_G4_Recovery_20260928_97337_log.ldf mapped from ROK_TRACKER_log, file ID 2.

Source: the 119 literal staged media paths in staging-restore-targets-draft-20260928.json. No directory scan, filename sorting, glob selection or new backup. Full set 97337 UUID 70E5C6BF-4A0A-4A48-B6F1-E6E653E8A36D, then log sets 97338–97455 in manifest order. Endpoint last LSN 19088000155032800001 is historical, not current production. R01.sql contains every literal restore operation and media identity guard.

| Operation | Command under .codex_artifacts/s11-g4-capture-preparation-20260926/commands | SHA256 |
|---|---|---|
| RP01 | RP01.ps1 | e7a2d56b9e12775dfeeb75ac1da8ce91b46e828fa0fb2cf2dce14f834e51539d |
| R01 | R01.sql | 97fb8a69752e5e7f8707aff3c180d98f694fc176d4cb0567fa2cd35bb27534d1 |

1. After exact approval, execute RP01 once on 9SX2VF4 using a hash-checked saved-file launcher. It reads eight directory boundaries, exact PD01 data ACL equality, C: ready NTFS/free space, and both target-file absence checks. No directory creation or ACL changes. Capture JSON and reconcile before R01. Reparse/access/ACL drift or existing target stops; do not repair permissions or rerun PD01.
2. After accepted RP01, open unchanged R01.sql in fresh development SSMS master. Set query timeout 1800 seconds. Execute entire file once; do not select individual statements. The batch repeats accepted identity and clear transaction guards, expiration, target database/catalog and physical absence. Physical check uses xp_fileexist as already used by authoritative local SQL restore source, and expects all three return fields. Unsupported result shape fails before restore. All 21 retained database identities and 49 file identities must still match the historical exclusions; no name is disposable based on naming alone.
3. R01 samples C: available bytes via sys.dm_os_volume_stats against master files. Require >=250 GiB before starting and >=100 GiB before each member and at completion. Then read each staged header into a temp table immediately before its restore: exact set UUID/type/position/LSNs/database/family/fork/checksum/encryption/damage flags. This is a mutation precondition recheck, not a rerun of the prior verification suites. No new cryptographic whole-file hash is claimed; accepted ST04 and verification evidence remain point-in-time evidence and media must remain untouched.
4. Full restore uses FILE=1,NORECOVERY,CHECKSUM,STOP_ON_ERROR and both MOVE clauses. Each log uses FILE=1,NORECOVERY,STOP_ON_ERROR; logs had no recorded backup checksum, so no unsupported CHECKSUM claim is made. SQL enforces log-chain application. No WITH REPLACE, RESTART, CONTINUE_AFTER_ERROR, overwrite, DROP, ALTER, final RECOVERY or cleanup.
5. Each completed member emits a receipt. Before each log, same newly assigned database ID/name and RESTORING state are required. Final checks require exactly the approved two file mappings, RESTORING state, and unchanged pre-existing database/file identity sets in both directions. Existing data rows are not read by these identity checks; do not describe catalog equality as row preservation proof.

## Effects / budgets

RP01: at most 10 seconds cooperative, operator cancel 15 seconds, 16 KiB output. No live operations were performed during preparation.

R01: creates one database and two files, writes restore history in msdb and normal engine logs/catalog metadata, allocates/initializes database storage, reads/decompresses media and applies redo, uses session/tempdb metadata. Initial MDF 18,239,979,520 bytes + LDF 68,719,476,736 bytes = 86,959,456,256 bytes (~81 GiB). With retained media and 64 GiB headroom the planning footprint is 158,494,113,792 bytes. Logical backed-up content across chain is 16,410,722,304 bytes. Engine memory/I/O and redo writes are not hard-capped; log initialization can take substantially longer than VERIFYONLY. Captured max file sizes are not the expected allocation or a quota. Space floors are sampled, not reservations; abort can leave allocated files.

Full/header step cooperative elapsed budget 900 seconds, each log/header step 120 seconds, total batch 1800 seconds including preflight. Per-step checks occur after calls and cannot interrupt a blocked call. SSMS timeout 1800 seconds is for the whole batch; operator cancels an observed full step at 910 seconds, any log step at 130 seconds, or whole batch at 1810 seconds, whichever threshold is first reached. Progress messages identify each step. After cancel, wait for control return; do not kill service/process or assume cancellation rolled back allocation. Reset query timeout to 10 seconds after control returns. No attempt starts outside approved window. Output budget 256 KiB (receipts + all Messages); excess/incomplete output stops acceptance.

Any guard/error/warning, unexpected target/writer, space/time limit, failed identity comparison or missing receipt stops the group. If SSMS displays a warning during an in-flight step, cancel and retain the result. Catchable SQL failures emit attempted set and completed receipts; client cancellation may bypass CATCH. Preserve Messages even if completion is printed. Do not automatically resume from the next set, rerun the batch, recover, drop, delete files, overwrite or perform rollback cleanup. Preserve the partial database, staged media, data directory and session output; next action requires exact observed-state reconciliation. The batch is not atomic.

Operator keeps this newly named target free of concurrent manual/automated restores or maintenance and does not modify the media. Guards are point-in-time checks, not an exclusive fence against another sysadmin. There is no application connection change or Bot restart. Existing development SQL Agent jobs are not disabled or authorized to touch this target by this packet.

## Evidence / acceptance

Retain RP01 JSON; R01 identity, preflight free bytes, all 119 per-set receipts, final database/file rows, final free bytes/count/elapsed marker and complete Messages/client completion. Copy/save Results and Messages immediately before navigating away. Original failed/partial output must be retained. Engine completion messages plus application receipts should agree on all 119 members; no warning or unexplained missing row may be ignored. Assistant reconciles supplied evidence against the sealed order/hash.

R01 completion accepts only the NORECOVERY chain-application stage. It is NOT recovered database acceptance, integrity evidence or any of the seven typed G4 proofs.

## Final recovery / integrity / preservation checkpoint (not executable under this approval)

After R01 receipt reconciliation, bind the observed new database ID, exact two paths, restore history and tail LSN to a separately sealed final RECOVERY operation. That packet must specify access restrictions and restored Service Broker state so application/activation work cannot start inadvertently. Do not change restored principals or install S11 as part of recovery.

Then authorize bounded full DBCC CHECKDB (no repair), online/file-map/chain-end checks and a preserved schema/row/receipt/fence baseline before installation. Current production cannot serve as a byte-identical baseline for this historical backup endpoint. Missing historical row digests remain a real limitation; no count/checksum shortcut may be called byte-exact preservation. Source schema confirms dbo.ExportJob OwnerID/Fence/Version and dbo.ExportAttempt OwnerID/Fence/Version/ReceiptJson; installation of these objects is not assumed. Inventory their actual presence first and pin any follow-on exact queries to observed shapes. Retained uncertain publication IDs and all S6/S8 databases remain protected. Final restore acceptance needs the original-row/receipt/fence comparisons required by the release packet; the baseline and later install comparisons are still pending. No new live production row scan is included here.

## Local validation / review

RP01 PowerShell parser passed without execution. Static R01 checks verified 119 ordered literal restores/header guards/receipts against the manifest, exact target/mappings, NORECOVERY throughout, absence of recovery/replace/drop/alter/backup/GO operations, and all protected file paths. An initial validator matched RECOVERY inside a human-readable result literal; corrected the validator to ignore strings/comments, leaving SQL unchanged. SQL has not been compiled/executed on a server; syntax/runtime proof remains pending. Independent-agent review not claimed or requested.

Source references read: authoritative SQL performance_remediation/kingdomscandata4/phase2/05_restore_preflight_backup_to_recovery.sql and phase1/update_all2_rehearsal/15_restore_update_all2_benchmark_database.sql; dbo.ExportJob.Table.sql and dbo.ExportAttempt.Table.sql. Historical reference scripts were not executed. Bot source remains unchanged. Original inventory 27 pending files and 394 evidence files checked unchanged; accepted ST04, V01, PD01 and V02 receipt seals verified.

Security routing: documented preparation-only skip for generated operator-review artifacts, with no deployed code/config/permission change or automatic execution. This is not a security clearance for broader rollout. Exact proposed effects manually reviewed above; no repository-wide audit or predecessor tests. Runtime pytest/architecture/deferred/security-routing validators skipped because no runtime source changed and no PR handoff occurs. All prior pending/recovered work remains retained.

[Microsoft RESTORE arguments](https://learn.microsoft.com/en-us/sql/t-sql/statements/restore-statements-arguments-transact-sql?view=sql-server-ver16) recommends NORECOVERY throughout a multi-step chain followed by a separate recovery operation. No fresh provider/Discord calls, memory investigation, deployment, Git publication or G5 approval is implied.
