"""Explicit first-release action boundary; discovery and receipts remain intact."""

from copy import deepcopy
from types import MappingProxyType

# A release may narrow fresh dispatch, never erase a previously accepted repair.
# New adapter actions are withheld until deliberately added with acceptance proof.
P0A_ACTIONS = MappingProxyType(
    {
        "evidence_batch": frozenset(),
        "historical_batch": frozenset(),
        "export_rollover": frozenset(
            {
                "continue_unstarted_rollover",
                "verify_rollover",
                "isolate_targets",
                "choose_replacements",
                "verify_replacements",
                "finish_replacement_check",
                "discard_replacement_check",
                "activate_replacements",
                "start_replacement_rollover",
                "verify_replacement_rollover",
            }
        ),
        "recovery_overview": frozenset(),
        "queue_admission": frozenset({"withdraw_queued", "close_withdrawn_read"}),
        "unowned_sql_hold": frozenset({"clear_unowned_hold"}),
        "player_report": frozenset(
            {
                "cancel_report",
                "resume_capture",
                "queue_capture",
                "abandon_capture",
                "complete_cache_only",
            }
        ),
        "all_kvk_capture": frozenset({"resume_capture", "queue_capture", "abandon_capture"}),
        "export_job": frozenset(
            {
                "retry_unstarted",
                "skip_unstarted",
                "retire_failed_export",
                "allow_next_export",
                "isolate_targets",
                "choose_replacements",
                "verify_replacements",
                "finish_replacement_check",
                "discard_replacement_check",
                "activate_replacements",
                "publish_replacement",
                "verify_publication",
                "retry_absent",
                "rebuild_damaged",
            }
        ),
        "private_evidence": frozenset(
            {"protect_evidence", "restore_evidence", "attest_containment", "attest_registration"}
        ),
        "configuration_read": frozenset({"release_read", "contain_read"}),
        "producer_refusal": frozenset(
            {
                "close_unstarted_admission",
                "resume_sql_stage",
                "resume_current_registration",
                "cancel_saved_stage",
            }
        ),
        "configuration_producer": frozenset(
            {
                "cancel_configuration",
                "resume_capture",
                "queue_capture",
                "abandon_capture",
                "complete_configuration_only",
            }
        ),
        "configuration_continuation": frozenset(
            {"retry_configuration", "continue_configuration_export", "keep_prior"}
        ),
        "configuration_read_continuation": frozenset(
            {"retry_configuration", "continue_configuration_export", "keep_prior"}
        ),
        "player_report_continuation": frozenset({"refresh_report", "refresh_cache", "keep_prior"}),
        # A resumed admission hands off here. Only proven rollback or completed
        # SQL output is included; accepting incomplete reports is not completion.
        "stats_report_continuation": frozenset({"continue_reports"}),
        "processing_pipeline": frozenset({"continue_stage", "verify_stage", "retain_stage"}),
        "unreceipted_producer": frozenset({"retain_unknown"}),
        "legacy_configuration_continuation": frozenset({"retry_configuration", "keep_prior"}),
        "stats_import": frozenset(
            {
                "release_failure",
                "resume_capture",
                "queue_capture",
                "abandon_capture",
                "retire_historical_export",
                "supersede_partial",
            }
        ),
    }
)


def p0a_presentation(row):
    """Filter a detached presentation without rewriting evidence or its hash."""
    result = deepcopy(row)
    evidence = result["evidence"]
    actions = evidence["actions"]
    allowed = P0A_ACTIONS.get(result["SourceKind"], frozenset())
    withheld = sorted(set(actions) - allowed)
    evidence["actions"] = {key: value for key, value in actions.items() if key in allowed}
    if result["State"] != "resolved" and (withheld or result["SourceKind"] not in P0A_ACTIONS):
        result["release_notice"] = (
            "This incident is being monitored, but this repair is not enabled in the first "
            "release (P0a). It remains part of the required full release (P0b). "
            "Its evidence and access protection are retained. Recheck updates the diagnosis; "
            "it does not unlock a repair that this release cannot perform."
        )
        if evidence["actions"]:
            result["release_notice"] = (
                "The repair buttons shown here are available after their displayed checks. "
                "Additional repairs for this incident remain required P0b work and are not "
                "enabled yet. Recheck refreshes the diagnosis; it does not enable those repairs."
            )
        if row.get("pending_action"):
            result["release_notice"] += (
                " The previously accepted repair will still be reconciled and verified; "
                "it will not be dispatched a second time."
            )
    return result
