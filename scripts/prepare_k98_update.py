"""Generate source or bounded combined release inputs from the protected seed.

This module never installs source, connects to SQL, or starts processes. The
Windows updater owns acquisition, custody checks and the deployment protocol.
"""

import ast
from collections.abc import Callable
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import runpy
import sys
from typing import Any
from uuid import uuid4

if __name__ == "__main__" and not __package__:
    # The native launcher authenticates installed tools, application source and
    # protected observation before this isolated process starts. Select the
    # installed verifier before core's transitive services imports.
    import argparse

    early = argparse.ArgumentParser(add_help=False)
    early.add_argument("--observation", required=True)
    early.add_argument("--observation-sha256", required=True)
    options, _ = early.parse_known_args()
    if not sys.flags.isolated:
        raise ValueError("Isolated installed preparer required")
    with Path(options.observation).open("rb") as stream:
        observation_raw = stream.read(4 * 1024 * 1024 + 1)
    if (
        not 0 < len(observation_raw) <= 4 * 1024 * 1024
        or hashlib.sha256(observation_raw).hexdigest() != options.observation_sha256
    ):
        raise ValueError("Protected observation identity differs")
    installed = Path(__file__).parent
    with (installed / "update-tool.json").open("rb") as stream:
        manifest_raw = stream.read(65537)
    if len(manifest_raw) > 65536:
        raise ValueError("Installed manifest exceeds bound")
    tool_manifest = json.loads(manifest_raw)
    with (installed / "verify_k98_update_pair.py").open("rb") as stream:
        verifier_raw = stream.read(2 * 1024 * 1024 + 1)
    if (
        len(verifier_raw) > 2 * 1024 * 1024
        or hashlib.sha256(verifier_raw).hexdigest()
        != tool_manifest["files"]["verify_k98_update_pair.py"]
    ):
        raise ValueError("Installed verifier identity differs")
    installed_verifier: dict[str, Any] = {
        "__name__": "installed_verifier",
        "__file__": str(installed / "verify_k98_update_pair.py"),
    }
    exec(compile(verifier_raw, installed_verifier["__file__"], "exec"), installed_verifier)
    observed_bindings = json.loads(observation_raw)["bindings"]
    expected_archive = tool_manifest["files"]["contract_verifier.zip"]
    if observed_bindings["contract_verifier_sha256"] != expected_archive:
        raise ValueError("Observation and installed verifier differ")
    installed_verifier["activate_contract_archive"](
        installed / "contract_verifier.zip", expected_archive, observed_bindings["root"]
    )

from core.export_release_seed import successor_seed
from services.export_execution_protocol import encode

TOOL_SOURCE_PATHS = frozenset(
    "scripts/" + name
    for name in (
        "Update-K98.ps1",
        "K98-SourceUpdate.ps1",
        "Deploy-K98Release.ps1",
        "prepare_k98_update.py",
        "prepare_k98_release.py",
        "verify_k98_update_pair.py",
        "package_k98_update_tool.py",
        "k98_update_transitions.json",
        "p0a_release.py",
        "p0a_release_spec.json",
        "recovery_release_seed.py",
    )
)

RELEASE_DESCRIPTION = "deploy/k98-release.json"
SQL_TOOLS = ("Deploy-SqlMigration.ps1", "SqlDeploy.ModuleRelease.ps1")

DRAINED_ISSUER_TRANSITION_PATHS = frozenset({"scripts/run_export_startup_issuer.py"})
STARTUP_CACHE_COMPLETION_PATHS = frozenset(
    {
        "bot_instance.py",
        "core/startup_diagnostics.py",
        "services/player_stats_startup.py",
    }
)
CONFIGURATION_READ_REQUEST_PATHS = frozenset(
    {
        "services/config_preparation_recovery_service.py",
        "services/configuration_producer_recovery.py",
        "services/configuration_read_continuation_dal.py",
    }
)
CONFIGURATION_INTENT_REPLAY_PATHS = frozenset(
    {
        "services/configuration_continuation.py",
        "services/configuration_continuation_dal.py",
        "services/configuration_read_continuation_dal.py",
        "services/producer_recovery_intent.py",
        "services/export_execution_dal.py",
        "services/export_reconciliation_service.py",
    }
)
PUBLICATION_TIMING_PATHS = frozenset(
    {"scripts/run_export_authority.py", "services/export_reconciliation_service.py"}
)
CONFIGURATION_PIPELINE_CONTINUATION_PATHS = frozenset(
    {
        "services/configuration_continuation.py",
        "services/configuration_continuation_dal.py",
        "services/configuration_read_continuation_dal.py",
        "services/legacy_export_snapshot_service.py",
        "services/producer_recovery_intent.py",
        "services/recovery_release_policy.py",
    }
)
PUBLICATION_DETAIL_PATHS = frozenset(
    {
        "services/export_publication_metrics.py",
        "services/export_reconciliation_service.py",
        "services/export_execution_authority.py",
        "services/export_request_budget.py",
    }
)
PUBLICATION_READBACK_BATCH_PATHS = frozenset(
    {
        "services/export_execution_dal.py",
        "services/export_reconciliation_service.py",
        "kvk/services/new_source_workbook_transport.py",
    }
)
PUBLICATION_RESULT_PATHS = frozenset(
    {
        "services/export_reconciliation_service.py",
        "services/export_recovery_service.py",
        "services/recovery_dal.py",
        "services/recovery_publication_result.py",
        "services/recovery_report.py",
        "services/recovery_service.py",
        "ui/views/recovery_view.py",
    }
)
REPORT_CACHE_HANDOFF_PATHS = frozenset(
    {
        "services/player_report_continuation.py",
        "services/player_report_recovery_service.py",
        "ui/views/recovery_view.py",
    }
)
PUBLICATION_RESULT_HANDOFF_PATHS = PUBLICATION_RESULT_PATHS | REPORT_CACHE_HANDOFF_PATHS
ROLLOVER_GUIDED_PATHS = frozenset(
    {
        "scripts/run_export_authority.py",
        "services/export_recovery_service.py",
        "services/export_runtime_composition.py",
        "services/recovery_release_policy.py",
        "services/rollover_replacement_adapter.py",
        "services/rollover_replacement_authority.py",
        "ui/views/recovery_view.py",
        "ui/views/recovery_input_view.py",
    }
)


