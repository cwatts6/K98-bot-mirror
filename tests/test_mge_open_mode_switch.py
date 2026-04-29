from __future__ import annotations

from mge.mge_event_service import switch_event_to_fixed, switch_event_to_open


class _DalStub:
    def __init__(self, status: str = "signup_open", rule_mode: str = "fixed"):
        self.status = status
        self.rule_mode = rule_mode
        self.called_open = False
        self.called_fixed = False

    def fetch_event_switch_context(self, event_id: int):
        return {
            "EventId": event_id,
            "Status": self.status,
            "RuleMode": self.rule_mode,
            "RulesText": "current rules",
        }

    def fetch_open_rule_template(self):
        return "open rules"

    def fetch_fixed_rule_template(self):
        return "fixed rules"

    def apply_open_mode_switch_atomic(self, **kwargs):
        self.called_open = True
        return 4

    def apply_fixed_mode_switch_atomic(self, **kwargs):
        self.called_fixed = True
        return 1


def test_switch_to_open_ok(monkeypatch):
    stub = _DalStub("signup_open", "fixed")
    from mge import mge_event_service as svc

    monkeypatch.setattr(svc, "mge_event_dal", stub)

    result = switch_event_to_open(event_id=1, actor_discord_id=123)

    assert result.success is True
    assert result.deleted_signup_count == 4
    assert stub.called_open is True


def test_switch_to_open_blocked_published(monkeypatch):
    stub = _DalStub("published", "fixed")
    from mge import mge_event_service as svc

    monkeypatch.setattr(svc, "mge_event_dal", stub)

    result = switch_event_to_open(event_id=1, actor_discord_id=123)

    assert result.success is False


def test_switch_to_open_blocked_completed(monkeypatch):
    stub = _DalStub("completed", "fixed")
    from mge import mge_event_service as svc

    monkeypatch.setattr(svc, "mge_event_dal", stub)

    result = switch_event_to_open(event_id=1, actor_discord_id=123)

    assert result.success is False


def test_switch_to_fixed_ok(monkeypatch):
    stub = _DalStub("signup_open", "open")
    from mge import mge_event_service as svc

    monkeypatch.setattr(svc, "mge_event_dal", stub)

    result = switch_event_to_fixed(event_id=2, actor_discord_id=456)

    assert result.success is True
    assert result.updated_row_count == 1
    assert stub.called_fixed is True


def test_switch_to_fixed_uses_fixed_rules(monkeypatch):
    stub = _DalStub("signup_open", "open")
    from mge import mge_event_service as svc

    monkeypatch.setattr(svc, "mge_event_dal", stub)

    captured: dict[str, object] = {}

    def _fake_apply(**kwargs):
        captured.update(kwargs)
        return 1

    stub.apply_fixed_mode_switch_atomic = _fake_apply  # type: ignore[method-assign]

    result = switch_event_to_fixed(event_id=3, actor_discord_id=789)

    assert result.success is True
    assert captured["new_rules_text"] == "fixed rules"
    assert captured["old_rule_mode"] == "open"


def test_switch_to_fixed_blocked_published(monkeypatch):
    stub = _DalStub("published", "open")
    from mge import mge_event_service as svc

    monkeypatch.setattr(svc, "mge_event_dal", stub)

    result = switch_event_to_fixed(event_id=4, actor_discord_id=123)

    assert result.success is False


def test_switch_to_fixed_blocked_completed(monkeypatch):
    stub = _DalStub("completed", "open")
    from mge import mge_event_service as svc

    monkeypatch.setattr(svc, "mge_event_dal", stub)

    result = switch_event_to_fixed(event_id=5, actor_discord_id=123)

    assert result.success is False
