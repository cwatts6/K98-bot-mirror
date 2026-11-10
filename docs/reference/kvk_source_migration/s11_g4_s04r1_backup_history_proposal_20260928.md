# S04R1 — bounded backup-history candidates

PREPARED, NOT APPROVED OR EXECUTED. Exact query `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S04R1.sql.txt`.

SHA256: `318442f3278d332100c9bc53c5e20a1fb0179730b164118c094819fb5d738ecf`.

## Scope and target

Existing SSMS connection on MINI_AMD, current database ROK_TRACKER, accepted SQL ORIGINAL_LOGIN MicrosoftAccount\cwattsconsulting@outlook.com. Read only msdb.dbo.backupset and msdb.dbo.backupmediafamily for database_name ROK_TRACKER. Chris Watts remains operator/reviewer/abort owner; Windows/UI identity remains separate. No new connection or native identity claim.

This updates retained S04's latest-twelve selection to at most two latest database/full (D), two differential (I) and eight log (L) sets, ordered within type by finish date and backup_set_id. Frequent logs cannot consume the entire candidate budget. These counts do not guarantee the correct base or an unbroken restore chain. It includes copy-only/damaged entries for honest observation rather than silently hiding them. Other types are outside scope.

Output set/media IDs, type, start/finish dates, five retained LSN fields, recovery model, copy-only/checksum/damage flags, recorded/compressed sizes, family number and recorded device path. LEFT JOIN preserves sets missing a media-family record as null fields. No file access follows from returning a path; recorded paths are not proof that media exists or is safe from pruning. No credential, module or command text query. If unexpected secret-bearing device metadata appears, keep it local and report a redacted stop rather than paste it.

## Reused evidence and separation

Six Agent commands have exact source matches; job hashes/schedules remain retained. Prune has a matching display hash and partial operator report: LOG/DIFF/FULL roots, 3/14/14 days, recursive and Force/SilentlyContinue deletion. Timestamp/cutoff, complete filters/exclusions/dependencies and review duration remain open. S04R1 does not resolve or waive those gaps. No media destination is approved for restore/reservation, and no pruning changes are authorized.

## Guards, budgets and effects

Exact S03R2 guard/identity prefix retained: isolated transaction/count/implicit checks, target/login, VIEW DEFINITION and database CONTROL, session SETs, identity row and sysadmin observer gate. Existing guard wording mentions session visibility; privileged observer requirement applies here without any grant or application-principal change.

Three result sets: one identity row; zero to 49 set/media rows representing at most 12 distinct selected sets; one completion row. Forty-nine is the sentinel for a 48-row media budget. Missing categories/bases/media mappings are retained gaps and stop downstream use, not grounds for an automatic wider query. Null/unfinished timestamps, damage or unexpected recovery metadata require reconciliation. No automatic claim that a chain is valid even when all rows fit.

One attempt, one batch, 64 KiB output, ten-second current-tab timeout, fifteen-second operator cutoff, one-second lock timeout, MAXDOP1. TOP limits results, not all msdb scans/sorts/CPU/memory/I/O. No transactionally consistent historical snapshot or source-to-media correspondence is proved. Backup dates have no timezone annotation here; retain as server-reported values, not UTC. Recorded backup sizes are not a restore capacity reservation.

Effects: catalog reads/audit/resource/locking, scalar assignments, retained NOCOUNT ON/LOCK_TIMEOUT1000/DEADLOCK_PRIORITY LOW and editor/history/autorecovery. No BACKUP, RESTORE, VERIFYONLY, FILELISTONLY, CHECKDB, file/media read, directory enumeration, SQL mutation, job/task control, provisioning, import/export, provider/Discord, deployment/restart or publication.

## Execution and stops after exact approval

Fresh twenty-minute UTC window required. Same existing SSMS session only; stop if unavailable/disconnected, target changed, unrelated editor work exists or reconnect/auth/certificate prompt appears. No new connection/settings/TLS/client. Five-second connection timeout unestablished; invisible automatic reconnect cannot be excluded.

Replace only previous capture text with complete query; verify marker `S04R1 backup history candidates completed`; confirm ten-second timeout; execute entire batch once, not selection. Start timing before Execute; cancel at fifteen seconds, report if still running. Cancellation does not prove server quiescence.

Stop on errors/guards, identity/visibility mismatch, sentinel, missing/ambiguous media metadata, damaged/unfinished candidates, secret-bearing metadata, truncation/output beyond 64 KiB, unexpected/missing sets or completion, or time cap. Preserve safe output/errors and timing. No retries, paging, expanded dates, file opens, grant/revoke, KILL, reconnect or COMMIT/ROLLBACK/state repair. No chain extension or later operation inherits approval.

## Validation and proof status

Local comparison to retained S04 fields and S03R2 prefix; explicit D/I/L partitions, per-partition caps and missing-media preservation. No application schema inference or live validation. Documentation/inert metadata preparation retains security-routing skip; runtime/predecessor tests, PR validators and security discovery inapplicable.

Actual restore and all seven typed G4 proofs remain incomplete; rollout/G5 remain unapproved. Preserve pending/recovered work, isolated hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues.
