# S11/G4 bounded capture subpacket — 2026-09-26

Packet: **S11-G4-CAPTURE-20260926-R1**. Preparation complete; **NOT APPROVED / NOT EXECUTED**.
This is an additive companion to the historical release packet, not its replacement.
The operator's current request and resumption handoff control historical instructions.
Approval must select individual operations and bind the execution envelope below. A general
“continue” cannot authorize held operations or targets discovered by an earlier read.

## 1. Reconciliation and preservation

Evidence root in this development checkout:
`C:\discord_file_downloader\.codex_artifacts\s11-g4-capture-preparation-20260926`.
`before-inventory.json` records exact paths, sizes, SHA256, retained-evidence mtimes and local refs.
`pending-before.zip` preserves all 27 pending files, including the file inside untracked `deploy/`.
Its SHA256 is `348327d26df9bea07d94714a1f77ac397473f68a56e4cca86b48aac80f20050f`.
The old recovery archive and all original evidence remain in place; no archive was overwritten.

- All 25 files in `recovery-20260926/restoration-verification.json` match their recovered hashes.
  The extra two pending files are the resumption handoff and `S11 G4 Resume After Hotfix - 20260926.md`.
- 24 of 25 paths match the earlier amendment validation seal. The exception is the historical
  release packet: current `a82a2fe5dc41008879b06265dc5e1835ff952d76388075dd4180e50d03a5ae57`
  matches the later recovery receipt. The older `df9609...` seal describes an earlier revision.
  All sealed amendment runtime/test/schema bytes match. This does not transfer old tests to
  the entire later merged tree or establish live readiness.
- 394 retained evidence files were inventoried across the plan, observations, deployed-v2 hotfix,
  recovery, authority-composition and resumption directories. This is byte-preservation evidence;
  it is not a claim that every assertion inside every historical receipt was independently verified.
- Local Bot HEAD/origin main: `2046ecdbd983450ab5098ec2a0caebfda91e41ab`.
  Local production/main: `3de899abee99102005911f5099c12b056f8aa490`.
  SQL HEAD: `4cd1554dc3d063e323f22350c88df1444cd0ed4b`. No network refresh.
- Retain delivery-proof, remote-file-proof, mirror282/production589/sql90 file records,
  source-pins and review receipts. Production589 patch remains
  `5cba76f916e6e81a9c3e8897a0e60566064b153cb940f3f8321dc37ada209df1`.
  Both S10E archive identities and SQL's `docs/SQL_DELIVERY_LOG.md` / `migrations/README.md` remain history.

## 2. Facts reused and stale statements superseded

| Area | Evidence usable now | Limit / current disposition |
| --- | --- | --- |
| Production build | Operator checkout/hash verification and hotfix OPERATOR-PACKET: `bd980c0f497faf2048eaf1fb6b79600662911763`, parent `abfc3845e9f8b78d70f88bada5a76c454ff32cb8` | Intentional isolated detached hotfix; not production/main; do not pull main |
| Startup/upload | HF06 log, follow-up through 21:22:12, upload evidence: 409 rows, counter 1028, 14 successful transfers, DONE 21:32:48.750 | Successful logged cycle, not independent SQL/Sheets content readback; no replay needed |
| Hotfix validation | Exact final candidate 3,720 passed / 2 skipped; local Python 3.11.9 and 108-package version parity; Changes/Deep-off scan `2fdbeb02-3842-4cb5-a063-944eb433e66b` | No installed-binary/native/provider attestation |
| Amendment | Matching retained source seal, 827 passed / 1 skipped; Changes/Deep-off `b08f5e51-ff25-4fa4-9bcd-15c5523c0e5a` | Local recovered work, not delivered/deployed by earlier S11 merges |
| Host | MINI_AMD, root `C:\discord_file_downloader`; observer SID `S-1-5-21-2970367362-111206357-3835881402-1001`; 04:46:41Z ACL receipt | Authenticated Users Modify on root/.env was observed; current final protected boundary unproved; no ACL edit now |
| Process | Prior chain and startup PID7020/venv path | All are historical; no PID/FILETIME/token binding may survive restart by inference |
| SQL | MINI_AMD/ROK_TRACKER, SQL16.0.1200.5, FULL/compat160; 480 name/type matches and 58 absent of 538 sources; roles absent, SHEETS_USER db_owner | Historical installation gap, not missing source implementation; no install-all-58 shortcut |
| Backup/storage | FULL/DIFF/LOG history under C:\SQL_BACKUP; prune and two LOG schedules; 17 retained development application DBs | Partial development file output is not a complete exclusion list; hotfix backup assurance is not actual restore |
| Provider | Legacy identity `sheets-service@statsupdate.iam.gserviceaccount.com`, project `statsupdate`; key reportedly on both machines | Nonsecret historical binding only; access/IAM/key inventory/fresh identity remain unproved |
| Output | Existing file `1EHirQ14aFvnOxM3RwgnlmZ_AogVmvJ0fuPtQuGHhfx0`, grid1683673174 | Protected exclusion; never adopt, clear, publish into or use as a fresh slot |