def coordinated_policy():
    """Load only the installed authenticated companion, never acquired source."""
    import importlib.util

    path = Path(__file__).with_name("p0a_release.py")
    if not path.exists():
        return None  # Older tools retain all ordinary protected-path refusals.
    spec = importlib.util.spec_from_file_location("installed_p0a_release", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FAILED_EXPORT_TRANSITION_PATHS = frozenset(
    {
        "scripts/run_export_authority.py",
        "services/export_coordination_dal.py",
        "services/export_evidence_catalog_dal.py",
        "services/export_reconciliation_service.py",
        "services/export_replacement_recovery_adapter.py",
        "services/export_runtime_composition.py",
        "services/failed_export_closeout.py",
        "services/failed_export_closeout_dal.py",
        "services/failed_export_recovery_authority.py",
        "services/recovery_release_policy.py",
    }
)

CACHE_ONLY_TRANSITION_PATHS = frozenset(
    {
        "player_stats_cache.py",
        "services/legacy_export_snapshot_service.py",
        "services/player_report_recovery_dal.py",
        "services/player_report_recovery_service.py",
        "services/producer_recovery_intent.py",
        "services/recovery_release_policy.py",
        "services/recovery_report.py",
        "services/recovery_service.py",
    }
)

CONFIGURATION_ONLY_TRANSITION_PATHS = frozenset(
    {
        "proc_config_import.py",
        "services/capture_recovery_context.py",
        "services/configuration_producer_recovery.py",
        "services/configuration_read_continuation_dal.py",
        "services/player_report_recovery_dal.py",
        "services/player_report_recovery_service.py",
        "services/producer_recovery_intent.py",
        "services/recovery_release_policy.py",
        "services/recovery_report.py",
        "services/recovery_service.py",
    }
)


MONITOR_ADMISSION_TRANSITION_PATHS = frozenset(
    {
        "bot_instance.py",
        "core/startup_diagnostics.py",
        "services/recovery_health.py",
        "services/recovery_runtime.py",
        "services/recovery_dal.py",
        "services/recovery_report.py",
        "services/producer_refusal_dal.py",
        "services/producer_refusal_recovery.py",
        "services/producer_recovery_review.py",
        "services/recovery_release_policy.py",
    }
)

REPORT_TIMEOUT_MONITOR_PATHS = frozenset(
    {
        "services/recovery_dal.py",
        "services/recovery_health.py",
        "services/recovery_runtime.py",
        "services/stats_report_continuation_dal.py",
    }
)


REPLACEMENT_WORKFLOW_TRANSITION_PATHS = frozenset(
    {
        "services/export_failure_diagnostics.py",
        "services/export_replacement_recovery_adapter.py",
        "services/recovery_release_policy.py",
    }
)

PUBLICATION_RECOVERY_TRANSITION_PATHS = frozenset(
    {
        "services/export_coordination_dal.py",
        "services/export_failure_diagnostics.py",
        "services/export_recovery_dal.py",
        "services/export_recovery_service.py",
        "services/export_replacement_recovery_adapter.py",
        "services/recovery_dal.py",
        "services/recovery_release_policy.py",
        "services/recovery_service.py",
        "ui/views/recovery_view.py",
        "ui/views/recovery_target_view.py",
        "ui/views/recovery_publication_view.py",
    }
)

PROBE_ADMISSION_TRANSITION_PATHS = frozenset(
    {"services/export_execution_dal.py", "services/legacy_export_snapshot_dal.py"}
)

PUBLICATION_PROGRESS_TRANSITION_PATHS = frozenset(
    {
        "scripts/run_export_authority.py",
        "services/export_proof_progress.py",
        "services/export_runtime_composition.py",
        "services/recovery_execution_guard.py",
        "services/recovery_health.py",
        "services/recovery_service.py",
        "services/recovery_runtime.py",
        "services/recovery_report.py",
        "ui/views/recovery_view.py",
    }
)

PROBE_BUSY_TRANSITION_PATHS = frozenset(
    {
        "services/config_preparation_recovery_service.py",
        "services/export_runtime_composition.py",
        "services/legacy_export_snapshot_service.py",
    }
)

REPORT_CACHE_TRANSITION_PATHS = frozenset(
    {
        "player_stats_cache.py",
        "scripts/run_export_authority.py",
        "services/configuration_continuation_dal.py",
        "services/export_proof_progress.py",
        "services/import_capture_recovery_service.py",
        "services/player_report_continuation.py",
        "services/player_report_continuation_dal.py",
        "services/player_report_recovery_dal.py",
        "services/player_report_recovery_service.py",
        "services/producer_recovery_intent.py",
        "services/recovery_release_policy.py",
        "services/recovery_runtime.py",
        "ui/views/recovery_view.py",
    }
)


EVIDENCE_BACKUP_PATHS = frozenset(
    {
        "services/export_evidence_storage.py",
        "services/export_evidence_recovery.py",
        "services/recovery_evidence_guidance.py",
        "services/producer_refusal_recovery.py",
        "services/queue_admission_recovery.py",
        "services/recovery_report.py",
        "ui/views/recovery_view.py",
    }
)

RECOVERY_RECEIPT_ROUNDTRIP_PATHS = frozenset(
    {
        "services/config_preparation_recovery_dal.py",
        "services/legacy_export_closeout_dal.py",
    }
)

AUTHORITY_DIAGNOSTIC_PATHS = frozenset(
    {
        "scripts/run_export_authority.py",
        "services/export_authority_diagnostics.py",
        "services/export_execution_authority.py",
        "services/export_reconciliation_service.py",
    }
)

PIPELINE_DECISION_BOUND_PATHS = frozenset({"services/processing_pipeline_receipt_dal.py"})

EXPORT_CONTENTION_HANDOFF_PATHS = frozenset(
    {
        "services/all_kvk_capture_recovery_service.py",
        "services/export_coordination_dal.py",
        "services/export_execution_dal.py",
        "services/export_execution_lock.py",
        "services/import_capture_recovery_service.py",
        "services/import_recovery_service.py",
        "services/pipeline_capture_handoff_dal.py",
        "services/recovery_runtime.py",
    }
)

EVENT_CACHE_READINESS_PATHS = frozenset(
    {
        "bot_instance.py",
        "commands/events_cmds.py",
        "core/event_rehydration_lifecycle.py",
        "core/scheduler_lifecycle.py",
        "event_cache.py",
        "event_data_loader.py",
        "event_embed_manager.py",
        "event_scheduler.py",
        "services/event_cache_service.py",
        "services/recovery_health.py",
    }
)


STARTUP_CACHE_FOUNDATIONS_PATHS = frozenset(
    {
        "bot_instance.py",
        "core/startup_diagnostics.py",
        "player_stats_cache.py",
        "profile_cache.py",
        "target_utils.py",
        "services/cache_admission_diagnostics.py",
        "services/cache_outcomes.py",
        "services/export_contention.py",
        "services/player_stats_cache_service.py",
        "services/profile_cache_service.py",
        "services/profile_cache_startup.py",
        "services/recovery_health.py",
        "stats/profile_cache_repository.py",
    }
)


EVENT_DELIVERY_PATHS = frozenset(
    {
        "bot_instance.py",
        "commands/admin_cmds.py",
        "commands/events_cmds.py",
        "core/private_status_response.py",
        "daily_KVK_overview_embed.py",
        "event_scheduler.py",
        "player_self_service/reminder_service.py",
        "rehydrate_views.py",
        "reminder_task_registry.py",
        "services/event_delivery_service.py",
        "services/event_delivery_store.py",
        "services/gsheets_health_service.py",
        "services/operator_status_dal.py",
        "services/operator_status_service.py",
        "services/overview_delivery_service.py",
        "services/recovery_health.py",
    }
)


MONITORING_RELIABILITY_PATHS = frozenset(
    {
        "bot_instance.py",
        "core/interaction_safety.py",
        "core/private_status_response.py",
        "core/recovery_lifecycle.py",
        "services/cache_admission_diagnostics.py",
        "services/export_evidence_recovery.py",
        "services/export_runtime_composition.py",
        "services/gsheets_health_service.py",
        "services/recovery_backlog_dal.py",
        "services/recovery_health.py",
        "services/recovery_runtime.py",
    }
)


PROCCONFIG_ADMISSION_PATHS = frozenset(
    {
        "services/cache_admission_diagnostics.py",
        "bot_instance.py",
        "services/unowned_sql_hold_dal.py",
        "proc_config_import.py",
        "services/export_contention.py",
        "services/recovery_runtime.py",
        "services/configuration_attempt_recovery.py",
        "services/legacy_export_snapshot_service.py",
        "services/recovery_release_policy.py",
    }
)


COORDINATION_LIFECYCLE_PATHS = frozenset(
    {
        "ark/registration_flow.py",
        "core/sql_observation.py",
        "gsheet_module.py",
        "kvk/dal/new_source_import_dal.py",
        "scripts/run_export_authority.py",
        "services/configuration_attempt_dal.py",
        "services/configuration_attempt_recovery.py",
        "services/export_contention.py",
        "services/export_coordination_dal.py",
        "services/failed_export_recovery_authority.py",
        "services/import_capture_recovery_dal.py",
        "services/legacy_export_snapshot_service.py",
        "services/player_report_recovery_service.py",
        "services/processing_pipeline_receipt_dal.py",
        "services/producer_admission.py",
        "services/producer_recovery_intent.py",
        "services/recovery_execution_guard.py",
        "services/recovery_runtime.py",
        "services/recovery_service.py",
        "services/stats_import_outcome_dal.py",
        "services/unowned_sql_hold_dal.py",
        "ui/views/ark_views.py",
        "ui/views/recovery_view.py",
    }
)


HEALTH_ACTIVITY_PATHS = frozenset(
    {
        "services/queue_admission_recovery_dal.py",
        "services/queue_admission_recovery.py",
        "services/recovery_service.py",
        "services/recovery_release_policy.py",
        "services/legacy_export_snapshot_service.py",
        "weekly_activity_importer.py",
        "gsheet_module.py",
    }
)


CHECKPOINT_OBSERVATION_PATHS = frozenset(
    {
        "admin_helpers.py",
        "core/sql_observation.py",
        "processing_pipeline.py",
        "kvk/dal/new_source_import_dal.py",
        "scripts/run_export_authority.py",
        "services/all_kvk_capture_recovery_dal.py",
        "services/authority_observation.py",
        "services/processing_notification_dal.py",
        "services/processing_notification_service.py",
        "services/processing_pipeline_receipts.py",
        "stats_alerts/processing_notifications.py",
        "services/export_contention.py",
        "services/legacy_export_snapshot_dal.py",
        "services/recovery_health.py",
        "services/stats_import_outcome_dal.py",
        "stats_module.py",
    }
)


MGE_LIFECYCLE_PATHS = frozenset(
    {
        "bot_instance.py",
        "core/coalesced_work.py",
        "core/interaction_safety.py",
        "core/operation_outcome.py",
        "core/owned_work.py",
        "mge/dal/mge_roster_dal.py",
        "mge/dal/mge_signup_dal.py",
        "mge/dal/mge_signup_mutation_dal.py",
        "mge/mge_board_delivery_adapter.py",
        "mge/mge_embed_manager.py",
        "mge/mge_roster_execution.py",
        "mge/mge_scheduler.py",
        "mge/mge_signup_service.py",
        "services/event_delivery_service.py",
        "services/legacy_export_snapshot_service.py",
        "ui/views/mge_admin_completion_view.py",
        "ui/views/mge_admin_view.py",
        "ui/views/mge_commander_admin_view.py",
        "ui/views/mge_publish_view.py",
        "ui/views/mge_roster_builder_view.py",
        "ui/views/mge_rules_edit_view.py",
        "ui/views/mge_signup_modal.py",
        "ui/views/mge_signup_view.py",
        "ui/views/mge_simplified_leadership_view.py",
        "ui/views/mge_simplified_signup_form_view.py",
        "ui/views/mge_simplified_signup_view.py",
        "ui/views/prepared_modal_view.py",
    }
)


MGE_A1A_PATHS = frozenset(
    {
        "core/interaction_safety.py",
        "core/operation_timing.py",
        "core/owned_work.py",
        "mge/dal/mge_review_dal.py",
        "mge/dal/mge_roster_dal.py",
        "mge/dataset_errors.py",
        "mge/mge_embed_manager.py",
        "mge/mge_publish_service.py",
        "mge/mge_roster_execution.py",
        "mge/mge_simplified_flow_service.py",
        "mge/mge_simplified_leadership_service.py",
        "ui/views/mge_simplified_leadership_view.py",
    }
)


MGE_A1B_PATHS = frozenset(
    {
        "mge/mge_embed_manager.py",
        "mge/mge_publish_discord_adapter.py",
        "mge/dataset_errors.py",
        "mge/dal/mge_publish_dal.py",
        "core/operation_outcome.py",
        "mge/mge_simplified_flow_service.py",
        "core/coalesced_work.py",
        "mge/mge_refresh_work.py",
        "ui/views/mge_signup_view.py",
        "mge/mge_publish_service.py",
        "mge/mge_roster_service.py",
        "ui/views/mge_roster_builder_view.py",
        "mge/dal/qualified_read.py",
        "mge/mge_scheduler.py",
        "core/interaction_safety.py",
        "ui/views/mge_rules_edit_view.py",
        "mge/dal/mge_board_identity_dal.py",
        "mge/mge_event_service.py",
        "mge/dal/mge_rules_dal.py",
        "core/operation_timing.py",
        "mge/mge_board_preparation.py",
        "mge/dal/mge_recovery_dal.py",
        "core/owned_work.py",
        "ui/views/mge_simplified_leadership_view.py",
        "mge/mge_recovery.py",
        "mge/mge_action_response.py",
        "mge/mge_action_result.py",
        "ui/views/mge_signup_modal.py",
        "commands/mge_cmds.py",
        "mge/dal/mge_leadership_dal.py",
        "mge/mge_board_delivery_adapter.py",
        "mge/mge_roster_execution.py",
        "mge/dal/mge_event_dal.py",
        "ui/views/mge_simplified_signup_form_view.py",
        "mge/mge_board_ownership.py",
        "ui/views/mge_admin_view.py",
        "mge/mge_rules_service.py",
        "mge/dal/mge_review_dal.py",
        "bot_instance.py",
        "mge/dal/mge_roster_dal.py",
        "mge/mge_simplified_leadership_service.py",
    }
)


MGE_FINALISATION_PATHS = frozenset(
    {
        "commands/mge_cmds.py",
        "core/board_lifecycle.py",
        "core/owned_work.py",
        "core/operation_outcome.py",
        "mge/dal/qualified_read.py",
        "mge/dal/mge_completion_dal.py",
        "mge/dal/mge_finalisation_dal.py",
        "mge/dal/mge_results_dal.py",
        "mge/dal/mge_roster_dal.py",
        "mge/dal/mge_rules_dal.py",
        "mge/dal/mge_signup_dal.py",
        "mge/mge_completion_service.py",
        "mge/mge_embed_manager.py",
        "mge/mge_finalisation.py",
        "mge/mge_publish_service.py",
        "mge/mge_recovery.py",
        "mge/mge_scheduler.py",
        "mge/mge_board_ownership.py",
        "mge/mge_board_preparation.py",
        "mge/mge_refresh_work.py",
        "ui/views/mge_admin_completion_view.py",
    }
)


def reviewed_transitions():
    """Only the installed tool selects exact reviewed protocol transitions.

    Target metadata cannot supply this policy. LF hashes permit authenticated
    Git/Windows newline representations; source_plan retains exact installed pins.
    """
    raw = Path(__file__).with_name("k98_update_transitions.json").read_bytes()
    if len(raw) > 110592:
        raise ValueError("Installed transition registry exceeds bound.")
    value = json.loads(raw)
    if set(value) != {"version", "transitions"} or value["version"] != 1:
        raise ValueError("Unsupported installed transition registry.")
    if not isinstance(value["transitions"], list) or len(value["transitions"]) > 52:
        raise ValueError("Bounded installed transitions required.")
    identities = set()
    for item in value["transitions"]:
        if set(item) != {"id", "members"} or not re.fullmatch(r"[a-z0-9_]{1,80}", item["id"]):
            raise ValueError("Exact installed transition required.")
        # These larger reviewed families are indivisible; other bounds remain 16.
        member_limit = (
            len(MGE_FINALISATION_PATHS)
            if item["id"] == "p1_mge_finalisation_v1"
            else (
                len(COORDINATION_LIFECYCLE_PATHS)
                if item["id"] == "coordination_lifecycle_v1"
                else (
                    len(MGE_A1B_PATHS)
                    if item["id"] == "p1_mge_a1b_v1"
                    else (len(MGE_LIFECYCLE_PATHS) if item["id"] == "p1_mge_lifecycle_v1" else 16)
                )
            )
        )
        if item["id"] in identities or not 1 <= len(item["members"]) <= member_limit:
            raise ValueError("Unique bounded transition required.")
        identities.add(item["id"])
        paths = set()
        for member in item["members"]:
            if set(member) != {"path", "before_sha256", "after_sha256"}:
                raise ValueError("Exact transition member required.")
            path = ordinary_path(member["path"])
            fixed_closeout = (
                item["id"] == "failed_export_closeout_v1" and path in FAILED_EXPORT_TRANSITION_PATHS
            )
            fixed_cache = (
                item["id"] == "cache_only_completion_v1" and path in CACHE_ONLY_TRANSITION_PATHS
            )
            fixed_configuration = (
                item["id"] == "configuration_only_completion_v1"
                and path in CONFIGURATION_ONLY_TRANSITION_PATHS
            )
            fixed_monitor = (
                item["id"] == "monitor_admission_closeout_v1"
                and path in MONITOR_ADMISSION_TRANSITION_PATHS
            )
            fixed_report_timeout = (
                item["id"] == "report_timeout_monitor_v1" and path in REPORT_TIMEOUT_MONITOR_PATHS
            )
            fixed_receipt_roundtrip = (
                item["id"] == "recovery_receipt_roundtrip_v1"
                and path in RECOVERY_RECEIPT_ROUNDTRIP_PATHS
            )
            fixed_authority_diagnostics = (
                item["id"] == "authority_diagnostic_capture_v1"
                and path in AUTHORITY_DIAGNOSTIC_PATHS
            )
            fixed_pipeline_decision = (
                item["id"] == "pipeline_decision_bound_v1" and path in PIPELINE_DECISION_BOUND_PATHS
            )
            fixed_export_contention = (
                item["id"] == "export_contention_handoff_v1"
                and path in EXPORT_CONTENTION_HANDOFF_PATHS
            )
            fixed_event_cache = (
                item["id"] == "event_cache_readiness_v1" and path in EVENT_CACHE_READINESS_PATHS
            )
            fixed_startup_foundations = (
                item["id"] == "startup_cache_foundations_v1"
                and path in STARTUP_CACHE_FOUNDATIONS_PATHS
            )
            fixed_event_delivery = (
                item["id"] == "p1_event_delivery_v1" and path in EVENT_DELIVERY_PATHS
            )
            fixed_health_activity = (
                item["id"] == "health_activity_completion_v1" and path in HEALTH_ACTIVITY_PATHS
            )
            fixed_checkpoint_observation = (
                item["id"] == "checkpoint_observation_lifecycle_v1"
                and path in CHECKPOINT_OBSERVATION_PATHS
            )
            fixed_coordination_lifecycle = (
                item["id"] == "coordination_lifecycle_v1" and path in COORDINATION_LIFECYCLE_PATHS
            )
            fixed_procconfig_admission = (
                item["id"] == "procconfig_admission_recovery_v1"
                and path in PROCCONFIG_ADMISSION_PATHS
            )
            fixed_monitoring_reliability = (
                item["id"] == "p1_monitoring_reliability_v1"
                and path in MONITORING_RELIABILITY_PATHS
            )
            fixed_mge_final = (
                item["id"] == "p1_mge_finalisation_v1" and path in MGE_FINALISATION_PATHS
            )
            fixed_mge_a1b = item["id"] == "p1_mge_a1b_v1" and path in MGE_A1B_PATHS
            fixed_mge_a1a = item["id"] == "p1_mge_a1a_v1" and path in MGE_A1A_PATHS
            fixed_mge_lifecycle = (
                item["id"] == "p1_mge_lifecycle_v1" and path in MGE_LIFECYCLE_PATHS
            )
            fixed_replacement = (
                item["id"] == "guided_replacement_release_v1"
                and path in REPLACEMENT_WORKFLOW_TRANSITION_PATHS
            )
            fixed_publication = (
                item["id"] == "guided_publication_recovery_v1"
                and path in PUBLICATION_RECOVERY_TRANSITION_PATHS
            )
            fixed_probe = (
                item["id"] == "probe_stream_admission_v1"
                and path in PROBE_ADMISSION_TRANSITION_PATHS
            )
            fixed_progress = (
                item["id"] == "publication_progress_v1"
                and path in PUBLICATION_PROGRESS_TRANSITION_PATHS
            )
            fixed_probe_busy = (
                item["id"] == "probe_busy_recovery_v1" and path in PROBE_BUSY_TRANSITION_PATHS
            )
            fixed_report_cache = (
                item["id"] == "fresh_report_cache_diagnostics_v1"
                and path in REPORT_CACHE_TRANSITION_PATHS
            )
            fixed_issuer = (
                item["id"] == "drained_issuer_exit_v1" and path in DRAINED_ISSUER_TRANSITION_PATHS
            )
            fixed_report_handoff = (
                item["id"] == "report_cache_handoff_v1" and path in REPORT_CACHE_HANDOFF_PATHS
            )
            fixed_publication_result = (
                item["id"] == "publication_result_v1" and path in PUBLICATION_RESULT_PATHS
            )
            fixed_publication_handoff = (
                item["id"] == "publication_result_handoff_v1"
                and path in PUBLICATION_RESULT_HANDOFF_PATHS
            )
            fixed_rollover = item["id"] == "guided_rollover_v1" and path in ROLLOVER_GUIDED_PATHS
            fixed_timing = (
                item["id"] == "publication_timing_v1" and path in PUBLICATION_TIMING_PATHS
            )
            fixed_readback_batch = (
                item["id"] == "publication_readback_batches_v1"
                and path in PUBLICATION_READBACK_BATCH_PATHS
            )
            fixed_evidence_backup = (
                item["id"] == "evidence_backup_collection_v1" and path in EVIDENCE_BACKUP_PATHS
            )
            fixed_startup_cache = (
                item["id"] == "startup_cache_completion_v1"
                and path in STARTUP_CACHE_COMPLETION_PATHS
            )
            fixed_configuration_read = (
                item["id"] == "configuration_read_request_v1"
                and path in CONFIGURATION_READ_REQUEST_PATHS
            )
            fixed_configuration_intent_replay = (
                item["id"] == "configuration_intent_replay_v1"
                and path in CONFIGURATION_INTENT_REPLAY_PATHS
            )
            fixed_configuration_pipeline = (
                item["id"] == "configuration_pipeline_continuation_v1"
                and path in CONFIGURATION_PIPELINE_CONTINUATION_PATHS
            )
            fixed_rollover_timing = item["id"] == "guided_rollover_timing_v1" and path in (
                ROLLOVER_GUIDED_PATHS | PUBLICATION_TIMING_PATHS
            )
            if (
                not (
                    path.startswith("services/export_")
                    or fixed_closeout
                    or fixed_cache
                    or fixed_configuration
                    or fixed_monitor
                    or fixed_report_timeout
                    or fixed_receipt_roundtrip
                    or fixed_authority_diagnostics
                    or fixed_pipeline_decision
                    or fixed_export_contention
                    or fixed_event_cache
                    or fixed_startup_foundations
                    or fixed_event_delivery
                    or fixed_health_activity
                    or fixed_checkpoint_observation
                    or fixed_coordination_lifecycle
                    or fixed_procconfig_admission
                    or fixed_monitoring_reliability
                    or fixed_mge_final
                    or fixed_mge_a1b
                    or fixed_mge_a1a
                    or fixed_mge_lifecycle
                    or fixed_replacement
                    or fixed_publication
                    or fixed_probe
                    or fixed_progress
                    or fixed_probe_busy
                    or fixed_report_cache
                    or fixed_issuer
                    or fixed_report_handoff
                    or fixed_publication_result
                    or fixed_publication_handoff
                    or fixed_rollover
                    or fixed_timing
                    or fixed_readback_batch
                    or fixed_evidence_backup
                    or fixed_startup_cache
                    or fixed_configuration_read
                    or fixed_configuration_intent_replay
                    or fixed_configuration_pipeline
                    or fixed_rollover_timing
                )
                or not path.endswith(".py")
                or path in paths
            ):
                raise ValueError("Unique export protocol source member required.")
            paths.add(path)
            for field in ("before_sha256", "after_sha256"):
                digest = member[field]
                if digest is None and field == "before_sha256":
                    continue
                if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
                    raise ValueError("Exact reviewed protocol hashes required.")
        if item["id"] == "evidence_backup_collection_v1" and paths != EVIDENCE_BACKUP_PATHS:
            raise ValueError("Complete fixed evidence-backup transition required.")
        if item["id"] == "drained_issuer_exit_v1" and paths != DRAINED_ISSUER_TRANSITION_PATHS:
            raise ValueError("Complete fixed drained-issuer transition required.")
        if item["id"] == "guided_rollover_v1" and paths != ROLLOVER_GUIDED_PATHS:
            raise ValueError("Complete fixed guided-rollover transition required.")
        if item["id"] == "publication_timing_v1" and paths != PUBLICATION_TIMING_PATHS:
            raise ValueError("Complete fixed publication-timing transition required.")
        if item["id"] == "publication_detail_v1" and paths != PUBLICATION_DETAIL_PATHS:
            raise ValueError("Complete fixed publication-detail transition required.")
        if (
            item["id"] == "publication_readback_batches_v1"
            and paths != PUBLICATION_READBACK_BATCH_PATHS
        ):
            raise ValueError("Complete fixed publication-readback batch transition required.")
        if item["id"] == "startup_cache_completion_v1" and paths != STARTUP_CACHE_COMPLETION_PATHS:
            raise ValueError("Complete fixed startup-cache completion transition required.")
        if (
            item["id"] == "configuration_read_request_v1"
            and paths != CONFIGURATION_READ_REQUEST_PATHS
        ):
            raise ValueError("Complete fixed configuration-read request transition required.")
        if (
            item["id"] == "configuration_intent_replay_v1"
            and paths != CONFIGURATION_INTENT_REPLAY_PATHS
        ):
            raise ValueError("Complete fixed configuration-intent/replay transition required.")
        if (
            item["id"] == "configuration_pipeline_continuation_v1"
            and paths != CONFIGURATION_PIPELINE_CONTINUATION_PATHS
        ):
            raise ValueError("Complete fixed configuration pipeline continuation required.")
        if item["id"] == "guided_rollover_timing_v1" and paths != (
            ROLLOVER_GUIDED_PATHS | PUBLICATION_TIMING_PATHS
        ):
            raise ValueError("Complete fixed rollover/timing transition required.")
        if item["id"] == "report_cache_handoff_v1" and paths != REPORT_CACHE_HANDOFF_PATHS:
            raise ValueError("Complete fixed report/cache handoff transition required.")
        if item["id"] == "publication_result_v1" and paths != PUBLICATION_RESULT_PATHS:
            raise ValueError("Complete fixed publication-result transition required.")
        if (
            item["id"] == "publication_result_handoff_v1"
            and paths != PUBLICATION_RESULT_HANDOFF_PATHS
        ):
            raise ValueError("Complete fixed publication-result handoff transition required.")
        if (
            item["id"] == "fresh_report_cache_diagnostics_v1"
            and paths != REPORT_CACHE_TRANSITION_PATHS
        ):
            raise ValueError("Complete fixed report/cache diagnostics transition required.")
        if item["id"] == "failed_export_closeout_v1" and paths != FAILED_EXPORT_TRANSITION_PATHS:
            raise ValueError("Complete fixed failed-export transition required.")
        if item["id"] == "cache_only_completion_v1" and paths != CACHE_ONLY_TRANSITION_PATHS:
            raise ValueError("Complete fixed cache-only transition required.")
        if (
            item["id"] == "configuration_only_completion_v1"
            and paths != CONFIGURATION_ONLY_TRANSITION_PATHS
        ):
            raise ValueError("Complete fixed configuration-only transition required.")
        if (
            item["id"] == "monitor_admission_closeout_v1"
            and paths != MONITOR_ADMISSION_TRANSITION_PATHS
        ):
            raise ValueError("Complete fixed monitor/admission transition required.")
        if item["id"] == "report_timeout_monitor_v1" and paths != REPORT_TIMEOUT_MONITOR_PATHS:
            raise ValueError("Complete fixed reporting-timeout/monitor transition required.")
        if (
            item["id"] == "recovery_receipt_roundtrip_v1"
            and paths != RECOVERY_RECEIPT_ROUNDTRIP_PATHS
        ):
            raise ValueError("Complete fixed recovery-receipt transition required.")
        if item["id"] == "authority_diagnostic_capture_v1" and paths != AUTHORITY_DIAGNOSTIC_PATHS:
            raise ValueError("Complete fixed authority diagnostic transition required.")
        if item["id"] == "pipeline_decision_bound_v1" and paths != PIPELINE_DECISION_BOUND_PATHS:
            raise ValueError("Complete fixed pipeline-decision transition required.")
        if (
            item["id"] == "export_contention_handoff_v1"
            and paths != EXPORT_CONTENTION_HANDOFF_PATHS
        ):
            raise ValueError("Complete fixed export-contention/handoff transition required.")
        if item["id"] == "event_cache_readiness_v1" and paths != EVENT_CACHE_READINESS_PATHS:
            raise ValueError("Complete fixed event-cache readiness transition required.")
        if item["id"] == "p1_event_delivery_v1" and paths != EVENT_DELIVERY_PATHS:
            raise ValueError("Complete fixed event-delivery transition required.")
        if item["id"] == "health_activity_completion_v1" and paths != HEALTH_ACTIVITY_PATHS:
            raise ValueError("Complete fixed health/activity transition required.")
        if (
            item["id"] == "checkpoint_observation_lifecycle_v1"
            and paths != CHECKPOINT_OBSERVATION_PATHS
        ):
            raise ValueError("Complete fixed checkpoint observation transition required.")
        if item["id"] == "coordination_lifecycle_v1" and paths != COORDINATION_LIFECYCLE_PATHS:
            raise ValueError("Complete fixed coordination lifecycle transition required.")
        if item["id"] == "procconfig_admission_recovery_v1" and paths != PROCCONFIG_ADMISSION_PATHS:
            raise ValueError("Complete fixed ProcConfig admission transition required.")
        if item["id"] == "p1_mge_finalisation_v1" and paths != MGE_FINALISATION_PATHS:
            raise ValueError("Complete fixed MGE finalisation transition required.")
        if item["id"] == "p1_mge_a1b_v1" and paths != MGE_A1B_PATHS:
            raise ValueError("Complete fixed MGE A1b transition required.")
        if item["id"] == "p1_mge_a1a_v1" and paths != MGE_A1A_PATHS:
            raise ValueError("Complete fixed MGE A1a transition required.")
        if item["id"] == "p1_mge_lifecycle_v1" and paths != MGE_LIFECYCLE_PATHS:
            raise ValueError("Complete fixed MGE lifecycle transition required.")
        if item["id"] == "p1_monitoring_reliability_v1" and paths != MONITORING_RELIABILITY_PATHS:
            raise ValueError("Complete fixed monitoring-reliability transition required.")
        if (
            item["id"] == "startup_cache_foundations_v1"
            and paths != STARTUP_CACHE_FOUNDATIONS_PATHS
        ):
            raise ValueError("Complete fixed startup-cache foundations transition required.")
        if (
            item["id"] == "guided_replacement_release_v1"
            and paths != REPLACEMENT_WORKFLOW_TRANSITION_PATHS
        ):
            raise ValueError("Complete fixed replacement workflow transition required.")
        if (
            item["id"] == "guided_publication_recovery_v1"
            and paths != PUBLICATION_RECOVERY_TRANSITION_PATHS
        ):
            raise ValueError("Complete fixed publication recovery transition required.")
        if item["id"] == "probe_stream_admission_v1" and paths != PROBE_ADMISSION_TRANSITION_PATHS:
            raise ValueError("Complete fixed probe admission transition required.")
        if (
            item["id"] == "publication_progress_v1"
            and paths != PUBLICATION_PROGRESS_TRANSITION_PATHS
        ):
            raise ValueError("Complete fixed publication progress transition required.")
        if item["id"] == "probe_busy_recovery_v1" and paths != PROBE_BUSY_TRANSITION_PATHS:
            raise ValueError("Complete fixed probe busy recovery transition required.")
    return value["transitions"]


def transition_paths():
    return {m["path"] for t in reviewed_transitions() for m in t["members"]}


def check_protocol_transition(path, read_blob, before, target):
    for transition in reviewed_transitions():
        if path not in {member["path"] for member in transition["members"]}:
            continue
        matched = True
        for member in transition["members"]:
            for commit, field in ((before, "before_sha256"), (target, "after_sha256")):
                raw = read_blob(commit, member["path"])
                digest = sha256(raw.replace(b"\r\n", b"\n")) if raw is not None else None
                matched = matched and digest == member[field]
        if matched:
            return {member["path"] for member in transition["members"]}
    raise ValueError(f"Protected protocol transition is not installed/reviewed: {path}")


# Installed policy, never supplied by the target tree. Only these application
# bodies may differ in otherwise protected mixed modules. Headers, imports,
# initialization and every other declaration remain structurally identical.
APPLICATION_METHODS = {
    "services/export_coordination_dal.py": ("ExportCoordinationDAL", {"enqueue"}),
    "services/export_coordination_service.py": ("ExportCoordinator", {"discover"}),
    "services/export_runtime_composition.py": ("ExportRuntime", {"__init__"}),
}
APPLICATION_ADDITIONS = {
    "services/export_coordination_dal.py": "def check_intent_weights(self, intent): pass",
}


def application_contract(path, raw):
    """Project protected syntax without importing or executing release source.

    This is a compatibility boundary for reviewed code, not a Python sandbox or
    proof of arbitrary application behavior. Unknown edits still need review of
    the installed updater policy, rather than a release-controlled exemption.
    """
    if not isinstance(raw, bytes) or not raw or len(raw) > 2 * 1024 * 1024:
        raise ValueError(f"Existing bounded application source required: {path}")
    try:
        tree = ast.parse(raw, filename=path)
        compile(tree, path, "exec")  # Syntax validation only; never execute target code.
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise ValueError(f"Cannot establish application compatibility: {path}") from exc
    class_name, methods = APPLICATION_METHODS[path]
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name]
    if len(classes) != 1:
        raise ValueError(f"Exact application class required: {path}")
    optional = (
        ast.parse(APPLICATION_ADDITIONS[path]).body[0] if path in APPLICATION_ADDITIONS else None
    )
    if optional is not None and not isinstance(optional, ast.FunctionDef):
        raise ValueError("Installed application policy is malformed.")
    seen, retained = set(), []
    for node in classes[0].body:
        name = getattr(node, "name", None)
        if name in methods or (optional is not None and name == optional.name):
            if name in seen or not isinstance(node, ast.FunctionDef):
                raise ValueError(f"Ambiguous application method: {path}:{name}")
            seen.add(name)
            node.body = [ast.Pass()]
            if optional is not None and name == optional.name:
                if ast.dump(node) != ast.dump(optional):
                    raise ValueError(f"Application helper signature differs: {path}:{name}")
                continue
        retained.append(node)
    if not methods <= seen:
        raise ValueError(f"Required application methods missing: {path}")
    classes[0].body = retained
    return ast.dump(tree), seen


