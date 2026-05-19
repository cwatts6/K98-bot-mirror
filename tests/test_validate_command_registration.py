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
            ("cogs/commands.py (secondary)", tmp_path / "cogs" / "commands.py"),
            ("subscribe.py (secondary)", tmp_path / "subscribe.py"),
        ],
    )

    assert validator.main() == 0

    output = capsys.readouterr().out
    assert "primary command limit warning" in output
    assert f"{validator.PRIMARY_COMMAND_WARNING_THRESHOLD}/100" in output
