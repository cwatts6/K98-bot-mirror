# V01 media verification and subsequent restore checkpoint

PREPARED, NOT EXECUTED. This exact approval request covers **V01 verification only**. The actual restore remains a separate decision after the verification receipt; the existing restore draft retains its unconditional THROW. Chris Watts is operator/reviewer/abort owner. Existing maintenance window ends 2026-09-29T09:23:23Z; no renewed scheduling preference is needed within it.

## Established basis

ST01R1 and ST04 match all 119 source/staged files by set ID, name, bytes and SHA256. M02 now has identity, 119 matching media headers, 238 identical two-file layout rows, completion and Messages receipts. First-log coverage and all 117 adjacent log boundaries match; endpoint is LSN 19088000155032800001. Full-backup checksum flag is true; all logs false. Expanded allocation is 86,959,456,256 bytes and staged media total 2,815,180,800 bytes. No source rerun, copy or predecessor test is needed.

The M02 query-timeout reset to ten seconds remains unconfirmed. Do not infer that current SSMS setting; the V01 decision explicitly specifies a different setting below, followed by reset. This is not a missing media-result issue.

## V01 exact execution target and hash

Saved command `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/V01.sql`, 33,902 bytes.

SHA256 `bf967730cf0b9f604c097a1d7f391f809d9a9fe0d2dfed9ba2ee7f496a357cc1`.

Execute the whole saved file once in existing development SSMS connection `localhost\K98DEV`, **master**, Windows Authentication. Guards require 9SX2VF4\K98DEV, machine 9SX2VF4, instance K98DEV, ORIGINAL_LOGIN MicrosoftAccount\cwattsconsulting@outlook.com, sysadmin=1 and SQL major 16. Captured transaction state/count and implicit-transactions setting must be clear; do not modify unrelated transactions to pass.

Proposed approval includes setting this query's client execution timeout to **600 seconds** and an operator cancellation cutoff of **610 seconds total**. Do not start if those limits cross the maintenance-window end. Restore the query timeout to ten seconds after control returns. No server configuration change or new connection. No automatic restart if cancelled.

## Fixed operations and effects

The exact 119 staged paths/UUIDs/first-last LSNs are embedded in the same manifest order under the existing development media directory. For each set, issue one HEADERONLY position-1 read as an in-operation identity guard, then one VERIFYONLY. These guard reads are required immediately before the heavier operation, not a standalone repeat of M02 evidence collection. Maximum 119 HEADERONLY plus 119 VERIFYONLY commands, serial, no discovery or retry.

Header guards compare UUID, type, position, ROK_TRACKER database, first/last LSN, BindingID, family/recovery-fork identity, damage/incomplete/snapshot/copy-only/encryption flags and expected checksum flag. Unexpected header count/shape or mismatch stops without changing the candidate. The 59-column header schema is the already-successful M02 schema.

Full set 97337: `RESTORE VERIFYONLY ... WITH FILE=1, STOP_ON_ERROR, CHECKSUM`.

Each of 118 logs: `RESTORE VERIFYONLY ... WITH FILE=1, STOP_ON_ERROR`, using default behavior; **not** a claim of backup-checksum verification when none was recorded. Do not add CHECKSUM to checksum-free logs, NO_CHECKSUM to bypass a full-backup failure, or CONTINUE_AFTER_ERROR. No MOVE, LOADHISTORY, RESTORE DATABASE/LOG, RECOVERY, BACKUP, production SQL, provider/Discord, job/task/process control or source-file access.

Effects: read staged media through SQL Server, decompression/verification CPU and I/O, ordinary audit/cache activity, one session-local `#V01Header` table and small expected/receipt table variables. DELETE affects only newly created temporary header rows between sets. Existing temp-name collision stops rather than dropping/reusing it. No persistent application data/schema or restore database is created. NOCOUNT, LOCK_TIMEOUT=1000 ms, DEADLOCK_PRIORITY=LOW and ANSI_WARNINGS=ON are query-session settings. No temp-object cleanup is authorized as a failure workaround.

## Resource budget and evidence

One attempt/batch, 600-second cooperative elapsed checks between operations, client timeout 600 seconds and operator cutoff 610 seconds. A blocking SQL command can exceed cooperative checks and cancellation may take time; no hard disk throughput/CPU/memory cap is claimed. LOW deadlock priority does not imply low CPU priority or throttling.

