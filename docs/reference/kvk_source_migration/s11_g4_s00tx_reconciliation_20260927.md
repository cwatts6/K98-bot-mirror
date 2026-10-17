# S00TX receipt and unresolved evaluation context — 2026-09-27

Raw header/row retained in `.codex_artifacts/s11-g4-capture-preparation-20260926/received-S00TX-20260927T100651Z.txt`. Server UTC 2026-09-27 10:06:30.0761993 lies within the approved 10:05:23–10:25:23 UTC window. Start/end/duration were not supplied, so elapsed-budget compliance remains unproved. Receipt time 10:06:51Z is separate.

The row reports mini_AMD / ROK_TRACKER / MicrosoftAccount\cwattsconsulting@outlook.com, matching accepted SQL identity. It reports transaction_count=0, transaction_state=1 and implicit_transactions_enabled=0.

The XACT_STATE value alone would satisfy S01R2's stop condition in this later observation. It does not retrospectively prove which value caused the earlier stop or that state was continuous between batches. Correction to shorthand commentary: this identifies a currently observed guard-triggering value, not a proven historical cause. No implicit-transactions enablement is reported by this row; no positive transaction nesting count is reported.

[Microsoft's @@TRANCOUNT documentation](https://learn.microsoft.com/en-us/sql/t-sql/functions/trancount-transact-sql?view=sql-server-ver16) describes the connection's transaction nesting counter. [XACT_STATE documentation](https://learn.microsoft.com/en-us/sql/t-sql/functions/xact-state-transact-sql?view=sql-server-ver17) describes transaction state and distinguishes it from nesting. Those general semantics do not, by themselves, explain this combination in the combined diagnostic expression on this instance. Do not label an engine defect, active operator-owned transaction, stale connection or guard implementation defect as established. Evaluation context is a hypothesis requiring separate evidence.

No COMMIT, ROLLBACK, connection close/reconnect, session kill or SET IMPLICIT_TRANSACTIONS OFF is authorized or justified by this receipt. The guard was added by the assistant during capture preparation, not part of the Bot/source implementation; its false-positive behavior has not yet been proved. Do not weaken it and rerun S01 on assumption.

A proposed separate diagnostic isolates XACT_STATE() in its own SELECT, followed by count/options and identity in separate SELECTs. It reads scalar functions only, without table access, transaction control or session SET changes. Sequential samples are not an atomic snapshot. Review results before designing any corrected guard; no metadata probe follows automatically.

All seven typed G4 proofs and actual restore remain incomplete. No S11 object results have been obtained from the stopped probes. Local reconciliation/public documentation review only; no new SQL executed by the assistant. Original evidence and scope boundaries are preserved.
