# tests/test_registry_dal.py
"""
Unit tests for registry.registry_dal

All tests mock _get_conn() to avoid requiring a real SQL connection.
The DAL is tested in isolation — no service or command layer involved.
"""

import pytest

import registry.dal.registry_dal as dal

# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


class _Cursor:
    """Minimal pyodbc-like cursor."""

    def __init__(self, *, output_row=None, fetchall_rows=None, raise_on_execute=None):
        self._output_row = output_row  # (NewID, ResultCode, ResultMessage)
        self._fetchall_rows = fetchall_rows or []
        self._description = [("col",)] * (len(fetchall_rows[0]) if fetchall_rows else 0)
        self._raise_on_execute = raise_on_execute
        self._fetchone_done = False
        self.executed = []

    @property
    def description(self):
        return self._description

    def execute(self, sql, params=None):
        if self._raise_on_execute:
            raise self._raise_on_execute
        self.executed.append((sql, params))

    def fetchone(self):
        if self._fetchone_done:
            return None
        self._fetchone_done = True
        return self._output_row

    def fetchall(self):
        return self._fetchall_rows

    def nextset(self):
        return False

    def close(self):
        pass


class _Conn:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


def _make_conn(monkeypatch, *, output_row=None, fetchall_rows=None, raise_on_execute=None):
    cur = _Cursor(
        output_row=output_row, fetchall_rows=fetchall_rows, raise_on_execute=raise_on_execute
    )
    conn = _Conn(cur)
    monkeypatch.setattr(dal, "_get_conn", lambda: conn)
    return conn, cur


# ---------------------------------------------------------------------------
# insert()
# ---------------------------------------------------------------------------


def test_insert_success(monkeypatch):
    conn, cur = _make_conn(monkeypatch, output_row=(1001, 0, "Inserted"))
    code, msg = dal.insert(
        discord_user_id=111,
        discord_name="Alice",
        governor_id=2441482,
        governor_name="Chrislos",
        account_type="Main",
    )
    assert code == 0
    assert conn.committed


def test_insert_duplicate_slot_returns_code_1(monkeypatch):
    _make_conn(monkeypatch, output_row=(None, 1, "Slot already active"))
    code, msg = dal.insert(
        discord_user_id=111,
        discord_name="Alice",
        governor_id=9999999,
        governor_name="Someone",
        account_type="Main",
    )
    assert code == 1
    assert "slot" in msg.lower() or msg  # message present


def test_insert_duplicate_governor_returns_code_2(monkeypatch):
    _make_conn(monkeypatch, output_row=(None, 2, "GovernorID already registered"))
    code, msg = dal.insert(
        discord_user_id=222,
        discord_name="Bob",
        governor_id=2441482,
        governor_name="Chrislos",
        account_type="Main",
    )
    assert code == 2


def test_insert_sql_exception_returns_code_9(monkeypatch):
    _make_conn(monkeypatch, raise_on_execute=RuntimeError("DB down"))
    code, msg = dal.insert(
        discord_user_id=111,
        discord_name="Alice",
        governor_id=9999,
        governor_name="Test",
        account_type="Main",
    )
    assert code == 9
    assert "DB down" in msg


# ---------------------------------------------------------------------------
# soft_delete()
# ---------------------------------------------------------------------------


def test_soft_delete_success(monkeypatch):
    conn, _ = _make_conn(monkeypatch, output_row=(None, 0, "Removed"))
    code, msg = dal.soft_delete(discord_user_id=111, account_type="Main")
    assert code == 0
    assert conn.committed


def test_soft_delete_not_found_returns_code_3(monkeypatch):
    _make_conn(monkeypatch, output_row=(None, 3, "No active row found"))
    code, msg = dal.soft_delete(discord_user_id=111, account_type="Alt 1")
    assert code == 3


def test_soft_delete_sql_exception_returns_code_9(monkeypatch):
    conn, _ = _make_conn(monkeypatch, raise_on_execute=RuntimeError("timeout"))
    code, msg = dal.soft_delete(discord_user_id=111, account_type="Main")
    assert code == 9
    assert conn.rolled_back


