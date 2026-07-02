from __future__ import annotations

import csv
from datetime import UTC, datetime, timedelta
import io

import pytest

from voting import export_service
from voting.models import VoteOption, VoteReminder, VoteSnapshot, VoteVoterAuditRow
from voting.service import VoteValidationError


def _snapshot(*, status: str = "Closed", total_votes: int = 4) -> VoteSnapshot:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    return VoteSnapshot(
        vote_post_id=42,
        guild_id=1,
        channel_id=2,
        message_id=3,
        created_by_discord_user_id=4,
        title="=Best rally time?",
        description="+Pick one",
        status=status,
        allow_vote_change=True,
        launch_mention_everyone=False,
        reminder_mention_everyone=False,
        close_mention_everyone=False,
        opens_at_utc=None,
        closes_at_utc=now - timedelta(minutes=1),
        closed_at_utc=now if status == "Closed" else None,
        closed_by_discord_user_id=99 if status == "Closed" else None,
        closed_reason="deadline" if status == "Closed" else None,
        background_asset_key=None,
        total_votes=total_votes,
        created_at_utc=now - timedelta(hours=1),
        updated_at_utc=now,
        options=(
            VoteOption(10, 42, "opt1", "+18:00 UTC", 1, vote_count=1 if total_votes else 0),
            VoteOption(11, 42, "opt2", "19:00 UTC", 2, vote_count=max(0, total_votes - 1)),
        ),
        reminders=(
            VoteReminder(
                reminder_id=7,
                vote_post_id=42,
                offset_minutes_before_close=60,
                due_at_utc=now - timedelta(hours=1),
                sent_at_utc=now - timedelta(minutes=55),
                message_id=700,
            ),
            VoteReminder(
                reminder_id=8,
                vote_post_id=42,
                offset_minutes_before_close=10,
                due_at_utc=now - timedelta(minutes=10),
                sent_at_utc=None,
                message_id=None,
            ),
        ),
    )


def _voter_audit_rows() -> tuple[VoteVoterAuditRow, ...]:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    return (
        VoteVoterAuditRow(
            vote_post_id=42,
            title="=Best rally time?",
            closed_at_utc=now,
            discord_user_id=123,
            option_id=11,
            option_key="opt2",
            option_label="19:00 UTC",
            original_option_id=10,
            original_option_key="opt1",
            original_option_label="+18:00 UTC",
            vote_created_at_utc=now - timedelta(minutes=30),
            vote_updated_at_utc=now - timedelta(minutes=10),
        ),
        VoteVoterAuditRow(
            vote_post_id=42,
            title="=Best rally time?",
            closed_at_utc=now,
            discord_user_id=456,
            option_id=11,
            option_key="opt2",
            option_label="19:00 UTC",
            original_option_id=11,
            original_option_key="opt2",
            original_option_label="19:00 UTC",
            vote_created_at_utc=now - timedelta(minutes=20),
            vote_updated_at_utc=now - timedelta(minutes=20),
        ),
    )


def test_vote_totals_csv_rows_include_outcome_and_operational_metadata() -> None:
    rows = export_service.vote_totals_csv_rows(_snapshot())

    assert rows[0]["VotePostID"] == 42
    assert rows[0]["OutcomeKind"] == "winner"
    assert rows[0]["OutcomeSummary"].startswith("Winner: 19:00 UTC")
    # architecture-check: allow - expected persisted Discord message URL text.
    assert rows[0]["MessageLink"] == "https://discord.com/channels/1/2/3"
    assert rows[0]["ReminderOffsetsMinutes"] == "60;10"
    assert rows[0]["ReminderSentCount"] == 1
    assert rows[0]["ReminderPendingCount"] == 1
    assert rows[0]["IsWinningOption"] == 0
    assert rows[1]["IsWinningOption"] == 1
    assert rows[1]["VotePercent"] == "75%"


def test_vote_totals_csv_escapes_formula_like_text() -> None:
    csv_bytes = export_service.build_vote_totals_csv_bytes(_snapshot())
    text = csv_bytes.getvalue().decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))

    assert rows[0]["Title"] == "'=Best rally time?"
    assert rows[0]["Description"] == "'+Pick one"
    assert rows[0]["OptionLabel"] == "'+18:00 UTC"
    assert rows[1]["OptionLabel"] == "19:00 UTC"


def test_vote_totals_csv_handles_no_votes() -> None:
    rows = export_service.vote_totals_csv_rows(_snapshot(total_votes=0))

    assert rows[0]["OutcomeKind"] == "no_votes"
    assert rows[0]["OutcomeSummary"] == "No votes were cast."
    assert rows[0]["VotePercent"] == "0%"


