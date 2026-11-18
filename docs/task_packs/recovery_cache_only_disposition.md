# P0b: prevent recurring cache-only capture incidents

## Problem and bounded result

The player-cache builder runs SP_Stats_for_Upload under coordinated writer ownership.
Normal writer completion retains a verified capture, but an independent cache refresh
does not request a spreadsheet export. Discovery previously presented every such
capture as an unresolved export decision. This increment records caller intent before
writer admission and verifies a durable no-export closeout for successful cache-only
captures. It preserves the SQL result and captured bytes.

The processing pipeline deliberately collects producer captures for subsequent
export. Its report invocations retain pipeline-export intent, including across thread
offload. An absent collector is interpreted only at the explicitly designated cache
entrypoint when creating a new request; it is never reconstructed after a crash or
applied to historical records.

## Architecture and SQL contract

- The existing producer-intent service records a bounded disposition in the request.
- Existing ExportPreparation RequestJson/RequestHash preserve that intent before SQL.
- PlayerReportRecoveryDAL accepts only the two named versioned dispositions for the
  player report producer; old requests remain valid without an assumed disposition.
- The player-report adapter verifies the atomic checkpoint, registered configuration,
  spool bytes, no queued job and no held resources before offering automatic closeout.
- The existing capture-conclusion DAL repeats version/owner checks, excludes active
  SQL execution and provider streams, and records the no-export receipt atomically.
- RecoveryService permits only the specific player_report/complete_cache_only pair
  in addition to its existing verified read release. Durable action receipts handle
  lost replies and restart. Configuration and historical captures retain their
  existing guided decisions.
- Reports show original intent, pending verification and verified completion. They
  do not certify cache freshness or spreadsheet delivery.

SQL contracts checked against C:/K98-bot-SQL-Server: dbo.ExportPreparation,
dbo.ExportResource, dbo.ExportExecutionStream and dbo.StatsImportExecution. Existing
columns, states and completion DAL are reused; no schema migration is introduced.
No new SQL is added to command or view layers. No generic automatic skip permission
or release of unknown-write reservations is introduced.

## Acceptance and validation

1. A new independent cache refresh records cache-only intent before admission.
2. A processing-pipeline refresh records export intent and remains exportable.
3. A successful unqueued cache-only capture closes once with a verified receipt;
   SQL output and spool identity remain unchanged and no job/provider write occurs.
4. Lost action or closeout acknowledgement reconciles the same receipt after restart.
5. Missing/corrupt bytes, changed registration/intent, held resources, live execution
   or provider streams cannot authorize this automatic closeout.
6. Existing historical and configuration captures still require guided decisions;
   the former backlog is not silently reclassified.
7. The downloadable report explains automatic verification and preserves the original
   input/configuration context; normal admin permission checks still govern buttons.

Focused coverage includes actual temporary SQL completion/lost-reply/restart cases,
thread propagation, legacy and pipeline negative controls, invalid intent and missing
capture checks, plus existing producer, queue/skip and guided workflow regressions.
Changes-only security review is required for the final immutable Bot diff; Deep is off.

## Operator verification

After this separate PR is reviewed and deployed, allow the normal startup cache
refresh and recovery cycle to finish. The new player-report record should show
cache_only_completed/resolved without an export decision. Download the complete
report and verify the original cache-only intent and saved completion. Existing
captures without that intent keep their Queue verified capture / Keep SQL; skip
this export choices. A pipeline report must still proceed through its normal export
handoff. No repeat import, provider write or extra restart is needed as a test.

## Remaining required P0b work

The priorities and acceptance criteria in recovery_capture_decision_summary.md remain
mandatory. This increment covers recurring independent player-cache captures only.
Configuration-output disposition, genuine membership conflicts, exhausted admission,
still-needed historical/unknown-write delivery and remaining producer/rollover recovery
remain in scope. Monitor contention diagnostics and the startup path warning also
remain required. Zero open incidents alone does not establish full recovery coverage.