def check_application_change(path, before, target):
    old, old_methods = application_contract(path, before)
    new, new_methods = application_contract(path, target)
    if old != new or not old_methods <= new_methods:
        raise ValueError(f"Protected application contract changed; non-routine release: {path}")


def combined_description(raw, before):
    """A reviewed target-tree descriptor, never a live/generated hash assertion."""
    value = validate_combined_description(raw)
    if before not in value["bot_predecessors"]:
        raise ValueError(f"Combined release does not support installed Bot predecessor {before}.")
    return value


def validate_combined_description(raw):
    """Validate committed metadata without claiming installed compatibility."""
    if len(raw) > 65536:
        raise ValueError("Combined release description exceeds bound.")
    value = json.loads(raw)
    fields = {"version", "profile", "bot_predecessors", "sql_commit", "migrations"}
    if not isinstance(value, dict) or type(value.get("version")) is not int:
        raise ValueError("Exact combined release fields and integer version required.")
    if value["version"] == 2:
        if value != MGE_PORTABLE_APPLICATION_RELEASE:
            raise ValueError("Portable MGE contract requires the exact reviewed release.")
        fields.add("application_contract_transition")
    elif value["version"] != 1:
        raise ValueError("Unsupported combined descriptor version; no drain requested.")
    if set(value) != fields:
        raise ValueError("Exact combined release fields required.")
    if value["profile"] not in {
        "module_grants_v1",
        "additive_tables_v1",
        "mge_finalisation_v1",
    }:
        raise ValueError("Unsupported combined SQL profile; no drain requested.")
    predecessors = value["bot_predecessors"]
    if (
        not isinstance(predecessors, list)
        or not 1 <= len(predecessors) <= 16
        or any(not isinstance(x, str) or not re.fullmatch(r"[a-f0-9]{40}", x) for x in predecessors)
    ):
        raise ValueError("Bounded exact Bot predecessor commits required.")
    if not isinstance(value["sql_commit"], str) or not re.fullmatch(
        r"[a-f0-9]{40}", value["sql_commit"]
    ):
        raise ValueError("Exact reviewed SQL commit required.")
    migrations = value["migrations"]
    if not isinstance(migrations, list) or not 1 <= len(migrations) <= 16:
        raise ValueError("Explicit bounded SQL migration order required.")
    seen = set()
    for migration in migrations:
        if not isinstance(migration, dict) or set(migration) != {"id", "sha256"}:
            raise ValueError("Exact migration ID and profile hash required.")
        name = migration["id"]
        if (
            not isinstance(name, str)
            or not re.fullmatch(r"[0-9]{8}_[0-9]{3}_[a-z0-9_]+", name)
            or name in seen
            or not isinstance(migration["sha256"], str)
            or not re.fullmatch(r"[a-f0-9]{64}", migration["sha256"])
        ):
            raise ValueError("Unique exact SQL migration selection required.")
        seen.add(name)
    return value


