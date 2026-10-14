from __future__ import annotations

from datetime import UTC, datetime

from mge.dal import mge_signup_dal


class _InsertSignupCursor:
    def __init__(self, event_mode: str):
        self.event_mode = event_mode
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self._last_sql = ""

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> None:
        self._last_sql = " ".join(sql.split())
        self.calls.append((self._last_sql, params))

    def fetchone(self) -> tuple[object, ...] | None:
        if self._last_sql.startswith("SELECT EventMode FROM dbo.MGE_Events"):
            return (self.event_mode,)
        if self._last_sql.startswith("INSERT INTO dbo.MGE_Signups"):
            return (42,)
        return None


def _insert_signup_kwargs() -> dict[str, object]:
    return {
        "event_id": 563,
        "governor_id": 100,
        "governor_name_snapshot": "Gov",
        "discord_user_id": 123,
        "request_priority": "High",
        "preferred_rank_band": "1-5",
        "requested_commander_id": 1,
        "requested_commander_name": "Cmdr",
        "current_heads": 100,
        "kingdom_role": None,
        "gear_text": None,
        "armament_text": None,
        "source": "discord",
        "now_utc": datetime(2026, 5, 11, tzinfo=UTC),
    }


def test_insert_signup_locks_event_and_inserts_only_when_controlled(monkeypatch):
    cursor = _InsertSignupCursor("controlled")

    def _fake_exec_with_cursor(callback):
        return callback(cursor)

    monkeypatch.setattr(mge_signup_dal, "exec_with_cursor", _fake_exec_with_cursor)

    signup_id = mge_signup_dal.insert_signup(**_insert_signup_kwargs())

    assert signup_id == 42
    lock_sql, lock_params = cursor.calls[0]
    insert_sql, insert_params = cursor.calls[1]
    assert "FROM dbo.MGE_Events WITH (UPDLOCK, HOLDLOCK)" in lock_sql
    assert "WHERE EventId = ?" in lock_sql
    assert lock_params == (563,)
    assert "INSERT INTO dbo.MGE_Signups" in insert_sql
    assert insert_params[0] == 563


def test_insert_signup_skips_insert_if_switch_changed_event_to_open(monkeypatch):
    cursor = _InsertSignupCursor("open")

    def _fake_exec_with_cursor(callback):
        return callback(cursor)

    monkeypatch.setattr(mge_signup_dal, "exec_with_cursor", _fake_exec_with_cursor)

    signup_id = mge_signup_dal.insert_signup(**_insert_signup_kwargs())

    assert signup_id is None
    assert len(cursor.calls) == 1
    assert cursor.calls[0][1] == (563,)
