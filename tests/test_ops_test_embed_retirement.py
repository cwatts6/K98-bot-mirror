"""Real Pycord invocation of the retired publisher must never reach stats work."""

import asyncio
import types
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
def guidance_command(monkeypatch):
    from commands import admin_cmds
    import decoraters
    import file_utils
    from stats_alerts import diagnostics, guard, interface, kvk_diagnostics, kvk_meta, state

    monkeypatch.setattr(admin_cmds, "GUILD_ID", 10)
    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 30)
    monkeypatch.setattr(decoraters, "NOTIFY_CHANNEL_ID", 40)
    usage = AsyncMock()
    monkeypatch.setattr(decoraters, "usage_tracker", lambda: types.SimpleNamespace(log=usage))
    groups = []
    bot = types.SimpleNamespace(add_application_command=groups.append, get_channel=Mock())
    admin_cmds.register_admin(bot)
    ops = next(group for group in groups if group.name == "ops")
    command = next(child for child in ops.subcommands if child.name == "test_embed")

    # Include the former command aliases to catch a regression to the old call path.
    selector = Mock(return_value=True)
    sender = AsyncMock(return_value=None)
    monkeypatch.setattr(admin_cmds, "is_currently_kvk", selector, raising=False)
    monkeypatch.setattr(kvk_meta, "is_currently_kvk", selector)
    monkeypatch.setattr(admin_cmds, "send_stats_update_embed", sender, raising=False)
    monkeypatch.setattr(interface, "send_stats_update_embed", sender)
    forbidden = [selector, sender, bot.get_channel]
    for runner in (diagnostics.runner, kvk_diagnostics.runner):
        spy = AsyncMock()
        monkeypatch.setattr(runner, "execute", spy)
        forbidden.append(spy)
    for name in ("load_state", "save_state", "update_prekvk_message"):
        spy = Mock()
        monkeypatch.setattr(state, name, spy)
        forbidden.append(spy)
    for module, name in ((file_utils, "run_blocking_in_thread"), (asyncio, "to_thread")):
        spy = AsyncMock()
        monkeypatch.setattr(module, name, spy)
        forbidden.append(spy)
    claim = Mock()
    monkeypatch.setattr(guard, "claim_send", claim)
    forbidden.append(claim)

    def context(*, owner=30, channel=40, parent=None, response_error=None):
        user = types.SimpleNamespace(id=owner, display_name="Operator")
        location = types.SimpleNamespace(id=channel, parent_id=parent)
        guild = types.SimpleNamespace(id=10)
        response = types.SimpleNamespace(
            is_done=Mock(return_value=False), send_message=AsyncMock(), defer=AsyncMock()
        )

        async def defer(**kwargs):
            response.is_done.return_value = True

        response.defer.side_effect = defer
        interaction = types.SimpleNamespace(
            user=user,
            guild=guild,
            channel=location,
            response=response,
            followup=types.SimpleNamespace(send=AsyncMock(side_effect=response_error)),
            data={"options": []},
        )
        return types.SimpleNamespace(
            bot=bot,
            user=user,
            guild=guild,
            channel=location,
            interaction=interaction,
            command=command,
        )

    yield types.SimpleNamespace(
        command=command,
        ops=ops,
        context=context,
        forbidden=forbidden,
        selector=selector,
        sender=sender,
        usage=usage,
        module=admin_cmds,
    )
    for spy in forbidden:
        spy.assert_not_called()


def assert_guide(ctx):
    reply = ctx.interaction.followup.send
    reply.assert_awaited_once()
    text = reply.call_args.args[0]
    assert "does not publish a stats embed" in text
    assert "/kvk_admin test_embed" in text and "/prekvk dispatch_test" in text
    assert "explicit diagnostic destination" in text
    assert "kvk_no" in text and "historical season" in text
    assert "Neither proves natural production delivery" in text
    assert "off-season/Kingdom Summary diagnostic is not currently available" in text
    assert "Posted to:" not in text and "Test stats embed sent" not in text
    assert len(text) <= 2000
    assert reply.call_args.kwargs["ephemeral"] is True
    assert reply.call_args.kwargs["allowed_mentions"].to_dict() == {"parse": []}
    assert not any(token in text for token in ("@everyone", "@here", "<@"))
    assert not any(key in reply.call_args.kwargs for key in ("embed", "embeds", "view", "file"))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("season", "legacy_result"),
    [
        (True, "sent"),
        (True, "edited"),
        (True, "guarded"),
        (False, None),
        (False, "unavailable"),
        (None, "failed"),
        (None, "uncertain"),
    ],
)
async def test_guide_never_selects_or_dispatches(guidance_command, season, legacy_result):
    setup = guidance_command
    setup.selector.return_value = season
    setup.sender.return_value = legacy_result
    ctx = setup.context()
    await setup.command._invoke(ctx)
    assert_guide(ctx)
    ctx.interaction.response.defer.assert_awaited_once_with(ephemeral=True)
    assert setup.usage.await_count == 1
    assert setup.command.callback.__version__ == "v1.08"
    payload = setup.command.to_dict()
    assert payload.get("options", []) == []
    assert "guidance" in payload["description"]
    assert len(setup.ops.to_dict()["options"]) == 25


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("owner", "channel", "parent", "allowed"),
    [(30, 41, 40, True), (31, 40, None, False), (30, 41, None, False)],
)
async def test_original_admin_notify_and_thread_gate(
    guidance_command, owner, channel, parent, allowed
):
    setup = guidance_command
    ctx = setup.context(owner=owner, channel=channel, parent=parent)
    await setup.command._invoke(ctx)
    if allowed:
        assert_guide(ctx)
    else:
        ctx.interaction.response.defer.assert_not_awaited()
        ctx.interaction.followup.send.assert_not_awaited()
        denial = ctx.interaction.response.send_message
        denial.assert_awaited_once()
        assert denial.call_args.kwargs["ephemeral"] is True
    assert setup.usage.await_count == 1


@pytest.mark.asyncio
async def test_failed_defer_stops_without_a_second_response(guidance_command, monkeypatch):
    setup = guidance_command
    monkeypatch.setattr(setup.module, "safe_defer", AsyncMock(return_value=False))
    ctx = setup.context()
    await setup.command._invoke(ctx)
    ctx.interaction.followup.send.assert_not_awaited()
    ctx.interaction.response.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_response_failure_has_no_retry_or_raw_error(guidance_command, caplog):
    setup = guidance_command
    ctx = setup.context(response_error=RuntimeError("private failure detail"))
    await setup.command._invoke(ctx)
    assert_guide(ctx)
    ctx.interaction.response.send_message.assert_not_awaited()
    assert "interaction_send_ephemeral_failed" in caplog.text
    assert "private failure detail" not in ctx.interaction.followup.send.call_args.args[0]


@pytest.mark.asyncio
async def test_cancellation_propagates_without_retry(guidance_command):
    setup = guidance_command
    ctx = setup.context(response_error=asyncio.CancelledError())
    with pytest.raises(asyncio.CancelledError):
        await setup.command._invoke(ctx)
    ctx.interaction.followup.send.assert_awaited_once()
    ctx.interaction.response.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_concurrent_invocations_need_no_session(guidance_command):
    setup = guidance_command
    contexts = [setup.context(), setup.context()]
    await asyncio.gather(*(setup.command._invoke(ctx) for ctx in contexts))
    for ctx in contexts:
        assert_guide(ctx)
