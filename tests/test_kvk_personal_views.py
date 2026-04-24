"""
tests/test_kvk_personal_views.py

Unit tests for ui.views.kvk_personal_views.

Tests cover:
- MyKVKStatsSelectView instantiation with accounts
- interaction_check rejects wrong user
- TargetLookupView.make_callback calls run_target_lookup only (no double-lookup)
- FuzzySelectView interaction_check rejects wrong user
"""

from __future__ import annotations

import asyncio
import types

import pytest

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Lightweight Discord stubs
# ---------------------------------------------------------------------------


class DummyUser:
    def __init__(self, uid=42):
        self.id = uid


class DummyResponse:
    def __init__(self):
        self._done = False
        self.sent = []

    def is_done(self):
        return self._done

    async def send_message(self, *args, **kwargs):
        self.sent.append({"args": args, "kwargs": kwargs})
        self._done = True


class DummyInteraction:
    def __init__(self, user_id=42):
        self.user = DummyUser(user_id)
        self.response = DummyResponse()
        self.followup = types.SimpleNamespace(sent=[], send=self._followup_send)

    async def _followup_send(self, *args, **kwargs):
        self.followup.sent.append({"args": args, "kwargs": kwargs})


class DummyCtx:
    def __init__(self, user_id=42):
        self.user = DummyUser(user_id)


# ---------------------------------------------------------------------------
# MyKVKStatsSelectView
# ---------------------------------------------------------------------------


async def test_my_kvk_stats_select_view_instantiates():
    """View can be created with a valid accounts dict."""
    from ui.views.kvk_personal_views import MyKVKStatsSelectView

    accounts = {
        "Main": {"GovernorID": "100", "GovernorName": "TestGov"},
        "Alt 1": {"GovernorID": "200", "GovernorName": "FarmAlt"},
    }
    ctx = DummyCtx(user_id=1)
    view = MyKVKStatsSelectView(ctx=ctx, accounts=accounts, author_id=1)

    assert view is not None
    assert view.author_id == 1
    # The select dropdown should have options matching the accounts
    assert hasattr(view, "select")
    option_values = [o.value for o in view.select.options]
    assert "100" in option_values
    assert "200" in option_values


async def test_my_kvk_stats_select_view_interaction_check_rejects_wrong_user():
    """interaction_check returns False and sends error for a different user."""
    from ui.views.kvk_personal_views import MyKVKStatsSelectView

    ctx = DummyCtx(user_id=1)
    view = MyKVKStatsSelectView(ctx=ctx, accounts={}, author_id=1)

    # Simulate a different user trying to interact
    interaction = DummyInteraction(user_id=99)
    result = await view.interaction_check(interaction)

    assert result is False
    assert interaction.response.sent, "Expected send_message to be called for wrong user"


async def test_my_kvk_stats_select_view_interaction_check_allows_correct_user():
    """interaction_check returns True for the correct user."""
    from ui.views.kvk_personal_views import MyKVKStatsSelectView

    ctx = DummyCtx(user_id=42)
    view = MyKVKStatsSelectView(ctx=ctx, accounts={}, author_id=42)

    interaction = DummyInteraction(user_id=42)
    result = await view.interaction_check(interaction)

    assert result is True


# ---------------------------------------------------------------------------
# TargetLookupView.make_callback — no double-lookup
# ---------------------------------------------------------------------------


async def test_target_lookup_view_make_callback_calls_run_target_lookup_only(monkeypatch):
    """
    make_callback should call run_target_lookup and NOTHING ELSE.
    No get_cached_target_info, no get_fallback_target_info, no build_target_embed.
    """
    from ui.views.kvk_personal_views import TargetLookupView

    run_called = {}
    extra_calls = []

    async def fake_run_target_lookup(interaction, gid, ephemeral=False):
        run_called["gid"] = gid
        run_called["ephemeral"] = ephemeral

    async def fake_extra(*args, **kwargs):
        extra_calls.append(args)

    # Patch target_utils module
    import target_utils

    monkeypatch.setattr(target_utils, "run_target_lookup", fake_run_target_lookup)

    # Patch anything that should NOT be called
    try:
        monkeypatch.setattr(target_utils, "get_cached_target_info", fake_extra, raising=False)
        monkeypatch.setattr(target_utils, "get_fallback_target_info", fake_extra, raising=False)
    except AttributeError:
        pass

    matches = [{"GovernorName": "TestGov", "GovernorID": "555"}]
    view = TargetLookupView(matches)

    interaction = DummyInteraction(user_id=1)
    callback = view.make_callback("555")
    await callback(interaction)

    assert run_called.get("gid") == "555", "run_target_lookup was not called with the correct gid"
    assert extra_calls == [], "Unexpected extra calls detected (dead code path may still be present)"


# ---------------------------------------------------------------------------
# FuzzySelectView — interaction_check
# ---------------------------------------------------------------------------


async def test_fuzzy_select_view_interaction_check_rejects_wrong_user():
    """FuzzySelectView.interaction_check returns False for different user."""
    from ui.views.kvk_personal_views import FuzzySelectView

    matches = [{"GovernorName": "Gov", "GovernorID": "123"}]
    view = FuzzySelectView(matches, author_id=10)

    interaction = DummyInteraction(user_id=99)
    result = await view.interaction_check(interaction)
    assert result is False


async def test_fuzzy_select_view_interaction_check_allows_correct_user():
    """FuzzySelectView.interaction_check returns True for the correct user."""
    from ui.views.kvk_personal_views import FuzzySelectView

    matches = [{"GovernorName": "Gov", "GovernorID": "123"}]
    view = FuzzySelectView(matches, author_id=10)

    interaction = DummyInteraction(user_id=10)
    result = await view.interaction_check(interaction)
    assert result is True


# ---------------------------------------------------------------------------
# PostLookupActions — interaction_check
# ---------------------------------------------------------------------------


async def test_post_lookup_actions_interaction_check_rejects_wrong_user():
    """PostLookupActions.interaction_check returns False for different user."""
    from ui.views.kvk_personal_views import PostLookupActions

    view = PostLookupActions(author_id=1, governor_id="999")
    interaction = DummyInteraction(user_id=2)
    result = await view.interaction_check(interaction)
    assert result is False


async def test_post_lookup_actions_interaction_check_allows_correct_user():
    """PostLookupActions.interaction_check returns True for the correct user."""
    from ui.views.kvk_personal_views import PostLookupActions

    view = PostLookupActions(author_id=1, governor_id="999")
    interaction = DummyInteraction(user_id=1)
    result = await view.interaction_check(interaction)
    assert result is True
