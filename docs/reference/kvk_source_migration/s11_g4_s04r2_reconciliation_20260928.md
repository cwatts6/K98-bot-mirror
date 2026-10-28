# S04R2 receipt — catalog recovery-chain candidate established

Bounded metadata observation COMPLETE. Nine retained-set identity rows and 110 distinct interval/media rows received, plus accepted identity and completion. All within approved row/output bounds; no sentinel/error. Original attachment retained byte-for-byte at `.codex_artifacts/s11-g4-capture-preparation-20260926/received-S04R2-20260928T101731Z.txt` (77,834 bytes, below 512 KiB).

Receipt recorded 2026-09-28T10:17:31Z. Server observed 10:17:12.7516032Z, completed 10:17:12.8009049Z; client completion 11:17:12.8276416+01:00 equals 10:17:12.8276416Z, within the maintenance window ending 2026-09-29T09:23:23Z. Batch-start/stopwatch duration not supplied, so no full elapsed-time claim. Accepted mini_AMD / ROK_TRACKER / MicrosoftAccount\cwattsconsulting@outlook.com, VIEW DEFINITION and database CONTROL both 1. Operator receipt does not independently attest executed bytes or client continuity.

## Catalog relationship

Candidate: full set 97337 plus 118 log sets 97338–97455. The new 110 sets 97338–97447 bridge the retained eight-log tail 97448–97455. No differential is required for this catalog candidate; no restore sequence is approved here.

- Full backup UUID: 70E5C6BF-4A0A-4A48-B6F1-E6E653E8A36D.
- Database GUID throughout: 2BAEE938-2F4C-4AF6-AF35-94A0E163C999.
- Family GUID throughout: C4DE892E-FD68-46E4-AB63-245E74BFC07B.
- First and last recovery-fork GUID throughout: 09F183A3-7582-4274-8B7F-ED127A825633; fork_point_lsn NULL throughout.
- All nine retained identities are present; type D for full, L for tail. All observed media positions are 1.
- First log 97338 spans 19080000061526400001 to 19080000061624000001, covering full's last_lsn 19080000061548800001.
- Every one of 117 adjacent log boundaries agrees exactly (earlier last_lsn = next first_lsn). Set 97447 ends at 19084000117953600001, exactly the retained tail's start. Tail ends at 19088000155032800001.

All 110 interval rows report is_copy_only=0, has_backup_checksums=0, is_damaged=0 and family_sequence_number=1. No reported damage is not physical validation; lack of log backup checksums remains retained. New interval compressed-size sum is 834,383,894 bytes, a historical catalog total only, not current file lengths or restore capacity. Exact LSNs remain strings/integers in `s04r2-local-analysis-20260928.json`, never floating point. Exact device filenames, including variable-width time tokens, remain unchanged in the receipt; do not regenerate filenames from timestamps.

These fields support a catalog chain candidate only. Different result statements/receipts are not an atomic snapshot. Media stripes/completeness, header/set identity and position on disk, existence/readability, version/encryption dependencies, destination isolation/capacity, prune protection and successful restore remain unproved. Backup dates remain unzoned server values; do not infer a UTC STOPAT or target recovery point from this capture. Choosing this analysis candidate is not approval to restore it.

## Next grouped preparation

Preserve a fixed candidate manifest from these receipts before any media operation. Next missing facts are development instance/database/file exclusions and exact destination volumes, plus independently bounded source-media metadata and prune protection. Separate hosts and read effects explicitly within a grouped packet; a known C: free-space snapshot is not sufficient to reserve restore files. Source-first planning may proceed, but no file/media access, backup/restore/VERIFYONLY/FILELISTONLY/CHECKDB, copy, provisioning, job control or expanded SQL is authorized by this receipt.

The approved maintenance window remains through 2026-09-29T09:23:23Z; no repeat scheduling confirmation is needed. New exact operation scopes still require approval. Prune timestamp/filter/exclusion/dependency gaps remain open. All seven typed G4 proofs and actual restore remain incomplete; rollout/G5 unapproved.

Preserve pending/recovered evidence, isolated hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues. Validation is local parsing/identity/LSN arithmetic, sealed input checks and original evidence preservation; no runtime/predecessor tests or security discovery applicable.
