> **Current E100, 5 November 2026: P01.5 CLOSED.** Private `24bca82f` deployed; exact custody repair, source/startup and observed normal calendar/pinned delivery accepted. See [closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.5%20Closeout%20-%202026-11-05.md), [retained natural observations](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Natural%20Acceptance%20-%202026-11-05.md) and [P01.6 handover/scope](Startup%20Import%20Export%20Reliability%20-%20P01.6%20Handover%20and%20Scope%20-%202026-11-05.md). P01.6 read-worker ownership is next, review/scope only. P01.4/P01.5 natural limits, fresh whole-flow import/export and P02-P05 remain explicit. Earlier checkpoints below are historical; do not replay accepted work. Preserve this local delta through the [carry-forward manifest](Startup%20Import%20Export%20Reliability%20-%20Documentation%20Carry-forward%20-%202026-11-05.md).

> **Historical E95 - 5 November 2026:** P01.4 delivered and deployed; locally qualified across the full scope; production acceptance confirmed for exercised paths, with remaining natural-activity checks tracked explicitly. See [closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.4%20Closeout%20-%202026-11-05.md), [acceptance register](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Natural%20Acceptance%20-%202026-11-05.md) and [P01.5 handover/scope](archive/Startup%20Import%20Export%20Reliability%20-%20P01.5%20Handover%20and%20Scope%20-%202026-11-05.md). P01.5 calendar ownership and outcomes (F23/F24/F25) is next, review/scope first. Earlier dated checkpoints below are historical. Carry this documentation delta through [the current manifest](archive/Startup%20Import%20Export%20Reliability%20-%20P01.5%20Delivered%20Documentation%20Carry-forward%20-%202026-11-05.md).

# Startup, import and export reliability: action census

> **Historical E91, 5 November 2026:** The [complete local qualification receipt](archive/Startup%20Import%20Export%20Reliability%20-%20P01.4%20Complete%20Local%20Qualification%20-%202026-11-05.md) records the full original P01.4 design implemented and qualified locally, with both optional workers enabled in the unpublished candidate. Cost, physical-drain, diagnostic-priority, updater, regression and Changes-review gates passed. No CSV scope was deferred. Publication/deployment and natural-activity acceptance remain outstanding; earlier E88-E90 disabled/pending statements below are historical. Existing changes and archive moves are preserved.

> **Historical E85/E86 - 5 November 2026: P01.3 CLOSED.** Passive health, persistent Refresh and the complete-ZIP correction are merged, deployed and live-validated at private `6ec393f71626d15fcb8c50c840854fb681d5f09e`. See [P01.3 closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.3%20Closeout%20-%202026-11-05.md) and [P01.4 handover/scope](archive/Startup%20Import%20Export%20Reliability%20-%20P01.4%20Handover%20and%20Scope%20-%202026-11-05.md). P01.4 (F17/F30) is next, review/scope only. P01.1/P01.2a remain accepted; P01.2b is closed by decision without feature delivery. P01.4-P01.6/P02-P05 and exact incident recovery remain open. Dated checkpoints below retain historical evidence, not current approval or scheduling authority. The [new documentation carry-forward manifest](archive/Startup%20Import%20Export%20Reliability%20-%20P01.4%20Delivered%20Documentation%20Carry-forward%20-%202026-11-05.md) covers this local closeout update.

> **Historical programme checkpoint - 4 November 2026 (E68/E69):** P01.2a is deployed and accepted for its declared reporting/evidence scope at private `67c4e12a8ecf0c25280770860480ac65a6826602`.
> Read the [P01.2a closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Closeout%20-%202026-11-04.md) for delivered corrections, evidence limits, learnings and remaining owners; [P01.2b handover](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Handover%20and%20Scope%20-%202026-11-04.md) is the next review/design task.
> The earlier checkpoint is retained history. Current remaining implementation is P01.5/P01.6/P02-P05 and exact incident recovery; P01.4 natural acceptance is tracked separately at E95. Do not replay accepted work.

Date: 2 November 2026. Source baseline: `a025adb7a69aac321fd62794b871ed5903338f44`.

