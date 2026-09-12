import datetime
import os
from pathlib import Path
import sys
import types

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["allowed", "owner", "notify", "guild", "permissions", "defer"])
@pytest.mark.parametrize("mode", ["defaults", "run", "status"])
async def test_prekvk_diagnostic_command_boundaries(monkeypatch, case, mode):
    from unittest.mock import AsyncMock, Mock

    import discord

    from commands import prekvk_cmds
    import decoraters
    from stats_alerts import diagnostics

    monkeypatch.setattr(decoraters, "ADMIN_USER_ID", 30)
    monkeypatch.setattr(decoraters, "NOTIFY_CHANNEL_ID", 40)
    monkeypatch.setattr(decoraters, "usage_tracker", lambda: types.SimpleNamespace(log=AsyncMock()))
    monkeypatch.setattr(prekvk_cmds, "GUILD_ID", 10)
    groups = []
    bot = types.SimpleNamespace(
        add_application_command=groups.append, slash_command=lambda **kwargs: lambda fn: fn
    )
    prekvk_cmds.register_prekvk(bot)
    ops = next(group for group in groups if group.name == "prekvk")
    command = next(cmd for cmd in ops.subcommands if cmd.name == "dispatch_test")
    assert command.callback.__version__ == "v1.02"
    payload_options = {option["name"]: option for option in command.to_dict()["options"]}
    assert payload_options["destination"]["type"] == 7
    assert payload_options["destination"]["required"] is True
    assert payload_options["action"]["type"] == 3
    assert [choice["value"] for choice in payload_options["action"]["choices"]] == ["run", "status"]
    assert payload_options["session"]["type"] == 3
    assert payload_options["session"]["required"] is False
    user = types.SimpleNamespace(id=31 if case == "owner" else 30, display_name="Operator")
    guild = types.SimpleNamespace(id=11 if case == "guild" else 10, me=object())
    location = types.SimpleNamespace(id=41 if case == "notify" else 40, parent_id=None)
    response = types.SimpleNamespace(
        is_done=lambda: False, send_message=AsyncMock(), defer=AsyncMock()
    )
    interaction = types.SimpleNamespace(
        user=user,
        guild=guild,
        channel=location,
        response=response,
        followup=types.SimpleNamespace(send=AsyncMock()),
    )
    ctx = types.SimpleNamespace(
        user=user, guild=guild, channel=location, interaction=interaction, command=command
    )
    target = Mock(spec=discord.TextChannel)
    target.id = 20
    target.guild = types.SimpleNamespace(id=10)
    target.type = discord.ChannelType.text
    target.permissions_for.return_value = types.SimpleNamespace(
        view_channel=True,
        send_messages=case != "permissions",
        embed_links=True,
        read_message_history=True,
    )
    execute = AsyncMock(
        return_value=diagnostics.DiagnosticResult("status", "a" * 32, "observation")
    )
    monkeypatch.setattr(diagnostics.runner, "execute", execute)
    monkeypatch.setattr(prekvk_cmds, "safe_defer", AsyncMock(return_value=case != "defer"))
    guild._channels = {20: target}
    guild._threads = {}
    guild.get_channel_or_thread = lambda channel_id: guild._channels.get(channel_id)
    options = [{"name": "destination", "type": 7, "value": "20"}]
    if mode != "defaults":
        options += [
            {"name": "action", "type": 3, "value": mode},
            {"name": "session", "type": 3, "value": "a" * 32},
        ]
    interaction.data = {
        "options": options,
        "resolved": {"channels": {"20": {"id": "20", "type": 0, "name": "diagnostic"}}},
    }
    await command._invoke(ctx)
    assert execute.await_count == (1 if case == "allowed" else 0)
    replies = response.send_message.call_args_list + interaction.followup.send.call_args_list
    for reply in replies:
        assert reply.kwargs["ephemeral"] is True
        assert not any(token in str(reply.args) for token in ("@everyone", "@here", "<@"))
    if case == "allowed":
        assert execute.call_args.kwargs["channel_id"] == target.id
        assert execute.call_args.kwargs["action"] == ("run" if mode == "defaults" else mode)
        assert execute.call_args.kwargs["token"] == (None if mode == "defaults" else "a" * 32)
        assert replies[0].kwargs["allowed_mentions"].to_dict() == {"parse": []}