The original collector and token helper remain **WITHDRAWN — NEVER RUN**. Their historical
hashes are in the before-inventory; this packet neither modifies nor invokes them. No incident
reproduction, replacement broad collector or memory-cause investigation is proposed. Cause stays
UNRESOLVED at operator direction. Empty KVK reporting and view-rehydration timeout are separate
retained issues; neither is a prerequisite to preparing this capture nor a reason to replay upload.

Historical “not published/not run”, “two accounts”, “Bot-inaccessible credentials”, pending output
preferences and unresolved source-digest fix statements are superseded by the handoff and matching
amendment. Current source confirms `single_account_application_v1`: supervisor v3, Bot v2,
enrollment outer v2, boundary/records v2, SQL readiness v3/application. Same SID, distinct PIDs,
exact native creation FILETIME/executable/hash/token and retained handles remain mandatory.
Schema source digest is `e9a6a1042de97e4fd4d7902756375f642a5a960354edb4018207ebc806a68b32`.
Git-byte schema hashes, deployed raw-file hashes and SQL UTF16 definition hashes are different domains.

One Windows account and Chris as admin operator/reviewer are settled. Review checkpoints are
distinct; reviewers need not be distinct people. Fresh generated output link/equivalent reports
are settled. Enrollment later uses admin-owner OAuth `drive.file`, then service-account Editor;
creation rights for that service account are not presumed. Player access remains Viewer.
Intended `KVK_DATA_CHANNEL=1549003662024642632` installation remains unobserved; do not set it now.

## 3. Execution envelope and hard boundaries

No command block below has been executed. Each block is also stored verbatim as a UTF-8/LF
`.txt` attachment under `commands/` with a SHA256 in `command-hashes.json` and the local seal.
These are review text, not a replacement collector or batch runner. No wrapper invokes them.

For each selected operation record: packet/seal hash, block hash, actor, machine, approved tool
path/hash, target, UTC start/expiry, abort owner, evidence destination, budget and result.
Proposed operator/reviewer/abort owner: Chris Watts (abort ownership still requires approval).
Window: operator-selected UTC start, expiry **20 minutes later**; a single operation must fit
inside it. No automatic recurring read or retry. Retention: keep originals until explicit later
disposition, with no automated pruning. Proposed returned-evidence destination is the existing
development evidence root above, using a new `received-<operation>-<UTC>.txt` per operation.
Do not write receipts to production application/log/data paths or overwrite prior files.

First-stage host reads use the operator's existing Windows PowerShell session on MINI_AMD.
H00 inventories that session/tool; it does not certify its trust. Its receipt must be reviewed
before pinning that executable for later H operations. SQL client and provider client executable,
version/hash and already authorized authentication identity are **UNRESOLVED**, so SQL/provider
blocks are sealed review candidates, not executable approval requests yet. No login, consent,
credential refresh, permission elevation or access repair is implied by preparing them.

Bounds are operator cutoffs unless the named API/client enforces a timeout. In particular,
PowerShell formatting, Task Scheduler and filesystem calls have no promised hard kill deadline.
Run one small block at a time; no asynchronous batch, recursive object serialization, recursive
filesystem scan, process-memory read, command-line/environment dump, Bot import or pip command.
If hard resource enforcement is required, an independently reviewed bounded runner is a separate
preparation item; do not revive the withdrawn helper or improvise one during execution.

Stop immediately on changed target/hash/identity, unexpected reparse point, denied visibility,
truncated output, sentinel row, secret-bearing output, command error, elapsed/output budget,
machine health degradation, or new operator input to stop. Do not weaken permissions or use
another identity to make a read succeed. Preserve partial output with FAILED/INCOMPLETE and the
last completed block. Cancel only the foreground observation; never stop Bot, SQL, a writer or
scheduled task. Cancellation is not proof that server/provider work has ended. No mutation
rollback is needed for these reads; no delete/reset/retry/restore is authorized as recovery.

Effects: host reads consume CPU/I/O and may create OS audit/cache activity; SQL reads open sessions,
use metadata locks/resources/tempdb as the engine requires and may create audit/plan activity;
provider reads consume quota and produce access/audit activity. Returned evidence files are writes
on development. “Read-only” does not mean zero operational load or proof of no concurrent writers.

## 4. First stage: bounded host binding reads

Approve individually after the envelope is recorded. **H00 only can precede tool pinning.**
H01–H05 depend on accepted H00 and its executable hash. No old PID is embedded in a command.

### H00 — observer/tool identity (MINI_AMD; 10 seconds; 8 KiB)

```powershell
$ErrorActionPreference = 'Stop'
if ($env:COMPUTERNAME -ne 'MINI_AMD') { throw 'Wrong host' }
[DateTime]::UtcNow.ToString('o')
[Security.Principal.WindowsIdentity]::GetCurrent().Name
[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$PSVersionTable.PSVersion.ToString()
$captureShell = (Get-Process -Id $PID).Path
Get-Item -LiteralPath $captureShell | Select-Object FullName,Length,Attributes
Get-FileHash -LiteralPath $captureShell -Algorithm SHA256
```

Evidence: observer only, exact PowerShell executable/version/hash. No claim about the Bot token.
If shell path differs from the expected Windows PowerShell installation, stop for review.

### H01 — path boundary and ACL metadata (MINI_AMD; 20 seconds; 64 KiB)

