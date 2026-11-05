# Startup, import and export reliability: separate final outlier sweep

> **Current programme checkpoint - 4 November 2026 (E68/E69):** P01.2a is deployed and accepted for its declared reporting/evidence scope at private `67c4e12a8ecf0c25280770860480ac65a6826602`.
> Read the [P01.2a closeout](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Closeout%20-%202026-11-04.md) for delivered corrections, evidence limits, learnings and remaining owners; [P01.2b handover](archive/Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Handover%20and%20Scope%20-%202026-11-04.md) is the next review/design task.
> Earlier dated statuses, holds and next-action instructions in this document are retained history and are superseded for current scheduling. P01.3-P01.6/P02-P05 and exact incident recovery remain open; no replay of accepted work.

Updated: 2 November 2026. Analysis and evidence only; no application or SQL change.
See the [tracker](Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md)
and [tracing](Startup%20Import%20Export%20Reliability%20-%20Tracing%20-%202026-11-02.md).

## Boundary and reconciliation

This is the separate M04a/A12 challenge requested after the main first pass. The
fresh tracked-file inventory contains 2,486 Python/SQL/PowerShell/batch files across
both repositories, including 868 test/validation fixtures. It found 680 files with
ownership, execution, outcome, provider, dynamic-call or retry signals. Of those,
322 were not literal path entries in the main coverage document. All 322 now have
an explicit scoped or boundary disposition below; none is silently discarded.
These counts use a wider denominator than the earlier Python/canonical-SQL census.
They are not counts of defects, unique execution paths or percentage coverage.

Pins: Bot `a025adb7a69aac321fd62794b871ed5903338f44`; SQL
`7e91989f619deb46836194c7e705b0a9eb2ebe11`. The historical 371-row ledger remains
separate and unchanged. Source hashes, AST import edges, signal lines and disposition
rows are retained privately in `startup-import-export-review-20261102/final-sweep`.
Python parsing reported zero failures. SQL dynamic-DDL bootstrap wrappers, ordinary
Python `execute` methods and prose mentioning a checkpoint were challenged as false
equivalences, not interpreted as execution locks.

## Independent cross-checks and results

- Reversed the trace from account/event/closure SQL guards to authority, private
  evidence store, closeout verifier and UI. The supplied 10:58:15 UTC read confirms
  the exact missing terminal event for old-export request 177. F02 is extended with
  the frozen-stream and stale-closure recovery gap; this is not a new failure count.
- Exercised the actual Python authority and verifier methods with inert substitutes:
  saved response before failed SQL append, terminated child before refused closure,
  stale cached seal after journal change, unknown-mutation rejection, and a normal
  success/closure control. SQL admission/51700 is modeled, not executed natively.
- Followed fresh dynamic-import hits through `file_utils.py`, `maintenance_worker.py`,
  `scripts/callable_worker.py`, protected updater/recovery loaders and the history-view
  compatibility shim. The callable launcher has no other tracked Python caller in
  the reverse search; this is not proof that no external operator invokes it.
- Rechecked zero-wait guards in snapshot/capture/receipt/refusal/backlog/unowned-hold
  paths. They have different custody/observation purposes and remain F03/F09/F10/G04
  design cases, not a blanket timeout increase. The 900-second local producer queue
  waits before taking a SQL connection and does not replace durable ownership.
- Expanded the SQL root challenge to the legacy `UPDATE_ALL` chain. F31 records its
  Rally child deleting an input before the parent commits and swallowing errors.
  `IMPORT_STAGING_PROC` retains its no-ambient-transaction guard and digest-bound core;
  legacy Rally must not be assumed to inherit that newer custody contract.
- Reviewed SQL Agent-style health/backup/cleanup procedures and deployment scripts.
  `CaptureLogHealth` inserts samples; KVK cleanup can delete rows when DryRun is off;
  neither is passive observation. Schema-export branch retention is Git maintenance,
  not provider account cleanup. Historical exact-case repairs remain non-reusable.
- No CREATE TRIGGER definition was found in the tracked canonical SQL inventory.
  That is a source boundary, not evidence that live SQL has no triggers, Agent jobs,
  synonyms or externally scheduled/manual calls. Native qualification must check
  actual installed bindings before claiming all live execution is covered.
- Preserved counterexamples: publication detail metrics catch collection/log failures;
  the queued-upload route owns the queue item before best-effort projection; owned
  work drains on cancellation; the accepted MGE consumers retain that contract.
  A separate fault check adds F32: the shared timing logger can raise before owned
  work starts or after the timed body completes. This is an injected sink failure,
  not evidence of installed-handler failure or a reason to reopen MGE domain acceptance.

## Disposition groups

Each group states the shared edge actually reviewed or the reason for the boundary.
S05 enablement, cleanup retention, native contention and protected evidence qualification
remain explicit design/operational obligations. A disposition is not an approval to
remove a guard, execute a historical repair, or declare a whole module defect-free.

