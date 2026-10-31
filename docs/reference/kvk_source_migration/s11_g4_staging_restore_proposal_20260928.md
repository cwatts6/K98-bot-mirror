# Staging and actual-restore proposal — preparation only

Status: DRAFT, NOT EXECUTABLE. Operator approved preparing this proposal after D03/D04/M01 reconciliation. No copy, directory/ACL creation, backup, restore, job change or activation is approved by that preparation decision. Maintenance scheduling is already approved through 2026-09-29T09:23:23Z. Chris Watts remains operator/reviewer/abort owner under the existing single-account model.

## Exact known targets

Source is the retained 119-file chain on MINI_AMD: full set 97337 and log sets 97338 through 97455, in manifest order. No wildcard or filename-time sorting. The last log ends at LSN 19088000155032800001; this is a historical recovery endpoint, not current production and not a point-in-time STOPAT claim. Do not acquire a new tail-log backup or substitute newer media.

Development server is 9SX2VF4\K98DEV (existing localhost\K98DEV connection), master for restore commands, Windows Authentication with observed original SQL login MicrosoftAccount\cwattsconsulting@outlook.com. Reported engine account is NT Service\MSSQL$K98DEV. No new account is proposed.

New database candidate: `S11_G4_Recovery_20260928_97337`.

Root candidate: `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11_G4_20260928_97337`.

Two proposed new children: `media` for immutable staged copies, `data` for restored database files. Under data, the exact MOVE mappings are:

| Source logical name | New physical basename |
|---|---|
| ROK_TRACKER | S11_G4_Recovery_20260928_97337.mdf |
| ROK_TRACKER_log | S11_G4_Recovery_20260928_97337_log.ldf |

All 119 exact source and staged paths, source UUID/LSN/fork metadata, F01 file lengths and both full destination paths are enumerated in `.codex_artifacts/s11-g4-capture-preparation-20260926/staging-restore-targets-draft-20260928.json`, SHA256 `0c4c49fe6cd5d8b7b36821021f6adf2bdb9c9a8d801de08a08b88976f28920cb`. Original 21 development databases/49 catalog files remain protected exclusions, irrespective of names. Sampled D03/D04 absence does not reserve the new root/database.

## Operator-selected manual transfer route

Operator reports that admin manual copying is quick/easy and an existing RDP redirected drive is available at `\\tsclient\C`. Manual transfer is acceptable; no automation requirement or new share/account is introduced. Expected direction is the MINI_AMD RDP session into 9SX2VF4's redirected C drive, but the mapping has not been observed. Before any later approved copy, confirm that mapping and stop if it points elsewhere. Do not assume a UNC server name from the tsclient alias.

`manual-rdp-copy-checklist-draft-20260928.txt` in the evidence root enumerates all 119 source files and corresponding proposed RDP destination paths under the exact new media directory. It is a planning checklist, not copy approval. Admin may perform the transfer manually; manifest equality, lengths and source/destination SHA256 checks remain required evidence, regardless of transfer method. Do not copy an entire LOG/FULL directory, guess files by timestamp, overwrite targets or use cloud transfer. Hash acquisition and target-creation commands still need a bounded execution packet.

Staging must copy only the 119 manifest members to new files, refuse overwrite and preserve partial results on failure. No move, mirror, sync-delete, cleanup, file timestamp rewriting or source mutation. Require source/staged length and SHA256 equality, recording each file separately. Source file locks/identity/stability checks must be designed for the actual transport; a before/after path check alone cannot establish atomic continuity. No source-to-destination hash is available yet.

The proposed destination lies outside the known production prune roots. That does not protect source media during capture or prove development retention. No job disable/stop is proposed as an incidental step. Source deletion/sharing failure, changing metadata/hash or an incomplete file is a stop without automatic retry. Do not silently replace missing media with another backup. A later exact staging packet must specify source-retention protection (for example, transport-supported handles denying write/delete during each verified capture) or an explicit operator-owned alternative. The existing prune review remains partial and unchanged.

## Proposed capacity and execution budgets

Initial restored allocation: 86,959,456,256 bytes. One media copy: 2,815,180,800 bytes. Combined initial footprint: 89,774,637,056 bytes. D02 free space was 1,747,644,268,544 bytes; this is historical, not a reservation. Full file MaxSize values are not a reasonable allocation budget.

Proposed planning budgets, subject to the final executable design and operator decision:

