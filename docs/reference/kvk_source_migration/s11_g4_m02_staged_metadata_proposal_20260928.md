# M02 — staged backup identities, continuity and file layouts

PREPARED FOR EXACT APPROVAL, NOT EXECUTED. Operator requested the next preparation after ST04 matched all 119 staged hashes to ST01R1. This is a new development SQL media-read scope. It does not restore a database or authorize subsequent verification/restore commands. Existing maintenance window ends 2026-09-29T09:23:23Z; Chris Watts remains operator/reviewer/abort owner.

## Exact target, command and client settings

Use the existing development SSMS connection `localhost\K98DEV`, database **master**, Windows Authentication. Guard requires observed server `9SX2VF4\K98DEV`, machine 9SX2VF4, instance K98DEV, ORIGINAL_LOGIN `MicrosoftAccount\cwattsconsulting@outlook.com`, sysadmin=1 and SQL major version 16. Do not use production MINI_AMD or open a new connection through a helper. Standalone transaction-state capture must show no transaction and implicit transactions off; do not commit/rollback unrelated state to pass.

Open complete saved file `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/M02.sql` in that connection. Execute once, no partial selection or GO-separated fragments.

SHA256: `317b4f535b17ee2a2ba04643b895ded3a4d838caaf4d2ee1c67187a6aca1d06f` (36,645 bytes).

Exact scope approval includes setting this query's SSMS execution timeout to **120 seconds**, replacing the earlier observation-only ten-second setting for this operation. Operator cancellation cutoff **130 seconds** for the whole batch; do not increase it or retry. Use Results to Grid and preserve each evidence_json cell in full (up to 2,048 characters); if the client cannot retain complete cells, stop rather than accept truncation. Restore the query timeout to ten seconds after completion/cancellation has returned control, before unrelated observations. No SQL Server configuration changes.

## Fixed inputs and operations

119 literal staged paths, exactly matching the ST04-verified set in `staging-restore-targets-draft-20260928.json`: full set 97337 plus logs 97338–97455, all directly under `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11_G4_20260928_97337\media` on 9SX2VF4. No wildcards, folder discovery or newer-file substitution. Source/destination hashes are retained in `source-destination-hash-matches-20260928.json`; this SQL batch does not recompute SHA256 or assume hashes reserve future file contents.

For each set, serially execute RESTORE HEADERONLY WITH FILE=1 and RESTORE FILELISTONLY WITH FILE=1 from that one staged file. Two metadata calls per set, **238 calls total**, one outstanding at a time. No CHECKSUM scan, VERIFYONLY, LOADHISTORY, BACKUP, RESTORE DATABASE/LOG, RECOVERY, REPLACE, application stored procedures, process/job/task control or provider/Discord calls.

Header guards require one row with exact UUID, type, position, database, first/last LSN, BindingID, family and recovery forks from retained evidence. Require no recorded damage/incomplete metadata/snapshot/copy-only/encryption and expected backup-checksum flags (full=1, logs=0); unknown/mismatched values stop, not a request for keys or automatic amendment. Check full checkpoint, first-log coverage of full end and each of the following 117 exact adjacent log boundaries. The accepted endpoint remains historical LSN 19088000155032800001, not current production.

File lists must contain 1–8 rows, D/L types only, no TDE/snapshot metadata, and only logical names ROK_TRACKER/ROK_TRACKER_log. Capture file IDs/GUIDs, original physical paths, Size/MaxSize, creation/drop LSN and IsPresent/IsReadOnly for later comparison. Do not assume IsPresent=1 or unchanged sizes across logs; returned evidence is reviewed before final MOVE/growth design. Original physical paths are evidence only and are never accessed or restored to by this batch.

## Effects and resource bounds

Creates two session-local temporary tables `#M02Header` and `#M02Files` in tempdb, plus table variables for 119 expected rows and bounded evidence. Refuse pre-existing same-name temporary objects instead of dropping them. Delete only rows of these newly created temporary tables between sets. No persistent user schema/table/data changes, no database creation or backup-history import. Temporary objects remain session-local after completion/failure; do not run cleanup or retry merely because they remain.