def test_soft_delete_parses_two_column_output(monkeypatch):
    """
    sp_Registry_SoftDelete returns (ResultCode, ResultMessage) — no leading NewID.
    _read_output_row must handle this correctly without raising ValueError.
    """
    conn, _ = _make_conn(monkeypatch, output_row=(0, "Registration marked as Removed."))
    code, msg = dal.soft_delete(discord_user_id=111, account_type="Alt 1")
    assert code == 0
    assert "Removed" in msg


def test_insert_parses_three_column_output(monkeypatch):
    """
    sp_Registry_Insert returns (NewRegistrationID, ResultCode, ResultMessage).
    Explicit regression test for the 3-column shape.
    """
    conn, _ = _make_conn(monkeypatch, output_row=(1001, 0, "Inserted successfully."))
    code, msg = dal.insert(
        discord_user_id=111,
        discord_name="Alice",
        governor_id=2441482,
        governor_name="Chrislos",
        account_type="Main",
    )
    assert code == 0


# ---------------------------------------------------------------------------
# get_by_discord_id()
# ---------------------------------------------------------------------------


def test_get_by_discord_id_returns_rows(monkeypatch):
    rows = [(111, "Alice", 2441482, "Chrislos", "Main", "Active")]
    cur = _Cursor(fetchall_rows=rows)
    cur._description = [
        ("DiscordUserID",),
        ("DiscordName",),
        ("GovernorID",),
        ("GovernorName",),
        ("AccountType",),
        ("RegistrationStatus",),
    ]
    conn = _Conn(cur)
    monkeypatch.setattr(dal, "_get_conn", lambda: conn)

    result = dal.get_by_discord_id(111)
    assert len(result) == 1
    assert result[0]["AccountType"] == "Main"
    assert result[0]["GovernorID"] == 2441482


def test_get_by_discord_id_raises_on_sql_error(monkeypatch):
    """
    Phase 6 requirement: get_by_discord_id must raise, not silently return [].
    Returning [] on SQL failure makes unavailability indistinguishable from
    "user has no registrations".
    """
    _make_conn(monkeypatch, raise_on_execute=RuntimeError("connection failed"))
    with pytest.raises(RuntimeError, match="connection failed"):
        dal.get_by_discord_id(111)


# ---------------------------------------------------------------------------
# get_all_active()
# ---------------------------------------------------------------------------


def test_get_all_active_raises_on_sql_error(monkeypatch):
    """
    Phase 6 requirement: get_all_active must raise, not silently return [].
    Returning [] would make audit/export silently produce incorrect output.
    """
    _make_conn(monkeypatch, raise_on_execute=RuntimeError("SQL unavailable"))
    with pytest.raises(RuntimeError, match="SQL unavailable"):
        dal.get_all_active()


def test_get_all_active_returns_empty_list_when_no_rows(monkeypatch):
    cur = _Cursor(fetchall_rows=[])
    conn = _Conn(cur)
    monkeypatch.setattr(dal, "_get_conn", lambda: conn)
    result = dal.get_all_active()
    assert result == []


# ---------------------------------------------------------------------------
# get_by_governor_id()
# ---------------------------------------------------------------------------


def test_get_by_governor_id_returns_none_when_not_found(monkeypatch):
    cur = _Cursor(fetchall_rows=[])
    conn = _Conn(cur)
    monkeypatch.setattr(dal, "_get_conn", lambda: conn)
    assert dal.get_by_governor_id(9999999) is None


def test_get_by_governor_id_returns_none_silently_on_sql_error(monkeypatch):
    """
    get_by_governor_id is used as a secondary pre-check only.
    SP constraints protect integrity regardless; silent None is safe here.
    """
    _make_conn(monkeypatch, raise_on_execute=RuntimeError("DB error"))
    result = dal.get_by_governor_id(9999999)
    assert result is None
