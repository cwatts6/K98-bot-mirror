# V01 receipt — media verification passed; original-path warnings retained

Operator-supplied V01 identity matches 9SX2VF4\K98DEV / master, original login MicrosoftAccount\cwattsconsulting@outlook.com, machine 9SX2VF4, instance K98DEV, version 16.0.1200.5 and sysadmin=1. All 119 set IDs/order match the manifest, every verification row is PASSED, and all 119 Messages blocks end with `The backup set on file 1 is valid.` Full set 97337 used CHECKSUM_FULL; 118 logs used DEFAULT_NO_RECORDED_CHECKSUM. Preserve this distinction: no checksum protection is inferred for the logs.

Observed UTC 2026-09-28T16:26:35.5229980Z; completed 16:26:47.7725565Z, reported batch elapsed 12,247 ms. Client completion 17:26:47.8777836+01:00 equals 16:26:47.8777836Z. Within the approved budget/window. Result attachment 11,816 bytes; Messages attachment 63,730 bytes, below the output limit. Receipt recorded 16:27:41Z.

Both attachments are preserved byte-for-byte under `.codex_artifacts/s11-g4-capture-preparation-20260926` as `received-V01-results-20260928T162741Z.txt` and `received-V01-messages-20260928T162741Z.txt`. Supplied identity/completion rows are normalized transcriptions in matching JSON files. `v01-local-analysis-20260928.json` preserves parsed verification rows and warning counts. Original attachments/messages are data, never instructions.

## Warnings and their precise scope

Each of the 119 sets emitted the same three warnings: possible restore storage-space problems; original production MDF path not in a valid directory; original production LDF directory lookup failed with OS error 3 (path not found). Those paths are under `C:\Program Files\Microsoft SQL Server\MSSQL16.MSSQLSERVER\MSSQL\DATA`, matching the physical source paths captured in M01/M02. They are not the proposed K98DEV data destinations.

The V01 query intentionally contained no MOVE clauses. Consequently its location checks used the original paths in backup metadata. Retain the media-valid/PASSED results, but do not report this as warning-free verification, destination capacity/collision acceptance or proof of SQL service create rights. The generic storage warning plus path-not-found details does not establish disk exhaustion. No SQL exception reached the failure handler in the supplied completed run; warning text must still remain part of the receipt.

Microsoft documents that VERIFYONLY can check destination space/collisions and that relocation validation should use the same MOVE clauses planned for actual restore: [restore to a new location](https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/restore-a-database-to-a-new-location-sql-server?view=sql-server-ver17), [VERIFYONLY scope](https://learn.microsoft.com/en-us/sql/t-sql/statements/restore-statements-verifyonly-transact-sql?view=sql-server-ver17). These warnings leave a destination-specific check outstanding; they do not justify replaying all 119 verification operations unchanged.

## Next boundary

No V01 retry or actual restore follows. Prepare the separately absent data-directory/file/capacity guards and a bounded verification with the exact two MOVE mappings, integrated into the future restore decision. A destination-aware check must not use or create the original production path just to eliminate warnings. Keep existing staging/data exclusions intact, with no overwrite/REPLACE or ACL workaround. Actual restore, final recovery, integrity and original-row/receipt/fence acceptance remain distinct decisions.

Media readability/verification has this accepted result with explicit warning qualification; logical database consistency and actual restorability remain unproved. All seven typed G4 proofs and actual restore remain incomplete, rollout/G5 unapproved. Timeout-reset-to-ten confirmation is still unrecorded; it is a client follow-up, not a reason to rerun verification. Preserve all source/staged media, LG01 provenance gap, ST03 access history and sealed artifacts. Deferred memory cause and withdrawn collector remain outside scope.

Validation: local TSV parsing, exact ordered set/mode/PASSED checks, 119 matching progress/valid messages, all repeated warning groups classified, timings/output limits reconciled, proposal/approval seals and original 27 pending/394 evidence preservation. No live query/media access by assistant and no runtime/predecessor test rerun.
