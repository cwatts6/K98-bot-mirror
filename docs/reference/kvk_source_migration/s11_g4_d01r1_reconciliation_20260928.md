# D01R1 receipt — protected development database/file exclusions

Bounded catalog observation COMPLETE. All five expected result sets received: accepted identity, 21 databases, 49 files, nonnull default data/log paths and completion. No sentinel/error. Every listed database is ONLINE, comprising four system and seventeen retained application databases. All database names and physical files are protected exclusions, including names containing Disposable or restore; none is available for overwrite/drop/reuse merely from its name.

Original attachment preserved byte-for-byte at `.codex_artifacts/s11-g4-capture-preparation-20260926/received-D01R1-20260928T105550Z.txt` (40,922 bytes, below 512 KiB). Receipt recorded 2026-09-28T10:55:50Z. Server observed 10:55:31.5036095Z, completed 10:55:31.5219948Z; client completion 11:55:31.5384792+01:00 equals 10:55:31.5384792Z. Within maintenance window ending 2026-09-29T09:23:23Z. No batch start/stopwatch supplied, so no full elapsed-time/timeout claim.

Server 9SX2VF4\K98DEV, machine 9SX2VF4, instance K98DEV, database master, product version 16.0.1200.5, ORIGINAL_LOGIN MicrosoftAccount\cwattsconsulting@outlook.com and observer_sysadmin=1 match accepted binding. Retain Windows/UI 9SX2VF4\cwatt separately; no account/SID equivalence or current client-binary attestation inferred.

## Durable exclusions and storage context

Exact names, database/file IDs, logical/physical paths, types and growth/size fields are preserved in `development-protected-exclusions-20260928.json`. The 49 physical paths are unique case-insensitively; every returned database has associated file rows. The file count includes tempdb's additional data files; do not infer two files per database.

All 49 paths share parent `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA`. Both reported default paths point to that same directory (with trailing slash). This is a catalog pathname observation, not physical volume/mount/reparse resolution or file existence proof. The directory and existing files are not proposed restore targets.

Current catalog allocated-size sum is 1,902,051,328 bytes using exact 8,192-byte page conversion. This is not host free capacity, actual filesystem allocation, reserved growth or restore size. Preserve max_size special values and percent-growth flag; do not treat -1 as a negative byte budget. No filesystem read or volume check occurred.

The earlier historical truncated development inventory gap is now filled by this durable bounded capture. Catalog completeness remains point-in-time and subject to query visibility/row caps; arbitrary unregistered filesystem files, other instances and path aliases are outside scope. No S11 target exists among these names, but no name/path reservation or creation follows.

## Next grouped preparation

Prepare exact host-local capacity and directory-boundary metadata for this observed development path and its ancestors, without recursively listing or opening database files. Use those results to propose distinct new paths/names with explicit collision/exclusion checks; final source-media headers/logical-file layout, size/growth budgets and prune protection remain separate dependencies before an actual restore packet. No mkdir, copy, database creation, restore, deletion or ACL change is authorized by this receipt.

Source chain candidate and F01 existence/length metadata remain separate from destination exclusions. Maintenance scheduling remains approved through 2026-09-29T09:23:23Z; new action scopes require exact approval. All seven typed G4 proofs and actual restore remain incomplete, rollout/G5 unapproved. Preserve pending/recovered work, isolated hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues.

Validation: local row parsing, 21/49 counts, path uniqueness/database coverage, page arithmetic, proposal/approval seals and original pending/evidence preservation. Evidence/documentation only; no live query by assistant, runtime/predecessor tests or security discovery.