```powershell
$ErrorActionPreference = 'Stop'
if ($env:COMPUTERNAME -ne 'MINI_AMD') { throw 'Wrong host' }
$capturePaths = @('C:\','C:\discord_file_downloader','C:\discord_file_downloader\.env','C:\discord_file_downloader\venv','C:\discord_file_downloader\venv\Scripts','C:\discord_file_downloader\venv\Scripts\python.exe','C:\Program Files','C:\Program Files\Python311','C:\Program Files\Python311\python.exe','C:\discord_file_downloader\data','C:\discord_file_downloader\logs','C:\discord_file_downloader\downloads')
foreach ($capturePath in $capturePaths) {
    $captureItem = Get-Item -LiteralPath $capturePath -Force
    if ($captureItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse boundary; stop' }
    $captureAcl = Get-Acl -LiteralPath $capturePath
    if ($captureAcl.Sddl.Length -gt 4096) { throw 'ACL output cap; stop' }
    [pscustomobject]@{Path=$capturePath;Attributes=[string]$captureItem.Attributes;Owner=[string]$captureAcl.Owner;Sddl=[string]$captureAcl.Sddl} | ConvertTo-Csv -NoTypeInformation
}
```

Evidence: current sampled parent/leaf owner/SDDL, not a full future S11 `host_acl`. No key paths
are guessed. Future source directories, manifests, spool, origin/evidence/retirement stores and
credential references require exact allowlisted parents/paths and a separately sealed extension.
Any denied/missing path is an unresolved observation, not permission to create or change it.

### H02 — narrow current file pins (MINI_AMD; 20 seconds; 16 KiB)

After H01 accepts the ancestor paths. At most 16 MiB per file and 64 MiB total; no directory walk.
Reuses retained package-version evidence; this does not rerun pip or prove installed package bytes.

```powershell
$ErrorActionPreference = 'Stop'
if ($env:COMPUTERNAME -ne 'MINI_AMD') { throw 'Wrong host' }
$captureFiles = @('C:\discord_file_downloader\file_utils.py','C:\discord_file_downloader\maintenance_worker.py','C:\discord_file_downloader\proc_config_import.py','C:\discord_file_downloader\run_bot.py','C:\discord_file_downloader\DL_bot.py','C:\discord_file_downloader\requirements.txt','C:\discord_file_downloader\.env','C:\discord_file_downloader\venv\pyvenv.cfg','C:\discord_file_downloader\venv\Scripts\python.exe','C:\Program Files\Python311\python.exe')
$captureBytes = 0L
foreach ($captureFile in $captureFiles) {
    $captureBefore = Get-Item -LiteralPath $captureFile -Force
    if ($captureBefore.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse file; stop' }
    $captureBytes += $captureBefore.Length
    if ($captureBefore.Length -gt 16MB -or $captureBytes -gt 64MB) { throw 'File byte budget; stop' }
    $captureHash = Get-FileHash -LiteralPath $captureFile -Algorithm SHA256
    $captureAfter = Get-Item -LiteralPath $captureFile -Force
    if ($captureBefore.Length -ne $captureAfter.Length -or $captureBefore.LastWriteTimeUtc -ne $captureAfter.LastWriteTimeUtc) { throw 'File changed; stop' }
    [pscustomobject]@{Path=$captureFile;Bytes=$captureAfter.Length;SHA256=$captureHash.Hash} | ConvertTo-Csv -NoTypeInformation
}
```

`.env` is hashed only, never printed; no credential JSON/key/token is opened or hashed. Compare
hotfix file representation to deployed-v2 manifest and supplied HF01/HF04 evidence; a mismatch
stops, including unexplained LF/CRLF differences. Final new-release source/dependency/config pins
must be prepared and independently compared later; these hotfix samples cannot satisfy that gate.

### H03 — current Python process candidates (MINI_AMD; 10 seconds; 16 KiB)

```powershell
$ErrorActionPreference = 'Stop'
if ($env:COMPUTERNAME -ne 'MINI_AMD') { throw 'Wrong host' }
$captureProcesses = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" -OperationTimeoutSec 5 | Select-Object -First 17 ProcessId,ParentProcessId,CreationDate,ExecutablePath)
if ($captureProcesses.Count -gt 16) { throw 'Process count cap; incomplete' }
$captureProcesses | ConvertTo-Csv -NoTypeInformation
```

Evidence: candidate parent chain/executable/creation dates only. Unknown wrapper/parent processes
need a new exact PID allowlist; no command lines. Millisecond creation time is not native FILETIME.
H03 does not authorize token reads of discovered PIDs or adopt a new Bot/authority incarnation.

### H04 — seven retained task identities, fixed scalar fields (MINI_AMD; 20 seconds; 32 KiB)