Changes only query-session NOCOUNT, LOCK_TIMEOUT=1000 ms, DEADLOCK_PRIORITY=LOW and ANSI_WARNINGS=ON. Normal metadata I/O, tempdb allocation, audit/cache/resource activity occur. Identity/guard queries are catalog/session reads. SQL service media-read capability may be demonstrated by successful completion but its full token/ACL effectiveness is not otherwise inspected.

120-second cooperative batch budget checked between media calls and at completion; 130-second operator cutoff, with SSMS timeout set to 120 seconds. Synchronous calls can overrun cooperative checks and cancellation may take time; no hard disk I/O-rate/byte ceiling claimed. The known staged set totals 2,815,180,800 bytes, but metadata processing is not asserted to read exactly that amount or scan all content. Stop rather than raise budget if this scope cannot complete.

Maximum accepted header rows 119 and file rows 952 (8 per set), projected evidence rows at most 1,071. JSON cell limit 2,048 characters; total JSON UTF-16 payload limit 512 KiB. The file-list capture checks row count after INSERT EXEC, so this is an acceptance bound, not a hard pre-read row/memory cap. ANSI_WARNINGS prevents silent string truncation into evidence cells. Identity result and small completion result are additional. Each set emits a short NOWAIT message; final evidence rows emit only when the whole loop succeeds. No deeply nested serialization or broad catalog/session inventory.

## Evidence and stops

Preserve identity result, all evidence_json rows, completion row (checked_backup_sets=119, evidence_rows, elapsed_ms), messages and client completion time as a text attachment. Expected usual evidence count is 357 if all file lists contain two rows; do not use that expectation as a substitute for checking every set/file. Maximum overall supplied output 1 MiB including formatting; use copied grid cells rather than fixed-width 2,048-character padding per row. Do not accept truncated/ellipsized cells or an error followed by partial results as success.

Stop on identity/visibility/transaction/version/temp-object mismatch, permission/media/schema-conversion error, different UUID/LSN/fork/flags, unsupported layout, deadline/output limit or missing completion. Do not grant permissions, request keys, retry, change targets or run remaining statements selectively. Keep all media and existing artifacts. A failure does not authorize cleanup or restore.

M02 success proves returned metadata can be read and matches selected guards at observation. It does not verify all backup pages/checksums, validate data, prove an actual restore or issue any of the seven typed G4 proofs. Stage-readability/integrity checks and actual restore remain later exact operator decisions; rollout/G5 remain unapproved.

## Source validation

Metadata result schemas were taken from current authoritative SQL repo examples: `performance_remediation/kingdomscandata4/phase1/update_all2_rehearsal/15_restore_update_all2_benchmark_database.sql` (59-column SQL 2022 header shape) and `phase2/05_restore_preflight_backup_to_recovery.sql` (file-list shape), under `C:\K98-bot-SQL-Server`. These are source references only, not predecessor scripts to execute. Official field/command references: [RESTORE HEADERONLY](https://learn.microsoft.com/en-us/sql/t-sql/statements/restore-statements-headeronly-transact-sql?view=sql-server-ver17) and [RESTORE FILELISTONLY](https://learn.microsoft.com/en-us/sql/t-sql/statements/restore-statements-filelistonly-transact-sql?view=sql-server-ver17).

Local validation checked every literal path/UUID and chain boundary against the retained manifest, the exact loop bound and exclusion of effectful restore/backup commands. SQL was not compiled/executed against a server; runtime result-shape compatibility remains a guarded observation, not locally proved. No SQL repo source was edited. Initial local generator quoting error occurred before a query file was written; corrected locally, with no live attempt.

Security routing: documented skip for additive inert approval artifacts only; manually reviewed literal-only dynamic statement construction, tempdb effects, projected output and fixed loop/limits. No Bot/SQL implementation, PR or deployment. No broad security scan, predecessor rerun or unrelated runtime tests. Original pending files and sealed evidence remain unchanged. Deferred memory investigation, withdrawn collector and separate KVK/view issues stay outside this operation.
