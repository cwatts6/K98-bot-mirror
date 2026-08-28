from __future__ import annotations

from player_self_service.dal import user_profile_preference_dal as dal


class _Cursor:
    def __init__(self, row=None) -> None:
        self.row = row
        self.executed = []
        self.description = [
            ("DiscordUserID",),
            ("TimezoneName",),
            ("LocationCountryCode",),
            ("PreferredLanguageTag",),
            ("CreatedAtUtc",),
            ("UpdatedAtUtc",),
            ("UpdatedByDiscordUserID",),
        ]
        self.raise_on_execute = False

    def execute(self, sql, params=()):
        if self.raise_on_execute:
            raise RuntimeError("execute failed")
        self.executed.append((sql, params))

    def fetchone(self):
        return self.row


class _Connection:
    def __init__(self, cursor: _Cursor) -> None:
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_fetch_profile_preference_maps_row(monkeypatch) -> None:
    cursor = _Cursor(row=(42, "Europe/London", "GB", "en-GB", "created", "updated", 42))
    conn = _Connection(cursor)
    monkeypatch.setattr(dal, "_get_conn", lambda: conn)

    row = dal.fetch_profile_preference(42)

    assert row == {
        "DiscordUserID": 42,
        "TimezoneName": "Europe/London",
        "LocationCountryCode": "GB",
        "PreferredLanguageTag": "en-GB",
        "CreatedAtUtc": "created",
        "UpdatedAtUtc": "updated",
        "UpdatedByDiscordUserID": 42,
    }
    assert "DiscordUserProfilePreference" in cursor.executed[0][0]
    assert cursor.executed[0][1] == (42,)
    assert conn.closed is True


def test_fetch_profile_preference_returns_none_for_missing_row(monkeypatch) -> None:
    cursor = _Cursor(row=None)
    conn = _Connection(cursor)
    monkeypatch.setattr(dal, "_get_conn", lambda: conn)

    assert dal.fetch_profile_preference(42) is None
    assert conn.closed is True


def test_upsert_profile_preference_field_is_atomic_and_field_specific(monkeypatch) -> None:
    cursor = _Cursor(row=(42, "Europe/London", "GB", "en-GB", "created", "updated", 42))
    conn = _Connection(cursor)
    monkeypatch.setattr(dal, "_get_conn", lambda: conn)

    row = dal.upsert_profile_preference_field(
        discord_user_id=42,
        field="country",
        value="GB",
        updated_by_discord_user_id=42,
    )

    sql, params = cursor.executed[0]
    assert "SET TRANSACTION ISOLATION LEVEL SERIALIZABLE" in sql
    assert "UPDATE dbo.DiscordUserProfilePreference WITH (UPDLOCK, HOLDLOCK)" in sql
    assert "SET LocationCountryCode = ?" in sql
    assert "INSERT dbo.DiscordUserProfilePreference" in sql
    assert "TimezoneName = ?" not in sql
    assert "PreferredLanguageTag = ?" not in sql
    assert params == ("GB", 42, 42, 42, "GB", 42, 42)
    assert row["LocationCountryCode"] == "GB"
    assert conn.committed is True
    assert conn.closed is True


def test_upsert_profile_preference_rolls_back_and_closes_on_execute_failure(
    monkeypatch,
) -> None:
    cursor = _Cursor()
    cursor.raise_on_execute = True
    conn = _Connection(cursor)
    monkeypatch.setattr(dal, "_get_conn", lambda: conn)

    try:
        dal.upsert_profile_preference_field(
            discord_user_id=42,
            field="timezone",
            value="Europe/London",
            updated_by_discord_user_id=42,
        )
    except RuntimeError as exc:
        assert str(exc) == "execute failed"
    else:
        raise AssertionError("expected execute failure")

    assert conn.rolled_back is True
    assert conn.closed is True


def test_upsert_profile_preference_field_rejects_unknown_field_before_connect(monkeypatch) -> None:
    monkeypatch.setattr(
        dal,
        "_get_conn",
        lambda: (_ for _ in ()).throw(AssertionError("connection should not open")),
    )

    try:
        dal.upsert_profile_preference_field(
            discord_user_id=42,
            field="invalid",  # type: ignore[arg-type]
            value="value",
        )
    except ValueError as exc:
        assert "Unsupported profile preference field" in str(exc)
    else:
        raise AssertionError("expected invalid field rejection")
