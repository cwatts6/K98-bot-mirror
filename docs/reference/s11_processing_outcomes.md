# S11 processing outcomes and admin resolution

This change is source work, not authorization to replay, settle or restart any
historical job. The successful 9 October export remains complete. Only imports
registered with the new exact execution receipt participate in automatic handling.

SQL import and Google delivery are separate outcomes. Fresh SQL/cache stats use
the normal stats channel and existing mention/cap rules. A separate configurable
Sheets channel receives analysis links and export outcomes without mentions.
See [notification operation and resolution](s11_notifications.md) for that separate
delivery layer and its local administrator command.

## What recovers automatically

Each coordinated import binds one `StatsImportExecution` receipt to its immutable
filename and exact export preparation/owner/fence. A single-use SQL wrapper holds
an execution lock. UPDATE_ALL2 records Phase A import commitment and final report
completion inside the corresponding transactions. Phase B can commit intermediate
reports; `partial` therefore does not mean that all derived work rolled back.

The bot releases metadata for a proven unstarted or rolled-back import only after
both execution and producer locks are exclusive, runtime scope matches, and every
ownership/version comparison passes. It retains imported data and input files.
It never repeats an import. A still-live writer can also finish a known completed
SQL checkpoint/capture while it holds the original snapshot guard. Unknown capture
or spool acknowledgments are retained.

The observer checks at most 16 eligible receipts every 30 seconds. Restart resumes
discovery; elapsed time and absence of a process never prove a SQL outcome.
Failed SQL skips cache rebuilding, maintenance, configuration import and export.
Failed configuration import skips its dependent export. A failed ancillary
notification cannot release or reacquire export ownership.

## Admin actions

Use the preparation UUID from `stats_import_outcome` or `export_writer_stage` logs.
The command is restricted to the existing admin/notification-channel boundary;
responses are ephemeral and cannot mention users or roles.

1. `/ops import_resolution preparation_id:<uuid> action:status`
2. If resolution is offered, use `action:preview` to get the exact confirmation token.
3. Copy the returned `action:resolve` command and supply an audit reason. Changed
   evidence invalidates the preview. Obtain a new preview rather than forcing it.

| Observed outcome | Admin action |
| --- | --- |
| Execution or producer still active | Let it finish, then check status again. Do not restart or clear its resource. |
| `prepared` or `rolled_back`, eligible ownership | Usually settles automatically. If the observer was unavailable, preview/resolve releases only this failed preparation. Fix the logged SQL/file/configuration cause before a fresh upload. |
| `partial` | Imported rows and possibly some reports are committed. Correct the reporting failure. Preview explains the explicit `accept_partial:true` decision to supersede unfinished reports with a **new scan containing new data**. A renamed/reuploaded copy is not a new scan. |
| `completed` but capture unacknowledged | Do not re-import or discard it. Preserve the preparation and spool. Escalate with the evidence bundle below for exact checkpoint/capture reconciliation. This command intentionally cannot clear committed generations. |
| `running`, `import_committed`, or missing exact receipt after interruption | SQL outcome remains unproven. Preserve ownership. Escalate with exact SQL transaction/claim/receipt evidence; a stopped process alone is insufficient. |
| Already resolved | No further action. Repeated confirmation is harmless and does not repeat settlement. |
| Ownership/version/scope differs | Stop. Preserve all records and collect the correlated evidence; never edit identifiers or broaden the release. |

For escalation, include preparation UUID, UTC time, `stage`, `outcome`,
`next_action`, sanitized `sqlstate`/`native_errors`, and the command's SQL outcome,
error number/procedure/line and committed scan. Retain the immutable input identity
and relevant SQL claim/receipt, preparation/resource and spool records. Do not paste
credentials, connection strings or player data into a public issue. The command
does not grant SQL permissions, repair filesystem ACLs or resume provider requests.

Useful root-cause checks: SQL error 4834 means the approved bulk permission needs
verification; log/headroom refusal needs SQL log-health investigation; source-data
validation failure requires a corrected new scan. For a contract/source mismatch,
verify the installed SQL migration and approved runtime contract instead of disabling
the gate. Use the exact logged error rather than guessing from a timeout alone.

## Rollout and review gates

The Bot foundation requires SQL migration `20261009_001_stats_import_outcomes`,
the new `deploy/export_stats_import_outcome_source.json`, and a reissued protected
SQL contract. The old source pin is deliberately rejected. The application grant
plan adds SELECT/INSERT/UPDATE on the receipt table; the migration grants the existing
legacy entry role EXECUTE on the wrapper. No new account, schema privilege, signing
fallback or activation flag is introduced.

After separate Bot/SQL Changes reviews and CI, use mirror-first patch promotion to
private main. Installation must drain the protected pair, apply the reviewed SQL
migration using the normal migration runner (which records its checksum), apply
the three reviewed receipt-table grants to the existing SID-bound application user,
and independently validate/reissue the source, metadata and permission contracts.
Deploy the matching private-main source through the supported updater. Deployment
and restart require their own readiness decision; none were performed here.

Rollback is a coordinated forward fix. Do not drop receipts or restore old SQL
definitions over new imports. Preserve both execution evidence and retained outputs.
An old Bot/runtime contract will refuse the amended module instead of silently
falling back. Disposable SQL rehearsal is required before merge readiness; synthetic
protocol tests do not certify the entire production UPDATE_ALL2 workload.
