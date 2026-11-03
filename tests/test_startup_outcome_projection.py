"""Pure feature interpretation must never confuse a child boolean with completion."""

import pytest

from services.startup_outcome_projection import project


@pytest.mark.parametrize(
    "label,value,expected",
    [
        ("proc_config_import", {"import_reported_success": True}, "succeeded"),
        ("proc_config_import", {"import_reported_success": False}, "unknown"),
        (
            "build_player_stats_cache",
            {"kind": "player_cache_readback", "last_kvk_state": "failed"},
            "partial",
        ),
        (
            "build_player_stats_cache",
            {
                "kind": "player_cache_readback",
                "last_kvk_state": "succeeded",
                "last_kvk_verification": "original_snapshot",
            },
            "succeeded",
        ),
        (
            "warm_profile_cache",
            {
                "execution": "succeeded",
                "availability": "loaded_populated",
                "persistence": "failed_preserved",
            },
            "partial",
        ),
        (
            "warm_name_cache",
            {
                "execution": "succeeded",
                "availability": "loaded_populated",
                "persistence": "not_applicable",
            },
            "succeeded",
        ),
        (
            "rehydrate_tracked_views",
            {"restoration_status": "complete", "attached": 21},
            "succeeded",
        ),
        ("rehydrate_tracked_views", {"restoration_status": "partial", "failed": 1}, "partial"),
        ("rehydrate_vote_post_views", {"success": True}, "unknown"),
    ],
)
def test_only_explicit_verification_contracts_establish_outcome(label, value, expected):
    assert project(label, value, checked=True)["feature_outcome"] == expected
    assert project(label, value, checked=False)["feature_outcome"] == "not_checked"
    assert project(label, value, checked=True, error=True)["feature_outcome"] == "unknown"


@pytest.mark.parametrize("label", ["warm_profile_cache", "warm_name_cache"])
@pytest.mark.parametrize("persistence", [None, "future_value", "unconfirmed"])
def test_unknown_persistence_cannot_establish_feature_success(label, persistence):
    result = project(
        label,
        {"execution": "succeeded", "availability": "loaded_populated", "persistence": persistence},
        checked=True,
    )
    assert result["feature_outcome"] == "unknown"


@pytest.mark.parametrize("availability", [None, "future_value", "unavailable"])
def test_unknown_data_availability_cannot_establish_feature_success(availability):
    result = project(
        "warm_profile_cache",
        {"execution": "succeeded", "availability": availability, "persistence": "saved"},
        checked=True,
    )
    assert result["feature_outcome"] == "unknown"


def test_untrusted_objects_are_not_inspected():
    class Hostile:
        def __getattribute__(self, name):
            raise AssertionError("No properties")

        def __repr__(self):
            raise AssertionError("No repr")

    assert (
        project("warm_profile_cache", Hostile(), checked=True)["feature_outcome"] == "not_checked"
    )


@pytest.mark.parametrize(
    "persistence",
    ["saved", "failed_preserved", "not_applicable", "unchanged", "verified_on_disk", "unconfirmed"],
)
def test_current_persistence_vocabulary_survives_projection_and_sink(persistence):
    from uuid import uuid4

    from services.operation_diagnostics import DiagnosticSink
    from tests.test_recovery_evidence_bundle import event

    projected = project(
        "warm_profile_cache",
        {"execution": "succeeded", "availability": "loaded_empty", "persistence": persistence},
        checked=True,
    )
    assert projected["persistence_outcome"] == persistence
    sink = DiagnosticSink()
    sink._accept(event(uuid4().hex, "completed", "warm_profile_cache", **projected))
    assert len(sink.records) == 1
