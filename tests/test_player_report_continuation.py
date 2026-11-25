from contextlib import nullcontext
from copy import deepcopy
import json
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.player_report_continuation import PlayerReportContinuation


def fixture():
    state = dict(
        root={"RequestJson": json.dumps({"request": {"config": {}}})},
        marker={"action": str(uuid4()), "choice": "retry"},
        child={"PreparationID": str(uuid4())},
        current={"scan_data": {}},
        blocker=None,
    )
    dal = Mock()
    dal.serialized.side_effect = lambda _: nullcontext()
    dal.snapshot.side_effect = lambda _: deepcopy(state)

    def record(source, token, marker):
        assert token == digest(state).hex()
        state["marker"] = deepcopy(marker)

    dal.record.side_effect = record
    producer = Mock()
    producer.inspect.return_value = ({"outcome": "cache_only_completed"}, "token", True)
    runner, cache = Mock(), Mock(return_value={"sha256": "a" * 64})
    adapter = PlayerReportContinuation(dal, producer, runner=runner, cache_runner=cache)
    action = dict(
        ActionID=str(uuid4()), ActionKind="refresh_cache", EvidenceHash=digest(state).hex()
    )
    return state, dal, adapter, action


def test_lost_cache_dispatch_fences_late_callback_without_replaying_sql_or_cache():
    state, dal, adapter, action = fixture()
    assert adapter.reconcile("source", action) == "not_applied"
    assert state["marker"]["cache_unacknowledged"] == action["ActionID"]
    with pytest.raises(SourceConflict):
        adapter.execute(
            "source",
            "refresh_cache",
            action["EvidenceHash"],
            "recovery:" + action["ActionID"],
            "Late callback",
        )
    adapter.runner.assert_not_called()
    adapter.cache_runner.assert_not_called()


def test_lost_cache_receipt_acknowledgement_verifies_without_rebuilding():
    state, dal, adapter, action = fixture()
    save = dal.record.side_effect

    def lose_ack(*args):
        save(*args)
        raise TimeoutError("Saved receipt reply lost")

    dal.record.side_effect = lose_ack
    with pytest.raises(TimeoutError):
        adapter.execute(
            "source",
            "refresh_cache",
            action["EvidenceHash"],
            "recovery:" + action["ActionID"],
            "Confirmed",
        )
    dal.record.side_effect = save
    assert adapter.reconcile("source", action) == "verified"
    adapter.cache_runner.assert_called_once()
    adapter.runner.assert_not_called()


def test_cache_failure_keeps_incident_open_and_existing_report_without_sql_replay():
    state, dal, adapter, action = fixture()
    adapter.cache_runner.side_effect = OSError("write refused")
    with pytest.raises(OSError):
        adapter.execute(
            "source",
            "refresh_cache",
            action["EvidenceHash"],
            "recovery:" + action["ActionID"],
            "Confirmed",
        )
    assert adapter.reconcile("source", action) == "not_applied"
    evidence, _, resolved = adapter.inspect("source")
    assert not resolved and "refresh_cache" in evidence["actions"]
    adapter.runner.assert_not_called()
