# H09 — two-script metadata/hash/ACL proposal

PREPARED, NOT APPROVED OR EXECUTED. The operator agreed to prepare the next exact capture. Live execution still requires approval of this command and a fresh window. H08 identified these two task targets; its withheld restart arguments remain unresolved and are outside H09.

## Exact targets and command

On MINI_AMD only, read these two leaf files in order:

1. `C:\discord_file_downloader\graceful_shutdown.py`
2. `C:\discord_file_downloader\rotate-logs.ps1`

Command text: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/H09.txt` (2238 bytes).

Command SHA256: `82942f6b0d9fa26b21107f16b5071aed8061da2d778c9b78b534ba3826c89389`.

Chris Watts remains operator/reviewer/abort owner, using existing `MINI_AMD\cwatt`. Retained tool: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`, SHA256 `60c9b29843624dd8af6b6a7b26147753be6aeef65098b9a503cc50850afe410f`. No elevation or alternate identity. The tool pin and H01 parent ACL observations are historical, not refreshed by H09.

For each named file the command reads leaf attributes/size/mtime, owner/SDDL, SHA256 and then leaf attributes/size/mtime again. It rejects directories and leaf reparse points and checks size/mtime stability. It emits file path, size, hash, attributes, last-write UTC, owner/SDDL and stability result, plus capture start/end UTC, elapsed milliseconds and completion marker. It does not emit file contents, import Python, invoke PowerShell script content, follow dependencies, or inspect environment/key material.

## Source comparison targets

Reviewed source is pinned to isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`. Git blobs and pin metadata remain retained with H08. Compare the exact source-byte domains below without modifying production line endings or assuming a mismatch is harmless.

| File | Domain | Bytes | SHA256 |
|---|---|---:|---|
| graceful_shutdown.py | Git blob | 13495 | `be79f5a3e2300cbddc221f8754d2fd654598308e70b5eb8f19de7d7511c305bc` |
| graceful_shutdown.py | CRLF representation | 13888 | `bcd2b61d271eb6e8ebd998dfb05853e794cf7aad6a0fd560c825e97aa67a8d03` |
| rotate-logs.ps1 | Git blob | 2222 | `677d4060c69a0f6604dbc91811da1ec73db83c1e723994759e33bc4d884bcda1` |
| rotate-logs.ps1 | CRLF representation | 2290 | `9d287c2eaa6f58779363a2c32d565206df148e9e80b935495ef7688b64f50730` |

H08 already retains source effects: shutdown can write markers/logs, contact Discord and terminate processes; rotation can replace/truncate the wrapper log via temporary-file fallbacks. H09 hashes the files without invoking those effects. Matching bytes would support the source interpretation for these files only, not installed dependencies/configuration, execution history, graceful drain, interpreter resolution or native process/token identity.

## Budget, effects and stops

- One attempt, two explicit files, at most 1 MiB hashed input per file (2 MiB total), 4096 SDDL characters per file, 16 KiB UTF-8 success payload, 20-second operator cutoff. No traversal, broad inventory, retries or additional targets. Each leaf has two metadata reads, one ACL read and one hash read.
- Effects: filesystem metadata/content reads for hashing, CPU/I/O/cache and possible audit activity. No file or ACL write, script invocation, task control, SQL/provider/Discord call, process start/stop or deployment. No key bytes are requested or read.
- Stop on wrong host, missing/denied file, directory/reparse leaf, oversized file/SDDL, size/mtime drift, error or time/output limit. Interrupt at 20 seconds, preserve partial output/error, no retry or concurrent replacement command. Stopwatch checks occur between synchronous calls and are not a hard cancellation or throughput bound; files can grow/race between checks. Do not claim race-free custody, effective-access certification, atomic ACL/content binding or a retained native handle.
- Hash mismatches are reviewed after the fixed two-file batch. Any mismatch stops progression to subsequent operations; it never permits normalizing, replacing, rerunning, executing or reading script contents. Preserve the unexpected hash as evidence.
- The completion marker is not an independent exit code or proof of adherence. Record operator output/error and reported times separately from receipt time. Parent-path protection and concurrent ACL stability remain outside this leaf snapshot.

## Approval, receipt and validation

Approve H09 by operation/hash above with Chris as operator/reviewer/abort owner and a fresh 20-minute UTC execution window recorded at approval. Earlier approvals/windows do not carry over. The exact command is retained as inert text; no live read follows preparation automatically.

Preserve supplied output in a new `received-H09-<receiptUTC>.txt` under the existing evidence directory, hash it, compare targets/budgets/source hashes and ACLs, and seal an additive reconciliation. Do not overwrite approvals, originals, historical receipts or seals. Missing/withheld results remain missing rather than silently inferred.

Local PowerShell parse: zero errors. Local retained source bytes confirm the four size/hash comparison pairs. Static inspection confirms two literal paths and read-only cmdlets; no live execution, source import or runtime test. Security routing is a documented skip for additive documentation and inert capture preparation, not approval of execution or pending S11 code. No PR is prepared; application test-selection/architecture/deferred validators are skipped because runtime/configuration/permissions are unchanged. No new security scan or remediation.

All seven typed G4 proofs and actual restore remain incomplete. Preserve original pending/recovered work, the single-account/admin-owned startup model, fresh output link/equivalent reports and isolated production hotfix. Memory-cause investigation remains deferred; the withdrawn collector must not run. Empty KVK/view-rehydration remain separate retained issues. Rollout, provisioning, restore, G5 and Git publication remain unapproved.
