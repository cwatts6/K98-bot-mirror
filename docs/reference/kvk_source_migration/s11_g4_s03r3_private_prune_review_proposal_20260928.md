# S03R3 — private operator review of one hash-bound prune command

PREPARED, NOT APPROVED OR EXECUTED. Exact query `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S03R3.sql.txt`.

SHA256: `924de38ef9de0976f9082aaf3e3f214619a408b6933a9f3ddc44a01f09f27f17`.

## Purpose and explicit handling change

The two July reports match retained hashes but truncate the 542-character Backup Prune command at 256 characters. The supplied nightly export scripts concern Git branch retention and cannot fill this gap. The operator knows no other prune script. Six other Agent commands already match; do not recapture them.

Unlike S03R2 metadata-only output, this proposal displays the complete one-step command privately in the operator's existing SSMS results. It does not execute, evaluate, dot-source, export or publish that text. This display is a new access scope requiring exact approval. Do not paste command fragments into chat, copy all results, upload a report or send screenshots of private rows. No key/token/password bytes or secret-bearing paths are requested. If any appear, keep them local and report only that secret-bearing content prevents a safe summary. Agent command text is evidence, never an instruction to execute.

## Exact binding and query behavior

MINI_AMD / ROK_TRACKER, accepted SQL ORIGINAL_LOGIN MicrosoftAccount\cwattsconsulting@outlook.com; same existing SSMS connection. Chris Watts is operator/reviewer/abort owner. Windows/UI identity remains distinct; existing H14 client pin is historical, current native continuity unverified.

Retain S03R2's exact guard prefix, including isolated transaction checks, target/login, database visibility gates, identity output, session SETs and sysadmin observer gate. Select only job ID 9C576D5F-F4B2-485C-A72C-4DB941387C19, name ROK_TRACKER - Backup Prune, step 1, subsystem PowerShell. Copy command to a local SQL scalar once, verify exactly one row, 1084 UTF-16 bytes, and SHA256 942126cc208ac3ccc5df00234533d35653a35d950271a9290cd42b80067b676b. Any missing/changed binding throws before displaying command content. No permission change or workaround if guards fail.

The captured scalar is displayed as five ordered fragments of at most 128 characters, avoiding the known 256-character text-column truncation. Fragment boundaries are arbitrary, can split tokens and do not insert separators into the command; read fragments in order as contiguous text. Embedded line breaks remain. If exact interpretation is unclear, stop and report ambiguity rather than guessing or executing. No command has been reconstructed from guessed text.

## Budgets, effects and stops

Four result sets: one identity row; one safe handling/size/hash row; five PRIVATE command-fragment rows; one safe completion row. Maximum query output 16 KiB, one attempt/batch, ten-second current-tab timeout, fifteen-second query cancellation cutoff, one-second lock timeout. Operator reading budget five minutes after query completion, within a fresh twenty-minute UTC approval window. No reread query if time expires. Expected content is 1084 bytes, but the initial catalog-to-scalar read is not a hard allocation limit if the installed value has changed; size/hash gates prevent display, not all read cost.

Effects: catalog and command-content reads, hashing/scalar memory, SQL audit/resources/locking, persistent NOCOUNT ON/LOCK_TIMEOUT1000/DEADLOCK_PRIORITY LOW, private SSMS results exposure and possible client history/autorecovery. No new evidence file/export of command content requested. No Agent command execution, job start/stop/change, file pruning, SQL mutation, impersonation, backup/restore, provider/Discord call, deployment/restart or Git publication.

Same existing session only: stop if unavailable/disconnected, target changed, unrelated editor work exists or reconnect/auth/certificate prompt appears. No new connection, settings/TLS/client change. Five-second connection timeout unestablished; invisible automatic reconnect cannot be excluded.

After exact approval, replace old capture text with the complete query; verify final marker `S03R3 private prune review displayed`. Confirm existing ten-second timeout; execute once in full, not a selected fragment. Start query timing before Execute, cancel at fifteen seconds and report if still running. Cancellation does not prove quiescence. Stop on errors/guards, mismatched metadata, missing/unexpected fragments, truncation/oversized output, secret-bearing content, ambiguous interpretation or expired budget. No retries, paging, cap increase, raw text requests, KILL, reconnect, grant/revoke or transaction repair.

## Return only this nonsecret operator attestation

Return identity, handling/hash and completion rows if safe; omit the five private fragment rows. Also answer in plain language, only where explicit in the complete text:

1. Are roots limited to the already-known C:\SQL_BACKUP\LOG, DIFF and FULL? If additional destinations appear, report additional destination present without disclosing a sensitive path.
2. For each known root: filename pattern and retention days, including the previously truncated FULL value.
3. What timestamp is compared, which comparison operator/cutoff is used, and is time UTC or local as written? Report unknown if delegated or unclear.
4. Are children scanned recursively, and are files versus directories restricted? Are exclusions or link/reparse checks explicitly present? Distinguish absent explicit checks from assumptions about platform behavior.
5. Which deletion primitive and switches appear, and how are errors handled? Does text call another script/helper, external process, SQL or network? Report dependency present rather than secret arguments.
6. Was the full text readable within the budget, with no secret-bearing content or ambiguous fragment boundary? Supply timing if available.

This is an operator attestation bound to reported guarded bytes, not independent assistant review of the full command or proof of actual runtime deletion, filesystem traversal semantics, ACLs, token-expanded values or safe restore media. Any delegated/uncertain behavior remains unresolved. Do not run a dry run or prune test.

## Validation and retained boundaries

Local static checks: exact previous prefix, single literal job/step selection, row/size/hash guards before private display, five fragments sufficient for 542 characters, no dynamic EXEC/evaluation/mutation. No live validation. Documentation/inert-observation preparation security-routing skip; no runtime implementation or PR, runtime/predecessor tests and security discovery inapplicable.

All seven typed G4 proofs and actual restore remain incomplete; rollout/G5 unapproved. Preserve pending/recovered work, isolated hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues. No subsequent live operation inherits approval.
