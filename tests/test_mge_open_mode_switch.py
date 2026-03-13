from __future__ import annotations

from mge.mge_event_service import switch_event_to_open


class _DalStub:
    def __init__(self, status: str = "signup_open"):
        self.status = status
        self.called = False

    def fetch_event_switch_context(self, event_id: int):
        return {
            "EventId": event_id,
            "Status": self.status,
            "RuleMode": "fixed",
            "RulesText": "fixed",
        }

    def fetch_open_rule_template(self):
        return "open rules"

    def apply_open_mode_switch_atomic(self, **kwargs):
        self.called = True
        return 4


def test_switch_to_open_ok(monkeypatch):
    stub = _DalStub("signup_open")
    from mge import mge_event_service as svc

    monkeypatch.setattr(svc, "mge_event_dal", stub)

    result = switch_event_to_open(event_id=1, actor_discord_id=123)

    assert result.success is True
    assert result.deleted_signup_count == 4
    assert stub.called is True


def test_switch_to_open_blocked_published(monkeypatch):
    stub = _DalStub("published")
    from mge import mge_event_service as svc

    monkeypatch.setattr(svc, "mge_event_dal", stub)

    result = switch_event_to_open(event_id=1, actor_discord_id=123)

    assert result.success is False


def test_switch_to_open_blocked_completed(monkeypatch):
    stub = _DalStub("completed")
    from mge import mge_event_service as svc

    monkeypatch.setattr(svc, "mge_event_dal", stub)

    result = switch_event_to_open(event_id=1, actor_discord_id=123)

    assert result.success is False
