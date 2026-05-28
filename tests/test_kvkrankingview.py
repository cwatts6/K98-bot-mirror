# tests/test_kvkrankingview.py
"""
Unit tests for KVKRankingView class in ui.views.stats_views.py

Updated fixtures and expectations to reflect:
- Filtering by STATUS == "INCLUDED" and min power in build_kvkrankings_embed/filter_rows_for_leaderboard
- Medal emojis removed; top ranks indicated by "*1", "*2", "*3"
"""

import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

utils_stub = types.ModuleType("utils")
utils_stub.fmt_short = lambda v: str(v)
sys.modules.setdefault("utils", utils_stub)

# Import the view class
from ui.views.stats_views import KVKRankingView


@pytest.fixture
def mock_cache():
    """Minimal cache for testing. Values meet the inclusion filter."""
    return {
        "_meta": {"generated_at": "2026-02-08"},
        "1": {"GovernorID": "1", "Starting Power": 100_000_000, "STATUS": "INCLUDED"},
        "2": {"GovernorID": "2", "Starting Power": 90_000_000, "STATUS": "INCLUDED"},
    }


@pytest.fixture
def large_cache():
    """Large cache for pagination testing (100 players). Provide high power + INCLUDED status."""
    cache = {"_meta": {"generated_at": "2026-02-08"}}
    for i in range(100):
        # Ensure all players meet min power threshold
        cache[str(i)] = {
            "GovernorID": str(i),
            "Starting Power": 100_000_000 + (1000 - i),
            "STATUS": "INCLUDED",
        }
    return cache


# === State Change Tests (Async) ===


@pytest.mark.asyncio
async def test_limit_change_updates_state(mock_cache):
    """Changing limit updates view state and resets page."""
    view = KVKRankingView(mock_cache, limit=10)

    interaction = AsyncMock()
    interaction.response.is_done = AsyncMock(return_value=False)

    with patch("ui.views.stats_views.build_kvkrankings_embed") as mock_embed:
        mock_embed.return_value = MagicMock(footer=MagicMock(text="test"), description="test")

        # Simulate clicking "Top 25" button
        handler = view._make_limit_handler(25)
        await handler(interaction)

    assert view.limit == 25
    assert view.page == 1


@pytest.mark.asyncio
async def test_next_page_increments_page(large_cache):
    """Clicking Next increments page number."""
    view = KVKRankingView(large_cache, limit=100)

    interaction = AsyncMock()
    interaction.response.is_done = AsyncMock(return_value=False)

    with patch("ui.views.stats_views.build_kvkrankings_embed") as mock_embed:
        mock_embed.return_value = MagicMock(footer=MagicMock(text="test"), description="test")

        await view._on_next_page(interaction)

    assert view.page == 2


@pytest.mark.asyncio
async def test_prev_page_decrements_page(large_cache):
    """Clicking Previous decrements page number."""
    view = KVKRankingView(large_cache, limit=100)
    view.page = 2

    interaction = AsyncMock()
    interaction.response.is_done = AsyncMock(return_value=False)

    with patch("ui.views.stats_views.build_kvkrankings_embed") as mock_embed:
        mock_embed.return_value = MagicMock(footer=MagicMock(text="test"), description="test")

        await view._on_prev_page(interaction)

    assert view.page == 1


@pytest.mark.asyncio
async def test_next_page_does_not_exceed_max(large_cache):
    """Next button does not go beyond last page."""
    view = KVKRankingView(large_cache, limit=100)
    view.page = 2  # Already on last page

    interaction = AsyncMock()
    interaction.response.is_done = AsyncMock(return_value=False)

    with patch("ui.views.stats_views.build_kvkrankings_embed") as mock_embed:
        mock_embed.return_value = MagicMock(footer=MagicMock(text="test"), description="test")

        await view._on_next_page(interaction)

    assert view.page == 2  # Should stay on page 2


@pytest.mark.asyncio
async def test_prev_page_does_not_go_below_1(large_cache):
    """Previous button does not go below page 1."""
    view = KVKRankingView(large_cache, limit=100)
    view.page = 1  # Already on first page

    interaction = AsyncMock()
    interaction.response.is_done = AsyncMock(return_value=False)

    with patch("ui.views.stats_views.build_kvkrankings_embed") as mock_embed:
        mock_embed.return_value = MagicMock(footer=MagicMock(text="test"), description="test")

        await view._on_prev_page(interaction)

    assert view.page == 1  # Should stay on page 1


# === Pagination Button Management Tests ===


@pytest.mark.asyncio
async def test_changing_to_top_100_adds_pagination(large_cache):
    """Changing from Top 10 to Top 100 adds pagination buttons."""
    view = KVKRankingView(large_cache, limit=10)

    # Initially no pagination
    assert not hasattr(view, "prev_btn")

    interaction = AsyncMock()
    interaction.response.is_done = AsyncMock(return_value=False)

    with patch("ui.views.stats_views.build_kvkrankings_embed") as mock_embed:
        mock_embed.return_value = MagicMock(footer=MagicMock(text="test"), description="test")

        # Change to Top 100
        handler = view._make_limit_handler(100)
        await handler(interaction)

    # Should now have pagination (large_cache contains 100 eligible rows)
    assert hasattr(view, "prev_btn")
    assert hasattr(view, "next_btn")