def validate_mge_profile(profile, migration_id):
    """Fixed schema family; environment bindings only, never target-supplied DDL."""
    if (
        not isinstance(profile, dict)
        or set(profile)
        != {
            "version",
            "profile",
            "migration_id",
            "database_collation",
            "tempdb_collation",
            "compatibility_level",
            "requires",
        }
        or type(profile["version"]) is not int
        or profile["version"] != 1
        or profile["profile"] != "mge_finalisation_v1"
        or profile["migration_id"] != migration_id
        or not isinstance(migration_id, str)
        or not re.fullmatch(r"[0-9]{8}_[0-9]{3}_[a-z0-9_]+", migration_id)
        or type(profile["compatibility_level"]) is not int
        or profile["compatibility_level"] not in {130, 140, 150, 160}
        or any(
            not isinstance(profile[k], str) or not re.fullmatch(r"[A-Za-z0-9_]{1,128}", profile[k])
            for k in ("database_collation", "tempdb_collation")
        )
        or not isinstance(profile["requires"], list)
        or len(profile["requires"]) > 64
    ):
        raise ValueError("Exact bounded MGE profile required.")
    seen = set()
    for dependency in profile["requires"]:
        if (
            not isinstance(dependency, dict)
            or set(dependency) != {"migration_id", "sha256", "status"}
            or not isinstance(dependency["migration_id"], str)
            or not re.fullmatch(r"[0-9]{8}_[0-9]{3}_[A-Za-z0-9_]+", dependency["migration_id"])
            or dependency["migration_id"] in seen
            or not isinstance(dependency["sha256"], str)
            or not re.fullmatch(r"[a-f0-9]{64}", dependency["sha256"])
            or dependency["status"] not in ("Applied", "Failed")
        ):
            raise ValueError("Exact unique MGE predecessor history required.")
        seen.add(dependency["migration_id"])
    return profile


