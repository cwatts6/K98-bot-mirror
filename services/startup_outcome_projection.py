"""Pure projections of already-returned verifications; never run a verifier here."""

SOURCES = frozenset(
    {
        "proc_config_import",
        "build_player_stats_cache",
        "warm_profile_cache",
        "warm_name_cache",
        "rehydrate_tracked_views",
    }
)


def project(label, completion, *, checked=False, error=False, pending=False, not_reached=False):
    source = label if type(label) is str and label in SOURCES else "unavailable"
    label = source
    result = {
        "feature_outcome": "unknown" if checked or error else "not_checked",
        "verification_source": source,
        "verification_reason": "no_checker",
    }
    if error:
        result["verification_reason"] = (
            "checker_cancelled" if error == "CancelledError" else "checker_failed"
        )
    elif checked:
        result["verification_reason"] = (
            "not_reached" if not_reached else "pending" if pending else "malformed_result"
        )
    if label == "proc_config_import" and error == "ProcConfigImportFailed":
        result["feature_outcome"] = "failed"
        result["verification_reason"] = "verified"
        return result
    if error or not checked or pending or not_reached or type(completion) is not dict:
        return result
    text_fields = {
        "build_player_stats_cache": ("kind", "last_kvk_state", "last_kvk_verification"),
        "warm_profile_cache": ("execution", "availability", "persistence"),
        "warm_name_cache": ("execution", "availability", "persistence"),
        "rehydrate_tracked_views": ("restoration_status",),
    }.get(label, ())
    # A dict is not sufficient verification: reject malformed consumed fields
    # before hashing/comparing them. Ignore unrelated payloads without inspection.
    if any(type(completion.get(key)) not in (str, type(None)) for key in text_fields):
        return result
    if label == "proc_config_import" and type(completion.get("import_reported_success")) not in (
        bool,
        type(None),
    ):
        return result
    if label == "rehydrate_tracked_views" and any(
        key in completion and (type(completion[key]) is not int or not 0 <= completion[key] < 2**63)
        for key in (
            "attached",
            "pruned",
            "superseded",
            "failed",
            "unattempted",
            "outcome_unconfirmed",
        )
    ):
        return result
    result["feature_outcome"] = "unknown"
    result["verification_reason"] = (
        "incomplete_evidence" if source != "unavailable" else "unsupported_stage"
    )
    if label == "proc_config_import":
        if completion.get("import_reported_success") is True:
            result["feature_outcome"] = "succeeded"
    elif label == "build_player_stats_cache":
        main = completion.get("kind") == "player_cache_readback"
        last = (
            completion.get("last_kvk_state") == "succeeded"
            and completion.get("last_kvk_verification") == "original_snapshot"
        )
        result.update(
            main_cache="succeeded" if main else "unknown",
            last_kvk_cache="succeeded" if last else "unknown",
            feature_outcome="succeeded" if main and last else "partial" if main else "unknown",
        )
    elif label in {"warm_profile_cache", "warm_name_cache"}:
        execution = completion.get("execution")
        available = completion.get("availability")
        persistence = completion.get("persistence")
        result.update(
            data_outcome=(
                available
                if available in {"loaded_populated", "loaded_empty", "unavailable"}
                else "unknown"
            ),
            execution_outcome=execution if execution in {"succeeded", "failed"} else "unknown",
            persistence_outcome=(
                persistence
                if persistence
                in {
                    "saved",
                    "failed_preserved",
                    "not_applicable",
                    "unchanged",
                    "verified_on_disk",
                    "unconfirmed",
                }
                else "unknown"
            ),
        )
        if result["execution_outcome"] == "succeeded" and result["data_outcome"] in {
            "loaded_populated",
            "loaded_empty",
        }:
            if result["persistence_outcome"] == "failed_preserved":
                result["feature_outcome"] = "partial"
            elif result["persistence_outcome"] in {
                "saved",
                "not_applicable",
                "unchanged",
                "verified_on_disk",
            }:
                result["feature_outcome"] = "succeeded"
    elif label == "rehydrate_tracked_views":
        status = completion.get("restoration_status")
        result["restoration_outcome"] = (
            status if status in {"complete", "partial", "cancelled", "unavailable"} else "unknown"
        )
        result["feature_outcome"] = {
            "complete": "succeeded",
            "partial": "partial",
            "cancelled": "unknown",
        }.get(status, "unknown")
        for name in (
            "attached",
            "pruned",
            "superseded",
            "failed",
            "unattempted",
            "outcome_unconfirmed",
        ):
            value = completion.get(name)
            if type(value) is int and 0 <= value < 2**63:
                result["failed_count" if name == "failed" else name] = value
    if result["feature_outcome"] in {"succeeded", "partial", "failed"}:
        result["verification_reason"] = "verified"
    return result
