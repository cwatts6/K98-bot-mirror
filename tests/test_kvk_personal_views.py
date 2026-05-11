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

    async def fake_run_target_lookup(governor_id):
        run_called["governor_id"] = governor_id
        return {"status": "not_found", "message": "no targets"}

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
    interaction.channel = None
    callback = view.make_callback("555")
    await callback(interaction)

    assert (
        run_called.get("governor_id") == "555"
    ), "run_target_lookup was not called with the correct gid"
    assert (
        extra_calls == []
    ), "Unexpected extra calls detected (dead code path may still be present)"


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


# ---------------------------------------------------------------------------
# PostLookupActions — btn_stats calls load_kvk_personal_stats + post_stats_embeds
# ---------------------------------------------------------------------------


async def test_post_lookup_actions_btn_stats_loads_and_posts(monkeypatch):
    """btn_stats loads stats via the service and posts to channel."""
    import types

    from ui.views.kvk_personal_views import PostLookupActions

    # --- stubs ---
    stats_called = {}

    async def fake_load_stats(gid):
        stats_called["gid"] = gid
        return {"GovernorID": gid, "GovernorName": "TestGov"}

    def fake_normalize(gid):
        return gid

    def fake_build_embed(row, user):
        return (["embed"], None)

    def fake_get_last_kvk(gid):
        return None

    # Patch service helpers
    import services.kvk_personal_service as svc

    monkeypatch.setattr(svc, "load_kvk_personal_stats", fake_load_stats)

    import utils

    monkeypatch.setattr(utils, "normalize_governor_id", fake_normalize, raising=False)

    import embed_utils

    monkeypatch.setattr(embed_utils, "build_stats_embed", fake_build_embed, raising=False)

    import stats_cache_helpers

    monkeypatch.setattr(
        stats_cache_helpers, "get_last_kvk_for_governor_sync", fake_get_last_kvk, raising=False
    )

    view = PostLookupActions(author_id=1, governor_id="123")

    dummy_client = types.SimpleNamespace()

    class FakeChannel:
        def __init__(self):
            self.sends = []

        async def send(self, **kwargs):
            self.sends.append(kwargs)

    class DummyInteractionWithClient(DummyInteraction):
        client = dummy_client
        channel = FakeChannel()

        async def _defer(self, **kwargs):
            self.response._done = True

    interaction = DummyInteractionWithClient(user_id=1)
    interaction.response.defer = interaction._defer

    await view.btn_stats.callback(interaction)

    assert stats_called.get("gid") == "123", "load_kvk_personal_stats not called with correct gid"
    assert (
        interaction.channel.sends or interaction.followup.sent
    ), "btn_stats did not post any message to the channel or followup"
