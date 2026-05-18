from __future__ import annotations

import pytest

import file_utils
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
