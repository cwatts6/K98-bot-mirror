from __future__ import annotations

from mge import mge_rules_service


def test_update_event_rules_text_preserves_mode(monkeypatch):
    ctx = {
        "EventId": 10,
        "RuleMode": "fixed",
        "RulesText": "old text",
        "SignupEmbedChannelId": 1234,
    }

    monkeypatch.setattr(
        "mge.mge_rules_service.mge_rules_dal.fetch_event_rules_context",
        lambda event_id: ctx,
    )

    captured: dict[str, object] = {}

    def _fake_update(**kwargs):
        captured.update(kwargs)
        return True

    monkeypatch.setattr(
        "mge.mge_rules_service.mge_rules_dal.update_event_rules_text_with_audit",
        _fake_update,
    )

    res = mge_rules_service.update_event_rules_text(
        event_id=10,
        new_rules_text="new text",
        actor_discord_id=999,
    )

    assert res.success is True
    assert captured["new_rule_mode"] == "fixed"
    assert captured["action_type"] == "edit"
    assert captured["new_rules_text"] == "new text"


def test_reset_rules_uses_current_mode_default(monkeypatch):
    ctx = {
        "EventId": 11,
        "RuleMode": "open",
        "RulesText": "custom",
        "SignupEmbedChannelId": 333,
    }

    monkeypatch.setattr(
        "mge.mge_rules_service.mge_rules_dal.fetch_event_rules_context",
        lambda event_id: ctx,
    )
    monkeypatch.setattr(
        "mge.mge_rules_service.mge_rules_dal.fetch_default_rules_text",
        lambda mode: "OPEN DEFAULT" if mode == "open" else None,
    )

    calls: dict[str, object] = {}

    def _fake_update(**kwargs):
        calls.update(kwargs)
        return True

    monkeypatch.setattr(
        "mge.mge_rules_service.mge_rules_dal.update_event_rules_text_with_audit",
        _fake_update,
    )

    res = mge_rules_service.reset_event_rules_to_mode_default(event_id=11, actor_discord_id=42)

    assert res.success is True
    assert calls["new_rule_mode"] == "open"
    assert calls["new_rules_text"] == "OPEN DEFAULT"
    assert calls["action_type"] == "reset_to_mode_default"


def test_reset_rules_missing_default(monkeypatch):
    ctx = {"EventId": 12, "RuleMode": "fixed", "RulesText": "x", "SignupEmbedChannelId": None}
    monkeypatch.setattr(
        "mge.mge_rules_service.mge_rules_dal.fetch_event_rules_context",
        lambda event_id: ctx,
    )
    monkeypatch.setattr(
        "mge.mge_rules_service.mge_rules_dal.fetch_default_rules_text",
        lambda mode: None,
    )

    res = mge_rules_service.reset_event_rules_to_mode_default(event_id=12, actor_discord_id=1)
    assert res.success is False
    assert "No active default rules found" in res.message
