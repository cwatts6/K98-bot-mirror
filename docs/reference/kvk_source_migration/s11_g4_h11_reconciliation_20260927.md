# H11 receipt reconciliation — 2026-09-27

Operator-supplied MINI_AMD output reports completion from 08:13:47.0802222Z to 08:13:48.5685747Z, elapsed 1489 ms. Reported timestamps fall within the approved 08:02:29–08:22:29 UTC window; stopwatch and approximately 1.488-second UTC endpoint duration are below 20 seconds. Preserve distinct clock fields. Both approved tasks are present and both argument allowlists matched. No error was supplied. Completed is not an independently observed OS exit code or native execution attestation.

Raw JSON and trailing prompt are retained at `.codex_artifacts/s11-g4-capture-preparation-20260926/received-H11-20260927T081404Z.txt`. Filename time records receipt, not execution. This additive record supersedes awaiting-output status only, leaving historical approvals/proposals/seals unchanged.

## Resolved action bindings

`\K98 SQL Nightly Schema Export` reports Ready, powershell.exe, working directory `C:\K98-bot-SQL-Server`, and the exact installer-default arguments:

```text
-NoProfile -ExecutionPolicy Bypass -File "C:\K98-bot-SQL-Server\deploy\Invoke-NightlyProdSchemaExport.ps1" -RepoPath "C:\K98-bot-SQL-Server" -BotRepoPath "C:\discord_file_downloader" -ServerName "MINI_AMD" -DatabaseName "ROK_TRACKER"
```

This binds the reported task to a named wrapper and explicit nonsecret targets. It does not prove deployed wrapper/dependency bytes, environment values, SQL permissions, executable resolution or actual effects. H11's reviewed local wrapper can perform Git fetch/pull, export, retention/postprocessing and failure alerts if invoked. No invocation, export or SQL connection occurred in this observation. Ready is not Running.

`\Restart\RUN_Bot` reports Disabled, executable `C:\discord_file_downloader\venv\Scripts\python.exe`, working directory `C:\discord_file_downloader`, and arguments `C:\discord_file_downloader\run_bot.py`. This resolves the disabled task's entrypoint. H02 previously sampled run_bot.py's hash; H11 is not a fresh file-byte observation or proof of continuity. It does not authorize enabling/starting this task. StartDLBotAfterSQL remains the operator-confirmed normal startup task.

## Remaining scope

The older disabled K98 SQL Schema Export script path and Restart daily arguments remain unknown/withheld. The pending question seeks only already-known nonsecret facts, without live inspection; no answer is assumed. Current nightly-wrapper deployed bytes/dependencies and complete task/service/manual-tool/SQL Agent writer exclusion remain unproved. Any later exact observation requires its own approved scope/window; do not rerun predecessors or broaden H11.

All seven typed G4 proofs and actual restore remain incomplete. Preserve native identity, protected-path/key custody, provider, SQL and storage gaps. Production remains the isolated hotfix by retained evidence; same-account/admin-owned startup/review and fresh output/equivalent reports stay settled. Memory cause stays deferred; withdrawn collector remains withdrawn; empty KVK/view-rehydration remain separate. No rollout, G5, provisioning, restore, deployment/restart or Git publication approval follows.

Validation: local JSON parsing, exact target/action argument/window/budget comparisons, command hash and original file/seal integrity verification. No application/configuration/permission change or PR; runtime tests, pre-PR validators and new security scan are skipped for this additive evidence-only record.