```powershell
$ErrorActionPreference = 'Stop'
if ($env:COMPUTERNAME -ne 'MINI_AMD') { throw 'Wrong host' }
$captureTasks = @(@('\','StartDLBotAfterSQL'),@('\','DLBotLogRotate'),@('\','K98 SQL Nightly Schema Export'),@('\','K98 SQL Schema Export'),@('\Restart\','Graceful DL_Bot Shutdown'),@('\Restart\','Restart daily'),@('\Restart\','RUN_Bot'))
foreach ($captureTask in $captureTasks) {
    $captureDefinition = Get-ScheduledTask -TaskPath $captureTask[0] -TaskName $captureTask[1]
    if (@($captureDefinition.Actions).Count -gt 4 -or @($captureDefinition.Triggers).Count -gt 8) { throw 'Task shape cap' }
    [pscustomobject]@{Path=$captureDefinition.TaskPath;Name=$captureDefinition.TaskName;State=[string]$captureDefinition.State;User=[string]$captureDefinition.Principal.UserId;RunLevel=[string]$captureDefinition.Principal.RunLevel;Actions=@($captureDefinition.Actions).Count;Triggers=@($captureDefinition.Triggers).Count;RestartCount=$captureDefinition.Settings.RestartCount;RestartInterval=[string]$captureDefinition.Settings.RestartInterval;MultipleInstances=[string]$captureDefinition.Settings.MultipleInstances} | ConvertTo-Csv -NoTypeInformation
    foreach ($captureAction in $captureDefinition.Actions) {
        [pscustomobject]@{Execute=[string]$captureAction.Execute;WorkingDirectory=[string]$captureAction.WorkingDirectory;ArgumentsPresent=([string]$captureAction.Arguments -ne '')} | ConvertTo-Csv -NoTypeInformation
    }
    foreach ($captureTrigger in $captureDefinition.Triggers) {
        [pscustomobject]@{Type=[string]$captureTrigger.CimClass.CimClassName;Enabled=$captureTrigger.Enabled;Start=[string]$captureTrigger.StartBoundary;End=[string]$captureTrigger.EndBoundary;Interval=[string]$captureTrigger.Repetition.Interval;Duration=[string]$captureTrigger.Repetition.Duration} | ConvertTo-Csv -NoTypeInformation
    }
}
```

No arguments, event subscription XML or COM action data leave the host. Their withheld effects
remain unresolved until Chris supplies nonsecret action/trigger details already known or a
separate narrow redacted read is approved. A disabled task can still be manually run; Ready is
not running. This read does not prove absence of other tasks/services/manual writers.
The purpose is G4 effects and future process lifecycle, not retroactive hotfix startup approval.

### H05 — production storage summary (MINI_AMD; 10 seconds; 8 KiB)

```powershell
$ErrorActionPreference = 'Stop'
if ($env:COMPUTERNAME -ne 'MINI_AMD') { throw 'Wrong host' }
Get-CimInstance Win32_LogicalDisk -Filter "DeviceID = 'C:'" -OperationTimeoutSec 5 | Select-Object DeviceID,FileSystem,Size,FreeSpace | ConvertTo-Csv -NoTypeInformation
```

No recursive backup/log enumeration or file-content scan. Storage sufficiency still requires the
approved restore/spool/log retention sizes and complete physical maps. Other volumes discovered
by SQL are not automatically added to this read scope.

## 5. SQL observation candidates — client/identity envelope still held

These are literal query text, **not executed** and not production migrations. Run only through
a separately pinned existing SQL client, on the stated target, with connection timeout 5 seconds,
command timeout 10 seconds, overall 15 seconds per block, one connection/block and no retry.
Client launch command/path/hash and secure existing authentication binding must be sealed before
approval. No `-C`/certificate bypass, connection-string dump or password in command text.
If the client cannot enforce both timeouts, the operation remains held.
Each query uses metadata only; lock timeout 1 second, low deadlock priority, MAXDOP1 on inventories.
Row caps include one sentinel: at the cap, mark INCOMPLETE and stop, never silently truncate or page.
Record exact original server/database/observer/time alongside the result. A permissions-filtered
catalog is incomplete: NULL/hidden metadata is not absence. No application import/readiness factory
is called merely to collect metadata.

### S00 — complete development DB/file exclusions (localhost\K98DEV, master; 256 KiB)

```sql
SET NOCOUNT ON; SET LOCK_TIMEOUT 1000; SET DEADLOCK_PRIORITY LOW;
SELECT SYSUTCDATETIME() observed_utc, @@SERVERNAME server_name, DB_NAME() database_name, ORIGINAL_LOGIN() observer;
SELECT TOP (65) database_id,name,state_desc FROM sys.databases ORDER BY database_id OPTION(MAXDOP 1);
SELECT TOP (257) database_id,DB_NAME(database_id) database_name,file_id,name logical_name,type_desc,physical_name,size,max_size,growth,is_percent_growth FROM sys.master_files ORDER BY database_id,file_id OPTION(MAXDOP 1);
```

Expected historical server `9SX2VF4\K98DEV`; a different alias resolution stops for operator review.
Require full metadata visibility and file rows for all DBs, including system/retained/offline DBs.
Preserve every returned name/path. Candidate `K98_S11_G4_20260926_validation` / `_restore` names
are unreserved and may also conflict with fixture naming gates; no creation is proposed here.
After accepted paths, seal separate exact development-volume free-space/ACL/reparse reads.

### S01 — small S11 presence/definition probe (MINI_AMD, ROK_TRACKER; 32 KiB)

