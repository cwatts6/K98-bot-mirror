from __future__ import annotations

import pytest

from kvk.services import kvk_targets_card_service as service

pytestmark = pytest.mark.asyncio


class _Context:
    kvk_name = "Tides of War"
    camp_name = "Wind"


async def _context(*_args):
    return _Context()


async def _empty_last_kvk_map():
    return {}


async def _acclaim_last_kvk_map():
    return {
        "2441482": {
            "T4&T5_Kills": 12_000_000,
            "Deads_Delta": 1_200_000,
            "DKP_SCORE": 25_000_000,
            "Acclaim": 4_700_000,
        }
    }


async def test_targets_payload_active_progress(monkeypatch):
    monkeypatch.setattr(
        service,
        "get_kvk_context_today",
        lambda: {"kvk_no": 15, "kvk_name": "Tides of War"},
    )
    monkeypatch.setattr(service, "load_kvk_stats_card_context", _context)
    monkeypatch.setattr(
        service.kvk_targets_dal,
        "fetch_target_row",
        lambda gid: {
            "GovernorID": gid,
            "GovernorName": "Target Gov",
            "Power": 123_000_000,
            "Kill_Target": 20_000_000,
            "Deads_Target": 1_000_000,
            "DKP_Target": 50_000_000,
            "KVK_NO": 15,
        },
    )
    monkeypatch.setattr(
        service.kvk_targets_dal,
        "fetch_target_cache_meta",
        lambda: {"generated_at": "2026-06-05T10:30:00+00:00", "state": "ACTIVE"},
    )
    monkeypatch.setattr(service.kvk_targets_dal, "fetch_exemption_row", lambda *_args: None)
    monkeypatch.setattr(
        service.stats_cache_helpers,
        "load_last_kvk_map",
        _acclaim_last_kvk_map,
    )
    monkeypatch.setattr(
        service,
        "load_stat_row",
        lambda gid: {
            "GovernorID": gid,
            "GovernorName": "Stats Gov",
            "T4&T5_Kills": 999,
            "Deads_Delta": 999,
            "DKP_SCORE": 999,
        },
    )

    payload = await service.build_kvk_targets_card_payload("2441482")

    assert payload.governor_name == "Stats Gov"
    assert payload.display_camp == "Wind"
    assert payload.target_state == "active"
    assert payload.status_label == "Target review"
    assert payload.metrics[0].percent == 60.0
    assert payload.metrics[0].remaining == 8_000_000
    assert payload.metrics[1].is_complete is True
    assert payload.metrics[3].label == "Acclaim Target"
    assert payload.metrics[3].current == 4_700_000
    assert "work on the table" in payload.next_action.lower()


async def test_targets_payload_complete(monkeypatch):
    monkeypatch.setattr(service, "get_kvk_context_today", lambda: {"kvk_no": 15})
    monkeypatch.setattr(service, "load_kvk_stats_card_context", _context)
    monkeypatch.setattr(
        service.kvk_targets_dal,
        "fetch_target_row",
        lambda gid: {
            "GovernorID": gid,
            "GovernorName": "Target Gov",
            "Kill_Target": 10,
            "Deads_Target": 5,
            "DKP_Target": 20,
        },
    )
    monkeypatch.setattr(service.kvk_targets_dal, "fetch_target_cache_meta", lambda: {})
    monkeypatch.setattr(service.kvk_targets_dal, "fetch_exemption_row", lambda *_args: None)
    monkeypatch.setattr(service.stats_cache_helpers, "load_last_kvk_map", _empty_last_kvk_map)
    monkeypatch.setattr(
        service,
        "load_stat_row",
        lambda _gid: {
            "GovernorName": "Done Gov",
            "T4&T5_Kills": 10,
            "Deads_Delta": 5,
            "DKP_SCORE": 21,
        },
    )

    payload = await service.build_kvk_targets_card_payload("1")

    assert payload.target_state == "complete"
    assert payload.status_label == "Complete"
    assert all(metric.is_complete for metric in payload.metrics[:3])
    assert payload.metrics[3].note == "Target coming next KVK"


async def test_targets_payload_exempt_uses_sql_contract(monkeypatch):
    monkeypatch.setattr(service, "get_kvk_context_today", lambda: {"kvk_no": 15})
    monkeypatch.setattr(service, "load_kvk_stats_card_context", _context)
    monkeypatch.setattr(service.kvk_targets_dal, "fetch_target_row", lambda _gid: None)
    monkeypatch.setattr(service.kvk_targets_dal, "fetch_target_cache_meta", lambda: {})
    monkeypatch.setattr(
        service.kvk_targets_dal,
        "fetch_exemption_row",
        lambda _gid, _kvk_no: {
            "GovernorID": 7,
            "GovernorName": "Exempt Gov",
            "Exempt": True,
            "KVK_NO": 15,
        },
    )

    payload = await service.build_kvk_targets_card_payload("7")

    assert payload.target_state == "exempt"
    assert payload.status_label == "Exempt"
    assert payload.governor_name == "Exempt Gov"
    assert payload.metrics == ()


async def test_targets_payload_source_unavailable_when_stats_missing(monkeypatch):
    monkeypatch.setattr(service, "get_kvk_context_today", lambda: {"kvk_no": 15})
    monkeypatch.setattr(service, "load_kvk_stats_card_context", _context)
    monkeypatch.setattr(
        service.kvk_targets_dal,
        "fetch_target_row",
        lambda _gid: {"GovernorName": "Target Gov", "Kill_Target": 100, "Kills KVK -1": 50},
    )
    monkeypatch.setattr(service.kvk_targets_dal, "fetch_target_cache_meta", lambda: {})
    monkeypatch.setattr(service.kvk_targets_dal, "fetch_exemption_row", lambda *_args: None)
    monkeypatch.setattr(service.stats_cache_helpers, "load_last_kvk_map", _empty_last_kvk_map)
    monkeypatch.setattr(service, "load_stat_row", lambda _gid: None)

    payload = await service.build_kvk_targets_card_payload("9")

    assert payload.target_state == "active"
    assert payload.metrics[0].current == 50
    assert payload.metrics[0].target == 100