@pytest.mark.asyncio
async def test_changing_to_top_10_removes_pagination(large_cache):
    """Changing from Top 100 to Top 10 removes pagination buttons."""
    view = KVKRankingView(large_cache, limit=100)

    # Initially has pagination (constructor may add it)
    assert hasattr(view, "prev_btn")

    interaction = AsyncMock()
    interaction.response.is_done = AsyncMock(return_value=False)

    with patch("ui.views.stats_views.build_kvkrankings_embed") as mock_embed:
        mock_embed.return_value = MagicMock(footer=MagicMock(text="test"), description="test")

        # Change to Top 10
        handler = view._make_limit_handler(10)
        await handler(interaction)

    # Should no longer have pagination
    assert not hasattr(view, "prev_btn")
    assert not hasattr(view, "next_btn")
    assert view.page == 1  # Reset to page 1


# === Timeout Tests ===


@pytest.mark.asyncio
async def test_timeout_disables_all_children(mock_cache):
    """on_timeout disables all UI elements."""
    view = KVKRankingView(mock_cache)

    # Mock message
    view.message = AsyncMock()

    await view.on_timeout()

    # All children should be disabled
    for child in view.children:
        assert child.disabled is True


@pytest.mark.asyncio
async def test_timeout_edits_message_if_available(mock_cache):
    """on_timeout edits message to show disabled state."""
    view = KVKRankingView(mock_cache)

    # Mock message
    view.message = AsyncMock()

    await view.on_timeout()

    # Message.edit should have been called with the view
    view.message.edit.assert_called_once()
    call_kwargs = view.message.edit.call_args.kwargs
    assert call_kwargs.get("view") is view


@pytest.mark.asyncio
async def test_timeout_handles_missing_message_gracefully(mock_cache):
    """on_timeout doesn't crash if message is None."""
    view = KVKRankingView(mock_cache)
    view.message = None

    # Should not raise
    await view.on_timeout()


# === Redraw Tests ===


@pytest.mark.asyncio
async def test_redraw_updates_dropdown_selection(mock_cache):
    """_redraw updates dropdown to reflect current metric."""
    view = KVKRankingView(mock_cache, metric="power")
    view.metric = "kills"  # Change metric

    interaction = AsyncMock()
    interaction.response.is_done = AsyncMock(return_value=False)

    with patch("ui.views.stats_views.build_kvkrankings_embed") as mock_embed:
        mock_embed.return_value = MagicMock(footer=MagicMock(text="test"), description="test")

        await view._redraw(interaction)

    # "kills" option should now be marked default
    kills_opt = next((opt for opt in view.metric_select.options if opt.value == "kills"), None)
    assert kills_opt.default is True

    # "power" option should not be default
    power_opt = next((opt for opt in view.metric_select.options if opt.value == "power"), None)
    assert power_opt.default is False


@pytest.mark.asyncio
async def test_redraw_updates_button_styles(mock_cache):
    """_redraw updates button styles to reflect current limit."""
    view = KVKRankingView(mock_cache, limit=10)
    view.limit = 25  # Change limit

    interaction = AsyncMock()
    interaction.response.is_done = AsyncMock(return_value=False)

    with patch("ui.views.stats_views.build_kvkrankings_embed") as mock_embed:
        mock_embed.return_value = MagicMock(footer=MagicMock(text="test"), description="test")

        await view._redraw(interaction)

    # Find limit buttons
    buttons = [
        c for c in view.children if hasattr(c, "label") and c.label and c.label.startswith("Top ")
    ]

    top_25_btn = next((b for b in buttons if b.label == "Top 25"), None)
    top_10_btn = next((b for b in buttons if b.label == "Top 10"), None)

    import discord

    assert top_25_btn.style == discord.ButtonStyle.primary
    assert top_10_btn.style == discord.ButtonStyle.secondary


@pytest.mark.asyncio
async def test_redraw_calls_embed_builder_with_current_state(mock_cache):
    """_redraw calls build_kvkrankings_embed with current view state."""
    view = KVKRankingView(mock_cache, metric="dkp", limit=50)
    view.page = 1

    interaction = AsyncMock()
    interaction.response.is_done = AsyncMock(return_value=False)

    with patch("ui.views.stats_views.build_kvkrankings_embed") as mock_embed:
        mock_embed.return_value = MagicMock(footer=MagicMock(text="test"), description="test")

        await view._redraw(interaction)

        # Check call arguments
        mock_embed.assert_called_once()
        call_args = mock_embed.call_args

        assert call_args.args[0] == view.rows  # rows
        assert call_args.args[1] == "dkp"  # metric
        assert call_args.args[2] == 50  # limit
        assert call_args.kwargs.get("page") == 1


# === Integration Test ===


@pytest.mark.asyncio
async def test_full_interaction_flow(large_cache):
    """Test complete user interaction flow."""
    view = KVKRankingView(large_cache, metric="power", limit=10)

    # Initial state
    assert view.metric == "power"
    assert view.limit == 10
    assert view.page == 1

    interaction = AsyncMock()
    interaction.response.is_done = AsyncMock(return_value=False)

    with patch("ui.views.stats_views.build_kvkrankings_embed") as mock_embed:
        mock_embed.return_value = MagicMock(footer=MagicMock(text="test"), description="test")

        # Change to Top 100
        handler = view._make_limit_handler(100)
        await handler(interaction)

        assert view.limit == 100
        assert view.page == 1  # Reset
        assert hasattr(view, "prev_btn")  # Pagination added

        # Go to page 2
        await view._on_next_page(interaction)
        assert view.page == 2

        # Change back to Top 10
        handler = view._make_limit_handler(10)
        await handler(interaction)

        assert view.limit == 10
        assert view.page == 1  # Reset
        assert not hasattr(view, "prev_btn")  # Pagination removed
