# S04R1 receipt — backup candidates, chain incomplete

Bounded metadata observation COMPLETE; usable restore chain remains INCOMPLETE. Operator supplied identity, twelve distinct backup/media rows (two D, two I, eight L) and completion. No sentinel, null media mapping, damaged flag or error observed. One family_sequence_number=1 row appears for each candidate; do not infer physical media completeness from that alone.

Original attachment retained byte-for-byte at `.codex_artifacts/s11-g4-capture-preparation-20260926/received-S04R1-20260928T092536Z.txt` (9,692 bytes). Receipt recorded 2026-09-28T09:25:36Z. Server observed 09:25:13.7585225Z, completed 09:25:13.7759045Z, inside approved maintenance interval 2026-09-28T09:23:23Z through 2026-09-29T09:23:23Z. Client completion and batch-start/stopwatch duration were not supplied; no full elapsed-time assertion.

Accepted mini_AMD / ROK_TRACKER / MicrosoftAccount\cwattsconsulting@outlook.com, VIEW DEFINITION=1 and database CONTROL=1. This is operator evidence, not independent executed-byte, client-continuity or media verification. Backup start/finish times are server-reported unzoned values, distinct from capture UTC.

## Candidate relationships

- Full set 97337 (2026-09-28 01:00 server-reported) has checkpoint_lsn 19080000061546400001 and last_lsn 19080000061548800001; recorded path C:\SQL_BACKUP\FULL\ROK_TRACKER_full_20260928.bak.
- Full set 97037 (2026-09-27 01:00) checkpoint_lsn is 18967000000865600011. Differential 97247 (2026-09-27 18:00) has matching database_backup_lsn and differential_base_lsn. This is a candidate base relationship only; it is not a differential based on the newer full 97337.
- Differential 96946 (2026-09-26 18:00) has base LSN 18807000149900800001, which matches neither captured full's checkpoint. Its base full is outside this sample. Do not confuse full 97037's database_backup_lsn with its own checkpoint or manufacture a base.
- Logs 97448–97455 share database_backup_lsn 19080000061546400001, matching latest full's checkpoint. Each successive captured first_lsn equals the prior captured last_lsn. The earliest captured log starts at 19084000117953600001, beyond full 97337's last_lsn, so the sample does not bridge that full to this log tail. Recovery fork/GUID/media-position metadata is also absent; equality alone does not prove a usable chain.

All candidates report FULL recovery, is_copy_only=0 and is_damaged=0. Full/differentials report has_backup_checksums=1; all eight logs report 0. These catalog flags are not physical validation or proof of corruption/health. All recorded paths lie under the partially understood C:\SQL_BACKUP prune roots.

Set 97454 records 4,480,888,832 backup bytes and 806,708,844 compressed bytes, materially larger than neighboring sampled logs. Retain for later media/I/O budgeting only; no memory-cause or workload investigation is resumed. Backup recorded sizes are not file existence/current length or restore storage requirements.

Exact rows/LSNs and seven checked adjacent log boundaries are retained in `s04r1-local-analysis-20260928.json`. No LSN was converted to floating point.

## Next grouped preparation

Use a coherent recovery-metadata packet rather than repeated latest-N samples: choose an explicit retained full anchor and a bounded fixed historical log interval, include identity/fork/media-position fields needed to assess continuity, and describe independent row/byte/time caps and stops. Avoid recapturing already sufficient fields except where additional identity binding is essential. No automatic paging or inferred chain acceptance. Choosing an anchor for analysis does not choose or approve a restore target.

Development database/file exclusions and exact storage targets remain separately bound to the development host; do not query production to infer them. Prune filters/timestamp/cutoff/exclusions and full runtime effects remain incomplete. Media access, restore/file mapping, provisioning and actual restore require separate exact decisions. No new query or file read is authorized by this receipt.

The maintenance window stays approved through 2026-09-29T09:23:23Z: do not ask again for scheduling approval within it. Prepare larger related bounded packets as requested. New action/target scope still needs concrete approval; window approval is not deployment/restore/G5 approval.

All seven typed G4 proofs and actual restore remain incomplete. Preserve pending/recovered files, isolated hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues.

Validation: twelve-row parsing, exact integer-string LSN comparison, counts/flags/window, receipt/proposal hashes and original 27 pending/394 evidence preservation. Documentation/evidence only; no live/media read, tests/predecessor runs or security discovery.
