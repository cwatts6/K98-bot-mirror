from __future__ import annotations

import json

from mge.dal import mge_event_dal
from mge.mge_event_service import switch_event_to_fixed, switch_event_to_open


class _DalStub:
    def __init__(
        self,
        status: str = "signup_open",
        rule_mode: str = "fixed",
        event_mode: str = "controlled",
    ):
        self.status = status
        self.rule_mode = rule_mode
        self.event_mode = event_mode
        self.called_open = False
        self.called_fixed = False

    def fetch_event_switch_context(self, event_id: int):
        return {
            "EventId": event_id,
            "EventMode": self.event_mode,
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
    stub = _DalStub("signup_open", "open", "open")
    from mge import mge_event_service as svc

    monkeypatch.setattr(svc, "mge_event_dal", stub)

    result = switch_event_to_fixed(event_id=2, actor_discord_id=456)

    assert result.success is True
    assert result.updated_row_count == 1
    assert stub.called_fixed is True


def test_switch_to_fixed_uses_fixed_rules(monkeypatch):
    stub = _DalStub("signup_open", "open", "open")
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
    stub = _DalStub("published", "open", "open")
    from mge import mge_event_service as svc

    monkeypatch.setattr(svc, "mge_event_dal", stub)

    result = switch_event_to_fixed(event_id=4, actor_discord_id=123)

    assert result.success is False


def test_switch_to_fixed_blocked_completed(monkeypatch):
    stub = _DalStub("completed", "open", "open")
    from mge import mge_event_service as svc

    monkeypatch.setattr(svc, "mge_event_dal", stub)

    result = switch_event_to_fixed(event_id=5, actor_discord_id=123)

    assert result.success is False


def test_switch_to_open_skips_when_already_open(monkeypatch):
    stub = _DalStub("signup_open", "open", "open")
    from mge import mge_event_service as svc

    monkeypatch.setattr(svc, "mge_event_dal", stub)

    result = switch_event_to_open(event_id=6, actor_discord_id=123)

    assert result.success is True
    assert result.changed is False
    assert stub.called_open is False


def test_switch_to_fixed_skips_when_already_controlled(monkeypatch):
    stub = _DalStub("signup_open", "fixed", "controlled")
    from mge import mge_event_service as svc

    monkeypatch.setattr(svc, "mge_event_dal", stub)

    result = switch_event_to_fixed(event_id=7, actor_discord_id=123)

    assert result.success is True
    assert result.changed is False
    assert stub.called_fixed is False


def test_switch_context_query_includes_event_mode():
    assert "EventMode" in mge_event_dal.SQL_SELECT_EVENT_SWITCH_CONTEXT


class _OpenSwitchCursor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self.rowcount = 0
        self._last_sql = ""

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> None:
        self._last_sql = " ".join(sql.split())
        self.calls.append((self._last_sql, params))
        if "DELETE FROM dbo.MGE_Awards" in self._last_sql:
            self.rowcount = 2
        elif "DELETE FROM dbo.MGE_Signups" in self._last_sql:
            self.rowcount = 3
        elif self._last_sql.startswith("UPDATE dbo.MGE_Events"):
            self.rowcount = 1
        else:
            self.rowcount = 0

    def fetchone(self) -> tuple[int] | None:
        if self._last_sql.startswith("SELECT EventId FROM dbo.MGE_Events"):
            return (563,)
        if "SELECT COUNT_BIG(1) AS DeletedAwardCount" in self._last_sql:
            return (2,)
        return None


def test_apply_open_switch_deletes_only_target_event_awards_before_signups(monkeypatch):
    cursor = _OpenSwitchCursor()
    actor_discord_id = 559076207627468807

    def _fake_exec_with_cursor(callback):
        return callback(cursor)

    monkeypatch.setattr(mge_event_dal, "exec_with_cursor", _fake_exec_with_cursor)

    deleted = mge_event_dal.apply_open_mode_switch_atomic(
        event_id=563,
        actor_discord_id=actor_discord_id,
        old_rule_mode="fixed",
        old_rules_text="old rules",
        new_rules_text="open rules",
    )

    assert deleted == 3

    sql_calls = [sql for sql, _ in cursor.calls]
    award_delete_idx = next(
        i for i, sql in enumerate(sql_calls) if "DELETE FROM dbo.MGE_Awards" in sql
    )
    signup_delete_idx = next(
        i for i, sql in enumerate(sql_calls) if "DELETE FROM dbo.MGE_Signups" in sql
    )

    assert award_delete_idx < signup_delete_idx

    award_delete_sql, award_delete_params = cursor.calls[award_delete_idx]
    signup_delete_sql, signup_delete_params = cursor.calls[signup_delete_idx]

    assert "OUTPUT" in award_delete_sql
    assert "INTO @DeletedAwards" in award_delete_sql
    assert "INSERT INTO dbo.MGE_AwardAudit" in award_delete_sql
    assert "SELECT COUNT_BIG(1) AS DeletedAwardCount" in award_delete_sql
    assert "WHERE EventId = ?" in award_delete_sql
    assert "WHERE EventId = ?" in signup_delete_sql
    assert award_delete_params[0] == 563
    assert award_delete_params[1] == actor_discord_id
    award_details = json.loads(award_delete_params[2])
    assert award_details == {"action": "bulk_delete_open_switch"}
    assert signup_delete_params == (563,)

    signup_audit_sql, signup_audit_params = next(
        (sql, params) for sql, params in cursor.calls if "INSERT INTO dbo.MGE_SignupAudit" in sql
    )
    assert "bulk_delete_open_switch" in signup_audit_sql
    details = json.loads(str(signup_audit_params[2]))
    assert details["deleted_signup_count"] == 3
    assert details["deleted_award_count"] == 2
