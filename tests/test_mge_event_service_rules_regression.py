from __future__ import annotations

from datetime import UTC, datetime, timedelta

from mge import mge_event_service


def test_sync_uses_fixed_default_rules(monkeypatch):
    now = datetime(2026, 3, 16, tzinfo=UTC)

    monkeypatch.setattr(
        "mge.mge_event_service.mge_event_dal.fetch_calendar_candidates",
        lambda start, end: [
            {
                "InstanceID": 1001,
                "EventType": "MGE",
                "Variant": "infantry",
                "Title": "MGE Infantry",
                "StartUTC": now + timedelta(days=7),
                "EndUTC": now + timedelta(days=13),
            }
        ],
    )
    monkeypatch.setattr(
        "mge.mge_event_service.mge_event_dal.fetch_active_variants",
        lambda: [{"VariantId": 1, "VariantName": "Infantry"}],
    )
    monkeypatch.setattr(
        "mge.mge_event_service.mge_event_dal.fetch_fixed_rule_template",
        lambda: "FIXED_DEFAULT_RULES",
    )
    monkeypatch.setattr(
        "mge.mge_event_service.mge_event_dal.fetch_mge_event_by_source",
        lambda source_id: None,
    )

    inserted: dict[str, object] = {}

    def _fake_insert(**kwargs):
        inserted.update(kwargs)
        return 501

    monkeypatch.setattr("mge.mge_event_service.mge_event_dal.insert_mge_event", _fake_insert)

    result, event_ids = mge_event_service.sync_mge_events_from_calendar(now_utc=now)

    assert result.created == 1
    assert event_ids == [501]
    assert inserted["rules_text"] == "FIXED_DEFAULT_RULES"


def test_switch_to_open_uses_open_default_rules(monkeypatch):
    monkeypatch.setattr(
        "mge.mge_event_service.mge_event_dal.fetch_event_switch_context",
        lambda event_id: {"Status": "signup_open", "RuleMode": "fixed", "RulesText": "OLD"},
    )
    monkeypatch.setattr(
        "mge.mge_event_service.mge_event_dal.fetch_open_rule_template",
        lambda: "OPEN_DEFAULT_RULES",
    )

    captured: dict[str, object] = {}

    def _fake_apply(**kwargs):
        captured.update(kwargs)
        return 3

    monkeypatch.setattr(
        "mge.mge_event_service.mge_event_dal.apply_open_mode_switch_atomic",
        _fake_apply,
    )

    res = mge_event_service.switch_event_to_open(event_id=700, actor_discord_id=9999)

    assert res.success is True
    assert captured["new_rules_text"] == "OPEN_DEFAULT_RULES"


def test_switch_to_fixed_uses_fixed_default_rules(monkeypatch):
    monkeypatch.setattr(
        "mge.mge_event_service.mge_event_dal.fetch_event_switch_context",
        lambda event_id: {"Status": "signup_open", "RuleMode": "open", "RulesText": "OLD"},
    )
    monkeypatch.setattr(
        "mge.mge_event_service.mge_event_dal.fetch_fixed_rule_template",
        lambda: "FIXED_DEFAULT_RULES",
    )

    captured: dict[str, object] = {}

    def _fake_apply(**kwargs):
        captured.update(kwargs)
        return 1

    monkeypatch.setattr(
        "mge.mge_event_service.mge_event_dal.apply_fixed_mode_switch_atomic",
        _fake_apply,
    )

    res = mge_event_service.switch_event_to_fixed(event_id=701, actor_discord_id=9998)

    assert res.success is True
    assert captured["new_rules_text"] == "FIXED_DEFAULT_RULES"
    assert captured["old_rule_mode"] == "open"