def test_register_commands_smoke(monkeypatch):
    monkeypatch.setenv("OUR_KINGDOM", os.getenv("OUR_KINGDOM", "0") or "0")
    if not hasattr(datetime, "UTC"):
        datetime.UTC = datetime.UTC

    sys.modules.setdefault("aiofiles", types.ModuleType("aiofiles"))
    gspread_mod = types.ModuleType("gspread")
    gspread_exc = types.ModuleType("gspread.exceptions")
    gspread_exc.APIError = Exception
    gspread_exc.SpreadsheetNotFound = Exception
    sys.modules.setdefault("gspread", gspread_mod)
    sys.modules.setdefault("gspread.exceptions", gspread_exc)
    sqlalchemy_mod = types.ModuleType("sqlalchemy")
    sqlalchemy_mod.create_engine = lambda *args, **kwargs: None
    sys.modules.setdefault("sqlalchemy", sqlalchemy_mod)

    import Commands

    registered_top_level = []
    registered_groups = {}
    fake_bot = types.SimpleNamespace()
    fake_bot.tree = types.SimpleNamespace(command=lambda **kw: (lambda fn: fn))
    fake_bot.add_listener = lambda *args, **kwargs: None

    def validate_options(payload, path):
        options = payload.get("options", [])
        assert len(options) <= 25, f"/{path}: {len(options)} options exceeds Discord's 25 limit"
        for option in options:
            validate_options(option, f"{path} {option['name']}")

    def add_application_command(command):
        payload = command.to_dict()
        validate_options(payload, command.name)
        registered_groups[command.name] = payload
        registered_top_level.append(command.name)

    fake_bot.add_application_command = add_application_command

    def slash_command(**kwargs):
        def deco(fn):
            registered_top_level.append(kwargs.get("name"))
            return fn

        return deco

    fake_bot.slash_command = slash_command

    Commands.register_commands(fake_bot)

    registered_names = [name for name in registered_top_level if name]
    assert len(registered_names) == 36
    ops_options = registered_groups["ops"]["options"]
    assert len(ops_options) == 24
    assert "test_embed" not in {option["name"] for option in ops_options}
    assert sum(len(group.get("options", [])) for group in registered_groups.values()) == 101
    assert all(len(group.get("options", [])) <= 25 for group in registered_groups.values())
    assert "test_embed" in {option["name"] for option in registered_groups["kvk_admin"]["options"]}
    assert "dispatch_test" in {option["name"] for option in registered_groups["prekvk"]["options"]}
    assert "ark" in registered_top_level
    assert "activity" in registered_top_level
    assert "crystaltech" in registered_top_level
    assert "events" in registered_top_level
    assert "honor" in registered_top_level
    assert "inventory" in registered_top_level
    assert "kvk_admin" in registered_top_level
    assert "kvk" in registered_top_level
    assert "location" in registered_top_level
    assert "me" in registered_top_level
    assert "ops" in registered_top_level
    assert "mge" in registered_top_level
    assert "prekvk" in registered_top_level
    assert "registry" in registered_top_level
    assert "stats" in registered_top_level
    assert "my_stats" not in registered_top_level
    assert "my_stats_export" not in registered_top_level
    assert "subscriptions" in registered_top_level
    assert "ark_create_match" not in registered_top_level
    assert "ark_force_announce" not in registered_top_level
    assert "ark_amend_match" not in registered_top_level
    assert "ark_cancel_match" not in registered_top_level
    assert "ark_reminder_prefs" not in registered_top_level
    assert "ark_set_preference" not in registered_top_level
    assert "ark_clear_preference" not in registered_top_level
    assert "ark_ban_add" not in registered_top_level
    assert "ark_ban_revoke" not in registered_top_level
    assert "ark_ban_list" not in registered_top_level
    assert "ark_set_result" not in registered_top_level
    assert "ark_report_players" not in registered_top_level
    assert "ark_generate_draft" not in registered_top_level
    assert "create_ark_team" not in registered_top_level
    assert "run_sql_proc" not in registered_top_level
    assert "mge_refresh_award_reminders" not in registered_top_level
    assert "prekvk_report" not in registered_top_level
    assert "prekvk_import_history" not in registered_top_level
    assert "summary" not in registered_top_level
    assert "weeksummary" not in registered_top_level
    assert "history" not in registered_top_level
    assert "failures" not in registered_top_level
    assert "usage" not in registered_top_level
    assert "usage_detail" not in registered_top_level
    assert "test_embed" not in registered_top_level
    assert "remove_registration" not in registered_top_level
    assert "remove_registration_by_id" not in registered_top_level
    assert "admin_register_governor" not in registered_top_level
    assert "registration_audit" not in registered_top_level
    assert "bulk_export_registrations" not in registered_top_level
    assert "bulk_import_registrations_dryrun" not in registered_top_level
    assert "bulk_import_registrations" not in registered_top_level
    assert "test_kvk_export" not in registered_top_level
    assert "refresh_stats_cache" not in registered_top_level
    assert "player_stats" not in registered_top_level
    assert "kvk_export_all" not in registered_top_level
    assert "kvk_recompute" not in registered_top_level
    assert "kvk_list_scans" not in registered_top_level
    assert "test_kvk_embed" not in registered_top_level
    assert "kvk_window_preview" not in registered_top_level
    assert "import_inventory" not in registered_top_level
    assert "inventory_import_audit" not in registered_top_level
    assert "calendar_refresh" not in registered_top_level
    assert "calendar_generate" not in registered_top_level
    assert "calendar_publish_cache" not in registered_top_level
    assert "calendar_status" not in registered_top_level
    assert "refresh_events" not in registered_top_level
    assert "refresh_kvk_overview" not in registered_top_level
    assert "list_subscribers" not in registered_top_level
    assert "migrate_subscriptions_dryrun" not in registered_top_level
    assert "migrate_subscriptions_apply" not in registered_top_level
    assert "crystaltech_validate" not in registered_top_level
    assert "crystaltech_reload" not in registered_top_level
    assert "crystaltech_admin_reset" not in registered_top_level
    assert "honor_purge_last" not in registered_top_level
    assert "import_locations" not in registered_top_level
    assert "player_location" not in registered_top_level
    assert "activity_top" not in registered_top_level
    assert "calendar" in registered_top_level
    assert "honor_rankings" in registered_top_level
    assert "player_profile" not in registered_top_level
    assert "ping" in registered_top_level


def test_startup_command_audit_uses_authoritative_inventory():
    source = Path("DL_bot.py").read_text(encoding="utf-8")

    assert "collect_static_primary_inventory" in source
    assert "commands package (authoritative)" in source
    assert "grouped_subcommands_detected" in source
    assert "_collect_declared_command_names_safely" in source
    assert "Failed parsing %s" in source
    assert "Commands.py (authoritative)" not in source
    assert "_collect_declared_slash_commands" not in source
