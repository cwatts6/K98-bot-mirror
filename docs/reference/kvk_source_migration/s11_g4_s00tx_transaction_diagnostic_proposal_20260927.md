# S00TX — session transaction-state diagnostic

PREPARED, NOT APPROVED OR EXECUTED. S01R2 stopped at its transaction guard. This distinct diagnostic does not retry the S11 probe or alter/clear any transaction.

Exact query: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S00TX.sql.txt`.

SHA256: `5be0482bb312ced431463fc9a48961276eaa122f440486df8abbed65b6de1f23`.

One SELECT without a FROM clause returns seven scalar fields: server UTC, @@SERVERNAME, DB_NAME(), ORIGINAL_LOGIN(), @@TRANCOUNT, XACT_STATE(), and whether @@OPTIONS bit 2 is enabled. It does not read tables, transaction contents, locks, input buffers, plans or other sessions. There is no SET, BEGIN, COMMIT, ROLLBACK, USE, procedure invocation or remedial action. Microsoft documents that [SELECT statements without table reads do not start implicit transactions](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-implicit-transactions-transact-sql?view=sql-server-ver16). This does not clear or determine ownership of any already-open transaction.

Chris Watts remains operator/reviewer/abort owner. Use the same existing SSMS query connection as the stopped S01R2: intended MINI_AMD / ROK_TRACKER, accepted SQL ORIGINAL_LOGIN MicrosoftAccount\cwattsconsulting@outlook.com, separately retained Windows/UI label MINI_AMD\cwatt. H14 client SHA256 is 935b24379389e8260ac0d02d5e77402b005fce12c72b0ed2894a4138a6864fb7. No authentication/account change. Current-tab timeout must remain the operator-reported ten seconds; no setting changes to make this diagnostic run.

Replace only the supplied S01R2 query text in the existing unsaved editor. Do not overwrite other work or save over a file. One attempt, one batch, one result row/seven columns, <=4 KiB supplied output, ten-second client timeout, fifteen-second operator cutoff. Time from Execute; request Cancel at cutoff and stop, no retry/kill/reconnect. If still running, retain/report that fact; cancellation is not proof server work ended.

Zero new connections requested. Stop if visible target changes or a disconnect/reconnect/authentication/certificate prompt appears; do not interact with it. Five-second connect timeout is not established and invisible client automatic reconnect cannot be excluded. No new query connection, session close, COMMIT, ROLLBACK or implicit-transaction setting change is included. Unexpected returned identity stops further SQL for reconciliation.

Effects: minimal session-state SELECT/audit/CPU activity, editor text replacement and normal SSMS history/autorecovery. No application data/schema/permission changes, install, import/export, backup/restore, task/job control, provider/Discord or Git publication. Returned transaction flags authorize no automatic remediation: request operator context about any pre-existing work before proposing a state-changing step.

Approve S00TX/hash with a fresh twenty-minute UTC window; S01R2 approval is consumed and does not carry over. Preserve row/errors and reported execution timing if available, separately from receipt time; hash/reconcile/seal additively. Local static review only, no live SQL validation. Documentation/inert-query preparation security-routing skip, no runtime/configuration change or PR. All seven typed G4 proofs and actual restore remain incomplete; existing scope boundaries stay in force.