See the [tracker](Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md) and [tracing review](Startup%20Import%20Export%20Reliability%20-%20Tracing%20-%202026-11-02.md) for findings, evidence limits and acceptance IDs.

All 73 allowed source/action pairs in `services/recovery_release_policy.py:P0A_ACTIONS` are mapped below: 52 distinct action names across 22 source kinds, four of which expose no individual actions. Availability still depends on the current state. This is a policy census, not a count of incidents or proof that every branch has run.

Recommendations require concrete design and qualification. They do not authorise automatic cancellation, replay or implementation. The four actions in the central automatic policy are not the entire automation system: `processing_outcome_worker` settles eligible known failures, and live writer recovery can capture exact completed SQL after a lost acknowledgement. Preserve both.

## Dispositions

| Disposition | Recommendation | Acceptance |
|---|---|---|
| `existing_automatic` | Keep exact-evidence automation; remove unnecessary operator presentation and handle ordinary contention. | A02/A05/A08 |
| `automatic_receipt_candidate` | Bind or finish the exact existing receipt automatically under reviewed idempotent policy; no new producer/provider request. | A05/A06/A08 |
| `automatic_copy_candidate` | Consider policy-approved exact-byte repair from a verified surviving copy/backup; preserve originals and audit; not delivery success. | A08/A09 |
| `existing_outcome_worker` | Already settled automatically for eligible unstarted/rolled-back receipts by processing_outcome_worker and writer failure handling; retain exact evidence and investigate any residual manual case. | A03/A05/A08 |
| `settlement_candidate` | Consider exact unstarted/rollback closure without operator acknowledgement; preserve failed original result and distinct continuation intent. | A03/A05/A08 |
| `continue_original_intent_candidate` | Preserve existing live completion/capture recovery; assess remaining automatic continuation from durable original intent and exact stage evidence. Capture/queue is not delivery. | A05/A08 |
| `fresh_work_policy` | Current inputs/configuration or independent new stage can change meaning; retain useful review when intent changes, otherwise define automatic continuation policy. | A05/A08 |
| `retry_policy` | Transient pre-entry failure may retry automatically with same intent; external re-export requires exact no-delayed-write/damage evidence and a separate repair identity. | A03/A06/A08 |
| `active_settlement_or_probe` | Separate original-work completion/settlement from optional fresh provider checks; schedule and bound necessary verification, do not run on view rendering. | A02/A06/A07 |
| `discard_read_decision` | Fencing/discarding an unstarted or entered read needs intent-specific policy; automate disposable health-read cleanup separately from business-input decisions. | A05/A08 |
| `business_disposition` | Retain genuine decision to stop/skip/abandon original work; explain remaining impact. Never require this to acknowledge already completed work. | A08/A09 |
| `unknown_outcome_disposition` | Current code accepts an explicit disposition while original effects may remain unknown; automate only if independent evidence establishes the same safe policy. | A04/A08/A09 |
| `destination_choice` | Retain meaningful output retirement/file/settings choice; avoid repeated confirmation of unchanged already-approved intent. | A06/A08 |
| `replacement_execution` | New externally visible work on changed destinations; preserve durable intended operation and consider one end-to-end approval rather than repeated acknowledgements. | A05/A06/A08 |
| `new_attestation` | New evidence of current independently verifiable state, not reconstruction of missing original success; evaluate whether system proof removes a valueless confirmation. | A08/A09 |

## Source and action coverage

