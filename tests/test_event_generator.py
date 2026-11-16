from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

import pytest

from event_calendar.event_generator import (
    compute_effective_hash,
    load_overrides,
    write_event_instances,
)


def test_load_overrides_rejects_invalid_action():
    class _Cur:
        description: ClassVar[tuple[tuple[str], ...]] = (
            ("OverrideID",),
            ("IsActive",),
            ("TargetKind",),
            ("TargetID",),
            ("TargetOccurrenceStartUTC",),
            ("ActionType",),
            ("NewStartUTC",),
            ("NewEndUTC",),
            ("NewTitle",),
            ("NewVariant",),
            ("NewEmoji",),
            ("NewImportance",),
            ("NewDescription",),
            ("NewLinkURL",),
            ("NewChannelID",),
            ("NewSignupURL",),
            ("NewTags",),
        )

        def execute(self, *_a, **_k):
            return None

        def fetchall(self):
            return [
                (
                    "ov1",
                    1,
                    "rule",
                    "r1",
                    None,
                    "noop",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                )
            ]

    class _Conn:
        def cursor(self):
            return _Cur()

    with pytest.raises(ValueError, match="action must be cancel\\|modify"):
        load_overrides(_Conn())


class _RecordingCursor:
    description: ClassVar[tuple[tuple[str], ...]] = (("InstanceID",), ("EffectiveHash",))

    def __init__(self, existing_rows):
        self.existing_rows = list(existing_rows)
        self.executed: list[tuple[str, tuple]] = []

    def execute(self, sql, *params):
        self.executed.append((sql.strip(), params))
        return None

    def fetchall(self):
        return list(self.existing_rows)


class _RecordingConn:
    def __init__(self, existing_rows):
        self._cursor = _RecordingCursor(existing_rows)

    def cursor(self):
        return self._cursor


def test_write_event_instances_reuses_existing_identity_for_unchanged_payload():
    instance = {
        "SourceKind": "oneoff",
        "SourceID": "evt-1",
        "StartUTC": datetime(2026, 3, 20, tzinfo=UTC),
        "EndUTC": datetime(2026, 3, 21, tzinfo=UTC),
        "AllDay": True,
        "Emoji": "🎯",
        "Title": "KE Battle",
        "EventType": "kvk",
        "Variant": "open",
        "Importance": "high",
        "Description": "desc",
        "LinkURL": "https://example.com",
        "ChannelID": "123",
        "SignupURL": "https://example.com/signup",
        "Tags": "alpha,beta",
        "SortOrder": 1,
        "IsCancelled": False,
    }
    existing_hash = compute_effective_hash(dict(instance))
    conn = _RecordingConn(existing_rows=[(42, existing_hash)])

    written = write_event_instances(conn=conn, instances=[dict(instance)])

    assert written == 1
    sql_calls = [sql for sql, _ in conn._cursor.executed]
    assert any("SELECT InstanceID, EffectiveHash" in sql for sql in sql_calls)
    assert any("DELETE FROM dbo.EventInstances" in sql for sql in sql_calls)
    assert any("SET IDENTITY_INSERT dbo.EventInstances ON" in sql for sql in sql_calls)
    preserved_insert = next(
        params
        for sql, params in conn._cursor.executed
        if "INSERT INTO dbo.EventInstances" in sql and "InstanceID" in sql
    )
    assert preserved_insert[0] == 42


def test_write_event_instances_uses_fresh_identity_for_new_payload():
    instance = {
        "SourceKind": "oneoff",
        "SourceID": "evt-2",
        "StartUTC": datetime(2026, 3, 22, tzinfo=UTC),
        "EndUTC": datetime(2026, 3, 23, tzinfo=UTC),
        "AllDay": False,
        "Emoji": None,
        "Title": "Ark Prep",
        "EventType": "ark",
        "Variant": None,
        "Importance": None,
        "Description": None,
        "LinkURL": None,
        "ChannelID": None,
        "SignupURL": None,
        "Tags": None,
        "SortOrder": None,
        "IsCancelled": False,
    }
    conn = _RecordingConn(existing_rows=[])

    written = write_event_instances(conn=conn, instances=[dict(instance)])

    assert written == 1
    assert not any(
        "SET IDENTITY_INSERT dbo.EventInstances ON" in sql for sql, _ in conn._cursor.executed
    )
    non_preserved_insert = next(
        params
        for sql, params in conn._cursor.executed
        if "INSERT INTO dbo.EventInstances" in sql and "InstanceID" not in sql
    )
    assert non_preserved_insert[0] == "oneoff"
