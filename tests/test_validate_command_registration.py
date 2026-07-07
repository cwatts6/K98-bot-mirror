from __future__ import annotations

import json
from pathlib import Path

from scripts import validate_command_registration as validator


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_collect_primary_inventory_counts_groups_and_subcommands(tmp_path, monkeypatch):
    _write(
        tmp_path / "commands" / "sample_cmds.py",
        """
import discord


def register_sample(bot):
    group = discord.SlashCommandGroup("ops", "Ops")

    @group.command(name="status", description="Status")
    async def status(ctx):
        pass

    @bot.slash_command(name="ping", description="Ping")
    async def ping(ctx):
        pass
""",
    )

    monkeypatch.setattr(validator, "ROOT", tmp_path)

    names, grouped = validator.collect_primary_inventory()

    assert names == {"ops", "ping"}
    assert grouped == {"ops": {"status"}}


def test_collect_primary_inventory_counts_helper_attached_group_subcommands(tmp_path, monkeypatch):
    _write(
        tmp_path / "commands" / "__init__.py",
        """
from .sample_cmds import register_sample


def register_all(bot):
    register_sample(bot)
""",
    )
    _write(
        tmp_path / "commands" / "helper_cmds.py",
        """
def attach_admin(group):
    @group.command(name="audit", description="Audit")
    async def audit(ctx):
        pass
""",
    )
    _write(
        tmp_path / "commands" / "sample_cmds.py",
        """
import discord

from .helper_cmds import attach_admin


def register_sample(bot):
    group = discord.SlashCommandGroup("ops", "Ops")

    @group.command(name="status", description="Status")
    async def status(ctx):
        pass

    attach_admin(group)
    bot.add_application_command(group)
""",
    )

    monkeypatch.setattr(validator, "ROOT", tmp_path)

    names, grouped = validator.collect_primary_inventory()

    assert names == {"ops"}
    assert grouped == {"ops": {"audit", "status"}}


def test_current_command_surface_reflects_phase5a_admin_grouping():
    names, grouped = validator.collect_primary_inventory()

    moved_to_ops = {
        "summary",
        "weeksummary",
        "history",
        "failures",
        "usage",
        "usage_detail",
        "test_embed",
        "calendar_refresh",
        "calendar_generate",
        "calendar_publish_cache",
        "calendar_status",
    }
    moved_to_ark = {
        "ark_create_match": "create_match",
        "ark_force_announce": "force_announce",
        "ark_amend_match": "amend_match",
        "ark_cancel_match": "cancel_match",
        "ark_reminder_prefs": "reminder_prefs",
        "ark_set_preference": "set_preference",
        "ark_clear_preference": "clear_preference",
        "ark_ban_add": "ban_add",
        "ark_ban_revoke": "ban_revoke",
        "ark_ban_list": "ban_list",
        "ark_set_result": "set_result",
        "ark_report_players": "report_players",
        "ark_generate_draft": "generate_draft",
        "create_ark_team": "create_team",
    }
    phase5a_moves = {
        "registry": {
            "remove_registration": "remove",
            "remove_registration_by_id": "remove_by_id",
            "admin_register_governor": "admin_register",
            "registration_audit": "audit",
            "bulk_export_registrations": "bulk_export",
            "bulk_import_registrations_dryrun": "bulk_import_dryrun",
            "bulk_import_registrations": "bulk_import",
        },
        "kvk_admin": {
            "test_kvk_export": "test_export",
            "refresh_stats_cache": "refresh_stats_cache",
            "kvk_export_all": "export_all",
            "kvk_recompute": "recompute",
            "kvk_list_scans": "list_scans",
            "test_kvk_embed": "test_embed",
            "kvk_window_preview": "window_preview",
        },
        "stats": {"player_stats": "player"},
        "inventory": {"import_inventory": "import", "inventory_import_audit": "audit"},
        "events": {"refresh_events": "refresh", "refresh_kvk_overview": "refresh_kvk_overview"},
        "subscriptions": {
            "list_subscribers": "list",
            "migrate_subscriptions_dryrun": "migrate_dryrun",
            "migrate_subscriptions_apply": "migrate_apply",
        },
        "crystaltech": {
            "crystaltech_validate": "validate",
            "crystaltech_reload": "reload",
            "crystaltech_admin_reset": "admin_reset",
        },
        "honor": {"honor_purge_last": "purge_last"},
        "location": {"import_locations": "import", "player_location": "player"},
        "activity": {"activity_top": "top"},
    }

    assert len(names) == 42
    assert "kvk" in names
    assert "kvk_admin" in names
    assert "me" in names
    assert {"stats", "targets", "history", "rankings"}.issubset(grouped["kvk"])
    assert {
        "dashboard",
        "accounts",
        "reminders",
        "preferences",
        "inventory",
        "exports",
    }.issubset(grouped["me"])
    assert moved_to_ops.isdisjoint(names)
    assert moved_to_ops.issubset(grouped["ops"])
    assert set(moved_to_ark).isdisjoint(names)
    assert set(moved_to_ark.values()).issubset(grouped["ark"])
    for group_name, mapping in phase5a_moves.items():
        assert set(mapping).isdisjoint(names)
        assert set(mapping.values()).issubset(grouped[group_name])
    assert len(grouped["ops"]) == 25
    assert len(grouped["ark"]) == 14
    assert sum(len(commands) for commands in grouped.values()) == 96
    assert "calendar" in names
    assert "honor_rankings" in names
    assert "player_profile" in names
    assert "ping" in names
    assert "vote_admin" in names
    assert {
        "create",
        "update",
        "close",
        "status",
        "dashboard",
        "export",
        "survey_create",
        "survey_close",
        "survey_status",
        "survey_export",
    }.issubset(grouped["vote_admin"])