def check_mge_release_binding(before, target, changes, read_blob):
    """Initial finalisation adoption must install its SQL through the combined runner."""
    introduced = {
        "core/board_lifecycle.py",
        "mge/dal/mge_finalisation_dal.py",
        "mge/mge_finalisation.py",
    }
    if not any(
        path in changes and read_blob(before, path) is None and read_blob(target, path) is not None
        for path in introduced
    ):
        return
    raw = read_blob(target, RELEASE_DESCRIPTION)
    if raw is None or raw == read_blob(before, RELEASE_DESCRIPTION):
        raise ValueError("MGE finalisation requires a changed, bound combined SQL descriptor.")
    description = combined_description(raw, before)
    if description["profile"] != "mge_finalisation_v1" or len(description["migrations"]) != 1:
        raise ValueError("MGE finalisation requires its single fixed SQL profile.")


def combined_payload(description, read_sql_blob, *, protected_objects=(), protected_principals=()):
    """Flatten only the explicit pinned profile/modules; preserve all SQL bytes."""
    files = {}
    sql_tools = SQL_TOOLS + (
        ("SqlDeploy.TableRelease.ps1", "SqlDeploy.MgeFinalisation.ps1")
        if description["profile"] == "mge_finalisation_v1"
        else (
            ("SqlDeploy.TableRelease.ps1",)
            if description["profile"] == "additive_tables_v1"
            else ()
        )
    )
    for name in sql_tools:
        raw = read_sql_blob("deploy/" + name)
        if not raw or len(raw) > 2 * 1024 * 1024:
            raise ValueError(f"Pinned SQL runner missing or oversized: {name}")
        files[name] = raw
    modules, grants, profiles = set(), set(), []
    protected_objects = {x.casefold() for x in protected_objects}
    protected_principals = {x.casefold() for x in protected_principals}
    for migration in description["migrations"]:
        name = migration["id"] + ".release.json"
        raw = read_sql_blob("migrations/" + name)
        if not raw or len(raw) > 1024 * 1024 or sha256(raw) != migration["sha256"]:
            raise ValueError(f"SQL profile differs from reviewed description: {name}")
        p = json.loads(raw)
        if description["profile"] == "mge_finalisation_v1":
            validate_mge_profile(p, migration["id"])
            objects = {
                "dbo.mge_boardfinalisation",
                "dbo.tr_mge_events_frozen",
                "dbo.tr_mge_awards_frozen",
                "dbo.tr_mge_signups_frozen",
                "dbo.mge_events",
                "dbo.mge_awards",
                "dbo.mge_signups",
            }
            if objects & (modules | protected_objects):
                raise ValueError("Repeated or protected MGE schema family.")
            modules.update(objects)
            if name in files:
                raise ValueError("SQL profile filename collision.")
            files[name] = raw
            profiles.append(dict(id=migration["id"], file=name, sha256=sha256(raw)))
            continue
        if description["profile"] == "additive_tables_v1":
            expected = {
                "version",
                "profile",
                "migration_id",
                "database_collation",
                "tempdb_collation",
                "compatibility_level",
                "tables",
                "requires",
            }
            if (
                not isinstance(p, dict)
                or set(p) != expected
                or p["version"] != 1
                or p["profile"] != "additive_tables_v1"
                or p["migration_id"] != migration["id"]
            ):
                raise ValueError("Exact additive table profile required.")
            if not isinstance(p["tables"], list) or not 1 <= len(p["tables"]) <= 8:
                raise ValueError("Bounded additive tables required.")
            for table in p["tables"]:
                if not isinstance(table, dict) or set(table) != {
                    "schema",
                    "name",
                    "columns",
                    "primary_key",
                    "unique_keys",
                    "checks",
                    "foreign_keys",
                }:
                    raise ValueError("Exact declarative table fields required.")
                if any(
                    not isinstance(table[k], str)
                    or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", table[k])
                    for k in ("schema", "name")
                ):
                    raise ValueError("Ordinary table identifiers required.")
                key = (table["schema"] + "." + table["name"]).casefold()
                if (
                    key in modules
                    or key in protected_objects
                    or key in {"dbo.schemamigrationhistory", "dbo.deploymentrunhistory"}
                ):
                    raise ValueError("Repeated or protected additive table.")
                modules.add(key)
            # The exact SQL runner validates the full type/check/key DSL before
            # drain and on every status/apply. No SQL text is acquired here.
            if name in files:
                raise ValueError("SQL profile filename collision.")
            files[name] = raw
            profiles.append(dict(id=migration["id"], file=name, sha256=sha256(raw)))
            continue
        if (
            not isinstance(p, dict)
            or set(p)
            != {
                "version",
                "profile",
                "migration_id",
                "database_collation",
                "tempdb_collation",
                "compatibility_level",
                "modules",
                "grants",
                "requires",
            }
            or p["version"] != 1
            or p["profile"] != description["profile"]
            or p["migration_id"] != migration["id"]
        ):
            raise ValueError(f"Unsupported SQL migration profile: {name}")
        # Full profile validation also runs through the exact SqlClient runner
        # before drain. Reject cross-step overlaps: prior postimages must remain
        # verifiable after any later step, including on every resume.
        for m in p["modules"]:
            key = (m["schema"] + "." + m["name"]).casefold()
            if key in protected_objects:
                raise ValueError(f"SQL module changes protected startup contract: {key}")
            if key in modules:
                raise ValueError(f"Repeated SQL module across release steps: {key}")
            modules.add(key)
            member = m["file"]
            if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,120}\.sql", member):
                raise ValueError("Ordinary flat SQL module filename required.")
            content = read_sql_blob("migrations/" + member)
            if not content or len(content) > 2 * 1024 * 1024 or sha256(content) != m["sha256"]:
                raise ValueError(f"Exact SQL module bytes differ: {member}")
            if member in files and files[member] != content:
                raise ValueError(f"SQL payload collision: {member}")
            files[member] = content
        for g in p["grants"]:
            if (g["schema"] + "." + g["name"]).casefold() in protected_objects or g[
                "principal"
            ].casefold() in protected_principals:
                raise ValueError("SQL grant changes protected startup contract.")
            key = tuple(str(g[k]).casefold() for k in ("schema", "name", "principal", "permission"))
            if key in grants:
                raise ValueError("Repeated SQL grant across release steps.")
            grants.add(key)
        if name in files:
            raise ValueError("SQL profile filename collision.")
        files[name] = raw
        profiles.append(dict(id=migration["id"], file=name, sha256=sha256(raw)))
    check_case_aliases(files)
    return (
        dict(
            commit=description["sql_commit"],
            profiles=profiles,
            members=[dict(name=n, sha256=sha256(b)) for n, b in sorted(files.items())],
        ),
        files,
    )


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def ordinary_path(path):
    """Reject paths whose Windows interpretation differs from a Git tree path."""
    if (
        not isinstance(path, str)
        or len(path) > 240
        or not re.fullmatch(r"[A-Za-z0-9_ .()/+-]+", path)
        or any(
            part in {"", ".", ".."}
            or part.endswith((".", " "))
            or part.split(".")[0].upper()
            in {
                "CON",
                "PRN",
                "AUX",
                "NUL",
                *(f"COM{i}" for i in range(10)),
                *(f"LPT{i}" for i in range(10)),
            }
            for part in path.split("/")
        )
        or path.casefold().startswith((".git/", "venv/", ".venv/"))
    ):
        raise ValueError(f"Unsupported source path: {path!r}")
    return path


