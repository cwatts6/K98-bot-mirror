# P0b: prevent recurring configuration-only capture incidents

## Scope and contract

Standalone startup and admin ProcConfig imports refresh SQL configuration and targets.
They retain coordinated output for recovery but do not request spreadsheet delivery.
The import pipeline does request delivery through its producer collector. Record that
distinction at the configuration import entrypoint, before writer admission, in the
hashed durable producer request: configuration_only_v1 or pipeline_export_v1.

Existing guided continuation requests keep their original approved intent. Historical
requests without a disposition remain eligible for their existing guided decisions;
absence of a collector during recovery cannot establish a no-export intention.

The configuration adapter reuses the verified no-export closeout. It requires the
atomic configuration/targets checkpoint, matching registered output, intact captured
bytes, no job and no retained resource ownership. The conclusion DAL rechecks version,
ownership, active SQL execution and provider streams before recording its durable
receipt. RecoveryService allows only configuration_producer/complete_configuration_only.
Lost approval or completion replies reconcile the same action after restart. No import
or provider write is replayed; captured bytes and the original request are retained.

SQL-facing contracts were checked against C:/K98-bot-SQL-Server ExportPreparation,
ExportResource, ExportExecutionStream and StatsImportExecution definitions. Existing
request, generation and conclusion columns are reused. No SQL migration is required.
No command/view SQL or new permission bypass is introduced.

## Acceptance and verification

1. Standalone imports record no-export intent before admission, including refusal.
2. Pipeline imports retain export intent across thread offload and remain exportable.
3. Complete unqueued configuration-only captures resolve automatically with the
   configuration_only_completed outcome and a verified durable action receipt.
4. Lost approval/completion acknowledgements and restart never create a second action.
5. Missing bytes, changed intent/configuration/ownership, active execution, provider
   streams, held resources or queued jobs cannot authorize automatic closeout.
6. Legacy captures, guided retries and requested exports keep guided review, queue,
   skip and verification workflows. No historical SQL success is invented.
7. Downloadable reports include original intent, input/configuration context, pending
   verification and completion without claiming provider delivery or cache freshness.
8. The protected updater accepts only the complete ten-file reviewed transition.
   Changed, missing or foreign members are refused. Upgrade uses the previous
   cache-only-r3 manifest and preserves existing installed custody checks.

Validation covers focused producer/configuration/guided-report regressions, disposable
SQL lost-reply/restart/negative cases, architecture/deferred/security-routing gates,
lint, imports, registration and protected upgrade rehearsal. Changes security review
targets the final immutable mirror and production diffs; Deep scan stays off.

## Operator acceptance after this release

Upgrade the installed updater using the supplied package, then deploy the reviewed
private-main release through the normal updater and prompted graceful restart.
Allow the normal startup configuration import and recovery cycle to finish. Download
the complete report: new standalone configuration captures should be resolved with
original_export_intent=configuration_only_v1 and outcome=configuration_only_completed.
No manual export decision should be necessary for those captures. Existing historical
or pipeline work must retain its original decisions. Check current monitor health and
pending verification as well as the open count. Do not rerun imports just to test this.

## Required remaining P0b scope

Zero open records is a production observation, not completion of P0b. The full matrix
in recovery_capture_decision_summary.md remains mandatory: monitor contention and
startup diagnostics; exhausted admission; genuine configuration membership conflicts;
still-needed historical/unknown-write replacement and delivery; remaining producer and
rollover interruptions. Each needs original input/configuration context, concise guided
decisions, durable verification and complete report coverage. None is deferred out of
P0b by this focused increment.