def test_validator_delegates_static_inventory_to_shared_helper():
    source = Path("scripts/validate_command_registration.py").read_text(encoding="utf-8")

    assert "collect_static_primary_inventory" in source
    assert "def _collect_group_helper_commands" not in source
    assert "def _active_command_paths" not in source
    assert "def _relative_label" not in source
    assert "def _literal_string" not in source
    assert "def _call_name" not in source


def test_main_reports_active_duplicate_risks(tmp_path, monkeypatch, capsys):
    _write(
        tmp_path / "commands" / "one_cmds.py",
        """
def register_one(bot):
    @bot.slash_command(name="ping", description="Ping")
    async def ping(ctx):
        pass
""",
    )
    _write(
        tmp_path / "commands" / "two_cmds.py",
        """
def register_two(bot):
    @bot.slash_command(name="ping", description="Ping again")
    async def ping_again(ctx):
        pass
""",
    )

    monkeypatch.setattr(validator, "ROOT", tmp_path)
    monkeypatch.setattr(validator, "APPROVED_TOP_LEVEL_COMMANDS", frozenset({"ping"}))
    monkeypatch.setattr(
        validator,
        "SECONDARY_MODULES",
        [
            validator.CommandSource(
                "cogs/commands.py (disabled legacy)", tmp_path / "cogs" / "commands.py"
            ),
            validator.CommandSource("subscribe.py (disabled legacy)", tmp_path / "subscribe.py"),
        ],
    )

    assert validator.main() == 0

    output = capsys.readouterr().out
    assert "active duplicate risks detected:" in output
    assert "/ping: commands/one_cmds.py, commands/two_cmds.py" in output


def test_main_warns_when_primary_command_count_nears_limit(tmp_path, monkeypatch, capsys):
    command_lines = []
    expected_names = set()
    for index in range(validator.PRIMARY_COMMAND_WARNING_THRESHOLD):
        expected_names.add(f"cmd_{index}")
        command_lines.append(f"""
    @bot.slash_command(name="cmd_{index}", description="Command {index}")
    async def cmd_{index}(ctx):
        pass
""")
    _write(
        tmp_path / "commands" / "many_cmds.py",
        "def register_many(bot):\n" + "\n".join(command_lines),
    )
    _write(tmp_path / "cogs" / "commands.py", "")
    _write(tmp_path / "subscribe.py", "")

    monkeypatch.setattr(validator, "ROOT", tmp_path)
    monkeypatch.setattr(validator, "APPROVED_TOP_LEVEL_COMMANDS", frozenset(expected_names))
    monkeypatch.setattr(
        validator,
        "SECONDARY_MODULES",
        [
            validator.CommandSource(
                "cogs/commands.py (disabled legacy)", tmp_path / "cogs" / "commands.py"
            ),
            validator.CommandSource("subscribe.py (disabled legacy)", tmp_path / "subscribe.py"),
        ],
    )

    assert validator.main() == 0

    output = capsys.readouterr().out
    assert "primary command limit warning" in output
    assert f"{validator.PRIMARY_COMMAND_WARNING_THRESHOLD}/100" in output


