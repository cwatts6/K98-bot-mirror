# H09 receipt reconciliation — 2026-09-27

Operator-supplied MINI_AMD output reports completion from 07:43:45.0846053Z to 07:43:45.1119604Z with elapsed stopwatch value 23 ms. These timestamps fall within the approved 07:41:53–08:01:53 UTC window. Both stopwatch and approximately 27.355 ms UTC endpoint duration are below 20 seconds; these are distinct clock fields. The completion marker is not independent execution attestation or an OS exit code.

Raw output is preserved at `.codex_artifacts/s11-g4-capture-preparation-20260926/received-H09-20260927T074405Z.txt`. Receipt time is distinct from execution and file modification times. This additive record updates awaiting-output status without changing historical approvals, proposals or seals.

| Target under C:\discord_file_downloader | Bytes | Source comparison |
|---|---:|---|
| graceful_shutdown.py | 13495 | SHA256 `be79f5a3e2300cbddc221f8754d2fd654598308e70b5eb8f19de7d7511c305bc` matches the reviewed hotfix Git blob exactly. |
| rotate-logs.ps1 | 2290 | SHA256 `9d287c2eaa6f58779363a2c32d565206df148e9e80b935495ef7688b64f50730` matches the reviewed hotfix CRLF representation. |

Both report Archive attributes, owner MINI_AMD\cwatt, and SizeAndMtimeStable=true. The SDDL in each includes inherited Authenticated Users rights 0x1301bf (Modify plus Synchronize). This extends the retained custody/ACL gap to both task scripts; no permission change is authorized. Metadata stability does not establish race-free custody, effective access, atomic ACL/content binding or future immutability. Last-write times are retained as file metadata, not deployment provenance.

Together with H08 task bindings, these point-in-time hashes support applying the reviewed script-source effects to the observed files. Shutdown can write markers/logs, attempt Discord notification and terminate processes; rotation can replace/truncate the wrapper log using temporary-file fallbacks and its default 1000-line setting. Neither script was invoked by H09. Dependencies/configuration, runtime TEMP, executable resolution, actual execution history, completed drain and native token/process binding remain unproved.

Restart daily arguments remain withheld/unresolved from H08. H07's schedule and one-minute boundary separation remain planning constraints. No broader argument capture, task invocation, task change or file reread follows this receipt.

All seven typed G4 proofs and actual restore remain incomplete. Remaining writer, protected-path/key, native identity, provider, SQL and storage gaps stay open. Preserve isolated production hotfix, single-account/admin-owned operation and accepted fresh output/equivalent reports. Memory-cause investigation stays deferred; withdrawn collector stays withdrawn; empty KVK/view-rehydration remain separate retained issues. No rollout, G5, provisioning or Git publication approval is implied.

Validation is local JSON parsing, target/window/budget/source-hash comparison and original file/seal integrity verification. Runtime tests and new security scan are skipped for this additive evidence-only record; application/configuration/permissions are unchanged and no PR is prepared. No live SQL/provider/Discord, deployment/restart, backup/restore, task control or script invocation was performed by the assistant.
