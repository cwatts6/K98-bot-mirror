# F01 — fixed recovery-candidate file metadata

PREPARED, NOT APPROVED OR EXECUTED. One grouped metadata batch for all 119 source paths, not a replacement broad host collector.

Manifest: `.codex_artifacts/s11-g4-capture-preparation-20260926/recovery-candidate-97337-through-97455-20260928.json`, SHA256 `ee412e2433ab9807e1e39b99e186406199010c17ce8c6c4353f0493381399842`.

Exact command text: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/F01.ps1.txt`, SHA256 `6e8de2d4e11ef61c02bb787509554bc2c7b5e04af91293eaf6dda32c8481aa77`.

## Fixed targets and effects

Operator executes only on MINI_AMD under existing MINI_AMD\cwatt Windows account using the retained Windows PowerShell route. Host-name gate stops another host; it is not native identity attestation. H00 PowerShell executable pin remains historical: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe SHA256 60c9b29843624dd8af6b6a7b26147753be6aeef65098b9a503cc50850afe410f. No launch/elevation/account/settings change included. Chris Watts is operator/reviewer/abort owner.

Manifest candidate: full 97337 plus logs 97338–97455, one recorded family each. Exact filenames come from S04R1/R2; do not regenerate timestamp strings or expand wildcards. Manifest compressed-byte sum 2,814,975,773 is not actual file length, restore size or reserved capacity. No destination or restore command approved.

Check only directory metadata at C:\, C:\SQL_BACKUP, C:\SQL_BACKUP\FULL and C:\SQL_BACKUP\LOG for directory/reparse attributes. Then Get-Item -LiteralPath for each of the 119 exact file paths. Return path, length, attributes and last-write UTC. No Get-ChildItem, recursion, ACL/group enumeration, file-content hash, header read, backup verification, file copy/move/delete, media open, script import, Bot/SQL/provider/Discord call or Git operation. Reads may cause ordinary filesystem audit/cache activity. Metadata access is not backup-content access or readability proof.

Parents and files with ReparsePoint or unexpected type stop. This sampled attribute check is not race-free traversal or retained-handle proof; paths can change afterward. Missing/inaccessible files stop on first failure and preserve accumulated rows. No bypass or retry.

## Bounds and execution

One attempt, one batch, four exact directory metadata checks plus up to 119 exact file metadata checks. Ten-second cooperative deadline checked before each call; operator cancels at fifteen seconds. A blocking Get-Item can exceed cooperative deadline, so no hard syscall timeout is claimed. Output one bounded JSON object, maximum 128 KiB, at most 119 four-field file records. No recursive serialization of live objects. Script emits only exception type on a caught failure, not arbitrary error text. No evidence file written by the script; console output/history is an effect. No automatic repeated observation if interrupted or output is missing.

Use the already approved maintenance window ending 2026-09-29T09:23:23Z; no renewed scheduling approval needed. Exact F01 scope still needs approval. After approval, run the supplied command once in the existing production PowerShell session; do not run local preparation tools or any withdrawn collector. Do not substitute a different manifest/path list, pipe through Invoke-Expression, change execution policy, or save it as a scheduled task. Start timing before execution and cancel at fifteen seconds, then report interruption without retry. No claim that cancellation guarantees immediate completion of an in-progress metadata call.

Accept only Operation F01, Host MINI_AMD, Status Completed, ExpectedFiles=ObservedFiles=119, expected exact paths and output within budget. Stop/reconcile on any missing row, Stopped status, access/type/reparse failure, deadline, zero-length file, unexpected path, oversized/truncated output or absent completion. Filesystem sizes need not equal compressed_backup_size; retain discrepancies for review without repairing or opening files. Post-output anomalies also stop downstream work.

## Destination work held separately

Retained development target is localhost\K98DEV/master with historical server identity 9SX2VF4\K98DEV and 17 retained application databases plus system databases. Complete database/file exclusions were not durably captured. The existing question requests only already-known open SSMS binding and observer login; no live inspection/new connection. Do not use the production session, copy its SQL login guard to development, guess a destination path, or create a disposable database. Exact development capture follows binding; media headers/restore storage and prune protection remain separate scopes.

## Validation and proof status

Local manifest creation checks 119 distinct IDs and paths, one full/118 logs, exact LSN adjacency, and source-receipt correspondence. Static PowerShell parsing only, never execution. Fixed paths cross-checked against manifest; no runtime validation. Documentation/inert fixed metadata proposal retains security-routing skip; no runtime implementation/PR, predecessor tests or security discovery.

All seven typed G4 proofs and actual restore remain incomplete. Metadata cannot satisfy media integrity, complete stripes, restore disjointness/capacity, prune exclusion or successful restore. Rollout/G5 unapproved. Preserve pending/recovered work, isolated hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues.