def test_main_reports_retired_secondary_surfaces_as_empty(tmp_path, monkeypatch, capsys):
    _write(
        tmp_path / "commands" / "sample_cmds.py",
        """
def register_sample(bot):
    @bot.slash_command(name="ping", description="Ping")
    async def ping(ctx):
        pass
""",
    )

    monkeypatch.setattr(validator, "ROOT", tmp_path)
    monkeypatch.setattr(validator, "APPROVED_TOP_LEVEL_COMMANDS", frozenset({"ping"}))
    monkeypatch.setattr(
        validator,
        "SECONDARY_MODULES",
        [
            validator.CommandSource(
                "cogs/commands.py (disabled legacy)", tmp_path / "cogs" / "commands.py"
            ),
            validator.CommandSource("subscribe.py (disabled legacy)", tmp_path / "subscribe.py"),
        ],
    )

    assert validator.main() == 0

    output = capsys.readouterr().out
    assert "disabled legacy command surfaces: none retained" in output
    assert "disabled_legacy=0" in output
    assert "no active duplicate risks detected" in output


def test_main_classifies_disabled_legacy_duplicates_separately(tmp_path, monkeypatch, capsys):
    _write(
        tmp_path / "commands" / "sample_cmds.py",
        """
def register_sample(bot):
    @bot.slash_command(name="ping", description="Ping")
    async def ping(ctx):
        pass
""",
    )
    _write(
        tmp_path / "cogs" / "commands.py",
        """
from discord.ext import commands


class SummaryCommands(commands.Cog):
    @commands.slash_command(name="ping", description="Test command")
    async def ping_command(self, ctx):
        pass
""",
    )
    _write(tmp_path / "subscribe.py", "")

    monkeypatch.setattr(validator, "ROOT", tmp_path)
    monkeypatch.setattr(validator, "APPROVED_TOP_LEVEL_COMMANDS", frozenset({"ping"}))
    monkeypatch.setattr(
        validator,
        "SECONDARY_MODULES",
        [
            validator.CommandSource(
                "cogs/commands.py (disabled legacy)", tmp_path / "cogs" / "commands.py"
            ),
            validator.CommandSource("subscribe.py (disabled legacy)", tmp_path / "subscribe.py"),
        ],
    )

    assert validator.main() == 0

    output = capsys.readouterr().out
    assert "disabled legacy command surfaces retained:" in output
    assert "no active duplicate risks detected" in output
    assert "disabled legacy duplicates detected:" in output
    assert "/ping: cogs/commands.py (disabled legacy), commands package (authoritative)" in output


def test_main_fails_on_unapproved_top_level_command(tmp_path, monkeypatch, capsys):
    _write(
        tmp_path / "commands" / "sample_cmds.py",
        """
def register_sample(bot):
    @bot.slash_command(name="new_admin_tool", description="New admin tool")
    async def new_admin_tool(ctx):
        pass
""",
    )

    monkeypatch.setattr(validator, "ROOT", tmp_path)
    monkeypatch.setattr(validator, "APPROVED_TOP_LEVEL_COMMANDS", frozenset({"ping"}))
    monkeypatch.setattr(
        validator,
        "SECONDARY_MODULES",
        [
            validator.CommandSource(
                "cogs/commands.py (disabled legacy)", tmp_path / "cogs" / "commands.py"
            ),
            validator.CommandSource("subscribe.py (disabled legacy)", tmp_path / "subscribe.py"),
        ],
    )

    assert validator.main() == 1

    output = capsys.readouterr().out
    assert "unexpected top-level command drift detected:" in output
    assert "/new_admin_tool" in output
    assert "approved top-level commands missing from current inventory:" in output
    assert "/ping" in output