def check_source_only(paths, *, tool_copies=(), read_blob=None, before=None, target=None):
    """Routine mode cannot silently install dependencies, SQL or environment."""
    protocols = transition_paths()
    for path in paths:
        ordinary_path(path)
        if path in TOOL_SOURCE_PATHS and path in tool_copies:
            continue  # source_plan must compare the target with installed bytes.
        if path in APPLICATION_METHODS and read_blob is not None:
            try:
                check_application_change(path, read_blob(before, path), read_blob(target, path))
            except ValueError:
                if path not in protocols:
                    raise
                # A protected method may change only through a complete exact
                # bundle authenticated by the installed updater registry.
                check_protocol_transition(path, read_blob, before, target)
            continue
        if path in protocols and read_blob is not None:
            check_protocol_transition(path, read_blob, before, target)
            continue
        lower = path.casefold()
        # Preparation runs installed tooling with predecessor helpers, while
        # the successor consumes the resulting seed. Keep both contract sides
        # unchanged; upgrading this boundary needs a coordinated release.
        if lower.startswith(
            (
                "core/export_",
                "services/export_",
                "scripts/run_export_",
                "scripts/provision_export_",
            )
        ) or lower in {
            "run_bot.py",
            "bot_config.py",
            "constants.py",
            "core/__init__.py",
            "services/__init__.py",
            "scripts/__init__.py",
            "scripts/prepare_k98_release.py",
            "scripts/prepare_k98_update.py",
            "scripts/verify_k98_update_pair.py",
            "scripts/package_k98_update_tool.py",
            "scripts/update-k98.ps1",
            "scripts/k98-sourceupdate.ps1",
            "scripts/deploy-k98release.ps1",
            "scripts/k98_update_transitions.json",
        }:
            raise ValueError(
                f"Startup/update contract change requires a non-routine release: {path}"
            )
        if "__pycache__" in lower.split("/") or lower.endswith(
            (".pyw", ".pyc", ".pyd", ".pyo", ".so")
        ):
            raise ValueError(f"Release includes a bootstrap-forbidden import artifact: {path}")
        if lower.startswith(
            ("requirements", "sql/", "migrations/", "config/", ".env")
        ) or lower in {
            "pyproject.toml",
            "poetry.lock",
            "uv.lock",
            "pipfile",
            "pipfile.lock",
        }:
            raise ValueError(f"Release includes a non-source contract change: {path}")


def bootstrap_source_path(path):
    """Match run_export_authority.code_files, including case-sensitive pruning.

    Kept local because the installed predecessor bootstraps the first updater.
    A filesystem parity regression checks this against the real enumerator.
    """
    parts = path.split("/")
    ignored = {
        ".venv",
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "tests",
        "data",
        "downloads",
        "artifacts",
        "docs",
        "logs",
        "smoke_artifacts",
        "sql",
        "assets",
    }
    return (
        parts[-1].lower().endswith(".py")
        and not (len(parts) > 1 and parts[0] == "venv")
        and not any(part in ignored or part.startswith(".") for part in parts[:-1])
    )


def check_case_aliases(paths):
    """Check every file/directory spelling, including unchanged non-runtime paths."""
    spellings = {}
    for path in sorted(set(paths)):
        parts = path.split("/")
        for depth in range(1, len(parts) + 1):
            prefix = "/".join(parts[:depth])
            folded_prefix = prefix.casefold()
            if spellings.setdefault(folded_prefix, prefix) != prefix:
                raise ValueError(f"Case-colliding source inventory: {path}")


def check_transition_inventory(changes, read_blob, before, target, *, admitted=()):
    """Require every changed bundle member, authenticating unchanged peers too."""
    changed = set(changes)
    for path in (changed & transition_paths()) - set(admitted):
        if path in APPLICATION_METHODS:
            try:
                check_application_change(path, read_blob(before, path), read_blob(target, path))
            except ValueError:
                pass  # The complete exact transition must authorize this change.
            else:
                continue
        # This authenticates every predecessor/successor member, including
        # dependencies omitted from Git's diff because their bytes did not change.
        bundle = check_protocol_transition(path, read_blob, before, target)
        if any(read_blob(before, peer) != read_blob(target, peer) for peer in bundle - changed):
            raise ValueError("Incomplete reviewed protocol transition inventory.")


def source_plan(previous, before, target, changes, read_blob, *, tool_sources=None):
    """Build exact source hashes using authenticated Git blobs, not live new bytes.

    ``changes`` contains ordinary add/modify/delete paths; renames are represented
    as delete+add. ``read_blob(commit, path)`` returns bytes or None for absence.
    Preserve installed newline conventions for existing source pins. New members
    use repository blob bytes; installation must explicitly verify those bytes.
    """
    if any(not re.fullmatch(r"[0-9a-f]{40}", value) for value in (before, target)):
        raise ValueError("Exact private-main commits required.")
    if before == target:
        raise ValueError("Source is already current.")
    if not changes or len(changes) > 4096 or len(set(changes)) != len(changes):
        raise ValueError("Bounded unique changed paths required.")
    tool_sources = tool_sources or {}
    policy = coordinated_policy()
    coordinated = policy.selected(before, target, changes, read_blob) if policy else None
    admitted = {r["path"] for r in coordinated["sources"]} if coordinated else set()
    check_transition_inventory(changes, read_blob, before, target, admitted=admitted)
    check_mge_release_binding(before, target, changes, read_blob)
    check_source_only(
        [p for p in changes if p not in admitted],
        tool_copies=tool_sources,
        read_blob=read_blob,
        before=before,
        target=target,
    )
    folded = [path.casefold() for path in changes]
    if len(set(folded)) != len(folded):
        raise ValueError("Case-colliding source paths refused.")
    pins = deepcopy(previous["AutomaticStartupPolicy.json"]["source_hashes"])
    # Windows aliases apply to retained files and directory components too.
    # Refuse even case-only rename releases before drain rather than relying on
    # Git's case-insensitive checkout behavior to repair the installed tree.
    check_case_aliases(set(pins) | set(changes))
    conventions = {}
    for path, digest in pins.items():
        ordinary_path(path)
        raw = read_blob(before, path)
        if raw is None:
            raise ValueError(f"Installed source absent from predecessor: {path}")
        lf = raw.replace(b"\r\n", b"\n")
        if sha256(raw) == digest:
            conventions[path] = b"\r\n" if b"\r\n" in raw else b"\n"
        elif sha256(lf) == digest:
            conventions[path] = b"\n"
        elif sha256(lf.replace(b"\n", b"\r\n")) == digest:
            conventions[path] = b"\r\n"
        else:
            raise ValueError(f"Installed policy does not match predecessor source: {path}")
    members, payload = [], {}
    for path in sorted(changes):
        old, new = read_blob(before, path), read_blob(target, path)
        if path in TOOL_SOURCE_PATHS and (new is None or new != tool_sources.get(path)):
            raise ValueError(
                f"Target updater copy differs from the installed reviewed tool: {path}"
            )
        if old == new or (old is None and new is None):
            raise ValueError(f"Changed-path inventory differs: {path}")
        if any(raw is not None and len(raw) > 2 * 1024 * 1024 for raw in (old, new)):
            raise ValueError(f"Source member exceeds bound: {path}")
        runtime = bootstrap_source_path(path)
        if new is None:
            pins.pop(path, None)
        else:
            if path in conventions:
                new = new.replace(b"\r\n", b"\n").replace(b"\n", conventions[path])
            payload[path] = new
            if runtime:
                pins[path] = sha256(new)
        members.append(
            dict(
                path=path,
                # Existing runtime files must retain the installed exact pin.
                # Non-runtime files may have Git's LF or CRLF checkout form.
                # These authenticated preimages constrain ownership preparation;
                # live content never supplies its own expected digest.
                before_sha256=(
                    [previous["AutomaticStartupPolicy.json"]["source_hashes"][path]]
                    if path in previous["AutomaticStartupPolicy.json"]["source_hashes"]
                    else (
                        sorted(
                            {
                                sha256(raw)
                                for raw in (
                                    (old,)
                                    if b"\0" in old
                                    else (
                                        old,
                                        old.replace(b"\r\n", b"\n"),
                                        old.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"),
                                    )
                                )
                            }
                        )
                        if old is not None
                        else []
                    )
                ),
                target_sha256=sha256(new) if new is not None else None,
                checkout_sha256=(
                    sorted(
                        {
                            sha256(raw)
                            for raw in (
                                (read_blob(target, path),)
                                if b"\0" in new
                                else (
                                    read_blob(target, path),
                                    read_blob(target, path).replace(b"\r\n", b"\n"),
                                    read_blob(target, path)
                                    .replace(b"\r\n", b"\n")
                                    .replace(b"\n", b"\r\n"),
                                )
                            )
                        }
                    )
                    if new is not None
                    else []
                ),
                runtime=runtime,
                deleted=new is None,
                added=old is None,
            )
        )
    if sum(map(len, payload.values())) > 64 * 1024 * 1024:
        raise ValueError("Source payload exceeds bound.")
    # Verify unchanged pins against the target as well: a missing diff member
    # must never produce a policy for a mixed predecessor/successor source tree.
    for path, digest in pins.items():
        raw = payload.get(path)
        if raw is None:
            raw = read_blob(target, path)
            if raw is None:
                raise ValueError(f"Target source pin is missing: {path}")
            raw = raw.replace(b"\r\n", b"\n").replace(b"\n", conventions[path])
        if sha256(raw) != digest:
            raise ValueError(f"Target inventory omitted changed source: {path}")
    return (
        dict(before=before, target=target, source_members=members, new_pins=pins),
        payload,
    )


