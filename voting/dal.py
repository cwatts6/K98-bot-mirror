from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
import json
import logging
from typing import Any

from file_utils import cursor_row_to_dict, fetch_all_dicts, fetch_one_dict, run_blocking_in_thread
from stats_alerts.db import exec_with_cursor, run_query_async, run_one_async
from voting.models import VoteCastResult, VoteCloseResult, VoteCreateRequest, VoteOption, VoteReminder, VoteSnapshot

logger = logging.getLogger(__name__)


def _naive_utc(value: datetime) -> datetime:
    aware = value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    return aware.replace(tzinfo=None)


def _aware_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    if isinstance(value, str):
        text = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    return None


def _bool(value: Any) -> bool:
    return bool(int(value or 0))


def _option_key(index: int) -> str:
    return f"opt{index + 1}"


def _reminder_due_at(closes_at_utc: datetime, offset_minutes: int) -> datetime:
    return closes_at_utc - timedelta(minutes=int(offset_minutes))


def _rows_to_options(rows: Sequence[dict[str, Any]]) -> tuple[VoteOption, ...]:
    return tuple(
        VoteOption(
            option_id=int(row["OptionID"]),
            vote_post_id=int(row["VotePostID"]),
            option_key=str(row.get("OptionKey") or ""),
            label=str(row.get("Label") or ""),
            sort_order=int(row.get("SortOrder") or 0),
            button_style=row.get("ButtonStyle"),
            vote_count=int(row.get("VoteCount") or 0),
        )
        for row in rows
    )


def _rows_to_reminders(rows: Sequence[dict[str, Any]]) -> tuple[VoteReminder, ...]:
    reminders: list[VoteReminder] = []
    for row in rows:
        due_at = _aware_utc(row.get("DueAtUtc"))
        if due_at is None:
            continue
        reminders.append(
            VoteReminder(
                reminder_id=int(row["ReminderID"]),
                vote_post_id=int(row["VotePostID"]),
                offset_minutes_before_close=int(row.get("OffsetMinutesBeforeClose") or 0),
                due_at_utc=due_at,
                sent_at_utc=_aware_utc(row.get("SentAtUtc")),
                message_id=(
                    int(row["MessageID"])
                    if row.get("MessageID") not in (None, "")
                    else None
                ),
            )
        )
    return tuple(reminders)


def _snapshot_from_rows(
    post: dict[str, Any],
    option_rows: Sequence[dict[str, Any]],
    reminder_rows: Sequence[dict[str, Any]],
) -> VoteSnapshot:
    closes_at = _aware_utc(post.get("ClosesAtUtc"))
    created_at = _aware_utc(post.get("CreatedAtUtc"))
    updated_at = _aware_utc(post.get("UpdatedAtUtc"))
    if closes_at is None or created_at is None or updated_at is None:
        raise ValueError("VotePost row is missing required UTC timestamps.")
    return VoteSnapshot(
        vote_post_id=int(post["VotePostID"]),
        guild_id=int(post["GuildID"]),
        channel_id=int(post["ChannelID"]),
        message_id=int(post["MessageID"]) if post.get("MessageID") not in (None, "") else None,
        created_by_discord_user_id=int(post["CreatedByDiscordUserID"]),
        title=str(post.get("Title") or ""),
        description=post.get("Description"),
        status=str(post.get("Status") or ""),
        allow_vote_change=_bool(post.get("AllowVoteChange")),
        launch_mention_everyone=_bool(post.get("LaunchMentionEveryone")),
        reminder_mention_everyone=_bool(post.get("ReminderMentionEveryone")),
        close_mention_everyone=_bool(post.get("CloseMentionEveryone")),
        opens_at_utc=_aware_utc(post.get("OpensAtUtc")),
        closes_at_utc=closes_at,
        closed_at_utc=_aware_utc(post.get("ClosedAtUtc")),
        closed_by_discord_user_id=(
            int(post["ClosedByDiscordUserID"])
            if post.get("ClosedByDiscordUserID") not in (None, "")
            else None
        ),
        closed_reason=post.get("ClosedReason"),
        background_asset_key=post.get("BackgroundAssetKey"),
        total_votes=int(post.get("TotalVotes") or 0),
        created_at_utc=created_at,
        updated_at_utc=updated_at,
        options=_rows_to_options(option_rows),
        reminders=_rows_to_reminders(reminder_rows),
    )


