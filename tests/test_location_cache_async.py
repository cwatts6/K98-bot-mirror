from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("ephemeral", [True, False])
async def test_acknowledges_before_worker_and_preserves_result_visibility(monkeypatch, ephemeral):
    from commands import location_cmds as command
    import decoraters
    from services.profile_lookup_service import ProfileLookupResult

    groups, events = [], []
    monkeypatch.setattr(command, "track_usage", lambda: lambda fn: fn)
    monkeypatch.setattr(command, "configure_location_views", lambda **kw: None)
    monkeypatch.setattr(command, "ALLOWED_CHANNEL_IDS", {10})
    monkeypatch.setattr(decoraters, "_is_admin", lambda user: True)
    command.register_location(SimpleNamespace(add_application_command=groups.append))
    callback = next(c.callback for c in groups[0].subcommands if c.name == "player")

    async def defer(**kw):
        events.append(("ack", kw["ephemeral"]))

    def lookup(**kw):
        assert events == [("ack", True)]
        events.append(("lookup",))
        return ProfileLookupResult("found", governor_id=1)

    monkeypatch.setattr(command, "resolve_profile_lookup", lookup)
    monkeypatch.setattr(command, "get_profile_async", AsyncMock(return_value={"GovernorID": 1}))
    inter = SimpleNamespace(
        user=SimpleNamespace(id=5),
        channel=SimpleNamespace(id=10),
        response=SimpleNamespace(is_done=lambda: False, defer=defer),
        edit_original_response=AsyncMock(),
        delete_original_response=AsyncMock(),
        followup=SimpleNamespace(send=AsyncMock()),
    )
    ctx = SimpleNamespace(interaction=inter, user=inter.user)
    await callback(ctx, governor_id=1, governor_name=None, ephemeral=ephemeral)
    assert events == [("ack", True), ("lookup",)]
    if ephemeral:
        inter.edit_original_response.assert_awaited_once()
        inter.followup.send.assert_not_awaited()
    else:
        inter.edit_original_response.assert_awaited_once_with(content="Posting location…")
        inter.followup.send.assert_awaited_once()
        assert inter.followup.send.await_args.kwargs["ephemeral"] is False
        inter.delete_original_response.assert_awaited_once()


@pytest.mark.asyncio
async def test_permission_denial_prevents_any_cache_work(monkeypatch):
    from commands import location_cmds as command
    import decoraters

    groups = []
    monkeypatch.setattr(command, "track_usage", lambda: lambda fn: fn)
    monkeypatch.setattr(command, "configure_location_views", lambda **kw: None)
    monkeypatch.setattr(command, "ALLOWED_CHANNEL_IDS", {10})
    monkeypatch.setattr(decoraters, "_is_admin", lambda user: False)
    monkeypatch.setattr(decoraters, "_has_leadership_role", lambda user: False)
    lookup = Mock(side_effect=AssertionError("unauthorized cache read"))
    monkeypatch.setattr(command, "resolve_profile_lookup", lookup)
    command.register_location(SimpleNamespace(add_application_command=groups.append))
    callback = next(c.callback for c in groups[0].subcommands if c.name == "player")
    response = SimpleNamespace(is_done=lambda: False, send_message=AsyncMock(), defer=AsyncMock())
    inter = SimpleNamespace(
        user=SimpleNamespace(id=5), channel=SimpleNamespace(id=10), response=response
    )
    await callback(
        SimpleNamespace(interaction=inter), governor_id=1, governor_name=None, ephemeral=True
    )
    lookup.assert_not_called()
    response.defer.assert_not_awaited()
    response.send_message.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("ephemeral", [True, False])
async def test_selection_acknowledges_before_read(monkeypatch, ephemeral):
    from commands import location_cmds as command

    response = SimpleNamespace(defer=AsyncMock())
    inter = SimpleNamespace(
        response=response,
        edit_original_response=AsyncMock(),
        channel=SimpleNamespace(send=AsyncMock()),
    )

    async def build(*a, **kw):
        response.defer.assert_awaited_once_with()
        return "embed"

    monkeypatch.setattr(command, "_build_location_embed_for_target", build)
    await command._on_location_selected(inter, 1, ephemeral)
    inter.edit_original_response.assert_awaited_once()
    if ephemeral:
        inter.channel.send.assert_not_awaited()
    else:
        inter.channel.send.assert_awaited_once_with(embed="embed")


@pytest.mark.asyncio
async def test_public_followup_is_distinct_from_deferred_original(monkeypatch):
    """Model Discord's first-followup compatibility behavior, not just AsyncMock."""
    from commands import location_cmds as command
    import decoraters
    from services.profile_lookup_service import ProfileLookupResult

    groups = []
    monkeypatch.setattr(command, "track_usage", lambda: lambda fn: fn)
    monkeypatch.setattr(command, "configure_location_views", lambda **kw: None)
    monkeypatch.setattr(command, "ALLOWED_CHANNEL_IDS", {10})
    monkeypatch.setattr(decoraters, "_is_admin", lambda user: True)
    monkeypatch.setattr(
        command, "resolve_profile_lookup", lambda **kw: ProfileLookupResult("found", governor_id=1)
    )
    monkeypatch.setattr(command, "get_profile_async", AsyncMock(return_value={"GovernorID": 1}))
    command.register_location(SimpleNamespace(add_application_command=groups.append))
    callback = next(c.callback for c in groups[0].subcommands if c.name == "player")
    state = {"loading": True, "public": False, "original_deleted": False}

    async def edit(**kw):
        state["loading"] = False

    async def send(**kw):
        # Direct first followup would consume the private loading response.
        state["public"] = not state["loading"] and not kw["ephemeral"]
        state["loading"] = False

    async def delete():
        state["original_deleted"] = True

    inter = SimpleNamespace(
        user=SimpleNamespace(id=5),
        channel=SimpleNamespace(id=10),
        response=SimpleNamespace(is_done=lambda: False, defer=AsyncMock()),
        edit_original_response=edit,
        delete_original_response=delete,
        followup=SimpleNamespace(send=send),
    )
    await callback(
        SimpleNamespace(interaction=inter, user=inter.user),
        governor_id=1,
        governor_name=None,
        ephemeral=False,
    )
    assert state["public"] and state["original_deleted"]
