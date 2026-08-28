from __future__ import annotations

import pytest

from kvk.models.kvk_target_row import TargetRow
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


async def _kills_last_kvk_map():
    return {"9": {"T4&T5_Kills": 50}}


async def _historical_targets_last_kvk_map():
    return {
        "9": {
            "T4&T5_Kills": 75,
            "Kill Target": 50,
            "DKP_SCORE": 120,
            "DKP Target": 100,
        }
    }


def _target_row(
    governor_id: str,
    *,
    governor_name: str = "Target Gov",
    power: int | None = None,
    dkp_target: int | None = None,
    kill_target: int | None = None,
    deads_target: int | None = None,
    min_kill_target: int | None = None,
    kvk_no: int = 15,
) -> TargetRow:
    return TargetRow(
        governor_id=governor_id,
        governor_name=governor_name,
        power=power,
        dkp_target=dkp_target,
        kill_target=kill_target,
        deads_target=deads_target,
        min_kill_target=min_kill_target,
        target_rank=1,
        kvk_no=kvk_no,
    )


def _publication_meta(*, state: str = "OFFICIAL") -> dict[str, object]:
    source_type = "MATCHMAKING_SCAN" if state == "OFFICIAL" else "DRAFTSCAN"
    source_scan = 1059 if state == "OFFICIAL" else 1040
    return {
        "PublicationId": 1,
        "KVK_NO": 15,
        "PublicationState": state,
        "SourceScanOrder": source_scan,
        "SourceScanType": source_type,
        "ConfiguredDraftScan": 1040,
        "ConfiguredMatchmakingScan": 1059,
        "PublishedAtUtc": "2026-06-05T10:30:00+00:00",
        "TargetRowCount": 2,
        "OutputObjectName": "dbo.EXCEL_EXPORT_KVK_TARGETS_15",
        "PublicationVersion": 1,
        "PublicationSignature": "2ad2a141-c5bf-4075-927b-832e44477e55",
        "cache_written_at_utc": "2026-06-05T10:31:00+00:00",
    }


async def test_targets_payload_active_progress(monkeypatch):
    kvk_context = {"kvk_no": 15, "kvk_name": "Tides of War"}
    received_contexts = []
    monkeypatch.setattr(
        service,
        "get_kvk_fighting_context_today",
        lambda: kvk_context,
    )
    monkeypatch.setattr(service, "load_kvk_stats_card_context", _context)

    def fetch_target_entry(gid, received_context):
        received_contexts.append(received_context)
        return (
            _target_row(
                gid,
                power=123_000_000,
                kill_target=20_000_000,
                deads_target=1_000_000,
                dkp_target=50_000_000,
            ),
            _publication_meta(),
        )

    monkeypatch.setattr(
        service.kvk_targets_dal,
        "fetch_target_entry",
        fetch_target_entry,
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

    presentation = await service.build_kvk_targets_presentation_input("2441482")
    payload = presentation.payload

    assert presentation.target_row is not None
    assert presentation.target_row.governor_id == "2441482"
    assert presentation.last_kvk is not None
    assert presentation.last_kvk["Acclaim"] == 4_700_000
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
    assert payload.publication_state == "OFFICIAL"
    assert payload.target_source_scan == 1059
    assert received_contexts == [kvk_context]


async def test_targets_payload_complete(monkeypatch):
    monkeypatch.setattr(service, "get_kvk_fighting_context_today", lambda: {"kvk_no": 15})
    monkeypatch.setattr(service, "load_kvk_stats_card_context", _context)
    monkeypatch.setattr(
        service.kvk_targets_dal,
        "fetch_target_entry",
        lambda gid, _kvk_context=None: (
            _target_row(gid, kill_target=10, deads_target=5, dkp_target=20),
            _publication_meta(),
        ),
    )
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


async def test_targets_payload_reports_no_target_values_for_unset_amounts(monkeypatch):
    monkeypatch.setattr(service, "get_kvk_fighting_context_today", lambda: {"kvk_no": 15})
    monkeypatch.setattr(service, "load_kvk_stats_card_context", _context)
    monkeypatch.setattr(
        service.kvk_targets_dal,
        "fetch_target_entry",
        lambda gid, _kvk_context=None: (
            _target_row(gid, governor_name="Awaiting Targets"),
            _publication_meta(),
        ),
    )
    monkeypatch.setattr(service.kvk_targets_dal, "fetch_exemption_row", lambda *_args: None)
    monkeypatch.setattr(service.stats_cache_helpers, "load_last_kvk_map", _empty_last_kvk_map)
    monkeypatch.setattr(service, "load_stat_row", lambda _gid: None)

    payload = await service.build_kvk_targets_card_payload("1")

    assert payload.target_state == "no_target_values"
    assert payload.status_label == "No target values"
    assert not any(metric.has_target for metric in payload.metrics)


async def test_targets_payload_exempt_uses_sql_contract(monkeypatch):
    monkeypatch.setattr(service, "get_kvk_fighting_context_today", lambda: {"kvk_no": 15})
    monkeypatch.setattr(service, "load_kvk_stats_card_context", _context)
    monkeypatch.setattr(
        service.kvk_targets_dal,
        "fetch_target_entry",
        lambda _gid, _kvk_context=None: (None, _publication_meta()),
    )
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
    monkeypatch.setattr(service, "get_kvk_fighting_context_today", lambda: {"kvk_no": 15})
    monkeypatch.setattr(service, "load_kvk_stats_card_context", _context)
    monkeypatch.setattr(
        service.kvk_targets_dal,
        "fetch_target_entry",
        lambda _gid, _kvk_context=None: (
            _target_row("9", kill_target=100),
            _publication_meta(),
        ),
    )
    monkeypatch.setattr(service.kvk_targets_dal, "fetch_exemption_row", lambda *_args: None)
    monkeypatch.setattr(service.stats_cache_helpers, "load_last_kvk_map", _kills_last_kvk_map)
    monkeypatch.setattr(service, "load_stat_row", lambda _gid: None)

    payload = await service.build_kvk_targets_card_payload("9")

    assert payload.target_state == "active"
    assert payload.metrics[0].current == 50
    assert payload.metrics[0].target == 100


async def test_targets_payload_preserves_historical_denominators_and_minimum_kills(monkeypatch):
    monkeypatch.setattr(service, "get_kvk_fighting_context_today", lambda: {"kvk_no": 15})
    monkeypatch.setattr(service, "load_kvk_stats_card_context", _context)
    monkeypatch.setattr(
        service.kvk_targets_dal,
        "fetch_target_entry",
        lambda _gid, _kvk_context=None: (
            _target_row(
                "9",
                kill_target=100,
                min_kill_target=25,
                dkp_target=200,
            ),
            _publication_meta(),
        ),
    )
    monkeypatch.setattr(service.kvk_targets_dal, "fetch_exemption_row", lambda *_args: None)
    monkeypatch.setattr(
        service.stats_cache_helpers,
        "load_last_kvk_map",
        _historical_targets_last_kvk_map,
    )
    monkeypatch.setattr(service, "load_stat_row", lambda _gid: None)

    payload = await service.build_kvk_targets_card_payload("9")

    kills, _, dkp, _ = payload.metrics
    assert kills.target == 100
    assert kills.comparison_target == 50
    assert kills.percent == 150.0
    assert kills.remaining == 0
    assert dkp.target == 200
    assert dkp.comparison_target == 100
    assert dkp.percent == 120.0
    assert payload.min_kill_target == 25
