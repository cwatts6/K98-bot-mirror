"""Pure projections of already-returned verifications; never run a verifier here."""


def project(label, completion, *, checked=False, error=False):
    result = {"feature_outcome": "unknown" if error else "not_checked"}
    if label == "proc_config_import" and error == "ProcConfigImportFailed":
        return {"feature_outcome": "failed"}
    if error or not checked or type(completion) is not dict:
        return result
    result["feature_outcome"] = "unknown"
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
        if execution == "succeeded":
            result["feature_outcome"] = (
                "partial" if persistence == "failed_preserved" else "succeeded"
            )
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
    return result