def test_main_writes_json_inventory_artifact(tmp_path, monkeypatch, capsys):
    _write(
        tmp_path / "commands" / "sample_cmds.py",
        """
import discord


def register_sample(bot):
    group = discord.SlashCommandGroup("ops", "Ops")

    @group.command(name="status", description="Status")
    async def status(ctx):
        pass

    bot.add_application_command(group)
""",
    )
    output_path = tmp_path / "artifacts" / "commands.json"

    monkeypatch.setattr(validator, "ROOT", tmp_path)
    monkeypatch.setattr(validator, "APPROVED_TOP_LEVEL_COMMANDS", frozenset({"ops"}))
    monkeypatch.setattr(
        validator,
        "SECONDARY_MODULES",
        [
            validator.CommandSource(
                "cogs/commands.py (disabled legacy)", tmp_path / "cogs" / "commands.py"
            ),
            validator.CommandSource("subscribe.py (disabled legacy)", tmp_path / "subscribe.py"),
        ],
    )

    assert validator.main(["--format", "json", "--output", str(output_path)]) == 0

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["summary"]["primary"] == 1
    assert payload["summary"]["grouped_subcommands_detected"] == 1
    assert payload["top_level_commands"] == ["ops"]
    assert payload["grouped_commands"] == {"ops": ["status"]}
    assert json.loads(capsys.readouterr().out)["summary"]["headroom"] == 99


def test_main_writes_markdown_inventory_artifact(tmp_path, monkeypatch):
    _write(
        tmp_path / "commands" / "sample_cmds.py",
        """
def register_sample(bot):
    @bot.slash_command(name="ping", description="Ping")
    async def ping(ctx):
        pass
""",
    )
    output_path = tmp_path / "artifacts" / "commands.md"

    monkeypatch.setattr(validator, "ROOT", tmp_path)
    monkeypatch.setattr(validator, "APPROVED_TOP_LEVEL_COMMANDS", frozenset({"ping"}))
    monkeypatch.setattr(
        validator,
        "SECONDARY_MODULES",
        [
            validator.CommandSource(
                "cogs/commands.py (disabled legacy)", tmp_path / "cogs" / "commands.py"
            ),
            validator.CommandSource("subscribe.py (disabled legacy)", tmp_path / "subscribe.py"),
        ],
    )

    assert validator.main(["--format", "markdown", "--output", str(output_path)]) == 0

    output = output_path.read_text(encoding="utf-8")
    assert "# Command Registration Inventory" in output
    assert "| Top-level commands | 1 |" in output
    assert "- `/ping`" in output
    assert "No unexpected top-level command drift detected" in output


def test_markdown_inventory_nests_missing_and_duplicate_details() -> None:
    report = validator.CommandRegistrationReport(
        primary_names={"new_tool", "ping"},
        grouped={},
        primary_name_sources={"ping": ["commands/a.py", "commands/b.py"]},
        paths={
            validator.PRIMARY_COMMAND_SURFACE_LABEL: {"new_tool", "ping"},
            "renamed secondary label": {"legacy_ping"},
        },
        active_duplicates={"ping": ["commands/a.py", "commands/b.py"]},
        disabled_legacy_duplicates={},
        unexpected_top_level={"new_tool"},
        missing_approved_top_level={"ops"},
    )

    output = validator._format_markdown(report)

    assert "- Approved top-level commands missing from current inventory:" in output
    assert "  - `/ops`" in output
    assert "- Active duplicate risks detected:" in output
    assert "  - `/ping`: commands/a.py, commands/b.py" in output
    assert "| Disabled legacy declarations | 1 |" in output


def test_report_secondary_counts_tolerate_missing_or_extended_labels() -> None:
    report = validator.CommandRegistrationReport(
        primary_names={"ping"},
        grouped={},
        primary_name_sources={},
        paths={
            validator.PRIMARY_COMMAND_SURFACE_LABEL: {"ping"},
            "custom secondary surface": {"legacy_ping", "legacy_subscribe"},
        },
        active_duplicates={},
        disabled_legacy_duplicates={},
        unexpected_top_level=set(),
        missing_approved_top_level=set(),
    )

    assert report.secondary_cogs_count == 0
    assert report.secondary_subscribe_count == 0
    assert report.disabled_legacy_count == 2
