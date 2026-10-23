# D01 stopped identity receipt and D01R1 proposal

D01 STOPPED as designed; development exclusion inventory remains incomplete. Operator error: Msg 51000, Level 16, State 1, Line 20, unexpected development server/database/original login. Safe identity row observed at 2026-09-28T10:42:02.5035780Z, received 10:42:20Z, within approved maintenance window. No completion or elapsed time supplied.

All target fields matched: server 9SX2VF4\K98DEV, machine 9SX2VF4, instance K98DEV, database master. ProductVersion 16.0.1200.5 and observer_sysadmin=1. ORIGINAL_LOGIN was MicrosoftAccount\cwattsconsulting@outlook.com, while D01 expected reported Windows/UI label 9SX2VF4\cwatt. The login comparison accounts for this stop; no transaction failure or wrong target is indicated by this receipt. Retain the two labels separately; do not claim SID/account equivalence or require another Windows account.

In the approved batch the guard precedes database/file/default-path reads, so the stopped receipt does not supply them. Earlier scalar and session SET effects remain. No retry, reconnect, grant or transaction repair occurred here. Raw user messages are retained in conversation; normalized receipt is `received-D01-stop-20260928T104220Z.json` in the capture evidence directory.

## D01R1: prepared, not approved or executed

Exact query `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/D01R1.sql.txt`.

SHA256: `2e20737c9c9831fb3df0fc5bc65b5247386981ba2f61921da7589888775dcdb7`.

Only two edits from D01: expected ORIGINAL_LOGIN becomes the observed MicrosoftAccount\cwattsconsulting@outlook.com; completion marker becomes `D01R1 development exclusion metadata completed`. No server/machine/instance/master, transaction or sysadmin guard is removed or widened. Catalog selects and budgets remain byte-identical. This proposes explicit acceptance of the observed SQL identity for this exact development observer, not general authorization for that identity on other targets.

The D01 proposal's full scope/effects/stops apply: existing local SSMS connection localhost\K98DEV, master, ten-second tab timeout, one attempt/batch, fifteen-second operator cancellation cutoff, 512 KiB output; five sets (identity, <=65 database rows, <=257 file rows, default paths, completion). Each sentinel stops; no retry/pagination. No new connection, settings beyond already-approved tab preparation, permissions, SQL mutation, file access, creation, backup/restore, job control or deployment. Preserve any partial output/errors. All returned databases/files remain protected exclusions; no destination is selected.

Existing maintenance window ends 2026-09-29T09:23:23Z; no scheduling reapproval required. New query hash and acceptance of observed SQL login need exact scope approval before execution. Replace old D01 text with complete D01R1 only after approval; do not rerun old query. Stop on any changed target/login, guard error, reconnect prompt, missing/truncated/unexpected output, row/output limit or time cap. Do not infer original client continuity from matching labels.

Local validation: exact two-replacement comparison and original evidence preservation. No live SQL. Documentation/inert-proposal security-routing skip; runtime tests/predecessor suites/security discovery inapplicable. All seven typed G4 proofs and actual restore remain incomplete, rollout/G5 unapproved. Preserve pending/recovered files, isolated hotfix, approved single-account/admin-owned model, deferred memory cause, withdrawn collector and separate KVK/view issues.