- Require at least 250 GiB available before any target creation/copy, with an abort floor of 100 GiB free. Neither is an existing quota or reservation.
- Allow initial expanded files plus 64 GiB growth/working headroom: 155,678,932,992 bytes including one staged media copy. Stop for review if later log layouts/restore growth exceed that plan. Do not shrink source or restored files to fit.
- Stage serially, one attempt per file; 30 minutes for the entire staging phase. Manual RDP transfer has no demonstrated rate limiter: the earlier planning target of 10 MiB/s is not enforceable by the chosen UI route. Before copy approval either explicitly accept unthrottled manual transfer within the time/byte bounds or use a reviewed throttled helper; do not claim a rate ceiling for manual copying. Additional hashing is I/O too: copying plus independent source/destination hashes can require approximately four times the 2,815,180,800-byte media set in aggregate read/write traffic, excluding transport/cache overhead. No hard device-I/O ceiling is claimed.
- Staged header/layout capture: 119 header reads and file-list reads as needed to prove every log's compatible file layout, serial, maximum 10 seconds per metadata command and 15-second operator cutoff, 20 minutes aggregate; bounded normalized receipt rather than a wide 119-header paste. Exact extraction commands and schema must be prepared before execution approval.
- Media verification, actual restore and post-restore checks need separate operational timeout settings: the observation-only 10-second SSMS setting must not be silently inherited or raised. Proposed restore budget is 30 minutes aggregate, with a 15-minute ceiling per full/log operation and 5-second storage monitoring. These are proposed cancellation thresholds, not hard SQL I/O/growth limits; controller and cancellation behavior must be specified before execution.

No quota, throughput limit or timeout has been installed. Monitoring must stop on low space, unexpected growth, errors or a changed target; interrupted restore remains retained for review, never automatically dropped or restarted.

## Restore sequence for exact review

The complete proposed 119-media sequence is in `commands/RESTORE-SEQUENCE-DRAFT-20260928.sql.txt` under the evidence root, SHA256 `05861b33745550d4052b72200a4730c79bcc50024e49730d002d7de645a5a052`. It starts with an unconditional THROW and has no GO separators: it is review text, not an approved runner. Do not remove the guard or execute selected statements. A later separately sealed execution packet must add live target guards, staged-media identity binding, budgets and receipt handling.

1. Verify staged media identities against the manifest, including every log's BackupSetGUID, database/family/fork, position, LSN continuity and supported file layout. M01 proved only the selected full header/layout. Review added files or file-size changes in the logs before final MOVE/growth design; do not assume the full's two files cover all later media changes.
2. Verify media readability/integrity within explicit I/O budgets. Full has backup checksums; the retained log catalog says no backup checksums. Do not force CHECKSUM on checksum-free logs and pretend success is equivalent. A VERIFYONLY result is supporting evidence, not actual restore proof.
3. Revalidate identity, transaction state, exact database/path absence, protected exclusions, source/staged bindings and free space as guards of the approved mutation, not a rerun of predecessor exercises. Establish only the new directories and required service access using separately reviewed create/ACL commands; no inherited effective-rights assumption.
4. RESTORE DATABASE from staged full position 1 WITH NORECOVERY, CHECKSUM and both exact MOVE mappings. Never WITH REPLACE or CONTINUE_AFTER_ERROR.
5. RESTORE LOG from each of the 118 staged logs in retained manifest order WITH FILE=1, NORECOVERY. Stop on the first failure. No recovery after a partial chain, no automatic retry/resume and no extension to current production.
6. Review all 119 operation receipts, restored file paths/sizes and state before the distinct final WITH RECOVERY checkpoint. Verify ONLINE state, recovered database identity and expected application/schema/data invariants using separately prepared bounded checks. These are read-only acceptance checks, not running Bot writers/importers on the restored database. No Bot connection string change or activation.

Record original/session identity, immutable command hashes, per-file source/staged hashes, per-media identities, per-step times/results, allocated sizes/free-space checks, final database/file identities and acceptance results. Actual restore success does not alone complete all seven typed G4 proofs.

## Remaining exact-decision dependencies

The route question is answered: use admin manual copying through the existing RDP redirected drive. Do not ask it again. Remaining items are observations or implementation details: secure destination creation/ACL and service effective access; transport capture/retention guarantees; staged media hashes and all log identities/layouts; bounded verification/restore controller; post-restore invariants. Do not request key bytes, reopen settled account/report preferences or treat installation gaps as missing source implementation.

All seven G4 typed proofs, actual restore, rollout and G5 retain their current incomplete/unapproved status. Preserve pending/recovered work and all media, including failed partial copies/restores. No cleanup, Git publication, PR, production pull/restart or new task. Memory investigation remains deferred, collector withdrawn and KVK/view issues separate.

Validation: local manifest generation and 119-path uniqueness/length arithmetic; every original source member retained in order; two exact logical-to-physical mappings; draft sequence count and fail-fast guard; original 27 pending/394 evidence files preserved. No SQL/media/transport action. This additive non-executable plan has no runtime/deployment effect: documented security-routing skip, no predecessor tests or broader security discovery. The transfer response is retained in the manifest. Operational hash/create/verification scripts still require exact review; no further preference question is needed.
