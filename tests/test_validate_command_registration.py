from __future__ import annotations

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


def test_current_command_surface_reflects_phase3_ops_grouping():
    names, grouped = validator.collect_primary_inventory()

    moved_to_ops = {
        "summary",
        "weeksummary",
        "history",
        "failures",
        "usage",
        "usage_detail",
        "test_embed",
    }

    assert len(names) == 75
    assert moved_to_ops.isdisjoint(names)
    assert moved_to_ops.issubset(grouped["ops"])
    assert len(grouped["ops"]) == 21
    assert sum(len(commands) for commands in grouped.values()) == 29


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
    for index in range(validator.PRIMARY_COMMAND_WARNING_THRESHOLD):
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
