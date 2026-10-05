# Grouped destination and full-backup metadata proposal — D03, D04, M01

PREPARED FOR EXACT SCOPE APPROVAL. The latest operator approval authorizes preparation following D02, not execution of these newly authored commands. No live action occurred. Chris Watts is operator, reviewer and abort owner. The existing maintenance window ends 2026-09-29T09:23:23Z; scheduling within it is already approved.

## Facts retained and proposed targets

D01R1 protects every one of the 21 existing development databases and 49 catalog files. D02 captured the six directory boundaries and 1,747,644,268,544 free bytes on development C:. F01 found all 119 selected source files, totaling 2,815,180,800 bytes. Those are historical observations, not reservations or media-integrity proof. The production S11 installation gap remains separate from delivered source implementation.

Proposed new database: `S11_G4_Recovery_20260928_97337` on `9SX2VF4\K98DEV`.

Proposed new directory: `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11_G4_20260928_97337` on development host 9SX2VF4. These are candidate names only. Neither exists merely because proposed; no creation or reuse is authorized. The candidate directory is separate from all retained catalog file paths and from production prune roots. Individual destination filenames and MOVE mappings await the actual backup file list. No existing file is a destination.

Single source media target: `C:\SQL_BACKUP\FULL\ROK_TRACKER_full_20260928.bak` on MINI_AMD, position 1, retained full backup set 97337. F01 observed length 1,173,233,664 bytes. Expected BackupSetGUID `70E5C6BF-4A0A-4A48-B6F1-E6E653E8A36D`, database ROK_TRACKER, full type, checkpoint LSN `19080000061546400001`, last LSN `19080000061548800001`. Full backup family GUID `C4DE892E-FD68-46E4-AB63-245E74BFC07B`, recovery fork `09F183A3-7582-4274-8B7F-ED127A825633`. Missing/different identity stops reconciliation without choosing another file.

## Exact operations, order and budgets

Commands are inert text under `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/`. Execute each entire text once only after exact scope approval. Do not combine SQL connections or substitute host/path/login. Stop the group on any failure; do not retry or repair settings/permissions to make it pass.

| Operation | Execution target and read scope | Limits | SHA256 |
|---|---|---|---|
| D03.sql.txt | Existing development SSMS connection, `localhost\K98DEV`, master; ORIGINAL_LOGIN `MicrosoftAccount\cwattsconsulting@outlook.com`. Guards require machine 9SX2VF4, instance K98DEV, sysadmin and clear captured transaction state. Test exact candidate database name and catalog directory prefix; return only the exact engine service's name/account/status from sys.dm_server_services. | One batch; 10-second SSMS execution timeout, 15-second operator cutoff; identity + candidate + at most 3 service rows + completion; 32 KiB output ceiling. Require exactly one engine row and Running status. | `c4abc222bf68a4a9f2521a54483b6b46cd033b2dfee00c43782e45b009b2eb85` |
| D04.ps1.txt | Existing Windows PowerShell on 9SX2VF4, same Windows account; one literal Get-Item on the exact proposed directory. ItemNotFound is distinguished from access/provider errors. No listing/content/ACL read or path creation. | One attempt; 10-second elapsed check after call; 15-second operator cutoff; one small JSON receipt, 4 KiB output ceiling. Require Completed and Present=false. | `09a5968241f675892ec98462c96d2f645b48bb7d7e0aade3b29c7a24e381a71d` |
| M01.sql.txt | Existing production SSMS connection MINI_AMD / ROK_TRACKER, same original SQL login above. Existing identity/visibility/sysadmin/transaction guards retained. RESTORE HEADERONLY and RESTORE FILELISTONLY, each from the one literal full-backup path WITH FILE=1. | One batch, two metadata media reads; 10-second SSMS execution timeout and 15-second operator cutoff for the entire batch; accept one header row and 1–32 file rows, plus identity/completion; 128 KiB returned-output ceiling. | `f8b11a3a8eaf587ef0d35e6ac31d011bde5acb68aec19f351051c887c2df5943` |