async def create_vote_post(req: VoteCreateRequest) -> int:
    def _callback(cur) -> int:
        now = _naive_utc(datetime.now(UTC))
        cur.execute(
            """
            INSERT INTO dbo.VotePosts
                (
                    GuildID, ChannelID, CreatedByDiscordUserID, Title, Description, Status,
                    AllowVoteChange, LaunchMentionEveryone, ReminderMentionEveryone,
                    CloseMentionEveryone, OpensAtUtc, ClosesAtUtc, BackgroundAssetKey,
                    CreatedAtUtc, UpdatedAtUtc
                )
            OUTPUT INSERTED.VotePostID
            VALUES (?, ?, ?, ?, ?, 'Open', ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                int(req.guild_id),
                int(req.channel_id),
                int(req.created_by_discord_user_id),
                req.title,
                req.description,
                1 if req.allow_vote_change else 0,
                1 if req.launch_mention_everyone else 0,
                1 if req.reminder_mention_everyone else 0,
                1 if req.close_mention_everyone else 0,
                _naive_utc(req.opens_at_utc) if req.opens_at_utc else None,
                _naive_utc(req.closes_at_utc),
                req.background_asset_key,
                now,
                now,
            ),
        )
        row = cur.fetchone()
        vote_post_id = int(row[0]) if row else 0
        for index, label in enumerate(req.options):
            cur.execute(
                """
                INSERT INTO dbo.VotePostOptions
                    (VotePostID, OptionKey, Label, SortOrder, CreatedAtUtc)
                VALUES (?, ?, ?, ?, ?);
                """,
                (vote_post_id, _option_key(index), label, index + 1, now),
            )
        for offset in req.reminder_offsets_minutes:
            due_at = _reminder_due_at(req.closes_at_utc, int(offset))
            cur.execute(
                """
                INSERT INTO dbo.VotePostReminders
                    (VotePostID, OffsetMinutesBeforeClose, DueAtUtc, CreatedAtUtc)
                VALUES (?, ?, ?, ?);
                """,
                (vote_post_id, int(offset), _naive_utc(due_at), now),
            )
        cur.execute(
            """
            INSERT INTO dbo.VotePostAudit
                (VotePostID, ActorDiscordUserID, ActionType, DetailsJson, CreatedAtUtc)
            VALUES (?, ?, 'Created', ?, ?);
            """,
            (
                vote_post_id,
                int(req.created_by_discord_user_id),
                json.dumps({"option_count": len(req.options)}, ensure_ascii=False),
                now,
            ),
        )
        return vote_post_id

    vote_post_id = await run_blocking_in_thread(_create_vote_post_sync, _callback, name="vote_create")
    return int(vote_post_id or 0)


def _create_vote_post_sync(callback) -> Any:
    return exec_with_cursor(callback)


async def update_vote_message(vote_post_id: int, *, channel_id: int, message_id: int) -> bool:
    row = await run_one_async(
        """
        UPDATE dbo.VotePosts
        SET ChannelID = ?,
            MessageID = ?,
            UpdatedAtUtc = SYSUTCDATETIME()
        OUTPUT INSERTED.VotePostID
        WHERE VotePostID = ?;
        """,
        (int(channel_id), int(message_id), int(vote_post_id)),
    )
    return bool(row)


async def get_vote_snapshot(vote_post_id: int) -> VoteSnapshot | None:
    post = await run_one_async(
        """
        SELECT p.*,
               (SELECT COUNT_BIG(1) FROM dbo.VotePostVotes v WHERE v.VotePostID = p.VotePostID) AS TotalVotes
        FROM dbo.VotePosts p
        WHERE p.VotePostID = ?;
        """,
        (int(vote_post_id),),
    )
    if not post:
        return None
    options = await run_query_async(
        """
        SELECT o.OptionID, o.VotePostID, o.OptionKey, o.Label, o.SortOrder, o.ButtonStyle,
               COUNT(v.DiscordUserID) AS VoteCount
        FROM dbo.VotePostOptions o
        LEFT JOIN dbo.VotePostVotes v ON v.OptionID = o.OptionID
        WHERE o.VotePostID = ?
        GROUP BY o.OptionID, o.VotePostID, o.OptionKey, o.Label, o.SortOrder, o.ButtonStyle
        ORDER BY o.SortOrder ASC, o.OptionID ASC;
        """,
        (int(vote_post_id),),
    )
    reminders = await run_query_async(
        """
        SELECT ReminderID, VotePostID, OffsetMinutesBeforeClose, DueAtUtc, SentAtUtc, MessageID
        FROM dbo.VotePostReminders
        WHERE VotePostID = ?
        ORDER BY DueAtUtc ASC, ReminderID ASC;
        """,
        (int(vote_post_id),),
    )
    return _snapshot_from_rows(post, options, reminders)


async def list_open_vote_posts() -> list[VoteSnapshot]:
    rows = await run_query_async(
        """
        SELECT p.*,
               (SELECT COUNT_BIG(1) FROM dbo.VotePostVotes v WHERE v.VotePostID = p.VotePostID) AS TotalVotes
        FROM dbo.VotePosts p
        WHERE p.Status = 'Open'
          AND p.MessageID IS NOT NULL
        ORDER BY p.ClosesAtUtc ASC, p.VotePostID ASC;
        """
    )
    snapshots: list[VoteSnapshot] = []
    for row in rows:
        snapshot = await get_vote_snapshot(int(row["VotePostID"]))
        if snapshot:
            snapshots.append(snapshot)
    return snapshots


async def cast_vote(
    *,
    vote_post_id: int,
    option_id: int,
    discord_user_id: int,
    now_utc: datetime,
) -> VoteCastResult:
    def _callback(cur) -> VoteCastResult:
        now = _naive_utc(now_utc)
        cur.execute(
            """
            SELECT VotePostID, Status, AllowVoteChange, ClosesAtUtc
            FROM dbo.VotePosts WITH (UPDLOCK, HOLDLOCK)
            WHERE VotePostID = ?;
            """,
            (int(vote_post_id),),
        )
        post = fetch_one_dict(cur)
        if not post:
            return VoteCastResult("missing", vote_post_id, message="This vote no longer exists.")
        closes_at = _aware_utc(post.get("ClosesAtUtc"))
        if str(post.get("Status")) != "Open" or (closes_at is not None and now_utc >= closes_at):
            return VoteCastResult("closed", vote_post_id, message="This vote is already closed.")

        cur.execute(
            """
            SELECT OptionID
            FROM dbo.VotePostOptions
            WHERE VotePostID = ? AND OptionID = ?;
            """,
            (int(vote_post_id), int(option_id)),
        )
        if cur.fetchone() is None:
            return VoteCastResult("invalid_option", vote_post_id, message="That option is not valid.")

        cur.execute(
            """
            SELECT OptionID
            FROM dbo.VotePostVotes WITH (UPDLOCK, HOLDLOCK)
            WHERE VotePostID = ? AND DiscordUserID = ?;
            """,
            (int(vote_post_id), int(discord_user_id)),
        )
        row = cur.fetchone()
        previous_option_id = int(row[0]) if row else None
        if previous_option_id == int(option_id):
            return VoteCastResult(
                "unchanged",
                vote_post_id,
                option_id=int(option_id),
                previous_option_id=previous_option_id,
                message="Your vote was already recorded for this option.",
            )
        if previous_option_id is not None and not _bool(post.get("AllowVoteChange")):
            return VoteCastResult(
                "change_blocked",
                vote_post_id,
                option_id=previous_option_id,
                previous_option_id=previous_option_id,
                message="You have already voted and changes are not enabled for this vote.",
            )
        if previous_option_id is None:
            cur.execute(
                """
                INSERT INTO dbo.VotePostVotes
                    (VotePostID, DiscordUserID, OptionID, OriginalOptionID, CreatedAtUtc, UpdatedAtUtc)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (int(vote_post_id), int(discord_user_id), int(option_id), int(option_id), now, now),
            )
            action = "VoteRecorded"
            status = "recorded"
            message = "Vote recorded."
        else:
            cur.execute(
                """
                UPDATE dbo.VotePostVotes
                SET OptionID = ?,
                    UpdatedAtUtc = ?
                WHERE VotePostID = ? AND DiscordUserID = ?;
                """,
                (int(option_id), now, int(vote_post_id), int(discord_user_id)),
            )
            action = "VoteChanged"
            status = "changed"
            message = "Vote updated."

        cur.execute(
            """
            INSERT INTO dbo.VotePostAudit
                (VotePostID, ActorDiscordUserID, ActionType, OptionID, PreviousOptionID, CreatedAtUtc)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                int(vote_post_id),
                int(discord_user_id),
                action,
                int(option_id),
                previous_option_id,
                now,
            ),
        )
        return VoteCastResult(
            status,
            vote_post_id,
            option_id=int(option_id),
            previous_option_id=previous_option_id,
            message=message,
        )

    result = await run_blocking_in_thread(_cast_vote_sync, _callback, name="vote_cast")
    if isinstance(result, VoteCastResult):
        return result
    return VoteCastResult("error", vote_post_id, message="Vote could not be recorded.")


def _cast_vote_sync(callback) -> Any:
    return exec_with_cursor(callback)


async def update_vote_post(
    *,
    vote_post_id: int,
    actor_discord_user_id: int,
    title: str | None = None,
    description: str | None = None,
    closes_at_utc: datetime | None = None,
    reminder_offsets_minutes: tuple[int, ...] | None = None,
    reminder_mention_everyone: bool | None = None,
    close_mention_everyone: bool | None = None,
) -> bool:
    def _callback(cur) -> bool:
        now = _naive_utc(datetime.now(UTC))
        cur.execute(
            """
            SELECT VotePostID, Status
            FROM dbo.VotePosts WITH (UPDLOCK, HOLDLOCK)
            WHERE VotePostID = ?;
            """,
            (int(vote_post_id),),
        )
        post = fetch_one_dict(cur)
        if not post or str(post.get("Status")) != "Open":
            return False
        if title is not None:
            cur.execute(
                "UPDATE dbo.VotePosts SET Title = ?, UpdatedAtUtc = ? WHERE VotePostID = ?;",
                (title, now, int(vote_post_id)),
            )
        if description is not None:
            cur.execute(
                "UPDATE dbo.VotePosts SET Description = ?, UpdatedAtUtc = ? WHERE VotePostID = ?;",
                (description, now, int(vote_post_id)),
            )
        if closes_at_utc is not None:
            cur.execute(
                "UPDATE dbo.VotePosts SET ClosesAtUtc = ?, UpdatedAtUtc = ? WHERE VotePostID = ?;",
                (_naive_utc(closes_at_utc), now, int(vote_post_id)),
            )
        if reminder_mention_everyone is not None:
            cur.execute(
                """
                UPDATE dbo.VotePosts
                SET ReminderMentionEveryone = ?, UpdatedAtUtc = ?
                WHERE VotePostID = ?;
                """,
                (1 if reminder_mention_everyone else 0, now, int(vote_post_id)),
            )
        if close_mention_everyone is not None:
            cur.execute(
                """
                UPDATE dbo.VotePosts
                SET CloseMentionEveryone = ?, UpdatedAtUtc = ?
                WHERE VotePostID = ?;
                """,
                (1 if close_mention_everyone else 0, now, int(vote_post_id)),
            )
        if reminder_offsets_minutes is not None:
            cur.execute(
                """
                DELETE FROM dbo.VotePostReminders
                WHERE VotePostID = ? AND SentAtUtc IS NULL;
                """,
                (int(vote_post_id),),
            )
            close_for_due = closes_at_utc
            if close_for_due is None:
                cur.execute("SELECT ClosesAtUtc FROM dbo.VotePosts WHERE VotePostID = ?;", (int(vote_post_id),))
                row = cur.fetchone()
                close_for_due = _aware_utc(row[0]) if row else None
            if close_for_due is not None:
                for offset in reminder_offsets_minutes:
                    cur.execute(
                        """
                        INSERT INTO dbo.VotePostReminders
                            (VotePostID, OffsetMinutesBeforeClose, DueAtUtc, CreatedAtUtc)
                        VALUES (?, ?, ?, ?);
                        """,
                        (
                            int(vote_post_id),
                            int(offset),
                            _naive_utc(_reminder_due_at(close_for_due, int(offset))),
                            now,
                        ),
                    )
        cur.execute(
            """
            INSERT INTO dbo.VotePostAudit
                (VotePostID, ActorDiscordUserID, ActionType, DetailsJson, CreatedAtUtc)
            VALUES (?, ?, 'Updated', ?, ?);
            """,
            (
                int(vote_post_id),
                int(actor_discord_user_id),
                json.dumps(
                    {
                        "title": title is not None,
                        "description": description is not None,
                        "closes_at": closes_at_utc is not None,
                        "reminders": reminder_offsets_minutes is not None,
                    }
                ),
                now,
            ),
        )
        return True

    result = await run_blocking_in_thread(_update_vote_post_sync, _callback, name="vote_update")
    return bool(result)


def _update_vote_post_sync(callback) -> Any:
    return exec_with_cursor(callback)


async def claim_due_reminders(now_utc: datetime, *, limit: int = 10) -> list[dict[str, Any]]:
    def _callback(cur) -> list[dict[str, Any]]:
        now = _naive_utc(now_utc)
        cur.execute(
            """
            ;WITH due AS (
                SELECT TOP (?) r.ReminderID
                FROM dbo.VotePostReminders r WITH (UPDLOCK, READPAST)
                JOIN dbo.VotePosts p ON p.VotePostID = r.VotePostID
                WHERE p.Status = 'Open'
                  AND r.SentAtUtc IS NULL
                  AND r.DueAtUtc <= ?
                  AND (r.ClaimedAtUtc IS NULL OR r.ClaimedAtUtc < DATEADD(minute, -30, ?))
                ORDER BY r.DueAtUtc ASC, r.ReminderID ASC
            )
            UPDATE r
            SET ClaimedAtUtc = ?
            OUTPUT INSERTED.ReminderID, INSERTED.VotePostID
            FROM dbo.VotePostReminders r
            JOIN due ON due.ReminderID = r.ReminderID;
            """,
            (int(limit), now, now, now),
        )
        return [cursor_row_to_dict(cur, row) for row in cur.fetchall()]

    rows = await run_blocking_in_thread(_claim_due_reminders_sync, _callback, name="vote_claim_reminders")
    return list(rows or [])


def _claim_due_reminders_sync(callback) -> Any:
    return exec_with_cursor(callback)


async def mark_reminder_sent(reminder_id: int, *, message_id: int, now_utc: datetime) -> bool:
    row = await run_one_async(
        """
        UPDATE dbo.VotePostReminders
        SET SentAtUtc = ?,
            MessageID = ?
        OUTPUT INSERTED.ReminderID
        WHERE ReminderID = ? AND SentAtUtc IS NULL;
        """,
        (_naive_utc(now_utc), int(message_id), int(reminder_id)),
    )
    return bool(row)


async def list_due_closes(now_utc: datetime, *, limit: int = 10) -> list[int]:
    rows = await run_query_async(
        """
        SELECT TOP (?) VotePostID
        FROM dbo.VotePosts
        WHERE Status = 'Open'
          AND ClosesAtUtc <= ?
        ORDER BY ClosesAtUtc ASC, VotePostID ASC;
        """,
        (int(limit), _naive_utc(now_utc)),
    )
    return [int(row["VotePostID"]) for row in rows]


async def close_vote(
    *,
    vote_post_id: int,
    actor_discord_user_id: int | None,
    reason: str,
    now_utc: datetime,
) -> VoteCloseResult:
    row = await run_one_async(
        """
        UPDATE dbo.VotePosts
        SET Status = 'Closed',
            ClosedAtUtc = ?,
            ClosedByDiscordUserID = ?,
            ClosedReason = ?,
            UpdatedAtUtc = ?
        OUTPUT INSERTED.VotePostID
        WHERE VotePostID = ?
          AND Status = 'Open';
        """,
        (
            _naive_utc(now_utc),
            int(actor_discord_user_id) if actor_discord_user_id is not None else None,
            reason,
            _naive_utc(now_utc),
            int(vote_post_id),
        ),
    )
    if row:
        await insert_audit(
            vote_post_id=vote_post_id,
            actor_discord_user_id=actor_discord_user_id,
            action_type="ClosedEarly" if actor_discord_user_id else "ClosedAutomatically",
            details={"reason": reason},
            now_utc=now_utc,
        )
        return VoteCloseResult("closed", vote_post_id, "Vote closed.")
    snapshot = await get_vote_snapshot(vote_post_id)
    if snapshot and snapshot.status == "Closed":
        return VoteCloseResult("already_closed", vote_post_id, "Vote is already closed.")
    return VoteCloseResult("missing", vote_post_id, "Vote was not found.")


async def insert_audit(
    *,
    vote_post_id: int,
    actor_discord_user_id: int | None,
    action_type: str,
    details: dict[str, Any] | None = None,
    option_id: int | None = None,
    previous_option_id: int | None = None,
    now_utc: datetime | None = None,
) -> None:
    await run_one_async(
        """
        INSERT INTO dbo.VotePostAudit
            (VotePostID, ActorDiscordUserID, ActionType, OptionID, PreviousOptionID, DetailsJson, CreatedAtUtc)
        OUTPUT INSERTED.AuditID
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        (
            int(vote_post_id),
            int(actor_discord_user_id) if actor_discord_user_id is not None else None,
            action_type,
            int(option_id) if option_id is not None else None,
            int(previous_option_id) if previous_option_id is not None else None,
            json.dumps(details, ensure_ascii=False) if details else None,
            _naive_utc(now_utc or datetime.now(UTC)),
        ),
    )