| Source kind | Action | Disposition | Implementation sources |
|---|---|---|---|
| `export_rollover` | `activate_replacements` | `destination_choice` | services/rollover_replacement_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/rollover_replacement.py |
| `export_rollover` | `choose_replacements` | `destination_choice` | services/rollover_replacement_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/rollover_replacement.py |
| `export_rollover` | `continue_unstarted_rollover` | `continue_original_intent_candidate` | services/rollover_replacement_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/rollover_replacement.py |
| `export_rollover` | `discard_replacement_check` | `discard_read_decision` | services/rollover_replacement_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/rollover_replacement.py |
| `export_rollover` | `finish_replacement_check` | `automatic_receipt_candidate` | services/rollover_replacement_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/rollover_replacement.py |
| `export_rollover` | `isolate_targets` | `destination_choice` | services/rollover_replacement_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/rollover_replacement.py |
| `export_rollover` | `start_replacement_rollover` | `replacement_execution` | services/rollover_replacement_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/rollover_replacement.py |
| `export_rollover` | `verify_replacement_rollover` | `active_settlement_or_probe` | services/rollover_replacement_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/rollover_replacement.py |
| `export_rollover` | `verify_replacements` | `active_settlement_or_probe` | services/rollover_replacement_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/rollover_replacement.py |
| `export_rollover` | `verify_rollover` | `active_settlement_or_probe` | services/rollover_replacement_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/rollover_replacement.py |
| `queue_admission` | `close_withdrawn_read` | `settlement_candidate` | services/queue_admission_recovery.py |
| `queue_admission` | `withdraw_health_probe` | `existing_automatic` | services/queue_admission_recovery.py |
| `queue_admission` | `withdraw_queued` | `business_disposition` | services/queue_admission_recovery.py |
| `unowned_sql_hold` | `clear_unowned_hold` | `unknown_outcome_disposition` | services/unowned_sql_hold_recovery.py |
| `player_report` | `abandon_capture` | `business_disposition` | services/player_report_recovery_service.py; services/all_kvk_capture_recovery_service.py; services/import_recovery_service.py |
| `player_report` | `cancel_report` | `settlement_candidate` | services/player_report_recovery_service.py; services/all_kvk_capture_recovery_service.py; services/import_recovery_service.py |
| `player_report` | `complete_cache_only` | `existing_automatic` | services/player_report_recovery_service.py; services/all_kvk_capture_recovery_service.py; services/import_recovery_service.py |
| `player_report` | `queue_capture` | `continue_original_intent_candidate` | services/player_report_recovery_service.py; services/all_kvk_capture_recovery_service.py; services/import_recovery_service.py |
| `player_report` | `resume_capture` | `continue_original_intent_candidate` | services/player_report_recovery_service.py; services/all_kvk_capture_recovery_service.py; services/import_recovery_service.py |
| `all_kvk_capture` | `abandon_capture` | `business_disposition` | services/all_kvk_capture_recovery_service.py; services/import_recovery_service.py |
| `all_kvk_capture` | `queue_capture` | `continue_original_intent_candidate` | services/all_kvk_capture_recovery_service.py; services/import_recovery_service.py |
| `all_kvk_capture` | `resume_capture` | `continue_original_intent_candidate` | services/all_kvk_capture_recovery_service.py; services/import_recovery_service.py |
| `export_job` | `activate_replacements` | `destination_choice` | services/export_replacement_recovery_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/legacy_export_closeout.py; services/failed_export_closeout.py |
| `export_job` | `allow_next_export` | `business_disposition` | services/export_replacement_recovery_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/legacy_export_closeout.py; services/failed_export_closeout.py |
| `export_job` | `choose_replacements` | `destination_choice` | services/export_replacement_recovery_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/legacy_export_closeout.py; services/failed_export_closeout.py |
| `export_job` | `discard_replacement_check` | `discard_read_decision` | services/export_replacement_recovery_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/legacy_export_closeout.py; services/failed_export_closeout.py |
| `export_job` | `finish_replacement_check` | `automatic_receipt_candidate` | services/export_replacement_recovery_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/legacy_export_closeout.py; services/failed_export_closeout.py |
| `export_job` | `isolate_targets` | `destination_choice` | services/export_replacement_recovery_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/legacy_export_closeout.py; services/failed_export_closeout.py |
| `export_job` | `publish_replacement` | `replacement_execution` | services/export_replacement_recovery_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/legacy_export_closeout.py; services/failed_export_closeout.py |
| `export_job` | `rebuild_damaged` | `retry_policy` | services/export_replacement_recovery_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/legacy_export_closeout.py; services/failed_export_closeout.py |
| `export_job` | `retire_failed_export` | `business_disposition` | services/export_replacement_recovery_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/legacy_export_closeout.py; services/failed_export_closeout.py |
| `export_job` | `retry_absent` | `retry_policy` | services/export_replacement_recovery_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/legacy_export_closeout.py; services/failed_export_closeout.py |
| `export_job` | `retry_unstarted` | `retry_policy` | services/export_replacement_recovery_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/legacy_export_closeout.py; services/failed_export_closeout.py |
| `export_job` | `skip_unstarted` | `business_disposition` | services/export_replacement_recovery_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/legacy_export_closeout.py; services/failed_export_closeout.py |
| `export_job` | `verify_publication` | `active_settlement_or_probe` | services/export_replacement_recovery_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/legacy_export_closeout.py; services/failed_export_closeout.py |
| `export_job` | `verify_replacements` | `active_settlement_or_probe` | services/export_replacement_recovery_adapter.py; services/export_recovery_service.py; services/export_replacement_workflow.py; services/legacy_export_closeout.py; services/failed_export_closeout.py |
| `private_evidence` | `attest_containment` | `new_attestation` | services/export_evidence_recovery.py |
| `private_evidence` | `attest_registration` | `new_attestation` | services/export_evidence_recovery.py |
| `private_evidence` | `protect_evidence` | `automatic_copy_candidate` | services/export_evidence_recovery.py |
| `private_evidence` | `restore_evidence` | `automatic_copy_candidate` | services/export_evidence_recovery.py |
| `configuration_read` | `contain_read` | `discard_read_decision` | services/config_read_recovery_adapter.py |
| `configuration_read` | `release_read` | `existing_automatic` | services/config_read_recovery_adapter.py |
| `producer_refusal` | `cancel_saved_stage` | `business_disposition` | services/producer_refusal_recovery.py |
| `producer_refusal` | `close_unstarted_admission` | `settlement_candidate` | services/producer_refusal_recovery.py |
| `producer_refusal` | `resume_current_registration` | `fresh_work_policy` | services/producer_refusal_recovery.py |
| `producer_refusal` | `resume_sql_stage` | `continue_original_intent_candidate` | services/producer_refusal_recovery.py |
| `configuration_producer` | `abandon_capture` | `business_disposition` | services/configuration_producer_recovery.py; services/player_report_recovery_service.py; services/import_recovery_service.py |
| `configuration_producer` | `cancel_configuration` | `settlement_candidate` | services/configuration_producer_recovery.py; services/player_report_recovery_service.py; services/import_recovery_service.py |
| `configuration_producer` | `complete_configuration_only` | `existing_automatic` | services/configuration_producer_recovery.py; services/player_report_recovery_service.py; services/import_recovery_service.py |
| `configuration_producer` | `queue_capture` | `continue_original_intent_candidate` | services/configuration_producer_recovery.py; services/player_report_recovery_service.py; services/import_recovery_service.py |
| `configuration_producer` | `resume_capture` | `continue_original_intent_candidate` | services/configuration_producer_recovery.py; services/player_report_recovery_service.py; services/import_recovery_service.py |
| `configuration_continuation` | `continue_configuration_export` | `fresh_work_policy` | services/configuration_continuation.py |
| `configuration_continuation` | `keep_prior` | `business_disposition` | services/configuration_continuation.py |
| `configuration_continuation` | `retry_configuration` | `fresh_work_policy` | services/configuration_continuation.py |
| `configuration_read_continuation` | `continue_configuration_export` | `fresh_work_policy` | services/configuration_read_continuation.py; services/configuration_continuation.py |
| `configuration_read_continuation` | `keep_prior` | `business_disposition` | services/configuration_read_continuation.py; services/configuration_continuation.py |
| `configuration_read_continuation` | `retry_configuration` | `fresh_work_policy` | services/configuration_read_continuation.py; services/configuration_continuation.py |
| `player_report_continuation` | `keep_prior` | `business_disposition` | services/player_report_continuation.py |
| `player_report_continuation` | `refresh_cache` | `fresh_work_policy` | services/player_report_continuation.py |
| `player_report_continuation` | `refresh_report` | `fresh_work_policy` | services/player_report_continuation.py |
| `stats_report_continuation` | `continue_reports` | `continue_original_intent_candidate` | services/stats_report_continuation.py |
| `processing_pipeline` | `continue_stage` | `fresh_work_policy` | services/processing_pipeline_recovery.py |
| `processing_pipeline` | `retain_stage` | `business_disposition` | services/processing_pipeline_recovery.py |
| `processing_pipeline` | `verify_stage` | `automatic_receipt_candidate` | services/processing_pipeline_recovery.py |
| `unreceipted_producer` | `retain_unknown` | `unknown_outcome_disposition` | services/unreceipted_producer_recovery.py |
| `legacy_configuration_continuation` | `keep_prior` | `business_disposition` | services/legacy_configuration_continuation.py; services/configuration_continuation.py |
| `legacy_configuration_continuation` | `retry_configuration` | `fresh_work_policy` | services/legacy_configuration_continuation.py; services/configuration_continuation.py |
| `stats_import` | `abandon_capture` | `business_disposition` | services/import_recovery_service.py; services/historical_import_recovery_service.py |
| `stats_import` | `queue_capture` | `continue_original_intent_candidate` | services/import_recovery_service.py; services/historical_import_recovery_service.py |
| `stats_import` | `release_failure` | `existing_outcome_worker` | services/import_recovery_service.py; services/historical_import_recovery_service.py; services/stats_import_outcome_service.py; services/processing_outcome_worker.py |
| `stats_import` | `resume_capture` | `continue_original_intent_candidate` | services/import_recovery_service.py; services/historical_import_recovery_service.py |
| `stats_import` | `retire_historical_export` | `business_disposition` | services/import_recovery_service.py; services/historical_import_recovery_service.py |
| `stats_import` | `supersede_partial` | `business_disposition` | services/import_recovery_service.py; services/historical_import_recovery_service.py |

