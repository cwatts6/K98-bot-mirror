from __future__ import annotations

from datetime import UTC, datetime

import pytest

from voting import dal
from voting.models import VoteCreateRequest
from voting.result_visibility import (
    RESULT_VISIBILITY_HIDDEN_UNTIL_CLOSE,
    RESULT_VISIBILITY_PUBLIC_LIVE,
)


def test_snapshot_from_rows_defaults_missing_result_visibility_to_public_live() -> None:
    now = datetime(2026, 7, 1, 12, 0)

    snapshot = dal._snapshot_from_rows(
        {
            "VotePostID": 42,
            "GuildID": 1,
            "ChannelID": 2,
            "MessageID": 3,
            "CreatedByDiscordUserID": 4,
            "Title": "Vote",
            "Description": None,
            "Status": "Open",
            "AllowVoteChange": 1,
            "LaunchMentionEveryone": 0,
            "ReminderMentionEveryone": 0,
            "CloseMentionEveryone": 0,
            "OpensAtUtc": None,
            "ClosesAtUtc": now,
            "ClosedAtUtc": None,
            "ClosedByDiscordUserID": None,
            "ClosedReason": None,
            "BackgroundAssetKey": None,
            "TotalVotes": 0,
            "CreatedAtUtc": now,
            "UpdatedAtUtc": now,
        },
        [],
        [],
    )

    assert snapshot.result_visibility == RESULT_VISIBILITY_PUBLIC_LIVE


@pytest.mark.asyncio
async def test_create_vote_post_persists_result_visibility_and_audit(monkeypatch) -> None:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    captured: list[tuple[str, tuple[object, ...]]] = []

    class _Cursor:
        def execute(self, sql, params=()):
            captured.append((str(sql), tuple(params)))

        def fetchone(self):
            return (42,)

    async def fake_run_blocking_in_thread(_sync_func, callback, *, name):
        assert name == "vote_create"
        return callback(_Cursor())

    monkeypatch.setattr(dal, "run_blocking_in_thread", fake_run_blocking_in_thread)

    vote_post_id = await dal.create_vote_post(
        VoteCreateRequest(
            guild_id=1,
            channel_id=2,
            created_by_discord_user_id=3,
            title="Vote",
            description=None,
            options=("A", "B"),
            closes_at_utc=now,
            reminder_offsets_minutes=(),
            result_visibility=RESULT_VISIBILITY_HIDDEN_UNTIL_CLOSE,
        )
    )

    assert vote_post_id == 42
    vote_post_insert = captured[0]
    assert "ResultVisibility" in vote_post_insert[0]
    assert vote_post_insert[0].count("?") == len(vote_post_insert[1])
    assert RESULT_VISIBILITY_HIDDEN_UNTIL_CLOSE in vote_post_insert[1]
    assert "VoteMode" in vote_post_insert[0]
    assert "MinSelections" in vote_post_insert[0]
    assert "MaxSelections" in vote_post_insert[0]
    audit_insert = captured[-1]
    assert "VotePostAudit" in audit_insert[0]
    assert '"result_visibility": "HiddenUntilClose"' in str(audit_insert[1])
    assert '"vote_mode": "OneChoice"' in str(audit_insert[1])


