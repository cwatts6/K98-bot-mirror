from __future__ import annotations

from datetime import UTC, datetime

from event_calendar.cache_contract import build_event_calendar_cache_payload


def test_build_event_calendar_cache_payload_happy_path():
    payload = build_event_calendar_cache_payload(
        events=[
            {
                "instance_id": 123,
                "title": "Mightiest Governor",
                "emoji": "👑",
                "type": "mge",
                "variant": "archer",
                "start_utc": datetime(2026, 3, 23, 0, 0, tzinfo=UTC),
                "end_utc": datetime(2026, 3, 29, 0, 0, tzinfo=UTC),
                "all_day": True,
                "importance": "major",
                "description": "desc",
                "link_url": "https://example.com",
                "channel_id": "1479421257853177938",
                "tags": "alliance,pve",
            }
        ],
        horizon_days=365,
        generated_utc=datetime(2026, 3, 6, 12, 0, tzinfo=UTC),
    )

    assert payload["horizon_days"] == 365
    assert payload["generated_utc"].startswith("2026-03-06T12:00:00")
    assert len(payload["events"]) == 1
    assert payload["events"][0]["tags"] == ["alliance", "pve"]
    assert payload["events"][0]["instance_id"] == "123"


def test_build_event_calendar_cache_payload_skips_invalid_rows():
    payload = build_event_calendar_cache_payload(
        events=[
            {"instance_id": "bad", "title": "No datetimes"},
            {
                "instance_id": "ok",
                "title": "Valid",
                "start_utc": datetime(2026, 3, 6, 20, 0, tzinfo=UTC),
                "end_utc": datetime(2026, 3, 6, 20, 30, tzinfo=UTC),
            },
        ]
    )

    assert len(payload["events"]) == 1
    assert payload["events"][0]["instance_id"] == "ok"
