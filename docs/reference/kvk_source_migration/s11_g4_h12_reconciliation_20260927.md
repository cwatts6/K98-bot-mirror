# H12 receipt reconciliation — 2026-09-27

Operator-supplied MINI_AMD output reports StartedUtc 09:01:18.5715262Z, FinishedUtc 09:01:18.6026705Z, elapsed stopwatch value 34 ms and Completed. Reported timestamps fall within the approved 08:59:50–09:19:50 UTC window. Both stopwatch and approximately 31.144 ms UTC endpoint duration are below 20 seconds; preserve these distinct clock fields. Exactly the four approved files are present, totalling 33897 bytes. No error was supplied. Completion is not an independently observed exit code or native execution attestation.

Raw output: `.codex_artifacts/s11-g4-capture-preparation-20260926/received-H12-20260927T090134Z.txt`. Receipt time is distinct from execution and file modification times. This additive record updates awaiting-output status without rewriting historical approvals, proposals or seals.

| File under C:\K98-bot-SQL-Server\deploy | Bytes | SHA256 matches reviewed CRLF source |
|---|---:|---|
| Invoke-NightlyProdSchemaExport.ps1 | 9328 | `832a7c67021d655bd4eb1d2011b6f5f372d1c56b17622033eb884e8e05d159cd` |
| SqlDeploy.Common.ps1 | 9131 | `6e6d6474284cab84668a0016e5ca5285aa085120ab48bb481b8a40916947d19b` |
| NightlyExportRetention.ps1 | 6898 | `ce366a276b54c183af9cfdb2b5f9c927c3fd34e865ea59064efc27bfb0dcb11d` |
| Export-ProdSchemaSnapshot.ps1 | 8540 | `e2649d6aa467a26fa599f12fc30afb5ad4b4553f4e839e15cd995abddb2b0687` |

Comparison source is SQL Git HEAD `4cd1554dc3d063e323f22350c88df1444cd0ed4b`; H12 retains Git blobs and both byte-domain hashes. All files report Archive and SizeAndMtimeStable=true. The common helper is owned by BUILTIN\Administrators; the other three by MINI_AMD\cwatt. Every supplied SDDL includes inherited Authenticated Users rights 0x1301bf (Modify plus Synchronize). Administrator ownership does not remove that allow entry. This remains a custody/ACL release gap, not permission to alter ACLs or a complete effective-access determination.

Together H11's task-action binding and H12's point-in-time file hashes support the reviewed source effects for the named wrapper/direct helpers. They do not prove actual export execution, full dependency/configuration closure, resolved executables/modules, protected parent paths, immutable future bytes, native process/token identity, SQL authority or complete writer exclusion. Last-write dates are file metadata, not installation provenance; size/mtime checks are not race-free ACL/content binding.

No script, SQL query, export or Git operation was invoked by H12. Reviewed source may perform schema replacement, Git fetch/pull/commit/push/retention and failure alerts if invoked; no such invocation is authorized. The optional Bot environment scripts and runtime environment remain outside this four-file snapshot.

The older disabled schema-export action and Restart daily arguments remain unresolved. The existing question asks only already-known nonsecret facts without live inspection; no answer is assumed. All seven typed G4 proofs and actual restore remain incomplete. Native identity, protected-path/key custody, provider, SQL, storage and complete writer evidence remain open. Preserve same-account/admin-owned operation, isolated hotfix and fresh output/equivalent reports. Memory cause stays deferred; withdrawn collector stays withdrawn; empty KVK/view-rehydration remain separate. No rollout/G5, provisioning, deployment/restart, restore or publication approval follows.

Validation: local JSON parsing, exact target/window/budget/source-hash comparisons and original file/seal integrity checks. Runtime tests, pre-PR validators and new security scan are skipped for this additive evidence-only record; no application/configuration/permission change or PR is made.
