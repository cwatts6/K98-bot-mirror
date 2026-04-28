from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ui.views.mge_admin_completion_view import MgeAdminCompletionView


class _FakeUser:
    def __init__(self, user_id: int):
        self.id = user_id


class _FakeChannel:
    def __init__(self) -> None:
        self.send = AsyncMock()


class _FakeClient:
    def __init__(self) -> None:
        self._channel = _FakeChannel()

    def get_channel(self, channel_id: int):
        del channel_id
        return self._channel


class _FakeInteraction:
    def __init__(self, user_id: int):
        self.user = _FakeUser(user_id)
        self.client = _FakeClient()

        # response.is_done() must be sync bool-returning callable
        self.response = SimpleNamespace(
            is_done=Mock(return_value=False),
            send_message=AsyncMock(),
        )
        self.followup = SimpleNamespace(send=AsyncMock())


@pytest.mark.asyncio
async def test_post_summary_admin_path() -> None:
    view = MgeAdminCompletionView(event_id=1, leadership_channel_id=999)
    interaction = _FakeInteraction(user_id=123)

    with (
        patch("core.mge_permissions._is_admin", return_value=True),
        patch(
            "mge.mge_report_service.build_post_event_summary",
            return_value={
                "Totals": {"TotalSignups": 10},
                "Awards": {"AwardedCount": 5, "WaitlistCount": 2},
                "RepublishMetrics": {"PublishVersion": 2, "ChangeCount": 4},
            },
        ),
        patch(
            "ui.views.mge_admin_completion_view.send_ephemeral",
            new_callable=AsyncMock,
        ) as mock_ephemeral,
    ):
        await view.post_summary_button.callback(interaction)
        assert mock_ephemeral.await_count == 1
        interaction.client._channel.send.assert_awaited_once()
