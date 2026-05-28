from __future__ import annotations

from datetime import UTC, datetime, timedelta

from mge.mge_event_service import sync_mge_events_from_calendar


def test_sync_creates_event_and_returns_event_ids(monkeypatch):
    now = datetime(2026, 3, 12, 12, 0, tzinfo=UTC)
    start = now + timedelta(days=7, minutes=1)
    end = start + timedelta(days=6)

    class FakeDal:
        inserted = False

        def fetch_calendar_candidates(self, *_):
            return [
                {
                    "InstanceID": 101,
                    "EventType": "MGE",
                    "Variant": "infantry",
                    "StartUTC": start,
                    "EndUTC": end,
                    "Title": "MGE Infantry",
                }
            ]

        def fetch_active_variants(self):
            return [{"VariantId": 1, "VariantName": "Infantry"}]

        def fetch_fixed_rule_template(self):
            return "fixed"

        def fetch_mge_event_by_source(self, _):
            return None if not self.inserted else {"EventId": 11, "RulesText": "fixed"}

        def insert_mge_event(self, **kwargs):
            self.inserted = True
            assert kwargs["signup_close_utc"] == start - timedelta(hours=1)
            return 11

        def touch_event_updated_utc(self, **kwargs):
            return True

    fake = FakeDal()
    monkeypatch.setattr("mge.mge_event_service.mge_event_dal", fake)

    result, ids = sync_mge_events_from_calendar(now_utc=now)
    assert result.created == 1
    assert result.errors == 0
    assert ids == [11]


def test_sync_existing_event_no_duplicate_insert(monkeypatch):
    now = datetime(2026, 3, 12, 12, 0, tzinfo=UTC)
    start = now + timedelta(days=7, minutes=1)
    end = start + timedelta(days=6)

    class FakeDal:
        def fetch_calendar_candidates(self, *_):
            return [
                {
                    "InstanceID": 202,
                    "EventType": "MGE",
                    "Variant": "cavalry",
                    "StartUTC": start,
                    "EndUTC": end,
                    "Title": "MGE Cavalry",
                }
            ]

        def fetch_active_variants(self):
            return [{"VariantId": 2, "VariantName": "Cavalry"}]

        def fetch_fixed_rule_template(self):
            return "fixed"

        def fetch_mge_event_by_source(self, _):
            return {"EventId": 22, "RulesText": "fixed"}

        def insert_mge_event(self, **kwargs):
            raise AssertionError("should not insert")

        def touch_event_updated_utc(self, **kwargs):
            return True

    monkeypatch.setattr("mge.mge_event_service.mge_event_dal", FakeDal())

    result, ids = sync_mge_events_from_calendar(now_utc=now)
    assert result.existing == 1
    assert result.created == 0
    assert ids == [22]
