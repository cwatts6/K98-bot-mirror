# D03 / D04 / M01 receipt — 2026-09-28

All three operator outputs report completion. D03 and M01 attachments are preserved byte-for-byte (6,201 and 13,400 bytes) as `received-D03-20260928T112458Z.txt` and `received-M01-20260928T112458Z.txt` under `.codex_artifacts/s11-g4-capture-preparation-20260926`. D04 is a normalized transcription of the supplied JSON in `received-D04-20260928T112458Z.json`. Selected fields and arithmetic are retained in `grouped-destination-media-analysis-20260928.json`. Receipt recorded at 11:24:58Z.

## Chronology and limits

D04 ran 11:22:39.4360092Z–11:22:39.4438072Z, reported 9 ms. D03 observed 11:23:41.3378092Z and completed 11:23:41.3388153Z, client completion 11:23:41.3695412Z. M01 observed 11:24:38.9367394Z and completed 11:24:38.9410981Z, client completion 11:24:38.9765876Z. All are inside the recorded maintenance window. SQL observation-to-completion intervals do not measure full batch runtime or independently prove client timeout configuration.

Actual order was D04, D03, M01 rather than the approved D03, D04, M01. Record this deviation; do not claim exact sequence compliance. The operations were independent metadata reads and no mutation relied on their order. Preserve the evidence without a corrective rerun. Candidate absence remains sampled, not reserved, and must be guarded again within any later approved creation operation.

## Development destination facts

D03 accepted 9SX2VF4\K98DEV / master, machine 9SX2VF4, instance K98DEV, version 16.0.1200.5, original SQL login MicrosoftAccount\cwattsconsulting@outlook.com, sysadmin=1. It found zero database-name and catalog-directory collisions for `S11_G4_Recovery_20260928_97337` and `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11_G4_20260928_97337`.

Exactly one engine row returned: SQL Server (K98DEV), account NT Service\MSSQL$K98DEV, Running. This is reported service configuration/status, not a native process token, SID mapping or effective-create test. D02's ACL SID remains separately retained; no rights equivalence is inferred.

D04 on 9SX2VF4 returned Completed, FailureType=null and Present=false for that exact proposed directory. No directory was created. All 21 existing databases and 49 file exclusions remain protected. No file-name MOVE mapping or storage reservation follows.

## Full backup header and layout

M01 accepted mini_AMD / ROK_TRACKER, original SQL login MicrosoftAccount\cwattsconsulting@outlook.com, VIEW DEFINITION=1 and database CONTROL=1. One header and two file rows plus completion returned, within the proposal row/output ceilings.

Header matches the selected full backup at position 1: DatabaseName ROK_TRACKER, BackupType=1, BackupSetGUID 70E5C6BF-4A0A-4A48-B6F1-E6E653E8A36D; BindingID 2BAEE938-2F4C-4AF6-AF35-94A0E163C999; FamilyGUID C4DE892E-FD68-46E4-AB63-245E74BFC07B; first/current recovery fork 09F183A3-7582-4274-8B7F-ED127A825633. First/checkpoint LSN 19080000061546400001, last LSN 19080000061548800001. Server/machine match retained production identity. Software 16.0.1200 and compatibility 160 are header facts, not a complete restore compatibility test.

BackupSize=7,304,765,440; CompressedBackupSize=1,173,233,788. These match catalog metadata; F01 physical length was 1,173,233,664. Preserve their distinction. HasBackupChecksums=1 and IsDamaged=0 describe recorded backup flags, not a checksum/integrity verification performed now. Encryption fields and both file TDEThumbprint fields returned NULL. This does not authorize requesting or accessing keys.

| Logical name | Type | Expanded Size bytes | MaxSize bytes | IsPresent |
|---|---|---:|---:|---:|
| ROK_TRACKER | D | 18,239,979,520 | 35,184,372,080,640 | 1 |
| ROK_TRACKER_log | L | 68,719,476,736 | 2,199,023,255,552 | 1 |

Both source physical paths are under production MSSQL16.MSSQLSERVER\MSSQL\DATA. They are historical source paths, never destination paths. No extra or unsupported file type appeared.

Initial expanded size is **86,959,456,256 bytes** (86.96 GB decimal). Adding all 119 F01 media lengths gives **89,774,637,056 bytes** before growth, working space, reserve and any extra media copies. D02 reported 1,747,644,268,544 bytes free on development C:, but those observations are not simultaneous or reserved. MaxSize values are upper bounds, not initial allocation requirements or a usable growth budget. The header/file list does not supply a complete operational growth policy.

## Next boundary

The full-backup identity/layout gap is filled by this metadata receipt. Complete log-media identity/readability, integrity and actual restore remain unproven. Next preparation can now specify two exact MOVE mappings under the proposed disjoint directory, source-media staging/copy targets, bounded growth/headroom and verification/recovery sequence. Any proposed capacity reserve is a new planning choice, not already selected or reserved.

Source prune protection remains unresolved; the known job's roots and retention days are partial attestation, not complete filter/cutoff/exclusion proof. Do not disable jobs, copy files or create targets from this receipt. Later copy/provisioning/restore steps require their own concrete operator decision. The maintenance window itself remains approved through 2026-09-29T09:23:23Z.

All seven typed G4 proofs and actual restore remain incomplete; rollout and G5 unapproved. Preserve the isolated hotfix, single-account/admin-owned model, fresh generated output/equivalent reports, withdrawn collector, deferred memory investigation and separate KVK/view issues.

Validation: local attachment byte preservation, selected-field reconciliation, row/output counts, integer storage arithmetic, command/proposal/approval hash checks and original 27 pending/394 evidence preservation. No new live observation by assistant, runtime/source changes or predecessor reruns. Receipt-only documentation requires no runtime suite or new security discovery.
