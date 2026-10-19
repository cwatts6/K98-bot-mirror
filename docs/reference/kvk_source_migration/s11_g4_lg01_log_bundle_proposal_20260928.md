# LG01 — select, copy and verify the exact 118 logs

PREPARED FOR EXACT OPERATION APPROVAL; not run. Operator approved preparing a folder-copy helper because manual selection of 118 logs was impractical. The full backup is reported manually copied to development; destination hash verification remains pending. Do not recopy it.

## Exact targets and commands

Host MINI_AMD, existing Windows account/PowerShell. Input: exactly sets 97338–97455 from `received-ST01R1-20260928T123029Z.json`, embedded as 118 literal source paths, lengths and SHA256 values. No discovery, wildcards, date filters or filename sorting. Total log bytes **1,641,947,136**. Full set 97337 is excluded.

New bundle directory: `C:\Users\cwatt\Downloads\S11-G4-logs-20260928-97338-97455`. Existing directory means stop, never reuse/overwrite. Create only this directory and its 118 named log files. No ZIP or compression, source move/deletion, cleanup, timestamp changes, ACL editing, elevation/policy change, new account/share or job control. The directory is outside known source prune roots; inherited ACL is captured, not hardened or claimed SQL-readable. Existing source retention is not modified.

Saved script: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S11-G4-LG01.ps1`.
SHA256: `dac35a6a9254894ae1b8646d3ff918f58e05354a6f1bd0c44a9374c6608dd263`.

After approval, copy this small script unchanged to the new file `C:\Users\cwatt\Downloads\S11-G4-LG01.ps1` on MINI_AMD using the settled manual method. Refuse existing-file overwrite or missing-directory/elevation workarounds. Use the exact one-line hash-check launcher in `commands/LG01-launch.txt`; never paste the full multiline script. Execution-policy or script-hash failure means stop without bypass/retry.

## Behavior and budgets

Check the six exact existing boundaries C:\, C:\Users, C:\Users\cwatt, its Downloads directory, C:\SQL_BACKUP and C:\SQL_BACKUP\LOG for directory/non-reparse attributes. Require ready NTFS C: and at least 10 GiB available before creating the new bundle. Require at least 8 GiB free before each file. These are snapshots, not disk reservations or continuous quotas.

Serially open each source read-only with FileShare.Read, denying new write/delete opens while held. Destination is CreateNew/ReadWrite/FileShare.None: an existing file fails without overwrite. Copy and calculate source SHA256 in a single streamed pass, compare against the embedded ST01R1 hash, check sampled length/mtime, flush the copy, then re-read the copy through the same exclusive handle and verify its SHA256 against ST01R1. Source and destination handles are disposed on success/failure. No read retry. A mismatch may leave a partial or complete-but-unaccepted copy; retain it and stop.

One 1 MiB buffer, one source/destination pair at a time. Approximately 10 MiB/s aggregate application read pacing across copy and destination verification, with one-chunk bursts; no hard disk/cache I/O-rate guarantee. Expected content traffic on success: source read 1,641,947,136 bytes, destination write the same, destination verification read the same, total **4,925,841,408 bytes**. Additional metadata/flush/cache effects are not included in that total. SQL media format/checksums are not verified here.

One attempt. Cooperative 240 seconds per file and 900 seconds total; operator cancels with Ctrl+C at 250 seconds on one file or 910 seconds total. Blocking calls/flush can exceed cooperative limits; no self-killing watchdog. Expected paced runtime roughly 5–6 minutes, not a guarantee. Fixed start line, bounded progress display and final JSON at most 64 KiB/118 rows. Stop on failure, missing/unexpected path/length/hash/type, reparse, low space, time/output limit or incomplete results. No continuation/retry, source substitution or automatic cleanup. Preserve created paths on every stop.

## Receipt and manual transfer boundary

Require Operation LG01, MINI_AMD, Completed, null FailureType, BundleCreated=true, ExpectedFiles=VerifiedFiles=118, exact expected bundle, and all per-set hashes/lengths equal ST01R1. Assistant reconciles the JSON before transfer. Receipt records only verified files; a failed current file can exist but is unaccepted. Never treat file count alone as success.

Once the receipt is accepted, admin can select **all 118 files inside this bundle** and copy them directly into the existing development destination:

`C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11_G4_20260928_97337\media`

Copy the contents, not the enclosing folder. Leave the already-copied full backup in place. Keep all originals and the bundle. This is the same manual route/destination, not an ST03 retry or ACL workaround. Final development set must be 119 media files totaling 2,815,180,800 bytes, followed by destination-hash reconciliation. Manual transfer retains its existing 30-minute/no-overwrite/stop-on-error bounds; no automatic transfer by this script. Actual restore remains separately unapproved.

## Validation and scope

Exact embedded entries checked against the accepted source receipt and retained candidate: 118 unique paths/names/sets in the same order, excluding full backup, byte sum as above. Static PowerShell parse passed. Only the copy function was exercised locally on synthetic files under `lg01-synthetic-tests`: full-chunk-plus-tail copy/hash passed; existing destination was rejected and unchanged; incorrect expected hash caused a stop and retained the unaccepted copy. Original LG01 host/main/production path execution never occurred. Synthetic files and test results are retained.

Security routing: narrowly scoped inert approval-artifact preparation, manually reviewed creation/read/share/hash/output behavior; no Bot/SQL runtime integration or existing ACL change. No repository-wide security scan or predecessor rerun. No PR/publication. Original pending/sealed evidence remains unchanged. No conclusion about production media integrity or runtime safety follows from synthetic tests.

Maintenance window remains approved through 2026-09-29T09:23:23Z. Preserve the ST03 access-denial evidence, ST01 cancelled-input history and ST01R1 accepted source hashes. All seven G4 proofs and actual restore remain incomplete; rollout/G5 unapproved. Memory investigation deferred; historical collector withdrawn; KVK/view issues separate.