```sql
SET NOCOUNT ON; SET LOCK_TIMEOUT 1000; SET DEADLOCK_PRIORITY LOW;
SELECT SYSUTCDATETIME() observed_utc, @@SERVERNAME server_name, DB_NAME() database_name, ORIGINAL_LOGIN() observer, HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','VIEW DEFINITION') view_definition;
WITH names(name) AS (SELECT name FROM (VALUES
(N'dbo.ExportExecutionSession'),(N'dbo.ExportExecutionStream'),(N'dbo.ExportProviderRequest'),
(N'dbo.ExportProviderRequestEvent'),(N'dbo.ExportReconciliationProof'),(N'dbo.ExportManagedFileOrigin'),
(N'dbo.usp_ExportExecutionSessionTransition'),(N'dbo.usp_ExportExecutionStreamTransition'),
(N'dbo.usp_ExportProviderRequestEventAppend'),(N'dbo.usp_ExportReconciliationProofIssue'),
(N'dbo.usp_ExportOutputEnrollmentTransition')) v(name))
SELECT n.name,o.type,CASE WHEN o.object_id IS NULL THEN 0 ELSE 1 END present,
DATALENGTH(m.definition) definition_bytes,
CONVERT(varchar(64),HASHBYTES('SHA2_256',CASE WHEN DATALENGTH(m.definition)<=1048576 THEN CONVERT(varbinary(max),m.definition) END),2) installed_definition_utf16_sha256
FROM names n LEFT JOIN sys.objects o ON o.object_id=OBJECT_ID(n.name)
LEFT JOIN sys.sql_modules m ON m.object_id=o.object_id ORDER BY n.name OPTION(MAXDOP 1);
```

Requires full VIEW DEFINITION visibility. Missing objects stop that object's shape capture;
oversized/encrypted/invisible definitions are unresolved. Do not re-run the 538-object name
inventory as a substitute for missing shapes. The exact subsequent source-derived object batches
must cover tables/UDTs/parameters, columns/defaults/computed/identity properties, indexes/checks/FKs,
triggers/synonyms/dependencies, ANSI settings, ownership/execution context, signatures and grants.
Use `services/export_execution_dal.py` metadata contracts and authoritative SQL source; do not
execute their live factories or learn expected fingerprints from these observed values.
Presence/history can be reused for scoping; final installation proof needs all required shapes.

### S02 — current principal/role metadata (MINI_AMD, ROK_TRACKER; 64 KiB)

```sql
SET NOCOUNT ON; SET LOCK_TIMEOUT 1000; SET DEADLOCK_PRIORITY LOW;
SELECT SYSUTCDATETIME() observed_utc, @@SERVERNAME server_name, DB_NAME() database_name, ORIGINAL_LOGIN() observer;
SELECT name,type_desc,default_schema_name FROM sys.database_principals WHERE name IN (N'SHEETS_USER',N'ExportExecutionAuthority',N'ExportExecutionReader',N'ExportLegacyEntryReader');
SELECT TOP (65) r.name role_name,m.name member_name FROM sys.database_role_members x JOIN sys.database_principals r ON r.principal_id=x.role_principal_id JOIN sys.database_principals m ON m.principal_id=x.member_principal_id ORDER BY r.name,m.name OPTION(MAXDOP 1);
SELECT TOP (129) p.name grantee,d.state_desc,d.permission_name,d.class_desc,d.major_id,d.minor_id FROM sys.database_permissions d JOIN sys.database_principals p ON p.principal_id=d.grantee_principal_id WHERE p.name IN (N'SHEETS_USER',N'public',N'ExportExecutionAuthority',N'ExportExecutionReader',N'ExportLegacyEntryReader') ORDER BY p.name,d.class,d.major_id,d.minor_id,d.permission_name OPTION(MAXDOP 1);
```

This observes current catalogs only, not restricted effective capabilities. The future application
principal is unselected; exact direct/transitive roles, server/database/object/column capabilities,
ownership, certificates/signatures and effective-session reads need that binding and review.
Authority role is required, Reader role is forbidden by DENYs; sysadmin/db_owner and excess
CONTROL/ALTER/IMPERSONATE cannot be “fixed” by granting more. No impersonation or grant/revoke.

### S03 — writer/session and Agent step metadata (MINI_AMD, ROK_TRACKER; 128 KiB)

```sql
SET NOCOUNT ON; SET LOCK_TIMEOUT 1000; SET DEADLOCK_PRIORITY LOW;
SELECT SYSUTCDATETIME() observed_utc, @@SERVERNAME server_name, DB_NAME() database_name, ORIGINAL_LOGIN() observer;
SELECT TOP (65) session_id,login_name,host_name,host_process_id,program_name,login_time,status FROM sys.dm_exec_sessions WHERE is_user_process=1 ORDER BY session_id OPTION(MAXDOP 1);
SELECT TOP (65) j.name job_name,j.enabled,s.step_id,s.subsystem,s.database_name,DATALENGTH(s.command) command_bytes,CONVERT(varchar(64),HASHBYTES('SHA2_256',CASE WHEN DATALENGTH(s.command)<=1048576 THEN CONVERT(varbinary(max),s.command) END),2) command_utf16_sha256 FROM msdb.dbo.sysjobs j LEFT JOIN msdb.dbo.sysjobsteps s ON s.job_id=j.job_id ORDER BY j.name,s.step_id OPTION(MAXDOP 1);
SELECT TOP (65) j.name job_name,s.name schedule_name,s.enabled,s.freq_type,s.freq_interval,s.freq_subday_type,s.freq_subday_interval,s.active_start_date,s.active_start_time FROM msdb.dbo.sysjobs j JOIN msdb.dbo.sysjobschedules x ON x.job_id=j.job_id JOIN msdb.dbo.sysschedules s ON s.schedule_id=x.schedule_id ORDER BY j.name,s.name OPTION(MAXDOP 1);
```

