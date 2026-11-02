# PD01 + V02 — new data directory and exact MOVE verification

PREPARED FOR EXACT APPROVAL, NOT EXECUTED. Two ordered operations on development 9SX2VF4 only. Chris Watts is operator/reviewer/abort owner; same Windows-account/admin model, no new accounts or privileges. Existing maintenance window ends 2026-09-29T09:23:23Z. Actual restore, final recovery and G5 are not included.

V01 verified all 119 sets but warned about the original production MDF/LDF paths because it had no MOVE clauses. Its media evidence remains accepted with that qualification. V02 checks the proposed destinations using only the single full backup; it does not repeat the 118 log verification operations.

## Exact paths

Existing root: `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11_G4_20260928_97337`.

New child to create: `data`. Do not reuse an existing child. Existing media child/marker and every retained database/file are untouched.

Proposed database remains `S11_G4_Recovery_20260928_97337`, but is not created here.

| Logical file | Exact proposed physical file |
|---|---|
| ROK_TRACKER | C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11_G4_20260928_97337\data\S11_G4_Recovery_20260928_97337.mdf |
| ROK_TRACKER_log | C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11_G4_20260928_97337\data\S11_G4_Recovery_20260928_97337_log.ldf |

Only source media read: existing staged `media\ROK_TRACKER_full_20260928.bak`, position 1, set UUID 70E5C6BF-4A0A-4A48-B6F1-E6E653E8A36D. No MINI_AMD or original-source-path access.

## Commands and hashes

All commands are under `.codex_artifacts/s11-g4-capture-preparation-20260926/commands`.

| File | SHA256 |
|---|---|
| PD01.ps1 | `9f06d151c6211f593602367663a5eacead216b27ae8ae748c11c3664c65d22f4` |
| PD01-launch.txt | `2d90a7cebd841f603ab9313d57bf5fb5833df92074abf953121267407707a717` |
| V02.sql | `3a1309485d585be4c464c310a194a8ea828373295e9412fc9760293fa63a2ae6` |

1. PD01: use existing development PowerShell and the single saved-file hash-check launcher. It checks seven existing parent boundaries for directory/non-reparse attributes, C: ready NTFS/free space at least 250 GiB, and exact data-child absence. New-Item without Force creates only that child; capture owner/SDDL; confirm both proposed MDF/LDF absent. No file data is created, ACL edited, SQL queried or directory traversed recursively. Stop if the data child already exists, even if empty. No elevation/policy/permission workaround.
2. Only after PD01 Completed with Created=true and both Present=false: V02 in existing development SSMS `localhost\K98DEV`, master, Windows Authentication. Guards require 9SX2VF4\K98DEV, machine/instance, observed MicrosoftAccount\cwattsconsulting@outlook.com original login, sysadmin=1, SQL major 16 and clear transaction state. Require database-name absence and neither destination path registered in sys.master_files. These SQL checks complement PD01's sampled physical absence, not atomic reservations or alias/race-proof access.
3. V02 reads the full header into new session-local #V02Header and verifies exact UUID/LSNs/family/fork/checksum/encryption/damage flags. It then issues one VERIFYONLY WITH FILE=1,CHECKSUM,STOP_ON_ERROR and both exact MOVE mappings. No database/log restore, RECOVERY, REPLACE, LOADHISTORY, backup, source write or cleanup. No MDF/LDF creation is requested by VERIFYONLY.

## Effects and limits

PD01 creates one directory with inherited ACLs and reads metadata/ACL/capacity. Ten-second cooperative checks, fifteen-second operator cancellation cutoff, one attempt, 16 KiB JSON ceiling. Failure can leave the directory created; retain it, report Created/status and do not rerun or delete it. Free capacity is a snapshot, not reservation; initial restored allocation is 86,959,456,256 bytes, with the separate growth/headroom plan still pending actual-restore approval.

V02: one full-backup HEADERONLY and one full CHECKSUM VERIFYONLY; source physical file length 1,173,233,664 bytes and logical backup content 7,304,765,440 bytes. Verification may decompress/process the logical content; no hard I/O/CPU cap claimed. Tempdb header rows and query-session settings NOCOUNT, LOCK_TIMEOUT=1000, DEADLOCK_PRIORITY=LOW, ANSI_WARNINGS=ON only. No permanent application objects modified. Pre-existing #V02Header means stop, not drop/reuse.

Exact scope includes SSMS query timeout **120 seconds**, cooperative budget 120 seconds and operator cutoff **130 seconds** for V02. After control returns, reset query timeout to ten seconds. No settings assumption is made from the earlier unconfirmed reset. These are cancellation thresholds, not guarantees for blocked system calls. Maximum combined execution allowance 145 seconds, excluding operator receipt review. V02 output: identity row, two proposed mappings, completion or failure row and Messages; maximum accepted 64 KiB.

## Acceptance and stop conditions

Require full PD01 JSON. For V02 preserve identity, both mappings, completion, all Messages and client completion time. The completion marker explicitly says to inspect Messages: SQL warnings can coexist with command completion, as V01 demonstrated. Require the valid-backup message and no unresolved destination warning before accepting destination validation. New warnings/errors mean stop and review, not switch paths or loosen guards.

Stop group on wrong target, existing path/database, reparse/access/schema/media/identity failure, capacity/time/output limit, incomplete receipt or any relevant warning. No retries or automatic rollback/cleanup. Retain created data child and all original/staged evidence. No existing files may be overwritten or moved. A successful destination check still does not prove SQL create/write behavior under actual restore or logical data consistency.

Actual restore remains a later separately sealed mutation: full plus 118 logs WITH NORECOVERY, final recovery and integrity/preservation acceptance checkpoints. Do not execute or remove the guard from the historical restore draft. All seven typed G4 proofs and actual restore remain incomplete; rollout/G5 unapproved.

## Local validation

PD01 parsed locally without execution. V02 paths and logical names match the manifest and M02's invariant two-file layout; header schema and identity guards reuse observed working forms. Checked one HEADERONLY/one VERIFYONLY, two exact MOVE clauses, absence/catalog guards, TRY/CATCH stop and absence of actual restore/history import. SQL was not run/compiled against a server. Earlier V01 receipts/seals and original 27 pending/394 evidence files remain unchanged.

Security routing: documented skip for inert approval preparation only; file creation is a new explicit effect covered by this proposed decision, with no existing ACL/runtime change. No codebase scan, predecessor suite, PR or publication. [Microsoft relocation guidance](https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/restore-a-database-to-a-new-location-sql-server?view=sql-server-ver17) supports VERIFYONLY with the planned MOVE parameters. Memory investigation stays deferred, collector withdrawn, separate KVK/view issues retained.