Physical staged media total 2,815,180,800 bytes. Catalog logical backup-byte sum is 16,410,722,304 bytes; verification may decompress/process that larger amount. Neither quantity is an enforced I/O ceiling, and file allocation sizes are distinct. No new backup, extracted copy or database allocation is part of V01. If verification exceeds the agreed time budget, stop rather than raise it.

Output: initial identity row, one NOWAIT progress message per set plus SQL verification messages, 119 receipt rows (set_id, verify_mode, started/finished UTC, PASSED), and final completion with verified_sets=119. On an exception, emit only failed set/ordinal/time/error number, then rethrow SQL's error. Preserve all Messages and result sets as an attachment; maximum accepted output 256 KiB including messages. Stop on excess/truncation and report rather than paste a large dump.

No error, all 119 PASSED rows, expected modes/count/order and final completion are required for acceptance. A partial PASSED prefix or progress message is not a success receipt. Stop on any error, identity/schema/permission/media issue, unexpected count, time/output limit or cancellation. Do not retry individual media, grant rights, alter files or proceed to restore.

## Actual restore checkpoint — separate decision, not executable yet

Retain exact database `S11_G4_Recovery_20260928_97337` and new data child under the already-created root. Existing 21 development databases/49 files remain protected. Proposed MDF/LDF basenames and 119-media order remain those in `staging-restore-targets-draft-20260928.json` and `RESTORE-SEQUENCE-DRAFT-20260928.sql.txt`; do not remove their execution guard.

After V01 reconciliation, prepare the following as concrete guarded mutation/acceptance commands before requesting actual restore approval:

1. Local destination preflight/create: freshly absent data child and MDF/LDF, at least 250 GiB available with a 100 GiB abort floor, new-child-only creation and inherited ACL receipt. No change to parent permissions. Existing media/root retained. Guard current exact database/path/catalog exclusions as part of mutation, not a predecessor rerun.
2. Full WITH NORECOVERY/CHECKSUM/MOVE to the two disjoint physical files, then exactly 118 ordered log WITH NORECOVERY operations, stop on first failure. No REPLACE, automatic retry/resume/drop, tail-log acquisition or source/current-production substitution. Bind each step to staged identity, state, file paths and immutable command receipt.
3. Separate final recovery decision after all 119 restore receipts are reconciled. No RECOVERY on a partial chain. Capture database/file identities/state/size and exact restored-chain evidence before later use.
4. Bounded integrity and original-row/receipt/fence preservation checks, followed by reviewer acceptance, before any install/tests. This is a requirement in the release packet; online state or VERIFYONLY cannot substitute. Exact checks must be derived from authoritative schema and retained target state, with costs/budgets reviewed. No Bot writers, imports or migrations are implicit.

Initial files plus one media copy require 89,774,637,056 bytes; the proposed 64 GiB additional working/growth headroom makes 158,494,113,792 bytes. Earlier draft's 155,678,932,992-byte figure omitted the media copy despite its label; retain that sealed history and use this corrected arithmetic. No growth quota/reservation is installed. Actual restore may require log initialization and more I/O than media verification; later time/monitoring budgets must be explicit. A staging root existing does not prove SQL service create rights.

## Validation and references

Local checks: all 119 literal path/UUID/LSN tuples preserved, full-only CHECKSUM branch, STOP_ON_ERROR, bounded serial loop, TRY/CATCH rethrow on command failures, no LOADHISTORY/restore mutation/source access, and exact schema reuse from M02. SQL not executed or recompiled locally. Original pending and sealed evidence preserved. No SQL repo source edit, runtime implementation, PR or deployment.

Documented security-routing skip is limited to inert approval preparation; dynamic SQL paths are fixed manifest literals and quoted, output is narrow, effects explicitly reviewed. No broad scan/predecessor suite. Official references: [VERIFYONLY scope and options](https://learn.microsoft.com/en-us/sql/t-sql/statements/restore-statements-verifyonly-transact-sql?view=sql-server-ver17) and [checksum behavior and absent-checksum limitations](https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/enable-or-disable-backup-checksums-during-backup-or-restore-sql-server?view=sql-server-ver17). VERIFYONLY supplements actual restore; it does not establish logical database consistency.

All seven typed G4 proofs and actual restore remain incomplete; rollout/G5 unapproved. Preserve all media and partial artifacts. Memory investigation deferred, historical collector withdrawn, KVK/view issues separate; no new task or publication.