@pytest.mark.asyncio
async def test_build_vote_totals_export_rejects_open_vote(monkeypatch) -> None:
    async def fake_get_vote_snapshot(_vote_post_id):
        return _snapshot(status="Open")

    monkeypatch.setattr(export_service.dal, "get_vote_snapshot", fake_get_vote_snapshot)

    with pytest.raises(VoteValidationError, match="Only closed votes"):
        await export_service.build_vote_totals_export(
            vote_post_id=42,
            requested_by_discord_user_id=99,
        )


@pytest.mark.asyncio
async def test_build_vote_totals_export_returns_private_upload_payload(monkeypatch) -> None:
    async def fake_get_vote_snapshot(_vote_post_id):
        return _snapshot()

    monkeypatch.setattr(export_service.dal, "get_vote_snapshot", fake_get_vote_snapshot)

    export = await export_service.build_vote_totals_export(
        vote_post_id=42,
        requested_by_discord_user_id=99,
    )

    assert export.filename.startswith("vote_42_best_rally_time_")
    assert export.filename.endswith(".csv")
    assert export.row_count == 2
    assert export.outcome_kind == "winner"
    assert export.csv_bytes.tell() == 0
    assert export.is_oversized() is False


def test_vote_voter_audit_csv_rows_include_discord_identity_and_change_flag() -> None:
    rows = export_service.vote_voter_audit_csv_rows(
        _voter_audit_rows(),
        discord_names_by_user_id={123: "Planner", 456: "Scout"},
    )

    assert rows[0]["DiscordUserID"] == "'123"
    assert rows[0]["DiscordName"] == "Planner"
    assert rows[0]["OriginalOptionLabel"] == "+18:00 UTC"
    assert rows[0]["VoteChanged"] == 1
    assert rows[1]["DiscordName"] == "Scout"
    assert rows[1]["VoteChanged"] == 0


def test_vote_voter_audit_csv_escapes_formula_like_text_and_unknown_names() -> None:
    csv_bytes = export_service.build_vote_voter_audit_csv_bytes(
        _voter_audit_rows(),
        discord_names_by_user_id={123: "=Planner"},
    )
    text = csv_bytes.getvalue().decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))

    assert rows[0]["Title"] == "'=Best rally time?"
    assert rows[0]["DiscordUserID"] == "'123"
    assert rows[0]["DiscordName"] == "'=Planner"
    assert rows[0]["OriginalOptionLabel"] == "'+18:00 UTC"
    assert rows[1]["DiscordName"] == "Unknown"


@pytest.mark.asyncio
async def test_build_vote_voter_audit_export_rejects_open_vote(monkeypatch) -> None:
    async def fake_get_vote_snapshot(_vote_post_id):
        return _snapshot(status="Open")

    monkeypatch.setattr(export_service.dal, "get_vote_snapshot", fake_get_vote_snapshot)

    with pytest.raises(VoteValidationError, match="Only closed votes"):
        await export_service.build_vote_voter_audit_export(
            vote_post_id=42,
            requested_by_discord_user_id=99,
        )


@pytest.mark.asyncio
async def test_build_vote_voter_audit_export_logs_sql_audit_event(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_get_vote_snapshot(_vote_post_id):
        return _snapshot()

    async def fake_list_vote_voter_audit_rows(_vote_post_id):
        return _voter_audit_rows()

    async def fake_insert_audit(**kwargs):
        captured.update(kwargs)

    async def fake_name_resolver(user_ids):
        assert user_ids == (123, 456)
        return {123: "Planner", 456: "Scout"}

    monkeypatch.setattr(export_service.dal, "get_vote_snapshot", fake_get_vote_snapshot)
    monkeypatch.setattr(
        export_service.dal,
        "list_vote_voter_audit_rows",
        fake_list_vote_voter_audit_rows,
    )
    monkeypatch.setattr(export_service.dal, "insert_audit", fake_insert_audit)

    export = await export_service.build_vote_voter_audit_export(
        vote_post_id=42,
        requested_by_discord_user_id=99,
        discord_name_resolver=fake_name_resolver,
    )

    assert export.filename.startswith("vote_42_best_rally_time_voter_audit_")
    assert export.row_count == 2
    assert export.csv_bytes.tell() == 0
    assert captured["vote_post_id"] == 42
    assert captured["actor_discord_user_id"] == 99
    assert captured["action_type"] == "VoterAuditExported"
    assert captured["details"]["mode"] == "voter_audit"
    assert captured["details"]["row_count"] == 2
    assert captured["details"]["byte_count"] == export.byte_count
    assert captured["details"]["max_upload_bytes"] == export_service.CSV_UPLOAD_MAX_BYTES
    assert captured["details"]["is_oversized"] is False
    assert captured["details"]["delivery_status"] == "ready_for_ephemeral_delivery"
    assert "DiscordName" in captured["details"]["columns"]