def release_seed(previous, pins, gate, *, policy_path=None, policy_sha256=None):
    """Derive fresh metadata and update only exact predecessor gate bindings."""
    deployment, review, pipe = (str(uuid4()) for _ in range(3))
    payload = successor_seed(
        previous, pins, deployment_id=deployment, review_id=review, pipe_id=pipe
    )
    old = previous["AutomaticStartupPolicy.json"]
    new = json.loads(payload["AutomaticStartupPolicy.json"])
    old_directory = str(PureWindowsPath(old["seed_plan"]["path"]).parent)
    if policy_path is not None:
        # A reviewed activation may keep its seed in the predecessor directory.
        # Rebind the gate and wrapper log from the active policy location.
        active_path = PureWindowsPath(policy_path)
        if (
            not active_path.is_absolute()
            or active_path.name != "AutomaticStartupPolicy.json"
            or gate.count(f"$policy='{active_path}'") != 1
        ):
            raise ValueError("Installed launch gate active policy path differs.")
        old_directory = str(active_path.parent)
    new_directory = str(PureWindowsPath(new["seed_plan"]["path"]).parent)
    # A launch gate remains reviewed code. No eval, regex template engine or
    # guessed substitution is used to alter executable behavior.
    # The active policy was authenticated as bytes. Activation packets may use
    # different JSON whitespace than encode(); predecessor identity must retain
    # that exact installed hash, not a hash of re-serialized semantic content.
    old_hash = policy_sha256 if policy_sha256 is not None else sha256(encode(old))
    if not isinstance(old_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", old_hash):
        raise ValueError("Installed policy checksum format differs.")
    new["predecessor"]["policy_sha256"] = old_hash
    payload["AutomaticStartupPolicy.json"] = encode(new)
    if old_directory not in gate or old_hash not in gate:
        raise ValueError("Installed launch gate does not bind predecessor policy.")
    gate = gate.replace(old_directory, new_directory).replace(
        old_hash, sha256(payload["AutomaticStartupPolicy.json"])
    )
    replacements = {}
    for path, old_digest in old["source_hashes"].items():
        if old_digest in gate:
            if path not in pins:
                raise ValueError("Launch-gate source member cannot be removed by a routine update.")
            if replacements.setdefault(old_digest, pins[path]) != pins[path]:
                raise ValueError(
                    "Ambiguous launch-gate source hashes require a non-routine release."
                )
    if replacements:
        # Match the original text once: a replacement digest can itself be a
        # different predecessor digest and must never be rewritten again.
        gate = re.sub("|".join(map(re.escape, replacements)), lambda m: replacements[m[0]], gate)
    payload["Start-ReviewedAutomaticStartup.ps1"] = gate.encode("utf-8")
    return payload


# Installed updater authority for one independently derived startup-contract delta.
# These are not acquired target-tree expectations or observed post-deploy hashes.
MGE_APPLICATION_BEFORE = "814a7e6be4ac3865ee29b65e3c55ec7ad06d4a2ddeb0831f5cf1480d39d9f49f"
MGE_APPLICATION_AFTER_METADATA = "103e92000529669ec7213a397f1062036a7965ef1d9be4ea7712dcb91e7feb5b"
MGE_APPLICATION_REVIEW = "26a303f7-e8b6-4be6-9dce-43086c78d98e"
MGE_APPLICATION_PARENTS = frozenset({"dbo.MGE_Events", "dbo.MGE_Awards", "dbo.MGE_Signups"})
MGE_APPLICATION_RELEASE = {
    "version": 1,
    "profile": "mge_finalisation_v1",
    "bot_predecessors": ["2c31de42eb91cf6b7f9f61f3aaf3efc3597c4ea6"],
    "sql_commit": "9344a37656b034dd43867435e7c039ed20ae1c5e",
    "migrations": [
        {
            "id": "20261029_001_mge_board_finalisation",
            "sha256": "8fea59034c0ac0d14cfb6f72e03a3eda9c823648ec2c0fead6cd208bd4312bb0",
        }
    ],
}


def mge_application_contract_transition(previous, description):
    """Admit only the reviewed three-trigger delta to one exact old contract.

    All source/scope/permission expectations remain byte-for-byte equivalent.
    Fresh predecessor and successor SQL observations still use the unchanged
    complete startup comparators. No runtime observation becomes an expectation.
    """
    if description != MGE_APPLICATION_RELEASE:
        raise ValueError("MGE startup contract requires the exact reviewed release.")
    bot = previous["bot-template.json"]
    before = bot["application_sql_contract"]
    if sha256(encode(before)) != MGE_APPLICATION_BEFORE:
        raise ValueError("MGE predecessor application contract differs from reviewed evidence.")
    after = deepcopy(before)
    after["metadata_hash"] = MGE_APPLICATION_AFTER_METADATA
    after["review_id"] = MGE_APPLICATION_REVIEW
    return {
        "contracts": {
            key: {"before": deepcopy(bot[key]), "after": deepcopy(bot[key])}
            for key in ("sql_contract", "legacy_sql_contract")
        }
        | {"application_sql_contract": {"before": deepcopy(before), "after": after}}
    }


# A distinct installed authority upgrades the raw v2 contract to portable v3.
# The before contract and SQL migration remain the original exact production
# bindings. This does not admit a rebuilt lab as that production predecessor.
MGE_PORTABLE_APPLICATION_RELEASE = deepcopy(MGE_APPLICATION_RELEASE) | {
    "version": 2,
    "application_contract_transition": "mge_application_schema_v2",
}
MGE_PORTABLE_APPLICATION_AFTER_METADATA = (
    "2825f1e9fb60d022a974951959f8443dfadabcb8e163d2fdb79e13ca6174648f"
)
MGE_PORTABLE_APPLICATION_REVIEW = "9d113843-0cf0-5f31-a1c6-296e5b335156"


def mge_portable_application_contract_transition(previous, description):
    """Admit one independently derived format and three-trigger transition.

    Complete old raw and new portable observations remain mandatory at their
    respective release gates. Neither target source nor observed SQL supplies
    the expected contract, and permission/scope expectations never change.
    """
    if description != MGE_PORTABLE_APPLICATION_RELEASE:
        raise ValueError("Portable MGE contract requires the exact reviewed release.")
    bot = previous["bot-template.json"]
    before = bot["application_sql_contract"]
    if (
        sha256(encode(before)) != MGE_APPLICATION_BEFORE
        or type(before.get("version")) is not int
        or before["version"] != 2
        or "fingerprint_format" in before
    ):
        raise ValueError("Portable MGE predecessor application contract differs from review.")
    after = deepcopy(before)
    after.update(
        version=3,
        fingerprint_format="application_schema_v2",
        metadata_hash=MGE_PORTABLE_APPLICATION_AFTER_METADATA,
        review_id=MGE_PORTABLE_APPLICATION_REVIEW,
    )
    return {
        "contracts": {
            key: {"before": deepcopy(bot[key]), "after": deepcopy(bot[key])}
            for key in ("sql_contract", "legacy_sql_contract")
        }
        | {"application_sql_contract": {"before": deepcopy(before), "after": after}}
    }


def prepare_update(
    observation,
    changes,
    read_blob,
    destination,
    tool_directory,
    *,
    secure_output=False,
    read_sql_blob=None,
):
    """Prepare a source or bounded combined package; inputs are machine-derived.

    The caller has authenticated installed metadata and acquired an exact private
    main revision. The generated binding is rechecked by preflight before drain.
    """
    previous = observation["seed"]
    config = deepcopy(observation["bindings"])
    tools = Path(tool_directory)
    verifier = runpy.run_path(str(tools / "verify_k98_update_pair.py"))
    archive = verifier["validate_contract_archive"](
        verifier["read"](tools / "contract_verifier.zip", limit=2 * 1024 * 1024),
        config["contract_verifier_sha256"],
    )
    tool_sources = {
        path: (tools / Path(path).name).read_bytes()
        for path in changes
        if path in TOOL_SOURCE_PATHS
    }
    plan, payload = source_plan(
        previous,
        config["before"],
        config["target"],
        changes,
        read_blob,
        tool_sources=tool_sources,
    )
    config.update(plan)
    recovery_policy = coordinated_policy()
    recovery = (
        recovery_policy.selected(config["before"], config["target"], changes, read_blob)
        if recovery_policy
        else None
    )
    description_raw = read_blob(config["target"], RELEASE_DESCRIPTION)
    previous_description = read_blob(config["before"], RELEASE_DESCRIPTION)
    sql_files = {}
    mge_contracts = None
    if recovery:
        if description_raw != previous_description:
            raise ValueError("Coordinated recovery cannot combine another SQL descriptor.")
        if read_sql_blob is None:
            raise ValueError("Exact recovery SQL acquisition required before drain.")
        config["sql"], sql_files = recovery_policy.sql_payload(
            recovery, config["sql_environment"], read_sql_blob
        )
        config["recovery_seed"] = "live_sql_observation_v1"
    elif description_raw != previous_description:
        if description_raw is None:
            raise ValueError("Removing a combined release description requires review.")
        description = combined_description(description_raw, config["before"])
        if read_sql_blob is None:
            raise ValueError("Exact SQL source acquisition required before drain.")
        from services.export_execution_dal import INSTALLATION_OBJECTS
        from services.export_runtime_composition import application_contract_scope

        bot = previous["bot-template.json"]
        scope = application_contract_scope(bot["application_sql_contract"])
        if scope is None:
            raise ValueError(
                "Whole-database startup SQL contract needs a separately reviewed upgrade."
            )
        if description["profile"] == "mge_finalisation_v1":
            transition = (
                mge_portable_application_contract_transition
                if description["version"] == 2
                else mge_application_contract_transition
            )
            mge_contracts = transition(previous, description)
            # Only application-scope parents receive this reviewed amendment.
            # Installation/legacy protection remains independent and unchanged.
            scope = set(scope) - MGE_APPLICATION_PARENTS
        protected = set(INSTALLATION_OBJECTS) | set(scope)
        protected.update(m["name"] for m in bot["legacy_sql_contract"]["source"]["modules"])
        principals = {
            bot[k]["principal"]
            for k in ("sql_contract", "legacy_sql_contract", "application_sql_contract")
        }
        config["sql"], sql_files = combined_payload(
            description,
            read_sql_blob,
            protected_objects=protected,
            protected_principals=principals,
        )
    seed = release_seed(
        previous,
        plan["new_pins"],
        observation["gate"],
        policy_path=config["old_policy"]["Path"],
        policy_sha256=config["old_policy"]["SHA256"],
    )
    if recovery:
        seed = recovery_policy.adapt_candidate(seed, recovery)
    elif mge_contracts is not None:
        from scripts.p0a_release import adapt_candidate

        seed = adapt_candidate(seed, mge_contracts)
    config["release_id"] = str(uuid4())
    config["seed_members"] = [
        dict(name=name, sha256=sha256(raw)) for name, raw in sorted(seed.items())
    ]
    config["new_policy"] = json.loads(seed["AutomaticStartupPolicy.json"])
    config["new_policy_sha256"] = sha256(seed["AutomaticStartupPolicy.json"])
    config["new_seed_directory"] = str(
        PureWindowsPath(config["new_policy"]["seed_plan"]["path"]).parent
    )
    config["new_state_directory"] = config["new_policy"]["state_directory"]
    config["old_pins"] = previous["AutomaticStartupPolicy.json"]["source_hashes"]
    config["flags"] = previous["AutomaticStartupPolicy.json"]["flags"]
    files = dict(seed)
    files.update(sql_files)
    files["Release-Step.ps1"] = (tools / "K98-SourceUpdate.ps1").read_bytes()
    files["Verify-NewPair.py"] = (tools / "verify_k98_update_pair.py").read_bytes()
    files["EmptyGitConfig.txt"] = b""
    files["contract_verifier.zip"] = archive
    config["extra_members"] = [
        dict(name="Verify-NewPair.py", sha256=sha256(files["Verify-NewPair.py"])),
        dict(name="contract_verifier.zip", sha256=sha256(archive)),
    ]
    if recovery:
        files["Verify-RecoverySeed.py"] = (tools / "recovery_release_seed.py").read_bytes()
        config["extra_members"].append(
            dict(
                name="Verify-RecoverySeed.py",
                sha256=sha256(files["Verify-RecoverySeed.py"]),
            )
        )
    # Flat payload names keep the runner's bounded inventory and avoid archive
    # extraction. Every target path is separately validated by the adapter.
    for index, member in enumerate(config["source_members"]):
        if not member["deleted"]:
            member["payload"] = f"source-{index:04d}.bin"
            files[member["payload"]] = payload[member["path"]]
    files["ReleaseBindings.json"] = encode(config)
    binding_hash = sha256(files["ReleaseBindings.json"])

    def invocation(action) -> dict[str, Any]:
        return dict(
            file="Release-Step.ps1",
            arguments=dict(Action=action, ExpectedBindingsSHA256=binding_hash),
        )

    manifest: dict[str, Any] = dict(
        version=4,
        release_id=config["release_id"],
        host=config["host"],
        application_sid=config["sid"],
        repository=config["root"],
        policy=dict(path=config["old_policy"]["Path"], sha256=config["old_policy"]["SHA256"]),
        issuer_launcher=dict(
            path=config["old_plan"]["Python"], sha256=config["old_plan"]["PythonSHA256"]
        ),
        members=[dict(name=name, sha256=sha256(raw)) for name, raw in sorted(files.items())],
        preflight=invocation("Preflight"),
        steps=[
            dict(id=kind, kind=kind, apply=invocation(apply), verify=invocation(verify))
            for kind, apply, verify in (
                ("source", "ApplySource", "VerifySource"),
                ("seed", "ApplySeed", "VerifySeed"),
                ("start", "ApplyStart", "VerifyStart"),
                ("readiness", "AwaitReadiness", "VerifyReadiness"),
            )
        ],
    )
    if sql_files:

        def sql_invocation(action, migration_id):
            call = invocation(action)
            call["arguments"]["MigrationId"] = migration_id
            return call

        manifest["steps"][:0] = [
            dict(
                id=f"sql-{index:02d}",
                kind="sql",
                apply=sql_invocation("ApplySql", item["id"]),
                verify=sql_invocation("VerifySql", item["id"]),
            )
            for index, item in enumerate(config["sql"]["profiles"])
        ]
    # Validate before writing anything, including the fixed-adapter member bound.
    # The installed companion is authenticated by Update-K98. Loading that copy
    # also supports upgrading from a predecessor whose validator lacks v4.
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "k98_release_validator", tools / "prepare_k98_release.py"
    )
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)

    validator.validate_updater_manifest(manifest)
    manifest_raw = encode(manifest)
    if len(manifest_raw) > 65536:
        raise ValueError("Encoded release exceeds runner's 64 KiB bound.")
    destination = Path(destination)
    mkdir, write = output_writers(config["sid"], secure_output=secure_output)
    mkdir(destination)
    # Match the existing packager's exact canonical manifest protocol while
    # creating native administrative custody atomically, before any bytes exist.
    package = destination / "package"
    mkdir(package)
    for name, raw in files.items():
        write(package / name, raw)
    runner_raw = (tools / "Deploy-K98Release.ps1").read_bytes()
    write(package / "release.json", manifest_raw)
    write(package / "Deploy-K98Release.ps1", runner_raw)
    result = dict(
        stage="RELEASE_PACKET_PREPARED_NOT_INSTALLED",
        release_id=config["release_id"],
        manifest=str((package / "release.json").resolve()),
        manifest_sha256=sha256(manifest_raw),
        runner_sha256=sha256(runner_raw),
        files=len(files) + 2,
        production_changed=False,
    )
    result.update(target=config["target"], before=config["before"], bindings_sha256=binding_hash)
    write(destination / "prepared.json", encode(result))
    return result