## Operations outside the individual-action policy

- `configuration_attempt`, `evidence_batch`, `historical_batch` and `recovery_overview` have no individual policy actions. That does not mean their associated workflows are passive.
- Evidence-group approval and historical-group approval are separate service operations. Group review can refresh each member (up to 25) and reconcile accepted actions. A protected-copy repair policy may remove repetitive approvals; retirement of original business work still needs a meaningful disposition.
- Replacement choices and inherited producer actions are included through their adapter chains. Fresh destination selection, registration activation and new provider publication are distinct from finishing a retained verification receipt.
- Generic Recheck is an orchestration operation rather than a member of this action policy. It can reconcile previously accepted work. Separate passive presentation from that execution and make routine convergence independent of a click.
- Report inspection has a separate classification gap (F27 in the tracing report): writer contention can be recorded as a failed check even though the next ordinary check can succeed. Correctly waiting for that observation is distinct from authorizing `continue_reports`; preserve genuine input/configuration conflicts and exact committed-stage receipts.
- F28 adds a terminal-projection case: once the exact saved-stage cancellation receipt is validated, linked import views should converge automatically to cancelled-before-SQL. The original cancellation remains a business decision; rechecking or asking for another cancellation after that receipt exists adds no value. Missing receipts alone are insufficient.
- Report 66 and the later screenshots show no offered `allow_next_export` action because exact closure checks fail. Preserve those ownership/result checks, but expose the precise failed condition. The same generic explanation covers several predicates and cannot establish that a physical writer is still running. Clearing an unrelated stale incident would not remove the account restriction.

## Evidence and remaining work

The offline census parses source without importing the application. It asserts that every distinct policy action has exactly one reviewed classification and that the referenced source files exist. The private generator, policy summary and detailed inventories are retained under `.codex_artifacts/startup-import-export-review-20261102`. Markdown is the durable review artifact because repository ignore rules exclude generated CSV files.

Nested replacement, rollover, producer inheritance, batch approval and existing outcome-worker paths were inspected during the second pass. State-specific eligibility, original-intent continuity, native concurrency and safe report-field projections remain design/qualification work; this table does not make any new automation safe by itself.
