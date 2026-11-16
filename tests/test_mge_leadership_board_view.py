from __future__ import annotations

import pytest

from ui.views.mge_leadership_board_view import MgeLeadershipBoardView


@pytest.mark.asyncio
async def test_view_constructs():
    view = MgeLeadershipBoardView(event_id=123)
    assert view.event_id == 123
