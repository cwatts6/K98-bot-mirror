# S04R2 — grouped fixed recovery-interval metadata

PREPARED, NOT APPROVED OR EXECUTED. Query `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S04R2.sql.txt`; exact SHA256 is recorded in the companion proposal seal and approval request.

## Scope and fixed targets

Same existing SSMS session: MINI_AMD / ROK_TRACKER, accepted SQL ORIGINAL_LOGIN MicrosoftAccount\cwattsconsulting@outlook.com. Chris Watts is operator/reviewer/abort owner. Read only msdb backupset/backupmediafamily. Maintenance scheduling is already approved through 2026-09-29T09:23:23Z; no renewed window approval requested. This request approves only the new query scope, not backup/media/restore operations.

Group two related gaps in one batch:

1. Add backup-set/database/family GUIDs, first/last recovery-fork GUIDs, fork-point LSN and media position for exact full set 97337 and log tail 97448–97455. Retain requested IDs even if missing. Re-emitted LSNs bind new identity fields to retained observations; this is not another latest-N survey.
2. Capture previously missing LOG metadata where last_lsn > 19080000061548800001 and first_lsn < 19084000117953600001, database ROK_TRACKER, backup_set_id <=97455. These are the retained full-end and earliest tail-start boundaries. No finish-date/timezone inference or floating-point LSN arithmetic. Include overlaps and different identities/forks for reconciliation rather than silently excluding incompatible rows. The upper set ID fixes the historical horizon; later backups are not pulled in automatically.

Guards confirm retained full 97337/type D/checkpoint 19080000061546400001/last LSN, and tail start 97448/type L/first LSN before capture. Missing/changed anchor stops. Original S04R1 guard prefix is unchanged, including isolated transaction checks, target/login, database visibility, sysadmin observer, session SET effects and identity row.

Identity result includes requested ID, type, GUIDs/forks/position, retained LSNs and present flag. Interval result includes set/media identity, GUIDs/forks/position, start/finish dates, first/last/base LSNs, copy-only/checksum/damage flags, recorded sizes, family number and device path. No media bytes, module/command text or application table data.

## Budgets and interpretation

Four result sets: one identity row; nine retained-set identity rows; zero to 257 interval/media rows; one completion row. Interval budget 256 rows plus sentinel: 257 stops without paging. Output maximum 512 KiB. One attempt, one batch, ten-second current-tab timeout, fifteen-second cancellation cutoff, one-second lock timeout and MAXDOP1 on both output queries. TOP does not hard-bound msdb scan/sort/hash/CPU/memory cost. No automatic retries or enlarged caps.

Full and logs are analysis candidates only. Matching GUIDs/LSNs and no apparent gap may support a catalog chain candidate but do not prove restorability, media existence/complete stripes, readability, file hashes, SQL version compatibility, destination disjointness, capacity or prune protection. Fork transitions/overlapping chains require explicit review, not automatic chain choice. The interval predicate is for missing candidate rows, not a general-purpose restore-chain algorithm. Restore selection/order/STOPAT remain unapproved.

Prune timestamp/filter/exclusion/dependency gaps stay open. Candidate media paths remain under prune roots; no copying, moving, reservation, deletion or pruning changes are authorized. Server backup times remain unzoned; capture UTC is separate. SQL scalar/read statements are not one transactional snapshot.

## Effects and execution stops

Catalog read/audit/locking/resources, scalar assignments, persistent NOCOUNT ON/LOCK_TIMEOUT1000/DEADLOCK_PRIORITY LOW, and SSMS editor/history/autorecovery only. No BACKUP/RESTORE/VERIFYONLY/FILELISTONLY/CHECKDB, media/filesystem reads, job control, provisioning, SQL mutation, provider/Discord, deployment/restart or publication.

Use same existing session, no new connection/settings/TLS/client. Stop on unavailable/disconnected/changed target, unrelated editor work or reconnect/auth/certificate prompt. Five-second connect timeout unestablished; invisible automatic reconnect cannot be excluded. Replace only previous capture text with the full query; check marker `S04R2 fixed recovery interval metadata completed`; confirm ten-second timeout and execute once in full. Start timing before Execute; cancel at fifteen seconds and report if still running. Cancellation is not proof of quiescence.

Stop/reconcile on errors/guards, missing retained rows or required GUID/position/media fields, type mismatch (97337 D, others L), damaged/unfinished sets, unexpected identity/fork change, row sentinel, oversized/truncated/secret-bearing path output, unexpected result shape or missing completion, timeout or unbridged interval. A null fork_point_lsn alone is not a missing-field failure; no fork transition may require one. Do not guess meaning of missing fields or retry. Return safe results/errors; keep any secret-bearing path local and report redacted stop. No additional inspection or chain extension follows automatically.

## Local validation and remaining proof

Static review checks prefix equality, literal nine IDs and fixed numeric boundaries, category/upper-ID restriction, LEFT JOIN missing-row preservation and 257 sentinel. Backup UUID/database/family/position fields are used by retained SQL-repository recovery scripts; those scripts were searched as source, never executed. No live syntax validation. Documentation/inert-capture security-routing skip; no runtime implementation/PR, predecessor tests or security discovery.

All seven typed G4 proofs and actual restore remain incomplete; rollout/G5 unapproved. Preserve pending/recovered evidence, isolated hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues.
