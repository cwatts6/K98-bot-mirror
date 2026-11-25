# S03R1 receipt — SQL user-session candidates

Bounded session-label observation COMPLETE. Operator supplied all three result sets, eleven distinct session IDs and the S03R1 completion marker. No error or 65-row sentinel. Original attachment retained byte-for-byte at `.codex_artifacts/s11-g4-capture-preparation-20260926/received-S03R1-20260928T084015Z.txt` (7,813 bytes, below 64 KiB).

Receipt recorded 2026-09-28T08:40:15Z. Server observed/completed both 08:39:56.1787189Z; client completion 09:39:56.2125284+01:00 equals 08:39:56.2125284Z, inside approval 08:39:00–08:59:00 UTC. No batch start/stopwatch duration supplied; equal timestamps do not establish zero/full elapsed duration or timeout compliance. User-supplied output does not independently attest query bytes or connection continuity.

Target mini_AMD / ROK_TRACKER / ORIGINAL_LOGIN MicrosoftAccount\cwattsconsulting@outlook.com matches accepted context. VIEW DEFINITION and database CONTROL both 1. Completion is consistent with the approved query's sysadmin visibility guard passing, but no raw IS_SRVROLEMEMBER value was emitted. Do not fabricate one or infer future application privilege.

## Candidate groups

All returned host_name labels are MINI_AMD. IDs and times remain exact in the raw receipt.

| Session IDs | login_name | host_process_id | program labels | Status |
| --- | --- | --- | --- | --- |
| 52, 62, 68, 76 | NT SERVICE\SQLSERVERAGENT | 11004 | Generic Refresher; Job invocation engine; Email Logger; Contained AG | sleeping |
| 59 | NT SERVICE\SQLTELEMETRY | 1504 | SQLServerCEIP | sleeping |
| 60, 69, 71 | SHEETS_USER | 16076 | Python | sleeping |
| 64 | mini_AMD\cwatt | 7096 | Microsoft SQL Server Management Studio - Query | running |
| 65 | mini_AMD\cwatt | 7096 | Microsoft SQL Server Management Studio - Transact-SQL IntelliSense | sleeping |
| 66 | mini_AMD\cwatt | 7096 | Framework Microsoft SqlClient Data Provider | sleeping |

These are SQL session/client labels, not authenticated native process bindings. Three Python-labeled sessions use SHEETS_USER, making PID label 16076 a candidate for later authorized native correlation, not proof it is the Bot. SQL session IDs/host PIDs can be reused; never adopt old H03 PIDs or equate these labels with native creation FILETIME/token/retained handles.

The DMV login_name mini_AMD\cwatt and scalar ORIGINAL_LOGIN MicrosoftAccount\cwattsconsulting@outlook.com are distinct observed fields; retain both without asserting SID/account equivalence or a new-account requirement. Session 64 is running, but @@SPID was not emitted, so do not assert that row is the observer. The SSMS client PID label 7096 differs from historical H13 native PID 12100; current native client identity and continuity remain unverified. This mismatch does not by itself prove reconnect, executable drift or wrong identity. No automatic new client inspection or reset follows.

login_time values lack timezone annotation; retain them as supplied, not UTC/FILETIME. Sleeping is not a drain/quiescence assertion. No current request, transaction, database-specific activity, input buffer, actual writer behavior or SQL Agent execution history was captured. No missing session excludes scheduled/future/manual/provider writers.

## Next preparation and proof boundaries

SQL Agent is a remaining inventory family. Prepare its bounded job/step/schedule metadata separately from sessions using retained source/receipts first; command bodies may contain secrets and must not be emitted. Do not rerun sessions merely to refresh them, inspect returned PIDs, stop processes, alter jobs or execute procedures based on this receipt. Any new live operation needs exact approval.

All seven typed G4 proofs and actual restore remain incomplete. Writer inventory is not closed admission, owned drain, termination or no-delayed-effects proof. Rollout/G5 remain unapproved. Preserve pending/recovered work, isolated hotfix, single-account/admin-owned operation, deferred memory cause, withdrawn collector and separate KVK/view issues.

Validation: local receipt byte count, eleven unique session IDs, approved-window comparison, proposal/approval seals and original pending/evidence hashes. Documentation/evidence only; runtime/predecessor tests, pre-PR validators and security discovery skipped as inapplicable. No live call or runtime change by the assistant.
