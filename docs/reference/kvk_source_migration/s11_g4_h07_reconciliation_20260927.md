# H07 receipt reconciliation — 2026-09-27

Operator-supplied H07 output reports MINI_AMD, completion from 07:10:46.2138102Z to 07:10:49.5604055Z, elapsed 3347 ms. These reported times fall within the approved 07:07:15–07:27:15 UTC window and 20-second budget. Exactly the four approved tasks are present. No error was supplied. The completion marker is not independent execution attestation or an OS exit code.

Raw pasted JSON and trailing shell prompt are retained in `.codex_artifacts/s11-g4-capture-preparation-20260926/received-H07-20260927T071112Z.txt`. The filename is receipt-recording time, not execution time. This additive record supersedes awaiting-output status only; no sealed original is edited.

| Task | Newly resolved settings | Remaining interpretation limits |
|---|---|---|
| StartDLBotAfterSQL | Enabled, demand-start allowed, logon trigger; no catch-up; PT72H limit; battery start/continue restrictions; no configured task restart | Logon-trigger user filter was not captured. Task limit is not a demonstrated Bot lifetime limit. Wrapper source/bytes were separately reviewed; actual launch/token continuity remains unproved. |
| Graceful DL_Bot Shutdown | Weekly, interval 1, day mask 9, boundary clock 05:44; catch-up enabled; PT0S limit; no configured task restart | Offset absent in boundary; no UTC conversion or next-run prediction. Action arguments/effects remain unbound. |
| Restart daily | Weekly, interval 1, day mask 9, boundary clock 05:45; catch-up disabled; wake enabled; restart count 3 / PT5M; PT72H limit | Name does not describe actual frequency. Action arguments, including shutdown options/delay, remain unknown. No claim an actual reboot occurred or will occur at a derived UTC instant. |
| DLBotLogRotate | Daily interval 1; boundary retained as 2025-11-06T04:00:00+01:00; no catch-up; PT72H limit; battery start/continue restrictions | Do not silently reinterpret the explicit offset as current host timezone. Script path/arguments and file effects remain unknown. |

Day mask 9 combines Sunday (1) and Wednesday (8), so both weekly triggers select Sunday and Wednesday, every week. This follows [Microsoft's DaysOfWeek mapping](https://learn.microsoft.com/en-us/windows/win32/taskschd/weeklytrigger-daysofweek). Their configured boundary clock times are one minute apart; this does not establish that graceful drain completes before restart, especially with catch-up enabled only for shutdown. Preserve this scheduling constraint for later rollout planning; do not modify tasks now.

All four report raw MultipleInstances=2, retained alongside H04's IgnoreNew rendering; neither proves process-wide singleton or writer exclusion. All report idle/network-only conditions false, trigger enabled, and no populated repetition interval/duration. Null fields are not certified defaults. Battery, wake and catch-up settings can affect execution; task definitions are not execution history. No task was invoked or modified by this capture.

Still missing: nonsecret action bindings for shutdown/restart/log rotation, other named task settings, service/manual-tool/SQL Agent writer effects, native process/token binding, protected-path/key custody, provider/SQL/storage evidence. H07 does not complete any of the seven typed G4 proofs or actual restore. Later operations require separate exact approval. Memory-cause investigation remains deferred; withdrawn collector stays withdrawn; empty KVK and view-rehydration warning remain separate issues.

Validation is local JSON parsing, exact-target/window/budget comparison, source-command hash and retained evidence/seal checks. No runtime tests or new security scan for this additive evidence record. No SQL/provider/Discord, provisioning, backup/restore, Bot restart/deployment, task control or Git publication was performed by the assistant. A public Microsoft documentation lookup was used solely to interpret the day mask.