M01 is a newly proposed media-read scope: it is not implied by earlier catalog-only approval. Despite the RESTORE keyword, HEADERONLY/FILELISTONLY do not restore a database. No VERIFYONLY, CHECKSUM media scan, LOADHISTORY, BACKUP, RESTORE DATABASE/LOG, copy, provisioning or writes to application data are included. Both metadata commands run in the same approved batch; header reconciliation follows receipt, before any later mutation. If SSMS stops/errors, do not manually run remaining statements.

Budgets are operator/client bounds, not hard server/filesystem I/O limits. The engine may perform metadata I/O and audit/cache work; no exact byte-read ceiling or immediate cancellation guarantee is claimed. Raw RESTORE output has no server TOP cap: row/output ceilings are acceptance/abort limits, not prevention of a large result. Cancel immediately on excess rows or unexpected output and report only status, not a large paste. Do not increase timeouts or retry. Allow up to 45 seconds execution across three operations, with host-switching and manual review outside that execution budget. No operation runs in a loop.

## Effects, evidence and stop conditions

D03 changes only connection NOCOUNT, LOCK_TIMEOUT (1000 ms) and DEADLOCK_PRIORITY (LOW), and reads server metadata. M01 uses the same session settings and performs the two media metadata reads. There is no explicit transaction; standalone transaction-state capture avoids the prior self-observation issue. Do not roll back or commit any pre-existing transaction to pass a guard. These batch settings persist in the query session; no changes to server configuration or privileges.

D04 uses scalar local variables and console output. It does not resolve all aliases or bind filesystem handles; absence is sampled, and cannot reserve the path or prove the parent remains unchanged. Retain D02 as historical boundary context. No shell elevation, execution-policy adjustment, executable substitution or service action is included. Production executable hashes are not development binary attestation.

Retain operation label, server/host/database/login identity, timestamps, complete small result sets, completion marker and any interruption status. For M01, prefer an SSMS result export supplied as a local text attachment if wide columns would truncate when pasted. Do not truncate numeric LSNs, logical names, paths, GUIDs, size/max-size, IsPresent, encryption/thumbprint fields or server-version metadata. No key bytes or credentials are requested. Stop on identity/permission/transaction errors, timeout, candidate collision, missing service, non-Running service, inaccessible/missing media, truncated results or limits exceeded. Do not execute proposed paths or follow returned paths.

Interpret service_account as a reported SQL service identity only; token/SID/effective-create access and ACL equivalence remain unproven. Require M01 header identity to match the retained anchor before designing subsequent actions. Header/file-list metadata does not validate every page, every log or actual restorability. Unexpected extra files, non-D/L file types, encryption or layout ambiguity are review stops, not reasons to omit files or request keys.

## After the grouped receipt

Use file-list Size/MaxSize and types to calculate expanded storage requirements and propose exact disjoint file names/MOVE mappings, copy staging and growth/headroom budgets. Do not infer expanded sizes from compressed backup length. A later mutation approval must include fresh collision guards, media identity continuity, prune protection, copy/retention decisions and complete log-chain evidence. No prune job is disabled or changed here. The partial prune attestation and missing filter/cutoff details remain retained gaps.

All seven typed G4 proofs and actual restore remain incomplete. This group is not controlled-rollout or G5 approval. Preserve the isolated hotfix, single-account/admin-owned model, fresh generated output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues.

## Local validation and review scope

PowerShell static parsing and literal-target checks only; no commands executed. D03 retains D01R1's accepted identity/transaction guards; M01 retains S04R2 guards. SQL source references checked: `C:\K98-bot-SQL-Server\performance_remediation\kingdomscandata4\phase5_1_acl\01_preflight.sql` for engine service columns and `phase2\05_restore_preflight_backup_to_recovery.sql` for HEADERONLY/FILELISTONLY. These are syntax/source references, not authorization to execute those predecessor scripts. No Bot schema or SQL repo source changed.

Security-routing decision: documented skip for this additive documentation/inert-command proposal only, with literal targets, outputs and effects manually reviewed. No runtime integration, deployment, privilege mutation or Git publication. Architecture/deferred/security-routing validators, test-selection and runtime suites are skipped because this is not a PR or implementation change; preservation, static parsing and hash checks are the relevant validation. No broader scan or predecessor rerun. Original pending work and sealed evidence stay unchanged.
