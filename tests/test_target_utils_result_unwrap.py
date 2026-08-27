from __future__ import annotations

import pytest

import file_utils
from kvk.models.kvk_target_row import TargetRow
import target_utils


@pytest.mark.asyncio
async def test_run_target_lookup_unwraps_ok_tuple_from_maintenance(monkeypatch):
    target = {
        "GovernorID": "2441482",
        "GovernorName": "Alice",
        "TargetState": "ACTIVE",
        "KVK_NO": 15,
    }

    async def fake_run_maintenance_with_isolation(*_args, **_kwargs):
        return True, target

    monkeypatch.setattr(
        file_utils,
        "run_maintenance_with_isolation",
        fake_run_maintenance_with_isolation,
        raising=True,
    )

    res = await target_utils.run_target_lookup("2441482")

    assert res == {"status": "found", "data": target}


def test_unwrap_targets_result_accepts_worker_parsed_tuple():
    target = {"GovernorID": "2441482", "TargetState": "ACTIVE"}

    assert target_utils._unwrap_targets_result((target, {"status": "success"})) == target


def test_unwrap_targets_result_raises_for_failed_maintenance_tuple():
    raw_error = "Return code 1. Output:\n" + ("secret-ish output " * 100)

    with pytest.raises(RuntimeError) as exc:
        target_utils._unwrap_targets_result((False, raw_error))

    assert str(exc.value) == "Target maintenance failed"
    assert "secret-ish output" not in str(exc.value)


def test_legacy_target_adapter_prefers_canonical_values_over_aliases():
    adapted = target_utils.adapt_target_row_for_legacy(
        {
            "GovernorID": "2441482",
            "GovernorName": "Canonical",
            "Governor Name": "Legacy",
            "Power": 100,
            "Kill_Target": 200,
            "Kill Target": 999,
            "Deads_Target": 10,
            "DKP_Target": 300,
            "Min_Kill_Target": 50,
            "TargetRank": 1,
            "KVK_NO": 16,
            "TargetState": "OFFICIAL",
        }
    )

    assert adapted is not None
    assert adapted["GovernorName"] == "Canonical"
    assert adapted["Kill_Target"] == 200
    assert adapted["TargetState"] == "OFFICIAL"
    assert "Governor Name" not in adapted
    assert "Kill Target" not in adapted


def test_legacy_target_adapter_serializes_typed_row_to_canonical_keys():
    adapted = target_utils.adapt_target_row_for_legacy(
        TargetRow("2441482", "Alice", 100, 300, 200, 10, 50, 1, 16)
    )

    assert adapted == {
        "GovernorID": "2441482",
        "GovernorName": "Alice",
        "Power": 100,
        "DKP_Target": 300,
        "Kill_Target": 200,
        "Deads_Target": 10,
        "Min_Kill_Target": 50,
        "TargetRank": 1,
        "KVK_NO": 16,
    }


@pytest.mark.asyncio
async def test_run_target_lookup_reports_error_for_failed_maintenance(monkeypatch):
    async def fake_run_maintenance_with_isolation(*_args, **_kwargs):
        return False, "database unavailable"

    monkeypatch.setattr(
        file_utils,
        "run_maintenance_with_isolation",
        fake_run_maintenance_with_isolation,
        raising=True,
    )

    res = await target_utils.run_target_lookup("2441482")

    assert res is not None
    assert res["status"] == "error"
    assert res["message"] == "Internal error retrieving targets by ID"