No SQL text/session input buffers/query plans or Agent command text is emitted. Hashes identify
steps for separately redacted effect review, not prove their effects. Polling, kill, disable/start
jobs, transaction/drain probes and live application table reads are excluded.

### S04 — bounded recovery-chain candidates (MINI_AMD, ROK_TRACKER; 64 KiB)

```sql
SET NOCOUNT ON; SET LOCK_TIMEOUT 1000; SET DEADLOCK_PRIORITY LOW;
SELECT SYSUTCDATETIME() observed_utc, @@SERVERNAME server_name, DB_NAME() database_name, ORIGINAL_LOGIN() observer;
WITH recent AS (SELECT TOP (12) backup_set_id,media_set_id,type,backup_start_date,backup_finish_date,first_lsn,last_lsn,checkpoint_lsn,database_backup_lsn,differential_base_lsn,recovery_model,is_copy_only,has_backup_checksums,is_damaged,backup_size,compressed_backup_size FROM msdb.dbo.backupset WHERE database_name=N'ROK_TRACKER' ORDER BY backup_finish_date DESC,backup_set_id DESC)
SELECT TOP (49) b.*,f.family_sequence_number,f.physical_device_name FROM recent b JOIN msdb.dbo.backupmediafamily f ON f.media_set_id=b.media_set_id ORDER BY b.backup_finish_date DESC,b.backup_set_id DESC,f.family_sequence_number OPTION(MAXDOP 1);
```

Twelve sets may not span a usable chain; that result stays incomplete, never “backup good”. Seal
an exact chain-range extension after review, not automatic pagination. Media existence/readability,
retention/prune exclusions, bytes/hash/ACL and restore logical/physical maps are later exact reads
with separate I/O budgets. No BACKUP, RESTORE, VERIFYONLY, FILELISTONLY, CHECKDB or media open here.
Actual restore remains a distinct effectful operation after disjointness and storage review.

## 6. Provider candidates — no authentication or provider call in this preparation

The operator reconfirms that `sheets-service@statsupdate.iam.gserviceaccount.com` is the KVK_ALL
Editor and that the admin generally creates sheets before the process writes them. Source agrees:
`kvk_all_importer._auto_export_kvk` supplies `KVK_SHEET_NAME` and `CREDENTIALS_FILE`;
`gsheet_module.get_gsheet_client` loads service-account credentials, and the primary renderer opens
the existing spreadsheet before updating tabs. No credential file was read. The email is
operator-confirmed, not independently extracted from private key material. Some additional-report
source branches can create a missing workbook; that is a writer-inventory effect to retain, not
evidence that the service account currently has creation rights.

This settles the historical Editor/admin workflow. The Google owner email, OAuth client/project
and intended fresh S11 service identity are still not supplied. Do not repeat the Editor question
or infer that the copied historical credential satisfies fresh issuance. Leave those fields
UNRESOLVED until nonsecret enrollment metadata is available. No new key issuance, token request,
consent, IAM change, sharing or file creation.

P00 is the following exact **read request specification**, using an already approved identity/client
after its path/version/hash and authentication effects are pinned. No Authorization header value
is logged. One attempt per request, 5-second connect / 10-second total, 256 KiB response cap,
four requests / 60 seconds total. No redirect, pagination or 429/503 retry. `nextPageToken`,
incomplete permissions or unexpected shared-drive/inherited access stops for a separate extension.

```http
GET https://www.googleapis.com/drive/v3/files/1EHirQ14aFvnOxM3RwgnlmZ_AogVmvJ0fuPtQuGHhfx0?fields=id,mimeType,trashed,driveId,parents,owners(emailAddress,permissionId),capabilities(canEdit,canShare)&supportsAllDrives=true
GET https://www.googleapis.com/drive/v3/files/1EHirQ14aFvnOxM3RwgnlmZ_AogVmvJ0fuPtQuGHhfx0/permissions?pageSize=100&fields=nextPageToken,permissions(id,type,role,emailAddress,domain,allowFileDiscovery,deleted,expirationTime,permissionDetails)&supportsAllDrives=true
GET https://sheets.googleapis.com/v4/spreadsheets/1EHirQ14aFvnOxM3RwgnlmZ_AogVmvJ0fuPtQuGHhfx0?includeGridData=false&fields=spreadsheetId,sheets(properties(sheetId,gridProperties(rowCount,columnCount)))
GET https://iam.googleapis.com/v1/projects/statsupdate/serviceAccounts/sheets-service%40statsupdate.iam.gserviceaccount.com/keys?keyTypes=USER_MANAGED&fields=keys(name,keyAlgorithm,keyOrigin,keyType,validAfterTime,validBeforeTime,disabled)
```

