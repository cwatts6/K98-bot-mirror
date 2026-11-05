# H12 — nightly export wrapper and direct helper file bindings

PREPARED, NOT APPROVED OR EXECUTED. This local preparation follows H11's exact task-action match. No new live read is authorized until the command and a fresh window are approved.

## Exact targets and command

On MINI_AMD, read only these four files, in order, under `C:\K98-bot-SQL-Server\deploy\`:

1. Invoke-NightlyProdSchemaExport.ps1
2. SqlDeploy.Common.ps1
3. NightlyExportRetention.ps1
4. Export-ProdSchemaSnapshot.ps1

The first is H11's observed action target; the others are named directly by its reviewed source. This is a fixed allowlist, not discovery or recursive dependency traversal. No SQL connection, export, Git operation or script invocation is part of the capture.

Command text: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/H12.txt`, 2380 bytes.

SHA256: `98be77fff3e8924104c3e776a7312d03c7d8d1ca394f45ee4ad5c6814ab48f95`.

Chris Watts remains operator/reviewer/abort owner, existing MINI_AMD\cwatt. Use retained Windows PowerShell `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`, SHA256 `60c9b29843624dd8af6b6a7b26147753be6aeef65098b9a503cc50850afe410f`. No elevation or alternate identity. The pin is historical.

The command uses the H09 read-only pattern: leaf metadata before; owner/SDDL; SHA256; leaf metadata after. It rejects directory/reparse leaves and checks size/mtime stability. It outputs only those fields and operation/host/start/end UTC/elapsed/completion metadata. It does not print source, dot-source/import scripts, load SQL modules, query SQL, follow script references, or read environment/key values.

## Source pins and effects map

All four candidate sources were read from local SQL Git HEAD `4cd1554dc3d063e323f22350c88df1444cd0ed4b`; local files match after line-ending normalization. Retained blobs are `h12-<filename>.source.txt`; `h12-source-pins.json` records exact Git and CRLF byte counts/SHA256. Neither representation is assumed deployed until the receipt matches.

| File | Git bytes | CRLF bytes | CRLF SHA256 |
|---|---:|---:|---|
| Invoke-NightlyProdSchemaExport.ps1 | 9088 | 9328 | `832a7c67021d655bd4eb1d2011b6f5f372d1c56b17622033eb884e8e05d159cd` |
| SqlDeploy.Common.ps1 | 8857 | 9131 | `6e6d6474284cab84668a0016e5ca5285aa085120ab48bb481b8a40916947d19b` |
| NightlyExportRetention.ps1 | 6729 | 6898 | `ce366a276b54c183af9cfdb2b5f9c927c3fd34e865ea59064efc27bfb0dcb11d` |
| Export-ProdSchemaSnapshot.ps1 | 8334 | 8540 | `e2649d6aa467a26fa599f12fc30afb5ad4b4553f4e839e15cd995abddb2b0687` |

Reviewed source can, if invoked, fetch/pull/switch Git branches, source optional Bot environment scripts, log, load SQL modules/SMO, query schema and write schema snapshots, replace repository schema files, commit/push exports, prune expired remote export branches and send failure alerts. Common helpers also define SQL query/file execution routines; definition presence does not prove every routine is called by the export. This is a source effects map, not a live execution report or approval to invoke any mode. Even a no-push/dry-run label must not be treated as metadata capture permission.

The four-file set is not a complete runtime closure: optional Bot activation/dev scripts, executable/module resolution, credentials/environment, remote state, file parents/output paths and actual SQL/provider capabilities remain unproved. A script can change after hashing; no lifetime immutability or native handle binding is claimed.

## Budgets, stops and evidence

- One attempt, four exact leaves, at most 1 MiB per file / 4 MiB total hashed input, 4096 SDDL characters per file, 32 KiB UTF-8 success payload, 20-second operator cutoff. Each leaf: two metadata reads, one ACL read, one hash read. No recursion, retries or additional targets.
- Effects: filesystem reads, CPU/I/O/cache and possible audit activity. No production writes, script evaluation, task control, SQL/provider/Discord request, schema export, Git fetch/pull/push, deployment/restart, provisioning or backup/restore.
- Stop on wrong host, missing/denied target, directory/reparse leaf, size/SDDL/error/time/output cap or size/mtime drift. Interrupt at 20 seconds, retain partial output/error, no retry or concurrent replacement. Synchronous I/O and check/read races mean no hard cancellation, throughput or memory guarantee. Parent reparse/ACL safety and atomic ACL/content binding are not certified by leaf samples.
- Compare hashes after the fixed four-file batch against retained Git and CRLF domains. Any unexpected hash stops subsequent progression for reconciliation, never permitting normalization, replacement, rerun or content disclosure. Nonmatching source is not permission to pull main.
- Exact approval must cover H12/hash, Chris and a fresh 20-minute UTC window recorded on approval. Old approvals/windows do not carry over. Preserve output/error in new `received-H12-<receiptUTC>.txt`, distinguish execution and receipt time, hash, reconcile and seal additively. Completion is not an independently observed OS exit code.

## Validation and unchanged boundaries

Local parser: zero errors. Static check confirms four literal file targets and read-only cmdlets; local source normalization/hash comparisons passed. No live run, dependency import or SQL test occurred. Security routing is a documentation/inert-preparation skip, not approval of execution or review of pending S11 implementation. Runtime tests and pre-PR validators are skipped because application/configuration/permissions are unchanged and no PR is prepared.

All seven typed G4 proofs and actual restore remain incomplete. Old disabled export-task path and withheld restart arguments remain unresolved; the question for already-known nonsecret facts remains pending, with no live inspection requested. Full writer exclusion, native identity, protected-path/key custody, provider/SQL/storage evidence stay open. Preserve single-account/admin-owned operation, isolated production hotfix, fresh output/equivalent reports and pending/recovered work. Memory cause stays deferred; withdrawn collector stays withdrawn; empty KVK/view-rehydration remain separate. Rollout/G5, provisioning, restore and publication remain unapproved.
