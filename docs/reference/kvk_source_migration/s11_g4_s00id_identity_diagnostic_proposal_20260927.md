# S00ID — one-row identity diagnostic after S01R1 guard stop

PREPARED, NOT APPROVED OR EXECUTED. S01R1 stopped at its identity guard. This is a distinct diagnostic, not a retry or weakened installation probe. The values it returns must be reviewed; no returned target is adopted automatically.

Exact SQL: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S00ID.sql.txt`.

SHA256: `f840f510ebc29831c7846218e097ed6f9530a1f136ffdce4fa988040215cc298`.

One SELECT returns only server UTC, @@SERVERNAME, DB_NAME() and ORIGINAL_LOGIN(), one row/four columns. It has no target guard because the purpose is to reveal the values rejected by the prior guard. Approval explicitly permits reporting these nonsecret session identity values even if they differ from the intended target. No catalogs, application objects, definition hashes, permissions, session options, data writes or application procedures are accessed/changed by this text.

Operator/reviewer/abort owner: Chris Watts. Use the same existing SSMS query connection associated with the failed S01R1, on the existing MINI_AMD RDP host. Expected visible target remains MINI_AMD / ROK_TRACKER / MINI_AMD\cwatt; if visible labels have changed or the session is disconnected, stop rather than reconnect/switch. Client is the H14-pinned SSMS executable (SHA256 935b24379389e8260ac0d02d5e77402b005fce12c72b0ed2894a4138a6864fb7); current-tab execution timeout must remain the operator-reported 10 seconds. Do not change settings to proceed.

Use the existing unsaved editor: replace only the previously supplied S01R1 batch with this exact diagnostic text, without rerunning the old batch or saving over a file. If the editor holds other work, stop. One attempt, one batch, one row, <=4 KiB output, 10-second query timeout and 15-second operator cutoff. Start timing before Execute; request Cancel at cutoff, preserve any result/error and do not retry. Cancellation is not proof server work ended; report persistent running state, no kill/reconnect. Zero new connections requested; no verified five-second connection timeout and no guarantee against invisible client automatic reconnection. Stop on reconnect/auth/certificate prompts without interaction.

Effects: a minimal metadata SELECT, normal SQL audit/CPU activity, editor text replacement and possible client history/autorecovery. No SET statements or data/schema/permission changes. No Bot/SQL installation, task/job control, provider/Discord calls, export, backup/restore, security-setting change or Git operation.

Approve S00ID by exact hash with a fresh 20-minute UTC window; S01R1 approval does not carry over. Preserve the one result row and all errors as a new dated receipt, along with execution timing if available; distinguish receipt time. Unexpected identities stop further SQL for reconciliation, not permission to relax the original guard. A new S01 probe would require its own exact decision after this review.

Validation: local static review of four built-in identity/time expressions; no live SQL validation performed. Documentation/inert-query preparation security-routing skip; no runtime/configuration change or PR. All seven typed G4 proofs and actual restore remain incomplete, and prior boundaries remain in force.