@pytest.mark.asyncio
async def test_search_closed_vote_posts_filters_to_closed_votes(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_run_query_async(sql, params=()):
        captured["sql"] = sql
        captured["params"] = params
        return [
            {
                "VotePostID": 42,
                "Title": "Best rally time?",
                "Status": "Closed",
                "ChannelID": 5,
                "ClosesAtUtc": datetime(2026, 7, 1, 20, 0),
                "ClosedAtUtc": datetime(2026, 7, 1, 21, 0),
            }
        ]

    monkeypatch.setattr(dal, "run_query_async", fake_run_query_async)

    choices = await dal.search_closed_vote_posts("rally", limit=99)

    assert "Status = 'Closed'" in str(captured["sql"])
    assert "MessageID IS NOT NULL" in str(captured["sql"])
    assert captured["params"] == (25, "rally", "%rally%", None)
    assert choices[0].vote_post_id == 42
    assert choices[0].closed_at_utc == datetime(2026, 7, 1, 21, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_list_vote_voter_audit_rows_maps_current_and_original_options(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_run_query_async(sql, params=()):
        captured["sql"] = sql
        captured["params"] = params
        return [
            {
                "VotePostID": 42,
                "Title": "Best rally time?",
                "ClosedAtUtc": datetime(2026, 7, 1, 21, 0),
                "DiscordUserID": 123,
                "OptionID": 11,
                "OptionKey": "opt2",
                "OptionLabel": "19:00 UTC",
                "OriginalOptionID": 10,
                "OriginalOptionKey": "opt1",
                "OriginalOptionLabel": "18:00 UTC",
                "VoteCreatedAtUtc": datetime(2026, 7, 1, 20, 0),
                "VoteUpdatedAtUtc": datetime(2026, 7, 1, 20, 30),
            }
        ]

    async def fake_run_one_async(sql, params=()):
        assert "VoteMode" in str(sql)
        assert params == (42,)
        return {"VoteMode": "OneChoice"}

    monkeypatch.setattr(dal, "run_one_async", fake_run_one_async)
    monkeypatch.setattr(dal, "run_query_async", fake_run_query_async)

    rows = await dal.list_vote_voter_audit_rows(42)

    assert "FROM dbo.VotePostVotes" in str(captured["sql"])
    assert "JOIN dbo.VotePostOptions o" in str(captured["sql"])
    assert "LEFT JOIN dbo.VotePostOptions original" in str(captured["sql"])
    assert captured["params"] == (42,)
    assert rows[0].discord_user_id == 123
    assert rows[0].option_label == "19:00 UTC"
    assert rows[0].original_option_label == "18:00 UTC"
    assert rows[0].vote_updated_at_utc == datetime(2026, 7, 1, 20, 30, tzinfo=UTC)


@pytest.mark.asyncio
async def test_list_vote_voter_audit_rows_maps_multi_select_rows(monkeypatch) -> None:
    now = datetime(2026, 7, 1, 21, 0)
    captured: list[str] = []

    async def fake_run_one_async(sql, params=()):
        assert "VoteMode" in str(sql)
        assert params == (42,)
        return {"VoteMode": "MultiSelect"}

    async def fake_run_query_async(sql, params=()):
        captured.append(str(sql))
        assert params == (42,)
        if "VotePostMultiSelectVotes" in str(sql):
            return [
                {
                    "VotePostID": 42,
                    "Title": "Availability?",
                    "ClosedAtUtc": now,
                    "DiscordUserID": 123,
                    "OriginalOptionIDsJson": "[10, 11]",
                    "VoteCreatedAtUtc": now,
                    "VoteUpdatedAtUtc": now,
                    "OptionID": 11,
                    "OptionKey": "opt2",
                    "OptionLabel": "19:00 UTC",
                },
                {
                    "VotePostID": 42,
                    "Title": "Availability?",
                    "ClosedAtUtc": now,
                    "DiscordUserID": 123,
                    "OriginalOptionIDsJson": "[10, 11]",
                    "VoteCreatedAtUtc": now,
                    "VoteUpdatedAtUtc": now,
                    "OptionID": 12,
                    "OptionKey": "opt3",
                    "OptionLabel": "20:00 UTC",
                },
            ]
        return [
            {"OptionID": 10, "OptionKey": "opt1", "Label": "18:00 UTC"},
            {"OptionID": 11, "OptionKey": "opt2", "Label": "19:00 UTC"},
            {"OptionID": 12, "OptionKey": "opt3", "Label": "20:00 UTC"},
        ]

    monkeypatch.setattr(dal, "run_one_async", fake_run_one_async)
    monkeypatch.setattr(dal, "run_query_async", fake_run_query_async)

    rows = await dal.list_vote_voter_audit_rows(42)

    assert any("FROM dbo.VotePostMultiSelectVotes" in sql for sql in captured)
    assert rows[0].selected_option_ids == (11, 12)
    assert rows[0].selected_option_labels == ("19:00 UTC", "20:00 UTC")
    assert rows[0].original_option_ids == (10, 11)
    assert rows[0].original_option_labels == ("18:00 UTC", "19:00 UTC")


@pytest.mark.asyncio
async def test_cast_multi_select_vote_replaces_selection_set_and_audits(monkeypatch) -> None:
    now = datetime(2026, 7, 1, 21, 0, tzinfo=UTC)
    executed: list[tuple[str, tuple[object, ...]]] = []

    class _Cursor:
        description = None

        def __init__(self) -> None:
            self._rows: list[tuple[object, ...]] = []

        def execute(self, sql, params=()):
            text = str(sql)
            executed.append((text, tuple(params)))
            if "FROM dbo.VotePosts WITH" in text:
                self.description = [
                    ("VotePostID",),
                    ("Status",),
                    ("AllowVoteChange",),
                    ("ClosesAtUtc",),
                    ("VoteMode",),
                    ("MinSelections",),
                    ("MaxSelections",),
                ]
                self._rows = [
                    (
                        42,
                        "Open",
                        1,
                        (now.replace(tzinfo=None) + datetime.resolution),
                        "MultiSelect",
                        1,
                        2,
                    )
                ]
            elif "FROM dbo.VotePostOptions" in text and "IN" in text:
                self.description = [("OptionID",)]
                self._rows = [(11,), (12,)]
            elif "FROM dbo.VotePostMultiSelectVotes WITH" in text:
                self.description = [("DiscordUserID",), ("OriginalOptionIDsJson",)]
                self._rows = [(123, "[10]")]
            elif "FROM dbo.VotePostMultiSelectSelections WITH" in text:
                self.description = [("OptionID",)]
                self._rows = [(10,)]
            else:
                self.description = None
                self._rows = []

        def fetchone(self):
            return self._rows.pop(0) if self._rows else None

        def fetchall(self):
            rows = self._rows
            self._rows = []
            return rows

    async def fake_run_blocking_in_thread(_sync_func, callback, *, name):
        assert name == "vote_multi_select_cast"
        return callback(_Cursor())

    monkeypatch.setattr(dal, "run_blocking_in_thread", fake_run_blocking_in_thread)

    result = await dal.cast_multi_select_vote(
        vote_post_id=42,
        option_ids=(11, 12),
        discord_user_id=123,
        now_utc=now,
    )

    assert result.status == "changed"
    assert result.selected_option_ids == (11, 12)
    assert result.previous_option_ids == (10,)
    assert any("DELETE FROM dbo.VotePostMultiSelectSelections" in sql for sql, _ in executed)
    assert sum("INSERT INTO dbo.VotePostMultiSelectSelections" in sql for sql, _ in executed) == 2
    audit = next(params for sql, params in executed if "INSERT INTO dbo.VotePostAudit" in sql)
    assert "MultiSelectVoteChanged" in audit
    assert '"option_ids": [11, 12]' in str(audit)