Evidence: existing-file owner/access/grid metadata and historical user-managed key IDs,
validity/status/origin/type metadata only. Key listing is not key download; do not call key.get
with public-key/private-key data formats. No cells, exports, file downloads or list-all-Drive.
An access failure (including the previous approval-token failure) means stop; no alternate route
to bypass it. API permissions visible to one principal are not automatically complete IAM evidence.

P01 remains **TARGET-UNBOUND / NOT AN APPROVAL REQUEST**: fresh project/client/service identity,
owner/enrollment reference, service-account/project/ancestor IAM bindings, issuer/admin/impersonator
capabilities, group membership closure and historical key holder/revocation metadata. Pin exact
resources and read requests after the nonsecret facts arrive. Do not search every project or
enumerate organization-wide IAM opportunistically. Preserve unresolved capabilities explicitly.

P02 remains **CREATION-DEPENDENT / NOT AN APPROVAL REQUEST**: fresh index/slot/grid IDs, aliases,
owner/editor/viewer/inherited permissions, full protected exclusions and private/public transition.
They can only be bound to later approved enrollment receipts. No fabricated creation origins,
title-based adoption, manual file creation or writes to the supplied existing file. Read-only
metadata cannot establish private blank-file readback or no-delayed-effects proof.

## 7. Remaining capture extensions and proof gates

This is a staged capture packet, not a promise that unresolved future commands are executable.
No command/hash is invented for a target not yet known. After accepted first-stage observations,
prepare **another sealed exact operation** for each remaining row before asking to execute it.
Suggested ceilings below constrain that preparation, not authorize a generic search.

| Missing observation | Exact target dependency / permitted next preparation | Proposed ceiling; evidence and stop |
| --- | --- | --- |
| Native Bot token/incarnation | Accepted H03 PID/path/time plus H02 binary; independently reviewed native observer, not withdrawn helper | One selected process, 5s, 32KiB; QUERY_LIMITED_INFORMATION/SYNCHRONIZE + TOKEN_QUERY only; exact FILETIME, groups incl disabled/deny-only, privileges, elevation/UIAccess; retained handle before/after; exit/drift stops |
| Future authority/Bot binding lifecycle | No authority is installed by this packet; later controlled launch, exact supervisor/child identities and admission-closed lifecycle | No launch command now; approve actual native procedure and restart policy separately; never auto-adopt PID/FILETIME |
| Full source/interpreter/dependencies | Independently prepared final new-release manifest, exact base Python/DLL/package files and artifact provenance | <=16 named files / 64MiB / 20s per reviewed batch; immutable source map, no recursive serialization; RECORD metadata is not installed-binary/wheel proof |
| Key references/ACLs and stores | Operator-known nonsecret exact paths on development and production, issuer/holders; no credential contents | <=16 explicit files/parents, 20s,64KiB; metadata owner/DACL/reparse only; missing path is not provision permission; keep shared-account trust semantics |
| Remaining task/service/manual-tool effects | H04/S03 identities, redacted action and trigger details, exact script bytes from retained/source first | <=4 named definitions/scripts per batch, <=1MiB each,20s; withhold possible secrets; unresolved action remains unknown writer |
| SQL installed shapes/signatures | S01 visibility/presence, authoritative S10A/C/D/E/S11 definitions and full 538-source manifest; exact object allowlists | <=16 objects / 512 rows per result / 1MiB output / 10s query; named contracts including UDT/parameters/signatures/grants; no app/business proc or migration execution |
| Restricted effective SQL capabilities | Exact application principal chosen and secure approved session method; direct/transitive role/owner/certificate closure | 5s connect/10s query/15s total,128KiB; observe own effective session, no impersonation/admin substitution; compare independently reviewed expected map |
| Development storage and file exclusions | S00 complete database/logical/physical paths and exact volume roots; no inferred C:-only inventory | <=8 named roots/volumes,10s,32KiB; preserve all files/DBs; free space must cover backup copies+restored data/log+growth+retention headroom before restore approval |
| Backup chain/readability/retention | S04 accepted exact set/LSN/media list plus prune-step effects and storage budget | Separate media I/O/SQL-header-read packet; no blanket 64MiB cap applied to database backups; explicit byte/rate/time limits required |
| Remaining provider exclusions/aliases | Source/config/retained S6 file IDs, exact observed legacy mappings and P00/P01 access | Explicit file IDs only; <=4 reads/60s/1MiB per batch; no title crawl; incomplete set blocks any resource mutation |

All **seven typed records remain INCOMPLETE**:

| Record | What this capture can supply | What it cannot supply |
| --- | --- | --- |
| host_acl | Current sampled hashes/owners/ACL/reparse facts | Approved final release/path ACLs, full binary/config/dependency map |
| bot_identity | Process candidates and later native observations | Future approved incarnations and retained execution-lifetime handles |
| identity_issuance | Nonsecret identity/IAM capability metadata | Fresh issuance/custody receipts; issuance is a separate mutation |
| key_inventory | Metadata IDs/status/locations/holders | Exhaustive exclusion of old writers by a fresh key alone |
| file_access | Existing file/provider metadata | Fresh origins/private blank readback/full P/Q/R registration and transition proofs |
| writer_drain | Tasks/jobs/process/session/manual-writer inventory | Closed admission, exact owned requests/children, termination, drain and no delayed effects |
| sql_installation | Current visible catalog facts for source comparison | Installation receipts, restricted capabilities, all exact shapes and transaction cases |

