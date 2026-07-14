from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from mge import mge_completion_service


def test_complete_event_changes_status() -> None:
    with (
        patch(
            "mge.dal.mge_completion_dal.fetch_event_completion_context",
            return_value={"EventId": 1, "Status": "published"},
        ),
        patch(
            "mge.dal.mge_completion_dal.mark_event_completed",
            return_value=True,
        ),
    ):
        result = mge_completion_service.complete_event(1, actor_discord_id=123)
        assert result["ok"] is True
        assert result["changed"] is True


def test_complete_event_invalid_status_blocked() -> None:
    with patch(
        "mge.dal.mge_completion_dal.fetch_event_completion_context",
        return_value={"EventId": 9, "Status": "created"},
    ):
        result = mge_completion_service.complete_event(9, actor_discord_id=123)
        assert result["ok"] is False
        assert result["changed"] is False
        assert result["reason"] == "invalid_status"
        assert result["status"] == "created"


def test_open_event_completion_works_without_roster_dependency() -> None:
    with (
        patch(
            "mge.dal.mge_completion_dal.fetch_event_completion_context",
            return_value={"EventId": 2, "Status": "signup_open", "EventMode": "open"},
        ),
        patch(
            "mge.dal.mge_completion_dal.mark_event_completed",
            return_value=True,
        ),
    ):
        result = mge_completion_service.complete_event(2, actor_discord_id=None, source="scheduler")
        assert result["ok"] is True
        assert result["changed"] is True


def test_reopen_requires_completed_state() -> None:
    with patch(
        "mge.dal.mge_completion_dal.fetch_event_completion_context",
        return_value={"EventId": 3, "Status": "published"},
    ):
        result = mge_completion_service.reopen_event(3, actor_discord_id=42)
        assert result["ok"] is False
        assert result["reason"] == "not_completed"


def test_auto_complete_due_events() -> None:
    now = datetime.now(UTC)
    with (
        patch(
            "mge.dal.mge_completion_dal.fetch_due_event_ids_for_completion",
            return_value=[10, 11],
        ),
        patch(
            "mge.mge_completion_service.complete_event",
            side_effect=[{"changed": True}, {"changed": False}],
        ),
    ):
        result = mge_completion_service.auto_complete_due_events(now)
        assert result["due_count"] == 2
        assert result["completed_count"] == 1
