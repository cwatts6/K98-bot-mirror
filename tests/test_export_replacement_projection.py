from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_replacement_projection import continuation_activation, project_destinations
from services.export_replacement_waiting import WaitingReplacementWorkflow


def history():
    return [
        dict(
            activation_id="first",
            mapping={"old-a": "new-a"},
            registration=dict(
                legacy_configuration=dict(
                    scan_data=dict(destinations=["new-a", "old-b", "unchanged"])
                )
            ),
        ),
        dict(
            activation_id="second",
            mapping={"old-b": "new-b"},
            registration=dict(
                legacy_configuration=dict(
                    scan_data=dict(destinations=["new-a", "new-b", "unchanged"])
                )
            ),
        ),
        dict(
            activation_id="third",
            mapping={"new-a": "newer-a"},
            registration=dict(
                legacy_configuration=dict(
                    scan_data=dict(destinations=["newer-a", "new-b", "unchanged"])
                )
            ),
        ),
    ]


def test_distinct_recoveries_and_recovery_of_a_replacement_compose():
    result = continuation_activation(
        history(), targets=["old-a", "old-b", "unchanged"], consumer="scan_data"
    )
    assert result["mapping"] == {"old-a": "newer-a", "old-b": "new-b", "unchanged": "unchanged"}
    assert result["activation_id"] == "third" and result["queued_continuation"]


def test_existing_delivery_keeps_its_original_activation_after_later_recovery():
    result = continuation_activation(
        history(), targets=["old-a", "old-b", "unchanged"], consumer="scan_data", anchor_id="second"
    )
    assert result["activation_id"] == "second"
    assert result["mapping"]["old-a"] == "new-a"


@pytest.mark.parametrize("fault", ["anchor", "scope", "unchanged", "cycle", "collision"])
def test_unverifiable_or_ambiguous_projection_cannot_continue(fault):
    chain = deepcopy(history())
    args = dict(targets=["old-a", "old-b"], consumer="scan_data")
    if fault == "anchor":
        args["anchor_id"] = "missing"
    elif fault == "scope":
        args["targets"].append("foreign")
    elif fault == "unchanged":
        args["targets"] = ["unchanged"]
    elif fault == "cycle":
        chain[-1]["mapping"] = {"new-a": "old-a"}
    else:
        chain[-1]["mapping"] = {"new-a": "new-b"}
    with pytest.raises(SourceConflict):
        continuation_activation(chain, **args)


def test_partial_blocker_completion_never_exposes_publish():
    snapshot = dict(
        job=dict(ConsumerKind="scan_data"),
        attempts=[],
        streams=[],
        isolated_targets=["old-a"],
        resources=[dict(ResourceKey="destination:old-a", ActiveJobID=None)],
    )
    states = {
        "first": dict(activation=dict(mapping={"old-a": "new-a"}), delivery=dict(resolved=True)),
        "second": dict(activation=None, delivery=None),
    }
    project, continuation = Mock(), Mock()
    workflow = WaitingReplacementWorkflow(
        discovery=SimpleNamespace(account="account", job=lambda _: snapshot),
        continuation=continuation,
        blocking_jobs=lambda *_: ["first", "second"],
        original_workflow=lambda key: SimpleNamespace(_state=lambda _: states[key]),
        project_activation=project,
    )
    state = workflow._state("waiting")
    assert state["activation"] is None and state["blockers"] == ["second"]
    project.assert_not_called()
    continuation.inspect.assert_not_called()


def test_mapping_does_not_mutate_authenticated_history():
    maps = [{"a": "b"}, {"b": "c"}]
    assert project_destinations(["a", "unaffected"], maps) == {"a": "c", "unaffected": "unaffected"}
    assert maps == [{"a": "b"}, {"b": "c"}]


def test_queued_source_follows_replacement_of_replacement_as_complete_pool():
    chain = [
        dict(
            activation_id="first",
            mapping={"old-index": "new-index", "old-slot": "new-slot"},
            registration=dict(pools=[dict(index_file_id="new-index", slot_file_ids=["new-slot"])]),
        ),
        dict(
            activation_id="second",
            mapping={"new-index": "final-index", "new-slot": "final-slot"},
            registration=dict(
                pools=[dict(index_file_id="final-index", slot_file_ids=["final-slot"])]
            ),
        ),
    ]
    result = continuation_activation(
        chain, targets=["old-index", "old-slot"], consumer="new_source"
    )
    assert result["mapping"] == {"old-index": "final-index", "old-slot": "final-slot"}
    assert result["activation_id"] == "second"
    with pytest.raises(SourceConflict, match="registration"):
        continuation_activation(chain, targets=["old-index"], consumer="new_source")