def output_writers(sid, *, secure_output):
    if not secure_output:

        def mkdir(path):
            path.mkdir(exist_ok=False)

        def write(path, raw):
            with path.open("xb") as stream:
                stream.write(raw)

        return mkdir, write
    import win32file

    from core.export_startup_windows import (
        _attributes,
        administrative_path,
        create_private_directory,
        write_new_protected,
    )

    if not re.fullmatch(r"S-1-5-21-(?:[0-9]+-){3}[0-9]+", sid):
        raise ValueError("Canonical application SID required.")

    def mkdir(path):
        create_private_directory(path, sid)

    def write(path, raw):
        if raw:
            write_new_protected(path, raw, sid)
            return
        # The Git configuration sentinel is the only empty member; retain the
        # same atomic ACL and exclusive creation as the existing startup helper.
        administrative_path(path.parent, private=True)
        handle = win32file.CreateFile(
            str(path), 0x40000000, 0, _attributes(sid), 1, 0x80000000, None
        )
        try:
            win32file.FlushFileBuffers(handle)
        finally:
            handle.Close()
        administrative_path(path, private=True)

    return mkdir, write


def main():
    import argparse
    import os
    import subprocess

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observation", required=True)
    parser.add_argument("--observation-sha256", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with Path(args.observation).open("rb") as stream:
        raw = stream.read(4 * 1024 * 1024 + 1)
    if hashlib.sha256(raw).hexdigest() != args.observation_sha256:
        raise ValueError("Protected observation changed after bootstrap")
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("Installed observation exceeds bound.")
    observation = json.loads(raw)
    config = observation["bindings"]
    before, target = config["before"], config["target"]
    if any(not re.fullmatch(r"[0-9a-f]{40}", value) for value in (before, target)):
        raise ValueError("Exact commit binding required.")
    environment = {
        key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")
    }
    environment.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_NO_REPLACE_OBJECTS="1",
        GIT_ATTR_NOSYSTEM="1",
    )

    def git(*arguments, data=None):
        result = subprocess.run(
            [
                config["git_path"],
                "--no-optional-locks",
                "-c",
                "core.hooksPath=NUL",
                "-c",
                "core.fsmonitor=false",
                "-c",
                f"safe.directory={config['root'].replace(chr(92), '/')}",
                "-C",
                config["root"],
                *arguments,
            ],
            input=data,
            capture_output=True,
            check=True,
            timeout=60,
            env=environment,
        )
        return result.stdout

    changes = (
        git("diff", "--no-renames", "--name-only", "-z", before, target)
        .decode("utf-8")
        .rstrip("\0")
        .split("\0")
    )
    recovery_policy = coordinated_policy()
    possible_recovery = (
        recovery_policy.possible_paths(before, changes) if recovery_policy else set()
    )
    # Known mixed modules require authenticated before/target blobs below. All
    # other forbidden paths still fail before acquisition. source_plan performs
    # the mandatory structural comparison before creating a release package.
    check_source_only(
        [
            path
            for path in changes
            if path not in APPLICATION_METHODS
            and path not in transition_paths()
            and path not in possible_recovery
        ],
        tool_copies=TOOL_SOURCE_PATHS,
    )
    requested = sorted(
        set(changes)
        | transition_paths()
        | {RELEASE_DESCRIPTION}
        | set(observation["seed"]["AutomaticStartupPolicy.json"]["source_hashes"])
    )
    objects = {}
    complete_inventory = set()
    for commit in (before, target):
        tree = git("ls-tree", "-r", "-l", "-z", commit)
        if len(tree) > 4 * 1024 * 1024:
            raise ValueError("Git tree inventory exceeds bound.")
        wanted = set(requested)
        for entry in tree.rstrip(b"\0").split(b"\0"):
            header, path_raw = entry.split(b"\t", 1)
            path = path_raw.decode("utf-8")
            complete_inventory.add(path)
            if path not in wanted:
                continue
            mode, kind, oid, length = header.split()
            if (
                mode not in {b"100644", b"100755"}
                or kind != b"blob"
                or int(length) > 2 * 1024 * 1024
            ):
                raise ValueError(f"Unsupported source object: {path}")
            objects[(commit, path)] = (oid, int(length))
    # ls-tree already supplies the full bounded inventories. Include unchanged
    # docs/assets/etc. before filtering blobs, since their directory spelling
    # controls what the case-insensitive checkout and bootstrap will see.
    check_case_aliases(complete_inventory)
    if sum(size for _, size in objects.values()) > 128 * 1024 * 1024:
        raise ValueError("Git source inventory exceeds bound.")
    # One subprocess for all blobs avoids per-file process startup overhead.
    keys = list(objects)
    batch = git("cat-file", "--batch", data=b"".join(objects[key][0] + b"\n" for key in keys))
    offset, blobs = 0, {}
    for key in keys:
        end = batch.index(b"\n", offset)
        oid, kind, size = batch[offset:end].split()
        expected_oid, expected_size = objects[key]
        if oid != expected_oid or kind != b"blob" or int(size) != expected_size:
            raise ValueError("Git object changed during preparation.")
        offset = end + 1
        content = batch[offset : offset + expected_size]
        if (
            len(content) != expected_size
            or batch[offset + expected_size : offset + expected_size + 1] != b"\n"
        ):
            raise ValueError("Truncated Git object stream.")
        blobs[key] = content
        offset += expected_size + 1
    if offset != len(batch):
        raise ValueError("Unexpected Git object stream suffix.")
    read_sql_blob: Callable[[str], bytes] | None = None
    description_raw = blobs.get((target, RELEASE_DESCRIPTION))
    recovery = (
        recovery_policy.selected(
            before, target, changes, lambda commit, path: blobs.get((commit, path))
        )
        if recovery_policy
        else None
    )
    description = None
    if recovery:
        if description_raw != blobs.get((before, RELEASE_DESCRIPTION)):
            raise ValueError("Recovery cannot combine a separate SQL descriptor.")
        description = dict(sql_commit=recovery["sql"]["commit"])
    elif description_raw != blobs.get((before, RELEASE_DESCRIPTION)):
        if description_raw is None:
            raise ValueError("Removing a combined release description requires review.")
        description = combined_description(description_raw, before)
    if description is not None:
        # Acquire SQL into a separate Git database, never merge its history into
        # Bot or select SQL main as the release target. The exact pin must be on main.
        sql_root = Path(args.output + "-sql")
        mkdir, _ = output_writers(config["sid"], secure_output=True)
        mkdir(sql_root)
        helper = config["credential_manager"].replace("\\", "/").replace(" ", "\\ ")

        def sql_git(*arguments):
            return subprocess.run(
                [
                    config["git_path"],
                    "-c",
                    "core.hooksPath=NUL",
                    "-c",
                    "core.fsmonitor=false",
                    "-c",
                    f"safe.directory={sql_root.as_posix()}",
                    "-c",
                    "credential.helper=",
                    "-c",
                    f"credential.helper={helper}",
                    "-C",
                    str(sql_root),
                    *arguments,
                ],
                capture_output=True,
                check=True,
                timeout=120,
                env=environment,
            ).stdout

        sql_git("init", "--bare")
        sql_git(
            "fetch",
            "--no-tags",
            "--no-recurse-submodules",
            "https://github.com/cwatts6/K98-bot-SQL-Server.git",
            "refs/heads/main:refs/heads/main",
        )
        sql_git("merge-base", "--is-ancestor", description["sql_commit"], "refs/heads/main")

        def acquired_sql_blob(path):
            ordinary_path(path)
            ref = description["sql_commit"] + ":" + path
            size = int(sql_git("cat-file", "-s", ref))
            if size > 2 * 1024 * 1024:
                raise ValueError(f"SQL source object exceeds bound: {path}")
            return sql_git("cat-file", "blob", ref)

        read_sql_blob = acquired_sql_blob

    result = prepare_update(
        observation,
        changes,
        lambda commit, path: blobs.get((commit, path)),
        args.output,
        Path(__file__).parent,
        secure_output=True,
        read_sql_blob=read_sql_blob,
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
