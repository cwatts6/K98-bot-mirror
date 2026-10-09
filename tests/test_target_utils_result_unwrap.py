from __future__ import annotations

import pytest

from kvk.models.kvk_target_row import TargetRow
from kvk.models.kvk_targets_card import KvkTargetsCardPayload, KvkTargetsPresentationInput
import target_utils


def _presentation(
    *,
    target_row: TargetRow | None,
    progress_state: str = "active",
) -> KvkTargetsPresentationInput:
    return KvkTargetsPresentationInput(
        payload=KvkTargetsCardPayload(
            governor_id="2441482",
            governor_name="Alice",
            kvk_no=16,
            kvk_name="Tides of War",
            camp_name=None,
            progress_state=progress_state,
            status_label="Target review",
            status_detail="Target details",
            next_action="Act",
            power=100,
            metrics=(),
            publication_state="OFFICIAL",
            publication_reason="matchmaking_source_confirmed",
            target_source_scan=1059,
            target_source_type="MATCHMAKING_SCAN",
            target_published_at="2026-08-26 19:22 UTC",
            publication_version=1,
            publication_signature="sig-1",
        ),
        target_row=target_row,
        last_kvk={"KVK_NO": 15, "T4&T5_Kills": 50},
    )


@pytest.mark.asyncio
async def test_run_target_lookup_uses_service_owned_presentation_input(monkeypatch):
    target_row = TargetRow("2441482", "Alice", 100, 300, 200, 10, 50, 1, 16)
    calls: list[str] = []

    async def fake_build(governor_id):
        calls.append(str(governor_id))
        return _presentation(target_row=target_row)

    monkeypatch.setattr(target_utils, "build_kvk_targets_presentation_input", fake_build)

    result = await target_utils.run_target_lookup("2441482")

    assert calls == ["2441482"]
    assert result is not None
    assert result["status"] == "found"
    assert result["data"]["GovernorID"] == "2441482"
    assert result["data"]["TargetState"] == "OFFICIAL"
    assert result["data"]["last_kvk"]["KVK_NO"] == 15


@pytest.mark.asyncio
async def test_name_lookup_routes_resolved_id_through_same_target_service(monkeypatch):
    target_row = TargetRow("2441482", "Alice", 100, 300, 200, 10, 50, 1, 16)
    calls: list[str] = []

    async def fake_lookup(_query):
        return {
            "status": "found",
            "data": {"GovernorID": "2441482", "GovernorName": "Alice"},
        }

    async def fake_build(governor_id):
        calls.append(str(governor_id))
        return _presentation(target_row=target_row)

    monkeypatch.setattr(target_utils, "lookup_governor_id", fake_lookup)
    monkeypatch.setattr(target_utils, "build_kvk_targets_presentation_input", fake_build)

    result = await target_utils.run_target_lookup("Alice")

    assert calls == ["2441482"]
    assert result is not None
    assert result["status"] == "found"
    assert result["data"]["GovernorName"] == "Alice"


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
async def test_run_target_lookup_reports_service_failure(monkeypatch):
    async def fail_build(_governor_id):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(target_utils, "build_kvk_targets_presentation_input", fail_build)

    result = await target_utils.run_target_lookup("2441482")

    assert result == {"status": "error", "message": "Internal error retrieving targets by ID"}


@pytest.mark.asyncio
async def test_run_target_lookup_preserves_exempt_outcome(monkeypatch):
    async def fake_build(_governor_id):
        return _presentation(target_row=None, progress_state="exempt")

    monkeypatch.setattr(target_utils, "build_kvk_targets_presentation_input", fake_build)

    result = await target_utils.run_target_lookup("2441482")

    assert result == {
        "status": "not_found",
        "message": "Governor Alice is exempt from KVK targets.",
    }
