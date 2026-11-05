# S00TX2 isolated state receipt — 2026-09-27

Raw supplied text is retained in `.codex_artifacts/s11-g4-capture-preparation-20260926/received-S00TX2-20260927T101526Z.txt`. Three one-row sets report:

- Standalone XACT_STATE(): 0.
- Transaction count: 0; implicit-transactions flag: 0.
- Server UTC: 2026-09-27 10:15:08.3731234; server mini_AMD; database ROK_TRACKER; original login MicrosoftAccount\cwattsconsulting@outlook.com.

Supplied client completion 2026-09-27T11:15:08.4230864+01:00 equals 10:15:08.4230864Z. Both timestamps fall within the approved 10:08:52–10:28:52 UTC window. The server timestamp occurs in the third SELECT, not at batch start; do not derive total duration from its difference to completion. Start/duration were not supplied. Receipt time 10:15:26Z is separate. No error was supplied; three expected one-row sets are present.

This differs from earlier combined S00TX's 0/1/0 observation. It supports an evaluation-context hypothesis for the state value, but does not prove an engine defect, exact causal mechanism or unchanged session state between batches. No operator-owned open transaction or need to commit/roll back is established by these observations. Preserve both receipts without recasting either as invalid.

A proposed guard revision captures XACT_STATE in an isolated statement before identity/system expressions, then separately captures count and implicit flag, and rejects any nonzero (or null) captured value. This retains the conservative acceptance condition rather than permitting XACT_STATE=1. It is a new query requiring approval; the new assignment form has not been live-tested by this SELECT-based diagnostic. Sequential scalar captures are not an atomic or lifetime transaction-state proof.

The guard is capture-only logic introduced during this task, not Bot/SQL application source. No application implementation fix, COMMIT, ROLLBACK, reconnect or transaction-setting change occurred. No S11 object rows have yet been obtained. All seven typed G4 proofs and actual restore remain incomplete. Validation here is local receipt/query comparison and additive evidence preservation; no new SQL executed by the assistant.
