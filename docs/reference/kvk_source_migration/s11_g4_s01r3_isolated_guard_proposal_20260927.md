# S01R3 — isolated transaction-state guard for the S11 metadata probe

PREPARED, NOT APPROVED OR EXECUTED. S00TX2 returned standalone state/count/implicit flag 0/0/0, contrasting with the combined diagnostic's 0/1/0. The operator suggests the observation may be tripping over its own transaction context. This is a plausible evaluation-context explanation, not a proven engine mechanism or proof of session continuity. No explicit transaction was started in the supplied capture SQL. The conservative guard was introduced by the assistant for capture; it is not application implementation.

Exact query: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S01R3.sql.txt`.

SHA256: `aea8c7a4f1ca7172c6499256afb0d01ed609fde330a513ca259f7a9fc82d4188`.

## Revised guard, unchanged acceptance rule

First declare a batch-local integer and assign XACT_STATE() using its own table-free SELECT. Separately capture @@TRANCOUNT and the implicit-transactions bit into batch-local integers. Reject any nonzero or null captured value before evaluating server/database/login expressions. No BEGIN/COMMIT/ROLLBACK, session transaction-setting changes or system/application writes are introduced. SELECT variable assignments do not add result sets. The specific assignment form has not been live-tested; S00TX2 tested isolated SELECT output. Sequential capture is not an atomic transaction-state proof. If this still fails, stop without bypassing the guard or claiming an open operator transaction.

The accepted SQL identity remains MINI_AMD / ROK_TRACKER / MicrosoftAccount\cwattsconsulting@outlook.com, with Windows/UI MINI_AMD\cwatt retained separately. Identity and VIEW DEFINITION guards remain. Eleven object targets, hash-size limit, output columns, MAXDOP1 and session settings remain identical to S01R2. Only transaction capture/evaluation ordering and final completion label change. Do not reinterpret the prior errors as missing S11 installation or source.

## Exact operator envelope

Chris Watts remains operator/reviewer/abort owner. Same existing SSMS connection and unsaved editor used for S00TX2; replace only supplied diagnostic text, not other work. No new query connection or file save. SSMS observed executable SHA256 is 935b24379389e8260ac0d02d5e77402b005fce12c72b0ed2894a4138a6864fb7 at `C:\Program Files\Microsoft SQL Server Management Studio 22\Release\Common7\IDE\SSMS.exe`. Operator-reported current-tab timeout must remain ten seconds; no settings adjustment is included.

One attempt, one batch, three result sets with rows 1/11/1, <=32 KiB output, <=1 MiB eligibility per module-definition hash. Ten-second client timeout and fifteen-second operator cutoff, timed from Execute. Cancel at cutoff, preserve output/errors, no retry/kill/reconnect. Cancellation does not prove server work ended. Catalog CPU/I/O/memory is not a certified hard bound. Stop on guard/error, identity/visibility mismatch, unexpected/truncated results, definition anomaly, time/output cap or disconnect/reconnect/auth/certificate prompt. No new connection requested; five-second connect timeout remains unestablished, and invisible client automatic reconnect cannot be excluded.

Effects: scalar assignments and metadata SELECTs/audit/CPU/locking; session NOCOUNT ON, LOCK_TIMEOUT 1000 and DEADLOCK_PRIORITY LOW remain after the batch; editor text and normal client history/autorecovery. No data/schema/permission write, application procedure, install, import/export, task/Agent control, provider/Discord, backup/restore, deployment or Git publication. Table module-definition fields may be null by design; missing/invisible/encrypted/oversized objects remain unresolved, not permission to install or retry.

## Approval and evidence

Approve S01R3/hash and the revised evaluation sequence under this same existing-session envelope for a fresh twenty-minute UTC window. Earlier probe/diagnostic approvals do not carry over. Preserve all three result sets/errors and operator elapsed/start/end if available; separate receipt time and seal additively. No later installation/probe follows automatically.

Validation: static delta review against sealed S01R2, eleven unchanged object names, isolated scalar capture before identity evaluation and conservative nonzero/null stop. No live SQL test of the revised batch. Documentation/inert-query security-routing skip; no application/configuration/permission change or PR. Original failures and diagnostic results remain intact. All seven typed G4 proofs and actual restore remain incomplete; established production/single-account/deferred-memory/withdrawn-collector and rollout/G5 boundaries are unchanged.
