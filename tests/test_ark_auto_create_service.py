from __future__ import annotations

from datetime import UTC, datetime, time

import pytest

from ark import ark_auto_create_service as svc


class DummyClient:
    pass


@pytest.mark.asyncio
async def test_sync_ark_matches_from_calendar_creates_missing_match(monkeypatch):
    now = datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    captured = {}

    async def _get_config():
        return {"SignupCloseDay": "Friday", "SignupCloseTimeUtc": "18:00"}

    async def _fetch_candidates(*, window_start, window_end):
        captured["window_start"] = window_start
        captured["window_end"] = window_end
        return [
            {
                "InstanceID": 16464,
                "Title": "Ark k98A Saturday 20:00",
                "EndUTC": datetime(2026, 4, 4, 0, 0, tzinfo=UTC),
            }
        ]

    async def _get_alliance(alliance):
        assert alliance == "k98A"
        return {"RegistrationChannelId": 111, "ConfirmationChannelId": 222}

    async def _get_match_by_alliance_weekend(alliance, ark_weekend_date):
        assert alliance == "k98A"
        assert ark_weekend_date.isoformat() == "2026-04-04"
        return None

    async def _create_match(req):
        captured["req"] = req
        return 77

    class _Controller:
        def __init__(self, *, match_id, config):
            captured["controller_match_id"] = match_id
            captured["controller_config"] = config

        async def ensure_registration_message(self, **kwargs):
            captured["ensure_kwargs"] = kwargs
            return type("Ref", (), {"channel_id": 111, "message_id": 999})()

    monkeypatch.setattr(svc, "get_config", _get_config)
    monkeypatch.setattr(svc, "fetch_ark_calendar_candidates", _fetch_candidates)
    monkeypatch.setattr(svc, "get_alliance", _get_alliance)
    monkeypatch.setattr(svc, "get_match_by_alliance_weekend", _get_match_by_alliance_weekend)
    monkeypatch.setattr(svc, "create_match", _create_match)
    monkeypatch.setattr(svc, "ArkRegistrationController", _Controller)

    result = await svc.sync_ark_matches_from_calendar(client=DummyClient(), now_utc=now)

    assert result.scanned == 1
    assert result.created == 1
    assert result.errors == 0
    assert captured["req"].alliance == "k98A"
    assert captured["req"].match_day == "Sat"
    assert captured["req"].match_time_utc == time(20, 0)
    assert captured["req"].calendar_instance_id == 16464
    assert captured["req"].created_source == "calendar_auto"
    assert captured["ensure_kwargs"]["announce"] is True
    assert captured["ensure_kwargs"]["target_channel_id"] == 111


@pytest.mark.asyncio
async def test_sync_ark_matches_from_calendar_skips_cancelled_existing_match(monkeypatch):
    async def _get_config():
        return {"SignupCloseDay": "Friday", "SignupCloseTimeUtc": "18:00"}

    async def _fetch_candidates(*, window_start, window_end):
        return [
            {
                "InstanceID": 16464,
                "Title": "Ark k98A Saturday 20:00",
                "EndUTC": datetime(2026, 4, 4, 0, 0, tzinfo=UTC),
            }
        ]

    async def _get_alliance(_alliance):
        return {"RegistrationChannelId": 111, "ConfirmationChannelId": 222}

    async def _get_match_by_alliance_weekend(_alliance, _ark_weekend_date):
        return {"MatchId": 88, "Status": "Cancelled"}

    async def _create_match(_req):
        raise AssertionError("create_match should not be called")

    monkeypatch.setattr(svc, "get_config", _get_config)
    monkeypatch.setattr(svc, "fetch_ark_calendar_candidates", _fetch_candidates)
    monkeypatch.setattr(svc, "get_alliance", _get_alliance)
    monkeypatch.setattr(svc, "get_match_by_alliance_weekend", _get_match_by_alliance_weekend)
    monkeypatch.setattr(svc, "create_match", _create_match)

    result = await svc.sync_ark_matches_from_calendar(
        client=DummyClient(), now_utc=datetime(2026, 3, 23, 12, 0, tzinfo=UTC)
    )

    assert result.scanned == 1
    assert result.created == 0
    assert result.skipped_cancelled_match == 1
    assert result.errors == 0


def test_parse_ark_calendar_title_happy_path():
    parsed = svc.parse_ark_calendar_title("Ark k98A Saturday 20:00")

    assert parsed is not None
    assert parsed.alliance == "k98A"
    assert parsed.match_day_display == "Saturday"
    assert parsed.match_day_short == "Sat"
    assert parsed.match_time_utc == time(20, 0)


def test_parse_ark_calendar_title_invalid_returns_none():
    assert svc.parse_ark_calendar_title("Ark Saturday 20:00") is None
    assert svc.parse_ark_calendar_title("Ark k98A Funday 20:00") is None