**Actual restore is also INCOMPLETE**. Neither VERIFYONLY, local archive extraction, historical
S8/S10 restore nor operator hotfix backup assurance satisfies this new target's restore proof.

Writer coverage must retain upload/daily scan/recompute/export, legacy all-KVK, ProcConfig,
new-source/admin/recovery/rebuild/rollover, compatibility wrappers, authority/children/enrollment,
manual tools/admins, copied keys and task/service/SQL Agent effects. Inventory is not drain.
No S11 close-admission/drain/termination or provider reconciliation runs during capture.

## 8. Preserved invariants, cases and later decisions

Retain fixed source per whole KVK, source/endpoint/UpdateID, B0 and the approved EndScanID
amendment; running A immutable and only eligible pending coalescing; daily order/fairness and
registration-aware intents; complete S10C provenance/spool/nested ownership; exact owner/fence/
version CAS, append-only dispositions and byte-exact receipts. Keep P/Q/R formula
`1 + P + P + max(P,Q) + P + R`, 9,000,000-cell parts, eight registrations/sixteen slots.
No flag flip or source merge is an activation decision.

Keep packet cases N01–N12, C01–C06, T01–T04, S01–S08, L01–L04, Q01–Q05, P01–P05,
R01–R04 and D01–D05 pending exact later case/target approval. Incomplete drain fails with retained
session; shared durable 429/503 cooldown never permits blind retry. Rollover closes admission,
drains/reconciles and proves old-writer termination/no delayed effects before private clear/readback
and audited reuse. Interrupted retirement needs explicit journal recovery. No uncertain claim is
released by time, process exit, job state or a successful hotfix upload.

S6-OPS01/PERF01/CAP01 remain OPEN. Preserve uncertain publications
`e19c89ac-7977-5f28-ae4c-031807cd1728` and `54a2480a-26fb-5bad-a3f5-9321525a731c` and every
associated database/file/receipt. S8A six scripts, S8B 50 cases and actual restore versus offline
history, and S8C seven local checks remain distinct. No predecessor rerun is proposed.

Later sequence: accepted bounded observations -> source-derived exact missing delta and complete
exclusions -> separately approved recovery/actual restore/provisioning/install/native/provider
cases -> separately approved controlled rollout -> explicit G5 accept/reject/defer and activation
decisions. No automatic PR/publication/task creation, deployment/restart or current-main pull.

## 9. Local preparation validation and approval form

Scope is this new Markdown packet, inert command-text attachments and preservation/seal receipts.
No runtime/test/SQL source, configuration, dependency, permissions or restart behavior changed.
No new helper or refactor is needed. Existing incident/output issues remain in their retained
records; no new optimisation item or vulnerability claim is manufactured.

K98 security routing: documented skip for this preparation delta only. Inert operation text has
been reviewed locally; it has not received a new runtime/native/SQL/provider execution test or
Codex Security certification. Prior amendment/hotfix scans retain their exact target scope.
Later executable tooling/runtime/config changes require Changes/Deep off on the exact Bot patch;
actual SQL changes require separate assessment. No whole-repository/deep scan.

Architecture/deferred/test-selector/security-routing validators, pytest, smoke imports and
registration runs are skipped here: no PR handoff or new runtime change; whole-worktree discovery
would include preserved prior amendment work. Local checks instead verify path/hash preservation,
archive contents, command-block/attachment identity, PowerShell parse-only validity and source pins.
SQL/API specifications have not been engine/provider validated; no such execution is authorized.

Preparation results: 27/27 original pending files and 394/394 retained evidence files unchanged;
new archive contents verified against each original SHA256; 538/538 schema source entries match
exact SQL Git blobs at the pinned commit and their canonical digest matches the source constant.
All six PowerShell blocks passed parse-only checks. Twelve command/request blocks are individually
hashed. SQL source remains unchanged. See `validation.json`, `powershell-parse.json`,
`command-hashes.json`, `source-read-pins.json` and `preparation-seal.json` in the evidence root.
The seal binds this packet and its attachments; its SHA256 is recorded separately to avoid
self-reference. No operational proof is emitted from these checks.

Approval record (blank fields block execution):

```text
Packet: S11-G4-CAPTURE-20260926-R1
Packet/seal SHA256: [copy exact value from preparation-seal.json / its recorded hash]
Decision: approve / reject / revise selected observation operations only
Operation IDs and command SHA256: [explicit list; no held or future operation]
Execution host and observer: [exact binding]
Tool path/hash: [accepted H00 for subsequent H; separately bound SQL/provider client]
UTC start / expiry: [start and +20 minutes]
Operator / reviewer / abort owner: Chris Watts [confirm abort ownership]
Evidence: development received-<operation>-<UTC>.txt, exclusive new file, retain originals
Budgets/effects/stops: as selected rows; no retry or automatic expansion
Separate decisions excluded: rollout, provisioning, restore, activation and G5
```

**Next approvable action is H00 only** once Chris supplies the UTC window and accepts the
operator/reviewer/abort-owner and receipt envelope. Its sole purpose is binding the observer/tool;
review its receipt before approving H01–H05. SQL/provider/native operations remain held until
their exact client/identity/target bindings and any required new command bytes are reviewed.
