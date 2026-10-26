# ST01R1 — saved-file retry proposal

PREPARED, NOT APPROVED OR RUN. Scope is one new source-hash attempt only. Do not advance to ST02/manual copy/ST04 from this proposal. Original ST01 and its approval/seals remain unchanged.

## Resolved console observation

Operator confirms the prior display was `>>`, and Ctrl+C returned `PS C:\WINDOWS\system32>`. This is continuation-input state; cancellation of that unfinished input is confirmed. It does not establish which earlier complete statements executed or whether any hashes were computed. No completion receipt exists. The earlier approximate 30-minute report must not be relabelled as measured hashing runtime. No SQL/memory incident is established, and the deferred memory investigation remains deferred.

## Exact file and launch

Prepared local file: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S11-G4-ST01R1.ps1`.

SHA256: `1fff7ad5311be25b1db415142f70039e6fc96e096610dccdaa1e4eed4c07cf7e`.

After exact retry approval, use the existing admin/RDP file-transfer method to copy this small script file unchanged onto MINI_AMD as `C:\Users\cwatt\Downloads\S11-G4-ST01R1.ps1`. Do not paste the multiline script into the console, re-save its contents through an editor, overwrite an existing file, create missing directories, change accounts/elevation or execution policy. If the directory is unavailable, an existing same-name file is present, transfer fails or policy blocks execution, stop and report. This file transfer is the only new local write authorized by the proposed retry; the 119 backup files are not copied.

On MINI_AMD, paste just the single complete line in `commands/ST01R1-launch.txt`. It hashes that exact saved script, throws on mismatch, then invokes it using PowerShell's call operator. Script hash verification is before execution; host guard remains in the script. No execution-policy bypass or new child process. Expected launcher:

```powershell
if ((Get-FileHash -LiteralPath 'C:\Users\cwatt\Downloads\S11-G4-ST01R1.ps1' -Algorithm SHA256 -ErrorAction Stop).Hash -ne '1FFF7AD5311BE25B1DB415142F70039E6FC96E096610DCCDAA1E4EED4C07CF7E') { throw 'Script hash mismatch; stop' }; & 'C:\Users\cwatt\Downloads\S11-G4-ST01R1.ps1'
```

## Delta from ST01

Only operation label ST01R1 and console visibility are changed: a fixed start message after the host guard, a progress update before each file and approximately once per second between chunks, then progress completion. File list/order/lengths, source boundaries, read/share modes, chunk size, pacing, SHA256 algorithm and JSON fields remain the same. Progress is host UI output, not an additional metadata query or a persisted log. Capture the final JSON separately from the fixed start message.

Progress can freeze at a blocking metadata/open/read call. This revision does not claim a hard timeout, independent watchdog or complete attribution of the earlier console state. A frozen update is a reason to obey the operator cutoff, not extend the budget.

## Exact effects and limits

One attempt on MINI_AMD. Four literal source-directory boundary checks and exactly 119 named backup-file hashes; 2,815,180,800 content bytes on successful completion, no backup-content output. Same approximately 10 MiB/s application pacing with 1 MiB buffer, per-file cooperative 180 seconds and total cooperative 600 seconds. Cancel with Ctrl+C at 190 seconds for one file or 610 seconds total; do not wait longer for an unresponsive call. One fixed start line, bounded progress UI and final JSON at most 64 KiB/119 records.

Source files are opened read-only with FileShare.Read, temporarily denying new write/delete opens while each file is hashed. No prune/task control, source write, backup copy, SQL/provider/Discord operation, ACL edit or provisioning. Local saved script remains as retained evidence, not automatically removed. No follow-up commands are implied if cancellation does not return control.

Require a visible `ST01R1 started` line. If `>>` appears instead, cancel unfinished input; do not add guessed quotes/braces/terminators or retry. Stop on any script-hash mismatch, host/path/type/reparse/length/stability/access failure, time/output limit, cancellation or incomplete receipt. No automatic retry. Return final JSON as a text attachment, or visible error/last progress state after cancellation.

Expected complete receipt: Operation ST01R1, Host MINI_AMD, Completed, ExpectedFiles=ObservedFiles=119, BytesRead=2,815,180,800, null FailureType and per-file SHA256. Receipt acceptance precedes any staging continuation. Maintenance window remains the existing one ending 2026-09-29T09:23:23Z; no new scheduling decision is needed inside it.

## Local validation

Saved script and launcher parsed locally without execution. Embedded list and hashing body compared with sealed ST01; changes limited to label/progress. A 1,048,593-byte synthetic MemoryStream (one full chunk plus tail) produced the same SHA256 through the chunk loop as a direct SHA256 calculation. This checks chunk arithmetic/hash usage only; no production files, filesystem/console timing simulation or watchdog guarantee. Original approval artifacts preserved; no retry has occurred.

Security-routing scope remains additive approval artifacts only; manually reviewed delta contains fixed UI text/progress and local script-hash verification, with no runtime integration or permission change. No new discovery or predecessor suite. All seven G4 proofs and actual restore remain incomplete, rollout/G5 unapproved, and the historical collector remains withdrawn.