| Group | Rows | Disposition |
|---|---|---|
| S01 | 10 | Authority/private evidence and recovery: F02/F03/F10/F12; exact event, child, closure and owner proof. Saved-evidence repair is not result settlement. |
| S02 | 6 | Producer/recovery routing and admission: F06/F09/F10/F13/F28. Shared adapters retain state-specific actions; local fair scheduling waits before SQL. |
| S03 | 23 | SQL dependency of the existing twelve import/report roots: retain atomic business receipts; F18/F21/F22 cover in-transaction maintenance and diagnostics. |
| S04 | 54 | SQL read/view/function definition: deployment bootstrap is a dynamic-DDL signal, not a runtime retry. Ordinary read lock/cost qualification remains A02/A04. |
| S05 | 15 | Legacy/manual SQL entrypoint: F31 for UPDATE_ALL/Rally; other legacy calculations require enablement inventory before retirement. No claim of live scheduled use. |
| S06 | 11 | SQL audit/backup/cleanup/support: F17/F18/G04; diagnostic writes and cleanup are active work, not passive observation. Protect unresolved evidence and schedule separately. |
| S07 | 91 | Historical migration/rollback/amendment: installation or one-off execution, not an additional scheduled producer. Canonical definitions govern current analysis; do not replay. |
| S08 | 48 | Rehearsal/performance/manual recovery tooling: explicit operator invocation and retained exact-case bindings; no execution in this sweep and no reuse for the current export. |
| S09 | 6 | SQL deployment/schema-export tooling: schema Git branch retention and release receipts differ from Sheets delivery/account settlement; live scheduler bindings remain qualification. |
| S10 | 7 | Accepted MGE interaction/lifecycle consumer: shared drain/ownership included; domain mutation/finalisation and historical-board contracts remain accepted P1 boundaries. |
| S11 | 23 | Independent UI/render/metadata/subscription/reminder consumer: actual dependency uses mapped shared helpers; no export settlement authority. Domain redesign remains outside this phase. |
| S12 | 5 | Shared drain/protocol/timing helpers: physical work is drained; protocol validates identity. Publication detail metrics catch logging faults, but core timing does not (F32). No independent retry or settlement authority. |
| S13 | 2 | Queued/Honor upload front door: F17/F30; queue ownership precedes UI projection, backup-trigger failures are caught. Downstream staging/callback outcomes remain distinct. |
| S14 | 3 | Runtime executable wrapper/dynamic import: follow installed module or supplied callable to existing worker/authority boundary; no separate blind retry or release authority inferred. |
| S15 | 11 | Diagnostic/validation/source-update script: explicit invocation, fixed host/custody or test entrypoint; read, deploy, mutation and provider effects are not interchangeable. |
| S16 | 7 | KVK publication/output-pool/read-model: existing exact-operation uncertainty and output ownership remain; derived checkpoints are data projections, not SQL commit receipts. |

## Additional paths checked without relying on signal matches

The closure reverse trace also inspected `services/stranded_export_recovery.py`,
`core/stranded_export_host.py`, `core/export_child_lifecycle.py`,
`services/export_snapshot_store.py`, `services/legacy_export_closeout.py` and the
authority/provider startup entrypoints. The stranded-writer procedure expects an
eligible running/open unblocked snapshot; it is not a repair for the current
uncertain/frozen/blocked job. Read-only containment is not mutation containment.
Startup and scheduled route registration remain tied to the main pass's entrypoint
map; no exclusion was made solely because this sweep produced zero lexical hits.

## New candidate ledger

The focused baseline run passed 300 authority/reconciliation/legacy-closeout tests.
Closure and timing fault experiments use inert substitutes; no native SQL, provider
or production process action was performed. Documentation gates and their precise
skip/fallback reasons are recorded in the tracker.

The line is a navigation signal at the pinned source, not the complete review range.
Paths in the SQL repository resolve under `C:/K98-bot-SQL-Server`; Bot paths resolve
under `C:/discord_file_downloader`. The fresh manifest retains exact file hashes.

