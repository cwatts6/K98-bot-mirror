# S01R3 metadata receipt — eleven named S11 objects absent

Operator supplied all three expected result sets: one identity/visibility row, eleven object rows and one completion row. Raw text is preserved at `.codex_artifacts/s11-g4-capture-preparation-20260926/received-S01R3-20260927T101919Z.txt`. Receipt time is separate from execution time.

Identity: mini_AMD / ROK_TRACKER / MicrosoftAccount\cwattsconsulting@outlook.com; VIEW DEFINITION=1. Server observed/completed UTC are both 2026-09-27 10:19:08.3306589. Client completion 2026-09-27T11:19:08.3472156+01:00 equals 10:19:08.3472156Z. These timestamps lie within the approved 10:17:35–10:37:35 UTC window. They do not include batch start or independent stopwatch duration; do not infer zero duration from equal server timestamps. No error was supplied.

## Result and consequence

All eleven exact targets report type=NULL, present=0, definition_bytes=NULL and installed_definition_utf16_sha256=NULL:

- dbo.ExportExecutionSession
- dbo.ExportExecutionStream
- dbo.ExportManagedFileOrigin
- dbo.ExportProviderRequest
- dbo.ExportProviderRequestEvent
- dbo.ExportReconciliationProof
- dbo.usp_ExportExecutionSessionTransition
- dbo.usp_ExportExecutionStreamTransition
- dbo.usp_ExportOutputEnrollmentTransition
- dbo.usp_ExportProviderRequestEventAppend
- dbo.usp_ExportReconciliationProofIssue

With the reported full database definition visibility and correct accepted target/observer, this is point-in-time absence evidence for those exact names in the observed production database. It is not the earlier table-module null-field ambiguity: present=0 and type=NULL apply to all eleven. No installed definition hash exists to compare for these targets. Stop their downstream shape/signature probes rather than querying nonexistent objects or rerunning the 538-object predecessor inventory.

The authoritative SQL source contains the named objects; source existence was checked during proposal preparation. Missing production installation is distinct from missing implementation. No install-all-58 shortcut, schema creation, migration, grant, principal creation or readiness declaration is authorized. This does not enumerate all prerequisites, all SQL objects or schema differences, nor prove a complete deploy delta.

## Guard and session evidence

Completion of the exact S01R3 path indicates its isolated captured state/count/implicit guard, identity guard and visibility guard allowed the batch. The captured transaction variables were not emitted; do not fabricate their raw observations or treat them as lifetime proof. Successful isolated guarding alongside the prior combined check's failure supports the evaluation-context explanation, without proving the exact SQL engine mechanism or continuity between runs. No COMMIT/ROLLBACK or transaction-setting fix occurred.

The batch's NOCOUNT ON, LOCK_TIMEOUT 1000 and DEADLOCK_PRIORITY LOW remain session effects as approved. Do not silently reset them or reconnect. Future exact packets must account for them. The SQL original login remains distinct from the retained Windows/UI MINI_AMD\cwatt label and is not the future restricted application identity.

## Next preparation, no live action

Reuse these eleven absences for the installation delta. Remaining relevant capture work includes current principal/role/effective-capability observations, writer/Agent effects, development database/file exclusions, recovery-chain/storage facts, provider/key metadata and native identity. Each has independent target/budget/approval requirements. Role metadata is not installed-shape proof or permission to grant roles. Earlier S02/S03/S04/S00 proposals remain held; S01R3 approval carries over to none of them.

All seven typed G4 records and actual restore remain INCOMPLETE. Preserve isolated production hotfix, successful startup/upload evidence, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view-rehydration issues. No rollout/G5, provisioning, restoration, deployment or publication approval follows.

Validation: local receipt row/name/value checks, exact query hash and original evidence/seal preservation. No new SQL by the assistant. Documentation/evidence-only security-routing skip; no application/configuration/permission change or PR, so runtime/pre-PR validators are skipped.
