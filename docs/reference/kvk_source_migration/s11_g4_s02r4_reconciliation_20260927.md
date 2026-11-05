# S02R4 receipt — public DENY targets identified

Bounded detail observation COMPLETE. Operator supplied all three expected result sets, exactly eight DENY entries, both resolution flags equal to 1 on every entry, and the S02R4 completion marker. No error supplied; no count drift or sentinel. This completes only the scoped public object/column DENY observation.

Original attachment preserved byte-for-byte at `.codex_artifacts/s11-g4-capture-preparation-20260926/received-S02R4-20260927T211710Z.txt` (10,704 bytes, below 32 KiB). Receipt recorded 2026-09-27T21:17:10Z. Server observed 21:16:55.4660572Z, completed 21:16:55.4695089Z, client completed 22:16:55.4906014+01:00 = 21:16:55.4906014Z on that date. Result timestamps fall within approval 21:16:10–21:36:10 UTC. Batch-start and stopwatch elapsed not supplied; result timestamps do not establish full elapsed-time or timeout compliance.

Identity matches mini_AMD / ROK_TRACKER / MicrosoftAccount\cwattsconsulting@outlook.com; VIEW DEFINITION and observer database CONTROL both 1. Windows/UI identity remains separately retained. This is operator evidence, not independent proof of executed bytes.

## Installed entries

All entries are public, DENY, OBJECT_OR_COLUMN, schema dbo, minor_id=0, column_name=NULL and both resolution flags 1. Column NULL is expected for object-level permission.

| major_id | Object | Type | DENY permissions |
| --- | --- | --- | --- |
| 1301292837 | ACQUIRE_KS4_IMPORT_LOCK | SQL_STORED_PROCEDURE | EXECUTE |
| 1317292894 | HASH_KS4_IMPORT_ARCHIVE_FILE | SQL_STORED_PROCEDURE | EXECUTE |
| 1349293008 | IMPORT_STAGING_PROC_CORE | SQL_STORED_PROCEDURE | EXECUTE |
| 1365293065 | KS4_ImportFileClaim | USER_TABLE | DELETE, INSERT, SELECT, UPDATE |
| 1461293407 | CLAIM_KS4_IMPORT_FILE | SQL_STORED_PROCEDURE | EXECUTE |

Eight permission entries concern five objects. Local source corroborates these clauses in authoritative SQL migrations `20260726_001_phase3_import_concurrency_and_direct_type_alignment.sql` (lines 281, 350, 959) and `20260728_001_phase5_immutable_import_file_handoff.sql` (lines 3099–3102). This is source agreement on the named DENY clauses, not proof of installed module content, signatures, execution context or effective application behavior. No source or SQL execution occurred during reconciliation.

These are existing import-related object names, not the absent S11 evidence objects. Do not treat them as an S11 installation failure or approve their removal. The result alone does not prove which access paths succeed or how any particular principal is affected; existing SHEETS_USER/db_owner evidence is separate. No effective-permission test or application replay occurred.

## Remaining work

Public negative-ID grants remain partly enumerated: S02R3 counted 217 while S02R1 retained only a prefix. Do not label them defaults, safe or fully reviewed merely from ID sign. No need to repeat these completed DENY details, named grants, principal/role inventory or object absence inventory. Any further metadata observation needs an exact approved packet and a concrete remaining purpose. No next live action is authorized by this receipt.

All seven typed G4 proofs and actual restore remain incomplete. Rollout/G5 remain unapproved. Preserve isolated hotfix, pending/recovered work, single-account/admin-owned operation, deferred memory cause, withdrawn collector and separate KVK/view-rehydration issues.

Validation: local row/byte checks, source-clause comparison, approval window, proposal/approval hashes and original pending/evidence preservation. Documentation/evidence only: runtime/predecessor tests, pre-PR validators and security discovery skipped as inapplicable. No permission or runtime change.