| Repository | Path | Group | Signal line |
|---|---|---|---|
| bot | `account_picker.py` | S11 | 176 |
| bot | `admin_helpers.py` | S11 | 221 |
| bot | `ark/db_reminder_prefs.py` | S11 | 37 |
| bot | `commands/subscriptions_cmds.py` | S11 | 287 |
| bot | `core/export_execution_host.py` | S01 | 726 |
| bot | `core/operation_timing.py` | S12 | 1 |
| bot | `core/owned_work.py` | S12 | 3 |
| bot | `input_helpers.py` | S11 | 57 |
| bot | `kvk/models/new_source_reader.py` | S16 | 128 |
| bot | `kvk/services/new_source_checkpoint_service.py` | S16 | 80 |
| bot | `kvk/services/new_source_cumulative.py` | S16 | 68 |
| bot | `kvk/services/new_source_delivery_service.py` | S16 | 22 |
| bot | `kvk/services/new_source_reader_support.py` | S16 | 43 |
| bot | `kvk/services/source_output_pool_service.py` | S16 | 153 |
| bot | `kvk_history_view.py` | S11 | 3 |
| bot | `leadership_player_review/renderer.py` | S11 | 397 |
| bot | `mge/dal/mge_signup_mutation_dal.py` | S10 | 50 |
| bot | `mge/mge_embed_manager.py` | S10 | 23 |
| bot | `mge/mge_roster_execution.py` | S10 | 15 |
| bot | `mge/mge_scheduler.py` | S10 | 10 |
| bot | `scripts/Invoke-Phase51ImmutableHandoffEvidence.ps1` | S15 | 325 |
| bot | `scripts/K98-SourceUpdate.ps1` | S15 | 599 |
| bot | `scripts/Read-K98AuthorityDiagnostics.ps1` | S15 | 13 |
| bot | `scripts/Reset-Phase51FailedEvidence.ps1` | S15 | 125 |
| bot | `scripts/benchmark_mge_refresh.py` | S15 | 223 |
| bot | `scripts/callable_worker.py` | S14 | 84 |
| bot | `scripts/collect_diagnostics.py` | S15 | 218 |
| bot | `scripts/install_s11_source_boundary.ps1` | S15 | 85 |
| bot | `scripts/processing_notifications.py` | S15 | 22 |
| bot | `scripts/recover_stranded_export.py` | S15 | 60 |
| bot | `scripts/run_export_provider_child.py` | S14 | 3 |
| bot | `scripts/run_export_startup_issuer.py` | S14 | 177 |
| bot | `scripts/smoke_imports.py` | S15 | 82 |
| bot | `scripts/validate_command_registration.py` | S15 | 21 |
| bot | `services/configuration_attempt_dal.py` | S02 | 16 |
| bot | `services/configuration_producer_recovery.py` | S02 | 82 |
| bot | `services/export_evidence_storage.py` | S01 | 97 |
| bot | `services/export_execution_protocol.py` | S12 | 88 |
| bot | `services/export_publication_metrics.py` | S12 | 3 |
| bot | `services/export_reconciliation_service.py` | S01 | 458 |
| bot | `services/export_replacement_delivery.py` | S01 | 115 |
| bot | `services/export_replacement_publication.py` | S01 | 184 |
| bot | `services/export_retirement_evidence.py` | S01 | 142 |
| bot | `services/export_retirement_recovery_evidence.py` | S01 | 177 |
| bot | `services/export_rollover_evidence.py` | S01 | 1 |
| bot | `services/export_sql_direct_permissions.py` | S01 | 160 |
| bot | `services/import_capture_recovery_service.py` | S02 | 285 |
| bot | `services/kvk_history_service.py` | S16 | 106 |
| bot | `services/player_report_continuation.py` | S02 | 55 |
| bot | `services/producer_admission.py` | S02 | 44 |
| bot | `services/recovery_failure_diagnostics.py` | S02 | 27 |
| bot | `services/rollover_replacement.py` | S01 | 150 |
| bot | `services/vision_client.py` | S11 | 276 |
| bot | `sql/dbo.sp_Build_Prekvk_And_Honor_Rankings.StoredProcedure.sql` | S07 | 7 |
| bot | `sql/kvk_all_phase10_recompute_correctness.sql` | S07 | 20 |
| bot | `sql/kvk_all_phase11_acclaim_output_contract.sql` | S07 | 181 |
| bot | `sql/kvk_all_phase2_full_data_capacity.sql` | S07 | 160 |
| bot | `sql/kvk_all_phase4_recompute_modernisation.sql` | S07 | 336 |
| bot | `sql/kvk_all_phase5_export_contract_decoupling.sql` | S07 | 26 |
| bot | `sql/kvk_all_phase8_ingest_retention.sql` | S07 | 171 |
| bot | `stats_alerts/delivery_outcomes.py` | S12 | 98 |
| bot | `stats_alerts/diagnostics.py` | S11 | 67 |
| bot | `stats_alerts/formatters.py` | S11 | 130 |
| bot | `stats_alerts/kvk_diagnostics.py` | S11 | 30 |
| bot | `stats_alerts/kvk_meta.py` | S11 | 19 |
| bot | `subscription_tracker.py` | S11 | 381 |
| bot | `ui/views/mge_admin_view.py` | S10 | 9 |
| bot | `ui/views/mge_signup_modal.py` | S10 | 11 |
| bot | `ui/views/mge_simplified_signup_form_view.py` | S10 | 28 |
| bot | `ui/views/stats_views.py` | S11 | 413 |
| bot | `upload_routes/fallback_queue_route.py` | S13 | 89 |
| bot | `upload_routes/honor_route.py` | S13 | 248 |
| sql | `deploy/Deploy-SqlMigration.ps1` | S09 | 342 |
| sql | `deploy/Measure-Phase81LeadershipPerformance.sql` | S09 | 15 |
| sql | `deploy/NightlyExportRetention.ps1` | S09 | 111 |
| sql | `deploy/SqlDeploy.ModuleRelease.ps1` | S09 | 83 |
| sql | `deploy/SqlDeploy.RecoveryRelease.ps1` | S09 | 181 |
| sql | `deploy/StatsImportOutcome.Source.ps1` | S09 | 25 |
| sql | `deploy/amendments/20261012_aggregate_row_permissions.sql` | S07 | 40 |
| sql | `deploy/amendments/20261014_reader_history_permissions.sql` | S07 | 35 |
| sql | `deploy/recovery/activity_snapshot_completion_20261027/reconcile.sql` | S08 | 8 |
| sql | `deploy/recovery/s11_manual_stats_20261008/settle.sql` | S08 | 7 |
| sql | `deploy/recovery/s11_withdraw_405_20261008/build_withdrawal.py` | S08 | 18 |
| sql | `deploy/recovery/s11_withdraw_405_20261008/withdraw.sql` | S08 | 5 |
| sql | `migrations/20260607_001_preserve_stats_for_upload_last_refresh_time.sql` | S07 | 96 |
| sql | `migrations/20260615_001_add_conduct_reporting_field.sql` | S07 | 116 |
| sql | `migrations/20260616_001_fix_excel_dashboard_explicit_union.sql` | S07 | 3 |
| sql | `migrations/20260628_001_import_schema_resilience_and_shield_time.sql` | S07 | 3 |
| sql | `migrations/20260628_002_unicode_fallback_import_raw_staging.sql` | S07 | 120 |
| sql | `migrations/20260709_001_add_update_all2_audit_outputs.sql` | S07 | 26 |
| sql | `migrations/20260709_001_add_vote_survey_admin_delete.sql` | S07 | 36 |
| sql | `migrations/20260719_001_add_rally_daily_completion_contract.sql` | S07 | 22 |
| sql | `migrations/20260719_002_add_alliance_activity_completion_evidence.sql` | S07 | 147 |
| sql | `migrations/20260719_003_add_governor_name_history_observations.sql` | S07 | 263 |
| sql | `migrations/20260719_004_add_kvk_final_report_header.sql` | S07 | 3 |
| sql | `migrations/20260719_005_add_leadership_player_review_audit.sql` | S07 | 163 |
| sql | `migrations/20260719_007_wire_governor_name_history_post_scan.sql` | S07 | 99 |
| sql | `migrations/20260721_001_fix_leadership_audit_temp_collation.sql` | S07 | 52 |
| sql | `migrations/20260721_002_backfill_leadership_activity_completion.sql` | S07 | 147 |
| sql | `migrations/20260721_003_allow_partial_leadership_activity_ranking.sql` | S07 | 132 |
| sql | `migrations/20260721_004_return_complete_leadership_alias_history.sql` | S07 | 88 |
| sql | `migrations/20260725_001_kingdomscandata4_shadow_type_remediation.sql` | S07 | 22 |
| sql | `migrations/20260726_001_phase3_import_concurrency_and_direct_type_alignment.sql` | S07 | 46 |
| sql | `migrations/20260727_000_retire_vAllianceActivity_WeeklyCumulative.sql` | S07 | 46 |
| sql | `migrations/20260727_001_phase4_view_type_alignment.sql` | S07 | 46 |
| sql | `migrations/20260728_001_phase5_immutable_import_file_handoff.sql` | S07 | 48 |
| sql | `migrations/20260816_001_phase5_1_claim_acl_hardening.sql` | S07 | 25 |
| sql | `migrations/20260825_001_kvk_target_publication_provenance.sql` | S07 | 41 |
| sql | `migrations/20260826_001_serialize_delta_preprocessing.sql` | S07 | 53 |
| sql | `migrations/20260827_001_standardize_exempt_from_stats_governor_id_bigint.sql` | S07 | 41 |
| sql | `migrations/20260827_002_align_kvk_healed_window_and_stats_refresh_provenance.sql` | S07 | 37 |
| sql | `migrations/20260910_001_kvk_source_publication_state.sql` | S07 | 103 |
| sql | `migrations/20260912_001_kvk_season_complete_updates.sql` | S07 | 14 |
| sql | `migrations/20260913_001_kvk_source_update_no_fight_context.sql` | S07 | 44 |
| sql | `migrations/20260914_001_shared_export_coordination.sql` | S07 | 35 |
| sql | `migrations/20260914_002_legacy_export_preparation.sql` | S07 | 31 |
| sql | `migrations/20260915_001_kvk_output_pool_rollover.sql` | S07 | 36 |
| sql | `migrations/20260915_002_kvk_output_operation_ownership.sql` | S07 | 14 |
| sql | `migrations/20260924_001_export_execution_evidence.sql` | S07 | 14 |
| sql | `migrations/20260924_002_export_legacy_module_permissions.sql` | S07 | 14 |
| sql | `migrations/20260929_001_manual_export_registration.sql` | S07 | 25 |
| sql | `migrations/20260929_002_manual_public_viewer_policy.sql` | S07 | 26 |
| sql | `migrations/20261001_001_legacy_export_preparation_installation.sql` | S07 | 38 |
| sql | `migrations/20261001_002_kvk_output_pool_installation.sql` | S07 | 41 |
| sql | `migrations/20261001_003_kvk_output_operation_installation.sql` | S07 | 19 |
| sql | `migrations/20261001_004_export_execution_evidence_installation.sql` | S07 | 19 |
| sql | `migrations/20261001_005_manual_export_registration_installation.sql` | S07 | 29 |
| sql | `migrations/20261001_006_manual_public_viewer_installation.sql` | S07 | 30 |
| sql | `migrations/20261001_007_manual_file_id_characters.sql` | S07 | 20 |
| sql | `migrations/20261001_008_manual_file_id_constraint.sql` | S07 | 17 |
| sql | `migrations/20261001_009_manual_resource_membership_order.sql` | S07 | 20 |
| sql | `migrations/20261001_010_reconciliation_file_id_characters.sql` | S07 | 20 |
| sql | `migrations/20261003_001_export_legacy_direct_permissions.sql` | S07 | 16 |
| sql | `migrations/20261006_001_source_output_file_id_constraint.sql` | S07 | 18 |
| sql | `migrations/20261006_002_initial_output_slot_disposition.sql` | S07 | 21 |
| sql | `migrations/20261007_001_legacy_export_per_file_audience.sql` | S07 | 18 |
| sql | `migrations/20261008_001_sql_auth_import_file_visibility.sql` | S07 | 28 |
| sql | `migrations/20261009_001_stats_import_outcomes.sql` | S07 | 23 |
| sql | `migrations/20261010_001_stats_import_outcomes_collation.sql` | S07 | 26 |
| sql | `migrations/20261010_002_stats_import_outcomes_encoding.sql` | S07 | 29 |
| sql | `migrations/20261010_003_stats_import_outcome_postimages.sql` | S07 | 20 |
| sql | `migrations/20261013_001_kvk_export_history.sql` | S07 | 14 |
| sql | `migrations/20261015_001_failed_read_history.sql` | S07 | 21 |
| sql | `migrations/20261015_002_guided_recovery.sql` | S07 | 14 |
| sql | `migrations/20261015_003_read_prefix_history.sql` | S07 | 21 |
| sql | `migrations/20261015_004_failed_publication_probe.sql` | S07 | 3 |
| sql | `migrations/20261015_005_read_prefix_closure.sql` | S07 | 22 |
| sql | `migrations/20261015_006_failed_probe_request_events.sql` | S07 | 22 |
| sql | `migrations/20261015_007_read_dispatch_containment.sql` | S07 | 19 |
| sql | `migrations/20261015_008_export_target_containment.sql` | S07 | 25 |
| sql | `migrations/20261015_009_guided_export_replacement.sql` | S07 | 25 |
| sql | `migrations/20261015_010_configuration_replacement.sql` | S07 | 24 |
| sql | `migrations/20261016_001_rollover_replacement.sql` | S07 | 25 |
| sql | `migrations/20261016_002_atomic_configuration_publication.sql` | S07 | 3 |
| sql | `migrations/20261022_001_p0_pipeline_receipts.sql` | S07 | 24 |
| sql | `migrations/20261022_003_stats_report_recovery_boundary.sql` | S07 | 23 |
| sql | `migrations/20261023_001_legacy_export_closeout.sql` | S07 | 22 |
| sql | `migrations/rollback/20260725_001_kingdomscandata4_shadow_type_remediation_rollback.sql` | S07 | 17 |
| sql | `migrations/rollback/20260726_001_phase3_import_concurrency_and_direct_type_alignment_rollback.sql` | S07 | 25 |
| sql | `migrations/rollback/20260727_001_phase4_view_type_alignment_rollback.sql` | S07 | 30 |
| sql | `migrations/rollback/20260728_001_phase5_immutable_import_file_handoff_rollback.sql` | S07 | 31 |
| sql | `migrations/rollback/20260816_001_phase5_1_claim_acl_hardening_rollback.sql` | S07 | 26 |
| sql | `migrations/rollback/20260827_001_standardize_exempt_from_stats_governor_id_bigint_rollback.sql` | S07 | 20 |
| sql | `migrations/rollback/20260827_002_align_kvk_healed_window_and_stats_refresh_provenance_rollback.sql` | S07 | 18 |
| sql | `migrations/rollback/20260924_002_export_legacy_module_permissions_rollback.sql` | S07 | 142 |
| sql | `migrations/rollback/_rollback_template.sql` | S07 | 23 |
| sql | `performance_remediation/kingdomscandata4/phase1/01_collect_environment_and_dependencies.sql` | S08 | 9 |
| sql | `performance_remediation/kingdomscandata4/phase1/02_validate_candidate_conversions.sql` | S08 | 9 |
| sql | `performance_remediation/kingdomscandata4/phase1/03_collect_query_store_baseline.sql` | S08 | 9 |
| sql | `performance_remediation/kingdomscandata4/phase1/04_run_controlled_baseline.sql` | S08 | 20 |
| sql | `performance_remediation/kingdomscandata4/phase1/05_collect_sql_agent_and_serialization.sql` | S08 | 13 |
| sql | `performance_remediation/kingdomscandata4/phase1/06_collect_sql_agent_full_job_inventory.sql` | S08 | 14 |
| sql | `performance_remediation/kingdomscandata4/phase1/Collect-ExternalSerializationEvidence.ps1` | S08 | 416 |
| sql | `performance_remediation/kingdomscandata4/phase1/migration_rehearsal/01_collect_preflight.sql` | S08 | 15 |
| sql | `performance_remediation/kingdomscandata4/phase1/migration_rehearsal/02_forward_shadow_rehearsal.sql` | S08 | 18 |
| sql | `performance_remediation/kingdomscandata4/phase1/migration_rehearsal/03_rollback_shadow_rehearsal.sql` | S08 | 16 |
| sql | `performance_remediation/kingdomscandata4/phase1/update_all2_rehearsal/05_apply_update_all2_test_path_override.sql` | S08 | 10 |
| sql | `performance_remediation/kingdomscandata4/phase1/update_all2_rehearsal/06_create_update_all2_rehearsal_snapshot.sql` | S08 | 88 |
| sql | `performance_remediation/kingdomscandata4/phase1/update_all2_rehearsal/07_reset_update_all2_rehearsal.sql` | S08 | 133 |
| sql | `performance_remediation/kingdomscandata4/phase1/update_all2_rehearsal/08_drop_update_all2_rehearsal_snapshot.sql` | S08 | 48 |
| sql | `performance_remediation/kingdomscandata4/phase1/update_all2_rehearsal/09_install_update_all2_phase_b_failure.sql` | S08 | 52 |
| sql | `performance_remediation/kingdomscandata4/phase1/update_all2_rehearsal/12_run_update_all2_concurrency_session.sql` | S08 | 51 |
| sql | `performance_remediation/kingdomscandata4/phase1/update_all2_rehearsal/14_create_update_all2_benchmark_seed_backup.sql` | S08 | 3 |
| sql | `performance_remediation/kingdomscandata4/phase1/update_all2_rehearsal/15_restore_update_all2_benchmark_database.sql` | S08 | 72 |
| sql | `performance_remediation/kingdomscandata4/phase2/01_preflight.sql` | S08 | 10 |
| sql | `performance_remediation/kingdomscandata4/phase2/02_verify.sql` | S08 | 16 |
| sql | `performance_remediation/kingdomscandata4/phase2/03_finalize.sql` | S08 | 16 |
| sql | `performance_remediation/kingdomscandata4/phase2/05_restore_preflight_backup_to_recovery.sql` | S08 | 4 |
| sql | `performance_remediation/kingdomscandata4/phase2/06_verify_recovered_preflight_backup.sql` | S08 | 7 |
| sql | `performance_remediation/kingdomscandata4/phase2/07_test_migration_history_retryability.sql` | S08 | 28 |
| sql | `performance_remediation/kingdomscandata4/phase3/05_archive_negative_path.sql` | S08 | 3 |
| sql | `performance_remediation/kingdomscandata4/phase3/06_apply_phase3_test_path_override.sql` | S08 | 9 |
| sql | `performance_remediation/kingdomscandata4/phase3/07_prepare_phase3_fixture.sql` | S08 | 31 |
| sql | `performance_remediation/kingdomscandata4/phase3/09_restage_duplicate_fixture.sql` | S08 | 39 |
| sql | `performance_remediation/kingdomscandata4/phase3/11_prepare_concurrent_fixture.sql` | S08 | 43 |
| sql | `performance_remediation/kingdomscandata4/phase3/15_prepare_concurrent_retry_fixture.sql` | S08 | 6 |
| sql | `performance_remediation/kingdomscandata4/phase3/16_prepare_proven_concurrent_fixture.sql` | S08 | 50 |
| sql | `performance_remediation/kingdomscandata4/phase3/18_run_invalid_and_corrected_retry.sql` | S08 | 3 |
| sql | `performance_remediation/kingdomscandata4/phase3/19_run_direct_and_legacy_entrypoints.sql` | S08 | 50 |
| sql | `performance_remediation/kingdomscandata4/phase3/20_run_controlled_phase_b_failure.sql` | S08 | 44 |
| sql | `performance_remediation/kingdomscandata4/phase3/22_verify_import_lock_authorization.sql` | S08 | 54 |
| sql | `performance_remediation/kingdomscandata4/phase3/23_verify_archive_reconciliation_digest.sql` | S08 | 103 |
| sql | `performance_remediation/kingdomscandata4/phase4/01_preflight.sql` | S08 | 311 |
| sql | `performance_remediation/kingdomscandata4/phase4/03_run_view_benchmarks.sql` | S08 | 126 |
| sql | `performance_remediation/kingdomscandata4/phase5/03_apply_test_path_override.sql` | S08 | 108 |
| sql | `performance_remediation/kingdomscandata4/phase5/04_run_protocol_smokes.sql` | S08 | 87 |
| sql | `performance_remediation/kingdomscandata4/phase5/Invoke-Phase5Rehearsal.ps1` | S08 | 429 |
| sql | `performance_remediation/kingdomscandata4/phase5_1_acl/01_preflight.sql` | S08 | 33 |
| sql | `performance_remediation/kingdomscandata4/release/Invoke-Phase52GuardedFinalizer.ps1` | S08 | 510 |
| sql | `performance_remediation/kingdomscandata4/release/Verify-Phase52CombinedPostPhase51.sql` | S08 | 18 |
| sql | `sql_schema/KVK.sp_KVK_Get_Exports.StoredProcedure.sql` | S05 | 5 |
| sql | `sql_schema/KVK.sp_KVK_Ingest_Cleanup.StoredProcedure.sql` | S06 | 5 |
| sql | `sql_schema/KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql` | S05 | 5 |
| sql | `sql_schema/KVK.vw_FightingDataset.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.CREATE_DASH.StoredProcedure.sql` | S05 | 5 |
| sql | `sql_schema/dbo.CREATE_DASH2.StoredProcedure.sql` | S03 | 427 |
| sql | `sql_schema/dbo.CREATE_THE_AVERAGES.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.CaptureLogHealth.StoredProcedure.sql` | S06 | 5 |
| sql | `sql_schema/dbo.DEADSSUMMARY_PROC.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.GOVERNOR_NAMES_PROC.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.HEALEDSUMMARY_PROC.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.HEALEDSUMMARY_PROC_OPT.StoredProcedure.sql` | S05 | 5 |
| sql | `sql_schema/dbo.IMPORT_STAGING_PROC.StoredProcedure.sql` | S05 | 5 |
| sql | `sql_schema/dbo.KILLPOINTSSUMMARY_PROC.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.KILLSSUMMARY_PROC.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.KT4SUMMARY_PROC.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.KT5SUMMARY_PROC.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.POWERSUMMARY_PROC.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.RANGEDSUMMARY_PROC.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.Refresh_PlayerScanMeta.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.SUMMARY_PROC.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.TARGETS.StoredProcedure.sql` | S05 | 5 |
| sql | `sql_schema/dbo.TARGETS_NEW.StoredProcedure.sql` | S05 | 178 |
| sql | `sql_schema/dbo.TEST.StoredProcedure.sql` | S05 | 5 |
| sql | `sql_schema/dbo.UPDATE_ALL.StoredProcedure.sql` | S05 | 5 |
| sql | `sql_schema/dbo.UPDATE_RALLY_DATA.StoredProcedure.sql` | S05 | 191 |
| sql | `sql_schema/dbo.fn_KVK_Camp_Aggregated.UserDefinedFunction.sql` | S04 | 5 |
| sql | `sql_schema/dbo.fn_KVK_Kingdom_Aggregated.UserDefinedFunction.sql` | S04 | 5 |
| sql | `sql_schema/dbo.fn_KVK_Player_Aggregated.UserDefinedFunction.sql` | S04 | 5 |
| sql | `sql_schema/dbo.fn_PreKvkLatestOverall.UserDefinedFunction.sql` | S04 | 5 |
| sql | `sql_schema/dbo.fn_PreKvkPhaseDelta.UserDefinedFunction.sql` | S04 | 5 |
| sql | `sql_schema/dbo.fn_StatsWindowDeltas.UserDefinedFunction.sql` | S04 | 5 |
| sql | `sql_schema/dbo.fn_StatsWindowDeltas_GovCsv.UserDefinedFunction.sql` | S04 | 5 |
| sql | `sql_schema/dbo.sp_Backfill_PlayerKVKHistory.StoredProcedure.sql` | S05 | 5 |
| sql | `sql_schema/dbo.sp_Build_Prekvk_And_Honor_Rankings.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.sp_Create_Excel_For_Kvk_Indexes.StoredProcedure.sql` | S03 | 68 |
| sql | `sql_schema/dbo.sp_ImportPlayerLocationFromStaging.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.sp_Import_Rally_AllTime.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.sp_Loop_ExcelOutput_ByKVK.StoredProcedure.sql` | S05 | 5 |
| sql | `sql_schema/dbo.sp_Maintain_PlayerKVKHistory.StoredProcedure.sql` | S05 | 50 |
| sql | `sql_schema/dbo.sp_QS_PerfPack.StoredProcedure.sql` | S06 | 5 |
| sql | `sql_schema/dbo.sp_RallyDaily_TopN.StoredProcedure.sql` | S05 | 5 |
| sql | `sql_schema/dbo.sp_Rebuild_RALLY_EXPORT.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.sp_Rebuild_v_PlayerKVK_Last3.StoredProcedure.sql` | S05 | 113 |
| sql | `sql_schema/dbo.sp_RefreshInactiveGovernors.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.sp_Refresh_View_EXCEL_FOR_KVK_All.StoredProcedure.sql` | S03 | 32 |
| sql | `sql_schema/dbo.sp_Registry_GetAllActive.StoredProcedure.sql` | S11 | 5 |
| sql | `sql_schema/dbo.sp_Registry_GetByDiscordID.StoredProcedure.sql` | S11 | 5 |
| sql | `sql_schema/dbo.sp_Registry_GetByGovernorID.StoredProcedure.sql` | S11 | 5 |
| sql | `sql_schema/dbo.sp_Registry_Insert.StoredProcedure.sql` | S11 | 5 |
| sql | `sql_schema/dbo.sp_Registry_SoftDelete.StoredProcedure.sql` | S11 | 5 |
| sql | `sql_schema/dbo.sp_Registry_UpsertFromImport.StoredProcedure.sql` | S11 | 5 |
| sql | `sql_schema/dbo.sp_ReplacePlayerLocationFromStaging.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.sp_Snapshot_PlayerForts.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.sp_Upsert_ProcConfig_From_Staging.StoredProcedure.sql` | S03 | 5 |
| sql | `sql_schema/dbo.usp_ArkRetentionCleanup.StoredProcedure.sql` | S06 | 5 |
| sql | `sql_schema/dbo.usp_ArkSchemaVerify.StoredProcedure.sql` | S11 | 5 |
| sql | `sql_schema/dbo.usp_CleanupLogBackupTriggerQueue.StoredProcedure.sql` | S06 | 5 |
| sql | `sql_schema/dbo.usp_GetPendingLogBackupTriggers.StoredProcedure.sql` | S06 | 5 |
| sql | `sql_schema/dbo.usp_GetPersonalStatsDaily.StoredProcedure.sql` | S11 | 5 |
| sql | `sql_schema/dbo.usp_GetPlayerStatsWindows.StoredProcedure.sql` | S11 | 5 |
| sql | `sql_schema/dbo.usp_ImportAudit_CompleteBatch.StoredProcedure.sql` | S06 | 5 |
| sql | `sql_schema/dbo.usp_ImportAudit_FailBatch.StoredProcedure.sql` | S06 | 5 |
| sql | `sql_schema/dbo.usp_ImportAudit_RecordPhase.StoredProcedure.sql` | S06 | 5 |
| sql | `sql_schema/dbo.usp_ImportAudit_StartBatch.StoredProcedure.sql` | S06 | 5 |
| sql | `sql_schema/dbo.usp_MarkLogBackupTriggerProcessed.StoredProcedure.sql` | S06 | 5 |
| sql | `sql_schema/dbo.vAllianceActivitySnapshots.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vAllianceActivityWeekFinals.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vAllianceActivity_DailyDelta.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vAllianceActivity_WeeklyDelta.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vDailyWithWTD_Activity.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vDaily_Activity.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vDaily_AllianceActivity.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vDaily_Helps.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vDaily_PlayerExport.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vDaily_RSSAssisted.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vDaily_RSSGathered.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vFortsCompleted_WeekToDate.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vWTD_Activity.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vWTD_Helps.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vWTD_RSSAssisted.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vWTD_RSSGathered.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vWeekly_AllianceActivity.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_Active_Players.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_EXCEL_FOR_KVK_All.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_EXCEL_FOR_KVK_Started.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_GovernorNames.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_GovernorNames_Strict.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_KVK_Honor_Latest.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_KVK_Honor_TopLatest.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_KVK_Under50_Last3_WithLatest.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_MGE_SignupReview.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_PlayerAccounts_Migrate.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_PlayerFortsLatest.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_PlayerFortsLatestWithRank.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_PlayerKVK_Last3.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_PlayerLatestStats.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_PlayerProfile.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_PlayerScanMeta.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_PreKvk13_All.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_PreKvk13_Overall.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_PreKvk13_Phase1.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_PreKvk13_Phase2.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_PreKvk13_Phase3.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_RallyDaily_Latest.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_RallyTotals_Current.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.v_TARGETS_FOR_UPLOAD.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vw_All_Governors_Clean.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vw_ArkPlayerReport.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vw_Governor_KVK_Summary_GlobalLatest.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vw_Top3_Week.View.sql` | S04 | 4 |
| sql | `sql_schema/dbo.vw_Top3_Yesterday.View.sql` | S04 | 4 |
